
import logging
import sys
import os

# Adjust path to import scraper
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper import get_next_week_matches

# Configure logging to see output
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    print("Testing get_next_week_matches...")
    matches = get_next_week_matches()
    print("Matches found:", matches)
