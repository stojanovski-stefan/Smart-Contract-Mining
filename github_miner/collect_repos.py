"""
collect_repos.py - Step 1: Discover qualifying Solidity repositories on GitHub.

This script queries the GitHub Search API using monthly date windows to find
all public Solidity repositories with >5 stars that have issues enabled.
Results are deduplicated and saved to data/repos.json.

This script is run ONCE by either researcher. The resulting repos.json file
is then shared between both researchers for the subsequent collection steps.

Usage:
    python collect_repos.py
"""

import json
import logging
import os
import random
import time

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from config import DATE_WINDOWS, GITHUB_TOKEN, REPO_SEARCH_QUERY

# Configure logging for error/skip reporting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Directory for output data files
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def create_session():
    """
    Create a requests.Session pre-configured with GitHub API authentication
    headers. Using a session allows connection reuse across multiple requests.
    """
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        # Pin to a specific API version for reproducibility
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return session


def request_with_backoff(session, url, params=None, max_retries=5):
    """
    Make a GET request with exponential backoff and jitter on retryable errors.

    Retries on:
        - 403 (rate limit exceeded)
        - 429 (too many requests)
        - 500 (server error)

    Skips (returns None) on:
        - 404 (not found)
        - 422 (validation failed - e.g., bad search query)
        - 451 (unavailable for legal reasons)

    Args:
        session: requests.Session with auth headers
        url: API endpoint URL
        params: query parameters dict
        max_retries: maximum number of retry attempts

    Returns:
        Response object on success, None on skip-worthy errors
    """
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params)

            if response.status_code == 200:
                return response

            # Non-retryable errors: skip and log
            if response.status_code in (404, 422, 451):
                logger.warning(
                    f"Skipping {url} - HTTP {response.status_code}: "
                    f"{response.json().get('message', 'unknown error')}"
                )
                return None

            # Retryable errors: exponential backoff with jitter
            if response.status_code in (403, 429, 500):
                # Check for rate limit reset header to sleep precisely
                if response.status_code in (403, 429):
                    reset_time = response.headers.get("X-RateLimit-Reset")
                    if reset_time:
                        wait = max(int(reset_time) - time.time(), 0) + 1
                    else:
                        wait = (2 ** attempt) + random.uniform(0, 1)
                else:
                    wait = (2 ** attempt) + random.uniform(0, 1)

                logger.warning(
                    f"HTTP {response.status_code} on {url}, "
                    f"retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait)
                continue

            # Unexpected status code - log and retry
            logger.error(f"Unexpected HTTP {response.status_code} on {url}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception on {url}: {e}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    logger.error(f"Max retries exceeded for {url}")
    return None


def search_repos_in_window(session, start, end):
    """
    Search for Solidity repositories created within a specific date window.

    Uses the GitHub Search API with a created:{start}..{end} qualifier to
    narrow results. The API returns at most 1000 results per query, so
    monthly windows help stay under that cap for popular languages.

    Args:
        session: authenticated requests.Session
        start: start date string (YYYY-MM-DD), inclusive
        end: end date string (YYYY-MM-DD), exclusive

    Returns:
        List of repository dicts with selected fields
    """
    repos = []
    page = 1

    # Construct search query with date range filter
    # The created qualifier uses ".." for range (inclusive on both ends in GitHub)
    query = f"{REPO_SEARCH_QUERY} created:{start}..{end}"

    while True:
        params = {
            "q": query,
            "sort": "stars",
            "per_page": 100,  # Maximum allowed by the API
            "page": page,
        }

        response = request_with_backoff(
            session,
            "https://api.github.com/search/repositories",
            params=params,
        )

        if response is None:
            break

        data = response.json()
        items = data.get("items", [])

        if not items:
            break

        for repo in items:
            repos.append({
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "stargazers_count": repo["stargazers_count"],
                "created_at": repo["created_at"],
                "open_issues_count": repo["open_issues_count"],
                "has_issues": repo["has_issues"],
                "default_branch": repo["default_branch"],
            })

        # GitHub Search API caps at 1000 results (10 pages of 100)
        # Stop if we've hit the cap or there are no more pages
        total_count = data.get("total_count", 0)
        if page * 100 >= total_count or page * 100 >= 1000:
            break

        page += 1

    return repos


def main():
    """
    Main collection loop: iterate over all monthly date windows, collect repos,
    deduplicate, filter for issues-enabled, and save to data/repos.json.
    """
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not set. Please set it in your .env file or environment.")
        return

    session = create_session()
    all_repos = []

    logger.info(f"Searching across {len(DATE_WINDOWS)} monthly windows...")

    # Iterate over each monthly window with a progress bar
    for start, end in tqdm(DATE_WINDOWS, desc="Searching date windows"):
        window_repos = search_repos_in_window(session, start, end)
        all_repos.extend(window_repos)

        # Brief pause between search queries to be respectful of rate limits.
        # The Search API has a stricter rate limit (30 req/min for authenticated users).
        time.sleep(2)

    # Deduplicate by full_name - repos may appear in multiple windows if
    # the created_at date falls on a boundary or due to API quirks
    seen = set()
    unique_repos = []
    for repo in all_repos:
        if repo["full_name"] not in seen:
            seen.add(repo["full_name"])
            # Filter: only keep repos with issues enabled, since we need
            # to collect issues in the next step
            if repo["has_issues"]:
                unique_repos.append(repo)

    # Save to JSON file
    output_path = os.path.join(DATA_DIR, "repos.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_repos, f, indent=2, ensure_ascii=False)

    logger.info(f"Total repos found (before dedup): {len(all_repos)}")
    logger.info(f"Unique repos with issues enabled: {len(unique_repos)}")
    logger.info(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
