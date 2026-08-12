#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-DURABLE-RUNTIME-ACTIVATION"
RECEIPT_ROOT = (ROOT / "receipts" / "sovereign-runtime-activation").resolve()
CANDIDATE_EVIDENCE = [
    Path("/var/lib/stegverse/heartbeat/activation.latest.json"),
    Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json",
    ROOT / "runtime" / "sovereign" / "activation.latest.json",
]
NODE_MARKERS = [Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json"]
THIRD_PARTY_ENV_VARS = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
REQUIRED_PREDICATES = [
    "runtime_materialized",
    "native_service_active",
    "continuous_runtime_live",
    "heartbeat_epoch_advanced",
    "worker_coordination_checkpoint_observed",
    "controlled_restart_observed",
    "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
]


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment() -> bool:
    return any(truthy(os.environ.get(name)) for name in THIRD_PARTY_ENV_VARS)


def sovereign_node_declared() -> bool:
    return truthy(os.environ.get("STEGVERSE_SOVEREIGN_NODE")) or any(path.is_file() for path in NODE_MARKERS)


def default_runtime_root() -> Path:
    override = os.environ.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def load_evidence() -> tuple[Path | None, dict | None]:
    for path in CANDIDATE_EVIDENCE:
        if not path.exists():
            continue
        try:
            return path, json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return path, None
    return None, None


def execute_native_solution() -> dict:
    result = {
        "attempted": False,
        "eligible_node": False,
        "hosted_environment_rejected": False,
        "installer_returncode": None,
        "verifier_returncode": None,
        "runtime_root": str(default_runtime_root()),
    }
    if third_party_hosted_environment():
        result["hosted_environment_rejected"] = True
        result["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
        return result
    if not sovereign_node_declared():
        result["reason"] = "SOVEREIGN_NODE_DECLARATION_NOT_PRESENT"
        return result

    result["eligible_node"] = True
    result["attempted"] = True
    runtime_root = default_runtime_root()
    installer = ROOT / "scripts" / "install_sovereign_heartbeat_service.py"
    verifier = ROOT / "scripts" / "verify_sovereign_runtime_activation.py"
    if not installer.is_file() or not verifier.is_file():
        result["reason"] = "ACTIVATION_TOOLING_MISSING"
        return result

    install = subprocess.run(
        [sys.executable, str(installer), "--source-root", str(ROOT), "--runtime-root", str(runtime_root)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    result["installer_returncode"] = install.returncode
    if install.returncode != 0:
        result["reason"] = "NATIVE_INSTALLATION_RETRY_REQUIRED"
        return result

    verify = subprocess.run(
        [sys.executable, str(verifier), "--runtime-root", str(runtime_root)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    result["verifier_returncode"] = verify.returncode
    result["reason"] = "SOVEREIGN_ACTIVATION_VERIFIED" if verify.returncode == 0 else "SOVEREIGN_ACTIVATION_PROOF_INCOMPLETE"
    return result


def unresolved_node_resolution_contract() -> dict:
    """Describe a physical-resource collision for engine-v11 task derivation.

    The current G18 worker cannot manufacture a new sovereign node or expand its
    own authority. Returning BLOCKED is therefore only a trigger for the
    canonical RESOLVE/ESCALATE path; it is never permission for passive waiting.
    """
    return {
        "dependency_class": "PHYSICAL_RESOURCE",
        "trigger_type": "CONDITIONAL_CONSTRAINT",
        "problem_statement": "No currently executing environment is declared as a StegVerse-owned/federated sovereign node eligible for native service activation.",
        "solution_required": True,
        "resolvable_by_current_worker": False,
        "escalation_target": "REPOSITORY_OWNER",
        "required_capabilities": ["repository_resolution", "sandbox_validation"],
        "workaround_candidates": [
            "Bind this worker to any existing StegVerse-owned/federated Linux, macOS, or Windows node by installing the node declaration and running the canonical native installer.",
            "Promote an existing StegVerse-002 micro-node to the carrier if it satisfies durable-state and native-supervision requirements.",
            "Construct a new StegVerse-owned/federated node from the repository-local runtime capsule; no hosted provider is required."
        ],
        "next_solution_action": "Derive and register the next-level sovereign-node resolution task; that resolver must select, promote, or construct an eligible node without weakening the no-hosted-provider or TV/TVC authority boundary.",
        "completion_evidence": [
            "An eligible StegVerse-owned/federated node declaration is machine-observable.",
            "The canonical native installer and verifier can execute on that node without GitHub-token or hosted-provider production authority."
        ],
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 4
    execution = handoff.get("execution") or {}
    required_caps = set(execution.get("required_capabilities") or [])
    for cap in ("runtime_observation", "continuous_process_execution", "durable_state_reconstruction", "bounded_repository_mutation"):
        if cap not in required_caps:
            return 5
    if "receipts/sovereign-runtime-activation/**" not in set(execution.get("allowed_paths") or []):
        return 6

    evidence_path, evidence = load_evidence()
    passed = bool(evidence) and all(evidence.get(name) is True for name in REQUIRED_PREDICATES)
    solution_attempt = {"attempted": False, "reason": "EXISTING_PROOF_COMPLETE"} if passed else execute_native_solution()
    if not passed and solution_attempt.get("attempted"):
        evidence_path, evidence = load_evidence()
        passed = bool(evidence) and all(evidence.get(name) is True for name in REQUIRED_PREDICATES)

    missing = [] if passed else (REQUIRED_PREDICATES if evidence is None else [name for name in REQUIRED_PREDICATES if evidence.get(name) is not True])
    if passed:
        transition = "SOVEREIGN_RUNTIME_VERIFIED"
        state = "COMPLETED"
        blocker = None
        expected = None
    elif solution_attempt.get("attempted"):
        transition = "SOVEREIGN_RUNTIME_SOLUTION_EXECUTING"
        state = "ACTIVE"
        expected = "SOVEREIGN_RUNTIME_SOLUTION_EXECUTION"
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "A declared sovereign node exists, but native installation and/or nine-predicate activation proof is not complete yet.",
            "solution_required": True,
            "workaround_candidates": [
                "Retry the node-local native installer and verifier on the same declared node.",
                "Switch to another declared StegVerse-owned/federated node if native supervision cannot satisfy the proof predicates.",
                "Use a StegVerse-002 micro-node carrier that can persist the same canonical runtime state and restart proof."
            ],
            "next_solution_action": "Continue node-local installer/verifier execution until the proof producer emits all nine predicates true or select another eligible sovereign node."
        }
    else:
        transition = "SOVEREIGN_RUNTIME_RESOLUTION_ESCALATION_REQUIRED"
        state = "BLOCKED"
        expected = "DERIVE_AND_REGISTER_RESOLUTION_TASK"
        blocker = unresolved_node_resolution_contract()

    receipt = {
        "schema": "stegverse.sovereign-runtime-worker-receipt/v0.4",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "state": state,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "required_predicates": REQUIRED_PREDICATES,
        "missing_predicates": missing,
        "solution_attempt": solution_attempt,
        "third_party_runtime_required": False,
        "third_party_dependency_is_blocker": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "authority_effect": "bounded_native_runtime_activation_under_existing_handoff",
        "completed": passed,
    }
    receipt_path = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 3,
        "expected_next_transition": expected,
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
        "evidence_refs": [
            f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
            "scripts/install_sovereign_heartbeat_service.py",
            "scripts/verify_sovereign_runtime_activation.py",
            "StegVerse-Labs/.github#12",
            "StegVerse-Labs/.github#59",
            "StegVerse-Labs/.github#65",
            "control/blocker-resolution-policy.json"
        ],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 2 if solution_attempt.get("attempted") else 1,
            "external_cost_usd": 0,
            "task_class": "sovereign_runtime_activation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
