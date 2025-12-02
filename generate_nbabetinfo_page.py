#!/usr/bin/env python3
"""
Generate a static HTML page with today's NBA games, start times in Pacific Time,
and betting metrics (SPI, AVI, CRI, TPI) for each team.

Intended to be run daily (e.g., from GitHub Actions) before the day's games.
The page can be hosted via GitHub Pages.
"""

import csv
import sys
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests

from zoneinfo import ZoneInfo  # Python 3.9+

from calculate_ats_metrics import calculate_team_ats_metrics
from generate_ats_plots import generate_plots_for_teams

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("WARNING: BeautifulSoup not available. Spreads will not be displayed.", file=sys.stderr)

# Mapping from NBA API "city name" + "team name" to TeamRankings team slug
TEAM_NAME_TO_SLUG: Dict[str, str] = {
    "Atlanta Hawks": "atlanta-hawks",
    "Boston Celtics": "boston-celtics",
    "Brooklyn Nets": "brooklyn-nets",
    "Charlotte Hornets": "charlotte-hornets",
    "Chicago Bulls": "chicago-bulls",
    "Cleveland Cavaliers": "cleveland-cavaliers",
    "Dallas Mavericks": "dallas-mavericks",
    "Denver Nuggets": "denver-nuggets",
    "Detroit Pistons": "detroit-pistons",
    "Golden State Warriors": "golden-state-warriors",
    "Houston Rockets": "houston-rockets",
    "Indiana Pacers": "indiana-pacers",
    "Los Angeles Clippers": "los-angeles-clippers",
    "Los Angeles Lakers": "los-angeles-lakers",
    "Memphis Grizzlies": "memphis-grizzlies",
    "Miami Heat": "miami-heat",
    "Milwaukee Bucks": "milwaukee-bucks",
    "Minnesota Timberwolves": "minnesota-timberwolves",
    "New Orleans Pelicans": "new-orleans-pelicans",
    "New York Knicks": "new-york-knicks",
    "Oklahoma City Thunder": "oklahoma-city-thunder",
    "Orlando Magic": "orlando-magic",
    "Philadelphia 76ers": "philadelphia-76ers",
    "Phoenix Suns": "phoenix-suns",
    "Portland Trail Blazers": "portland-trail-blazers",
    "Sacramento Kings": "sacramento-kings",
    "San Antonio Spurs": "san-antonio-spurs",
    "Toronto Raptors": "toronto-raptors",
    "Utah Jazz": "utah-jazz",
    "Washington Wizards": "washington-wizards",
}


NBA_SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
TEAMRANKINGS_NBA_URL = "https://www.teamrankings.com/nba/"


@dataclass
class TeamInfo:
    label: str  # e.g. "Boston Celtics"
    slug: Optional[str]  # TeamRankings slug, if known
    metrics: Optional[Dict]  # SPI/AVI/CRI/TPI dict from calculate_team_metrics
    spread: Optional[str] = None  # Today's spread, e.g. "-13.5" or "+5.5"


@dataclass
class GameInfo:
    game_id: str
    start_time_pt: datetime
    away: TeamInfo
    home: TeamInfo


def fetch_todays_spreads() -> Dict[str, Dict[str, str]]:
    """Fetch today's spreads from TeamRankings.com.
    
    Returns dict mapping team labels to their spread info:
    {"Boston Celtics": {"spread": "-1.5", "is_home": True}, ...}
    """
    if not HAS_BS4:
        return {}
    
    try:
        resp = requests.get(TEAMRANKINGS_NBA_URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"WARNING: Failed to fetch spreads from TeamRankings: {e}", file=sys.stderr)
        return {}
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    spreads = {}
    
    # Find the matchups section in the right sidebar
    matchup_links = soup.select('aside.right-sidebar table.tr-table a')
    
    for link in matchup_links:
        text = link.get_text(strip=True)
        # Examples:
        # "Washington at Philadelphia (-13.5)"
        # "Minnesota (-11.5) at New Orleans"
        
        import re
        # Pattern to extract teams and spread
        # Look for "Team1 at Team2 (-X.X)" or "Team1 (-X.X) at Team2"
        match = re.search(r'(.+?)\s+(?:\(([+-]?[\d.]+)\)\s+)?at\s+(.+?)(?:\s+\(([+-]?[\d.]+)\))?$', text)
        
        if match:
            away_team = match.group(1).strip()
            away_spread = match.group(2)  # Could be None
            home_team = match.group(3).strip()
            home_spread = match.group(4)  # Could be None
            
            # Normalize team names to match our TEAM_NAME_TO_SLUG keys
            # Map short names to full names
            team_name_map = {
                "Washington": "Washington Wizards",
                "Philadelphia": "Philadelphia 76ers",
                "Portland": "Portland Trail Blazers",
                "Toronto": "Toronto Raptors",
                "Memphis": "Memphis Grizzlies",
                "San Antonio": "San Antonio Spurs",
                "New York": "New York Knicks",
                "Boston": "Boston Celtics",
                "Minnesota": "Minnesota Timberwolves",
                "New Orleans": "New Orleans Pelicans",
                "Okla City": "Oklahoma City Thunder",
                "Golden State": "Golden State Warriors",
            }
            
            away_full = team_name_map.get(away_team, away_team)
            home_full = team_name_map.get(home_team, home_team)
            
            # Determine spreads
            if home_spread:
                spreads[home_full] = {"spread": home_spread, "is_home": True}
                # Calculate away spread (opposite)
                try:
                    away_val = -float(home_spread)
                    spreads[away_full] = {"spread": f"{away_val:+.1f}", "is_home": False}
                except ValueError:
                    pass
            elif away_spread:
                spreads[away_full] = {"spread": away_spread, "is_home": False}
                # Calculate home spread (opposite)
                try:
                    home_val = -float(away_spread)
                    spreads[home_full] = {"spread": f"{home_val:+.1f}", "is_home": True}
                except ValueError:
                    pass
    
    return spreads


def fetch_todays_games() -> List[GameInfo]:
    """Fetch today's NBA games from the public NBA scoreboard API."""
    try:
        resp = requests.get(NBA_SCOREBOARD_URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Failed to fetch NBA scoreboard: {e}", file=sys.stderr)
        return []

    data = resp.json()
    games_raw = data.get("scoreboard", {}).get("games", [])

    games: List[GameInfo] = []
    pt_tz = ZoneInfo("America/Los_Angeles")

    for g in games_raw:
        game_id = g.get("gameId") or g.get("gameId", "")
        game_time_utc_str = g.get("gameTimeUTC")
        if not game_time_utc_str:
            # Skip games without a clear start time
            continue

        # Example format: "2025-11-29T03:00:00Z"
        try:
            if game_time_utc_str.endswith("Z"):
                game_time_utc_str = game_time_utc_str.replace("Z", "+00:00")
            dt_utc = datetime.fromisoformat(game_time_utc_str)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        except Exception:
            # Fallback: skip unparseable dates
            continue

        dt_pt = dt_utc.astimezone(pt_tz)

        home_raw = g.get("homeTeam", {})
        away_raw = g.get("awayTeam", {})

        home_label = f"{home_raw.get('teamCity', '').strip()} {home_raw.get('teamName', '').strip()}".strip()
        away_label = f"{away_raw.get('teamCity', '').strip()} {away_raw.get('teamName', '').strip()}".strip()

        home_slug = TEAM_NAME_TO_SLUG.get(home_label)
        away_slug = TEAM_NAME_TO_SLUG.get(away_label)

        games.append(
            GameInfo(
                game_id=str(game_id),
                start_time_pt=dt_pt,
                home=TeamInfo(label=home_label, slug=home_slug, metrics=None),
                away=TeamInfo(label=away_label, slug=away_slug, metrics=None),
            )
        )

    # Filter out games that are clearly missing team labels
    return [g for g in games if g.home.label and g.away.label]


def ensure_team_csv(slug: str, repo_root: Path) -> Path:
    """Ensure we have an up-to-date ATS results CSV for the given TeamRankings slug.

    This will call the local scraper script to refresh data for that team.
    """
    csv_path = repo_root / f"ats_results_{slug}.csv"

    scraper_path = repo_root / "scrape_ats_results.py"
    if not scraper_path.exists():
        print(f"WARNING: scraper script not found at {scraper_path}; cannot refresh {slug}.", file=sys.stderr)
        return csv_path

    cmd = [sys.executable, str(scraper_path), "--team-slug", slug, "--output", str(csv_path)]
    try:
        print(f"Refreshing ATS results data for {slug}...", file=sys.stderr)
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to scrape data for {slug}: {e}", file=sys.stderr)

    return csv_path


def load_metrics_for_games(games: List[GameInfo], repo_root: Path) -> None:
    """Populate metrics for each team in the given list of games.

    This reuses calculate_team_ats_metrics from calculate_ats_metrics.py and
    auto-refreshes each needed team via the scraper.
    """
    seen: Dict[str, Optional[Dict]] = {}

    for game in games:
        for team in (game.home, game.away):
            if not team.slug:
                continue
            if team.slug in seen:
                team.metrics = seen[team.slug]
                continue

            csv_path = ensure_team_csv(team.slug, repo_root)
            metrics = calculate_team_ats_metrics(str(csv_path))
            team.metrics = metrics
            seen[team.slug] = metrics


def format_time_pt(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0") + " PT"


def render_html(games: List[GameInfo], output_path: Path, plot_files: dict) -> None:
    """Render a simple static HTML page for nbabetinfo."""
    today_pt = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%B %d, %Y")

    rows_html = []
    for g in sorted(games, key=lambda x: x.start_time_pt):
        time_str = format_time_pt(g.start_time_pt)

        def metric_vals(team: TeamInfo):
            if not team.metrics:
                return None, None, None, None
            m = team.metrics
            total_diff = f"{m['TOTAL_DIFF']:+.2f}"
            fav_diff = f"{m['FAV_DIFF']:+.2f}" if m['FAV_DIFF'] is not None else None
            dog_diff = f"{m['DOG_DIFF']:+.2f}" if m['DOG_DIFF'] is not None else None
            cri = f"{m['CRI']*100:.1f}%"
            return total_diff, fav_diff, dog_diff, cri

        away_total, away_fav, away_dog, away_cri = metric_vals(g.away)
        home_total, home_fav, home_dog, home_cri = metric_vals(g.home)

        def td_metric(val: Optional[str]) -> str:
            if val is None:
                return "<td class='metric na'>—</td>"
            return f"<td class='metric'>{val}</td>"
        
        # Format team names with spread
        away_display = g.away.label
        if g.away.spread:
            away_display += f" ({g.away.spread})"
        
        home_display = g.home.label
        if g.home.spread:
            home_display += f" ({g.home.spread})"

        row = [
            f"<td class='time'>{time_str}</td>",
            f"<td class='team-name'>{away_display}</td>",
            td_metric(away_total),
            td_metric(away_fav),
            td_metric(away_dog),
            td_metric(away_cri),
            f"<td class='team-name'>{home_display}</td>",
            td_metric(home_total),
            td_metric(home_fav),
            td_metric(home_dog),
            td_metric(home_cri),
        ]

        rows_html.append("<tr>" + "".join(row) + "</tr>")

    rows_block = "\n".join(rows_html) if rows_html else "<tr><td colspan='11'>No games found for today.</td></tr>"

    # Compact legend
    legend_html = """
    <section class="legend">
      <h2>NBA Betting Metrics (Quick Guide)</h2>
      <ul>
        <li><strong>Total DIFF</strong>: Average ATS differential across all games. Shows overall spread performance.</li>
        <li><strong>Fav DIFF</strong>: Average ATS differential when team is favorite (negative spread). How they perform when favored.</li>
        <li><strong>Dog DIFF</strong>: Average ATS differential when team is underdog (positive spread). How they perform as underdog.</li>
        <li><strong>CRI</strong> (Cover Rate): Percentage of games covering the spread. Above 50% = covers more often than not.</li>
      </ul>
      <p><em>Positive differentials indicate beating the spread. Look for teams with positive DIFFs and high CRI for betting value.</em></p>
    </section>
    """.strip()
    
    # Generate plots HTML
    plots_items = []
    for g in games:
        for team in (g.away, g.home):
            if team.slug and team.slug in plot_files:
                team_name = team.label
                plot_path = plot_files[team.slug]
                plots_items.append(f'<div class="plot-item"><img src="{plot_path}" alt="{team_name} ATS Performance" /></div>')
    
    plots_html = "\n        ".join(plots_items) if plots_items else "<p>No plots available for today's teams.</p>"

    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>NBA Betting Info - {today_pt}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {{
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 1.5rem;
        background: #0b1020;
        color: #f4f4f4;
      }}
      h1 {{
        font-size: 1.75rem;
        margin-bottom: 0.25rem;
      }}
      h2 {{
        font-size: 1.1rem;
        margin-top: 1.5rem;
      }}
      .table-wrapper {{
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-top: 1rem;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        background: #151a30;
        border-radius: 6px;
        overflow: hidden;
        min-width: 800px;
      }}
      th, td {{
        padding: 0.4rem 0.5rem;
        border-bottom: 1px solid #252b45;
        vertical-align: top;
        font-size: 0.85rem;
      }}
      th {{
        text-align: left;
        background: #202640;
        font-weight: 600;
      }}
      tr:last-child td {{
        border-bottom: none;
      }}
      td.time {{
        white-space: nowrap;
        font-weight: 600;
      }}
      td.team-name {{
        font-weight: 600;
        white-space: nowrap;
      }}
      td.metric {{
        text-align: right;
        font-variant-numeric: tabular-nums;
      }}
      td.metric.na {{
        color: #555b80;
      }}
      .legend {{
        font-size: 0.85rem;
        color: #d0d4f8;
      }}
      .legend ul {{
        padding-left: 1.2rem;
      }}
      .legend li {{
        margin-bottom: 0.25rem;
      }}
      footer {{
        margin-top: 1.5rem;
        font-size: 0.75rem;
        color: #888fb2;
      }}
      .plots-section {{
        margin-top: 2rem;
      }}
      .plots-section h2 {{
        font-size: 1.3rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #252b45;
        padding-bottom: 0.5rem;
      }}
      .plots-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
        gap: 2rem;
        margin-top: 1.5rem;
      }}
      .plot-item {{
        background: #151a30;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #252b45;
      }}
      .plot-item img {{
        width: 100%;
        height: auto;
        border-radius: 4px;
      }}
      @media (max-width: 768px) {{
        body {{
          margin: 1rem;
        }}
        h1 {{
          font-size: 1.5rem;
        }}
        h2 {{
          font-size: 1rem;
        }}
        th, td {{
          padding: 0.35rem 0.4rem;
          font-size: 0.75rem;
        }}
        .legend {{
          font-size: 0.8rem;
        }}
        .legend ul {{
          padding-left: 1rem;
        }}
        .plots-section h2 {{
          font-size: 1.1rem;
        }}
        .plots-grid {{
          grid-template-columns: 1fr;
          gap: 1rem;
        }}
        .plot-item {{
          padding: 0.75rem;
        }}
      }}
      @media (max-width: 480px) {{
        body {{
          margin: 0.75rem;
        }}
        h1 {{
          font-size: 1.3rem;
        }}
        th, td {{
          padding: 0.3rem 0.35rem;
          font-size: 0.7rem;
        }}
        .legend {{
          font-size: 0.75rem;
        }}
        footer {{
          font-size: 0.7rem;
        }}
      }}
    </style>
  </head>
  <body>
    <h1>NBA Betting Info</h1>
    <div>Games for {today_pt} (times in Pacific Time)</div>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th rowspan="2">Time (PT)</th>
            <th colspan="5">Away</th>
            <th colspan="5">Home</th>
          </tr>
          <tr>
            <th>Team</th>
            <th>Total</th>
            <th>Fav</th>
            <th>Dog</th>
            <th>CRI</th>
            <th>Team</th>
            <th>Total</th>
            <th>Fav</th>
            <th>Dog</th>
            <th>CRI</th>
          </tr>
        </thead>
        <tbody>
          {rows_block}
        </tbody>
      </table>
    </div>

    {legend_html}

    <footer>
      Metrics computed from TeamRankings ATS results data. Data scraped from teamrankings.com/nba.
    </footer>

    <section class="plots-section">
      <h2>ATS Performance Charts for Today's Teams</h2>
      <div class="plots-grid">
        {plots_html}
      </div>
    </section>
  </body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote HTML to {output_path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent

    games = fetch_todays_games()
    if not games:
        print("WARNING: No games fetched for today; still generating page with notice.", file=sys.stderr)

    # Fetch today's spreads
    spreads = fetch_todays_spreads()
    if spreads:
        print(f"Fetched spreads for {len(spreads)} teams")
        # Attach spreads to games
        for game in games:
            if game.away.label in spreads:
                game.away.spread = spreads[game.away.label]["spread"]
            if game.home.label in spreads:
                game.home.spread = spreads[game.home.label]["spread"]

    load_metrics_for_games(games, repo_root)
    
    # Generate plots for all teams playing today
    teams_playing = set()
    for game in games:
        if game.away.slug:
            teams_playing.add(game.away.slug)
        if game.home.slug:
            teams_playing.add(game.home.slug)
    
    print(f"Generating ATS plots for {len(teams_playing)} teams...")
    plot_files = generate_plots_for_teams(list(teams_playing), data_dir=str(repo_root), output_dir=str(repo_root / "plots"))
    print(f"Generated {len(plot_files)} plots")

    # Write to index.html at repo root so GitHub Pages (root) serves it
    output_path = repo_root / "index.html"
    render_html(games, output_path, plot_files)


if __name__ == "__main__":
    main()
