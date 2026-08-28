#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=[
 "KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md",
 "handoffs/KV-CONNECTION-REVALIDATION-001.json",
 "control/worker-registry.d/kv-connection-revalidation-001.json",
 "control/process-worker-adapters.d/kv-connection-revalidation-001.json",
 "cost-basis/worker-runtime/kv-connection-revalidation.json",
 "control/admissible-existence-retrospective-conformance.d/kv-connection-revalidation-001.json",
 "workers/kv_connection_revalidation_worker.py",
 "tests/test_kv_connection_revalidation_worker.py"
]
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f"missing KV connection revalidation worker artifact: {rel}")
for rel in [x for x in required if x.endswith(".json")]:
    json.loads((ROOT/rel).read_text(encoding="utf-8"))
worker=(ROOT/"workers/kv_connection_revalidation_worker.py").read_text(encoding="utf-8")
for marker in ["HOSTED_SURFACE_REJECTED","FORBIDDEN_CREDENTIAL_ENV","REVALIDATION_PROOF_ASSEMBLY_MISMATCH","REVALIDATION_TIME_FLOOR_REQUIRED","proof_generated_by_worker","provider_network_access_performed","admit_revalidation"]:
    if marker not in worker: raise SystemExit(f"missing revalidation worker invariant: {marker}")
for forbidden in ["urllib.request","requests.get(","Authorization: Bearer","COINBASE_API_SECRET ="]:
    if forbidden in worker: raise SystemExit(f"provider network/credential source prohibited: {forbidden}")
print("KV connection revalidation worker static checks: PASS")
