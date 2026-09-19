#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
ORG_TASK = "ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001"
ORG_VECTOR = "50000000101000"
PACKET_ID = "stegbrowser-manifest-intr-ingress"
PACKET_REL = Path("spool/organization-local-boundary/ingress") / f"{PACKET_ID}.json"
ORG_RECEIPT_REL = Path("receipts/organization-local-boundary") / f"{PACKET_ID}.json"
OUTPUT_REL = Path("receipts/sovereign-host/stegbrowser-manifest-intr-ingress.latest.json")
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
BINDING_REL = Path("receipts/sovereign-host/stegbrowser-node-interlock-runtime-binding.latest.json")
TARGETED = Path("scripts/refresh_and_execute_resident_task.py")

def canonical_json(v: Any) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def sha256_uri(v: Any) -> str:
    raw = v if isinstance(v, (bytes, bytearray)) else canonical_json(v)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value

def validated_binding(runtime: Path, manifest_sha256: str) -> dict[str, Any]:
    path = runtime / BINDING_REL
    if not path.is_file():
        raise RuntimeError("StegBrowser Node/Interlock/runtime binding receipt missing")
    binding = load(path)
    required = {
        "schema": "stegverse.stegbrowser-node-interlock-runtime-binding/v1",
        "state": "NODE_INTERLOCK_LEASE_RUNTIME_BOUND",
        "task_id": SUBJECT_TASK,
        "cosv_task_vector": COSV,
        "manifest_sha256": manifest_sha256,
        "runtime_class": "EVENT_EPHEMERAL",
        "rendezvous_requirement": "NOT_REQUIRED",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_IDENTITY_BINDING_ONLY",
    }
    for key, expected in required.items():
        if binding.get(key) != expected:
            raise RuntimeError(f"StegBrowser binding mismatch:{key}")
    for key in ("node_id", "interlock_id", "registration_receipt_sha256", "lease_id", "runtime_id", "state_root_binding", "binding_sha256"):
        if not isinstance(binding.get(key), str) or not binding[key]:
            raise RuntimeError(f"StegBrowser binding field missing:{key}")
    return binding

def packet(source: Path, runtime: Path) -> dict[str, Any]:
    if str(os.environ.get("STEGVERSE_STEGBROWSER_INVOCATION_NONCE") or "").strip() != NONCE:
        raise RuntimeError("StegBrowser immutable invocation nonce missing or mismatched")
    manifest_path = source / MANIFEST_REL
    manifest = load(manifest_path)
    raw = manifest_path.read_bytes()
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    binding = validated_binding(runtime, manifest_sha256)
    payload = {
        "subject_task_id": SUBJECT_TASK,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "purpose": "STEGBROWSER_MANIFEST_DEFINED_INTR_INGRESS",
        "manifest_ref": str(MANIFEST_REL),
        "manifest_sha256": manifest_sha256,
        "node_id": binding["node_id"],
        "interlock_id": binding["interlock_id"],
        "registration_receipt_sha256": binding["registration_receipt_sha256"],
        "lease_id": binding["lease_id"],
        "runtime_id": binding["runtime_id"],
        "state_root_binding": binding["state_root_binding"],
        "node_interlock_runtime_binding_sha256": binding["binding_sha256"],
        "route_owner": manifest.get("route_owner"),
        "outbound_interlock_intr_endpoint": (manifest.get("outbound") or {}).get("interlock_intr_endpoint"),
        "far_end_receiver": (manifest.get("outbound") or {}).get("receiver"),
        "round_trip_1_return_target": (manifest.get("round_trip_1") or {}).get("return_target"),
        "expected_runtime_predicate": "AUTHENTIC_INTR_INGRESS_OBSERVED",
    }
    return {
        "schema": "stegverse.organization-local-boundary.packet/v1",
        "profile_id": "stegverse.organization-local-intr/v1",
        "direction": "INGRESS",
        "packet_id": PACKET_ID,
        "payload": payload,
        "payload_hash": sha256_uri(payload),
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "carrier_grants_execution_authority": False,
        "canonical_state_change_authorized": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        "transition_basis": {"subject_task_id": SUBJECT_TASK, "cosv_task_vector": COSV, "invocation_request_nonce": NONCE, "authority_effect": "NONE_EVIDENCE_ONLY"},
    }

def verified(receipt: dict[str, Any], expected: dict[str, Any]) -> bool:
    claim, fence = receipt.get("claim_id"), receipt.get("fencing_token")
    return (
        receipt.get("schema") == "stegverse.organization-local-boundary.receipt/v1"
        and receipt.get("task_id") == ORG_TASK
        and receipt.get("packet_id") == PACKET_ID
        and receipt.get("payload_hash") == expected["payload_hash"]
        and receipt.get("ingress_packet_sha256") == sha256_uri(expected)
        and receipt.get("disposition") == "ACCEPTED_LOCAL_BOUNDARY"
        and receipt.get("credential_authority") == "TV/TVC"
        and receipt.get("github_token_runtime_authority") == "NONE"
        and receipt.get("canonical_state_changed") is False
        and receipt.get("external_side_effect_performed") is False
        and receipt.get("authority_effect") == "NONE"
        and isinstance(fence, int) and fence >= 1
        and isinstance(claim, str) and claim.endswith(f"-G{fence}")
    )

def execute(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source, runtime = source_root.resolve(), runtime_root.resolve()
    expected = packet(source, runtime)
    ingress, receipt_path = runtime / PACKET_REL, runtime / ORG_RECEIPT_REL
    ingress.parent.mkdir(parents=True, exist_ok=True)
    if ingress.is_file() and load(ingress) != expected:
        raise RuntimeError("StegBrowser organization-local ingress packet collision")
    if not receipt_path.is_file():
        ingress.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        runner = runtime / TARGETED
        if not runner.is_file():
            runner = source / TARGETED
        cmd = [sys.executable, str(runner), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", ORG_TASK, "--cosv-task-vector", ORG_VECTOR]
        completed = subprocess.run(cmd, cwd=runtime, capture_output=True, text=True, check=False, timeout=1200, env=os.environ.copy())
        if completed.returncode != 0 and not receipt_path.is_file():
            return {"state":"STEGBROWSER_ORG_INTR_INGRESS_EXECUTION_ATTEMPT_FAILED","returncode":completed.returncode,"stderr_tail":completed.stderr[-1200:]}
    if not receipt_path.is_file():
        return {"state":"STEGBROWSER_ORG_INTR_INGRESS_RECEIPT_PENDING"}
    receipt = load(receipt_path)
    if not verified(receipt, expected):
        raise RuntimeError("StegBrowser organization-local receipt failed exact verification")
    payload = expected["payload"]
    result = {
        "schema":"stegverse.stegbrowser-manifest-intr-ingress/v1",
        "state":"AUTHENTIC_INTR_INGRESS_OBSERVED",
        "subject_task_id":SUBJECT_TASK,
        "cosv_task_vector":COSV,
        "invocation_request_nonce":NONCE,
        "executor_task_id":ORG_TASK,
        "organization_local_receipt_ref":str(ORG_RECEIPT_REL),
        "claim_id":receipt["claim_id"],
        "fencing_token":receipt["fencing_token"],
        "manifest_sha256":payload["manifest_sha256"],
        "node_id":payload["node_id"],
        "interlock_id":payload["interlock_id"],
        "registration_receipt_sha256":payload["registration_receipt_sha256"],
        "lease_id":payload["lease_id"],
        "runtime_id":payload["runtime_id"],
        "state_root_binding":payload["state_root_binding"],
        "node_interlock_runtime_binding_sha256":payload["node_interlock_runtime_binding_sha256"],
        "workercoordinator_claim_fence_observed":True,
        "organization_local_intr_ingress_receipt_verified":True,
        "manifest_defined_path":True,
        "node_interlock_lease_runtime_correlation_verified":True,
        "external_runtime_required":False,
        "authority_effect":"NONE_EVIDENCE_ONLY",
    }
    out = runtime / OUTPUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,default=ROOT); p.add_argument("--runtime-root",type=Path,required=True); a=p.parse_args()
    result=execute(a.source_root,a.runtime_root); print(json.dumps(result,sort_keys=True)); return 0 if result.get("state")=="AUTHENTIC_INTR_INGRESS_OBSERVED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
