#!/usr/bin/env python3
"""
scrape_ats_results.py

Purpose: Scrape ATS (Against The Spread) results from TeamRankings NBA team pages.
This page shows detailed spread performance including the spread line, result, and diff.

Usage:
    python scrape_ats_results.py --team-slug los-angeles-clippers
    python scrape_ats_results.py --team-slug indiana-pacers --output my_data.csv
"""

import argparse
import csv
import sys
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape TeamRankings NBA ATS results for a specific team."
    )
    parser.add_argument(
        "--team-slug",
        type=str,
        required=True,
        help="NBA team slug (e.g., 'los-angeles-clippers')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: ats_results_<team-slug>.csv)"
    )
    return parser.parse_args()


def build_url(team_slug):
    """Construct the TeamRankings ATS results URL for the given team slug."""
    base_url = "https://www.teamrankings.com/nba/team/"
    return urljoin(base_url, f"{team_slug}/ats-results")


def fetch_page(url):
    """
    Fetch the HTML content from the given URL with a polite User-Agent.
    Returns the response object or exits on error.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch URL '{url}': {e}", file=sys.stderr)
        sys.exit(1)

    if response.status_code != 200:
        print(
            f"ERROR: Received HTTP {response.status_code} for URL '{url}'",
            file=sys.stderr
        )
        sys.exit(1)

    return response


def clean_text(text):
    """
    Clean text by stripping whitespace and removing non-breaking spaces.
    """
    if text is None:
        return ""
    # Replace non-breaking spaces and other whitespace variants
    cleaned = text.replace("\xa0", " ").replace("\u00a0", " ")
    return cleaned.strip()


def parse_spread(text):
    """
    Parse spread from TeamRankings format (e.g., "-6.0", "+3.5", "PK").
    Returns float or None if parsing fails.
    """
    text = clean_text(text)
    if not text or text == "-" or text.lower() == "n/a" or text.lower() == "pk":
        return None
    # Keep +/- sign for spread
    try:
        return float(text)
    except ValueError:
        return None


def parse_diff(text):
    """
    Parse diff (ATS margin) from TeamRankings format (e.g., "+7.0", "-1.0").
    Returns float or None if parsing fails.
    """
    text = clean_text(text)
    if not text or text == "-" or text.lower() == "n/a":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_result(text):
    """
    Parse result from TeamRankings format (e.g., "W by 1", "L by 12").
    Returns tuple (outcome, margin) where outcome is 'W' or 'L', margin is int.
    Returns (None, None) if parsing fails.
    """
    text = clean_text(text)
    if not text or text == "-":
        return None, None
    
    # Match "W by 12" or "L by 5"
    match = re.match(r"([WL])\s+by\s+(\d+)", text)
    if match:
        outcome = match.group(1)
        margin = int(match.group(2))
        return outcome, margin
    
    return None, None


def find_ats_table(soup):
    """
    Locate the 'Detailed ATS Performance' table in the HTML.
    Returns the table element or None if not found.
    """
    # Look for the table with ATS performance data
    # The page typically has a heading like "Detailed ATS Performance"
    tables = soup.find_all("table")
    
    for table in tables:
        # Check if table has the expected column headers
        thead = table.find("thead")
        if not thead:
            continue
        
        header_row = thead.find("tr")
        if not header_row:
            continue
        
        headers = [clean_text(th.get_text()).lower() for th in header_row.find_all("th")]
        headers_joined = " ".join(headers)
        
        # Look for ATS-specific columns: Date, Opponent, Line (with team prefix), Result, Diff
        # The line column is often named like "LAC Line" or "NY Line"
        if "date" in headers and "opponent" in headers and "line" in headers_joined and "diff" in headers:
            return table
    
    return None


def parse_ats_table(table, team_slug):
    """
    Parse the ATS results table and extract game data.
    Returns a list of dictionaries, one per game.
    """
    games = []
    
    tbody = table.find("tbody")
    if not tbody:
        return games
    
    rows = tbody.find_all("tr")
    
    for row in rows:
        cells = row.find_all("td")
        
        # The ATS results table typically has these columns:
        # Date, H/A/N, Opponent, Opp Rank, [Team] Line, Result, Diff
        # So we expect at least 7 columns
        if len(cells) < 7:
            continue
        
        # Extract raw cell text
        date_text = clean_text(cells[0].get_text())
        home_away_text = clean_text(cells[1].get_text())
        opponent_text = clean_text(cells[2].get_text())
        opp_rank_text = clean_text(cells[3].get_text())
        line_text = clean_text(cells[4].get_text())
        result_text = clean_text(cells[5].get_text())
        diff_text = clean_text(cells[6].get_text())
        
        # Skip header rows or empty rows
        if (date_text.lower() == "date" or 
            not date_text or 
            date_text == "-"):
            continue
        
        # Parse home/away
        home_away = home_away_text.lower() if home_away_text.lower() in ["home", "away", "neutral"] else "home"
        
        # Parse numeric fields
        spread = parse_spread(line_text)
        outcome, margin = parse_result(result_text)
        ats_diff = parse_diff(diff_text)
        
        # Try to parse opponent rank
        try:
            opp_rank = int(opp_rank_text) if opp_rank_text and opp_rank_text != "-" else None
        except ValueError:
            opp_rank = None
        
        # Build game dictionary
        game = {
            "date": date_text,
            "home_away": home_away,
            "opponent": opponent_text,
            "opp_rank": opp_rank,
            "spread": spread,
            "result": outcome,
            "margin": margin,
            "ats_diff": ats_diff
        }
        
        games.append(game)
    
    return games


def write_to_csv(games, output_path):
    """
    Write the list of game dictionaries to a CSV file.
    """
    fieldnames = ["date", "home_away", "opponent", "opp_rank", "spread", "result", "margin", "ats_diff"]
    
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(games)
    except IOError as e:
        print(f"ERROR: Failed to write to '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the scraper."""
    args = parse_arguments()
    
    # Build URL from team slug
    url = build_url(args.team_slug)
    print(f"Fetching data from: {url}")
    
    # Fetch the page
    response = fetch_page(url)
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the ATS table
    table = find_ats_table(soup)
    if table is None:
        print(
            "ERROR: Could not find the 'Detailed ATS Performance' table on the page.",
            file=sys.stderr
        )
        print("The page structure may have changed or the team slug may be incorrect.", file=sys.stderr)
        sys.exit(1)
    
    # Parse the table into game records
    games = parse_ats_table(table, args.team_slug)
    
    if not games:
        print("WARNING: No game data found in the table.", file=sys.stderr)
    
    # Determine output path
    output_path = args.output or f"ats_results_{args.team_slug}.csv"
    
    # Write to CSV
    write_to_csv(games, output_path)
    
    # Report success
    print(f"Successfully scraped {len(games)} games.")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
