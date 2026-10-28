#!/usr/bin/env python3
"""Submit the unchanged StegBrowser one-shot invocation through shared Universal InTr.

This composes existing StegOS Universal InTr builders, the existing
StegBrowser profile ingress admission that the shared /intr/materialization
listener routes to (workers/stegbrowser_intr_materialization_ingress.py admit),
and the existing StegBrowser manifest-bound runner. The StegBrowser route on the
shared router is decided by the SDK route installer
(stegverse.universal_intr_route_installer.evaluate_installation, SDK main
c138cad4 or later), read-only: this path never rewrites the router in place,
and the standalone Labs installer it used to run is retired. The exact node trigger is
admitted in-process and persisted write-once into the durable queue: no
listener, socket, timeout or receiver liveness is a predicate of the transition
(DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION). The submission projects
INGRESS_ADMITTED only and never claims downstream execution. It creates no
additional listener implementation, runtime, scheduler, WorkerCoordinator,
transport, endpoint, credential path, or authority surface.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
GOAL_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
PARENT_TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
REQUEST_REL = Path("control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json")
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
BINDING_DIR_REL = Path("intr-payloads/stegbrowser-manifest-invocation")
OUTBOX_DIR_REL = Path("intr-outbox/stegbrowser-manifest-invocation")
DESTINATION_SUBSYSTEM = "StegBrowser:ManifestInvocation"
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#1952"
EDGE_CONSUMER_ID = "stegbrowser"
ROUTER_REL = Path("workers/universal_intr_profiled_ingress.py")
SDK_MODULE = "stegverse.universal_intr_route_installer"
SDK_MIN_COMMIT = "StegVerse-org/StegVerse-SDK@c138cad4"
ROUTE_OWNING_GOAL = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"
RETRY_ENTRYPOINT = "scripts/run_stegbrowser_universal_intr_materialization.py::submit_once"
# The standard six-field refusal names (org-kernel/kernel.py SIX_FIELDS; ORRD L61).
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


class StegBrowserAdmissionRefused(RuntimeError):
    """A non-ALLOW of this path. It carries the six fields and commits nothing."""

    def __init__(self, disposition: Mapping[str, Any]):
        missing = [field for field in SIX_FIELDS if not disposition.get(field)]
        if missing:
            raise ValueError("refusal_missing_six_fields:" + ",".join(missing))
        self.disposition = dict(disposition)
        super().__init__(f"{self.disposition['failure_code']}:{self.disposition.get('detail', '')}")


def refusal(failure_code: str, failed_predicate: str, repair: str, detail: str, *,
            owning_existing_goal: str = GOAL_ID, retry_entrypoint: str = RETRY_ENTRYPOINT,
            disposition: str = "FAIL_CLOSED", **extra: Any) -> StegBrowserAdmissionRefused:
    return StegBrowserAdmissionRefused({
        "schema": "stegverse.stegbrowser-universal-intr-submission/v1",
        "disposition": disposition, "failure_code": failure_code, "failed_predicate": failed_predicate,
        "detail": detail, "required_evidence_or_repair": repair, "retry_entrypoint": retry_entrypoint,
        "owning_existing_goal": owning_existing_goal,
        "next_attempt": {"entrypoint": retry_entrypoint, "resubmit": "THE_SAME_INVOCATION_AFTER_THE_REPAIR",
                         "awaits_an_external_machine": False},
        "receiver_liveness_predicate": False, "authority_effect": "NONE_REFUSAL_ONLY", **extra})


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + sha256_hex(raw)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object_required:{path}")
    return value


def write_once(path: Path, value: Mapping[str, Any]) -> Path:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"write_once_collision:{path}")
        return path
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    if path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"write_readback_mismatch:{path}")
    return path


def validate_unchanged_request(value: Mapping[str, Any]) -> None:
    expected = {
        "requested_goal_task_id": GOAL_ID,
        "requested_test_scope": "A0_A4_SINGLE_INVOCATION",
        "requested_invocation_count": 1,
        "invocation_request_nonce": NONCE,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise RuntimeError(f"unchanged_one_shot_request_{key}_mismatch")


def load_sdk_route_installation() -> Any:
    """The SDK route installer's evaluator, imported the way Labs reads the SDK.

    Same import form as resident-runtime/organization_manifest_ingress.py
    (``from stegverse.<module> import ...``): no new dependency, no vendored copy.
    """
    try:
        from stegverse.universal_intr_route_installer import evaluate_installation
    except ImportError as exc:
        raise refusal(
            "SDK_ROUTE_INSTALLER_NOT_IMPORTABLE", "THE_SDK_ROUTE_INSTALLER_DECIDES_THE_STEGBROWSER_ROUTE",
            f"install the StegVerse SDK at {SDK_MIN_COMMIT} or later (it provides {SDK_MODULE}); "
            "this path never falls back to rewriting the router in place",
            f"{SDK_MODULE} is not importable: {exc}", owning_existing_goal=ROUTE_OWNING_GOAL) from None
    return evaluate_installation


def stegbrowser_route_declaration() -> dict[str, Any]:
    """The StegBrowser route exactly as the SDK publishes it; never inferred or substituted."""
    try:
        from stegverse.route_resolution import PUBLISHED_ROUTES, STEGBROWSER_ROUTE_ID, _ROUTE_FIELDS
    except ImportError as exc:
        raise refusal(
            "SDK_ROUTE_INSTALLER_NOT_IMPORTABLE", "THE_SDK_ROUTE_INSTALLER_DECIDES_THE_STEGBROWSER_ROUTE",
            f"install the StegVerse SDK at {SDK_MIN_COMMIT} or later",
            f"stegverse.route_resolution is not importable: {exc}", owning_existing_goal=ROUTE_OWNING_GOAL) from None
    return {field: PUBLISHED_ROUTES[STEGBROWSER_ROUTE_ID][field] for field in _ROUTE_FIELDS}


def evaluate_route(*, source_root: Path, hb_epoch: Any, evaluate: Any = None, route: Any = None) -> dict[str, Any]:
    """The SDK installer's read-only decision on the StegBrowser route; a non-ALLOW is raised with its six fields.

    It replaces running the retired standalone Labs StegBrowser route installer,
    which rewrote the shared router in place. The router is read, never written.
    """
    evaluate = evaluate or load_sdk_route_installation()
    router_path = source_root / ROUTER_REL
    try:
        router_source = router_path.read_bytes()
    except OSError as exc:
        raise refusal(
            "SHARED_ROUTER_NOT_READABLE", "THE_EXISTING_SHARED_UNIVERSAL_INTR_ROUTER_IS_READABLE",
            f"restore {ROUTER_REL} in the source root; no second listener is created",
            str(exc), owning_existing_goal=ROUTE_OWNING_GOAL) from None
    request = {
        "schema": "stegverse.universal-intr-route-installation-request/v1",
        "consumer_id": EDGE_CONSUMER_ID,
        "route": route if route is not None else stegbrowser_route_declaration(),
        "hb_epoch": hb_epoch,
        "router": {"path": str(ROUTER_REL), "predecessor_sha256": "sha256:" + sha256_hex(router_source)},
    }
    result = evaluate(request, router_source)
    if not isinstance(result, dict):
        raise refusal("SDK_ROUTE_DECISION_UNREADABLE", "THE_SDK_ROUTE_INSTALLER_RETURNS_ONE_DISPOSITION",
                      f"use {SDK_MODULE}.evaluate_installation at {SDK_MIN_COMMIT} or later",
                      f"evaluate_installation returned {type(result).__name__}", owning_existing_goal=ROUTE_OWNING_GOAL)
    if result.get("disposition") != "ALLOW":
        if all(result.get(field) for field in SIX_FIELDS):
            raise StegBrowserAdmissionRefused(result)
        raise refusal("SDK_ROUTE_DECISION_WITHOUT_SIX_FIELDS", "EVERY_NON_ALLOW_CARRIES_THE_SIX_FIELDS",
                      f"use {SDK_MODULE}.evaluate_installation at {SDK_MIN_COMMIT} or later",
                      f"non-ALLOW {result.get('disposition')!r} without the six fields", owning_existing_goal=ROUTE_OWNING_GOAL)
    transition = result.get("transition") or {}
    return {"disposition": "ALLOW", "route": transition.get("route"),
            "transition_sha256": result.get("transition_sha256"),
            "router_predecessor_sha256": request["router"]["predecessor_sha256"],
            "router_noop": bool((transition.get("evidence") or {}).get("noop")),
            "router_written": False, "hb_epoch": hb_epoch}


def load_profile_admission() -> Any:
    """The existing StegBrowser profile admit, which persists the node trigger write-once."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    path = ROOT / "workers/stegbrowser_intr_materialization_ingress.py"
    spec = importlib.util.spec_from_file_location("stegbrowser_intr_materialization_ingress", path)
    if spec is None or spec.loader is None:
        raise refusal("STEGBROWSER_PROFILE_ADMISSION_NOT_LOADABLE", "THE_EXISTING_STEGBROWSER_PROFILE_ADMIT_LOADS",
                      "restore workers/stegbrowser_intr_materialization_ingress.py", "import spec missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.admit


def admit_trigger(trigger: Mapping[str, Any], *, runtime_root: Path, admit: Any) -> dict[str, Any]:
    """Admit the exact node trigger write-once in-process; a refusal is typed and commits nothing."""
    raw = canonical_bytes(trigger)
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "STEGOS_NODE_OUTBOX",
        "X-StegVerse-Payload-SHA256": sha256_hex(raw),
    }
    try:
        receipt = admit(runtime_root=runtime_root.resolve(), body=raw, headers=headers)
    except ValueError as exc:
        raise refusal("STEGBROWSER_INTR_ADMISSION_REFUSED", "THE_EXACT_NODE_TRIGGER_IS_ADMISSIBLE",
                      "rebuild the node trigger from the unchanged one-shot request and resubmit it exactly",
                      "stegbrowser_intr_admission_refused:" + str(exc), disposition="DENY") from exc
    return receipt


def build_binding(*, source_root: Path, runtime_root: Path, stegos_root: Path, node_receipt_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    stegos = stegos_root.resolve()
    one_shot = load(source / REQUEST_REL)
    validate_unchanged_request(one_shot)
    manifest_path = source / MANIFEST_REL
    manifest_raw = manifest_path.read_bytes()
    manifest = load(manifest_path)
    if manifest.get("task_id") != PARENT_TASK_ID or str(manifest.get("cosv_task_vector")) != COSV:
        raise RuntimeError("manifest_task_cosv_mismatch")
    if not node_receipt_path.is_file():
        raise RuntimeError("node_genesis_receipt_missing")
    sys.path.insert(0, str(stegos))
    from stegos.network_manifold import validate_node_genesis_receipt
    from stegos.universal_intr_transport import build_transport_intent, sha256_uri as stegos_sha256_uri
    from stegos.universal_intr_materialization import build_materialization_request

    node = load(node_receipt_path)
    validate_node_genesis_receipt(node)
    node_id = str(node.get("node_id") or "")
    interlock_id = str(node.get("interlock_id") or "")
    registration_receipt_sha256 = str(node.get("receipt_sha256") or "")
    if not node_id or not interlock_id or not registration_receipt_sha256:
        raise RuntimeError("node_binding_incomplete")

    binding = {
        "schema": "stegverse.stegbrowser-universal-intr-invocation-binding/v1",
        "state": "BOUND_FOR_UNIVERSAL_INTR_MATERIALIZATION",
        "goal_task_id": GOAL_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "manifest_ref": str(manifest_path),
        "manifest_sha256": sha256_hex(manifest_raw),
        "node_genesis_receipt_ref": str(node_receipt_path.resolve()),
        "node_id": node_id,
        "interlock_id": interlock_id,
        "registration_receipt_sha256": registration_receipt_sha256,
        "stegos_source_root": str(stegos),
        "request_mutated": False,
        "resident_request_sweep_required": False,
        "control_plane_source_package_required": False,
        "credential_authority": "TV/TVC",
        "github_runtime_authority": "NONE",
        "authority_effect": "NONE_BINDING_ONLY",
    }
    binding_hash = sha256_hex(canonical_bytes(binding))
    binding_path = runtime / BINDING_DIR_REL / f"{binding_hash}.json"
    write_once(binding_path, binding)
    payload_hash = stegos_sha256_uri(binding)
    intent = build_transport_intent(
        operation_id=f"STEGBROWSER:{GOAL_ID}:{NONCE}",
        payload_hash=payload_hash,
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="StegBrowser:ManifestRequest",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem=DESTINATION_SUBSYSTEM,
    )
    request = build_materialization_request(intent, payload_ref=str(binding_path), downstream_owner_ref=DOWNSTREAM_OWNER)
    entry_body = {
        "schema": "stegos.node_intr_outbox_entry.v1",
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "response_sha256": binding_hash,
        "provenance_sha256": sha256_uri({"manifest_sha256": binding["manifest_sha256"], "nonce": NONCE}),
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
        "materialization_request": request,
        "network_delivery_observed": False,
        "runtime_materialization_observed": False,
        "receiver_receipt_observed": False,
        "tvc_receipt_observed": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
    }
    entry = {**entry_body, "outbox_entry_hash": sha256_uri(entry_body)}
    trigger_body = {
        "schema": "stegos.node_intr_materialization_trigger.v1",
        "transport_origin": "STEGOS_NODE_OUTBOX",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    trigger = {**trigger_body, "trigger_sha256": sha256_uri(trigger_body)}
    write_once(runtime / OUTBOX_DIR_REL / f"{request['materialization_id']}.json", trigger)
    return binding, request, trigger


def submit_once(*, source_root: Path, runtime_root: Path, stegos_root: Path, node_receipt_path: Path,
                hb_epoch: Any = None, admit: Any = None, evaluate: Any = None) -> dict[str, Any]:
    # The route is decided by the SDK installer first; a refusal builds and persists nothing.
    route = evaluate_route(source_root=source_root, hb_epoch=hb_epoch, evaluate=evaluate)
    try:
        _binding, request, trigger = build_binding(source_root=source_root, runtime_root=runtime_root, stegos_root=stegos_root, node_receipt_path=node_receipt_path)
    except StegBrowserAdmissionRefused:
        raise
    except (RuntimeError, OSError, ValueError) as exc:
        raise refusal("STEGBROWSER_INVOCATION_BINDING_NOT_BUILT", "THE_UNCHANGED_ONE_SHOT_INVOCATION_BINDS_TO_A_VALID_NODE",
                      "supply the unchanged one-shot request, its transport manifest and a valid node genesis receipt",
                      f"{type(exc).__name__}: {exc}") from None
    receipt = admit_trigger(trigger, runtime_root=runtime_root, admit=admit or load_profile_admission())
    if not isinstance(receipt, dict) or receipt.get("schema") != "stegverse.stegbrowser-intr-materialization-ingress/v1" or receipt.get("state") != "INGRESS_ADMITTED":
        raise refusal("STEGBROWSER_INTR_INGRESS_NOT_ADMITTED", "THE_PROFILE_ADMIT_RETURNS_INGRESS_ADMITTED",
                      "resubmit the exact trigger; the write-once queue returns the existing receipt",
                      "stegbrowser_intr_ingress_not_admitted")
    if receipt.get("materialization_id") != request.get("materialization_id") or receipt.get("request_hash") != request.get("request_hash"):
        raise refusal("STEGBROWSER_INTR_INGRESS_REQUEST_BINDING_MISMATCH", "THE_INGRESS_RECEIPT_BINDS_THE_SUBMITTED_REQUEST",
                      "resubmit the exact trigger", "stegbrowser_intr_ingress_request_binding_mismatch")
    if receipt.get("write_once_persisted") is not True or not receipt.get("queue_ref"):
        raise refusal("STEGBROWSER_INTR_INGRESS_WRITE_ONCE_RECEIPT_MISSING", "THE_INGRESS_PERSISTS_THE_TRIGGER_WRITE_ONCE",
                      "resubmit the exact trigger to the write-once queue", "stegbrowser_intr_ingress_write_once_receipt_missing")
    return {
        "schema": "stegverse.stegbrowser-universal-intr-submission/v1",
        "state": "INGRESS_ADMITTED",
        "goal_task_id": GOAL_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "ingress_receipt": receipt,
        "sdk_route_decision": route,
        "ingress_queue_ref": receipt["queue_ref"],
        "ingress_write_once_persisted": True,
        "in_process_write_once_admission": True,
        "receiver_liveness_predicate": False,
        "downstream_execution_observed": False,
        "consumer_dispatch_attempted": bool((receipt.get("dispatch") or {}).get("consumer_dispatch_attempted") is True),
        "runtime_predicates_promoted": False,
        "round_trip_1_started": False,
        "authority_effect": "NONE_SUBMISSION_AND_ADMISSION_EVIDENCE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--stegos-root", type=Path)
    parser.add_argument("--node-genesis-receipt", type=Path)
    parser.add_argument("--hb-epoch", help="the supplied heartbeat epoch (ASCII digits >= 32); no clock is read")
    args = parser.parse_args()
    stegos_root = (args.stegos_root or Path(os.environ.get("STEGVERSE_STEGOS_SOURCE_ROOT") or args.source_root.parent / "StegOS")).expanduser().resolve()
    node_receipt = (args.node_genesis_receipt or Path(os.environ.get("STEGVERSE_NODE_GENESIS_RECEIPT") or "")).expanduser().resolve()
    hb_epoch = args.hb_epoch if args.hb_epoch is not None else os.environ.get("STEGVERSE_HB_EPOCH")
    try:
        result = submit_once(source_root=args.source_root.expanduser().resolve(), runtime_root=args.runtime_root.expanduser().resolve(), stegos_root=stegos_root, node_receipt_path=node_receipt, hb_epoch=hb_epoch)
    except StegBrowserAdmissionRefused as refused:
        print(json.dumps(refused.disposition, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
