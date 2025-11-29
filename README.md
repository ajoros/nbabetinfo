# nbabetinfo

`nbabetinfo` is a small analytics tool that builds a daily view of the NBA betting board, combining game schedule data with historical against-the-spread performance.

Each day it produces a compact HTML page that shows:

- **Today’s NBA games**
  - One row per game on the schedule
  - **Tip-off time in Pacific Time (PT)** for each matchup
- **Per‑team betting metrics** (for both away and home teams)
  - SPI (Spread Performance Index)
  - AVI (ATS Value Index)
  - CRI (Cover Rate Index)
  - TPI (Totals Performance Index)
- **Quick metrics legend** so you can interpret the numbers at a glance

## Data & Metrics

The tool works off game‑level betting data scraped from TeamRankings for each NBA team. For every team, it computes the following summary metrics:

- **SPI – Spread Performance Index**  
  Average ATS (Against The Spread) margin  
  Formula: `(team_score - opp_score) + spread`  
  - Positive SPI → team tends to beat the spread  
  - Negative SPI → team tends to fail to cover  

- **AVI – ATS Value Index**  
  Market mispricing (inverse of SPI)  
  Formula: `-SPI`  
  - Positive AVI → market undervalues the team (potential value)  
  - Negative AVI → market overvalues the team  

- **CRI – Cover Rate Index**  
  How often a team covers the spread  
  Formula: `ATS wins / ATS decisions` (games with a valid spread)  
  - Above 50% → covers more often than not  
  - Below 50% → fails to cover more often  

- **TPI – Totals Performance Index**  
  Whether games go OVER or UNDER the total  
  Formula: `(team_score + opp_score) - posted_total`  
  - Positive TPI → games tend to go OVER  
  - Negative TPI → games tend to go UNDER  
