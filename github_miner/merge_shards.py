"""
merge_shards.py - Step 4: Merge shard outputs from both researchers.

After both Evan and Stefan have completed their collection runs, one researcher
runs this script to combine the JSONL shard files, deduplicate records, and
produce unified output files with summary statistics.

Usage:
    python merge_shards.py
"""

import json
import logging
import os
from collections import Counter

from dotenv import load_dotenv

# Load .env for consistency (not strictly needed here, but keeps imports uniform)
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MERGED_DIR = os.path.join(DATA_DIR, "merged")
os.makedirs(MERGED_DIR, exist_ok=True)


def load_jsonl(filepath):
    """
    Load a JSONL file into a list of dicts.

    Each line in the file is a standalone JSON object. Empty lines are skipped.

    Args:
        filepath: path to the .jsonl file

    Returns:
        List of parsed JSON objects (dicts)
    """
    records = []
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return records

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records


def write_jsonl(records, filepath):
    """
    Write a list of dicts as a JSONL file (one JSON object per line).

    Args:
        records: list of dicts to serialize
        filepath: output file path
    """
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    """
    Merge issue and commit shards, deduplicate, write merged files,
    and print comprehensive summary statistics.
    """
    # --- Merge Issues ---
    # Load both researchers' issue shards
    issues_evan = load_jsonl(os.path.join(DATA_DIR, "issues_shard_evan.jsonl"))
    issues_stefan = load_jsonl(os.path.join(DATA_DIR, "issues_shard_stefan.jsonl"))

    logger.info(f"Issues from Evan's shard: {len(issues_evan)}")
    logger.info(f"Issues from Stefan's shard: {len(issues_stefan)}")

    # Deduplicate by (repo_full_name, issue_number) - an issue might appear
    # in both shards if it was updated across date window boundaries
    all_issues = issues_evan + issues_stefan
    seen_issues = set()
    unique_issues = []

    for issue in all_issues:
        key = (issue["repo_full_name"], issue["issue_number"])
        if key not in seen_issues:
            seen_issues.add(key)
            unique_issues.append(issue)

    issues_output = os.path.join(MERGED_DIR, "issues_merged.jsonl")
    write_jsonl(unique_issues, issues_output)
    logger.info(f"Merged issues (deduplicated): {len(unique_issues)}")

    # --- Merge Commits ---
    # Load both researchers' commit shards
    commits_evan = load_jsonl(os.path.join(DATA_DIR, "commits_shard_evan.jsonl"))
    commits_stefan = load_jsonl(os.path.join(DATA_DIR, "commits_shard_stefan.jsonl"))

    logger.info(f"Commits from Evan's shard: {len(commits_evan)}")
    logger.info(f"Commits from Stefan's shard: {len(commits_stefan)}")

    # Deduplicate by (repo_full_name, sha) - a single commit could be linked
    # to multiple issues in the same repo, but we keep one record per unique commit
    all_commits = commits_evan + commits_stefan
    seen_commits = set()
    unique_commits = []

    for commit in all_commits:
        key = (commit["repo_full_name"], commit["sha"])
        if key not in seen_commits:
            seen_commits.add(key)
            unique_commits.append(commit)

    commits_output = os.path.join(MERGED_DIR, "commits_merged.jsonl")
    write_jsonl(unique_commits, commits_output)
    logger.info(f"Merged commits (deduplicated): {len(unique_commits)}")

    # --- Summary Statistics ---
    print("\n" + "=" * 60)
    print("MERGE SUMMARY")
    print("=" * 60)

    # Total unique repos that have at least one qualifying issue
    repos_with_issues = set(issue["repo_full_name"] for issue in unique_issues)
    print(f"\nTotal unique repos with qualifying issues: {len(repos_with_issues)}")

    # Issue state breakdown
    closed_issues = sum(1 for i in unique_issues if i["state"] == "closed")
    open_issues = sum(1 for i in unique_issues if i["state"] == "open")
    print(f"\nTotal qualifying issues: {len(unique_issues)}")
    print(f"  - Closed: {closed_issues}")
    print(f"  - Open:   {open_issues}")

    # Commit statistics
    print(f"\nTotal fixing commits linked: {len(unique_commits)}")

    # Issues with at least one linked commit vs. those without
    # Build set of (repo, issue_number) pairs that have commits
    issues_with_commits = set(
        (c["repo_full_name"], c["issue_number"]) for c in unique_commits
    )
    issues_linked = sum(
        1 for i in unique_issues
        if (i["repo_full_name"], i["issue_number"]) in issues_with_commits
    )
    issues_not_linked = len(unique_issues) - issues_linked
    print(f"\nIssues with at least one linked commit: {issues_linked}")
    print(f"Issues with no linked commit (excluded): {issues_not_linked}")

    # Top 10 most common matched keywords across all issues
    # Each issue has a matched_keywords list; count occurrences of each keyword
    keyword_counter = Counter()
    for issue in unique_issues:
        for kw in issue.get("matched_keywords", []):
            keyword_counter[kw] += 1

    print("\nTop 10 most common matched keywords:")
    for keyword, count in keyword_counter.most_common(10):
        print(f"  {keyword:20s} : {count}")

    print("\n" + "=" * 60)
    print(f"Output files:")
    print(f"  {issues_output}")
    print(f"  {commits_output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
