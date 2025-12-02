# nbabetinfo

`nbabetinfo` is a small analytics tool that builds a daily view of the NBA betting board, combining game schedule data with historical against-the-spread (ATS) performance from TeamRankings.

Each day it produces a compact HTML page that shows:

- **Today's NBA games**
  - One row per game on the schedule
  - **Tip-off time in Pacific Time (PT)** for each matchup
- **Per‑team betting metrics** (for both away and home teams)
  - AVI (ATS Value Index) - identifies value opportunities
  - CRI (Cover Rate Index) - shows consistency
- **Quick metrics legend** so you can interpret the numbers at a glance

## Data & Metrics

The tool scrapes ATS results from TeamRankings.com (`/nba/team/{team-slug}/ats-results` pages), which show game-by-game spread performance including the spread line, result, and ATS differential.

For every team, it computes the following summary metrics:

- **SPI – Spread Performance Index**  
  Average ATS differential from TeamRankings data  
  Shows how much teams beat or miss the spread by on average
  - Positive SPI → team tends to beat the spread  
  - Negative SPI → team tends to fail to cover  

- **AVI – ATS Value Index**  
  Market mispricing indicator (negative of SPI)  
  Formula: `-SPI`  
  - Positive AVI → market consistently undervalues the team (betting value)  
  - Negative AVI → market overvalues the team (avoid)  

- **CRI – Cover Rate Index**  
  ATS win rate - percentage of games covering the spread  
  Formula: `ATS wins / Total ATS decisions`  
  - Above 50% → covers more often than not  
  - Below 50% → fails to cover more often

**How to identify value:**
- High positive AVI (e.g., +5 or more) suggests the market is consistently setting pessimistic lines
- Combine high AVI with 50%+ CRI for the best value opportunities
- Teams with negative AVI may be overvalued - bookies are setting optimistic lines
