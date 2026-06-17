"""
fixtures.py — Parse and structure match fixtures from scraped data.
"""

import re
from datetime import datetime


# ── Parse raw match boxes from BeautifulSoup ─────────────────────────────────

def parse_fixtures_from_soup(soup) -> list[dict]:
    """
    Main entry point: extract all match fixtures from the group-stage page.
    Returns list of match dicts sorted by date.
    """
    matches = []
    matches.extend(_parse_footballboxes(soup))
    if not matches:
        matches.extend(_parse_table_rows(soup))
    matches = _deduplicate(matches)
    matches = _sort_fixtures(matches)
    return matches


def _parse_footballboxes(soup) -> list[dict]:
    """Parse structured football-box divs used on Wikipedia match pages."""
    matches = []

    for box in soup.find_all("div", class_=re.compile(r"footballbox", re.I)):
        try:
            home_el  = box.find(class_=re.compile(r"fhome|team1", re.I))
            away_el  = box.find(class_=re.compile(r"faway|team2", re.I))
            score_el = box.find(class_=re.compile(r"fscore|score", re.I))
            date_el  = box.find(class_=re.compile(r"fdate|date", re.I))
            time_el  = box.find(class_=re.compile(r"ftime|time", re.I))
            venue_el = box.find(class_=re.compile(r"fstadium|venue|stadium", re.I))

            if not home_el or not away_el:
                continue

            home  = _clean(home_el.get_text())
            away  = _clean(away_el.get_text())
            raw_score = _clean(score_el.get_text()) if score_el else ""
            date  = _clean(date_el.get_text()) if date_el else ""
            time  = _clean(time_el.get_text()) if time_el else ""
            venue = _clean(venue_el.get_text()) if venue_el else ""

            score_a, score_b, played = _parse_score(raw_score)

            # Try to extract goalscorers from box
            scorers = _extract_scorers(box)

            matches.append({
                "home":     home,
                "away":     away,
                "score_a":  score_a,
                "score_b":  score_b,
                "played":   played,
                "raw_score": raw_score,
                "date":     date,
                "time":     time,
                "venue":    venue,
                "scorers":  scorers,
                "group":    _detect_group(box),
            })
        except Exception:
            continue

    return matches


def _parse_table_rows(soup) -> list[dict]:
    """Fallback: look for score patterns in table rows."""
    matches = []
    score_pat = re.compile(r"^(\d+)\s*[–\-]\s*(\d+)$")

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            for i, cell in enumerate(cells):
                m = score_pat.match(cell)
                if m and i > 0 and i < len(cells) - 1:
                    home  = cells[i - 1]
                    away  = cells[i + 1]
                    sa, sb, played = int(m.group(1)), int(m.group(2)), True
                    if len(home) > 2 and len(away) > 2:
                        matches.append({
                            "home":  home, "away": away,
                            "score_a": sa, "score_b": sb,
                            "played": played, "raw_score": cell,
                            "date": cells[0] if cells else "",
                            "time": "", "venue": "", "scorers": {},
                            "group": "",
                        })
    return matches


def _parse_score(raw: str):
    """Return (score_a, score_b, played). played=False for upcoming matches."""
    raw = raw.strip()
    if not raw or raw.lower() in ("vs", "v", "-", "–", "tbd", ""):
        return None, None, False
    m = re.match(r"(\d+)\s*[–\-]\s*(\d+)", raw)
    if m:
        return int(m.group(1)), int(m.group(2)), True
    return None, None, False


def _extract_scorers(box) -> dict:
    """
    Attempt to extract goalscorer names from a match box.
    Returns dict: {"home": [...], "away": [...]}
    """
    scorers = {"home": [], "away": []}
    for team_side, css_key in [("home", "fhomeg"), ("away", "fawayg")]:
        el = box.find(class_=re.compile(css_key, re.I))
        if el:
            text = el.get_text(separator=" ", strip=True)
            # Remove minute markers like "23'" or "45+1'"
            names = re.sub(r"\d+\+?\d*'", "", text).strip()
            if names:
                scorers[team_side] = [n.strip() for n in names.split(",") if n.strip()]
    return scorers


def _detect_group(box) -> str:
    """Try to detect which group this match belongs to."""
    # Walk up to find a heading
    for parent in box.parents:
        prev = parent.find_previous_sibling(["h2", "h3"])
        if prev:
            text = prev.get_text(strip=True)
            m = re.search(r"Group\s+([A-L])", text, re.I)
            if m:
                return m.group(1).upper()
    return ""


def _clean(s: str) -> str:
    s = re.sub(r"\[\w+\]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _deduplicate(matches: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for m in matches:
        key = (m["home"].lower(), m["away"].lower(), m.get("date", ""))
        if key not in seen:
            seen.add(key)
            result.append(m)
    return result


def _sort_fixtures(matches: list[dict]) -> list[dict]:
    """Sort: played matches first (by date desc), then upcoming (by date asc)."""
    played   = [m for m in matches if m.get("played")]
    upcoming = [m for m in matches if not m.get("played")]
    return played + upcoming


# ── Public summary helpers ────────────────────────────────────────────────────

def split_played_upcoming(matches: list[dict]) -> tuple[list[dict], list[dict]]:
    played   = [m for m in matches if m.get("played")]
    upcoming = [m for m in matches if not m.get("played")]
    return played, upcoming


def group_by_group(matches: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for m in matches:
        g = m.get("group", "Unknown")
        grouped.setdefault(g, []).append(m)
    return grouped
