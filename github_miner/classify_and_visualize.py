"""
classify_and_visualize.py - Step 5: Classify issues and commits, generate charts.

Reads merged JSONL files from data/merged/, classifies each record using
rule-based keyword matching, writes enriched JSONL to data/classified/,
and saves 8 PNG charts to data/figures/.

Usage:
    python classify_and_visualize.py
"""

import json
import logging
import os
from collections import Counter
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # must be before pyplot import — non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MERGED_DIR = os.path.join(DATA_DIR, "merged")
CLASSIFIED_DIR = os.path.join(DATA_DIR, "classified")
FIGURES_DIR = os.path.join(DATA_DIR, "figures")

os.makedirs(CLASSIFIED_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)


def load_jsonl(filepath):
    """Load a JSONL file into a list of dicts. Empty lines are skipped."""
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
    """Write a list of dicts as a JSONL file (one JSON object per line)."""
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _classify_vuln_subtype(text):
    """
    Classify vulnerability subtype from lowercased issue text.
    Returns one of: reentrancy, overflow, access_control, front_running, dos, other_vuln
    """
    if any(kw in text for kw in ["reentrancy", "re-entrancy", "reentrant"]):
        return "reentrancy"
    if any(kw in text for kw in ["overflow", "underflow", "integer overflow"]):
        return "overflow"
    if any(kw in text for kw in ["access control", "ownership", "onlyowner", "unauthorized", "privilege"]):
        return "access_control"
    if any(kw in text for kw in ["front-running", "frontrunning", "miner extractable", "mempool", "sandwich"]):
        return "front_running"
    if any(kw in text for kw in ["denial of service", "dos attack", "griefing", "block gas limit", "gas exhaustion"]):
        return "dos"
    return "other_vuln"


def classify_issue(issue):
    """
    Classify an issue by type and (for security issues) vulnerability subtype.

    Returns:
        (issue_type, vuln_subtype) where vuln_subtype is None for non-security issues.
    """
    text = " ".join([
        issue.get("title", "") or "",
        issue.get("body", "") or "",
    ]).lower()
    labels_lower = [l.lower() for l in issue.get("labels", [])]

    # Priority 1: security — checked first, before any label-based categories
    security_kws = [
        "reentrancy", "re-entrancy", "reentrant",
        "overflow", "underflow",
        "exploit", "vulnerability", "attack", "audit", "hack",
        "unauthorized", "denial of service", "dos attack", "access control",
        "front-running", "frontrunning",
    ]
    if any(kw in text for kw in security_kws):
        return "security", _classify_vuln_subtype(text)

    # Priority 2: gas — checked before bug to avoid "gas bug" misfiling
    gas_kws = ["gas optimization", "gas cost", "gas limit", "gas usage", "expensive", "cheaper"]
    if any(kw in text for kw in gas_kws):
        return "gas", None

    # Priority 3: bug — label or keyword
    bug_kws = ["doesn't work", "broken", "fails", "error", "crash", "incorrect", "wrong"]
    if any("bug" in l for l in labels_lower) or any(kw in text for kw in bug_kws):
        return "bug", None

    # Priority 4: feature — label or keyword
    feature_kws = ["add support", "implement", "would like", "feature request", "introduce"]
    if any("enhancement" in l for l in labels_lower) or any(kw in text for kw in feature_kws):
        return "feature", None

    # Priority 5: documentation — label or keyword
    doc_kws = ["readme", "docs", "comment", "typo", "spelling"]
    if any("doc" in l for l in labels_lower) or any(kw in text for kw in doc_kws):
        return "documentation", None

    # Priority 6: question — label or keyword
    question_kws = ["how do", "why does", "is it possible", "clarification"]
    if any("question" in l for l in labels_lower) or any(kw in text for kw in question_kws):
        return "question", None

    return "other", None


def _classify_fix_type(message):
    """
    Classify a commit by fix type using keyword matching on the commit message.
    security_patch is checked first to avoid being subsumed by bug_fix.
    """
    text = message.lower()
    rules = [
        ("security_patch", ["fix vulnerability", "security fix", "patch", "exploit", "reentrancy", "overflow"]),
        ("bug_fix",        ["fix", "bug", "resolve", "correct", "repair", "closes", "resolves"]),
        ("test",           ["test", "spec", "coverage", "assert", "unit test"]),
        ("refactor",       ["refactor", "clean up", "restructure", "rename", "simplify", "reorganize"]),
        ("feature",        ["add", "implement", "support", "introduce", "new feature"]),
        ("docs",           ["docs", "readme", "comment", "changelog", "documentation"]),
    ]
    for fix_type, keywords in rules:
        if any(kw in text for kw in keywords):
            return fix_type
    return "other"


def _classify_fix_scope(files_changed):
    """
    Classify commit scope from the list of changed file paths.
    Fully deterministic — no NLP required.
    """
    if not files_changed:
        return "other"

    def is_sol(f):
        return f.endswith(".sol")

    def is_test(f):
        return (
            f.endswith(".test.ts") or f.endswith(".test.js")
            or f.endswith(".spec.ts") or f.endswith(".spec.js")
            or "/test/" in f or "/tests/" in f or "/spec/" in f
            or f.startswith("test/") or f.startswith("tests/") or f.startswith("spec/")
        )

    def is_doc(f):
        return f.endswith(".md") or f.endswith(".txt")

    def is_infra(f):
        return any(f.endswith(ext) for ext in [".json", ".yaml", ".yml", ".sh", ".tf", ".toml"])

    sols  = [f for f in files_changed if is_sol(f)]
    tests = [f for f in files_changed if is_test(f)]
    docs  = [f for f in files_changed if is_doc(f)]

    if all(is_sol(f) for f in files_changed):
        return "contract_only"
    if all(is_test(f) for f in files_changed):
        return "test_only"
    if all(is_doc(f) for f in files_changed):
        return "docs_only"
    if sols and tests and all(is_sol(f) or is_test(f) for f in files_changed):
        return "contract_and_test"
    if sols:
        return "mixed"
    if all(is_infra(f) or is_doc(f) for f in files_changed):
        return "infrastructure"
    return "other"


def classify_commit(commit):
    """
    Classify a commit by fix type (from commit_message) and fix scope (from files_changed).

    Returns:
        (fix_type, fix_scope)
    """
    fix_type  = _classify_fix_type(commit.get("commit_message", ""))
    fix_scope = _classify_fix_scope(commit.get("files_changed", []))
    return fix_type, fix_scope


def generate_charts(issues, commits):
    pass


def main():
    # --- Load ---
    issues  = load_jsonl(os.path.join(MERGED_DIR, "issues_merged.jsonl"))
    commits = load_jsonl(os.path.join(MERGED_DIR, "commits_merged.jsonl"))
    logger.info(f"Loaded {len(issues)} issues, {len(commits)} commits")

    # --- Classify issues ---
    for issue in issues:
        issue_type, vuln_subtype = classify_issue(issue)
        issue["issue_type"]   = issue_type
        issue["vuln_subtype"] = vuln_subtype

    # --- Classify commits ---
    for commit in commits:
        fix_type, fix_scope = classify_commit(commit)
        commit["fix_type"]  = fix_type
        commit["fix_scope"] = fix_scope

    # --- Write enriched JSONL ---
    issues_out  = os.path.join(CLASSIFIED_DIR, "issues_classified.jsonl")
    commits_out = os.path.join(CLASSIFIED_DIR, "commits_classified.jsonl")
    write_jsonl(issues,  issues_out)
    write_jsonl(commits, commits_out)
    logger.info(f"Written classified issues  → {issues_out}")
    logger.info(f"Written classified commits → {commits_out}")

    # --- Summary table ---
    issue_type_counts  = Counter(i["issue_type"]   for i in issues)
    vuln_subtype_counts = Counter(
        i["vuln_subtype"] for i in issues if i["issue_type"] == "security"
    )
    fix_type_counts    = Counter(c["fix_type"]  for c in commits)
    fix_scope_counts   = Counter(c["fix_scope"] for c in commits)

    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)

    print("\nIssue Types:")
    for label, count in sorted(issue_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {label:20s} {count:5d}")

    print("\nVulnerability Subtypes (security issues only):")
    for label, count in sorted(vuln_subtype_counts.items(), key=lambda x: -x[1]):
        print(f"  {label:20s} {count:5d}")

    print("\nFix Types:")
    for label, count in sorted(fix_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {label:20s} {count:5d}")

    print("\nFix Scopes:")
    for label, count in sorted(fix_scope_counts.items(), key=lambda x: -x[1]):
        print(f"  {label:20s} {count:5d}")

    print("\n" + "=" * 60)

    # --- Charts (implemented in later tasks) ---
    generate_charts(issues, commits)


if __name__ == "__main__":
    main()
