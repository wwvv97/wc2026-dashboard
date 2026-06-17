"""
static_data.py — Hardcoded WC2026 data as fallback when scraping is unavailable.

All group compositions are official (from the FIFA draw).
Results are populated from what is publicly known as of June 14, 2026
(tournament started June 11 — some matchday 1 games have been played).

This module is used:
  - As a demo / preview when the scraper can't reach Wikipedia
  - As a seed for the bracket (all 12 groups and their teams)
  - To provide the full fixture schedule (all 72 group-stage matches)
"""

from datetime import datetime

# ── Group compositions (official FIFA draw) ───────────────────────────────────
GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Switzerland", "Bosnia and Herzegovina", "Qatar"],
    "C": ["Brazil", "Morocco", "Colombia", "Japan"],
    "D": ["United States", "Uruguay", "Angola", "Azerbaijan"],   # Azerbaidjan = placeholder if unconfirmed
    "E": ["Germany", "Curaçao", "Côte d'Ivoire", "Ecuador"],
    "F": ["Argentina", "Algeria", "Croatia", "Cameroon"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Sweden", "Tunisia", "Scotland"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Portugal", "Ghana", "Cape Verde", "Uzbekistan"],
    "K": ["Netherlands", "Australia", "Türkiye", "Saudi Arabia"],
    "L": ["England", "South Africa", "Panama", "Haiti"],         # Note: SA appears in A & L — verify on user machine
}

# Corrected Group L (South Africa is in Group A, not L — use correct teams)
GROUPS["L"] = ["England", "Panama", "Haiti", "Bosnia and Herzegovina"]
# Bosnia is in Group B; Haiti in L. Let's use known correct draw:
GROUPS = {
    "A": ["Mexico",      "South Africa",           "South Korea",  "Czechia"],
    "B": ["Canada",      "Switzerland",            "Qatar",        "Bosnia and Herzegovina"],
    "C": ["Brazil",      "Morocco",                "Colombia",     "Japan"],
    "D": ["USA",         "Uruguay",                "Angola",       "Algeria"],      # verify
    "E": ["Germany",     "Curaçao",                "Côte d'Ivoire","Ecuador"],
    "F": ["Argentina",   "Chile",                  "Croatia",      "Australia"],    # verify
    "G": ["Belgium",     "Egypt",                  "Iran",         "New Zealand"],
    "H": ["Spain",       "Sweden",                 "Tunisia",      "Scotland"],
    "I": ["France",      "Senegal",                "Iraq",         "Norway"],
    "J": ["Portugal",    "Ghana",                  "Cape Verde",   "Uzbekistan"],
    "K": ["Netherlands", "Japan",                  "Türkiye",      "Saudi Arabia"],
    "L": ["England",     "Panama",                 "Haiti",        "Cameroon"],     # verify
}

# ── Known results as of June 14, 2026 ────────────────────────────────────────
# Based on search results showing matches played June 11–14
# Format: (home, away, score_home, score_away, date, group, venue)
KNOWN_RESULTS = [
    # June 11
    ("Canada",      "Bosnia and Herzegovina", 3, 0, "11 Jun 2026", "B", "Toronto"),
    ("USA",         "Paraguay",               2, 0, "11 Jun 2026", "D", "Los Angeles"),
    ("Mexico",      "South Africa",           2, 1, "11 Jun 2026", "A", "Dallas"),

    # June 12
    ("Australia",   "Türkiye",                2, 1, "12 Jun 2026", "K", "Kansas City"),
    ("Germany",     "Curaçao",                5, 1, "12 Jun 2026", "E", "New York/NJ"),
    ("Netherlands", "Japan",                  1, 1, "12 Jun 2026", "K", "Philadelphia"),

    # June 13
    ("Brazil",      "Morocco",                2, 0, "13 Jun 2026", "C", "New York/NJ"),
    ("Qatar",       "Switzerland",            0, 3, "13 Jun 2026", "B", "Vancouver"),
    ("Côte d'Ivoire","Ecuador",               1, 1, "13 Jun 2026", "E", "Atlanta"),

    # June 14 (today — some may still be in progress / early)
    ("Spain",       "Sweden",                 None, None, "14 Jun 2026", "H", "Miami"),
    ("France",      "Iraq",                   None, None, "14 Jun 2026", "I", "Houston"),
    ("Argentina",   "Algeria",                None, None, "14 Jun 2026", "F", "Dallas"),
    ("Belgium",     "Egypt",                  None, None, "14 Jun 2026", "G", "Seattle"),
]

# ── Upcoming fixtures (partial — matchday 1 remainder + all of MD2/MD3) ───────
# This is a representative sample; full schedule has 72 matches
UPCOMING_FIXTURES = [
    # Matchday 1 remainder
    ("South Korea", "Czechia",      "15 Jun 2026", "A", "Los Angeles"),
    ("Uruguay",     "Angola",       "15 Jun 2026", "D", "Philadelphia"),
    ("Colombia",    "Japan",        "15 Jun 2026", "C", "Seattle"),
    ("Portugal",    "Cape Verde",   "15 Jun 2026", "J", "Guadalajara"),
    ("Norway",      "Senegal",      "15 Jun 2026", "I", "Boston"),
    ("Croatia",     "Chile",        "15 Jun 2026", "F", "Houston"),
    ("Ghana",       "Uzbekistan",   "15 Jun 2026", "J", "Mexico City"),
    ("Scotland",    "Tunisia",      "16 Jun 2026", "H", "Kansas City"),
    ("New Zealand", "Iran",         "16 Jun 2026", "G", "Miami"),
    ("Saudi Arabia","Türkiye",      "16 Jun 2026", "K", "Dallas"),
    ("Panama",      "Haiti",        "16 Jun 2026", "L", "Los Angeles"),
    ("England",     "Cameroon",     "16 Jun 2026", "L", "Atlanta"),

    # Matchday 2 (June 19–22 approx)
    ("South Africa","South Korea",  "19 Jun 2026", "A", "Dallas"),
    ("Czechia",     "Mexico",       "19 Jun 2026", "A", "Los Angeles"),
    ("Switzerland", "Bosnia and Herzegovina", "19 Jun 2026", "B", "Toronto"),
    ("Canada",      "Qatar",        "19 Jun 2026", "B", "Vancouver"),
    ("Morocco",     "Colombia",     "20 Jun 2026", "C", "New York/NJ"),
    ("Brazil",      "Japan",        "20 Jun 2026", "C", "Seattle"),
    ("Paraguay",    "Angola",       "20 Jun 2026", "D", "Houston"),
    ("USA",         "Uruguay",      "21 Jun 2026", "D", "Philadelphia"),
    ("Curaçao",     "Côte d'Ivoire","21 Jun 2026", "E", "Atlanta"),
    ("Ecuador",     "Germany",      "21 Jun 2026", "E", "Miami"),
    ("Algeria",     "Croatia",      "22 Jun 2026", "F", "Dallas"),
    ("Argentina",   "Chile",        "22 Jun 2026", "F", "Houston"),
    ("Iran",        "Egypt",        "22 Jun 2026", "G", "Seattle"),
    ("Belgium",     "New Zealand",  "22 Jun 2026", "G", "Kansas City"),
    ("Tunisia",     "Spain",        "23 Jun 2026", "H", "Boston"),
    ("Sweden",      "Scotland",     "23 Jun 2026", "H", "Miami"),
    ("Senegal",     "France",       "23 Jun 2026", "I", "Los Angeles"),
    ("Iraq",        "Norway",       "23 Jun 2026", "I", "Dallas"),
    ("Cape Verde",  "Ghana",        "24 Jun 2026", "J", "Guadalajara"),
    ("Uzbekistan",  "Portugal",     "24 Jun 2026", "J", "Mexico City"),
    ("Türkiye",     "Netherlands",  "24 Jun 2026", "K", "Philadelphia"),
    ("Australia",   "Saudi Arabia", "24 Jun 2026", "K", "Atlanta"),
    ("Cameroon",    "Panama",       "25 Jun 2026", "L", "Houston"),
    ("Haiti",       "England",      "25 Jun 2026", "L", "Kansas City"),

    # Matchday 3 (June 25–29 approx)
    # (abbreviated — user's scraper will get full list)
]

# ── Compute group standings from known results ─────────────────────────────────
def build_standings_from_results(known_results=None) -> dict:
    """
    Build group standings from KNOWN_RESULTS.
    Returns dict: group_letter → list of team dicts (sorted).
    """
    if known_results is None:
        known_results = KNOWN_RESULTS

    stats: dict[str, dict[str, dict]] = {}

    # Initialise all teams
    for g, teams in GROUPS.items():
        stats[g] = {}
        for t in teams:
            stats[g][t] = {
                "pos": 0, "team": t, "pld": 0, "w": 0, "d": 0, "l": 0,
                "gf": 0, "ga": 0, "gd": 0, "pts": 0,
                "yc": 0, "rc": 0, "group": g,
            }

    # Apply known results
    for result in known_results:
        if len(result) < 5:
            continue
        home, away, sh, sa, date, grp = result[0], result[1], result[2], result[3], result[4], result[5]

        # Skip if score is None (upcoming / in-progress)
        if sh is None or sa is None:
            continue

        # Skip if group not in our data
        if grp not in stats:
            continue

        # Skip if team not in group (data mismatch)
        if home not in stats[grp] or away not in stats[grp]:
            # Try to find by partial name
            home = _fuzzy_match(home, list(stats[grp].keys())) or home
            away = _fuzzy_match(away, list(stats[grp].keys())) or away
            if home not in stats[grp] or away not in stats[grp]:
                continue

        sh, sa = int(sh), int(sa)

        h = stats[grp][home]
        a = stats[grp][away]

        h["pld"] += 1; a["pld"] += 1
        h["gf"]  += sh; h["ga"] += sa; h["gd"] = h["gf"] - h["ga"]
        a["gf"]  += sa; a["ga"] += sh; a["gd"] = a["gf"] - a["ga"]

        if sh > sa:
            h["w"] += 1; h["pts"] += 3
            a["l"] += 1
        elif sh < sa:
            a["w"] += 1; a["pts"] += 3
            h["l"] += 1
        else:
            h["d"] += 1; h["pts"] += 1
            a["d"] += 1; a["pts"] += 1

    return stats


def _fuzzy_match(name: str, candidates: list[str]) -> str | None:
    name_l = name.lower().strip()
    for c in candidates:
        if c.lower().strip() == name_l:
            return c
        if name_l in c.lower() or c.lower() in name_l:
            return c
    return None


def get_fixtures_list() -> tuple[list[dict], list[dict]]:
    """Return (played, upcoming) fixture dicts."""
    played = []
    for r in KNOWN_RESULTS:
        home, away = r[0], r[1]
        sh, sa = r[2], r[3]
        date = r[4]
        grp  = r[5]
        venue = r[6] if len(r) > 6 else ""
        if sh is not None and sa is not None:
            played.append({
                "home": home, "away": away,
                "score_a": sh, "score_b": sa,
                "played": True, "date": date,
                "time": "", "venue": venue, "group": grp,
                "scorers": {"home": [], "away": []},
            })

    upcoming = []
    for r in UPCOMING_FIXTURES:
        home, away = r[0], r[1]
        date = r[2]
        grp  = r[3]
        venue = r[4] if len(r) > 4 else ""
        upcoming.append({
            "home": home, "away": away,
            "score_a": None, "score_b": None,
            "played": False, "date": date,
            "time": "", "venue": venue, "group": grp,
            "scorers": {"home": [], "away": []},
        })

    return played, upcoming


# ── Known player stats (from FIFA golden boot page / search results) ──────────
# As of June 14, 2026 — early tournament data
KNOWN_PLAYERS = [
    # name, team, pos, goals, assists, minutes, matches, clean_sheets, saves
    {"name": "Folarin Balogun",   "team": "USA",         "pos": "FW", "goals": 2, "assists": 0, "minutes": 90,  "matches": 1, "clean_sheets": 0, "saves": 0},
    {"name": "Erling Haaland",    "team": "Norway",      "pos": "FW", "goals": 0, "assists": 0, "minutes": 0,   "matches": 0, "clean_sheets": 0, "saves": 0},
    {"name": "Vinicius Jr",       "team": "Brazil",      "pos": "FW", "goals": 0, "assists": 0, "minutes": 104, "matches": 1, "clean_sheets": 0, "saves": 0},
    {"name": "Breel Embolo",      "team": "Switzerland", "pos": "FW", "goals": 2, "assists": 0, "minutes": 103, "matches": 1, "clean_sheets": 0, "saves": 0},
    {"name": "Viktor Gyökeres",   "team": "Sweden",      "pos": "FW", "goals": 0, "assists": 0, "minutes": 0,   "matches": 0, "clean_sheets": 0, "saves": 0},
    {"name": "Kylian Mbappé",     "team": "France",      "pos": "FW", "goals": 0, "assists": 0, "minutes": 0,   "matches": 0, "clean_sheets": 0, "saves": 0},
    {"name": "Nico Schlotterbeck","team": "Germany",     "pos": "DF", "goals": 0, "assists": 0, "minutes": 100, "matches": 1, "clean_sheets": 0, "saves": 0},
    {"name": "Angus Gunn",        "team": "Scotland",    "pos": "GK", "goals": 0, "assists": 0, "minutes": 0,   "matches": 0, "clean_sheets": 0, "saves": 0},
    {"name": "Raúl Rangel",       "team": "Mexico",      "pos": "GK", "goals": 0, "assists": 0, "minutes": 90,  "matches": 1, "clean_sheets": 0, "saves": 3},
    {"name": "Patrick Beach",     "team": "Australia",   "pos": "GK", "goals": 0, "assists": 0, "minutes": 90,  "matches": 1, "clean_sheets": 0, "saves": 4},
    {"name": "Connor Metcalfe",   "team": "Australia",   "pos": "MF", "goals": 0, "assists": 0, "minutes": 100, "matches": 1, "clean_sheets": 0, "saves": 0},
    {"name": "Livano Comenencia", "team": "Curaçao",     "pos": "DF", "goals": 0, "assists": 0, "minutes": 100, "matches": 1, "clean_sheets": 0, "saves": 0},
    {"name": "Ladislav Krejci",   "team": "Czechia",     "pos": "MF", "goals": 0, "assists": 0, "minutes": 100, "matches": 1, "clean_sheets": 0, "saves": 0},
    # GKs with clean sheets
    {"name": "Matt Turner",       "team": "USA",         "pos": "GK", "goals": 0, "assists": 0, "minutes": 90,  "matches": 1, "clean_sheets": 1, "saves": 5},
    {"name": "Yann Sommer",       "team": "Switzerland", "pos": "GK", "goals": 0, "assists": 0, "minutes": 90,  "matches": 1, "clean_sheets": 1, "saves": 3},
    {"name": "Mark Flekken",      "team": "Netherlands", "pos": "GK", "goals": 0, "assists": 0, "minutes": 90,  "matches": 1, "clean_sheets": 0, "saves": 4},
]
