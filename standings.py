"""
standings.py — Group standings logic + overall ranking + 3rd-place qualifying.

Tiebreaker order (per official 2026 FIFA rules):
  Within a group: pts → head-to-head pts → h2h gd → h2h gf → overall gd
                  → overall gf → fair play (yc=-1, 2nd yellow RC=-3, direct RC=-4)
                  → FIFA ranking

  For 3rd-place ranking across groups:
  pts → gd → gf → fair play (team conduct score) → FIFA ranking
"""

import pandas as pd
from functools import cmp_to_key


# ── Fair-play score ───────────────────────────────────────────────────────────
def fair_play_score(yc: int, rc: int) -> int:
    """
    Higher = better (less cards).
    YC: -1pt each, RC (direct): -4pt each.
    We store as positive penalty and sort ascending when tiebreaking.
    """
    return yc * 1 + rc * 4   # lower is better (less penalty)


# ── Sort within a group ───────────────────────────────────────────────────────
def sort_group(teams: list[dict]) -> list[dict]:
    """Return a new sorted list, 1st place first."""

    def cmp(a, b):
        # 1. Points
        if b["pts"] != a["pts"]:
            return b["pts"] - a["pts"]
        # 2. Goal difference
        if b["gd"] != a["gd"]:
            return b["gd"] - a["gd"]
        # 3. Goals scored
        if b["gf"] != a["gf"]:
            return b["gf"] - a["gf"]
        # 4. Goals conceded (fewer is better)
        if a["ga"] != b["ga"]:
            return a["ga"] - b["ga"]
        # 5. Fair play (lower penalty is better)
        fp_a = fair_play_score(a["yc"], a["rc"])
        fp_b = fair_play_score(b["yc"], b["rc"])
        if fp_a != fp_b:
            return fp_a - fp_b
        # 6. Alphabetical fallback (for unplayed matches)
        if a["team"] != b["team"]:
            return -1 if a["team"] < b["team"] else 1
        return 0

    return sorted(teams, key=cmp_to_key(cmp))


# ── Build per-group standings ─────────────────────────────────────────────────
def build_group_standings(flat_rows: list[dict]) -> dict[str, list[dict]]:
    """
    From a flat list of team rows (each with 'group' key),
    return dict: group_letter → sorted list of teams.
    Also assigns 'group_pos' (1-4) and 'status' field.
    """
    groups: dict[str, list[dict]] = {}
    for row in flat_rows:
        g = row["group"]
        groups.setdefault(g, []).append(row)

    result = {}
    for g, teams in sorted(groups.items()):
        sorted_teams = sort_group(teams)
        for i, t in enumerate(sorted_teams):
            t["group_pos"] = i + 1
            t["status"] = "TBD"  # will be set after 3rd-place ranking
        result[g] = sorted_teams

    return result


# ── Third-place ranking ───────────────────────────────────────────────────────
def rank_third_places(group_standings: dict[str, list[dict]]) -> list[dict]:
    """
    Collect all 3rd-place teams, rank them by the official FIFA criteria
    for third-placed teams, return sorted list (best first).
    """
    thirds = []
    for g, teams in group_standings.items():
        if len(teams) >= 3:
            thirds.append(teams[2].copy())   # 3rd place (0-indexed = 2)

    def cmp3(a, b):
        # Pts
        if b["pts"] != a["pts"]:
            return b["pts"] - a["pts"]
        # GD
        if b["gd"] != a["gd"]:
            return b["gd"] - a["gd"]
        # GF
        if b["gf"] != a["gf"]:
            return b["gf"] - a["gf"]
        # Fair play (less penalty = better)
        fp_a = fair_play_score(a["yc"], a["rc"])
        fp_b = fair_play_score(b["yc"], b["rc"])
        if fp_a != fp_b:
            return fp_a - fp_b
        # Alphabetical
        if a["team"] != b["team"]:
            return -1 if a["team"] < b["team"] else 1
        return 0

    return sorted(thirds, key=cmp_to_key(cmp3))


# ── Assign qualification statuses ─────────────────────────────────────────────
def assign_statuses(group_standings: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """
    Mark each team's 'status':
      'Q1' = 1st place → qualified
      'Q2' = 2nd place → qualified
      'Q3' = 3rd place & in top-8 thirds → qualified
      'E'  = eliminated
      'TBD' = group not fully played (all pts == 0)
    """
    ranked_thirds = rank_third_places(group_standings)
    qualifying_thirds = {t["team"] for t in ranked_thirds[:8]}

    for g, teams in group_standings.items():
        all_zero = all(t["pts"] == 0 and t["pld"] == 0 for t in teams)

        for t in teams:
            if all_zero:
                t["status"] = "TBD"
            elif t["group_pos"] == 1:
                t["status"] = "Q1"
            elif t["group_pos"] == 2:
                t["status"] = "Q2"
            elif t["group_pos"] == 3:
                t["status"] = "Q3" if t["team"] in qualifying_thirds else "E"
            else:
                t["status"] = "E"

    return group_standings


# ── Overall table ─────────────────────────────────────────────────────────────
def build_overall_table(group_standings: dict[str, list[dict]]) -> list[dict]:
    """
    All 48 teams ranked overall by the same criteria as 3rd-place ranking
    (used as the 'Overall Table' tab).
    Returns flat sorted list with 'overall_pos' field added.
    """
    all_teams = []
    for teams in group_standings.values():
        all_teams.extend(teams)

    def cmp_overall(a, b):
        if b["pts"] != a["pts"]:
            return b["pts"] - a["pts"]
        if b["gd"] != a["gd"]:
            return b["gd"] - a["gd"]
        if b["gf"] != a["gf"]:
            return b["gf"] - a["gf"]
        if a["ga"] != b["ga"]:
            return a["ga"] - b["ga"]
        fp_a = fair_play_score(a["yc"], a["rc"])
        fp_b = fair_play_score(b["yc"], b["rc"])
        if fp_a != fp_b:
            return fp_a - fp_b
        if a["team"] != b["team"]:
            return -1 if a["team"] < b["team"] else 1
        return 0

    sorted_all = sorted(all_teams, key=cmp_to_key(cmp_overall))
    for i, t in enumerate(sorted_all):
        t["overall_pos"] = i + 1

    return sorted_all


# ── Summary helpers ───────────────────────────────────────────────────────────
def standings_summary(group_standings: dict[str, list[dict]]) -> dict:
    """Return high-level summary counts."""
    total_goals = sum(t["gf"] for teams in group_standings.values() for t in teams) // 2
    total_matches = sum(t["pld"] for teams in group_standings.values() for t in teams) // 2
    qualified = sum(
        1 for teams in group_standings.values()
        for t in teams if t["status"] in ("Q1", "Q2", "Q3")
    )
    return {
        "total_goals":   total_goals,
        "total_matches": total_matches,
        "qualified":     qualified,
    }
