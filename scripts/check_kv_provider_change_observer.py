#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=[
  "KV_PROVIDER_CHANGE_OBSERVER_MIRROR_HANDOFF.md",
  "handoffs/KV-PROVIDER-CHANGE-OBSERVER-001.json",
  "control/worker-registry.d/kv-provider-change-observer-001.json",
  "control/process-worker-adapters.d/kv-provider-change-observer-001.json",
  "workers/kv_provider_change_observer_worker.py",
  "tests/test_kv_provider_change_observer_worker.py",
  "schemas/kv-provider-monitor-targets.v1.schema.json",
  "cost-basis/worker-runtime/kv-provider-change-observer.json"
]
for rel in required:
  if not (ROOT/rel).is_file(): raise SystemExit(f"missing KV provider change observer artifact: {rel}")
for rel in [x for x in required if x.endswith(".json")]:
  json.loads((ROOT/rel).read_text(encoding="utf-8"))
worker=(ROOT/"workers/kv_provider_change_observer_worker.py").read_text(encoding="utf-8")
for marker in ["HOSTED_SURFACE_REJECTED","FORBIDDEN_CREDENTIAL_ENV","TARGET_HTTPS_REQUIRED","SOURCE_REDIRECT_PROHIBITED","provider_operation_authorized"]:
  if marker not in worker: raise SystemExit(f"missing observer invariant: {marker}")
for forbidden in ["Authorization: Bearer","Cookie:","COINBASE_API_SECRET =","access_token ="]:
  if forbidden in worker: raise SystemExit(f"credential-bearing observer source prohibited: {forbidden}")
print("KV provider change observer static checks: PASS")
