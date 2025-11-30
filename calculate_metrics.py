#!/usr/bin/env python3
"""
calculate_metrics.py

Calculate betting analytics metrics (SPI, AVI, CRI, TPI) from scraped TeamRankings data.
"""

import csv
import sys
from pathlib import Path


def calculate_team_metrics(csv_file):
    """
    Calculate betting metrics for a single team from their scraped CSV.
    
    Returns dict with:
    - SPI (Spread Performance Index): avg ATS margin
    - AVI (ATS Value Index): -SPI (market mispricing)
    - CRI (Cover Rate Index): ATS win rate
    - TPI (Totals Performance Index): avg total margin
    - games_played: number of completed games
    """
    
    ats_margins = []
    ats_wins = 0
    ats_decisions = 0
    total_margins = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Skip games without results (future games)
                if not row['team_score'] or not row['opp_score']:
                    continue
                
                team_score = int(row['team_score'])
                opp_score = int(row['opp_score'])
                
                # Skip games without betting lines
                if not row['spread'] or not row['total']:
                    continue
                    
                spread = float(row['spread'])
                total = float(row['total'])
                
                # Calculate ATS margin (team_score - opp_score + spread)
                point_diff = team_score - opp_score
                ats_margin = point_diff + spread
                ats_margins.append(ats_margin)
                
                # ATS decision tracking
                ats_decisions += 1
                if ats_margin > 0:
                    ats_wins += 1
                
                # Calculate total margin (team_score + opp_score - total)
                actual_total = team_score + opp_score
                total_margin = actual_total - total
                total_margins.append(total_margin)
    
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error processing {csv_file}: {e}", file=sys.stderr)
        return None
    
    if not ats_margins:
        return None
    
    # Calculate metrics
    spi = sum(ats_margins) / len(ats_margins)
    avi = -spi
    cri = ats_wins / ats_decisions if ats_decisions > 0 else 0
    tpi = sum(total_margins) / len(total_margins) if total_margins else 0
    
    return {
        'SPI': spi,
        'AVI': avi,
        'CRI': cri,
        'TPI': tpi,
        'games_played': len(ats_margins),
        'ats_wins': ats_wins,
        'ats_decisions': ats_decisions
    }


def main():
    """Calculate and display metrics for today's matchups."""
    
    # Define today's matchups (Nov 29, 2024)
    matchups = [
        {"away": "Boston", "home": "Minnesota", "spread": -6.5, "file_away": "boston-celtics", "file_home": "minnesota-timberwolves"},
        {"away": "Toronto", "home": "Charlotte", "spread": 8.5, "file_away": "toronto-raptors", "file_home": "charlotte-hornets"},
        {"away": "Chicago", "home": "Indiana", "spread": -3.5, "file_away": "chicago-bulls", "file_home": "indiana-pacers"},
        {"away": "Brooklyn", "home": "Milwaukee", "spread": -11.5, "file_away": "brooklyn-nets", "file_home": "milwaukee-bucks"},
        {"away": "Detroit", "home": "Miami", "spread": -3.5, "file_away": "detroit-pistons", "file_home": "miami-heat"},
        {"away": "New Orleans", "home": "Golden State", "spread": -8.5, "file_away": "new-orleans-pelicans", "file_home": "golden-state-warriors"},
        {"away": "Denver", "home": "Phoenix", "spread": -4.5, "file_away": "denver-nuggets", "file_home": "phoenix-suns"},
        {"away": "Dallas", "home": "LA Clippers", "spread": -7.5, "file_away": "dallas-mavericks", "file_home": "los-angeles-clippers"},
    ]
    
    print("=" * 90)
    print("NBA BETTING ANALYTICS - NOVEMBER 29, 2024")
    print("=" * 90)
    print()
    
    for matchup in matchups:
        away_team = matchup['away']
        home_team = matchup['home']
        spread = matchup['spread']
        
        # Determine favorite
        if spread < 0:
            favorite = home_team
            underdog = away_team
            fav_spread = spread
        else:
            favorite = away_team
            underdog = home_team
            fav_spread = -spread
        
        # Load metrics
        away_file = f"teamrankings_{matchup['file_away']}.csv"
        home_file = f"teamrankings_{matchup['file_home']}.csv"
        
        away_metrics = calculate_team_metrics(away_file)
        home_metrics = calculate_team_metrics(home_file)
        
        # Display matchup
        print(f"{'─' * 90}")
        print(f"🏀  {away_team} @ {home_team}  |  Spread: {home_team} {spread:+.1f}")
        print(f"{'─' * 90}")
        
        if away_metrics:
            print(f"\n{away_team.upper()} (Away):")
            print(f"  SPI: {away_metrics['SPI']:+.2f}  |  AVI: {away_metrics['AVI']:+.2f}  |  CRI: {away_metrics['CRI']:.1%}  |  TPI: {away_metrics['TPI']:+.2f}")
            print(f"  ATS Record: {away_metrics['ats_wins']}-{away_metrics['ats_decisions'] - away_metrics['ats_wins']} ({away_metrics['games_played']} games)")
        else:
            print(f"\n{away_team.upper()}: No data available")
        
        if home_metrics:
            print(f"\n{home_team.upper()} (Home):")
            print(f"  SPI: {home_metrics['SPI']:+.2f}  |  AVI: {home_metrics['AVI']:+.2f}  |  CRI: {home_metrics['CRI']:.1%}  |  TPI: {home_metrics['TPI']:+.2f}")
            print(f"  ATS Record: {home_metrics['ats_wins']}-{home_metrics['ats_decisions'] - home_metrics['ats_wins']} ({home_metrics['games_played']} games)")
        else:
            print(f"\n{home_team.upper()}: No data available")
        
        # Edge analysis
        if away_metrics and home_metrics:
            print(f"\n📊 EDGE ANALYSIS:")
            
            # AVI comparison (shows market mispricing)
            avi_diff = away_metrics['AVI'] - home_metrics['AVI']
            if abs(avi_diff) > 2:
                if avi_diff > 0:
                    print(f"  ⚡ {away_team} may have VALUE (AVI edge: {avi_diff:+.2f})")
                else:
                    print(f"  ⚡ {home_team} may have VALUE (AVI edge: {-avi_diff:+.2f})")
            
            # CRI comparison
            cri_diff = away_metrics['CRI'] - home_metrics['CRI']
            if abs(cri_diff) > 0.10:
                if cri_diff > 0:
                    print(f"  📈 {away_team} covers more often (CRI: {away_metrics['CRI']:.1%} vs {home_metrics['CRI']:.1%})")
                else:
                    print(f"  📈 {home_team} covers more often (CRI: {home_metrics['CRI']:.1%} vs {away_metrics['CRI']:.1%})")
            
            # TPI totals bias
            avg_tpi = (away_metrics['TPI'] + home_metrics['TPI']) / 2
            if avg_tpi > 2:
                print(f"  🔥 OVER lean (combined TPI: +{avg_tpi:.2f})")
            elif avg_tpi < -2:
                print(f"  ❄️  UNDER lean (combined TPI: {avg_tpi:.2f})")
        
        print()
    
    print("=" * 90)
    print()
    print("METRIC DEFINITIONS:")
    print("  SPI (Spread Performance Index)  = Avg ATS margin (how much team beats/misses spread)")
    print("  AVI (ATS Value Index)           = -SPI (positive = market undervalues team)")
    print("  CRI (Cover Rate Index)          = ATS win rate (% of games covering spread)")
    print("  TPI (Totals Performance Index)  = Avg total margin (positive = games go OVER)")
    print("=" * 90)


if __name__ == "__main__":
    main()
