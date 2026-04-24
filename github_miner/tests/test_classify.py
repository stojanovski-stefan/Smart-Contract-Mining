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
