# Classify and Visualize Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `classify_and_visualize.py` (pipeline Step 5) that classifies 8,678 issues and 1,863 commits using rule-based keyword matching, writes enriched JSONL outputs, and generates 8 PNG charts.

**Architecture:** Single script following existing pipeline conventions (`merge_shards.py` style). Classification functions are pure and tested with pytest. Chart functions use matplotlib/seaborn/pandas and write directly to `data/figures/`. `main()` orchestrates load → classify → write → chart.

**Tech Stack:** Python 3, pytest, matplotlib, seaborn, pandas, python-dotenv (all already installed)

---

## File Structure

| File | Purpose |
|---|---|
| `classify_and_visualize.py` | Main script — all classification logic and chart generation |
| `tests/test_classify.py` | Unit tests for `classify_issue` and `classify_commit` |

---

### Task 1: Skeleton + test infrastructure

**Files:**
- Create: `classify_and_visualize.py`
- Create: `tests/__init__.py`
- Create: `tests/test_classify.py`

- [ ] **Step 1: Create the script skeleton**

Create `classify_and_visualize.py` with all imports, directory constants, and empty stubs for every function:

```python
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
    pass


def classify_issue(issue):
    pass


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
```

- [ ] **Step 2: Create test infrastructure**

Create `tests/__init__.py` (empty file) and `tests/test_classify.py` with imports only:

```python
# tests/test_classify.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from classify_and_visualize import classify_issue, classify_commit
```

- [ ] **Step 3: Verify imports work**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python -c "import classify_and_visualize; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add classify_and_visualize.py tests/__init__.py tests/test_classify.py
git commit -m "feat: add classify_and_visualize skeleton and test file"
```

---

### Task 2: Implement `classify_issue` (both levels)

**Files:**
- Modify: `classify_and_visualize.py` — implement `_classify_vuln_subtype`, `classify_issue`
- Modify: `tests/test_classify.py` — add tests

- [ ] **Step 1: Write the failing tests**

Replace the contents of `tests/test_classify.py` with:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from classify_and_visualize import classify_issue, classify_commit


# --- classify_issue: Level 1 ---

def test_issue_classified_as_security_by_keyword():
    issue = {"title": "Reentrancy attack in withdraw()", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "security"

def test_issue_classified_as_security_overflow():
    issue = {"title": "Integer overflow in transfer", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "security"

def test_issue_classified_as_gas():
    issue = {"title": "gas optimization for loop", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "gas"

def test_gas_takes_priority_over_bug():
    # "gas cost error" should be gas, not bug
    issue = {"title": "gas cost error in function", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "gas"

def test_issue_classified_as_bug_by_label():
    issue = {"title": "Something wrong", "body": "", "labels": ["bug"]}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "bug"

def test_issue_classified_as_bug_by_keyword():
    issue = {"title": "Function broken after update", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "bug"

def test_issue_classified_as_feature_by_label():
    issue = {"title": "Add ERC721 support", "body": "", "labels": ["enhancement"]}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "feature"

def test_issue_classified_as_feature_by_keyword():
    issue = {"title": "Would like to add batch transfer", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "feature"

def test_issue_classified_as_documentation():
    issue = {"title": "Fix typo in README", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "documentation"

def test_issue_classified_as_question():
    issue = {"title": "How do I deploy this contract?", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "question"

def test_issue_classified_as_other():
    issue = {"title": "Monthly progress update", "body": "", "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "other"

def test_security_takes_priority_over_bug_label():
    # "vulnerability" in title should win over bug label
    issue = {"title": "vulnerability in contract", "body": "", "labels": ["bug"]}
    issue_type, _ = classify_issue(issue)
    assert issue_type == "security"

def test_none_body_handled():
    issue = {"title": "Some title", "body": None, "labels": []}
    issue_type, _ = classify_issue(issue)
    assert issue_type in {"security", "gas", "bug", "feature", "documentation", "question", "other"}


# --- classify_issue: Level 2 vuln subtype ---

def test_vuln_subtype_reentrancy():
    issue = {"title": "reentrancy in withdraw", "body": "", "labels": []}
    _, subtype = classify_issue(issue)
    assert subtype == "reentrancy"

def test_vuln_subtype_overflow():
    issue = {"title": "integer overflow in balances", "body": "", "labels": []}
    _, subtype = classify_issue(issue)
    assert subtype == "overflow"

def test_vuln_subtype_access_control():
    issue = {"title": "unauthorized access to admin functions", "body": "", "labels": []}
    _, subtype = classify_issue(issue)
    assert subtype == "access_control"

def test_vuln_subtype_front_running():
    issue = {"title": "front-running attack possible in auction", "body": "", "labels": []}
    _, subtype = classify_issue(issue)
    assert subtype == "front_running"

def test_vuln_subtype_dos():
    issue = {"title": "denial of service via block gas limit", "body": "", "labels": []}
    _, subtype = classify_issue(issue)
    assert subtype == "dos"

def test_vuln_subtype_other_for_generic_exploit():
    issue = {"title": "exploit in contract logic", "body": "", "labels": []}
    _, subtype = classify_issue(issue)
    assert subtype == "other_vuln"

def test_non_security_has_null_subtype():
    issue = {"title": "Add batch transfer feature", "body": "", "labels": ["enhancement"]}
    _, subtype = classify_issue(issue)
    assert subtype is None
```

- [ ] **Step 2: Run tests to confirm they all fail**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python -m pytest tests/test_classify.py -v 2>&1 | head -40
```

Expected: multiple `FAILED` lines, `TypeError` or `AssertionError` since functions return `None`.

- [ ] **Step 3: Implement `_classify_vuln_subtype` and `classify_issue`**

Replace the two stub functions in `classify_and_visualize.py`:

```python
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
```

- [ ] **Step 4: Run tests — all should pass**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python -m pytest tests/test_classify.py -v -k "issue"
```

Expected: all `test_issue_*` and `test_vuln_*` and `test_non_security_*` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add classify_and_visualize.py tests/test_classify.py
git commit -m "feat: implement classify_issue with two-level taxonomy"
```

---

### Task 3: Implement `classify_commit`

**Files:**
- Modify: `classify_and_visualize.py` — implement `_classify_fix_type`, `_classify_fix_scope`, `classify_commit`
- Modify: `tests/test_classify.py` — add commit tests

- [ ] **Step 1: Append commit tests to `tests/test_classify.py`**

Add the following to the end of `tests/test_classify.py`:

```python
# --- classify_commit: fix_type ---

def test_commit_security_patch():
    commit = {"commit_message": "fix reentrancy vulnerability in withdraw", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "security_patch"

def test_commit_security_patch_takes_priority_over_bug_fix():
    commit = {"commit_message": "fix overflow bug", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "security_patch"

def test_commit_bug_fix():
    commit = {"commit_message": "fix incorrect balance calculation", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "bug_fix"

def test_commit_refactor():
    commit = {"commit_message": "refactor token transfer logic", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "refactor"

def test_commit_feature():
    commit = {"commit_message": "add batch transfer support", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "feature"

def test_commit_test():
    commit = {"commit_message": "add unit test for withdraw", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "test"

def test_commit_docs():
    commit = {"commit_message": "update readme with deployment instructions", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "docs"

def test_commit_other():
    commit = {"commit_message": "bump version to 2.1.0", "files_changed": []}
    fix_type, _ = classify_commit(commit)
    assert fix_type == "other"


# --- classify_commit: fix_scope ---

def test_fix_scope_contract_only():
    commit = {"commit_message": "fix bug", "files_changed": ["contracts/Token.sol", "contracts/Vault.sol"]}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "contract_only"

def test_fix_scope_test_only():
    commit = {"commit_message": "add tests", "files_changed": ["test/Token.test.js", "test/Vault.test.ts"]}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "test_only"

def test_fix_scope_docs_only():
    commit = {"commit_message": "update docs", "files_changed": ["README.md", "CHANGELOG.md"]}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "docs_only"

def test_fix_scope_contract_and_test():
    commit = {"commit_message": "fix and test", "files_changed": ["contracts/Token.sol", "test/Token.test.ts"]}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "contract_and_test"

def test_fix_scope_mixed():
    commit = {"commit_message": "fix", "files_changed": ["contracts/Token.sol", "package.json"]}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "mixed"

def test_fix_scope_infrastructure():
    commit = {"commit_message": "update config", "files_changed": ["hardhat.config.js", "package.json", ".github/ci.yml"]}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "infrastructure"

def test_fix_scope_empty_files():
    commit = {"commit_message": "fix", "files_changed": []}
    _, fix_scope = classify_commit(commit)
    assert fix_scope == "other"
```

- [ ] **Step 2: Run new tests to confirm they fail**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python -m pytest tests/test_classify.py -v -k "commit" 2>&1 | head -30
```

Expected: all `test_commit_*` and `test_fix_scope_*` tests FAIL.

- [ ] **Step 3: Implement `_classify_fix_type`, `_classify_fix_scope`, `classify_commit`**

Replace the three stubs in `classify_and_visualize.py`:

```python
def _classify_fix_type(message):
    """
    Classify a commit by fix type using keyword matching on the commit message.
    security_patch is checked first to avoid being subsumed by bug_fix.
    """
    text = message.lower()
    rules = [
        ("security_patch", ["fix vulnerability", "security fix", "patch", "exploit", "reentrancy", "overflow"]),
        ("bug_fix",        ["fix", "bug", "resolve", "correct", "repair", "closes", "resolves"]),
        ("refactor",       ["refactor", "clean up", "restructure", "rename", "simplify", "reorganize"]),
        ("feature",        ["add", "implement", "support", "introduce", "new feature"]),
        ("test",           ["test", "spec", "coverage", "assert", "unit test"]),
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
        )

    def is_doc(f):
        return f.endswith(".md") or f.endswith(".txt")

    def is_infra(f):
        return any(f.endswith(ext) for ext in [".json", ".yaml", ".yml", ".sh", ".tf", ".toml", ".js", ".ts"])

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
```

- [ ] **Step 4: Run all tests**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python -m pytest tests/test_classify.py -v
```

Expected: all tests PASS. Total should be 37+ tests.

- [ ] **Step 5: Commit**

```bash
git add classify_and_visualize.py tests/test_classify.py
git commit -m "feat: implement classify_commit with fix_type and fix_scope"
```

---

### Task 4: Implement I/O and `main()` classification pass

**Files:**
- Modify: `classify_and_visualize.py` — implement `load_jsonl`, `write_jsonl`, `main()`

- [ ] **Step 1: Implement `load_jsonl` and `write_jsonl`**

Replace the two stubs (these are identical to `merge_shards.py` — copy the exact same implementations):

```python
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
```

- [ ] **Step 2: Implement `main()` — classification pass only (no charts yet)**

Replace the `main()` stub:

```python
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
```

- [ ] **Step 3: Run the script — verify classification works and files are written**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python classify_and_visualize.py
```

Expected output (exact counts will vary):
```
...INFO... Loaded 8678 issues, 1863 commits
...INFO... Written classified issues  → .../data/classified/issues_classified.jsonl
...INFO... Written classified commits → .../data/classified/commits_classified.jsonl
============================================================
CLASSIFICATION SUMMARY
============================================================
Issue Types:
  bug                  XXXX
  feature              XXXX
  security             XXXX
  ...
```

Also verify the output files exist:
```bash
wc -l data/classified/issues_classified.jsonl data/classified/commits_classified.jsonl
```

Expected: `8678` and `1863`.

- [ ] **Step 4: Commit**

```bash
git add classify_and_visualize.py
git commit -m "feat: implement I/O and classification pass in main()"
```

---

### Task 5: Charts 1–3 — Distribution bar charts

**Files:**
- Modify: `classify_and_visualize.py` — implement `generate_charts` with first 3 chart functions

- [ ] **Step 1: Implement `generate_charts` and the first 3 chart functions**

Replace the `generate_charts` stub:

```python
def generate_charts(issues, commits):
    logger.info("Generating charts...")
    sns.set_theme(style="whitegrid", palette="muted")

    _plot_issue_type_distribution(issues)
    _plot_vuln_subtype_breakdown(issues)
    _plot_fix_type_distribution(commits)
    _plot_issues_over_time(issues)
    _plot_fix_scope_file_types(commits)
    _plot_issue_fix_heatmap(issues, commits)
    _plot_resolution_time_boxplot(issues)
    _plot_keyword_frequency(issues)

    logger.info(f"All charts saved to {FIGURES_DIR}")


def _plot_issue_type_distribution(issues):
    counts = Counter(i["issue_type"] for i in issues)
    labels = sorted(counts, key=lambda k: counts[k])
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(labels, values, color=sns.color_palette("muted", len(labels)))
    ax.set_xlabel("Number of Issues")
    ax.set_title("Issue Type Distribution")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "issue_type_distribution.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")


def _plot_vuln_subtype_breakdown(issues):
    security_issues = [i for i in issues if i["issue_type"] == "security"]
    counts = Counter(i["vuln_subtype"] for i in security_issues)
    labels = sorted(counts, key=lambda k: counts[k])
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(labels, values, color=sns.color_palette("OrRd_r", len(labels)))
    ax.set_xlabel("Number of Security Issues")
    ax.set_title("Vulnerability Subtype Breakdown (Security Issues Only)")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "vuln_subtype_breakdown.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")


def _plot_fix_type_distribution(commits):
    counts = Counter(c["fix_type"] for c in commits)
    labels = sorted(counts, key=lambda k: counts[k])
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(labels, values, color=sns.color_palette("Blues_d", len(labels)))
    ax.set_xlabel("Number of Commits")
    ax.set_title("Fix Type Distribution")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "fix_type_distribution.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")
```

- [ ] **Step 2: Add no-op stubs for the 5 charts not yet implemented**

`generate_charts` calls all 8 chart functions. Add these stubs immediately below `_plot_fix_type_distribution` so the script doesn't crash when called:

```python
def _plot_issues_over_time(issues): pass
def _plot_fix_scope_file_types(commits): pass
def _plot_issue_fix_heatmap(issues, commits): pass
def _plot_resolution_time_boxplot(issues): pass
def _plot_keyword_frequency(issues): pass
```

- [ ] **Step 3: Run the script and verify 3 PNGs are created**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python classify_and_visualize.py 2>&1 | grep -E "Saved|ERROR"
ls data/figures/
```

Expected: `issue_type_distribution.png`, `vuln_subtype_breakdown.png`, `fix_type_distribution.png` present. No ERRORs.

- [ ] **Step 4: Commit**

```bash
git add classify_and_visualize.py
git commit -m "feat: add issue_type, vuln_subtype, fix_type distribution charts"
```

---

### Task 6: Charts 4–5 — Time series and fix scope

**Files:**
- Modify: `classify_and_visualize.py` — replace `_plot_issues_over_time` and `_plot_fix_scope_file_types` stubs

- [ ] **Step 1: Implement `_plot_issues_over_time`**

Replace the `_plot_issues_over_time` stub:

```python
def _plot_issues_over_time(issues):
    # Build a DataFrame with year-month and issue_type columns
    rows = []
    for issue in issues:
        created = issue.get("created_at", "")
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            rows.append({"month": dt.strftime("%Y-%m"), "issue_type": issue["issue_type"]})
        except ValueError:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        logger.warning("No date data for issues_over_time chart")
        return

    pivot = (
        df.groupby(["month", "issue_type"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(14, 6))
    pivot.plot(kind="area", stacked=True, ax=ax, alpha=0.75,
               colormap="tab10")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Issues")
    ax.set_title("Smart Contract Issues Over Time (2018–2024)")
    # Show every 6th month label to avoid crowding
    ticks = pivot.index.tolist()
    ax.set_xticks(range(0, len(ticks), 6))
    ax.set_xticklabels(ticks[::6], rotation=45, ha="right", fontsize=8)
    ax.legend(loc="upper left", fontsize=8)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "issues_over_time.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")
```

- [ ] **Step 2: Implement `_plot_fix_scope_file_types`**

Replace the `_plot_fix_scope_file_types` stub:

```python
def _plot_fix_scope_file_types(commits):
    # Count file extensions across all fixing commits
    ext_counter = Counter()
    for commit in commits:
        for f in commit.get("files_changed", []):
            ext = f.rsplit(".", 1)[-1].lower() if "." in f else "no_ext"
            ext_counter[ext] += 1

    # Keep top 10 extensions, group the rest as "other"
    top_n = 10
    top_exts = [ext for ext, _ in ext_counter.most_common(top_n)]
    other_count = sum(count for ext, count in ext_counter.items() if ext not in top_exts)

    labels = top_exts + (["other"] if other_count > 0 else [])
    values = [ext_counter[e] for e in top_exts] + ([other_count] if other_count > 0 else [])

    # Sort by value ascending for horizontal bar readability
    paired = sorted(zip(labels, values), key=lambda x: x[1])
    labels, values = zip(*paired)

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(labels, values, color=sns.color_palette("Set2", len(labels)))
    ax.set_xlabel("Total Files Changed")
    ax.set_title("File Types Touched in Fixing Commits")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "fix_scope_file_types.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")
```

- [ ] **Step 3: Run and verify 2 more PNGs appear**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python classify_and_visualize.py 2>&1 | grep "Saved"
ls data/figures/
```

Expected: `issues_over_time.png` and `fix_scope_file_types.png` now present alongside the 3 from Task 5.

- [ ] **Step 4: Commit**

```bash
git add classify_and_visualize.py
git commit -m "feat: add issues_over_time and fix_scope_file_types charts"
```

---

### Task 7: Charts 6–8 — Heatmap, box plot, keyword frequency

**Files:**
- Modify: `classify_and_visualize.py` — replace final 3 chart stubs

- [ ] **Step 1: Implement `_plot_issue_fix_heatmap`**

Replace the `_plot_issue_fix_heatmap` stub:

```python
def _plot_issue_fix_heatmap(issues, commits):
    # Build a lookup: (repo_full_name, issue_number) → issue_type
    issue_type_lookup = {
        (i["repo_full_name"], i["issue_number"]): i["issue_type"]
        for i in issues
    }

    rows = []
    for commit in commits:
        key = (commit["repo_full_name"], commit["issue_number"])
        issue_type = issue_type_lookup.get(key, "unknown")
        rows.append({"issue_type": issue_type, "fix_type": commit["fix_type"]})

    df = pd.DataFrame(rows)
    if df.empty:
        logger.warning("No data for issue_fix_heatmap")
        return

    pivot = df.groupby(["issue_type", "fix_type"]).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5, ax=ax)
    ax.set_title("Issue Type × Fix Type Co-occurrence")
    ax.set_xlabel("Fix Type")
    ax.set_ylabel("Issue Type")
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "issue_fix_heatmap.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")
```

- [ ] **Step 2: Implement `_plot_resolution_time_boxplot`**

Replace the `_plot_resolution_time_boxplot` stub:

```python
def _plot_resolution_time_boxplot(issues):
    rows = []
    for issue in issues:
        if issue.get("state") != "closed":
            continue
        created = issue.get("created_at", "")
        closed  = issue.get("closed_at",  "")
        if not created or not closed:
            continue
        try:
            dt_created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            dt_closed  = datetime.fromisoformat(closed.replace("Z", "+00:00"))
            days = (dt_closed - dt_created).days
            if days >= 0:
                rows.append({"issue_type": issue["issue_type"], "days_open": days})
        except ValueError:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        logger.warning("No resolution time data")
        return

    # Order categories by median resolution time for readability
    order = df.groupby("issue_type")["days_open"].median().sort_values().index.tolist()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x="days_open", y="issue_type", order=order,
                palette="muted", ax=ax, showfliers=False)
    ax.set_xlabel("Days Open (outliers hidden)")
    ax.set_ylabel("Issue Type")
    ax.set_title("Resolution Time by Issue Type (Closed Issues)")
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "resolution_time_boxplot.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")
```

- [ ] **Step 3: Implement `_plot_keyword_frequency`**

Replace the `_plot_keyword_frequency` stub:

```python
def _plot_keyword_frequency(issues):
    kw_counter    = Counter()
    label_counter = Counter()

    for issue in issues:
        for kw in issue.get("matched_keywords", []):
            kw_counter[kw] += 1
        for label in issue.get("labels", []):
            label_counter[label.lower()] += 1

    # Top 10 keywords + top 10 labels, labeled with source
    top_kws    = [(f"kw: {k}", v) for k, v in kw_counter.most_common(10)]
    top_labels = [(f"label: {k}", v) for k, v in label_counter.most_common(10)]
    combined   = sorted(top_kws + top_labels, key=lambda x: x[1])
    labels, values = zip(*combined)

    colors = ["#5b9bd5" if l.startswith("kw:") else "#ed7d31" for l in labels]

    fig, ax = plt.subplots(figsize=(9, 8))
    bars = ax.barh(labels, values, color=colors)
    ax.set_xlabel("Frequency")
    ax.set_title("Top 10 Matched Keywords vs. Top 10 GitHub Labels")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor="#5b9bd5", label="Matched keyword"),
                       Patch(facecolor="#ed7d31", label="GitHub label")]
    ax.legend(handles=legend_elements, loc="lower right")

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "keyword_frequency.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info(f"Saved {out}")
```

- [ ] **Step 4: Run and verify all 8 PNGs are present**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python classify_and_visualize.py 2>&1 | grep -E "Saved|ERROR|WARNING"
ls data/figures/
```

Expected — 8 files:
```
fix_scope_file_types.png
fix_type_distribution.png
issue_fix_heatmap.png
issue_type_distribution.png
issues_over_time.png
keyword_frequency.png
resolution_time_boxplot.png
vuln_subtype_breakdown.png
```

- [ ] **Step 5: Run the full test suite one final time**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
python -m pytest tests/test_classify.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add classify_and_visualize.py
git commit -m "feat: add heatmap, resolution time boxplot, and keyword frequency charts"
```

---

### Task 8: Final integration check and cleanup

**Files:**
- Modify: `classify_and_visualize.py` — add `.gitignore` entry for figures if needed

- [ ] **Step 1: Check `.gitignore` for data outputs**

```bash
cat .gitignore 2>/dev/null | grep -E "data/|figures|classified" || echo "no relevant entries"
```

If `data/` is not ignored, add entries so large JSONL files and generated figures aren't committed accidentally:

```bash
echo "data/classified/" >> .gitignore
echo "data/figures/" >> .gitignore
```

- [ ] **Step 2: Do a clean end-to-end run from scratch**

```bash
cd /Users/stefanstojanovski/Code/cse620F/Smart-Contract-Mining/github_miner
rm -rf data/classified data/figures
python classify_and_visualize.py
```

Expected: directories recreated, all 8 charts saved, summary table printed, no errors.

- [ ] **Step 3: Verify output record counts match input**

```bash
wc -l data/merged/issues_merged.jsonl data/classified/issues_classified.jsonl
wc -l data/merged/commits_merged.jsonl data/classified/commits_classified.jsonl
```

Expected: classified counts match merged counts exactly (every record classified, none dropped).

- [ ] **Step 4: Final commit**

```bash
git add .gitignore
git commit -m "chore: gitignore generated data/classified and data/figures dirs"
```
