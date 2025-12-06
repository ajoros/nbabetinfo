# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

`nbabetinfo` is a daily NBA betting analytics dashboard that scrapes game schedules and historical against-the-spread (ATS) performance data from TeamRankings.com and NBA.com to generate an HTML betting insights page. The system runs automatically via GitHub Actions and publishes to GitHub Pages.

## Core Architecture

### Data Pipeline Flow
The system operates in three distinct stages:

1. **Data Collection** (`scrape_ats_results.py`, `scrape_all_ats.py`)
   - Scrapes ATS results from TeamRankings.com for all 30 NBA teams
   - Extracts: date, home/away, opponent, spread, result, margin, ATS differential
   - Outputs: `ats_results_{team-slug}.csv` files

2. **Metric Calculation** (`calculate_ats_metrics.py`)
   - Processes CSV data to compute betting metrics for each team:
     - **TOTAL_DIFF**: Overall spread performance average
     - **FAV_DIFF**: Performance when favored (negative spread)
     - **DOG_DIFF**: Performance as underdog (positive spread)
     - **CRI**: Cover Rate Index (percentage of games covering spread)
   - These metrics split by role (favorite vs underdog) to identify situational value

3. **Page Generation** (`generate_nbabetinfo_page.py`)
   - Fetches today's games from TeamRankings sidebar
   - Refreshes ATS data for teams playing today
   - Generates performance plots via `generate_ats_plots.py`
   - Renders `index.html` with metrics table and charts

### Key Design Patterns

**Team Name Mapping**: NBA API uses variations ("LA Lakers", "LA Clippers") that must be mapped to TeamRankings slugs. The canonical mapping lives in `TEAM_NAME_TO_SLUG` in `generate_nbabetinfo_page.py`.

**Spread Conventions**: Negative spread = favorite, positive = underdog. This convention is used throughout for role-based metric calculation.

**Timezone Handling**: All game times converted from Eastern Time to Pacific Time using `zoneinfo.ZoneInfo`.

**Subprocess Pattern**: `scrape_all_ats.py` and `generate_nbabetinfo_page.py` invoke scrapers via subprocess to refresh data, ensuring up-to-date metrics.

## Common Commands

### Development Workflow

```bash
# Install dependencies
pip install -r requirements.txt

# Scrape ATS data for all teams (takes 2-3 minutes)
python scrape_all_ats.py

# Scrape single team
python scrape_ats_results.py --team-slug oklahoma-city-thunder

# Calculate and display team metrics/rankings
python calculate_ats_metrics.py

# Generate today's betting page (includes auto-refresh of teams playing today)
python generate_nbabetinfo_page.py

# Generate plot for single team (for testing)
python generate_ats_plots.py boston-celtics
```

### Testing Changes

```bash
# Test full pipeline locally
python scrape_all_ats.py && python generate_nbabetinfo_page.py

# Open generated page
open index.html
```

### GitHub Actions

The workflow `.github/workflows/nbabetinfo.yml` runs hourly and can be triggered manually via GitHub UI (Actions → NBA Betting Info Page → Run workflow).

## Development Guidelines

### When Adding New Teams
Update the `NBA_TEAMS` list in `scrape_all_ats.py` and `TEAM_NAME_TO_SLUG` mapping in `generate_nbabetinfo_page.py`. Both dictionaries must stay in sync.

### When Modifying Metrics
Metric calculation logic lives in `calculate_ats_metrics.py:calculate_team_ats_metrics()`. Any new metrics should:
- Be computed from the `ats_diff`, `spread`, and `result` fields in CSV
- Return values in the metrics dictionary
- Be documented in README.md metric definitions

### When Changing HTML/Styling
The entire HTML template is string-formatted in `generate_nbabetinfo_page.py:render_html()`. The inline CSS is designed for dark mode and responsive mobile layout. Color coding:
- Blue highlight: Metric relevant to today's role (fav/dog)
- Green: Strong positive indicators (good favorite or value underdog)
- Red: Warning signals (poor underdog performance)

### When Web Scraping Breaks
TeamRankings structure changes will break scrapers. Check:
1. `scrape_ats_results.py:find_ats_table()` - looks for table with date/opponent/line/diff columns
2. `generate_nbabetinfo_page.py:fetch_todays_games_from_teamrankings()` - parses sidebar matchups using regex pattern for "Team (spread) at Team (spread)"

The scraper includes a polite User-Agent header and 15-second timeout.

### Working with Matplotlib Plots
`generate_ats_plots.py` uses `matplotlib.use('Agg')` backend for headless rendering (GitHub Actions). Always set this before importing pyplot. Plots are saved to `plots/` directory and referenced in HTML as relative paths.

## File Organization

```
nbabetinfo/
├── scrape_ats_results.py        # Core scraper for single team
├── scrape_all_ats.py            # Batch scraper for all 30 teams
├── calculate_ats_metrics.py     # Metric calculation and rankings
├── generate_ats_plots.py        # Matplotlib visualization generation
├── generate_nbabetinfo_page.py  # Main pipeline orchestrator
├── ats_results_*.csv            # ATS data for each team (30 files)
├── index.html                   # Generated betting page
├── plots/                       # Generated PNG charts
│   └── ats_*.png
└── .github/workflows/
    └── nbabetinfo.yml          # Hourly automated deployment

Documentation:
├── README.md                    # User-facing: metrics explained, how it works
├── USAGE.md                     # Developer-facing: command reference
└── WARP.md                      # This file
```

## Dependencies

Core libraries (see `requirements.txt`):
- `requests` - HTTP requests for scraping
- `beautifulsoup4` - HTML parsing for TeamRankings pages
- `matplotlib` - Chart generation (uses Agg backend)
- `numpy` - Numerical operations for plot stats

Python 3.9+ required for `zoneinfo` module (timezone handling).

## Deployment

The system auto-deploys via GitHub Actions to GitHub Pages. The workflow:
1. Runs hourly via cron schedule
2. Executes `generate_nbabetinfo_page.py` (which internally refreshes today's team data)
3. Commits `index.html`, `plots/`, and updated CSV files
4. GitHub Pages serves from repo root (index.html)

Manual deployment: Push to `main` branch or trigger via Actions UI.

## Important Notes

**Data Freshness**: ATS CSVs are only refreshed for teams playing today during page generation. To get full season data for all teams, run `scrape_all_ats.py` manually.

**Rate Limiting**: `scrape_all_ats.py` makes 30 sequential HTTP requests. No explicit delays, but be mindful of TeamRankings load.

**No Tests**: This codebase has no automated tests. Verify changes by running the full pipeline and inspecting `index.html` output.

**TeamRankings Dependency**: This project depends on TeamRankings.com HTML structure. If scrapers break, check if the site layout changed before debugging code.
