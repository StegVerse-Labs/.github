#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
GOAL_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
COSV = "40000100100000"
ORG_TASK = "ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001"
ORG_VECTOR = "50000000101000"
PACKET_ID = "stegbrowser-manifest-intr-ingress"
PACKET_REL = Path("spool/organization-local-boundary/ingress") / f"{PACKET_ID}.json"
ORG_RECEIPT_REL = Path("receipts/organization-local-boundary") / f"{PACKET_ID}.json"
OUTPUT_REL = Path("receipts/sovereign-host/stegbrowser-manifest-intr-ingress.latest.json")
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
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

def required_env(name: str) -> str:
    value = str(os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"required StegBrowser invocation binding missing:{name}")
    return value

def invocation_binding(source: Path) -> dict[str, str]:
    manifest_path = source / MANIFEST_REL
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    bound_manifest = required_env("STEGVERSE_STEGBROWSER_MANIFEST_SHA256")
    if bound_manifest != manifest_sha256:
        raise RuntimeError("StegBrowser manifest binding mismatch")
    receipt_sha256 = required_env("STEGVERSE_STEGBROWSER_REGISTRATION_RECEIPT_SHA256")
    if len(receipt_sha256) != 64:
        raise RuntimeError("StegBrowser registration receipt digest invalid")
    return {
        "goal_task_id": GOAL_ID,
        "node_id": required_env("STEGVERSE_STEGBROWSER_NODE_ID"),
        "interlock_id": required_env("STEGVERSE_STEGBROWSER_INTERLOCK_ID"),
        "registration_receipt_sha256": receipt_sha256,
        "lease_id": required_env("STEGVERSE_STEGBROWSER_LEASE_ID"),
        "runtime_id": required_env("STEGVERSE_STEGBROWSER_RUNTIME_ID"),
        "manifest_sha256": manifest_sha256,
    }

def packet(source: Path) -> dict[str, Any]:
    manifest_path = source / MANIFEST_REL
    manifest = load(manifest_path)
    binding = invocation_binding(source)
    payload = {
        "subject_task_id": SUBJECT_TASK,
        "goal_task_id": GOAL_ID,
        "cosv_task_vector": COSV,
        "purpose": "STEGBROWSER_MANIFEST_DEFINED_INTR_INGRESS",
        "manifest_ref": str(MANIFEST_REL),
        "manifest_sha256": binding["manifest_sha256"],
        "node_id": binding["node_id"],
        "interlock_id": binding["interlock_id"],
        "registration_receipt_sha256": binding["registration_receipt_sha256"],
        "lease_id": binding["lease_id"],
        "runtime_id": binding["runtime_id"],
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
        "transition_basis": {"subject_task_id": SUBJECT_TASK, "goal_task_id": GOAL_ID, "cosv_task_vector": COSV, "authority_effect": "NONE_EVIDENCE_ONLY"},
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
    expected = packet(source)
    binding = expected["payload"]
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
    result = {
        "schema":"stegverse.stegbrowser-manifest-intr-ingress/v1",
        "state":"AUTHENTIC_INTR_INGRESS_OBSERVED",
        "subject_task_id":SUBJECT_TASK,
        "goal_task_id":GOAL_ID,
        "cosv_task_vector":COSV,
        "executor_task_id":ORG_TASK,
        "manifest_sha256":binding["manifest_sha256"],
        "node_id":binding["node_id"],
        "interlock_id":binding["interlock_id"],
        "registration_receipt_sha256":binding["registration_receipt_sha256"],
        "lease_id":binding["lease_id"],
        "runtime_id":binding["runtime_id"],
        "organization_local_receipt_ref":str(ORG_RECEIPT_REL),
        "claim_id":receipt["claim_id"],
        "fencing_token":receipt["fencing_token"],
        "workercoordinator_claim_fence_observed":True,
        "organization_local_intr_ingress_receipt_verified":True,
        "manifest_defined_path":True,
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
