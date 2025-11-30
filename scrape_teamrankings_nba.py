#!/usr/bin/env python3
"""
scrape_teamrankings_nba.py

Purpose: Scrape the "Results and Schedule -> Betting View" table from TeamRankings 
NBA team pages and save game-level betting data to CSV for building ATS and totals indices.

Usage:
    python scrape_teamrankings_nba.py --team-slug indiana-pacers
    python scrape_teamrankings_nba.py --team-slug indiana-pacers --output my_data.csv
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
        description="Scrape TeamRankings NBA betting data for a specific team."
    )
    parser.add_argument(
        "--team-slug",
        type=str,
        required=True,
        help="NBA team slug (e.g., 'indiana-pacers')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: teamrankings_<team-slug>.csv)"
    )
    return parser.parse_args()


def build_url(team_slug):
    """Construct the TeamRankings betting URL for the given team slug."""
    base_url = "https://www.teamrankings.com/nba/team/"
    return urljoin(base_url, f"{team_slug}/.betting")


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
    # Remove + sign if present, keep - sign
    text = text.replace("+", "")
    try:
        return float(text)
    except ValueError:
        return None


def parse_total(text):
    """
    Parse total from TeamRankings format (e.g., "Ov 229.5", "Un 218.0").
    Returns float or None if parsing fails.
    """
    text = clean_text(text)
    if not text or text == "-" or text.lower() == "n/a":
        return None
    # Extract number from "Ov 229.5" or "Un 218.0" format
    match = re.search(r"[Oo][vV]?\s+([\d.]+)", text)
    if match:
        return float(match.group(1))
    match = re.search(r"[Uu][nN]?\s+([\d.]+)", text)
    if match:
        return float(match.group(1))
    # Try direct float parsing as fallback
    try:
        return float(text)
    except ValueError:
        return None


def parse_int_or_none(text):
    """
    Parse a string to int, handling +/- signs for moneyline.
    Returns None if parsing fails or text is empty.
    """
    text = clean_text(text)
    if not text or text == "-" or text.lower() == "n/a":
        return None
    # Keep +/- signs for moneyline parsing
    try:
        return int(text)
    except ValueError:
        return None


def infer_home_away(opponent_text):
    """
    Infer home/away status from opponent text.
    Returns 'away' if '@' or 'at' prefix is found, 'home' otherwise.
    """
    opponent_text = clean_text(opponent_text).lower()
    # Check for common away indicators
    if opponent_text.startswith("@") or opponent_text.startswith("at "):
        return "away"
    return "home"


def extract_opponent_name(opponent_text):
    """
    Extract clean opponent name by removing '@' or 'at' prefix.
    """
    opponent_text = clean_text(opponent_text)
    # Remove leading @ or 'at ' (case-insensitive)
    opponent_text = re.sub(r"^@\s*", "", opponent_text)
    opponent_text = re.sub(r"^at\s+", "", opponent_text, flags=re.IGNORECASE)
    return opponent_text.strip()


def find_betting_table(soup):
    """
    Locate the 'Results and Schedule / Betting View' table in the HTML.
    Returns the table element or None if not found.
    """
    # Try finding tables and checking headers
    tables = soup.find_all("table")
    
    for table in tables:
        # Check if table has header row with expected columns
        thead = table.find("thead")
        if not thead:
            continue
        
        header_row = thead.find("tr")
        if not header_row:
            continue
        
        headers = [clean_text(th.get_text()).lower() for th in header_row.find_all("th")]
        
        # Check if this looks like the betting table
        # Must have: Date, Opponent, Result, Spread, Total
        required_cols = ["date", "opponent", "result", "spread", "total"]
        headers_joined = " ".join(headers)
        
        if all(col in headers_joined for col in required_cols):
            return table
    
    return None


def parse_scores(result_text):
    """
    Parse team_score and opp_score from result_raw field.
    Expected format: "W 116-105" or "L 98-102" or empty for future games.
    Returns (team_score, opp_score) as ints, or (None, None) if unparseable.
    """
    if not result_text:
        return None, None
    
    # Match patterns like "W 116-105" or "L 98-102"
    # Format: [W/L] [team_score]-[opp_score]
    match = re.search(r"[WL]\s+(\d+)\s*-\s*(\d+)", result_text)
    if match:
        team_score = int(match.group(1))
        opp_score = int(match.group(2))
        return team_score, opp_score
    
    return None, None


def parse_betting_table(table):
    """
    Parse the betting table and extract game data.
    Returns a list of dictionaries, one per game.
    """
    games = []
    
    tbody = table.find("tbody")
    if not tbody:
        return games
    
    rows = tbody.find_all("tr")
    
    for row in rows:
        cells = row.find_all("td")
        
        # Skip rows that don't have enough cells
        # Expected: Date, Opponent, Result, Location, W/L, Div, Spread, Total, Money
        if len(cells) < 9:
            continue
        
        # Extract raw cell text
        date_text = clean_text(cells[0].get_text())
        opponent_text = clean_text(cells[1].get_text())
        result_text = clean_text(cells[2].get_text())
        location_text = clean_text(cells[3].get_text())
        spread_text = clean_text(cells[6].get_text())
        total_text = clean_text(cells[7].get_text())
        money_text = clean_text(cells[8].get_text())
        
        # Skip header rows or footnote rows
        if (date_text.lower() == "date" or 
            "note:" in date_text.lower() or
            not date_text):
            continue
        
        # Get home/away from Location column and clean opponent name
        home_away = location_text.lower() if location_text.lower() in ["home", "away"] else "home"
        opponent = opponent_text  # Already clean in this table format
        
        # Parse scores from result
        team_score, opp_score = parse_scores(result_text)
        
        # Parse numeric fields
        spread = parse_spread(spread_text)
        total = parse_total(total_text)
        moneyline = parse_int_or_none(money_text)
        
        # Build game dictionary
        game = {
            "date": date_text,
            "opponent": opponent,
            "home_away": home_away,
            "result_raw": result_text,
            "team_score": team_score,
            "opp_score": opp_score,
            "spread": spread,
            "total": total,
            "moneyline": moneyline
        }
        
        games.append(game)
    
    return games


def write_to_csv(games, output_path):
    """
    Write the list of game dictionaries to a CSV file.
    """
    fieldnames = ["date", "opponent", "home_away", "result_raw", "team_score", "opp_score", "spread", "total", "moneyline"]
    
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
    
    # Find the betting table
    table = find_betting_table(soup)
    if table is None:
        print(
            "ERROR: Could not find the 'Results and Schedule / Betting View' table on the page.",
            file=sys.stderr
        )
        print("The page structure may have changed or the team slug may be incorrect.", file=sys.stderr)
        sys.exit(1)
    
    # Parse the table into game records
    games = parse_betting_table(table)
    
    if not games:
        print("WARNING: No game data found in the table.", file=sys.stderr)
    
    # Determine output path
    output_path = args.output or f"teamrankings_{args.team_slug}.csv"
    
    # Write to CSV
    write_to_csv(games, output_path)
    
    # Report success
    print(f"Successfully scraped {len(games)} games.")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
