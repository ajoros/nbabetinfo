#!/usr/bin/env python3
"""
calculate_ats_metrics.py

Calculate betting analytics metrics (SPI, AVI, CRI) from ATS results data.
This uses the data from the ATS results page which shows spread performance.
"""

import csv
import sys
from pathlib import Path


def calculate_team_ats_metrics(csv_file):
    """
    Calculate betting metrics for a single team from their ATS results CSV.
    
    Returns dict with:
    - SPI (Spread Performance Index): avg ATS diff (margin vs spread)
    - AVI (ATS Value Index): -SPI (market mispricing)
    - CRI (Cover Rate Index): ATS win rate
    - games_played: number of completed games
    - ats_wins: number of covers
    - ats_losses: number of non-covers
    """
    
    ats_diffs = []
    ats_wins = 0
    ats_losses = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Skip games without results (future games or missing data)
                if not row['ats_diff'] or row['ats_diff'] == '':
                    continue
                
                try:
                    ats_diff = float(row['ats_diff'])
                except (ValueError, TypeError):
                    continue
                
                ats_diffs.append(ats_diff)
                
                # Positive diff = covered, negative = didn't cover
                if ats_diff > 0:
                    ats_wins += 1
                else:
                    ats_losses += 1
    
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error processing {csv_file}: {e}", file=sys.stderr)
        return None
    
    if not ats_diffs:
        return None
    
    # Calculate metrics
    spi = sum(ats_diffs) / len(ats_diffs)
    avi = -spi  # Positive AVI means market undervalues the team
    ats_decisions = ats_wins + ats_losses
    cri = ats_wins / ats_decisions if ats_decisions > 0 else 0
    
    return {
        'SPI': spi,
        'AVI': avi,
        'CRI': cri,
        'games_played': len(ats_diffs),
        'ats_wins': ats_wins,
        'ats_losses': ats_losses,
        'ats_decisions': ats_decisions
    }


def get_all_team_metrics(data_dir="."):
    """
    Load ATS metrics for all teams that have data files.
    
    Returns dict mapping team slug to metrics dict.
    """
    data_path = Path(data_dir)
    all_metrics = {}
    
    # Find all ATS results CSV files
    ats_files = list(data_path.glob("ats_results_*.csv"))
    
    for csv_file in ats_files:
        # Extract team slug from filename
        # Format: ats_results_<team-slug>.csv
        team_slug = csv_file.stem.replace("ats_results_", "")
        
        metrics = calculate_team_ats_metrics(csv_file)
        if metrics:
            all_metrics[team_slug] = metrics
    
    return all_metrics


def display_team_rankings(all_metrics):
    """
    Display teams ranked by different metrics.
    """
    if not all_metrics:
        print("No team data available.")
        return
    
    # Sort teams by different metrics
    by_avi = sorted(all_metrics.items(), key=lambda x: x[1]['AVI'], reverse=True)
    by_cri = sorted(all_metrics.items(), key=lambda x: x[1]['CRI'], reverse=True)
    by_spi = sorted(all_metrics.items(), key=lambda x: x[1]['SPI'])
    
    print("=" * 90)
    print("NBA ATS METRICS - TEAM RANKINGS")
    print("=" * 90)
    print()
    
    # Top 10 by AVI (best value bets)
    print("TOP 10 TEAMS BY AVI (Market Undervalues - Potential Value)")
    print("-" * 90)
    for i, (team, metrics) in enumerate(by_avi[:10], 1):
        print(f"{i:2d}. {team:30s}  AVI: {metrics['AVI']:+.2f}  CRI: {metrics['CRI']:.1%}  SPI: {metrics['SPI']:+.2f}  ({metrics['ats_wins']}-{metrics['ats_losses']})")
    print()
    
    # Bottom 10 by AVI (avoid)
    print("BOTTOM 10 TEAMS BY AVI (Market Overvalues - Avoid)")
    print("-" * 90)
    for i, (team, metrics) in enumerate(reversed(by_avi[-10:]), 1):
        print(f"{i:2d}. {team:30s}  AVI: {metrics['AVI']:+.2f}  CRI: {metrics['CRI']:.1%}  SPI: {metrics['SPI']:+.2f}  ({metrics['ats_wins']}-{metrics['ats_losses']})")
    print()
    
    # Top 10 by CRI (best cover rate)
    print("TOP 10 TEAMS BY CRI (Cover Most Often)")
    print("-" * 90)
    for i, (team, metrics) in enumerate(by_cri[:10], 1):
        print(f"{i:2d}. {team:30s}  CRI: {metrics['CRI']:.1%}  AVI: {metrics['AVI']:+.2f}  SPI: {metrics['SPI']:+.2f}  ({metrics['ats_wins']}-{metrics['ats_losses']})")
    print()
    
    print("=" * 90)
    print()
    print("METRIC DEFINITIONS:")
    print("  SPI (Spread Performance Index)  = Avg ATS diff (how much team beats/misses spread)")
    print("  AVI (ATS Value Index)           = -SPI (positive = market undervalues team)")
    print("  CRI (Cover Rate Index)          = ATS win rate (% of games covering spread)")
    print("=" * 90)


def main():
    """Display team rankings by ATS metrics."""
    all_metrics = get_all_team_metrics()
    display_team_rankings(all_metrics)


if __name__ == "__main__":
    main()
