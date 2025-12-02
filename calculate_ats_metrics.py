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
    - TOTAL_DIFF: avg ATS diff across all games
    - FAV_DIFF: avg ATS diff when team is favorite (negative spread)
    - DOG_DIFF: avg ATS diff when team is underdog (positive spread)
    - CRI (Cover Rate Index): ATS win rate
    - games_played: number of completed games
    - ats_wins: number of covers
    - ats_losses: number of non-covers
    """
    
    ats_diffs = []
    fav_diffs = []  # When spread is negative (team is favorite)
    dog_diffs = []  # When spread is positive (team is underdog)
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
                    spread = float(row['spread'])
                except (ValueError, TypeError):
                    continue
                
                ats_diffs.append(ats_diff)
                
                # Categorize by favorite/underdog
                if spread < 0:
                    fav_diffs.append(ats_diff)
                elif spread > 0:
                    dog_diffs.append(ats_diff)
                # If spread == 0 (pick'em), include in total but not fav/dog
                
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
    total_diff = sum(ats_diffs) / len(ats_diffs)
    fav_diff = sum(fav_diffs) / len(fav_diffs) if fav_diffs else None
    dog_diff = sum(dog_diffs) / len(dog_diffs) if dog_diffs else None
    
    ats_decisions = ats_wins + ats_losses
    cri = ats_wins / ats_decisions if ats_decisions > 0 else 0
    
    return {
        'TOTAL_DIFF': total_diff,
        'FAV_DIFF': fav_diff,
        'DOG_DIFF': dog_diff,
        'CRI': cri,
        'games_played': len(ats_diffs),
        'fav_games': len(fav_diffs),
        'dog_games': len(dog_diffs),
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
    by_total_diff = sorted(all_metrics.items(), key=lambda x: x[1]['TOTAL_DIFF'], reverse=True)
    by_cri = sorted(all_metrics.items(), key=lambda x: x[1]['CRI'], reverse=True)
    
    print("=" * 100)
    print("NBA ATS METRICS - TEAM RANKINGS")
    print("=" * 100)
    print()
    
    # Top 10 by Total Diff
    print("TOP 10 TEAMS BY TOTAL DIFF (Best Overall Spread Performance)")
    print("-" * 100)
    for i, (team, metrics) in enumerate(by_total_diff[:10], 1):
        fav = f"{metrics['FAV_DIFF']:+.2f}" if metrics['FAV_DIFF'] is not None else "N/A"
        dog = f"{metrics['DOG_DIFF']:+.2f}" if metrics['DOG_DIFF'] is not None else "N/A"
        print(f"{i:2d}. {team:30s}  Total: {metrics['TOTAL_DIFF']:+.2f}  Fav: {fav:>6s}  Dog: {dog:>6s}  CRI: {metrics['CRI']:.1%}  ({metrics['ats_wins']}-{metrics['ats_losses']})")
    print()
    
    # Bottom 10 by Total Diff
    print("BOTTOM 10 TEAMS BY TOTAL DIFF (Worst Overall Spread Performance)")
    print("-" * 100)
    for i, (team, metrics) in enumerate(reversed(by_total_diff[-10:]), 1):
        fav = f"{metrics['FAV_DIFF']:+.2f}" if metrics['FAV_DIFF'] is not None else "N/A"
        dog = f"{metrics['DOG_DIFF']:+.2f}" if metrics['DOG_DIFF'] is not None else "N/A"
        print(f"{i:2d}. {team:30s}  Total: {metrics['TOTAL_DIFF']:+.2f}  Fav: {fav:>6s}  Dog: {dog:>6s}  CRI: {metrics['CRI']:.1%}  ({metrics['ats_wins']}-{metrics['ats_losses']})")
    print()
    
    # Top 10 by CRI (best cover rate)
    print("TOP 10 TEAMS BY CRI (Cover Most Often)")
    print("-" * 100)
    for i, (team, metrics) in enumerate(by_cri[:10], 1):
        fav = f"{metrics['FAV_DIFF']:+.2f}" if metrics['FAV_DIFF'] is not None else "N/A"
        dog = f"{metrics['DOG_DIFF']:+.2f}" if metrics['DOG_DIFF'] is not None else "N/A"
        print(f"{i:2d}. {team:30s}  CRI: {metrics['CRI']:.1%}  Total: {metrics['TOTAL_DIFF']:+.2f}  Fav: {fav:>6s}  Dog: {dog:>6s}  ({metrics['ats_wins']}-{metrics['ats_losses']})")
    print()
    
    print("=" * 100)
    print()
    print("METRIC DEFINITIONS:")
    print("  TOTAL_DIFF = Avg ATS differential across all games")
    print("  FAV_DIFF   = Avg ATS differential when team is favorite (negative spread)")
    print("  DOG_DIFF   = Avg ATS differential when team is underdog (positive spread)")
    print("  CRI        = Cover Rate Index - ATS win rate (% of games covering spread)")
    print("=" * 100)


def main():
    """Display team rankings by ATS metrics."""
    all_metrics = get_all_team_metrics()
    display_team_rankings(all_metrics)


if __name__ == "__main__":
    main()
