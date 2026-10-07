import io, json, runpy, sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT=Path(__file__).parents[1]/"scripts"/"evaluate_pr_precreation_gate.py"

def run(req):
    old=sys.stdin; sys.stdin=io.StringIO(json.dumps(req)); out=io.StringIO()
    try:
        with redirect_stdout(out): runpy.run_path(str(SCRIPT),run_name="__main__")
    finally: sys.stdin=old
    return json.loads(out.getvalue())

BASE={"repository":"StegVerse-Labs/Site","lane_id":"TASK-1"}

def test_no_predecessor_requires_complete_search():
    assert run({**BASE,"predecessor_search_complete":False})["disposition"]=="FAIL_CLOSED"
    assert run({**BASE,"predecessor_search_complete":True})["disposition"]=="ALLOW"

def test_open_and_superseded_open_deny():
    assert run({**BASE,"predecessor":{"state":"open"}})["predicate"]=="PREDECESSOR_PR_OPEN"
    assert run({**BASE,"predecessor":{"state":"open","superseded":True}})["predicate"]=="PREDECESSOR_PR_SUPERSEDED_BUT_OPEN"

def test_red_pending_and_changed_head_deny():
    p={"state":"closed","head_sha":"a","validated_head_sha":"a","required_checks":[{"conclusion":"failure"}],"merged":True}
    assert run({**BASE,"predecessor":p})["predicate"]=="PREDECESSOR_REQUIRED_CHECK_FAILED"
    p["required_checks"]=[{"conclusion":"in_progress"}]
    assert run({**BASE,"predecessor":p})["predicate"]=="PREDECESSOR_REQUIRED_CHECK_PENDING_OR_MISSING"
    p.update(head_sha="b",required_checks=[{"conclusion":"success"}])
    assert run({**BASE,"predecessor":p})["predicate"]=="PREDECESSOR_HEAD_CHANGED_AFTER_VALIDATION"

def test_only_validated_merged_or_explicit_closed_terminal_allows():
    p={"state":"closed","head_sha":"a","validated_head_sha":"a","required_checks":[{"conclusion":"success"}],"merged":True}
    assert run({**BASE,"predecessor":p})["disposition"]=="ALLOW"
    p["merged"]=False; p["terminal_disposition"]="SUPERSEDED"
    assert run({**BASE,"predecessor":p})["disposition"]=="ALLOW"
    p.pop("terminal_disposition")
    assert run({**BASE,"predecessor":p})["predicate"]=="PREDECESSOR_TERMINAL_DISPOSITION_UNPROVEN"
