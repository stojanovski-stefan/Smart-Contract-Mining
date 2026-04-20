"""
collect_issues.py - Step 2: Collect smart-contract-related issues from GitHub repos.

Each researcher runs this script independently with their assigned shard (date range).
The script iterates over all repos in data/repos.json, fetches issues created within
the researcher's assigned date windows, applies keyword filtering to identify
smart-contract-relevant issues, and saves qualifying issues to a JSONL shard file.

Usage:
    python collect_issues.py --researcher evan
    python collect_issues.py --researcher stefan
"""

import argparse
import json
import logging
import os
import random
import time
from datetime import datetime

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from config import GITHUB_TOKEN, KEYWORDS, SHARD_ASSIGNMENTS

# Configure logging - errors and skipped repos go to stderr via logging,
# progress updates use tqdm
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Output directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def create_session():
    """
    Create a requests.Session with GitHub API authentication headers.
    Reusing a session enables HTTP keep-alive for faster sequential requests.
    """
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return session


def request_with_backoff(session, url, params=None, max_retries=5):
    """
    Make a GET request with exponential backoff and jitter on retryable errors.

    Retryable (403, 429, 500): wait and retry up to max_retries times.
    Non-retryable (404, 422, 451): return None immediately (caller should skip).

    Args:
        session: authenticated requests.Session
        url: full API URL
        params: optional query parameters
        max_retries: max retry attempts before giving up

    Returns:
        Response object on success, None on non-retryable or exhausted retries
    """
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params)

            if response.status_code == 200:
                return response

            # Non-retryable: resource doesn't exist, bad request, or legal block
            if response.status_code in (404, 422, 451):
                logger.warning(
                    f"Skipping {url} - HTTP {response.status_code}"
                )
                return None

            # Retryable: rate limit, too many requests, or server error
            if response.status_code in (403, 429, 500):
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time and response.status_code in (403, 429):
                    wait = max(int(reset_time) - time.time(), 0) + 1
                else:
                    wait = (2 ** attempt) + random.uniform(0, 1)

                logger.warning(
                    f"HTTP {response.status_code} on {url}, "
                    f"retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait)
                continue

            # Unexpected status - retry with backoff
            logger.error(f"Unexpected HTTP {response.status_code} on {url}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    logger.error(f"Max retries exceeded for {url}")
    return None


def fetch_issues_for_window(session, owner, repo, state, start, end):
    """
    Fetch all issues of a given state from a repo within a date window.

    We use the 'since' parameter to get issues updated since the start date,
    then filter by created_at to only keep issues actually created in the window.
    The Issues API 'since' param filters by updated_at, not created_at, so we
    must do client-side filtering on created_at to ensure correct windowing.

    Note: We fetch state=closed and state=open separately because the API
    doesn't support fetching both with date filtering in one call - the 'state'
    parameter is required to be a single value.

    Args:
        session: authenticated requests.Session
        owner: repository owner
        repo: repository name
        state: "open" or "closed"
        start: window start date (YYYY-MM-DD)
        end: window end date (YYYY-MM-DD)

    Returns:
        List of issue dicts that fall within the date window
    """
    issues = []
    page = 1

    while True:
        params = {
            "state": state,
            "since": start,  # Only return issues updated at or after this date
            "per_page": 100,
            "direction": "asc",  # Oldest first for consistent pagination
            "page": page,
        }

        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        response = request_with_backoff(session, url, params=params)

        if response is None:
            break

        items = response.json()

        # Empty page means we've exhausted all results
        if not items:
            break

        for item in items:
            # The Issues API also returns pull requests (they share the same
            # endpoint). Skip items that have a pull_request key.
            if "pull_request" in item:
                continue

            # Filter by created_at to ensure the issue was actually created
            # within our target window, not just updated during it
            created = item.get("created_at", "")
            if created >= start and created < end:
                issues.append(item)

        page += 1

    return issues


def matches_keywords(title, body):
    """
    Check if an issue's title or body contains any of the smart contract keywords.

    Case-insensitive matching. Returns the list of matched keywords so we can
    record which terms triggered inclusion (useful for later analysis).

    Args:
        title: issue title string
        body: issue body string (may be None for empty issues)

    Returns:
        List of matched keyword strings (empty if no match)
    """
    matched = []
    # Combine title and body for unified search; handle None body
    text = f"{title} {body or ''}".lower()

    for keyword in KEYWORDS:
        if keyword.lower() in text:
            matched.append(keyword)

    return matched


def main():
    """
    Main entry point: parse args, load repos, iterate over assigned date windows,
    collect and filter issues, write qualifying issues to JSONL shard file.
    """
    parser = argparse.ArgumentParser(
        description="Collect smart-contract-related issues from GitHub repos."
    )
    parser.add_argument(
        "--researcher",
        required=True,
        choices=["evan", "stefan"],
        help="Researcher name to determine which date shard to process.",
    )
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not set. Please set it in your .env file or environment.")
        return

    # Load the shared repository list
    repos_path = os.path.join(DATA_DIR, "repos.json")
    if not os.path.exists(repos_path):
        logger.error(f"repos.json not found at {repos_path}. Run collect_repos.py first.")
        return

    with open(repos_path, "r", encoding="utf-8") as f:
        repos = json.load(f)

    # Get this researcher's assigned date windows
    date_windows = SHARD_ASSIGNMENTS[args.researcher]
    logger.info(
        f"Researcher: {args.researcher}, "
        f"Date windows: {date_windows[0][0]} to {date_windows[-1][1]}, "
        f"Repos to process: {len(repos)}"
    )

    session = create_session()
    output_path = os.path.join(DATA_DIR, f"issues_shard_{args.researcher}.jsonl")
    total_issues = 0

    # Open output file in append mode so we can resume if interrupted
    # (duplicate filtering happens in merge step)
    with open(output_path, "w", encoding="utf-8") as outfile:
        # Progress bar over repos (outer loop)
        for repo_info in tqdm(repos, desc="Processing repos"):
            full_name = repo_info["full_name"]
            owner, repo_name = full_name.split("/")

            repo_issue_count = 0

            # For each date window assigned to this researcher
            for start, end in date_windows:
                # Fetch closed issues and open issues separately.
                # We do two passes because the API's state parameter only accepts
                # a single value, and we want both states for completeness.
                for state in ["closed", "open"]:
                    issues = fetch_issues_for_window(
                        session, owner, repo_name, state, start, end
                    )

                    for issue in issues:
                        title = issue.get("title", "")
                        body = issue.get("body", "")

                        # Apply keyword filter - only keep issues relevant to
                        # smart contracts / Solidity development
                        matched = matches_keywords(title, body)
                        if not matched:
                            continue

                        # Extract label names from the nested label objects
                        labels = [
                            label["name"]
                            for label in issue.get("labels", [])
                        ]

                        # Build the output record with all fields needed for analysis
                        record = {
                            "repo_full_name": full_name,
                            "issue_number": issue["number"],
                            "title": title,
                            "body": body,
                            "state": issue["state"],
                            "labels": labels,
                            "created_at": issue["created_at"],
                            "closed_at": issue.get("closed_at"),
                            "comments_url": issue["comments_url"],
                            "html_url": issue["html_url"],
                            "matched_keywords": matched,
                        }

                        # Write as newline-delimited JSON (one record per line)
                        outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                        repo_issue_count += 1
                        total_issues += 1

            if repo_issue_count > 0:
                logger.info(f"  {full_name}: {repo_issue_count} qualifying issues")

            # Sleep between repos to stay well within rate limits.
            # The Issues API shares the 5000 req/hour limit with other endpoints.
            time.sleep(1)

    logger.info(f"Done. Total qualifying issues saved: {total_issues}")
    logger.info(f"Output: {output_path}")


if __name__ == "__main__":
    main()
