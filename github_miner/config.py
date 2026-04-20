"""
config.py - Central configuration for the GitHub mining pipeline.

Defines API tokens, search keywords, date ranges, shard assignments for
parallel data collection between two researchers (Evan and Stefan), and
constants used across all collection scripts.

Usage:
    Import this module in any pipeline script:
        from config import GITHUB_TOKEN, KEYWORDS, DATE_WINDOWS, ...
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
load_dotenv()

# GitHub personal access token - must be set in environment or .env file
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Keywords for filtering smart-contract-related issues.
# An issue must contain at least one of these (case-insensitive) in its
# title or body to be considered relevant to our study.
KEYWORDS = [
    "smart contract",
    "solidity",
    "evm",
    "ethereum",
    "reentrancy",
    "overflow",
    "gas",
    "transaction",
    "exploit",
    "vulnerability",
    "token",
    "transfer",
]

# GitHub Search API query string for discovering Solidity repositories.
# Filters: must be primarily Solidity, at least 5 stars (quality signal),
# and publicly accessible.
REPO_SEARCH_QUERY = "language:Solidity stars:>5 is:public"

# Date windows: monthly intervals from 2018-01-01 to 2024-12-31.
# Each tuple is (start_date_inclusive, end_date_exclusive_of_next_month).
# We use monthly granularity because the GitHub Search API limits results
# to 1000 per query; smaller windows reduce the chance of hitting that cap.
DATE_WINDOWS = []
for year in range(2018, 2025):
    for month in range(1, 13):
        start = f"{year}-{month:02d}-01"
        # Calculate end date as the first day of the next month
        if month == 12:
            end = f"{year + 1}-01-01"
        else:
            end = f"{year}-{month + 1:02d}-01"
        DATE_WINDOWS.append((start, end))

# Shard assignments split the DATE_WINDOWS list between two researchers
# so they can collect data in parallel without overlap.
# First 42 months: 2018-01 through 2021-06 (Evan)
# Remaining 42 months: 2021-07 through 2024-12 (Stefan)
SHARD_ASSIGNMENTS = {
    "evan": DATE_WINDOWS[:42],
    "stefan": DATE_WINDOWS[42:],
}

# Keywords that indicate a commit or PR closes/fixes an issue.
# Used in regex matching against commit messages and PR bodies.
CLOSING_KEYWORDS = ["fixes", "closes", "resolves", "fix", "close", "resolve"]

# File extensions that identify smart contract source files.
# Used to check whether a fixing commit touches actual contract code.
SMART_CONTRACT_FILE_EXTENSIONS = [".sol"]
