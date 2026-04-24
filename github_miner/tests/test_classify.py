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
