#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md",
    "handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json",
    "control/worker-registry.d/kv-connection-revalidation-worker-001.json",
    "control/process-worker-adapters.d/kv-connection-revalidation-worker-001.json",
    "workers/kv_connection_revalidation_worker.py",
    "tests/test_kv_connection_revalidation_worker.py",
]
for rel in required:
    if not (ROOT / rel).is_file():
        raise SystemExit(f"missing KV connection revalidation worker artifact: {rel}")
for rel in [item for item in required if item.endswith(".json")]:
    json.loads((ROOT / rel).read_text(encoding="utf-8"))

worker = (ROOT / "workers/kv_connection_revalidation_worker.py").read_text(encoding="utf-8")
required_markers = [
    "HOSTED_SURFACE_REJECTED",
    "FORBIDDEN_CREDENTIAL_ENV",
    "EXACT_CONNECTION_ASSEMBLY_NOT_FOUND",
    "CONNECTION_REVALIDATION_REJECTED",
    "admit_revalidation",
    "persist_health_receipt",
    "provider_network_access_performed",
    "proof_manufactured",
    "connection_verified",
]
for marker in required_markers:
    if marker not in worker:
        raise SystemExit(f"missing revalidation worker invariant: {marker}")
for forbidden in [
    "urllib.request",
    "requests.get(",
    "requests.post(",
    "Authorization: Bearer",
    "COINBASE_API_SECRET =",
    "boto3.client(",
]:
    if forbidden in worker:
        raise SystemExit(f"provider network/credential source prohibited: {forbidden}")

handoff = json.loads((ROOT / "handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json").read_text(encoding="utf-8"))
if handoff["authority"]["credential_authority"] != "TV/TVC":
    raise SystemExit("credential authority must remain TV/TVC")
if handoff["authority"]["provider_operation_authority"] != "NONE":
    raise SystemExit("provider operation authority must remain NONE")

print("KV connection revalidation worker static checks: PASS")
