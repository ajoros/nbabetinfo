# nbabetinfo

**A daily NBA betting analytics dashboard** that combines today's games with historical against-the-spread (ATS) performance metrics to help identify betting value.

## What It Does

`nbabetinfo` automatically generates a daily HTML page showing:

- **Today's NBA schedule** with game times (Pacific Time) and current spreads from TeamRankings
- **Role-specific performance metrics** for each team — how they perform as favorites vs. underdogs
- **Visual performance charts** showing spread vs. actual margin trends over recent games
- **Cover rate analysis** to identify consistent performers

The tool is designed to answer key betting questions:
- Which favorites consistently beat their spreads?
- Which underdogs provide value when catching points?
- Is a team's spread performance consistent or volatile?

## Data Sources

### Game Schedule & Spreads
- **NBA Official API** (`cdn.nba.com`) — Today's games and start times
- **TeamRankings.com** — Current spread lines from the main NBA page

### Historical Performance
- **TeamRankings ATS Results** (`/nba/team/{team}/ats-results`) — Game-by-game spread performance including:
  - Date and opponent
  - Opening spread
  - Game result and margin
  - ATS differential (how many points they beat/missed the spread by)

The scraper collects full-season data for all 30 teams daily, storing results in CSV format for metric calculation.

## Betting Metrics Explained

### Total DIFF (Overall Spread Performance)
**Average ATS differential across all games**

- Measures how many points a team beats or misses the spread by on average
- Formula: `mean(actual_margin - spread)`
- **+3.0**: Team beats spread by 3 points on average (value opportunity)
- **-2.5**: Team misses spread by 2.5 points on average (avoid)

### Fav DIFF (Favorite Performance)
**Average ATS differential when team is favored (negative spread)**

- Shows how favorites perform when expected to win
- Critical for evaluating whether a favorite is worth laying points with
- **+2.0 or higher**: Strong favorite that covers consistently
- **Negative**: Favorite that struggles to cover — overvalued by market

### Dog DIFF (Underdog Performance)
**Average ATS differential when team is underdog (positive spread)**

- Shows how underdogs perform when catching points
- Identifies "live dogs" that provide value
- **+3.0 or higher**: Strong underdog play
- **-2.0 or worse**: Underdog that gets blown out — avoid

### CRI - Cover Rate Index
**Percentage of games where team covers the spread**

- Formula: `(ATS Wins / Total Games) × 100`
- **Above 55%**: Consistent performer, high reliability
- **50-55%**: Average cover rate
- **Below 45%**: Inconsistent or overvalued by market

## Using the Metrics Together

### Strong Favorite Signal
✅ Team is favored today (negative spread)  
✅ Fav DIFF > +2.0  
✅ CRI > 55%

→ **Recommendation**: Consider laying the points with this favorite

### Value Underdog Signal
✅ Team is underdog today (positive spread)  
✅ Dog DIFF > +2.0  
✅ CRI > 50%

→ **Recommendation**: Value opportunity on the underdog

### Warning Signal
⚠️ Team is underdog today  
⚠️ Dog DIFF < -2.0  
⚠️ CRI < 45%

→ **Recommendation**: Avoid — team likely to lose by more than the spread

## Visual Dashboard Features

The generated HTML page includes:

### Game Table
- Side-by-side comparison of away vs. home metrics
- Highlighted cells indicate today's role (favorite or underdog)
- Color coding:
  - **Blue highlight**: Relevant metric for today's role
  - **Green**: Strong performance indicator
  - **Red**: Warning signal (poor underdog)

### Performance Charts
For each team playing today:
- **Spread vs. Actual Margin**: Line chart showing bookmaker expectations vs. reality
- **ATS Differential Bar Chart**: Game-by-game cover/miss magnitude
- **Cover rate shading**: Green for covers, red for misses
- **Summary statistics**: Season totals and averages

## How It Works

1. **Daily refresh** (automated via GitHub Actions):
   - Fetch today's NBA schedule from official API
   - Scrape current spreads from TeamRankings
   - Update ATS results data for all 30 teams

2. **Metric calculation**:
   - Calculate Total/Fav/Dog DIFF and CRI for each team
   - Identify role-specific strengths and weaknesses

3. **Visualization**:
   - Generate performance plots for teams playing today
   - Build HTML dashboard with metrics table and charts

4. **Publishing**:
   - Deploy static HTML to GitHub Pages
   - Accessible via web browser on any device

---

**Data source**: [TeamRankings.com](https://www.teamrankings.com/nba/)  
**License**: Educational/personal use only  
**Updates**: Daily before first game tip-off
