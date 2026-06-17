#!/usr/bin/env python3
"""
main.py — World Cup 2026 Dashboard Generator
============================================
Usage:
    python main.py                    # full scrape + render
    python main.py --static-only      # skip scraping, use static data only
    python main.py --no-players       # skip player stats scraping
    python main.py --output out.html  # custom output path

Scraping rules observed:
  - Wikipedia article pages only (/wiki/ namespace, allowed by robots.txt)
  - Polite User-Agent identifying this script
  - 1.5s minimum delay between all requests (Wikimedia policy)
  - Sequential requests only (concurrency = 1)
  - Exponential back-off on 5xx / 429 responses
  - Falls back gracefully to static data if scraping is unavailable
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scraper import (
    scrape_all_groups,
    scrape_player_stats,
    scrape_squads,
    _fetch_wiki_html,
)
from static_data import (
    GROUPS as STATIC_GROUPS,
    KNOWN_PLAYERS,
    build_standings_from_results,
    get_fixtures_list,
)
from standings import (
    build_group_standings,
    assign_statuses,
    rank_third_places,
    build_overall_table,
    standings_summary,
)
from knockout import build_bracket
from players import compute_kpis, select_best_xi
from fixtures import parse_fixtures_from_soup, split_played_upcoming
from template import render

DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "world_cup_2026.html")


def parse_args():
    p = argparse.ArgumentParser(description="WC2026 Dashboard Generator")
    p.add_argument("--static-only",  action="store_true", help="Use static data (no scraping)")
    p.add_argument("--no-players",   action="store_true", help="Skip player stats scraping")
    p.add_argument("--no-fixtures",  action="store_true", help="Skip fixture scraping")
    p.add_argument("--no-squads",    action="store_true", help="Skip squad scraping")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help="Output HTML file path")
    return p.parse_args()


def build_fallback_rows(stats_dict: dict) -> list[dict]:
    """Convert static_data standings dict to flat list of team rows."""
    rows = []
    for g, teams in stats_dict.items():
        for t in teams.values():
            rows.append(t)
    return rows


def build_empty_best_xi() -> dict:
    def empty(pos, n):
        return [{"name": "TBD", "team": "—", "pos": pos,
                 "goals": 0, "assists": 0, "clean_sheets": 0, "saves": 0}
                for _ in range(n)]
    return {
        "gk":          empty("GK", 1)[0],
        "defenders":   empty("DF", 4),
        "midfielders": empty("MF", 3),
        "forwards":    empty("FW", 3),
        "formation":   "4-3-3",
    }


def main():
    args = parse_args()
    print("=" * 60)
    print("  FIFA World Cup 2026 Dashboard Generator")
    print("=" * 60)

    # ── 1. Group standings ────────────────────────────────────────
    print("\n[1/5] Building group standings …")
    flat_rows = []
    scraped_ok = False

    if not args.static_only:
        print("  Attempting live scrape from Wikipedia …")
        try:
            flat_rows = scrape_all_groups()
            # Check if any real data came back (not all zeros)
            if any(r["pld"] > 0 for r in flat_rows):
                scraped_ok = True
                print("  ✓ Live data obtained!")
            else:
                print("  Scraping returned zero matches — falling back to static data")
        except Exception as exc:
            print(f"  Scrape failed ({exc}) — falling back to static data")

    if not scraped_ok:
        print("  Using static data (known results as of June 14, 2026)")
        static_stats = build_standings_from_results()
        flat_rows = build_fallback_rows(static_stats)

    group_standings = build_group_standings(flat_rows)
    group_standings = assign_statuses(group_standings)
    ranked_thirds   = rank_third_places(group_standings)
    overall_table   = build_overall_table(group_standings)
    summary         = standings_summary(group_standings)

    print(f"  Groups:        {len(group_standings)}/12")
    print(f"  Teams loaded:  {len(flat_rows)}")
    print(f"  Total goals:   {summary['total_goals']}")
    print(f"  Matches played:{summary['total_matches']}")
    print(f"  Qualified:     {summary['qualified']}/32")

    # ── 2. Knockout bracket ───────────────────────────────────────
    print("\n[2/5] Building knockout bracket …")
    bracket = build_bracket(group_standings, ranked_thirds)
    print(f"  R32 slots: {len(bracket['r32'])} | R16: {len(bracket['r16'])} | QF: {len(bracket['qf'])}")

    # ── 3. Fixtures ───────────────────────────────────────────────
    played_fixtures   = []
    upcoming_fixtures = []

    if not args.no_fixtures:
        print("\n[3/5] Loading fixtures …")
        fixture_scraped = False

        if not args.static_only:
            try:
                soup = _fetch_wiki_html("2026_FIFA_World_Cup_group_stage")
                all_fx = parse_fixtures_from_soup(soup)
                pf, uf = split_played_upcoming(all_fx)
                if pf or uf:
                    played_fixtures, upcoming_fixtures = pf, uf
                    fixture_scraped = True
                    print(f"  ✓ Live: {len(played_fixtures)} played, {len(upcoming_fixtures)} upcoming")
            except Exception as exc:
                print(f"  Fixture scrape failed ({exc})")

        if not fixture_scraped:
            played_fixtures, upcoming_fixtures = get_fixtures_list()
            print(f"  Static: {len(played_fixtures)} played, {len(upcoming_fixtures)} upcoming")
    else:
        print("\n[3/5] Fixtures skipped (--no-fixtures)")

    # ── 4. Player stats ───────────────────────────────────────────
    player_kpis = None
    best_xi     = None

    if not args.no_players:
        print("\n[4/5] Loading player stats …")
        players = []
        squads  = []
        player_scraped = False

        if not args.static_only:
            try:
                players = scrape_player_stats()
                if players:
                    player_scraped = True
                    print(f"  ✓ Live player records: {len(players)}")
            except Exception as exc:
                print(f"  Player scrape failed ({exc})")

        if not player_scraped:
            players = [dict(p) for p in KNOWN_PLAYERS]
            print(f"  Static player records: {len(players)}")

        if not args.no_squads and not args.static_only:
            try:
                squads = scrape_squads()
                print(f"  Squad records: {len(squads)}")
            except Exception as exc:
                print(f"  Squad scrape failed ({exc})")

        if players:
            try:
                player_kpis = compute_kpis(players, squads)
                best_xi     = select_best_xi(players, squads)
                print(f"  KPIs computed: {len(player_kpis)}")
            except Exception as exc:
                print(f"  KPI computation error: {exc}")
                import traceback; traceback.print_exc()
    else:
        print("\n[4/5] Player stats skipped (--no-players)")

    # Defaults if still None
    if player_kpis is None:
        player_kpis = {}
    if best_xi is None:
        best_xi = build_empty_best_xi()

    # ── 5. Render ─────────────────────────────────────────────────
    print(f"\n[5/5] Rendering HTML …")
    render(
        group_standings   = group_standings,
        overall_table     = overall_table,
        bracket           = bracket,
        player_kpis       = player_kpis,
        played_fixtures   = played_fixtures,
        upcoming_fixtures = upcoming_fixtures,
        best_xi           = best_xi,
        output_path       = args.output,
    )

    data_note = "live Wikipedia" if scraped_ok else "static data (run on your machine for live scraping)"
    print(f"\n{'=' * 60}")
    print(f"  ✅ Done!  Data source: {data_note}")
    print(f"  Open in browser: {os.path.abspath(args.output)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
