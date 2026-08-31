#!/usr/bin/env python3
"""Canonical sovereign SDK/StegCore first-round execution worker for SV-DN-1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping

TASK_ID = "SV-DN1-SDK-FIRST-ROUND-001"
WORKER_ID = "sv-dn1-sdk-first-round-worker"
PARENT_TASK_ID = "SV-DN1-INTR-RUNTIME-001"
PARENT_TRANSITION = "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE"

BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
DEMO_ROOT_ENV = "STEGVERSE_SV_DN1_SOURCE_ROOT"
RESIDENT_STATE_ENV = "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT"
INTR_STATE_ENV = "STEGVERSE_SV_DN1_INTR_STATE_ROOT"
SOURCE_PREP_STATE_ENV = "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT"

DEFAULT_BOUND = Path.home() / ".stegverse" / "state" / "sv-dn1-sdk-first-round"
DEFAULT_DEMO = Path.home() / ".stegverse" / "source" / "stegverse-demo-suite"
DEFAULT_RESIDENT = Path.home() / ".stegverse" / "state" / "sv-dn1-resident-observer"
DEFAULT_INTR = Path.home() / ".stegverse" / "state" / "sv-dn1-intr-runtime"
DEFAULT_SOURCE_PREP = Path.home() / ".stegverse" / "state" / "sv-dn1-production-source-prep"

COMPONENT_TO_RUNTIME_KEY = {
    "stegverse.sdk": "sdk",
    "stegverse.stegcore": "stegcore",
    "stegverse.core-lite": "core_lite",
    "stegverse.master-records": "master_records",
}

ANCHORS = {
    "sdk": {
        "stegverse/governance_ingress_runtime.py": "62c5ae4799ae018f6b100766215c3c68078c5b2e",
        "stegverse/sovereign_validation_runtime.py": "6bc0944633b6299c19f065f44dd5999434445dd7",
    },
    "stegcore": {
        "src/stegcore/transaction_lifecycle.py": "81935669846fedd2867272810b090226b05780ab",
    },
    "core_lite": {
        "core_lite/transaction_route.py": "734923a86bfcd4d41d07e0fb8797de50f0fb9408",
    },
    "master_records": {
        "services/manifest_receipt_custody.py": "26a4c1e082ee91128648b2b9bd13cc32ce915f82",
    },
}

DEMO_FILES = (
    "scripts/build_sv_dn1_sdk_ingress_manifest.py",
    "scripts/bind_sv_dn1_sdk_live_result.py",
    "scripts/sv_dn1_evaluator.py",
    "scripts/finalize_sv_dn1_first_round.py",
    "config/sv_dn1_runtime_source_manifest.json",
)

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AZURE_CLIENT_SECRET",
    "GOOGLE_APPLICATION_CREDENTIALS", "OAUTH_TOKEN",
)
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")


class UpstreamPending(RuntimeError):
    pass


class LocalArtifactPending(RuntimeError):
    pass


class SourceDrift(RuntimeError):
    pass


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_json(path: Path, *, pending: type[RuntimeError] = RuntimeError) -> dict[str, Any]:
    if not path.is_file():
        raise pending(f"required JSON object not present: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    spec.loader.exec_module(module)
    return module


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            node = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(node, dict):
                raise RuntimeError("sovereign node declaration must be object")
            if node.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if node.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if node.get("github_token_required") is not False:
                raise RuntimeError("sovereign node may not require GitHub token")
            return path, node
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("unexpected invocation schema")
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    timing = task.get("heartbeat_timing") or {}
    if not isinstance(timing.get("fencing_token"), int):
        raise RuntimeError("fresh fencing token is required")

    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("first-round worker may not write repositories")
    if authority.get("external_consequence_authority") is not False:
        raise RuntimeError("SV-DN-1 first round may not authorize external consequences")
    if authority.get("publication_authority") is not False:
        raise RuntimeError("first-round worker may not publish")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant first-round authority")

    contract = handoff.get("input_contract") or {}
    if contract.get("parent_task_id") != PARENT_TASK_ID:
        raise RuntimeError("parent task drift")
    if contract.get("parent_transition_id") != PARENT_TRANSITION:
        raise RuntimeError("parent transition drift")
    if contract.get("candidate_readiness") != "READY_FOR_SDK_0B":
        raise RuntimeError("candidate readiness contract drift")
    if contract.get("sdk_route_id") != "stegverse.route.canonical-governed.v1":
        raise RuntimeError("SDK route contract drift")
    if contract.get("sdk_result_schema") != "stegverse.sovereign-production-validation-result.v1":
        raise RuntimeError("SDK result schema contract drift")
    return dict(task)


def resolve_path(env_name: str, default: Path) -> Path:
    raw = str(os.getenv(env_name) or "").strip()
    return Path(raw).expanduser().resolve() if raw else default.expanduser().resolve()


def bound_root() -> Path:
    root = resolve_path(BOUND_STATE_ENV, DEFAULT_BOUND)
    root.mkdir(parents=True, exist_ok=True)
    return root


def demo_root() -> Path:
    root = resolve_path(DEMO_ROOT_ENV, DEFAULT_DEMO)
    if not root.is_dir() or not all((root / rel).is_file() for rel in DEMO_FILES):
        raise LocalArtifactPending(f"exact demo-suite source root unavailable: {root}")
    manifest = load_json(root / "config/sv_dn1_runtime_source_manifest.json", pending=LocalArtifactPending)
    if manifest.get("schema") != "stegverse.sv-dn1.runtime-source-manifest/v1":
        raise SourceDrift("wrong demo-suite runtime source manifest")
    return root


def resolve_canonical_roots() -> tuple[dict[str, Path], dict[str, str], dict[str, Any]]:
    prep_root = resolve_path(SOURCE_PREP_STATE_ENV, DEFAULT_SOURCE_PREP)
    prep = load_json(prep_root / "receipts/latest.json", pending=LocalArtifactPending)
    if prep.get("schema") != "stegverse.sv-dn1.production-source-prep-receipt/v2":
        raise LocalArtifactPending("production source preparation v2 receipt is required")
    if prep.get("state") != "COMPLETE" or prep.get("transition_id") != "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE":
        raise LocalArtifactPending("production source preparation has not completed")
    if prep.get("source_identity_scheme") != "sha256-content-manifest":
        raise SourceDrift("production source identity scheme drift")
    if prep.get("network_source_fetch_performed") is not False or prep.get("github_platform_required") is not False:
        raise SourceDrift("production source receipt retains external platform dependency")
    raw_roots = prep.get("source_roots")
    raw_ids = prep.get("source_identities")
    if not isinstance(raw_roots, dict) or not isinstance(raw_ids, dict):
        raise LocalArtifactPending("production source receipt lacks roots/identities")
    expected = set(COMPONENT_TO_RUNTIME_KEY)
    if set(raw_roots) != expected or set(raw_ids) != expected:
        raise SourceDrift("production source component set drift")
    roots: dict[str, Path] = {}
    identities: dict[str, str] = {}
    for component_id, runtime_key in COMPONENT_TO_RUNTIME_KEY.items():
        identity = str(raw_ids.get(component_id) or "")
        if not identity.startswith("sha256:") or len(identity) != 71:
            raise SourceDrift(f"invalid content-addressed source identity: {component_id}")
        root = Path(str(raw_roots[component_id])).expanduser().resolve()
        if not root.is_dir():
            raise LocalArtifactPending(f"materialized source root unavailable: {component_id}={root}")
        for rel, expected_sha1 in ANCHORS[runtime_key].items():
            path = root / rel
            if not path.is_file():
                raise LocalArtifactPending(f"migration source anchor missing: {path}")
            actual = git_blob_sha1(path.read_bytes())
            if actual != expected_sha1:
                raise SourceDrift(f"migration source anchor drift: {component_id}:{rel}")
        roots[runtime_key] = root
        identities[runtime_key] = identity
    return roots, identities, prep

def source_evidence(roots: Mapping[str, Path], identities: Mapping[str, str]) -> dict[str, Any]:
    return {
        key: {
            "root": str(root),
            "source_identity": identities[key],
            "source_identity_scheme": "sha256-content-manifest",
            "migration_anchors": {
                rel: {"git_blob_sha1": git_blob_sha1((root / rel).read_bytes()), "expected_git_blob_sha1": expected}
                for rel, expected in ANCHORS[key].items()
            },
        }
        for key, root in roots.items()
    }


def upstream_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    resident = resolve_path(RESIDENT_STATE_ENV, DEFAULT_RESIDENT)
    intr = resolve_path(INTR_STATE_ENV, DEFAULT_INTR)
    resident_receipt = load_json(resident / "receipts/latest.json", pending=UpstreamPending)
    capture = load_json(resident / "observed/source-capture.json", pending=UpstreamPending)
    exchange = load_json(resident / "observed/exchange.json", pending=UpstreamPending)
    intr_receipt = load_json(intr / "receipts/latest.json", pending=UpstreamPending)

    if resident_receipt.get("state") != "COMPLETE" or resident_receipt.get("transition_id") != "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE":
        raise UpstreamPending("resident observer has not completed authentic capture")
    if intr_receipt.get("state") != "COMPLETE" or intr_receipt.get("route_id") != "SV-DN-1-HF-PUBLIC":
        raise UpstreamPending("route-specific InTr receipt is not COMPLETE")
    if intr_receipt.get("exchange_id") != exchange.get("exchange_id"):
        raise RuntimeError("InTr/exchange identity mismatch")
    if intr_receipt.get("claims", {}).get("sdk_admitted") is not False:
        raise RuntimeError("pre-SDK InTr receipt already claims SDK admission")
    return resident_receipt, capture, exchange, intr_receipt


def child_env(roots: Mapping[str, Path]) -> dict[str, str]:
    return {
        "PATH": os.getenv("PATH", "/usr/bin:/bin"),
        "HOME": os.getenv("HOME", str(Path.home())),
        "LANG": os.getenv("LANG", "C.UTF-8"),
        "LC_ALL": os.getenv("LC_ALL", "C.UTF-8"),
        "PYTHONPATH": os.pathsep.join([
            str(roots["sdk"]),
            str(roots["stegcore"] / "src"),
            str(roots["core_lite"]),
            str(roots["master_records"]),
        ]),
    }


SDK_CHILD = r'''
import json
import sys
from pathlib import Path
from stegverse.governance_ingress_runtime import run_external_manifest
from stegverse.sovereign_validation_runtime import replay_sovereign, reconstruct_sovereign

manifest_path, db_path = sys.argv[1], sys.argv[2]
manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
result = run_external_manifest(
    manifest,
    custody_db=db_path,
    host_identity="sv-dn1-sdk-first-round-worker",
)
rid = result["manifest_receipt_id"]
replay = replay_sovereign(rid, custody_db=db_path)
reconstruction = reconstruct_sovereign(rid, custody_db=db_path)
print(json.dumps({
    "sdk_result": result,
    "replay": replay,
    "reconstruction": reconstruction,
}, sort_keys=True))
'''


def atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic_write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def execute(invocation: Mapping[str, Any], *, runner=subprocess.run) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign SV-DN-1 first round")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for SV-DN-1 first round: " + ",".join(sorted(present)))

    node_path, _ = find_node()
    task = validate_invocation(invocation)
    demo = demo_root()
    roots, source_identities, source_prep_receipt = resolve_canonical_roots()
    resident_receipt, capture, exchange, intr_receipt = upstream_evidence()
    bound = bound_root()

    builder = load_module(demo / "scripts/build_sv_dn1_sdk_ingress_manifest.py", "sv_dn1_sdk_first_round_builder")
    binder = load_module(demo / "scripts/bind_sv_dn1_sdk_live_result.py", "sv_dn1_sdk_first_round_binder")
    evaluator = load_module(demo / "scripts/sv_dn1_evaluator.py", "sv_dn1_sdk_first_round_evaluator")
    finalizer = load_module(demo / "scripts/finalize_sv_dn1_first_round.py", "sv_dn1_sdk_first_round_finalizer")

    context = invocation.get("context") or {}
    created_at = str(context.get("observed_at") or capture.get("observed_at") or "")
    if not created_at:
        raise RuntimeError("candidate created_at is unavailable")

    candidate = builder.build_ingress_candidate(
        resident_receipt, capture, exchange, created_at, intr_receipt
    )
    if candidate.get("execution_readiness") != "READY_FOR_SDK_0B":
        raise UpstreamPending("canonical demo-suite candidate is not READY_FOR_SDK_0B")

    candidate_dir = bound / "candidate"
    sdk_dir = bound / "sdk"
    round_dir = bound / "round"
    candidate_path = candidate_dir / "sdk-ingress-candidate.json"
    manifest_path = candidate_dir / "manifest.json"
    write_json(candidate_path, candidate)
    write_json(manifest_path, candidate["manifest"])

    db_path = sdk_dir / "master-records.db"
    sdk_dir.mkdir(parents=True, exist_ok=True)
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass

    run = runner(
        [sys.executable, "-c", SDK_CHILD, str(manifest_path), str(db_path)],
        cwd=roots["sdk"],
        env=child_env(roots),
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    if run.returncode != 0:
        raise RuntimeError("canonical SDK first-round execution failed: " + (run.stderr or run.stdout)[-4000:])
    try:
        child_result = json.loads(run.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("canonical SDK execution did not emit parseable result") from exc

    sdk_result = child_result.get("sdk_result")
    replay = child_result.get("replay")
    reconstruction = child_result.get("reconstruction")
    if not all(isinstance(x, dict) for x in (sdk_result, replay, reconstruction)):
        raise RuntimeError("canonical SDK execution result/replay/reconstruction missing")
    if sdk_result.get("schema") != "stegverse.sovereign-production-validation-result.v1":
        raise RuntimeError("wrong canonical SDK result schema")
    if sdk_result.get("external_side_effect") is not False:
        raise RuntimeError("SV-DN-1 canonical SDK run produced external side effect")
    if sdk_result.get("third_party_host_required") is not False:
        raise RuntimeError("SV-DN-1 canonical SDK run required third-party host")
    if sdk_result.get("master_records_custody_status") != "RECORDED":
        raise RuntimeError("Master Records did not record exact SDK run")

    admission = binder.bind(candidate, sdk_result)
    if admission.get("state") != "SDK_ADMITTED":
        raise RuntimeError("canonical SDK result did not bind to SDK_ADMITTED")

    result_receipt = evaluator.evaluate(exchange, admission)
    analysis, pipeline = finalizer.finalize(
        capture=capture,
        exchange=exchange,
        intr=intr_receipt,
        candidate=candidate,
        sdk_result=sdk_result,
        admission=admission,
        result_receipt=result_receipt,
        reconstruction=reconstruction,
        replay=replay,
        lane_findings=None,
    )

    write_json(sdk_dir / "sdk-result.json", sdk_result)
    write_json(sdk_dir / "sdk-admission.json", admission)
    write_json(sdk_dir / "replay.json", replay)
    write_json(sdk_dir / "reconstruction.json", reconstruction)
    write_json(round_dir / "result-receipt.json", result_receipt)
    write_json(round_dir / "first-round-analysis.json", analysis)
    write_json(round_dir / "production-pipeline-observation.json", pipeline)
    atomic_write(round_dir / "report.md", finalizer.REPORT.render(exchange, result_receipt, pipeline))
    atomic_write(round_dir / "index.html", finalizer.DASH.render(exchange, result_receipt, 12, pipeline))

    receipt = {
        "schema": "stegverse.sv-dn1.sdk-first-round-worker-receipt/v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "state": "COMPLETE",
        "transition_id": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
        "claim_id": task.get("claim_id"),
        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
        "node_declaration_ref": str(node_path),
        "exchange_id": exchange["exchange_id"],
        "intr_receipt_hash": intr_receipt["receipt_hash"],
        "sdk_request_id": sdk_result["request_id"],
        "manifest_receipt_id": sdk_result["manifest_receipt_id"],
        "sdk_result_binding_hash": sdk_result["result_binding_hash"],
        "sdk_admission": "SDK_ADMITTED",
        "governance_state": sdk_result["governance_state"],
        "master_records_custody_status": sdk_result["master_records_custody_status"],
        "replay_consequence_reexecuted": replay.get("consequence_reexecuted"),
        "reconstruction_consequence_reexecuted": reconstruction.get("consequence_reexecuted"),
        "reconstruction_original_record_mutated": reconstruction.get("original_record_mutated"),
        "first_round_analysis": analysis["state"],
        "publication_state": pipeline["publication_state"],
        "external_summary": analysis["external_evaluation"]["summary"],
        "external_failures": analysis["external_evaluation"]["failures"],
        "external_unknowns": analysis["external_evaluation"]["unknowns"],
        "dashboard_generated": True,
        "dashboard_publicly_hosted": False,
        "source_evidence": source_evidence(roots, source_identities),
        "source_identities": source_identities,
        "source_prep_receipt_schema": source_prep_receipt.get("schema"),
        "github_platform_required": False,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "certification_claimed": False,
        "production_perfection_claimed": False,
        "authority_effect": "NONE",
    }
    write_json(bound / "receipts/latest.json", receipt)
    return receipt


def completed_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_PUBLIC_AUTHENTIC_DASHBOARD_PUBLISHED",
        "checkpoint_ref": "receipts/latest.json",
        "evidence_refs": [
            "candidate/sdk-ingress-candidate.json",
            "sdk/sdk-result.json",
            "sdk/sdk-admission.json",
            "sdk/replay.json",
            "sdk/reconstruction.json",
            "round/result-receipt.json",
            "round/first-round-analysis.json",
            "round/production-pipeline-observation.json",
            "round/report.md",
            "round/index.html",
            "receipts/latest.json",
        ],
        "manifest_receipt_id": receipt.get("manifest_receipt_id"),
        "governance_state": receipt.get("governance_state"),
        "publication_state": receipt.get("publication_state"),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def wait_response(exc: Exception, transition: str, dependency: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "dependency_class": dependency,
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Allow the existing canonical machine-owned predecessor/local artifact lane to satisfy the exact missing predicate; do not substitute fixture or hosted execution.",
            "machine_observable_release_condition": "authentic InTr evidence and exact local canonical production anchors are present",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "human_action_required": False,
        },
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "SV_DN1_SDK_FIRST_ROUND_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "dependency_class": "CANONICAL_PRODUCTION_RUNTIME",
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Repair the exact canonical SDK/StegCore/Master Records predicate and retry this same fenced production task without widening authority.",
            "machine_observable_release_condition": "SDK result binding, custody, replay/reconstruction and first-round finalization all validate",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "human_action_required": False,
        },
    }


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be JSON object")
        receipt = execute(invocation)
        print(json.dumps(completed_response(receipt), sort_keys=True))
        return 0
    except UpstreamPending as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_INTR_RUNTIME_PENDING", "UPSTREAM_EVIDENCE"), sort_keys=True))
        return 0
    except LocalArtifactPending as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_CANONICAL_LOCAL_ARTIFACTS_PENDING", "LOCAL_CANONICAL_ARTIFACTS"), sort_keys=True))
        return 0
    except SourceDrift as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_CANONICAL_SOURCE_DRIFT", "SOURCE_IDENTITY"), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
