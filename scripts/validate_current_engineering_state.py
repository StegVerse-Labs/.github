#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"data/current-engineering-state.json"
ALLOWED={"DECLARED","SOURCE_IMPLEMENTED","SOURCE_VALIDATED","RUNTIME_OBSERVED","EXTERNAL_EXECUTION_OBSERVED","CUSTODY_OBSERVED","RECONSTRUCTION_OBSERVED","INDEPENDENTLY_REPRODUCED"}
NON_SOURCE={"RUNTIME_OBSERVED","EXTERNAL_EXECUTION_OBSERVED","CUSTODY_OBSERVED","RECONSTRUCTION_OBSERVED","INDEPENDENTLY_REPRODUCED"}

def fail(msg): raise SystemExit(msg)
def main():
 d=json.loads(P.read_text())
 if d.get("schema")!="stegverse.current-engineering-state/v1": fail("schema")
 if d.get("historical_assessment",{}).get("rule") is None: fail("historical assessment immutability rule missing")
 bounds=d.get("authority_boundaries") or {}
 vals=list(bounds.values())
 if len(vals)!=len(set(vals)): fail("contradictory authority assignments")
 seen=set()
 for row in d.get("invariants",[]):
  iid=row.get("invariant_id")
  if not iid or iid in seen: fail("missing/duplicate invariant_id")
  seen.add(iid)
  ec=row.get("evidence_class")
  if ec not in ALLOWED: fail(f"{iid}: invalid evidence_class")
  refs=row.get("derivation_evidence_refs") or []
  if not refs: fail(f"{iid}: evidence refs required")
  for ref in refs:
   if ref.startswith(("http:","https:","github-")): continue
   if not (ROOT/ref).exists(): fail(f"{iid}: stale/missing evidence ref {ref}")
  for b in row.get("authority_boundaries") or []:
   if b not in bounds: fail(f"{iid}: unknown authority boundary {b}")
  if ec in NON_SOURCE and not row.get("class_native_evidence_refs"):
   fail(f"{iid}: unsupported status promotion to {ec}")
  if row.get("independent_observation_status")!="NOT_OBSERVED" and not row.get("independent_observation_refs"):
   fail(f"{iid}: independent observation status lacks evidence")
 ev=d.get("evaluator_semantics") or {}
 for k in ("observations_are_evidence_not_authority","independent_observation_does_not_mutate_canonical_state","independent_observation_does_not_grant_authority"):
  if ev.get(k) is not True: fail(k)
 print("CURRENT_ENGINEERING_STATE_VALIDATION_PASS")
if __name__=="__main__": main()
