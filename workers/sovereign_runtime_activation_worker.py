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


def sovereign_node_declared() -> bool:
    return truthy(os.environ.get("STEGVERSE_SOVEREIGN_NODE")) or any(path.is_file() for path in NODE_MARKERS)


def persist_authorized_node_declaration() -> Path | None:
    """Persist an already-explicit declaration; never manufacture authority."""
    for marker in NODE_MARKERS:
        if marker.is_file():
            return marker
    if not truthy(os.environ.get("STEGVERSE_SOVEREIGN_NODE")):
        return None
    marker = Path.home() / ".stegverse" / "node.json"
    atomic_write(marker, {
        "schema": "stegverse.sovereign-node-declaration/v0.1",
        "declared": True,
        "declaration_source": "STEGVERSE_SOVEREIGN_NODE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "PERSIST_EXISTING_NODE_DECLARATION_ONLY",
    })
    return marker


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


def canonical_proof_path() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json").resolve()


def ephemeral_console_root() -> Path:
    return (default_runtime_root().parent / "ephemeral-sovereign-console").resolve()


def ephemeral_console_receipt_path() -> Path:
    return (ephemeral_console_root() / "ephemeral-console.latest.json").resolve()


def clean_bootstrap_env(env: dict[str, str] | None = None) -> dict[str, str]:
    values = os.environ if env is None else env
    clean = {name: values[name] for name in SAFE_BOOTSTRAP_ENV if values.get(name)}
    clean["STEGVERSE_HEARTBEAT_ROOT"] = str(default_runtime_root(values))
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
    """Run released self-bootstrap, then one-host logical-node fallback if needed."""
    runtime_root = default_runtime_root()
    explicit_marker = persist_authorized_node_declaration()
    result = {
        "attempted": False,
        "eligible_node": explicit_marker is not None,
        "pre_existing_node_declaration_required": False,
        "physical_additional_machine_required": False,
        "hosted_environment_rejected": False,
        "bootstrap_returncode": None,
        "runtime_root": str(runtime_root),
        "node_declaration_marker": str(explicit_marker) if explicit_marker else None,
        "bootstrap_receipt_ref": str(bootstrap_receipt_path()),
        "ephemeral_console_attempted": False,
        "ephemeral_console_returncode": None,
        "ephemeral_console_receipt_ref": str(ephemeral_console_receipt_path()),
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
        capture_output=True, text=True, timeout=420, check=False, env=clean_bootstrap_env(),
    )
    result["bootstrap_returncode"] = completed.returncode
    receipt = load_json(bootstrap_receipt_path()) or {}
    result["bootstrap_state"] = receipt.get("state")
    result["bootstrap_reason"] = receipt.get("reason")
    result["node_declaration_marker"] = receipt.get("node_declaration_ref") or result["node_declaration_marker"]
    result["eligible_node"] = bool((receipt.get("node_eligibility") or {}).get("eligible")) or result["eligible_node"]
    result["post_bootstrap_stegfin"] = receipt.get("post_bootstrap_stegfin")

    if completed.returncode == 0 and receipt.get("state") == "COMPLETE":
        result["reason"] = "SOVEREIGN_SELF_BOOTSTRAP_VERIFIED"
        return result

    console = ROOT / "scripts" / "run_sovereign_ephemeral_console.py"
    if not console.is_file():
        result["reason"] = receipt.get("reason") or "SOVEREIGN_EPHEMERAL_CONSOLE_TOOLING_MISSING"
        return result

    result["ephemeral_console_attempted"] = True
    console_completed = subprocess.run(
        [
            sys.executable,
            str(console),
            "--source-root", str(ROOT),
            "--console-root", str(ephemeral_console_root()),
            "--canonical-proof-path", str(canonical_proof_path()),
        ],
        capture_output=True, text=True, timeout=600, check=False, env=clean_bootstrap_env(),
    )
    result["ephemeral_console_returncode"] = console_completed.returncode
    console_receipt = load_json(ephemeral_console_receipt_path()) or {}
    result["ephemeral_console_state"] = console_receipt.get("state")
    result["ephemeral_console_reason"] = console_receipt.get("reason")
    result["logical_node_count"] = console_receipt.get("requested_node_count")
    result["third_logical_machine_proven"] = console_receipt.get("third_logical_machine_proven") is True
    result["primary_runtime_retained"] = console_receipt.get("primary_retained") is True
    result["canonical_proof_promoted"] = console_receipt.get("canonical_proof_promoted") is True
    if console_completed.returncode == 0 and console_receipt.get("state") == "COMPLETE" and result["canonical_proof_promoted"]:
        result["reason"] = "SOVEREIGN_EPHEMERAL_CONSOLE_VERIFIED"
    else:
        result["reason"] = console_receipt.get("reason") or receipt.get("reason") or "SOVEREIGN_RUNTIME_SOLUTION_INCOMPLETE"
    return result


def unresolved_node_resolution_contract(solution_attempt: dict | None = None) -> dict:
    return {
        "dependency_class": "LOCAL_EXECUTION_SURFACE",
        "trigger_type": "CONDITIONAL_CONSTRAINT",
        "problem_statement": "Neither native bootstrap nor the one-host StegVerse ephemeral logical-node console established the sovereign runtime on the current execution surface. A second or third physical machine is not required.",
        "solution_required": True,
        "resolvable_by_current_worker": False,
        "escalation_target": "SOVEREIGN_RUNTIME_OWNER",
        "required_capabilities": ["local_process_execution", "writable_state", "repository_resolution"],
        "observed_bootstrap_reason": (solution_attempt or {}).get("bootstrap_reason"),
        "observed_ephemeral_console_reason": (solution_attempt or {}).get("ephemeral_console_reason"),
        "physical_additional_machine_required": False,
        "workaround_candidates": [
            "On any one StegVerse-owned/federated non-hosted Linux, macOS, or Windows surface containing canonical source, let G18 invoke self-bootstrap and then the three-logical-node ephemeral console automatically.",
            "Use an existing StegVerse-002 micro-node as that single host; peer-machine validation is emulated with isolated node identities/state roots/processes.",
            "Use the repository-local runtime capsule on one sovereign host; do not add a hosted provider or separate physical machine dependency."
        ],
        "next_solution_action": "Run canonical G18 on one eligible non-hosted StegVerse-controlled surface. The worker automatically tries native self-bootstrap, then scripts/run_sovereign_ephemeral_console.py if needed.",
        "completion_evidence": [
            "activation.latest.json has all nine predicates true",
            "ephemeral-console.latest.json proves three isolated logical nodes when fallback is used",
            "physical_additional_machine_required=false",
            "no non-TV/TVC secret/token or hosted-provider production authority is used"
        ],
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1": return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    execution = (invocation.get("handoff") or {}).get("execution") or {}
    timing = task.get("heartbeat_timing") or {}
    claim_id, fence = task.get("claim_id"), timing.get("fencing_token")
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK: return 3
    if not claim_id or not isinstance(fence, int): return 4
    required_caps = set(execution.get("required_capabilities") or [])
    if not {"runtime_observation","continuous_process_execution","durable_state_reconstruction","bounded_repository_mutation"}.issubset(required_caps): return 5
    if "receipts/sovereign-runtime-activation/**" not in set(execution.get("allowed_paths") or []): return 6

    evidence_path, evidence = load_evidence()
    passed = bool(evidence) and all(evidence.get(name) is True for name in REQUIRED_PREDICATES)
    solution_attempt = {"attempted": False, "reason": "EXISTING_PROOF_COMPLETE", "physical_additional_machine_required": False} if passed else execute_native_solution()
    if not passed and solution_attempt.get("attempted"):
        evidence_path, evidence = load_evidence()
        passed = bool(evidence) and all(evidence.get(name) is True for name in REQUIRED_PREDICATES)
    missing = [] if passed else (REQUIRED_PREDICATES if evidence is None else [n for n in REQUIRED_PREDICATES if evidence.get(n) is not True])
    hard_surface_reasons = {"THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE","LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN","SOVEREIGN_SELF_BOOTSTRAP_TOOLING_MISSING","HOSTED_RUNNER_MAY_VALIDATE_SOURCE_BUT_CANNOT_PRODUCE_SOVEREIGN_ACTIVATION"}
    if passed:
        transition, state, expected, blocker = "SOVEREIGN_RUNTIME_VERIFIED", "COMPLETED", None, None
    elif solution_attempt.get("attempted") and solution_attempt.get("reason") not in hard_surface_reasons:
        transition, state, expected = "SOVEREIGN_RUNTIME_SOLUTION_EXECUTING", "ACTIVE", "SOVEREIGN_RUNTIME_SOLUTION_EXECUTION"
        blocker = {
            "dependency_class":"INTERNAL_CAPABILITY",
            "problem_statement":"Canonical native bootstrap and/or one-host ephemeral console executed on this non-hosted surface, but the nine-predicate proof is not complete.",
            "solution_required":True,
            "physical_additional_machine_required":False,
            "workaround_candidates":["Retry the same released one-host path after its machine-observable condition clears."],
            "next_solution_action":"Continue native bootstrap/ephemeral-console execution until activation.latest.json passes or exact local fail-closed evidence identifies the remaining defect."
        }
    else:
        transition, state, expected, blocker = "SOVEREIGN_RUNTIME_RESOLUTION_ESCALATION_REQUIRED", "BLOCKED", "DERIVE_AND_REGISTER_RESOLUTION_TASK", unresolved_node_resolution_contract(solution_attempt)

    receipt = {
        "schema":"stegverse.sovereign-runtime-worker-receipt/v0.6","task_id":EXPECTED_TASK,"claim_id":claim_id,
        "worker_id":task.get("worker_id"),"worker_instance_id":task.get("worker_instance_id"),"heartbeat_epoch":epoch,"fencing_token":fence,
        "transition_id":transition,"state":state,"evidence_path":str(evidence_path) if evidence_path else None,"required_predicates":REQUIRED_PREDICATES,"missing_predicates":missing,
        "solution_attempt":solution_attempt,"pre_existing_node_declaration_required":False,"physical_additional_machine_required":False,
        "self_bootstrap_entrypoint":"scripts/bootstrap_sovereign_runtime.py","ephemeral_console_entrypoint":"scripts/run_sovereign_ephemeral_console.py",
        "third_party_runtime_required":False,"third_party_dependency_is_blocker":False,"blocker_policy_ref":"control/blocker-resolution-policy.json","blocker":blocker,
        "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","non_tv_tvc_secret_or_token_forwarded":False,
        "authority_effect":"bounded_native_or_stegverse_local_runtime_activation_under_existing_handoff","completed":passed,
    }
    atomic_write(RECEIPT_ROOT / f"{EXPECTED_TASK}.json", receipt)
    response = {
        "schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":4,"expected_next_transition":expected,
        "expected_next_earliest_epoch":None if passed else epoch+1,"expected_next_latest_epoch":None if passed else epoch+1,
        "checkpoint_ref":f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
        "evidence_refs":[f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json","scripts/bootstrap_sovereign_runtime.py","scripts/run_sovereign_ephemeral_console.py","scripts/verify_sovereign_runtime_activation.py","StegVerse-Labs/.github#12","management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json"],
        "blocker":blocker,"cost_observation":{"hb_transition_count":1,"compute_units":3 if solution_attempt.get("ephemeral_console_attempted") else (2 if solution_attempt.get("attempted") else 1),"external_cost_usd":0,"task_class":"sovereign_runtime_activation"},
    }
    json.dump(response, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0


if __name__ == "__main__": raise SystemExit(main())
