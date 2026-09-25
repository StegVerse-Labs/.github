#!/usr/bin/env python3
"""Read-only exact Registry/shard/index/COSV reconciliation; not session admission."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.cosv import encode_task,validate_record
TASKS=["ECOSYSTEM-INGRESS-AI-BOUNDARIES-001","WORKER-TASK-RESOURCE-COST-LINKAGE-001","OPTICAL-PHYSICAL-STATE-REPLAY-RESEARCH-001","GOVERNANCE-METERED-POLICY-RECOVERY-001"]
OPTICAL="OPTICAL-PHYSICAL-STATE-REPLAY-RESEARCH-001"
def audit(root=ROOT):
 reg=json.loads((root/"data/canonical-task-registry.json").read_text())
 ix=json.loads((root/"control/task-vector-index.json").read_text())
 rows={r["task_id"]:r for r in reg["tasks"]}
 if len(rows)!=len(reg["tasks"]):raise ValueError("duplicate canonical identity")
 matches=[x for x in ix["tasks"] if x["task_id"] in TASKS]
 if len(matches)!=4 or len({x["task_id"] for x in matches})!=4:raise ValueError("four unique index records required")
 im={x["task_id"]:x for x in matches}
 out=[]
 for id in TASKS:
  r=rows[id];s=json.loads((root/"data/canonical-task-records"/(id+".json")).read_text())
  v=json.loads((root/"control/task-vectors"/(id+".json")).read_text())
  if not validate_record(v) or v["task_id"]!=id or v["profile"]!="task.v1":raise ValueError("invalid source-state record: "+id)
  if len(v["metric_evidence"])!=14 or v["vector"]!=encode_task(v["source_state"]):raise ValueError("unsupported metric provenance: "+id)
  if not (r["cosv_task_vector"]==s["cosv_task_vector"]==v["vector"]==im[id]["vector"]):raise ValueError("vector mismatch: "+id)
  if not (r["source_state_vector_ref"]==s["source_state_vector_ref"]==im[id]["source_state_vector_ref"]=="control/task-vectors/"+id+".json"):raise ValueError("vector path mismatch: "+id)
  if (r["coordination_state"],r["checkout_state"])!=(s["coordination_state"],s["checkout_state"]):raise ValueError("owner-shard state conflict: "+id)
  if v["observed_registry_generation"]>=reg["generation"]:raise ValueError("source generation is not predecessor: "+id)
  state=v["source_state"]
  if state["lifecycle"]!=("CLAIMED_IMPLEMENTATION" if r["checkout_state"]=="CHECKED_OUT" else "UNCLAIMED"):raise ValueError("unsupported lifecycle: "+id)
  if state["unassigned_work"]!=(0 if r["checkout_state"]=="CHECKED_OUT" else 1):raise ValueError("unsupported unassigned work: "+id)
  blockers=len(s.get("remaining_predicates",[])) if id==TASKS[0] else len(s.get("blockers",[]))
  if state["blocker_count"]!=min(9,blockers) or v["exact_metrics"]["blocker_count_exact"]!=blockers:raise ValueError("blocker evidence mismatch: "+id)
  if state["thread_required"] is not (True if id==OPTICAL else None):raise ValueError("native thread provenance changed: "+id)
  if not (state["canonical_owner_installed"] and all(state[k] is False for k in ("evidence_complete","activated","propagated","archive_ready"))):raise ValueError("unproven terminal or authority claim: "+id)
  if v["authority_effect"]!="NONE" or not v["tracking_only"] or v["authentic_ai_session_disposition_observed"] or v["workercoordinator_claim_or_fence_inferred"]:raise ValueError("source state escalated runtime authority: "+id)
  if id==OPTICAL:
   if v["vector"]!="10111110114000" or s["cosv_source_proposal"]["vector"]!=v["vector"] or not s["cosv_tracking"]["tracking_authoritative"]:raise ValueError("native optical vector/provenance replaced")
  out.append((id,v["vector"]))
 comp=json.loads((root/"data/goal-task-component-profiles"/(TASKS[0]+".json")).read_text())
 if comp["cosv_task_vector"]!=rows[TASKS[0]]["cosv_task_vector"]:raise ValueError("component profile conflict")
 return out
if __name__=="__main__":
 for id,v in audit():print("COSV_TRACKING_PASS",id,v)
