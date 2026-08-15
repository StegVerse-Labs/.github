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
THIRD_PARTY_ENV_VARS = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
REQUIRED_PREDICATES = [
    "runtime_materialized", "native_service_active", "continuous_runtime_live",
    "heartbeat_epoch_advanced", "worker_coordination_checkpoint_observed",
    "controlled_restart_observed", "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence", "state_reconstruction_pass",
]
SAFE_BOOTSTRAP_ENV = {
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "LANG", "LC_ALL", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID",
}


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(values.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def bootstrap_receipt_path() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "bootstrap.latest.json").resolve()


def clean_bootstrap_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Forward only non-secret local process/runtime locators to self-bootstrap."""
    values = os.environ if env is None else env
    clean = {name: values[name] for name in SAFE_BOOTSTRAP_ENV if values.get(name)}
    clean["STEGVERSE_HEARTBEAT_ROOT"] = str(default_runtime_root(values))
    # Explicitly carry no authority-bearing token/secret/key material. The bootstrap
    # derives local node eligibility and TV/TVC remains the only credential authority.
    return clean


def load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def load_evidence() -> tuple[Path | None, dict | None]:
    for path in CANDIDATE_EVIDENCE:
        if path.exists():
            return path, load_json(path)
    return None, None


def execute_native_solution() -> dict:
    """Run the released self-bootstrap; no pre-existing node declaration is required."""
    runtime_root = default_runtime_root()
    result = {
        "attempted": False,
        "eligible_node": False,
        "pre_existing_node_declaration_required": False,
        "hosted_environment_rejected": False,
        "bootstrap_returncode": None,
        "runtime_root": str(runtime_root),
        "node_declaration_marker": None,
        "bootstrap_receipt_ref": str(bootstrap_receipt_path()),
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_forwarded": False,
    }
    if third_party_hosted_environment():
        result["hosted_environment_rejected"] = True
        result["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
        return result

    bootstrap = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"
    if not bootstrap.is_file():
        result["reason"] = "SOVEREIGN_SELF_BOOTSTRAP_TOOLING_MISSING"
        return result

    result["attempted"] = True
    completed = subprocess.run(
        [sys.executable, str(bootstrap), "--source-root", str(ROOT), "--runtime-root", str(runtime_root)],
        capture_output=True,
        text=True,
        timeout=420,
        check=False,
        env=clean_bootstrap_env(),
    )
    result["bootstrap_returncode"] = completed.returncode
    receipt = load_json(bootstrap_receipt_path()) or {}
    result["bootstrap_state"] = receipt.get("state")
    result["bootstrap_reason"] = receipt.get("reason")
    result["node_declaration_marker"] = receipt.get("node_declaration_ref")
    result["eligible_node"] = bool((receipt.get("node_eligibility") or {}).get("eligible"))
    result["post_bootstrap_stegfin"] = receipt.get("post_bootstrap_stegfin")
    if completed.returncode == 0 and receipt.get("state") == "COMPLETE":
        result["reason"] = "SOVEREIGN_SELF_BOOTSTRAP_VERIFIED"
    else:
        result["reason"] = receipt.get("reason") or "SOVEREIGN_SELF_BOOTSTRAP_INCOMPLETE"
    return result


def unresolved_node_resolution_contract(solution_attempt: dict | None = None) -> dict:
    return {
        "dependency_class": "PHYSICAL_RESOURCE",
        "trigger_type": "CONDITIONAL_CONSTRAINT",
        "problem_statement": "The released self-bootstrap could not establish the sovereign local runtime on the current execution surface; a pre-existing node declaration is not required.",
        "solution_required": True,
        "resolvable_by_current_worker": False,
        "escalation_target": "REPOSITORY_OWNER",
        "required_capabilities": ["repository_resolution", "sandbox_validation"],
        "observed_bootstrap_reason": (solution_attempt or {}).get("reason"),
        "workaround_candidates": [
            "Bind G18 to an existing StegVerse-owned/federated non-hosted Linux, macOS, or Windows surface containing canonical local source; G18 invokes self-bootstrap itself.",
            "Promote an existing StegVerse-002 micro-node by materializing the canonical runtime capsule; no hand-created node declaration is required.",
            "Construct a StegVerse-owned/federated node from the repository-local runtime capsule without hosted-provider or GitHub-token production authority."
        ],
        "next_solution_action": "Bind the canonical G18 worker to an eligible non-hosted local execution surface containing canonical source/runtime capsule; it will invoke scripts/bootstrap_sovereign_runtime.py automatically.",
        "completion_evidence": [
            "bootstrap.latest.json COMPLETE with credential_requirement NONE and credential_authority TV/TVC",
            "activation.latest.json has all nine predicates true",
            "no non-TV/TVC secret/token or hosted-provider production authority is used"
        ],
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    execution = (invocation.get("handoff") or {}).get("execution") or {}
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    if not claim_id or not isinstance(fence, int):
        return 4
    required_caps = set(execution.get("required_capabilities") or [])
    if not {"runtime_observation", "continuous_process_execution", "durable_state_reconstruction", "bounded_repository_mutation"}.issubset(required_caps):
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
    hard_surface_reasons = {
        "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE",
        "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN",
        "SOVEREIGN_SELF_BOOTSTRAP_TOOLING_MISSING",
    }
    if passed:
        transition, state, expected, blocker = "SOVEREIGN_RUNTIME_VERIFIED", "COMPLETED", None, None
    elif solution_attempt.get("attempted") and solution_attempt.get("reason") not in hard_surface_reasons:
        transition, state, expected = "SOVEREIGN_RUNTIME_SOLUTION_EXECUTING", "ACTIVE", "SOVEREIGN_RUNTIME_SOLUTION_EXECUTION"
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "Canonical self-bootstrap was attempted on this non-hosted surface, but nine-predicate activation proof is not complete.",
            "solution_required": True,
            "workaround_candidates": ["Retry the released self-bootstrap after its machine-observable condition clears.", "Use another StegVerse-owned/federated non-hosted surface containing the same canonical runtime capsule."],
            "next_solution_action": "Continue canonical self-bootstrap until activation.latest.json has all nine predicates true or exact fail-closed evidence requires local-surface remediation."
        }
    else:
        transition, state, expected = "SOVEREIGN_RUNTIME_RESOLUTION_ESCALATION_REQUIRED", "BLOCKED", "DERIVE_AND_REGISTER_RESOLUTION_TASK"
        blocker = unresolved_node_resolution_contract(solution_attempt)

    receipt = {
        "schema": "stegverse.sovereign-runtime-worker-receipt/v0.5",
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
        "pre_existing_node_declaration_required": False,
        "self_bootstrap_entrypoint": "scripts/bootstrap_sovereign_runtime.py",
        "third_party_runtime_required": False,
        "third_party_dependency_is_blocker": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_forwarded": False,
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
        "evidence_refs": [f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json", "scripts/bootstrap_sovereign_runtime.py", "scripts/verify_sovereign_runtime_activation.py", "StegVerse-Labs/.github#12", "management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json"],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 2 if solution_attempt.get("attempted") else 1, "external_cost_usd": 0, "task_class": "sovereign_runtime_activation"},
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
