#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
task_id="KV-CONNECTION-REVALIDATION-WORKER-001"
vector="50000000102000"
required=[
    "KV_CONNECTION_REVALIDATION_COSV_MIRROR_HANDOFF.md",
    f"control/task-vectors/{task_id}.json",
    "control/task-vector-index.json",
    "control/cosv-global-registry-coverage.json",
    "tests/test_kv_connection_revalidation_cosv.py",
]
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f"missing KV revalidation COSV artifact: {rel}")
state=json.loads((ROOT/f"control/task-vectors/{task_id}.json").read_text())
index=json.loads((ROOT/"control/task-vector-index.json").read_text())
coverage=json.loads((ROOT/"control/cosv-global-registry-coverage.json").read_text())
if state.get("vector") != vector: raise SystemExit("KV revalidation vector mismatch")
if state.get("authority_effect") != "NONE": raise SystemExit("KV revalidation authority promotion")
entries=[x for x in index.get("tasks",[]) if x.get("task_id")==task_id]
if len(entries)!=1 or entries[0].get("vector")!=vector: raise SystemExit("KV revalidation index parity failure")
if task_id in coverage.get("active_worker_task_ids_missing_canonical_cosv",[]): raise SystemExit("KV revalidation remains active-unvectorized")
indexed=[x for x in coverage.get("indexed_vectors",[]) if x.get("task_id")==task_id]
if indexed != [{"task_id":task_id,"vector":vector}]: raise SystemExit("KV revalidation coverage parity failure")
summary=coverage["worker_registry_summary"]
total=summary["unique_task_ids_global_plus_fragments"]
indexed_count=summary["canonically_indexed_task_ids"]
active_gap=summary["active_unvectorized_unique_task_ids"]
completed=summary["completed_only_historical_unvectorized_task_ids"]
superseded=summary["superseded_historical_unvectorized_task_ids"]
if total != indexed_count + active_gap + completed + superseded:
    raise SystemExit("KV revalidation denominator partition mismatch")
if active_gap != len(coverage.get("active_worker_task_ids_missing_canonical_cosv", [])):
    raise SystemExit("KV revalidation active-gap mismatch")
print("KV connection revalidation COSV checks: PASS")
