# Usage Guide

## Quick Start

### 1. Scrape ATS results for all NBA teams
```bash
python scrape_all_ats.py
```

This will scrape ATS results from TeamRankings for all 30 NBA teams and save them as `ats_results_{team-slug}.csv` files.

### 2. View team rankings
```bash
python calculate_ats_metrics.py
```

This displays:
- Top 10 teams by AVI (best value opportunities)
- Bottom 10 teams by AVI (avoid - market overvalues)
- Top 10 teams by CRI (best cover rate)

### 3. Generate today's webpage
```bash
python generate_nbabetinfo_page.py
```

This will:
- Fetch today's NBA schedule from NBA.com API
- Refresh ATS data for teams playing today
- Generate `index.html` with metrics for each matchup

## Individual Team Scraping

To scrape just one team:
```bash
python scrape_ats_results.py --team-slug los-angeles-clippers
```

Available team slugs:
- atlanta-hawks
- boston-celtics
- brooklyn-nets
- charlotte-hornets
- chicago-bulls
- cleveland-cavaliers
- dallas-mavericks
- denver-nuggets
- detroit-pistons
- golden-state-warriors
- houston-rockets
- indiana-pacers
- los-angeles-clippers
- los-angeles-lakers
- memphis-grizzlies
- miami-heat
- milwaukee-bucks
- minnesota-timberwolves
- new-orleans-pelicans
- new-york-knicks
- oklahoma-city-thunder
- orlando-magic
- philadelphia-76ers
- phoenix-suns
- portland-trail-blazers
- sacramento-kings
- san-antonio-spurs
- toronto-raptors
- utah-jazz
- washington-wizards

## Understanding the Data

### CSV Files (ats_results_*.csv)

Each CSV contains:
- `date` - Game date (MM/DD format)
- `home_away` - Whether team was home or away
- `opponent` - Opposing team
- `opp_rank` - Opponent's ATS rank (1-30)
- `spread` - The spread line for this team (negative = favorite)
- `result` - W or L
- `margin` - Points won/lost by
- `ats_diff` - ATS differential (positive = covered, negative = didn't cover)

### Metrics

**SPI (Spread Performance Index)**
- Average of all `ats_diff` values
- Shows overall spread performance
- Negative SPI = team underperforms vs spread

**AVI (ATS Value Index)**
- Calculated as `-SPI`
- **Positive AVI** = Market undervalues team (betting opportunity!)
- **Negative AVI** = Market overvalues team (avoid)

**CRI (Cover Rate Index)**  
- Percentage of games where `ats_diff > 0`
- 50%+ = Good cover rate
- Combined with positive AVI = strong value bet

## Example Interpretation

```
Team: Los Angeles Clippers
AVI: +7.36
CRI: 23.8%
Record: 5-16 ATS
```

**What this means:**
- The Clippers have a very high positive AVI (+7.36)
- This suggests the market is consistently setting lines too pessimistic for them
- However, their CRI is only 23.8% - they're only covering 5 out of 21 games
- **Interpretation:** Despite the high AVI, the poor CRI suggests this team is genuinely struggling and not a good bet yet

```
Team: Indiana Pacers  
AVI: +3.76
CRI: 52.4%
Record: 11-10 ATS
```

**What this means:**
- Positive AVI indicates some market undervaluation
- CRI above 50% shows they're covering more often than not
- **Interpretation:** This is a potential value opportunity - market is slightly undervaluing them and they're backing it up with covers

## Daily Workflow

1. **Morning:** Run `python scrape_all_ats.py` to refresh all data
2. **Check Rankings:** Run `python calculate_ats_metrics.py` to see current value opportunities
3. **View Today's Games:** Run `python generate_nbabetinfo_page.py` and open `index.html`
4. **Identify Value:** Look for matchups where a high-AVI team is playing, especially if they have decent CRI (45%+)

## Data Source

All data comes from TeamRankings.com ATS results pages:
- Example: https://www.teamrankings.com/nba/team/los-angeles-clippers/ats-results
- Shows detailed game-by-game spread performance
- Updated after each game with actual results
