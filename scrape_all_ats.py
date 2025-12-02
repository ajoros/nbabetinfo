#!/usr/bin/env python3
"""
scrape_all_ats.py

Scrape ATS results for all NBA teams from TeamRankings.
"""

import subprocess
import sys
from pathlib import Path

# All NBA teams with their TeamRankings slugs
NBA_TEAMS = [
    "atlanta-hawks",
    "boston-celtics",
    "brooklyn-nets",
    "charlotte-hornets",
    "chicago-bulls",
    "cleveland-cavaliers",
    "dallas-mavericks",
    "denver-nuggets",
    "detroit-pistons",
    "golden-state-warriors",
    "houston-rockets",
    "indiana-pacers",
    "los-angeles-clippers",
    "los-angeles-lakers",
    "memphis-grizzlies",
    "miami-heat",
    "milwaukee-bucks",
    "minnesota-timberwolves",
    "new-orleans-pelicans",
    "new-york-knicks",
    "oklahoma-city-thunder",
    "orlando-magic",
    "philadelphia-76ers",
    "phoenix-suns",
    "portland-trail-blazers",
    "sacramento-kings",
    "san-antonio-spurs",
    "toronto-raptors",
    "utah-jazz",
    "washington-wizards",
]


def main():
    """Scrape ATS results for all NBA teams."""
    repo_root = Path(__file__).resolve().parent
    scraper_path = repo_root / "scrape_ats_results.py"
    
    if not scraper_path.exists():
        print(f"ERROR: Scraper not found at {scraper_path}", file=sys.stderr)
        sys.exit(1)
    
    success_count = 0
    failed_teams = []
    
    for i, team_slug in enumerate(NBA_TEAMS, 1):
        print(f"\n[{i}/{len(NBA_TEAMS)}] Scraping {team_slug}...")
        
        output_path = repo_root / f"ats_results_{team_slug}.csv"
        cmd = [sys.executable, str(scraper_path), "--team-slug", team_slug, "--output", str(output_path)]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ {team_slug} completed")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"✗ {team_slug} FAILED: {e.stderr}", file=sys.stderr)
            failed_teams.append(team_slug)
    
    print("\n" + "=" * 80)
    print(f"Scraping complete: {success_count}/{len(NBA_TEAMS)} teams successful")
    
    if failed_teams:
        print(f"\nFailed teams ({len(failed_teams)}):")
        for team in failed_teams:
            print(f"  - {team}")
        sys.exit(1)
    else:
        print("All teams scraped successfully!")


if __name__ == "__main__":
    main()
