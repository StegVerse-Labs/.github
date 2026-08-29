#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
required=[
 "KV_REVALIDATION_PROOF_INTAKE_MIRROR_HANDOFF.md",
 "schemas/kv-revalidation-proof-intake.schema.json",
 "handoffs/KV-REVALIDATION-PROOF-INTAKE-001.json",
 "control/worker-registry.d/kv-revalidation-proof-intake-001.json",
 "control/process-worker-adapters.d/kv-revalidation-proof-intake-001.json",
 "cost-basis/worker-runtime/kv-revalidation-proof-intake.json",
 "control/task-vectors/KV-REVALIDATION-PROOF-INTAKE-001.json",
 "control/admissible-existence-retrospective-conformance.d/kv-revalidation-proof-intake-001.json",
 "workers/kv_revalidation_proof_intake_worker.py",
 "tests/test_kv_revalidation_proof_intake_worker.py",
 "tests/test_kv_revalidation_proof_intake_cosv.py",
 "control/task-vector-index.json",
 "control/cosv-global-registry-coverage.json"
]
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f"missing KV proof intake artifact: {rel}")
for rel in [x for x in required if x.endswith('.json')]:
    json.loads((ROOT/rel).read_text(encoding='utf-8'))
worker=(ROOT/'workers/kv_revalidation_proof_intake_worker.py').read_text(encoding='utf-8')
for marker in ['HOSTED_SURFACE_REJECTED','FORBIDDEN_CREDENTIAL_ENV','INTAKE_MANIFEST_NETWORK_LOCATION_REJECTED','TARGET_REVALIDATION_WORKER_IDENTITY_MISMATCH','connection_verified_by_intake','proof_manufactured']:
    if marker not in worker: raise SystemExit(f"missing proof intake invariant: {marker}")
for forbidden in ['urllib.request','requests.get(','Authorization: Bearer','COINBASE_API_SECRET =']:
    if forbidden in worker: raise SystemExit(f"provider network/credential source prohibited: {forbidden}")

task_id='KV-REVALIDATION-PROOF-INTAKE-001'
vector='50000000102000'
index=json.loads((ROOT/'control/task-vector-index.json').read_text(encoding='utf-8'))
coverage=json.loads((ROOT/'control/cosv-global-registry-coverage.json').read_text(encoding='utf-8'))
rows=[x for x in index.get('tasks',[]) if x.get('task_id')==task_id]
if len(rows)!=1 or rows[0].get('vector')!=vector:
    raise SystemExit('KV proof intake index parity failure')
if task_id in coverage.get('active_worker_task_ids_missing_canonical_cosv',[]):
    raise SystemExit('KV proof intake remains active-unvectorized')
indexed=[x for x in coverage.get('indexed_vectors',[]) if x.get('task_id')==task_id]
if indexed != [{'task_id':task_id,'vector':vector}]:
    raise SystemExit('KV proof intake coverage parity failure')
summary=coverage['worker_registry_summary']
total=summary['unique_task_ids_global_plus_fragments']
indexed_count=summary['canonically_indexed_task_ids']
active_gap=summary['active_unvectorized_unique_task_ids']
completed=summary['completed_only_historical_unvectorized_task_ids']
superseded=summary['superseded_historical_unvectorized_task_ids']
if total < 58 or indexed_count < 36:
    raise SystemExit('KV proof intake denominator regressed')
if total != indexed_count + active_gap + completed + superseded:
    raise SystemExit('KV proof intake denominator partition mismatch')
if active_gap != len(coverage.get('active_worker_task_ids_missing_canonical_cosv',[])):
    raise SystemExit('KV proof intake active-gap mismatch')
print('KV revalidation proof intake static checks: PASS')
