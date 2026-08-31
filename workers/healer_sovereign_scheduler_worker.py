#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "healer-sovereign-scheduler").resolve()
EXPECTED_TASK = "SHWP-HEALER-SOVEREIGN-SCHEDULER-001"
CURRENT_AUTHORITY = "TV/TVC"
EVALUATOR_CONFIG_ENV = "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG"
EVALUATOR_CONFIG_DEFAULT = Path.home() / ".stegverse" / "config" / "evaluator-intr-runtime.json"
SV002_OBSERVE_CONFIG_ENV = "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG"
SV002_OBSERVE_CONFIG_DEFAULT = Path.home() / ".stegverse" / "config" / "sv002-public-observation-runtime.json"
HIL_INTR_CONFIG_ENV = "STEGVERSE_HIL_INTR_ROUTE_CONFIG"
HIL_INTR_CONFIG_DEFAULT = Path.home() / ".stegverse" / "config" / "hil-intr-runtime.json"

CANONICAL_REPO_BASES = (
    Path.home() / ".stegverse" / "repos",
    Path("/var/lib/stegverse/source"),
    Path("/srv/stegverse/repos"),
    Path("/opt/stegverse/repos"),
)


def _complete_healer_root(path: Path) -> bool:
    root = path.expanduser().resolve()
    return (
        root.is_dir()
        and (root / "app" / "dispatch_orchestrators.py").is_file()
        and (root / "data" / "orchestrator_targets.json").is_file()
        and (root / "docs" / "HEALER_MIRROR_HANDOFF.md").is_file()
    )


def discover_healer_root(explicit: str = "") -> tuple[Path | None, str]:
    if explicit.strip():
        root = Path(explicit).expanduser().resolve()
        return (root, "EXPLICIT_NONSECRET_OVERRIDE") if _complete_healer_root(root) else (None, "EXPLICIT_INVALID")
    candidates = [
        base / "StegVerse-Labs" / "StegVerse-Healer"
        for base in CANONICAL_REPO_BASES
    ]
    valid = [path.resolve() for path in candidates if _complete_healer_root(path)]
    unique = list(dict.fromkeys(str(path) for path in valid))
    if len(unique) == 1:
        return Path(unique[0]), "CANONICAL_LOCAL_DISCOVERY"
    return None, "AMBIGUOUS" if len(unique) > 1 else "NOT_FOUND"


def discover_repo_roots(explicit_json: str = "") -> tuple[dict[str, str], str]:
    if explicit_json.strip():
        try:
            parsed = json.loads(explicit_json)
        except Exception:
            return {}, "EXPLICIT_INVALID"
        if not isinstance(parsed, dict):
            return {}, "EXPLICIT_INVALID"
        roots = {}
        for repository, value in parsed.items():
            if not isinstance(repository, str) or "/" not in repository or not isinstance(value, str):
                continue
            path = Path(value).expanduser().resolve()
            if path.is_dir():
                roots[repository] = str(path)
        return roots, "EXPLICIT_NONSECRET_OVERRIDE" if roots else "EXPLICIT_INVALID"

    roots: dict[str, str] = {}
    ambiguous: set[str] = set()
    for base in CANONICAL_REPO_BASES:
        if not base.is_dir():
            continue
        for owner in sorted(path for path in base.iterdir() if path.is_dir()):
            for repository_path in sorted(path for path in owner.iterdir() if path.is_dir()):
                repository = f"{owner.name}/{repository_path.name}"
                resolved = str(repository_path.resolve())
                existing = roots.get(repository)
                if existing and existing != resolved:
                    ambiguous.add(repository)
                else:
                    roots[repository] = resolved
    for repository in ambiguous:
        roots.pop(repository, None)
    return roots, "CANONICAL_LOCAL_DISCOVERY" if roots else "NOT_FOUND"


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def evaluator_gateway_projection() -> dict[str, str]:
    raw = os.environ.get(EVALUATOR_CONFIG_ENV, "").strip()
    path = Path(raw).expanduser().resolve() if raw else EVALUATOR_CONFIG_DEFAULT.expanduser().resolve()
    disabled = {
        "STEGVERSE_EVALUATOR_INTR_ENABLED": "false",
        "STEGVERSE_EVALUATOR_INTR_UPSTREAM": "",
    }
    if not path.is_file():
        return disabled
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return disabled
    if not isinstance(value, dict):
        return disabled
    if value.get("schema") != "stegverse.evaluator-intr-route-config/v1":
        return disabled
    if value.get("credential_authority") != "TV/TVC":
        return disabled
    if value.get("github_token_runtime_authority") != "NONE":
        return disabled
    if value.get("public_tls_terminated_by") != "STEGVERSE_SHARED_SERVICE_GATEWAY":
        return disabled
    if value.get("host") != "127.0.0.1":
        return disabled
    port = value.get("port")
    if not isinstance(port, int) or port < 1024 or port > 65535:
        return disabled
    return {
        "STEGVERSE_EVALUATOR_INTR_ENABLED": "true",
        "STEGVERSE_EVALUATOR_INTR_UPSTREAM": f"http://127.0.0.1:{port}/intr/evaluator",
    }


def sv002_observation_gateway_projection() -> dict[str, str]:
    raw = os.environ.get(SV002_OBSERVE_CONFIG_ENV, "").strip()
    path = Path(raw).expanduser().resolve() if raw else SV002_OBSERVE_CONFIG_DEFAULT.expanduser().resolve()
    disabled = {"STEGVERSE_SV002_OBSERVE_ENABLED": "false", "STEGVERSE_SV002_OBSERVE_UPSTREAM": ""}
    if not path.is_file(): return disabled
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except Exception: return disabled
    if not isinstance(value, dict): return disabled
    if value.get("schema") != "stegverse.sv002-public-observation-route-config/v1": return disabled
    if value.get("credential_authority") != "TV/TVC": return disabled
    if value.get("github_token_runtime_authority") != "NONE": return disabled
    if value.get("public_tls_terminated_by") != "STEGVERSE_SHARED_SERVICE_GATEWAY": return disabled
    if value.get("host") != "127.0.0.1": return disabled
    port = value.get("port")
    if not isinstance(port, int) or port < 1024 or port > 65535: return disabled
    return {"STEGVERSE_SV002_OBSERVE_ENABLED": "true", "STEGVERSE_SV002_OBSERVE_UPSTREAM": f"http://127.0.0.1:{port}/intr/sv002-observe"}



def hil_intr_gateway_projection() -> dict[str, str]:
    raw = os.environ.get(HIL_INTR_CONFIG_ENV, "").strip()
    path = Path(raw).expanduser().resolve() if raw else HIL_INTR_CONFIG_DEFAULT.expanduser().resolve()
    disabled = {"STEGVERSE_HIL_INTR_ENABLED": "false", "STEGVERSE_HIL_INTR_UPSTREAM": ""}
    if not path.is_file():
        return disabled
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return disabled
    if not isinstance(value, dict):
        return disabled
    expected = {
        "schema": "stegverse.hil-intr-route-config/v1",
        "public_origin": "https://stegverse.org",
        "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "g18_completion_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_CONFIG_ONLY",
    }
    if any(value.get(k) != v for k, v in expected.items()):
        return disabled
    loopback = str(value.get("loopback_url") or "").rstrip("/")
    if not loopback.startswith("http://127.0.0.1:"):
        return disabled
    try:
        port = int(loopback.rsplit(":", 1)[1])
    except Exception:
        return disabled
    if port < 1024 or port > 65535:
        return disabled
    return {
        "STEGVERSE_HIL_INTR_ENABLED": "true",
        "STEGVERSE_HIL_INTR_UPSTREAM": loopback + "/intr/materialization",
    }

NAMED_REPOSITORY_ROOT_BINDINGS = {
    "STEGVERSE_HEALER_ROOT": "StegVerse-Labs/StegVerse-Healer",
    "STEGVERSE_LLM_ADAPTER_ROOT": "StegVerse-org/LLM-adapter",
    "STEGVERSE_TVC_ROOT": "StegVerse-Labs/TVC",
    "STEGVERSE_TV_ROOT": "StegVerse-Labs/TV",
    "STEGVERSE_STEGOS_ROOT": "StegVerse-Labs/StegOS",
    "STEGVERSE_SITE_ROOT": "StegVerse-Labs/Site",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": "StegVerse-002/micro-node-runtime",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": "master-records/orchestration",
}


def merge_named_repository_roots(roots: dict[str, str]) -> dict[str, str]:
    merged = dict(roots)
    for env_name, repository in NAMED_REPOSITORY_ROOT_BINDINGS.items():
        raw = str(os.environ.get(env_name) or "").strip()
        if not raw:
            continue
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            merged.setdefault(repository, str(path))
    return merged


def build_healer_child_env(targets: Path, roots_json: str) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "RUN_SCOPE": "all",
        "DISPATCH_MODE": "schedule",
        "TARGETS_FILE": str(targets),
        "STEGVERSE_REPO_ROOTS_JSON": roots_json,
    }
    env.update(evaluator_gateway_projection())
    env.update(sv002_observation_gateway_projection())
    env.update(hil_intr_gateway_projection())
    return env


def _response(state: str, transition: str, checkpoint: str, blocker: dict | None, epoch: int) -> dict:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "HEALER_SOVEREIGN_SCHEDULER_RECHECK",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "healer_sovereign_scheduler",
        },
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid invocation: {exc}", file=sys.stderr)
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 4
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    allowed = set(execution.get("allowed_paths") or [])
    if "healer_sovereign_scheduling" not in required:
        return 6
    if "receipts/healer-sovereign-scheduler/**" not in allowed:
        return 7

    forbidden = [name for name in ("HEALER_GH_TOKEN", "GITHUB_TOKEN", "GH_TOKEN", "HEALER_PAT", "GH_STEGVERSE_AI_TOKEN") if os.getenv(name)]
    healer_root, healer_root_source = discover_healer_root(os.getenv("STEGVERSE_HEALER_ROOT", ""))
    repo_roots, repo_roots_source = discover_repo_roots(os.getenv("STEGVERSE_REPO_ROOTS_JSON", ""))
    repo_roots = merge_named_repository_roots(repo_roots)
    roots_json = json.dumps(repo_roots, sort_keys=True, separators=(",", ":")) if repo_roots else ""
    blocker = None
    child_receipt: dict = {}
    state = "BLOCKED"
    transition = "HEALER_SOVEREIGN_SCHEDULER_BLOCKED"

    if forbidden:
        blocker = {
            "dependency_class": "AUTHORITY_CONFLICT",
            "problem_statement": "Forbidden GitHub credential environment is present in the sovereign Healer worker.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "REMOVE_GITHUB_CREDENTIAL_ENVIRONMENT",
            "forbidden_variables": sorted(forbidden),
        }
    elif healer_root is None:
        blocker = {
            "dependency_class": "LOCAL_RESOURCE",
            "problem_statement": "A unique complete local StegVerse-Healer root was not discovered.",
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "MATERIALIZE_UNIQUE_LOCAL_STEGVERSE_HEALER_ROOT",
            "discovery_state": healer_root_source,
        }
    elif not roots_json:
        blocker = {
            "dependency_class": "LOCAL_RESOURCE",
            "problem_statement": "No usable local repository-root map was discovered.",
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "MATERIALIZE_LOCAL_REPOSITORY_ROOTS_OR_SUPPLY_NONSECRET_MAP",
            "discovery_state": repo_roots_source,
        }
    else:
        entry = healer_root / "app" / "dispatch_orchestrators.py"
        targets = healer_root / "data" / "orchestrator_targets.json"
        if not healer_root.is_dir() or not entry.is_file() or not targets.is_file():
            blocker = {
                "dependency_class": "LOCAL_RESOURCE",
                "problem_statement": "Declared StegVerse-Healer root is incomplete.",
                "solution_required": True,
                "may_remain_blocked": True,
                "next_solution_action": "MATERIALIZE_COMPLETE_STEGVERSE_HEALER_TREE",
            }
        else:
            env = build_healer_child_env(targets, roots_json)
            proc = subprocess.run(
                [sys.executable, str(entry)],
                cwd=healer_root,
                env=env,
                text=True,
                capture_output=True,
                timeout=240,
                check=False,
            )
            try:
                child_receipt = json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception:
                child_receipt = {
                    "state": "FAILED",
                    "error": "INVALID_HEALER_CHILD_RECEIPT",
                    "stdout_tail": proc.stdout[-4000:],
                    "stderr_tail": proc.stderr[-4000:],
                }
            child_state = child_receipt.get("state")
            if proc.returncode == 0 and child_state == "COMPLETE":
                state = "COMPLETED"
                transition = "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"
            elif child_state in {"BLOCKED", "REVIEW_REQUIRED"}:
                state = "BLOCKED"
                transition = "HEALER_SOVEREIGN_SCHEDULER_BLOCKED"
                blocker = {
                    "dependency_class": "INTERNAL_CAPABILITY",
                    "problem_statement": "One or more due Healer targets lack a completed sovereign local handler.",
                    "solution_required": True,
                    "may_remain_blocked": True,
                    "next_solution_action": "COMPLETE_BLOCKED_HEALER_TARGET_ADAPTERS",
                }
            else:
                state = "FAILED"
                transition = "HEALER_SOVEREIGN_SCHEDULER_FAILED"
                blocker = {
                    "dependency_class": "IMPLEMENTATION",
                    "problem_statement": "Sovereign Healer child execution failed.",
                    "solution_required": True,
                    "may_remain_blocked": False,
                    "next_solution_action": "REPAIR_HEALER_SOVEREIGN_SCHEDULER",
                }

    receipt = {
        "schema": "stegverse.healer.sovereign_scheduler_worker_receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "state": state,
        "transition_id": transition,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "github_actions_production_role": False,
        "child_receipt": child_receipt,
        "healer_root": str(healer_root) if healer_root is not None else None,
        "healer_root_source": healer_root_source,
        "repository_root_count": len(repo_roots),
        "repository_roots_source": repo_roots_source,
        "blocker": blocker,
        "authority_effect": "BOUNDED_LOCAL_SCHEDULER_EXECUTION_ONLY",
    }
    rel = f"receipts/healer-sovereign-scheduler/{EXPECTED_TASK}.json"
    atomic_write(ROOT / rel, receipt)
    json.dump(_response(state, transition, rel, blocker, epoch), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
