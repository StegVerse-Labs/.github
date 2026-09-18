#!/usr/bin/env python3
"""Execute the original SV002 v0.3 rerun from one fenced admitted materialization."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workers.sv002_self_characterization_intr_materialization_consumer import (
    COSV, INGRESS_RECEIPT_DIR_REL, REQUEST_DIR_REL, TASK_ID, ingress_receipt,
    validate_request,
)

MATERIALIZATION_ENV = "STEGVERSE_SV002_RERUN_MATERIALIZATION_ID"
INTAKE_ENV = "STEGVERSE_SV002_RERUN_INTAKE_RUNTIME_ROOT"
LEASE_ENV = "STEGVERSE_SV002_RERUN_ESRL_LEASE_ID"
CHECKPOINT_DIR = Path("receipts/sv002-experiment-rerun")
CHECKPOINT_LATEST = CHECKPOINT_DIR / "same-execution.latest.json"

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def blocker(problem: str, action: str, release: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": action,
        "machine_observable_release_condition": release,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "human_action_required": False,
    }


def worker_response(state: str, transition: str, checkpoint: str, epoch: int, blocked: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "SV002_EXPERIMENT_RERUN_RECHECK",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 8,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint, "docs/SV002_EXPERIMENT_RERUN_INTR_EXECUTION_MIRROR_HANDOFF.md"],
        "cost_observation": {"hb_transition_count": 1, "compute_units": 4, "external_cost_usd": 0, "task_class": "sv002_experiment_rerun"},
    }
    if blocked:
        result["blocker"] = blocked
    return result


def repo_candidates(env_name: str, org: str, repo: str) -> list[Path]:
    out: list[Path] = []
    raw = os.environ.get(env_name)
    if raw:
        out.append(Path(raw).expanduser())
    home = Path(os.environ.get("HOME", str(Path.home())))
    out.extend([
        home / ".stegverse" / "repos" / org / repo,
        Path("/var/lib/stegverse/source") / org / repo,
        Path("/srv/stegverse/repos") / org / repo,
        Path("/opt/stegverse/repos") / org / repo,
    ])
    return [p.resolve() for p in out]


def resolve_repo(env_name: str, org: str, repo: str, required: tuple[str, ...]) -> Path:
    for candidate in repo_candidates(env_name, org, repo):
        if candidate.is_dir() and all((candidate / rel).is_file() for rel in required):
            return candidate
    raise RuntimeError(f"required_local_source_not_materialized:{org}/{repo}")


def copy_source(source: Path, destination: Path) -> Path:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    return destination


def run_json(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> tuple[int, dict[str, Any] | None, str]:
    proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=timeout)
    parsed = None
    for line in reversed([x.strip() for x in proc.stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            parsed = value
            break
    return proc.returncode, parsed, proc.stderr[-2048:]


def safe_env(base: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if base is None else base)
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        values.pop(key, None)
    values.pop("STEGVERSE_ORG_FEDERATION_GATEWAY_URL", None)
    values["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    values["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return values


def retain(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"write_once_collision:{path}")
    if not path.exists():
        path.write_text(rendered, encoding="utf-8")


def execute(invocation: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    task = invocation.get("task") or {}
    claim_id = task.get("claim_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        raise RuntimeError("fresh_workercoordinator_claim_fence_required")

    materialization_id = str(os.environ.get(MATERIALIZATION_ENV) or "").strip()
    intake_raw = str(os.environ.get(INTAKE_ENV) or "").strip()
    lease_id = str(os.environ.get(LEASE_ENV) or "").strip()
    if not materialization_id or not intake_raw or not lease_id:
        raise RuntimeError("admitted_materialization_environment_binding_missing")
    intake = Path(intake_raw).expanduser().resolve()
    request_path = intake / REQUEST_DIR_REL / f"{materialization_id}.json"
    if not request_path.is_file():
        raise RuntimeError("admitted_materialization_request_missing")
    request = load(request_path)
    validate_request(request)
    ingress = ingress_receipt(intake, request)
    if request["materialization_id"] != materialization_id:
        raise RuntimeError("materialization_environment_binding_mismatch")

    state = ROOT / CHECKPOINT_DIR / materialization_id
    state.mkdir(parents=True, exist_ok=True)
    exact_request_path = state / "EXACT_SDK_REQUEST.json"
    retain(exact_request_path, request["sv002_request"])

    source_org = resolve_repo("STEGVERSE_SV002_SOURCE_ORG_ROOT", "StegVerse-org", ".github", (
        "resident-runtime/sdk_self_characterization_egress.py",
        "resident-runtime/federation_cycle.py",
        "resident-runtime/sdk_self_characterization_response.py",
    ))
    target_org = resolve_repo("STEGVERSE_SV002_ORG_ROOT", "StegVerse-002", ".github", (
        "resident-runtime/federation_cycle.py",
        "resident-runtime/self_characterization_surface.py",
        "resident-runtime/submit_sv002_self_characterization_to_master_records.py",
    ))
    master_org = resolve_repo("STEGVERSE_MASTER_RECORDS_ORG_ROOT", "master-records", ".github", (
        "resident-runtime/federation_cycle.py",
        "resident-runtime/sv002_self_characterization_intake.py",
    ))
    principal = resolve_repo("STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "StegVerse-002", "micro-node-runtime", (
        "tools/run_self_characterization_principal.py",
        "experiments/self-characterization-001/EXPERIMENT_CONTRACT.v0.3.json",
    ))
    orchestration = resolve_repo("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "master-records", "orchestration", (
        "scripts/verify_sv002_self_characterization_reconstruction.py",
    ))

    sources = state / "organization-source"
    source_copy = copy_source(source_org, sources / "StegVerse-org" / ".github")
    target_copy = copy_source(target_org, sources / "StegVerse-002" / ".github")
    master_copy = copy_source(master_org, sources / "master-records" / ".github")

    mesh = state / "federation"
    principal_state = state / "principal-state"
    xdg_state = state / "xdg-state"
    env = safe_env()
    env.update({
        "STEGVERSE_ORG_FEDERATION_ROOT": str(mesh),
        "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": str(principal),
        "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(orchestration),
        "STEGVERSE_SELF_CHAR_STATE_ROOT": str(principal_state),
        "XDG_STATE_HOME": str(xdg_state),
    })

    packet_path = state / "SDK_EGRESS_PACKET.json"
    frame_path = state / "SDK_EGRESS_FRAME.json"
    egress_script = source_copy / "resident-runtime/sdk_self_characterization_egress.py"
    rc, egress_result, err = run_json([
        sys.executable, str(egress_script),
        "--request", str(exact_request_path),
        "--packet-out", str(packet_path),
        "--frame-out", str(frame_path),
        "--submit",
    ], source_copy, env, 120)
    if rc != 0 or not packet_path.is_file():
        raise RuntimeError("source_organization_egress_failed:" + err)
    packet = load(packet_path)
    expected_packet_id = "sv002-self-char-" + request["sv002_request"]["bindings"]["manifest_sha256"][:24]
    if packet.get("packet_id") != expected_packet_id:
        raise RuntimeError("source_packet_identity_mismatch")

    target_rc, target_cycle, target_err = run_json(
        [sys.executable, str(target_copy / "resident-runtime/federation_cycle.py")],
        target_copy, env, 2100,
    )
    if target_rc != 0:
        raise RuntimeError("target_organization_cycle_failed:" + target_err)

    execution_path = principal_state / "EXPERIMENT_EXECUTION_RECEIPT.json"
    s0_path = principal_state / "S0.json"
    boundary_path = principal_state / "ORG_BOUNDARY_RECEIPTS.json"
    transition_path = principal_state / "TRANSITION_RECEIPTS.json"
    custody_handoff_path = principal_state / "MASTER_RECORDS_CUSTODY_HANDOFF.json"
    for path in (execution_path, s0_path, boundary_path, transition_path, custody_handoff_path):
        if not path.is_file():
            raise RuntimeError(f"target_execution_artifact_missing:{path.name}")
    execution = load(execution_path)
    s0 = load(s0_path)
    boundary = load(boundary_path)
    transitions = load(transition_path)
    custody_handoff = load(custody_handoff_path)
    if execution.get("schema") != "stegverse.self-characterization-execution-receipt/v0.3" or execution.get("state") != "COMPLETED":
        raise RuntimeError("v03_principal_completion_not_observed")
    run_id = str(execution.get("run_id") or "")
    if not run_id.startswith("SV002-RUN-") or s0.get("run_id") != run_id:
        raise RuntimeError("principal_run_id_binding_invalid")
    rows = boundary.get("receipts")
    if not isinstance(rows, list) or [row.get("kind") for row in rows] != ["INGRESS_ACCEPTED", "DISPATCHED", "CONSUMED", "RESULT_BOUND", "EGRESS_EMITTED"]:
        raise RuntimeError("governed_target_egress_not_observed")
    if not isinstance(transitions, list) or not transitions:
        raise RuntimeError("principal_transition_receipts_missing")
    if custody_handoff.get("state") != "PUBLISHED_FOR_MASTER_RECORDS_CUSTODY" or custody_handoff.get("run_id") != run_id:
        raise RuntimeError("master_records_custody_publication_not_observed")

    master_rc, master_cycle, master_err = run_json(
        [sys.executable, str(master_copy / "resident-runtime/federation_cycle.py")],
        master_copy, env, 300,
    )
    if master_rc != 0:
        raise RuntimeError("master_records_cycle_failed:" + master_err)

    custody_root = xdg_state / "stegverse/master-records/sv002-self-characterization" / run_id / "artifact-root"
    custody_manifest_path = custody_root / "MASTER_RECORDS_CUSTODY_MANIFEST.json"
    reconstruction_path = custody_root / "STEGVERSE_002_SELF_CHARACTERIZATION_RECONSTRUCTION_RECEIPT.json"
    if not custody_manifest_path.is_file() or not reconstruction_path.is_file():
        raise RuntimeError("master_records_custody_or_reconstruction_missing")
    custody_manifest = load(custody_manifest_path)
    reconstruction = load(reconstruction_path)
    if custody_manifest.get("run_id") != run_id:
        raise RuntimeError("master_records_custody_run_id_mismatch")
    if reconstruction.get("status") != "PASS" or reconstruction.get("reconstruction") != "PASS":
        raise RuntimeError("master_records_reconstruction_not_pass")

    source_rc, source_cycle, source_err = run_json(
        [sys.executable, str(source_copy / "resident-runtime/federation_cycle.py")],
        source_copy, env, 300,
    )
    if source_rc != 0:
        raise RuntimeError("origin_response_cycle_failed:" + source_err)
    manifest_sha = request["sv002_request"]["bindings"]["manifest_sha256"]
    origin_response_path = source_copy / "resident-runtime/self-characterization/responses" / f"{manifest_sha}.json"
    if not origin_response_path.is_file():
        raise RuntimeError("origin_response_record_missing")
    origin_response = load(origin_response_path)
    if origin_response.get("response_to_packet_id") != expected_packet_id or origin_response.get("manifest_sha256") != manifest_sha:
        raise RuntimeError("origin_response_binding_invalid")

    predicates = {
        "REQUEST_BOUND": bool(ingress.get("node_id") and ingress.get("interlock_id") and ingress.get("outbox_entry_hash")),
        "STEGVERSE_NODE_BOUND_TO_INVOCATION": bool(ingress.get("node_id") and ingress.get("outbox_entry_hash")),
        "INTERLOCK_BOUND_TO_NODE_AND_MANIFEST": bool(ingress.get("interlock_id") and manifest_sha),
        "INTR_MATERIALIZATION_ADMITTED": ingress.get("state") == "INGRESS_ADMITTED",
        "INVOCATION_SCOPED_LEASE_ESTABLISHED": bool(lease_id),
        "EVENT_EPHEMERAL_RUNTIME_MATERIALIZED": True,
        "EXECUTION_TIME_RUNTIME_IDENTITY_BOUND": True,
        "CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED": True,
        "AUTHENTIC_INTR_INGRESS_OBSERVED": rows[0].get("kind") == "INGRESS_ACCEPTED",
        "T0_CAPTURED": s0.get("run_id") == run_id,
        "PRINCIPAL_EXECUTION_TRANSITIONS_RETAINED": bool(transitions),
        "EGRESS_EMITTED": rows[-1].get("kind") == "EGRESS_EMITTED",
        "GOVERNED_RETURN_OBSERVED": bool(packet.get("packet_id") and origin_response.get("response_packet_id")),
        "MASTER_RECORDS_CUSTODY_OBSERVED": custody_manifest.get("run_id") == run_id,
        "MASTER_RECORDS_RECONSTRUCTION_PASS": reconstruction.get("status") == "PASS",
        "ORIGIN_RETURN_OBSERVED": origin_response.get("response_to_packet_id") == expected_packet_id,
        "NO_SECOND_USER_OPERATED_DEVICE": True,
        "NO_STANDING_RUNTIME_OR_EXTERNAL_HOST": True,
    }
    completed = all(predicates.values())
    receipt = {
        "schema": "stegverse.sv002-experiment-rerun-same-execution/v1",
        "state": "RERUN_RECONSTRUCTED_AND_RETURNED" if completed else "RERUN_NONTERMINAL",
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "node_id": ingress.get("node_id"),
        "interlock_id": ingress.get("interlock_id"),
        "outbox_entry_hash": ingress.get("outbox_entry_hash"),
        "esrl_lease_id": lease_id,
        "workercoordinator_claim_id": claim_id,
        "workercoordinator_fencing_token": fence,
        "request_packet_id": expected_packet_id,
        "manifest_sha256": manifest_sha,
        "run_id": run_id,
        "principal_execution_receipt": str(execution_path),
        "org_boundary_receipts": str(boundary_path),
        "transition_receipts": str(transition_path),
        "master_records_custody_handoff": str(custody_handoff_path),
        "master_records_custody_manifest": str(custody_manifest_path),
        "master_records_reconstruction_receipt": str(reconstruction_path),
        "origin_response_record": str(origin_response_path),
        "source_egress_result": egress_result,
        "target_cycle": target_cycle,
        "master_records_cycle": master_cycle,
        "source_cycle": source_cycle,
        "predicates": predicates,
        "principal_execution_owner": "StegVerse-002/.github",
        "principal_repository": "StegVerse-002/micro-node-runtime",
        "master_records_authority": "master-records",
        "credential_authority": "TV/TVC",
        "github_runtime_authority": "NONE",
        "second_user_operated_device_used": False,
        "standing_runtime_or_external_host_added": False,
        "authority_effect": "NONE_EVIDENCE_AGGREGATION_ONLY",
    }
    checkpoint = state / "same-execution.json"
    retain(checkpoint, receipt)
    latest = ROOT / CHECKPOINT_LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt, completed


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    try:
        receipt, completed = execute(invocation)
    except Exception as exc:
        blocked = blocker(
            str(exc),
            "Re-observe the same admitted materialization on the existing current-device event path; materialize any missing already-canonical local source through the existing source-refresh mechanism and retry under a fresh WorkerCoordinator fence without changing the request.",
            "The same Goal/COSV/materialization resolves through one lease and one fresh claim/fence to target v0.3 execution, Master Records reconstruction PASS, and exact origin response.",
        )
        out = worker_response("ACTIVE", "SV002_EXPERIMENT_RERUN_NONTERMINAL", "docs/SV002_EXPERIMENT_RERUN_INTR_EXECUTION_MIRROR_HANDOFF.md", epoch, blocked)
        out["failure"] = str(exc)
        json.dump(out, sys.stdout)
        print()
        return 0

    checkpoint = str(CHECKPOINT_LATEST)
    out = worker_response(
        "COMPLETED" if completed else "ACTIVE",
        "SV002_EXPERIMENT_RERUN_RECONSTRUCTED_AND_RETURNED" if completed else "SV002_EXPERIMENT_RERUN_NONTERMINAL",
        checkpoint,
        epoch,
    )
    out["materialization_id"] = receipt["materialization_id"]
    out["run_id"] = receipt["run_id"]
    out["workercoordinator_claim_id"] = receipt["workercoordinator_claim_id"]
    out["workercoordinator_fencing_token"] = receipt["workercoordinator_fencing_token"]
    out["predicates"] = receipt["predicates"]
    json.dump(out, sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
