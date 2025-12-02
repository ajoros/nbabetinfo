#!/usr/bin/env python3
"""
generate_ats_plots.py

Generate ATS performance plots for NBA teams.
"""

import csv
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def generate_team_plot(team_slug, csv_file, output_file):
    """
    Generate ATS performance plot for a single team.
    
    Args:
        team_slug: Team slug (e.g., "oklahoma-city-thunder")
        csv_file: Path to ATS results CSV
        output_file: Path to save the plot PNG
    
    Returns:
        True if successful, False otherwise
    """
    # Read data
    dates = []
    spreads = []
    actual_margins = []
    ats_diffs = []
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['spread'] and row['margin'] and row['ats_diff']:
                    dates.append(row['date'])
                    spreads.append(float(row['spread']))
                    actual_margins.append(float(row['margin']))
                    ats_diffs.append(float(row['ats_diff']))
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return False
    
    if not dates:
        return False
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Format team name for title
    team_name = team_slug.replace('-', ' ').title()
    fig.suptitle(f'{team_name} - ATS Performance', fontsize=14, fontweight='bold')
    
    # Use dates for x-axis
    game_nums = list(range(len(dates)))
    
    # Subplot 1: Spread vs Actual Margin
    ax1.plot(game_nums, spreads, 'o-', linewidth=2, markersize=6, 
             label="Bookies' Spread", color='#1f77b4', alpha=0.7)
    ax1.plot(game_nums, actual_margins, 's-', linewidth=2, markersize=6,
             label='Actual Margin', color='#ff7f0e', alpha=0.7)
    
    # Highlight covers (green) and non-covers (red)
    for i, (spread, margin, ats_diff) in enumerate(zip(spreads, actual_margins, ats_diffs)):
        if ats_diff > 0:  # Covered
            ax1.axvspan(i-0.4, i+0.4, alpha=0.12, color='green')
        else:  # Didn't cover
            ax1.axvspan(i-0.4, i+0.4, alpha=0.12, color='red')
    
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    ax1.set_xlabel('Date', fontsize=10)
    ax1.set_ylabel('Points', fontsize=10)
    ax1.set_title("Spread vs Actual (Green = Cover, Red = Miss)", fontsize=11)
    ax1.legend(fontsize=9, loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(game_nums)
    ax1.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)
    
    # Subplot 2: ATS Differential (magnitude of cover/miss)
    colors = ['green' if diff > 0 else 'red' for diff in ats_diffs]
    bars = ax2.bar(game_nums, ats_diffs, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Add value labels on bars (only for larger values to avoid clutter)
    for i, (bar, diff) in enumerate(zip(bars, ats_diffs)):
        if abs(diff) > 10:  # Only show labels for big covers/misses
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                     f'{diff:+.0f}',
                     ha='center', va='bottom' if height > 0 else 'top',
                     fontsize=7, fontweight='bold')
    
    ax2.axhline(y=0, color='black', linewidth=1.5)
    ax2.set_xlabel('Date', fontsize=10)
    ax2.set_ylabel('ATS Differential', fontsize=10)
    ax2.set_title('Cover/Miss Margin (+ = Covered)', fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(game_nums)
    ax2.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)
    
    # Add summary stats
    avg_ats = np.mean(ats_diffs)
    covers = sum(1 for d in ats_diffs if d > 0)
    total = len(ats_diffs)
    cover_pct = (covers / total) * 100
    
    stats_text = f"SPI = {avg_ats:+.2f} | Covers: {covers}/{total} ({cover_pct:.1f}%) | AVI = {-avg_ats:+.2f}"
    fig.text(0.5, 0.02, stats_text, ha='center', fontsize=10, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    
    try:
        plt.savefig(output_file, dpi=100, bbox_inches='tight')
        plt.close(fig)
        return True
    except Exception as e:
        print(f"Error saving plot {output_file}: {e}")
        plt.close(fig)
        return False


def generate_plots_for_teams(team_slugs, data_dir=".", output_dir="plots"):
    """
    Generate plots for multiple teams.
    
    Args:
        team_slugs: List of team slugs to generate plots for
        data_dir: Directory containing ATS results CSVs
        output_dir: Directory to save plots
    
    Returns:
        Dict mapping team_slug to plot filename (relative path)
    """
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    plot_files = {}
    
    for team_slug in team_slugs:
        csv_file = data_path / f"ats_results_{team_slug}.csv"
        if not csv_file.exists():
            print(f"Warning: CSV not found for {team_slug}")
            continue
        
        plot_file = output_path / f"ats_{team_slug}.png"
        
        if generate_team_plot(team_slug, csv_file, plot_file):
            # Store relative path for HTML
            plot_files[team_slug] = f"plots/ats_{team_slug}.png"
        else:
            print(f"Failed to generate plot for {team_slug}")
    
    return plot_files


if __name__ == "__main__":
    # Test with a single team
    import sys
    if len(sys.argv) > 1:
        team = sys.argv[1]
        csv_file = f"ats_results_{team}.csv"
        output_file = f"plots/ats_{team}.png"
        Path("plots").mkdir(exist_ok=True)
        if generate_team_plot(team, csv_file, output_file):
            print(f"Plot generated: {output_file}")
        else:
            print(f"Failed to generate plot for {team}")
    else:
        print("Usage: python generate_ats_plots.py <team-slug>")
