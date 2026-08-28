#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

EXPECTED_CAPABILITIES = {"repository_resolution", "sandbox_validation"}
RECEIPT_ROOT = Path("receipts/sovereign-runtime-activation")
NODE_MARKERS = [Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json"]
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
CANONICAL_RUNTIME_FILES = (
    Path("heartbeat_runtime/engine_v13.py"),
    Path("heartbeat_runtime/independent_oscillator.py"),
    Path("heartbeat_runtime/oscillator_producer.py"),
    Path("heartbeat_runtime/worker_runtime.py"),
    Path("heartbeat_runtime/assignment_timer.py"),
    Path("scripts/install_sovereign_heartbeat_service.py"),
    Path("scripts/verify_sovereign_runtime_activation.py"),
    Path("scripts/run_heartbeat_runtime.py"),
    Path("scripts/run_worker_runtime.py"),
    Path("scripts/advance_heartbeat_transition.py"),
    Path("control/heartbeat-state.json"),
    Path("control/worker-registry.json"),
    Path("management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json"),
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment() -> bool:
    return any(truthy(os.environ.get(name)) for name in THIRD_PARTY_ENV_VARS)


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def existing_node_declaration() -> tuple[bool, str | None]:
    if truthy(os.environ.get("STEGVERSE_SOVEREIGN_NODE")):
        return True, "env:STEGVERSE_SOVEREIGN_NODE"
    for path in NODE_MARKERS:
        if path.is_file():
            return True, str(path)
    return False, None


def canonical_runtime_root() -> Path:
    override = os.environ.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path.cwd().resolve()


def durable_state_root() -> Path:
    override = os.environ.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    base = os.environ.get("XDG_STATE_HOME")
    if base:
        return (Path(base).expanduser().resolve() / "stegverse" / "heartbeat-runtime")
    return (Path.home() / ".local" / "state" / "stegverse" / "heartbeat-runtime").resolve()


def local_runtime_eligibility() -> dict:
    source_root = canonical_runtime_root()
    state_root = durable_state_root()
    canonical_files = {str(path): (source_root / path).is_file() for path in CANONICAL_RUNTIME_FILES}
    try:
        state_root.mkdir(parents=True, exist_ok=True)
        probe = state_root / ".eligibility-write-probe"
        probe.write_text("stegverse\n", encoding="utf-8")
        probe.unlink()
        durable_state_writable = True
    except Exception:
        durable_state_writable = False
    third_party = hosted_environment()
    return {
        "source_root": str(source_root),
        "state_root": str(state_root),
        "canonical_files": canonical_files,
        "canonical_runtime_complete": all(canonical_files.values()),
        "durable_state_writable": durable_state_writable,
        "hosted_environment_rejected": third_party,
        "eligible": all(canonical_files.values()) and durable_state_writable and not third_party,
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False,
        "always_on_external_host_required": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "third_party_runtime_required": False,
    }


def derive_node_declaration() -> tuple[bool, str | None, dict]:
    declared, ref = existing_node_declaration()
    eligibility = local_runtime_eligibility()
    if declared:
        eligibility["declaration_mode"] = "EXISTING"
        return True, ref, eligibility
    if not eligibility["eligible"]:
        eligibility["declaration_mode"] = "NOT_DERIVED"
        return False, None, eligibility

    marker = Path.home() / ".stegverse" / "node.json"
    atomic_write(
        marker,
        {
            "schema": "stegverse.sovereign-node-declaration/v0.4",
            "declared": True,
            "declaration_source": "DERIVED_LOCAL_RUNTIME_ELIGIBILITY",
            "source_root": eligibility["source_root"],
            "state_root": eligibility["state_root"],
            "canonical_runtime_complete": True,
            "durable_state_writable": True,
            "hosted_environment_rejected": False,
            "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
            "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
            "heartbeat_event_trigger_required": False,
            "always_on_external_host_required": False,
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "third_party_runtime_required": False,
            "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
        },
    )
    eligibility["declaration_mode"] = "DERIVED_LOCAL_RUNTIME_ELIGIBILITY"
    return True, str(marker), eligibility


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    scope = invocation.get("scope") or {}
    if not isinstance(epoch, int):
        return 3
    task_id = str(task.get("task_id") or "")
    if not task_id or "SHWP-DURABLE-RUNTIME-ACTIVATION" not in task_id:
        return 4
    required = set(scope.get("required_capabilities") or handoff.get("execution", {}).get("required_capabilities") or [])
    if not EXPECTED_CAPABILITIES.issubset(required):
        return 5
    claim_id = str(task.get("claim_id") or "")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not claim_id or not isinstance(fence, int) or fence < 1:
        return 6

    declared, declaration_ref, eligibility = derive_node_declaration()
    third_party = eligibility["hosted_environment_rejected"]
    if declared and not third_party:
        state = "COMPLETED"
        transition = "SOVEREIGN_NODE_DECLARATION_RESOLVED"
        expected = None
        blocker = None
    else:
        state = "BLOCKED"
        transition = "SOVEREIGN_NODE_COMPONENT_ESCALATION_REQUIRED"
        expected = "DERIVE_AND_REGISTER_RESOLUTION_TASK"
        blocker = {
            "trigger_type": "CONDITIONAL_CONSTRAINT",
            "dependency_class": "PHYSICAL_RESOURCE",
            "problem_statement": (
                "Repository-owner resolution cannot prove a non-hosted local runtime surface with canonical source and writable durable state."
            ),
            "solution_required": True,
            "workaround_candidates": [
                "Execute the resolver from an already locally materialized canonical StegVerse heartbeat source tree; it will derive the node declaration automatically when local eligibility passes.",
                "Set STEGVERSE_HEARTBEAT_SOURCE_ROOT to an already materialized canonical source tree and STEGVERSE_HEARTBEAT_ROOT to writable durable node-local state.",
                "Component authority may select another StegVerse-owned/federated node only if local runtime eligibility cannot be satisfied on the current surface."
            ],
            "next_solution_action": "Retry on a non-hosted local surface containing the canonical runtime files and writable durable state; do not require a hand-created declaration marker.",
            "resolvable_by_current_worker": False,
            "escalation_target": "COMPONENT_AUTHORITY",
            "required_capabilities": ["component_resolution", "governance_validation"],
            "completion_evidence": [
                "A v0.4 derived sovereign-node declaration records the canonical v13 oscillator/WorkerCoordinator runtime source and writable durable state.",
                "The canonical native installer and verifier can execute without GitHub-token or hosted-provider production authority."
            ],
        }

    receipt = {
        "schema": "stegverse.sovereign-node-repository-resolution-receipt/v0.2",
        "task_id": task_id,
        "claim_id": claim_id,
        "fencing_token": fence,
        "heartbeat_epoch": epoch,
        "state": state,
        "transition_id": transition,
        "node_declared": declared,
        "node_declaration_ref": declaration_ref,
        "node_eligibility": eligibility,
        "hosted_environment_rejected": third_party,
        "github_token_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "RUNTIME_ELIGIBILITY_RESOLUTION_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
    }
    receipt_path = RECEIPT_ROOT / f"{task_id}.repository-resolution.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 2,
        "expected_next_transition": expected,
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": receipt_path.as_posix(),
        "evidence_refs": [receipt_path.as_posix(), declaration_ref] if declaration_ref else [receipt_path.as_posix()],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "sovereign_node_repository_resolution",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
