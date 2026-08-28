#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=[
 "KV_CONNECTION_HEALTH_RECONCILER_MIRROR_HANDOFF.md",
 "handoffs/KV-CONNECTION-HEALTH-RECONCILER-001.json",
 "control/worker-registry.d/kv-connection-health-reconciler-001.json",
 "control/process-worker-adapters.d/kv-connection-health-reconciler-001.json",
 "cost-basis/worker-runtime/kv-connection-health-reconciler.json",
 "control/admissible-existence-retrospective-conformance.d/kv-connection-health-reconciler-001.json",
 "workers/kv_connection_health_reconciler_worker.py",
 "tests/test_kv_connection_health_reconciler_worker.py"
]
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f"missing KV connection health reconciler artifact: {rel}")
for rel in [x for x in required if x.endswith(".json")]:
    json.loads((ROOT/rel).read_text(encoding="utf-8"))
worker=(ROOT/"workers/kv_connection_health_reconciler_worker.py").read_text(encoding="utf-8")
for marker in ["HOSTED_SURFACE_REJECTED","FORBIDDEN_CREDENTIAL_ENV","RECONCILER_MAY_NOT_RESTORE_VERIFIED","provider_network_access_performed","connection_verified"]:
    if marker not in worker: raise SystemExit(f"missing reconciler invariant: {marker}")
for forbidden in ["urllib.request","requests.get(","Authorization: Bearer","COINBASE_API_SECRET ="]:
    if forbidden in worker: raise SystemExit(f"provider network/credential source prohibited: {forbidden}")
print("KV connection health reconciler static checks: PASS")
