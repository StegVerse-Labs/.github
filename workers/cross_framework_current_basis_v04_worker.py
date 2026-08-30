#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001"
CAPABILITY = "cross_framework_current_basis_v04_execution"
HANDOFF_PATH = ROOT / "handoffs" / f"{TASK_ID}.json"
RECEIPT_PATH = ROOT / "receipts" / "cross-framework-current-basis-v04" / f"{TASK_ID}.json"
RESULT_ROOT_REL = Path("receipts/cross-framework-current-basis-v04/result")
CUSTODY_DB_REL = Path("receipts/cross-framework-current-basis-v04/master-records.db")

FROZEN_SHA256 = "07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f"
FROZEN_BLOB = "59d818a15fc7be732c97dae7d2174d8cfe9a7bab"
REQUIRED_SDK_ANCESTOR = "28f5f5646f2f44f45e66a50c4f0ee0db31ed1012"
REQUIRED_STEGCORE_ANCESTOR = "057d1d33c553829844bdaa8d65093437698d5c27"
REQUIRED_CORE_LITE_ANCESTOR = "72bdb0f110031ccc2cd98b8ebb7c22b1ab7326f8"
REQUIRED_MASTER_RECORDS_ANCESTOR = "03312236c115bc814024d700810391340648601f"

HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "WALLET_PRIVATE_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def _atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    os.replace(temp, path)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=False, timeout=20,
    )


def _source_ok(root: Path, ancestor: str, required_files: tuple[str, ...]) -> dict[str, Any]:
    row: dict[str, Any] = {"path": str(root), "present": False, "selected": False}
    if not (root / ".git").is_dir():
        return row
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    ancestor_check = _git(root, "merge-base", "--is-ancestor", ancestor, "HEAD")
    files_ok = all((root / rel).is_file() for rel in required_files)
    row.update({
        "present": True,
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "clean_worktree": status.returncode == 0 and not status.stdout.strip(),
        "required_ancestor": ancestor,
        "required_ancestor_present": ancestor_check.returncode == 0,
        "required_files_present": files_ok,
    })
    row["selected"] = bool(
        row["head"] and row["clean_worktree"] and row["required_ancestor_present"] and files_ok
    )
    return row


def _candidate_roots(env_name: str, org: str, repo: str) -> list[Path]:
    values: list[Path] = []
    raw = os.environ.get(env_name, "").strip()
    if raw:
        values.append(Path(raw).expanduser())
    values.extend([
        Path.home() / ".stegverse" / "repos" / org / repo,
        Path("/var/lib/stegverse/source") / org / repo,
        Path("/srv/stegverse/repos") / org / repo,
        Path("/opt/stegverse/repos") / org / repo,
    ])
    return values


def _locate(env_name: str, org: str, repo: str, ancestor: str, files: tuple[str, ...]) -> tuple[Path | None, list[dict[str, Any]]]:
    observed: list[dict[str, Any]] = []
    for candidate in _candidate_roots(env_name, org, repo):
        row = _source_ok(candidate, ancestor, files)
        if row["present"]:
            observed.append(row)
        if row["selected"]:
            return candidate.resolve(), observed
    return None, observed


def _parse_last_json(stdout: str) -> dict[str, Any] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        whole = json.loads(text)
        if isinstance(whole, dict):
            return whole
    except Exception:
        pass
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for start in range(len(lines)):
        try:
            value = json.loads("\n".join(lines[start:]))
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if task.get("task_id") != TASK_ID:
        return 4
    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 5
    if "receipts/cross-framework-current-basis-v04/**" not in set(execution.get("allowed_paths") or []):
        return 6

    hosted = [name for name in HOSTED_ENV if _truthy(os.environ.get(name))]
    observations: dict[str, Any] = {}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if hosted:
        state = "BLOCKED"
        result: dict[str, Any] = {
            "reason": "HOSTED_RUNTIME_PROHIBITED",
            "hosted_markers": hosted,
            "runtime_execution_attempted": False,
        }
    else:
        sdk, observations["sdk"] = _locate(
            "STEGVERSE_SDK_SOURCE_ROOT", "StegVerse-org", "StegVerse-SDK",
            REQUIRED_SDK_ANCESTOR,
            (
                "scripts/run_cross_framework_current_basis_v04.py",
                "inspection/examples/cross-framework-current-basis-request.draft.json",
                "stegverse/sovereign_validation_runtime.py",
                "stegverse/current_basis.py",
            ),
        )
        core, observations["stegcore"] = _locate(
            "STEGVERSE_STEGCORE_SOURCE_ROOT", "StegVerse-Labs", "StegCore",
            REQUIRED_STEGCORE_ANCESTOR,
            ("src/stegcore/current_basis.py", "src/stegcore/steggate.py"),
        )
        core_lite, observations["core_lite"] = _locate(
            "STEGVERSE_CORE_LITE_SOURCE_ROOT", "Data-Continuation", "core-lite",
            REQUIRED_CORE_LITE_ANCESTOR,
            ("core_lite/transaction_route.py",),
        )
        master_records, observations["master_records"] = _locate(
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "master-records", "orchestration",
            REQUIRED_MASTER_RECORDS_ANCESTOR,
            ("services/manifest_receipt_custody.py",),
        )
        if not all((sdk, core, core_lite, master_records)):
            state = "BLOCKED"
            result = {
                "reason": "REQUIRED_ALREADY_LOCAL_CANONICAL_SOURCE_NOT_READY",
                "observed_sources": observations,
                "network_source_fetch_performed": False,
                "source_mutation_performed": False,
                "runtime_execution_attempted": False,
            }
        else:
            assert sdk and core and core_lite and master_records
            run_dir = ROOT / RESULT_ROOT_REL
            custody_db = ROOT / CUSTODY_DB_REL
            py_path = os.pathsep.join([
                str(sdk),
                str(core / "src"),
                str(core_lite),
                str(master_records),
            ])
            env = {
                name: os.environ[name]
                for name in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "XDG_STATE_HOME", "XDG_CONFIG_HOME")
                if os.environ.get(name)
            }
            for name in FORBIDDEN_ENV:
                env.pop(name, None)
            env["PYTHONPATH"] = py_path
            env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
            env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"

            command = [
                sys.executable,
                str(sdk / "scripts/run_cross_framework_current_basis_v04.py"),
                "--manifest",
                str(sdk / "inspection/examples/cross-framework-current-basis-request.draft.json"),
                "--custody-db",
                str(custody_db),
                "--run-dir",
                str(run_dir),
                "--host-identity",
                "stegverse-sovereign-resident",
            ]
            completed = subprocess.run(
                command,
                cwd=sdk,
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=900,
            )
            run_complete_path = run_dir / "RUN_COMPLETE.json"
            run_complete = _load(run_complete_path) if run_complete_path.is_file() else None
            terminal = bool(
                completed.returncode == 0
                and isinstance(run_complete, dict)
                and run_complete.get("status") == "COMPLETE"
                and run_complete.get("manifest_sha256") == FROZEN_SHA256
                and run_complete.get("manifest_git_blob_sha1") == FROZEN_BLOB
                and run_complete.get("independent_execution_complete") is True
                and run_complete.get("s1_observed") is True
                and run_complete.get("transition_receipt_bound") is True
                and run_complete.get("custody_recorded") is True
                and run_complete.get("replay_recorded") is True
                and run_complete.get("reconstruction_recorded") is True
                and run_complete.get("authority_granted") is False
                and run_complete.get("external_side_effect") is False
            )
            state = "COMPLETED" if terminal else "BLOCKED"
            result = {
                "reason": "CROSS_FRAMEWORK_CURRENT_BASIS_V04_COMPLETE" if terminal else "CURRENT_BASIS_V04_RUN_NOT_TERMINAL",
                "runtime_execution_attempted": True,
                "command": command,
                "returncode": completed.returncode,
                "run_complete": run_complete,
                "run_complete_ref": RESULT_ROOT_REL.as_posix() + "/RUN_COMPLETE.json",
                "stdout_tail": (completed.stdout or "")[-6000:],
                "stderr_tail": (completed.stderr or "")[-6000:],
                "observed_sources": observations,
                "network_source_fetch_performed": False,
                "source_mutation_performed": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "external_side_effect": False,
            }

    receipt = {
        "schema": "stegverse.cross-framework-current-basis-v04-worker-receipt/v1",
        "task_id": TASK_ID,
        "generated_at": now,
        "state": state,
        "result": result,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "authority_effect": "REGISTERED_SOVEREIGN_TEST_EXECUTION_ONLY",
    }
    _atomic(RECEIPT_PATH, receipt)

    blocker = None if state == "COMPLETED" else {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": result["reason"],
        "solution_required": True,
        "may_remain_blocked": True,
        "next_solution_action": "RECHECK_ALREADY_LOCAL_CANONICAL_SOURCES_AND_RETRY_EXACT_FROZEN_V04_RUN",
        "machine_observable_release_condition": "RUN_COMPLETE.json proves exact frozen v0.4 S1 observation, transition receipt, custody, replay, and reconstruction",
    }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": f"CROSS_FRAMEWORK_CURRENT_BASIS_V04_{state}",
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "CROSS_FRAMEWORK_CURRENT_BASIS_V04_RECHECK",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "recheck_policy": None if state == "COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref": "receipts/cross-framework-current-basis-v04/SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001.json",
        "evidence_refs": [
            "docs/CROSS_FRAMEWORK_CURRENT_BASIS_V04_RESIDENT_RUN_MIRROR_HANDOFF.md",
            "receipts/cross-framework-current-basis-v04/SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001.json",
            RESULT_ROOT_REL.as_posix() + "/RUN_COMPLETE.json",
            "StegVerse-org/StegVerse-SDK#99",
            "StegVerse-Labs/StegCore#162",
        ],
        "blocker": blocker,
        "cost_observation": {
            "task_control_evaluations": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": CAPABILITY,
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
