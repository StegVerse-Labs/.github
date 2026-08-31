#!/usr/bin/env python3
"""Execute the already-admitted TV/TVC resident proof without receiving credential bytes."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-TV-TVC-RESIDENT-PROOF-001"
TV_SHA = "e0d102a8c187c059754eced9ac017fdb056a0222"
TVC_MIN_SHA = "e4bef703b4d6ccad858459ec502637c598948c42"
RECEIPT_ROOT = (ROOT / "receipts" / "tv-tvc-resident-proof").resolve()
ALLOWED_CAPABILITIES = {
    "runtime_observation",
    "bounded_process_execution",
    "durable_state_reconstruction",
    "tv_tvc_resident_operational_proof_activation",
}
ALLOWED_PATHS = ["receipts/tv-tvc-resident-proof/**"]
ALLOWED_SERVICES = ["stegtvc-tv-artifact-exchange@.service"]
TV_REQUIRED = [Path("scripts/tv_run_resident_operational_proof.py"), Path("docs/TV_OPERATIONAL_PROOF_SCHEMA.json")]
TVC_REQUIRED = [Path("tools/task_dispatcher.py"), Path("tv_resident_operational_proof_task.py"), Path("scripts/activate_tv_resident_operational_proof.py")]


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def _response(state: str, transition_id: str, checkpoint: str, *, next_epoch: int | None = None) -> dict[str, Any]:
    terminal = state == "COMPLETED"
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition_id,
        "transition_sequence": 1,
        "expected_next_transition": None if terminal else "TV_TVC_RESIDENT_PROOF_RECHECK",
        "expected_next_earliest_epoch": None if terminal else next_epoch,
        "expected_next_latest_epoch": None if terminal else next_epoch,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "tv_tvc_resident_operational_proof",
        },
    }


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _git_head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.strip().lower()


def _clean_worktree(root: Path) -> bool:
    return not _git(root, "status", "--porcelain").stdout.strip()


def _tvc_contains_required_source(root: Path) -> bool:
    return _git(root, "merge-base", "--is-ancestor", TVC_MIN_SHA, "HEAD", check=False).returncode == 0


def _canonical_candidates(repo_name: str, env_name: str) -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get(env_name, "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    home = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
    candidates.extend([
        home / ".stegverse" / "repos" / "StegVerse-Labs" / repo_name,
        Path("/var/lib/stegverse/source/StegVerse-Labs") / repo_name,
        Path("/srv/stegverse/repos/StegVerse-Labs") / repo_name,
        Path("/opt/stegverse/repos/StegVerse-Labs") / repo_name,
    ])
    result: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        marker = str(resolved)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(resolved)
    return result


def _locate_local_source(repo_name: str, env_name: str, required: list[Path], *, exact_head: str | None = None, required_ancestor: str | None = None) -> tuple[Path | None, list[dict[str, Any]]]:
    observed: list[dict[str, Any]] = []
    for root in _canonical_candidates(repo_name, env_name):
        record: dict[str, Any] = {"root": str(root), "present": root.is_dir()}
        if not root.is_dir():
            observed.append(record)
            continue
        missing = [str(path) for path in required if not (root / path).is_file()]
        if missing:
            record["missing_required"] = missing
            observed.append(record)
            continue
        if not (root / ".git").is_dir():
            record["git_repository"] = False
            observed.append(record)
            continue
        try:
            head = _git_head(root)
            clean = _clean_worktree(root)
        except Exception as exc:
            record["git_error_type"] = type(exc).__name__
            observed.append(record)
            continue
        record.update({"head": head, "clean_worktree": clean})
        if not clean:
            observed.append(record)
            continue
        if exact_head is not None and head != exact_head:
            record["exact_head_match"] = False
            observed.append(record)
            continue
        if required_ancestor is not None:
            ancestor_ok = _git(root, "merge-base", "--is-ancestor", required_ancestor, "HEAD", check=False).returncode == 0
            record["required_ancestor_present"] = ancestor_ok
            if not ancestor_ok:
                observed.append(record)
                continue
        record["selected"] = True
        observed.append(record)
        return root, observed
    return None, observed


def _portable_manifest() -> tuple[Path | None, dict[str, Any] | None]:
    raw = os.environ.get("STEGVERSE_RESIDENT_SOURCE_MANIFEST", "").strip()
    if not raw:
        return None, None
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        return path, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return path, None
    return (path, value) if isinstance(value, dict) else (path, None)


def _portable_source(repo_name: str, env_name: str, required: list[Path]) -> tuple[Path | None, str | None]:
    manifest_path, manifest = _portable_manifest()
    raw_root = os.environ.get(env_name, "").strip()
    if manifest_path is None or manifest is None or not raw_root:
        return None, "PORTABLE_SOURCE_MANIFEST_OR_ROOT_ABSENT"
    if not (
        manifest.get("schema") == "stegverse.sovereign-control-plane-bundle/v1"
        and manifest.get("network_fetch_required") is False
        and manifest.get("credential_authority") == "TV/TVC"
        and manifest.get("github_token_runtime_authority") == "NONE"
        and manifest.get("bundle_grants_authority") is False
    ):
        return None, "PORTABLE_SOURCE_MANIFEST_INVARIANT_INVALID"
    proof = (manifest.get("vendor_source_proofs") or {}).get(repo_name)
    if not isinstance(proof, dict) or proof.get("state") != "VERIFIED_LOCAL_GIT_SOURCE":
        return None, "PORTABLE_SOURCE_PROOF_NOT_VERIFIED"
    if proof.get("repository") != f"StegVerse-Labs/{repo_name}" or proof.get("materialized_subpath") != f"vendor/{repo_name}":
        return None, "PORTABLE_SOURCE_IDENTITY_INVALID"
    root = Path(raw_root).expanduser().resolve()
    if root != (manifest_path.parent / "vendor" / repo_name).resolve():
        return None, "PORTABLE_SOURCE_ROOT_BINDING_INVALID"
    if repo_name == "TV" and not (proof.get("head") == TV_SHA and proof.get("exact_head_verified") is True and proof.get("clean_worktree_at_packaging") is True):
        return None, "PORTABLE_TV_EXACT_SOURCE_IDENTITY_INVALID"
    if repo_name == "TVC" and not (proof.get("resident_proof_min_sha_present") is True and TVC_MIN_SHA in set(proof.get("verified_ancestors") or [])):
        return None, "PORTABLE_TVC_REQUIRED_ANCESTOR_NOT_PROVEN"
    declared = {str(e.get("path")): e for e in manifest.get("files", []) if isinstance(e, dict) and isinstance(e.get("path"), str)}
    for rel in required:
        path = root / rel
        entry = declared.get(f"vendor/{repo_name}/{rel.as_posix()}")
        if not path.is_file() or not isinstance(entry, dict):
            return None, "PORTABLE_REQUIRED_SOURCE_MISSING"
        data = path.read_bytes()
        if len(data) != entry.get("size") or hashlib.sha256(data).hexdigest() != entry.get("sha256"):
            return None, "PORTABLE_SOURCE_DIGEST_MISMATCH"
    return root, "VERIFIED_PORTABLE_BUNDLE_PROOF"

def _parse_dispatcher(stdout: str) -> dict[str, Any]:
    value = json.loads(stdout)
    if not isinstance(value, dict):
        raise ValueError("dispatcher response must be an object")
    return value


def _hosted_runtime_observed() -> bool:
    flags = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES")
    return any(str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes"} for name in flags)


def _blocked_receipt(*, epoch: int, claim_id: str, fence: int, worker_id: str | None, worker_instance_id: str | None, reason: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": "stegverse.tv-tvc-resident-proof-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "state": "BLOCKED",
        "reason": reason,
        "evidence": evidence or {},
        "credential_authority": "TV/TVC",
        "credential_value_exposed": False,
        "consumer_secret_received": False,
        "github_token_runtime_authority": False,
        "g18_authority_reused": False,
        "source_fetch_performed": False,
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid invocation: {exc}", file=sys.stderr)
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        print("unsupported invocation schema", file=sys.stderr)
        return 3

    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or epoch < 0 or task.get("task_id") != TASK_ID:
        print("invocation outside admitted TV/TVC task", file=sys.stderr)
        return 4
    execution = handoff.get("execution") or {}
    if set(execution.get("required_capabilities") or []) != ALLOWED_CAPABILITIES:
        print("required capability mismatch", file=sys.stderr)
        return 5
    if execution.get("allowed_paths") != ALLOWED_PATHS or execution.get("allowed_services") != ALLOWED_SERVICES:
        print("execution boundary mismatch", file=sys.stderr)
        return 6
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC" or authority.get("g18_authority_inherited") is not False:
        print("authority boundary mismatch", file=sys.stderr)
        return 7

    claim_id = task.get("claim_id")
    worker_id = task.get("worker_id")
    worker_instance_id = task.get("worker_instance_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        print("fresh fenced claim required", file=sys.stderr)
        return 8

    checkpoint = f"receipts/tv-tvc-resident-proof/{TASK_ID}.json"
    receipt_path = (ROOT / checkpoint).resolve()
    if RECEIPT_ROOT not in receipt_path.parents:
        print("receipt path escaped admitted namespace", file=sys.stderr)
        return 9
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        if prior.get("claim_id") != claim_id or prior.get("fencing_token") != fence:
            print("existing receipt belongs to a different claim/fence", file=sys.stderr)
            return 10
        if prior.get("state") == "COMPLETED":
            json.dump(_response("COMPLETED", "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED", checkpoint), sys.stdout, sort_keys=True)
            sys.stdout.write("\n")
            return 0

    def block(reason: str, evidence: dict[str, Any] | None = None) -> int:
        receipt = _blocked_receipt(epoch=epoch, claim_id=claim_id, fence=fence, worker_id=worker_id, worker_instance_id=worker_instance_id, reason=reason, evidence=evidence)
        atomic_write(receipt_path, receipt)
        json.dump(_response("BLOCKED", "TV_TVC_RESIDENT_PROOF_BLOCKED", checkpoint, next_epoch=epoch + 1), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if _hosted_runtime_observed():
        return block("HOSTED_RUNTIME_NOT_AUTHORIZED")

    tv_root, tv_observed = _locate_local_source("TV", "STEGVERSE_TV_ROOT", TV_REQUIRED, exact_head=TV_SHA)
    tvc_root, tvc_observed = _locate_local_source("TVC", "STEGVERSE_TVC_ROOT", TVC_REQUIRED, required_ancestor=TVC_MIN_SHA)
    if tv_root is None or tvc_root is None:
        return block(
            "LOCAL_TV_TVC_SOURCE_NOT_MATERIALIZED",
            {
                "tv_selected": str(tv_root) if tv_root else None,
                "tvc_selected": str(tvc_root) if tvc_root else None,
                "tv_candidates": tv_observed,
                "tvc_candidates": tvc_observed,
                "network_lookup_performed": False,
            },
        )

    # Recheck identities at execution time after discovery. No fetch/pull/update is performed.
    try:
        tv_head = _git_head(tv_root)
    except Exception as exc:
        return block("LOCAL_TV_GIT_IDENTITY_UNAVAILABLE", {"error_type": type(exc).__name__})
    if tv_head != TV_SHA:
        return block("TV_SOURCE_SHA_MISMATCH", {"expected": TV_SHA, "observed": tv_head})
    if not _tvc_contains_required_source(tvc_root):
        return block("TVC_ROOTLESS_ACTIVATION_SOURCE_NOT_PRESENT", {"required_ancestor": TVC_MIN_SHA})

    child_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "STEGVERSE_TV_SERVICE_MANAGER": "user",
        "STEGTV_TV_CREDENTIAL_MIGRATION_ACTIVATION_AUTHORITY": "TV/TVC",
        "STEGTV_TV_REPO_ROOT": str(tv_root),
    }
    for name in ("XDG_STATE_HOME", "XDG_CONFIG_HOME"):
        value = os.environ.get(name)
        if value:
            child_env[name] = value

    dispatcher = [sys.executable, str(tvc_root / "tools/task_dispatcher.py")]
    preflight = subprocess.run(dispatcher + ["tvc.tv_resident_operational_proof.preflight"], cwd=str(tvc_root), env=child_env, capture_output=True, text=True)
    try:
        preflight_json = _parse_dispatcher(preflight.stdout)
    except Exception as exc:
        return block("TVC_PREFLIGHT_RESPONSE_INVALID", {"returncode": preflight.returncode, "error_type": type(exc).__name__})
    if preflight.returncode == 2 or preflight_json.get("status") == "blocked":
        result = preflight_json.get("result") or {}
        return block("TVC_PREFLIGHT_BLOCKED", {"reason": result.get("reason")})
    if preflight.returncode != 0 or preflight_json.get("status") != "ok":
        return block("TVC_PREFLIGHT_FAILED", {"returncode": preflight.returncode})
    if (preflight_json.get("result") or {}).get("state") != "READY_FOR_TV_TVC_RESIDENT_ACTIVATION":
        return block("TVC_PREFLIGHT_NOT_READY")

    activation = subprocess.run(dispatcher + ["tvc.tv_resident_operational_proof.activate"], cwd=str(tvc_root), env=child_env, capture_output=True, text=True)
    try:
        activation_json = _parse_dispatcher(activation.stdout)
    except Exception as exc:
        return block("TVC_ACTIVATION_RESPONSE_INVALID", {"returncode": activation.returncode, "error_type": type(exc).__name__})
    if activation.returncode == 2 or activation_json.get("status") == "blocked":
        result = activation_json.get("result") or {}
        detail = result.get("evidence") or {}
        activation_result = detail.get("activation_result") or {}
        return block("TVC_ACTIVATION_BLOCKED", {"reason": activation_result.get("reason") or result.get("reason")})
    result = activation_json.get("result") or {}
    safe = (
        activation.returncode == 0
        and activation_json.get("status") == "ok"
        and result.get("state") == "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED"
        and result.get("runtime_execution_observed") is True
        and result.get("credential_value_exposed") is False
        and result.get("consumer_secret_received") is False
        and isinstance(result.get("receipt_path"), str)
        and bool(result.get("receipt_path"))
        and isinstance(result.get("proof_sha256"), str)
        and len(result.get("proof_sha256")) == 64
    )
    if not safe:
        return block("TVC_ACTIVATION_COMPLETION_NOT_PROVEN", {"returncode": activation.returncode, "dispatcher_status": activation_json.get("status"), "result_state": result.get("state")})

    receipt = {
        "schema": "stegverse.tv-tvc-resident-proof-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "state": "COMPLETED",
        "transition_id": "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED",
        "tv_source_root": str(tv_root),
        "tvc_source_root": str(tvc_root),
        "tv_source_sha": TV_SHA,
        "tvc_required_source_ancestor": TVC_MIN_SHA,
        "service_manager": "systemd-user",
        "runtime_receipt_path": result["receipt_path"],
        "proof_sha256": result["proof_sha256"],
        "runtime_execution_observed": True,
        "credential_authority": "TV/TVC",
        "credential_value_exposed": False,
        "consumer_secret_received": False,
        "github_token_runtime_authority": False,
        "g18_authority_reused": False,
        "source_fetch_performed": False,
    }
    atomic_write(receipt_path, receipt)
    json.dump(_response("COMPLETED", "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED", checkpoint), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
