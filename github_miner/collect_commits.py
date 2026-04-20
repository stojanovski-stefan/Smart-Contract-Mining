"""
collect_commits.py - Step 3: Find fixing commits linked to qualifying issues.

For each issue in a researcher's shard, this script searches commit messages
and pull request bodies for closing keywords (e.g., "fixes #123") that link
commits to issues. Found commits are recorded with metadata and saved to a
JSONL shard file.

The script caches per-repo commit and PR lists in memory to avoid redundant
API calls when multiple issues belong to the same repository.

Usage:
    python collect_commits.py --researcher evan
    python collect_commits.py --researcher stefan
"""

import argparse
import json
import logging
import os
import random
import re
import time

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from config import CLOSING_KEYWORDS, GITHUB_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Precompile the regex for matching closing keywords + issue numbers in commit
# messages and PR bodies. Pattern explanation:
#   \b(fixes|closes|resolves|fix|close|resolve)\b - one of the closing keywords
#   \s+  - one or more whitespace characters
#   #(\d+) - a '#' followed by the issue number (captured in group 2)
# Case-insensitive to catch "Fixes #42", "CLOSES #42", etc.
CLOSING_PATTERN = re.compile(
    r"\b(" + "|".join(CLOSING_KEYWORDS) + r")\b\s+#(\d+)",
    re.IGNORECASE,
)


def create_session():
    """
    Create a requests.Session with GitHub API authentication headers.
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
    Make a GET request with exponential backoff on retryable errors.

    Retryable: 403 (rate limit), 429 (too many requests), 500 (server error).
    Non-retryable: 404, 422, 451 - returns None so caller can skip.

    Args:
        session: authenticated requests.Session
        url: API endpoint
        params: query parameters
        max_retries: maximum retry attempts

    Returns:
        Response on success, None on non-retryable or exhausted retries
    """
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params)

            if response.status_code == 200:
                return response

            if response.status_code in (404, 422, 451):
                logger.warning(f"Skipping {url} - HTTP {response.status_code}")
                return None

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

            logger.error(f"Unexpected HTTP {response.status_code} on {url}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    logger.error(f"Max retries exceeded for {url}")
    return None


def fetch_all_commits(session, owner, repo):
    """
    Fetch all commits from a repository, paginating through all pages.

    This retrieves commits from the default branch. We fetch all commits
    upfront and cache them so that multiple issues in the same repo don't
    each trigger separate API calls.

    Args:
        session: authenticated requests.Session
        owner: repo owner
        repo: repo name

    Returns:
        List of commit dicts from the API (each contains sha, commit.message, etc.)
    """
    commits = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {"per_page": 100, "page": page}
        response = request_with_backoff(session, url, params=params)

        if response is None:
            break

        items = response.json()
        if not items:
            break

        commits.extend(items)
        page += 1

    return commits


def fetch_all_prs(session, owner, repo):
    """
    Fetch all closed pull requests from a repository, paginating through all pages.

    We only fetch closed PRs because we're looking for merged fix PRs that
    reference issues via closing keywords.

    Args:
        session: authenticated requests.Session
        owner: repo owner
        repo: repo name

    Returns:
        List of PR dicts from the API
    """
    prs = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        params = {"state": "closed", "per_page": 100, "page": page}
        response = request_with_backoff(session, url, params=params)

        if response is None:
            break

        items = response.json()
        if not items:
            break

        prs.extend(items)
        page += 1

    return prs


def fetch_pr_commits(session, owner, repo, pr_number):
    """
    Fetch all commits associated with a specific pull request.

    Args:
        session: authenticated requests.Session
        owner: repo owner
        repo: repo name
        pr_number: pull request number

    Returns:
        List of commit dicts from the PR
    """
    commits = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        params = {"per_page": 100, "page": page}
        response = request_with_backoff(session, url, params=params)

        if response is None:
            break

        items = response.json()
        if not items:
            break

        commits.extend(items)
        page += 1

    return commits


def fetch_commit_detail(session, owner, repo, sha):
    """
    Fetch detailed information for a single commit, including the list of
    files changed. The list endpoint only returns summary info; we need the
    individual commit endpoint for the files array.

    Args:
        session: authenticated requests.Session
        owner: repo owner
        repo: repo name
        sha: commit SHA

    Returns:
        List of filenames changed in this commit, or empty list on failure
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    response = request_with_backoff(session, url)

    if response is None:
        return []

    data = response.json()
    # Extract just the filenames from the files array
    return [f["filename"] for f in data.get("files", [])]


def find_closing_issue_numbers(text):
    """
    Extract all issue numbers referenced by closing keywords in a text string.

    For example, "Fixes #42 and closes #99" returns {42, 99}.

    Args:
        text: commit message or PR body to search

    Returns:
        Set of integer issue numbers found
    """
    if not text:
        return set()
    return {int(match.group(2)) for match in CLOSING_PATTERN.finditer(text)}


def main():
    """
    Main entry point: load issues shard, find linked fixing commits via
    commit message scanning and PR body matching, save to commits JSONL shard.
    """
    parser = argparse.ArgumentParser(
        description="Find fixing commits linked to qualifying issues."
    )
    parser.add_argument(
        "--researcher",
        required=True,
        choices=["evan", "stefan"],
        help="Researcher name to determine which issue shard to process.",
    )
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not set. Please set it in your .env file or environment.")
        return

    # Load this researcher's issue shard
    issues_path = os.path.join(DATA_DIR, f"issues_shard_{args.researcher}.jsonl")
    if not os.path.exists(issues_path):
        logger.error(f"Issue shard not found at {issues_path}. Run collect_issues.py first.")
        return

    issues = []
    with open(issues_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                issues.append(json.loads(line))

    logger.info(f"Loaded {len(issues)} issues from {issues_path}")

    session = create_session()

    # Cache commit and PR lists per repo to avoid redundant API calls.
    # Key: repo full_name, Value: list of commits/PRs from the API.
    # This is crucial because many issues may belong to the same repo,
    # and re-fetching all commits for each issue would be extremely wasteful.
    repo_commits_cache = {}
    repo_prs_cache = {}

    output_path = os.path.join(DATA_DIR, f"commits_shard_{args.researcher}.jsonl")
    total_linked = 0

    with open(output_path, "w", encoding="utf-8") as outfile:
        for issue in tqdm(issues, desc="Scanning issues for linked commits"):
            full_name = issue["repo_full_name"]
            owner, repo_name = full_name.split("/")
            issue_number = issue["issue_number"]

            # --- Step A: Scan commit messages for direct issue references ---

            # Fetch and cache all commits for this repo
            if full_name not in repo_commits_cache:
                logger.info(f"  Fetching commits for {full_name}...")
                repo_commits_cache[full_name] = fetch_all_commits(
                    session, owner, repo_name
                )
                time.sleep(1)  # Courtesy pause between repo fetches

            all_commits = repo_commits_cache[full_name]

            # Track fixing commits by SHA to deduplicate across direct and PR links
            fixing_commits = {}

            for commit in all_commits:
                message = commit.get("commit", {}).get("message", "")
                referenced_issues = find_closing_issue_numbers(message)

                # Check if this commit references our target issue number
                if issue_number in referenced_issues:
                    sha = commit["sha"]
                    if sha not in fixing_commits:
                        fixing_commits[sha] = {
                            "link_type": "direct",
                            "pr_number": None,
                            "commit": commit,
                        }

            # --- Step B: Scan PR bodies for issue references (secondary heuristic) ---
            # Some fixes are linked via PR descriptions rather than individual commit
            # messages, especially in squash-merge workflows.

            if full_name not in repo_prs_cache:
                logger.info(f"  Fetching PRs for {full_name}...")
                repo_prs_cache[full_name] = fetch_all_prs(
                    session, owner, repo_name
                )
                time.sleep(1)

            all_prs = repo_prs_cache[full_name]

            for pr in all_prs:
                pr_body = pr.get("body", "") or ""
                pr_title = pr.get("title", "") or ""
                # Check both PR body and title for closing references
                combined_text = f"{pr_title} {pr_body}"
                referenced_issues = find_closing_issue_numbers(combined_text)

                if issue_number in referenced_issues:
                    # This PR references our issue - fetch its commits
                    pr_number = pr["number"]
                    pr_commits = fetch_pr_commits(
                        session, owner, repo_name, pr_number
                    )

                    for commit in pr_commits:
                        sha = commit["sha"]
                        # Only add if not already found via direct commit scan
                        # (direct link takes precedence)
                        if sha not in fixing_commits:
                            fixing_commits[sha] = {
                                "link_type": "pull_request",
                                "pr_number": pr_number,
                                "commit": commit,
                            }

            # --- Step C: Write fixing commits to output ---
            # Skip issues with no linked commits (as specified in requirements)

            if not fixing_commits:
                continue

            for sha, info in fixing_commits.items():
                commit = info["commit"]

                # Fetch detailed commit info to get the list of changed files
                files_changed = fetch_commit_detail(
                    session, owner, repo_name, sha
                )

                # Extract author login - may be None for commits without
                # a linked GitHub account
                author = commit.get("author")
                author_login = author["login"] if author else None

                record = {
                    "repo_full_name": full_name,
                    "issue_number": issue_number,
                    "sha": sha,
                    "commit_message": commit.get("commit", {}).get("message", ""),
                    "author_login": author_login,
                    "committed_at": commit.get("commit", {}).get("committer", {}).get("date"),
                    "files_changed": files_changed,
                    "link_type": info["link_type"],
                    "pr_number": info["pr_number"],
                }

                outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_linked += 1

    logger.info(f"Done. Total fixing commit records: {total_linked}")
    logger.info(f"Output: {output_path}")


if __name__ == "__main__":
    main()
