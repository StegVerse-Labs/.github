#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/"control/current-user-ios-interaction-queue.json"

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--journal-report",type=Path,required=True,help="Fresh read-only StegOS journal replay/export summary")
    p.add_argument("--action-id",default=None,help="Optional candidate to evaluate after fresh-head reconciliation")
    args=p.parse_args()
    q=json.loads(QUEUE.read_text())
    obs=json.loads(args.journal_report.read_text())
    state=obs.get("state") or obs.get("journal_replay",{}).get("state")
    entries=obs.get("entries")
    tail=obs.get("tail_sha256")
    if entries is None and isinstance(obs.get("journal_replay"),dict):
        entries=obs["journal_replay"].get("entries")
        tail=obs["journal_replay"].get("tail_sha256")
    out={
      "schema":"stegverse.current-user-ios-interaction-admission-evaluation/v1",
      "decision":"HOLD",
      "authority_effect":"NONE_EVALUATION_ONLY",
      "queue_issue":q.get("issue"),
      "fresh_observation":{"state":state,"entries":entries,"tail_sha256":tail},
      "action_id":args.action_id,
      "reasons":[]
    }
    if state!="PASS" or not isinstance(entries,int) or not isinstance(tail,str) or len(tail)!=64:
        out["reasons"].append("fresh journal replay/export is incomplete or not PASS")
    candidate=None
    if args.action_id:
        candidate=next((x for x in q.get("candidate_actions",[]) if x.get("action_id")==args.action_id),None)
        if candidate is None: out["reasons"].append("candidate action is not registered")
    if not out["reasons"] and candidate is not None:
        if candidate.get("rerun_terminal_source") is True:
            out["reasons"].append("candidate would rerun a terminal source transition")
        else:
            out["decision"]="ELIGIBLE_FOR_SINGLE_ACTION_ADMISSION_REVIEW"
            out["reasons"].append("fresh head is structurally valid and candidate is registered; task-specific prerequisites still require reconciliation before queue mutation")
    print(json.dumps(out,sort_keys=True))
    return 0 if out["decision"]!="HOLD" else 2

if __name__=="__main__":
    raise SystemExit(main())
