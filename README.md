# ⚽ FIFA World Cup 2026 — Live Dashboard

A Python dashboard that scrapes live World Cup 2026 data from Wikipedia and renders it as a single self-contained HTML file you can open in any browser.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

| Tab | What it shows |
|-----|---------------|
| 🏟 **Group Standings** | All 12 groups (A–L) with live points, GD, goals, colour-coded qualification status |
| 📊 **Overall Table** | All 48 teams ranked across groups by pts → GD → GF → GA → fair play |
| 🏆 **Knockout Bracket** | Round of 32 → Final, projected from current standings |
| 👤 **Players** | 8 KPI cards + Top 5 tables (goals, assists, clean sheets, saves…) with full table toggle |
| 📅 **Fixtures** | All played results and upcoming matches |
| ⭐ **Best XI** | 4-3-3 tactics board selected by stats (GK: saves + CS · DEF: CS + goals/assists · MID/FWD: goals + assists) |

---

## Quick Start

### 1. Install dependencies

```bash
pip install requests beautifulsoup4 pandas jinja2 lxml
```

### 2. Run

```bash
python main.py
```

Open `world_cup_2026.html` in your browser. That's it.

### Options

```bash
python main.py                        # full live scrape from Wikipedia
python main.py --static-only          # instant render, no network needed
python main.py --no-players           # skip player stats (faster)
python main.py --output my_file.html  # custom output path
```

---

## How it works

```
main.py          ← orchestrator: scrape → process → render
scraper.py       ← polite Wikipedia scraper (1.5s delays, User-Agent, retry/backoff)
static_data.py   ← fallback data (all 48 teams, known results, early player stats)
standings.py     ← group sorting + 3rd-place ranking + overall table
knockout.py      ← bracket builder from standings
players.py       ← KPI computation + Best XI selection
fixtures.py      ← match parser
template.py      ← Jinja2 renderer
templates/
  dashboard.html ← full HTML/CSS/JS template (all 6 tabs)
```

### Scraping policy

This project follows [Wikimedia's robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy):

- Only fetches `/wiki/` article pages (allowed by `robots.txt`)
- Identifies itself with a descriptive `User-Agent`
- Enforces a **1.5 second minimum delay** between every request
- Sequential requests only (concurrency = 1)
- Exponential back-off on `429` / `5xx` responses
- Falls back gracefully to static data if Wikipedia is unreachable

---

## GitHub Pages (live version)

The `wc2026_live.html` file in this repo is a **standalone browser app** that needs no Python or server. It calls the Anthropic API directly to fetch live WC2026 data.

### Deploy to GitHub Pages

1. Push this repo to GitHub
2. Go to **Settings → Pages**
3. Set source to `main` branch, root folder
4. Your dashboard will be live at `https://<your-username>.github.io/<repo-name>/wc2026_live.html`

When you open it, enter your [Anthropic API key](https://console.anthropic.com) to load live data.

> **Cost:** ~$0.01–0.03 per full refresh (4 API calls to Claude Sonnet). A $5 credit covers hundreds of sessions.

---

## Qualifying rules implemented

- **Positions 1 & 2** per group → automatic qualification (24 teams)
- **Best 8 of 12 third-place teams** qualify by: pts → GD → GF → GA → fair play
- Total: **32 teams** in the Round of 32

### Tiebreaker order (within group)

1. Points
2. Goal difference
3. Goals scored
4. Goals conceded
5. Fair play (yellow cards, red cards)
6. Alphabetical (for unplayed groups)

### Best XI selection weights

| Position | Formula |
|----------|---------|
| GK | `clean_sheets × 3 + saves × 0.3` |
| DF | `clean_sheets × 2 + goals × 1.5 + assists` |
| MF | `goals × 2 + assists × 1.5` |
| FW | `goals × 2.5 + assists` |

---

## Requirements

- Python 3.10+
- `requests`, `beautifulsoup4`, `pandas`, `jinja2`, `lxml`

---

## License

MIT — free to use, modify, and share.
