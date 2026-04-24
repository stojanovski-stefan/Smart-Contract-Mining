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
    pass


def write_jsonl(records, filepath):
    pass


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
    pass


def _classify_fix_scope(files_changed):
    pass


def classify_commit(commit):
    pass


def generate_charts(issues, commits):
    pass


def main():
    pass


if __name__ == "__main__":
    main()
