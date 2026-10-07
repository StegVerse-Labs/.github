#!/usr/bin/env python3
"""Fail-closed predecessor PR lane gate for PR-creating callers.

Reads one JSON request on stdin. GitHub observation is supplied by the caller so
this evaluator remains deterministic and credential-free.
"""
import json, sys

DENY = {
    "open": "PREDECESSOR_PR_OPEN",
    "superseded_but_open": "PREDECESSOR_PR_SUPERSEDED_BUT_OPEN",
    "failed": "PREDECESSOR_REQUIRED_CHECK_FAILED",
    "pending": "PREDECESSOR_REQUIRED_CHECK_PENDING_OR_MISSING",
    "missing": "PREDECESSOR_REQUIRED_CHECK_PENDING_OR_MISSING",
    "head_changed": "PREDECESSOR_HEAD_CHANGED_AFTER_VALIDATION",
    "terminal_unproven": "PREDECESSOR_TERMINAL_DISPOSITION_UNPROVEN",
}

def emit(disposition, predicate, req):
    print(json.dumps({
        "schema":"stegverse.pr-precreation-disposition/v1",
        "disposition":disposition,
        "predicate":predicate,
        "repository":req.get("repository"),
        "lane_id":req.get("lane_id"),
        "predecessor_pr":req.get("predecessor_pr"),
        "authority_effect":"NONE_COORDINATION_ONLY",
    }, sort_keys=True))

def main():
    req=json.load(sys.stdin)
    if not req.get("repository") or not req.get("lane_id"):
        emit("FAIL_CLOSED","PRECREATION_IDENTITY_INCOMPLETE",req); return
    pred=req.get("predecessor")
    if pred is None:
        if req.get("predecessor_search_complete") is True:
            emit("ALLOW","NO_PREDECESSOR_LANE_EXISTS",req)
        else:
            emit("FAIL_CLOSED","PREDECESSOR_SEARCH_NOT_PROVEN_COMPLETE",req)
        return
    if pred.get("state")=="open":
        emit("DENY",DENY["superseded_but_open"] if pred.get("superseded") else DENY["open"],req); return
    if pred.get("validated_head_sha") and pred.get("head_sha") != pred.get("validated_head_sha"):
        emit("DENY",DENY["head_changed"],req); return
    checks=pred.get("required_checks")
    if not isinstance(checks,list) or not checks:
        emit("DENY",DENY["missing"],req); return
    conclusions={str(x.get("conclusion") or "").lower() for x in checks}
    if conclusions & {"failure","failed","cancelled","timed_out","action_required"}:
        emit("DENY",DENY["failed"],req); return
    if any(c not in {"success","skipped","neutral"} for c in conclusions):
        emit("DENY",DENY["pending"],req); return
    if pred.get("merged") is True:
        emit("ALLOW","PREDECESSOR_MERGED_EXACT_HEAD_VALIDATED",req); return
    if pred.get("state")=="closed" and pred.get("terminal_disposition") in {"SUPERSEDED","SATISFIED_BY_EXISTING_STATE","RETIRED"}:
        emit("ALLOW","PREDECESSOR_CLOSED_WITH_EXPLICIT_TERMINAL_DISPOSITION",req); return
    emit("DENY",DENY["terminal_unproven"],req)

if __name__=="__main__":
    main()
