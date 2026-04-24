# Classify and Visualize — Design Spec

**Date:** 2026-04-24  
**Pipeline step:** 5 (after `merge_shards.py`)  
**Script:** `classify_and_visualize.py`

---

## Overview

Reads the merged JSONL datasets produced by `merge_shards.py`, classifies every issue and fixing commit using rule-based keyword matching, writes enriched output files, and generates 8 static PNG charts to `data/figures/`.

No external APIs or ML models are required. Classification is fully deterministic and reproducible.

---

## Inputs

| File | Records |
|---|---|
| `data/merged/issues_merged.jsonl` | 8,678 issues |
| `data/merged/commits_merged.jsonl` | 1,863 commits |

---

## Issue Classification

### Level 1 — Issue Type

Classified from the issue `title`, `body`, and `labels` fields (case-insensitive). Rules are evaluated in priority order; first match wins. Falls back to `other`.

| Category | Signals |
|---|---|
| `security` | keywords: reentrancy, re-entrancy, overflow, underflow, exploit, vulnerability, attack, audit, hack |
| `gas` | keywords: gas optimization, gas cost, gas limit, expensive, cheaper — **checked before bug** to avoid "gas bug" being filed as bug |
| `bug` | label contains "bug" OR keywords: doesn't work, broken, fails, error, crash, incorrect, wrong |
| `feature` | label contains "enhancement" OR keywords: add support, implement, would like, feature request, introduce |
| `documentation` | label contains "doc" OR keywords: readme, docs, comment, typo, spelling |
| `question` | label contains "question" OR keywords: how do, why does, is it possible, clarification |
| `other` | fallback |

### Level 2 — Vulnerability Subtype

Applied only to issues classified as `security`. Falls back to `other_vuln`.

| Subtype | Keywords |
|---|---|
| `reentrancy` | reentrancy, re-entrancy, reentrant |
| `overflow` | overflow, underflow, integer overflow |
| `access_control` | access control, ownership, onlyOwner, unauthorized, privilege |
| `front_running` | front-running, frontrunning, miner extractable, mempool, sandwich |
| `dos` | denial of service, dos attack, griefing, block gas limit, gas exhaustion |
| `other_vuln` | fallback for security issues |

Non-security issues have `vuln_subtype` set to `null`.

---

## Fix / Commit Classification

### Fix Type

Classified from `commit_message` (case-insensitive). Rules evaluated in priority order; first match wins.

| Category | Keywords |
|---|---|
| `security_patch` | fix vulnerability, security fix, patch, exploit, reentrancy, overflow — **checked first** |
| `bug_fix` | fix, bug, resolve, correct, repair, closes, resolves |
| `refactor` | refactor, clean up, restructure, rename, simplify, reorganize |
| `feature` | add, implement, support, introduce, new feature |
| `test` | test, spec, coverage, assert, unit test |
| `docs` | docs, readme, comment, changelog, documentation |
| `other` | fallback |

### Fix Scope

Derived deterministically from `files_changed` — no NLP needed.

| Scope | Rule |
|---|---|
| `contract_only` | all changed files are `.sol` |
| `test_only` | all changed files are test files (`.test.ts`, `.test.js`, `test/`, `spec/`) |
| `contract_and_test` | mix of `.sol` and test files, no other types |
| `mixed` | `.sol` present alongside non-test files |
| `infrastructure` | no `.sol` files; only config/build files (`.json`, `.yaml`, `.yml`, `.sh`, `.tf`) |
| `docs_only` | only `.md` or `.txt` files |
| `other` | fallback |

---

## Outputs

### Enriched JSONL

- `data/classified/issues_classified.jsonl` — all original fields plus `issue_type` (str) and `vuln_subtype` (str or null)
- `data/classified/commits_classified.jsonl` — all original fields plus `fix_type` (str) and `fix_scope` (str)

### Charts (all PNG, saved to `data/figures/`)

| Filename | Chart type | Description |
|---|---|---|
| `issue_type_distribution.png` | Horizontal bar | Count of each issue type |
| `vuln_subtype_breakdown.png` | Horizontal bar | Count of each vulnerability subtype (security issues only) |
| `fix_type_distribution.png` | Horizontal bar | Count of each fix type |
| `issues_over_time.png` | Stacked line by month | Issue volume 2018–2024, stacked by issue type |
| `fix_scope_file_types.png` | Stacked horizontal bar | File extension breakdown across fixing commits |
| `issue_fix_heatmap.png` | Heatmap matrix | issue_type × fix_type co-occurrence counts |
| `resolution_time_boxplot.png` | Box plot | Days open for closed issues, grouped by issue_type |
| `keyword_frequency.png` | Horizontal bar | Top 15 matched keywords + GitHub labels across all issues |

---

## Script Structure

```
classify_and_visualize.py
├── load_jsonl(filepath) → list[dict]
├── write_jsonl(records, filepath)
├── classify_issue(issue) → (issue_type, vuln_subtype)
├── classify_commit(commit) → (fix_type, fix_scope)
├── generate_charts(issues, commits)
│   ├── plot_issue_type_distribution()
│   ├── plot_vuln_subtype_breakdown()
│   ├── plot_fix_type_distribution()
│   ├── plot_issues_over_time()
│   ├── plot_fix_scope_file_types()
│   ├── plot_issue_fix_heatmap()
│   ├── plot_resolution_time_boxplot()
│   └── plot_keyword_frequency()
└── main()
```

---

## Dependencies

- `matplotlib` — chart rendering
- `seaborn` — heatmap and box plot styling
- `pandas` — time-series grouping and pivot tables
- `python-dotenv` — already used in the pipeline

All should already be installed in the project environment. No new API keys required.

---

## Usage

```bash
python classify_and_visualize.py
```

Prints a summary table of classification counts to stdout. Output files are written to `data/classified/` and `data/figures/`.
