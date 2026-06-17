"""
template.py — Render the Jinja2 HTML template with all data.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def render(
    group_standings: dict,
    overall_table: list,
    bracket: dict,
    player_kpis: dict,
    played_fixtures: list,
    upcoming_fixtures: list,
    best_xi: dict,
    output_path: str,
):
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )

    # Add a custom 'get' filter for dict access in templates
    def dict_get(d, key, default=""):
        if isinstance(d, dict):
            return d.get(key, default)
        return default

    env.filters["get"] = dict_get

    template = env.get_template("dashboard.html")

    html = template.render(
        generated_at=datetime.now().strftime("%d %b %Y %H:%M UTC"),
        group_standings=group_standings,
        overall_table=overall_table,
        bracket=bracket,
        player_kpis=player_kpis,
        played_fixtures=played_fixtures,
        upcoming_fixtures=upcoming_fixtures,
        best_xi=best_xi,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard written to: {output_path}")
    return output_path
