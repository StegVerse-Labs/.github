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
 "tests/test_kv_revalidation_proof_intake_worker.py"
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
print('KV revalidation proof intake static checks: PASS')
