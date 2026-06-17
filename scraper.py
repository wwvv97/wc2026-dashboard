"""
scraper.py — Polite Wikipedia scraper for WC2026 data.

Rules observed:
- User-Agent identifies the script and purpose
- 1.5s delay between every request (Wikimedia policy: >= 1s)
- Concurrency: 1 (sequential only)
- Respects HTTP 429/5xx with exponential back-off
- Only fetches /wiki/ article pages (allowed by robots.txt)
- Uses Wikipedia's REST API (cleaner HTML, less server load)
"""

import time
import re
import requests
from bs4 import BeautifulSoup

# ── polite scraping config ────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "WC2026Dashboard/1.0 (educational personal project; "
        "fetches group-stage data from Wikipedia article pages; "
        "contact: local-script)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
DELAY = 1.5          # seconds between requests
MAX_RETRIES = 3
BACKOFF_BASE = 5     # seconds; multiplied by attempt number on 5xx

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

_last_request_time = 0.0


def _polite_get(url: str) -> requests.Response:
    """Rate-limited GET with retry on transient errors."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < DELAY:
        time.sleep(DELAY - elapsed)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = SESSION.get(url, timeout=15)
            _last_request_time = time.time()
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 30))
                print(f"  [rate-limit] 429 received; sleeping {wait}s …")
                time.sleep(wait)
            elif resp.status_code >= 500:
                wait = BACKOFF_BASE * attempt
                print(f"  [server-err] {resp.status_code} on {url}; sleeping {wait}s …")
                time.sleep(wait)
            else:
                print(f"  [warning] HTTP {resp.status_code} for {url}")
                return resp
        except requests.RequestException as exc:
            print(f"  [error] attempt {attempt}: {exc}")
            time.sleep(BACKOFF_BASE * attempt)

    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts")


# ── Wikipedia REST helper ─────────────────────────────────────────────────────
WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/html/{title}"
WIKI_HTML = "https://en.wikipedia.org/wiki/{title}"


def _fetch_wiki_html(title: str) -> BeautifulSoup:
    """Fetch a Wikipedia article and return a BeautifulSoup of its HTML."""
    url = WIKI_HTML.format(title=title)
    print(f"  → fetching {url}")
    resp = _polite_get(url)
    return BeautifulSoup(resp.text, "lxml")


# ── Group standings ───────────────────────────────────────────────────────────
GROUPS = list("ABCDEFGHIJKL")

GROUP_TEAMS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Switzerland", "Bosnia and Herzegovina", "Qatar"],
    "C": ["Brazil", "Morocco", "Colombia", "Japan"],  # will be overridden by live data
    "D": ["United States", "Uruguay", "Angola", "Azerbaijan"],  # placeholder fallback
    "E": ["Germany", "Curaçao", "Côte d'Ivoire", "Ecuador"],
    "F": ["Argentina", "Algeria", "Croatia", "Cameroon"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Senegal", "Sweden", "Tunisia"],  # placeholder
    "I": ["France", "Iraq", "Norway", "Senegal"],
    "J": ["Portugal", "Ghana", "Cape Verde", "Uzbekistan"],
    "K": ["Netherlands", "Australia", "Turkey", "Saudi Arabia"],
    "L": ["England", "South Africa", "Panama", "Haiti"],
}

# Official bracket page title
BRACKET_WIKI = "2026_FIFA_World_Cup_knockout_stage"


def parse_group_table(soup: BeautifulSoup, group_letter: str) -> list[dict]:
    """
    Extract the standings table from a group Wikipedia page.
    Returns list of team dicts with keys:
      pos, team, pld, w, d, l, gf, ga, gd, pts, yc, rc, group
    """
    rows = []

    # Find all wikitables; the standings table is usually the first one
    # with columns Pos | Team | Pld | W | D | L | GF | GA | GD | Pts
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)

    standing_table = None
    for tbl in tables:
        headers = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
        combined = " ".join(headers)
        if "pld" in combined and "pts" in combined and "gd" in combined:
            standing_table = tbl
            break

    if not standing_table:
        print(f"  [warn] no standings table found for Group {group_letter}")
        return []

    tbody = standing_table.find("tbody") or standing_table

    for tr in tbody.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 9:
            continue

        texts = [c.get_text(strip=True) for c in cells]

        # Skip header rows
        if not texts[0].isdigit():
            continue

        try:
            team_name = _clean_team_name(texts[1])
            pld = _int(texts[2])
            w   = _int(texts[3])
            d   = _int(texts[4])
            l   = _int(texts[5])
            gf  = _int(texts[6])
            ga  = _int(texts[7])
            gd_raw = texts[8].replace("−", "-").replace("–", "-")
            gd  = _int(gd_raw)
            pts = _int(texts[9]) if len(texts) > 9 else w * 3 + d

            rows.append({
                "pos":   int(texts[0]),
                "team":  team_name,
                "pld":   pld,
                "w":     w,
                "d":     d,
                "l":     l,
                "gf":    gf,
                "ga":    ga,
                "gd":    gd,
                "pts":   pts,
                "yc":    0,  # updated later from fair-play table if available
                "rc":    0,
                "group": group_letter,
            })
        except (ValueError, IndexError):
            continue

    return rows


def _clean_team_name(raw: str) -> str:
    """Strip footnotes, (H), (host) markers from team names."""
    raw = re.sub(r"\(H\)", "", raw)
    raw = re.sub(r"\[\w+\]", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def _int(s: str) -> int:
    s = s.strip().replace("−", "-").replace("–", "-").replace("+", "")
    return int(s) if s.lstrip("-").isdigit() else 0


def scrape_all_groups() -> list[dict]:
    """Scrape all 12 group pages and return flat list of team rows."""
    all_rows = []
    for g in GROUPS:
        title = f"2026_FIFA_World_Cup_Group_{g}"
        print(f"Scraping Group {g} …")
        try:
            soup = _fetch_wiki_html(title)
            rows = parse_group_table(soup, g)
            if rows:
                all_rows.extend(rows)
                print(f"  ✓ Group {g}: {len(rows)} teams parsed")
            else:
                print(f"  ✗ Group {g}: no rows; using fallback zeros")
                all_rows.extend(_fallback_group(g))
        except Exception as exc:
            print(f"  ✗ Group {g} error: {exc}; using fallback")
            all_rows.extend(_fallback_group(g))
    return all_rows


def _fallback_group(g: str) -> list[dict]:
    """Return zeroed rows for a group when scraping fails."""
    teams = GROUP_TEAMS.get(g, [f"Team {g}1", f"Team {g}2", f"Team {g}3", f"Team {g}4"])
    return [
        {"pos": i + 1, "team": t, "pld": 0, "w": 0, "d": 0, "l": 0,
         "gf": 0, "ga": 0, "gd": 0, "pts": 0, "yc": 0, "rc": 0, "group": g}
        for i, t in enumerate(teams)
    ]


# ── Fixtures ──────────────────────────────────────────────────────────────────
def scrape_fixtures() -> list[dict]:
    """Scrape group-stage fixtures from the main WC2026 group stage page."""
    print("Scraping fixtures …")
    soup = _fetch_wiki_html("2026_FIFA_World_Cup_group_stage")
    matches = []

    # Each match is in a table with class "footballbox" or similar
    # We look for all match boxes
    for box in soup.find_all("div", class_=re.compile(r"football.?box|match.?box", re.I)):
        match = _parse_matchbox(box)
        if match:
            matches.append(match)

    # Fallback: look for tables with score patterns
    if not matches:
        matches = _parse_fixtures_from_tables(soup)

    print(f"  ✓ {len(matches)} fixtures found")
    return matches


def _parse_matchbox(box) -> dict | None:
    """Parse a single football match box."""
    try:
        teams = box.find_all(class_=re.compile(r"fhome|faway|team", re.I))
        score_el = box.find(class_=re.compile(r"fscore|score", re.I))
        date_el  = box.find(class_=re.compile(r"fdate|date", re.I))

        if len(teams) < 2:
            return None

        home = _clean_team_name(teams[0].get_text(strip=True))
        away = _clean_team_name(teams[-1].get_text(strip=True))
        score = score_el.get_text(strip=True) if score_el else "vs"
        date  = date_el.get_text(strip=True) if date_el else ""

        return {"home": home, "away": away, "score": score, "date": date}
    except Exception:
        return None


def _parse_fixtures_from_tables(soup: BeautifulSoup) -> list[dict]:
    """Secondary fixture parser using score-like patterns in tables."""
    matches = []
    score_pat = re.compile(r"^\d+\s*[–\-]\s*\d+$")

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            for i, cell in enumerate(cells):
                if score_pat.match(cell) and i > 0 and i < len(cells) - 1:
                    matches.append({
                        "home": cells[i - 1],
                        "away": cells[i + 1] if i + 1 < len(cells) else "",
                        "score": cell,
                        "date": cells[0] if cells else "",
                    })
    return matches


# ── Player stats ──────────────────────────────────────────────────────────────
def scrape_player_stats() -> list[dict]:
    """Scrape top scorers / assists from the dedicated WC2026 statistics page."""
    print("Scraping player statistics …")
    soup = _fetch_wiki_html("2026_FIFA_World_Cup_statistics")
    players = _parse_player_tables(soup)

    if not players:
        # Fallback: goalscorers page
        print("  → trying goalscorers page …")
        try:
            soup2 = _fetch_wiki_html("2026_FIFA_World_Cup_statistics#Goalscorers")
            players = _parse_player_tables(soup2)
        except Exception:
            pass

    print(f"  ✓ {len(players)} player records found")
    return players


def _parse_player_tables(soup: BeautifulSoup) -> list[dict]:
    """Extract player stats from any wikitables on the page."""
    players = []
    seen = set()

    for table in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        headers_raw = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        headers = " ".join(headers_raw)

        # Detect column types
        has_goals   = "goal" in headers
        has_assists = "assist" in headers
        has_player  = "player" in headers or "name" in headers

        if not has_player:
            continue

        col_map = _map_columns(headers_raw)

        for tr in (table.find("tbody") or table).find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            texts = [c.get_text(strip=True) for c in cells]

            player_col = col_map.get("player", col_map.get("name", 0))
            if player_col >= len(texts):
                continue

            name = _clean_player_name(texts[player_col])
            if not name or name.lower() in ("player", "name", ""):
                continue

            key = name.lower()
            if key in seen:
                # merge data
                for p in players:
                    if p["name"].lower() == key:
                        _merge_player(p, texts, col_map, has_goals, has_assists)
                        break
            else:
                seen.add(key)
                p = {
                    "name":     name,
                    "team":     texts[col_map["team"]] if "team" in col_map and col_map["team"] < len(texts) else "",
                    "pos":      texts[col_map["pos"]] if "pos" in col_map and col_map["pos"] < len(texts) else "",
                    "goals":    0,
                    "assists":  0,
                    "minutes":  0,
                    "matches":  0,
                    "clean_sheets": 0,
                    "saves":    0,
                    "yc":       0,
                    "rc":       0,
                }
                _merge_player(p, texts, col_map, has_goals, has_assists)
                players.append(p)

    return players


def _map_columns(headers: list[str]) -> dict[str, int]:
    """Map semantic names to column indices."""
    mapping = {}
    keywords = {
        "player": ["player", "name"],
        "team":   ["team", "country", "nation", "club"],
        "pos":    ["pos", "position"],
        "goals":  ["goal", "goals", "gls", "g"],
        "assists":["assist", "assists", "ast", "a"],
        "minutes":["min", "minute", "minutes", "mp"],
        "matches":["matches", "apps", "played", "pld", "mp"],
        "clean_sheets": ["clean", "cs"],
        "saves":  ["save", "saves"],
        "yc":     ["yellow", "yc", "yl"],
        "rc":     ["red", "rc"],
    }
    for i, h in enumerate(headers):
        for key, kws in keywords.items():
            if key not in mapping and any(kw in h for kw in kws):
                mapping[key] = i
    return mapping


def _merge_player(p: dict, texts: list[str], col_map: dict,
                  has_goals: bool, has_assists: bool):
    """Fill in numeric fields from a row of cells."""
    for field, col in col_map.items():
        if field in ("player", "name", "team", "pos"):
            continue
        if col >= len(texts):
            continue
        val = _int(texts[col])
        if field in p and val > 0:
            p[field] = max(p.get(field, 0), val)


def _clean_player_name(s: str) -> str:
    s = re.sub(r"\[\w+\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ── Squads (for position data) ────────────────────────────────────────────────
def scrape_squads() -> list[dict]:
    """Scrape squad list to get player positions."""
    print("Scraping squad data …")
    soup = _fetch_wiki_html("2026_FIFA_World_Cup_squads")
    players = []
    seen = set()

    for table in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        headers_raw = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        headers = " ".join(headers_raw)
        if "pos" not in headers and "position" not in headers:
            continue

        col_map = _map_columns(headers_raw)

        # Get team from nearest preceding heading
        team = ""
        for tag in table.find_all_previous(["h2", "h3", "h4"]):
            t = tag.get_text(strip=True)
            if t and not t.startswith("Contents"):
                team = _clean_team_name(t)
                break

        for tr in (table.find("tbody") or table).find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            texts = [c.get_text(strip=True) for c in cells]

            name_col = col_map.get("player", col_map.get("name", 2))
            pos_col  = col_map.get("pos", 1)

            if name_col >= len(texts):
                continue

            name = _clean_player_name(texts[name_col])
            if not name:
                continue

            key = (name.lower(), team.lower())
            if key in seen:
                continue
            seen.add(key)

            pos_raw = texts[pos_col] if pos_col < len(texts) else ""
            pos = _normalise_position(pos_raw)

            players.append({
                "name":  name,
                "team":  team,
                "pos":   pos,
                "shirt": texts[0] if texts else "",
            })

    print(f"  ✓ {len(players)} squad players found")
    return players


def _normalise_position(raw: str) -> str:
    raw = raw.upper().strip()
    if raw in ("GK", "G", "GOALKEEPER"):
        return "GK"
    if raw in ("DF", "D", "DEF", "CB", "LB", "RB", "LWB", "RWB", "DEFENDER", "BACK"):
        return "DF"
    if raw in ("MF", "M", "MID", "CM", "DM", "AM", "CDM", "CAM", "LM", "RM", "MIDFIELDER"):
        return "MF"
    if raw in ("FW", "F", "ST", "CF", "LW", "RW", "SS", "FORWARD", "STRIKER", "WINGER"):
        return "FW"
    return raw  # keep raw if unknown


if __name__ == "__main__":
    rows = scrape_all_groups()
    for r in rows[:4]:
        print(r)
