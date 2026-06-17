"""
players.py — Player KPIs, stat leaders, and Best XI selection.

Best XI selection weights:
  GK:  clean_sheets * 3 + saves * 0.3
  DEF: clean_sheets * 2 + goals * 1.5 + assists * 1.0
  MID: goals * 2.0  + assists * 1.5
  FWD: goals * 2.5  + assists * 1.0
"""

from __future__ import annotations


# ── KPI builders ──────────────────────────────────────────────────────────────

def compute_kpis(players: list[dict], squads: list[dict]) -> dict:
    """
    Merge squad position data into player stats and compute all KPIs.
    Returns a dict with keys for each KPI, each containing:
      {value, top5: [...], full: [...]}
    """
    # Merge position from squads if not already set
    squad_pos = {(p["name"].lower(), p["team"].lower()): p["pos"] for p in squads}
    squad_pos_by_name = {p["name"].lower(): p["pos"] for p in squads}

    for p in players:
        if not p.get("pos") or p["pos"] in ("", "?"):
            key = (p["name"].lower(), p.get("team", "").lower())
            p["pos"] = (
                squad_pos.get(key)
                or squad_pos_by_name.get(p["name"].lower())
                or "?"
            )

    # Filter: only players with minutes played
    active = [p for p in players if p.get("minutes", 0) > 0 or p.get("matches", 0) > 0]
    if not active:
        active = players  # fallback

    kpis = {}

    # 1. Players with minutes played
    with_minutes = [p for p in active if p.get("minutes", 0) > 0]
    kpis["players_with_minutes"] = {
        "label":   "Players with Minutes",
        "icon":    "⏱️",
        "value":   len(with_minutes),
        "unit":    "players",
        "top5":    _top5_by(with_minutes, key="minutes", tie_asc="minutes",
                            desc_label="Min", reverse=True),
        "full":    _sort_by(with_minutes, key="minutes", reverse=True),
        "show_col": "minutes",
    }

    # 2. Goals scored
    scorers = [p for p in active if p.get("goals", 0) > 0]
    kpis["goals_scored"] = {
        "label":   "Goals Scored (top scorer)",
        "icon":    "⚽",
        "value":   sum(p.get("goals", 0) for p in active),
        "unit":    "goals total",
        "top5":    _top5_by(scorers, key="goals", tie_asc="minutes",
                            desc_label="Gls", reverse=True),
        "full":    _sort_by(scorers, key="goals", reverse=True),
        "show_col": "goals",
    }

    # 3. Unique goalscorers (tie: fewer minutes first)
    kpis["unique_scorers"] = {
        "label":   "Different Goalscorers",
        "icon":    "🎯",
        "value":   len(scorers),
        "unit":    "players",
        "top5":    _top5_by(scorers, key="goals", tie_asc="minutes",
                            desc_label="Gls", reverse=True),
        "full":    _sort_by(scorers, key="goals", reverse=True),
        "show_col": "goals",
    }

    # 4. Players scoring more than 1 goal
    multi_scorers = [p for p in active if p.get("goals", 0) > 1]
    kpis["multi_scorers"] = {
        "label":   "Players with 2+ Goals",
        "icon":    "🔥",
        "value":   len(multi_scorers),
        "unit":    "players",
        "top5":    _top5_by(multi_scorers, key="goals", tie_asc="minutes",
                            desc_label="Gls", reverse=True),
        "full":    _sort_by(multi_scorers, key="goals", reverse=True),
        "show_col": "goals",
    }

    # 5. Assists (tie: fewer minutes first)
    assisters = [p for p in active if p.get("assists", 0) > 0]
    kpis["assists"] = {
        "label":   "Top Assist Provider",
        "icon":    "🅰️",
        "value":   sum(p.get("assists", 0) for p in active),
        "unit":    "assists total",
        "top5":    _top5_by(assisters, key="assists", tie_asc="minutes",
                            desc_label="Ast", reverse=True),
        "full":    _sort_by(assisters, key="assists", reverse=True),
        "show_col": "assists",
    }

    # 6. Players with 2+ assists
    multi_assisters = [p for p in active if p.get("assists", 0) > 1]
    kpis["multi_assisters"] = {
        "label":   "Players with 2+ Assists",
        "icon":    "✨",
        "value":   len(multi_assisters),
        "unit":    "players",
        "top5":    _top5_by(multi_assisters, key="assists", tie_asc="minutes",
                            desc_label="Ast", reverse=True),
        "full":    _sort_by(multi_assisters, key="assists", reverse=True),
        "show_col": "assists",
    }

    # 7. GK clean sheets (tie: more matches first)
    gks = [p for p in active if p.get("pos", "").upper() in ("GK", "G", "GOALKEEPER")]
    gks_with_cs = [p for p in gks if p.get("clean_sheets", 0) > 0]
    if not gks_with_cs:
        # fall back to everyone with clean_sheets data
        gks_with_cs = [p for p in active if p.get("clean_sheets", 0) > 0]
    kpis["gk_clean_sheets"] = {
        "label":   "GK Clean Sheets",
        "icon":    "🧤",
        "value":   len(gks_with_cs),
        "unit":    "GKs with clean sheet",
        "top5":    _top5_by(gks_with_cs, key="clean_sheets", tie_asc=None,
                            tie_desc="matches", desc_label="CS", reverse=True),
        "full":    _sort_by(gks_with_cs, key="clean_sheets", reverse=True),
        "show_col": "clean_sheets",
    }

    # 8. Saves (bonus KPI)
    savers = [p for p in active if p.get("saves", 0) > 0]
    kpis["gk_saves"] = {
        "label":   "Most Saves (GK)",
        "icon":    "🙌",
        "value":   max((p.get("saves", 0) for p in savers), default=0),
        "unit":    "saves (leader)",
        "top5":    _top5_by(savers, key="saves", tie_asc="minutes",
                            desc_label="Saves", reverse=True),
        "full":    _sort_by(savers, key="saves", reverse=True),
        "show_col": "saves",
    }

    return kpis


def _top5_by(players: list[dict], key: str, tie_asc: str | None,
             desc_label: str, reverse: bool = True,
             tie_desc: str | None = None) -> list[dict]:
    def sort_key(p):
        primary = p.get(key, 0)
        if tie_asc:
            secondary = p.get(tie_asc, 0)
            return (-primary if reverse else primary, secondary)
        elif tie_desc:
            secondary = -p.get(tie_desc, 0)
            return (-primary if reverse else primary, secondary)
        return (-primary if reverse else primary,)

    ranked = sorted(players, key=sort_key)
    result = []
    for i, p in enumerate(ranked[:5]):
        result.append({
            "rank":  i + 1,
            "name":  p.get("name", ""),
            "team":  p.get("team", ""),
            "pos":   p.get("pos", ""),
            "value": p.get(key, 0),
            "label": desc_label,
            "minutes": p.get("minutes", 0),
            "matches": p.get("matches", 0),
        })
    return result


def _sort_by(players: list[dict], key: str, reverse: bool = True) -> list[dict]:
    return sorted(players, key=lambda p: p.get(key, 0), reverse=reverse)


# ── Best XI ───────────────────────────────────────────────────────────────────

POSITION_GROUPS = {
    "GK": ["GK"],
    "DF": ["DF", "DEF", "CB", "LB", "RB", "D"],
    "MF": ["MF", "MID", "CM", "DM", "AM", "CDM", "CAM", "M"],
    "FW": ["FW", "FWD", "ST", "CF", "LW", "RW", "F"],
}


def gk_score(p: dict) -> float:
    return p.get("clean_sheets", 0) * 3 + p.get("saves", 0) * 0.3


def def_score(p: dict) -> float:
    return (
        p.get("clean_sheets", 0) * 2.0
        + p.get("goals", 0) * 1.5
        + p.get("assists", 0) * 1.0
    )


def mid_score(p: dict) -> float:
    return (
        p.get("goals", 0) * 2.0
        + p.get("assists", 0) * 1.5
    )


def fwd_score(p: dict) -> float:
    return (
        p.get("goals", 0) * 2.5
        + p.get("assists", 0) * 1.0
    )


def _classify(p: dict) -> str:
    """Return GK / DF / MF / FW based on pos field."""
    raw = p.get("pos", "").upper().strip()
    for group, aliases in POSITION_GROUPS.items():
        if raw in aliases or raw == group:
            return group
    # Guess from name patterns if pos is unknown
    return "?"


def select_best_xi(players: list[dict], squads: list[dict]) -> dict:
    """
    Select Best XI in a 4-3-3 formation.
    Returns dict: {gk, defenders: [4], midfielders: [3], forwards: [3]}
    """
    # Merge squad positions
    squad_pos_name = {p["name"].lower(): p["pos"] for p in squads}
    for p in players:
        if not p.get("pos") or p["pos"] == "?":
            p["pos"] = squad_pos_name.get(p["name"].lower(), "?")

    # Classify
    gks  = [p for p in players if _classify(p) == "GK"]
    defs = [p for p in players if _classify(p) == "DF"]
    mids = [p for p in players if _classify(p) == "MF"]
    fwds = [p for p in players if _classify(p) == "FW"]

    # Score and pick
    best_gk = sorted(gks,  key=gk_score,  reverse=True)[:1]
    best_df = sorted(defs, key=def_score, reverse=True)[:4]
    best_mf = sorted(mids, key=mid_score, reverse=True)[:3]
    best_fw = sorted(fwds, key=fwd_score, reverse=True)[:3]

    # Pad with "?" entries if not enough positional data
    def pad(lst, n, pos_label):
        while len(lst) < n:
            lst.append({"name": "TBD", "team": "—", "pos": pos_label,
                        "goals": 0, "assists": 0, "clean_sheets": 0, "saves": 0})
        return lst[:n]

    return {
        "gk":          pad(best_gk, 1, "GK")[0],
        "defenders":   pad(best_df, 4, "DF"),
        "midfielders": pad(best_mf, 3, "MF"),
        "forwards":    pad(best_fw, 3, "FW"),
        "formation":   "4-3-3",
    }
