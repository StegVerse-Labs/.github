#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd().resolve()
REGISTRY = ROOT / "control" / "repo-heartbeat-federation.json"
MANIFEST_DIR = ROOT / "federation" / "repo-heartbeats"
RECEIPT_ROOT = (ROOT / "receipts" / "repo-heartbeat-federation").resolve()
EXPECTED_TASK = "SHWP-REPO-HEARTBEAT-FEDERATION-001"
CURRENT_AUTHORITY = "TV/TVC"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def canonical_hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_manifest(manifest: dict, expected: dict, now: datetime) -> tuple[bool, list[str], bool]:
    errors: list[str] = []
    if manifest.get("schema") != "stegverse.repo-heartbeat-manifest/v0.1":
        errors.append("SCHEMA")
    for key, expected_value in (("repo_id", expected["repo_id"]), ("org", expected["organization"]), ("repository", expected["repository"]), ("participant_class", expected["participant_class"])):
        if manifest.get(key) != expected_value:
            errors.append(f"IDENTITY_{key.upper()}")
    if not isinstance(manifest.get("sequence"), int) or manifest.get("sequence", -1) < 0:
        errors.append("SEQUENCE")
    emitted = parse_time(manifest.get("emitted_at"))
    fresh_until = parse_time(manifest.get("fresh_until"))
    if emitted is None or fresh_until is None or fresh_until <= emitted:
        errors.append("FRESHNESS_WINDOW")
    authority = manifest.get("authority") or {}
    if authority.get("credential_authority") != CURRENT_AUTHORITY:
        errors.append("CREDENTIAL_AUTHORITY")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        errors.append("HEARTBEAT_AUTHORITY_ESCALATION")
    if authority.get("github_token_required") is not False:
        errors.append("GITHUB_TOKEN_REQUIRED")
    if manifest.get("status") not in {"READY", "DEGRADED", "BLOCKED", "FAILED", "RETIRED"}:
        errors.append("STATUS")
    if expected["participant_class"] in {"CONTROL", "RUNTIME", "SERVICE"}:
        sha = manifest.get("commit_sha")
        if not isinstance(sha, str) or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
            errors.append("COMMIT_SHA")
        if not manifest.get("runtime_id"):
            errors.append("RUNTIME_ID")
    stale = fresh_until is None or fresh_until <= now
    return not errors, errors, stale


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
    if "repo_heartbeat_federation_reconciliation" not in set(execution.get("required_capabilities") or []):
        return 6
    if "receipts/repo-heartbeat-federation/**" not in set(execution.get("allowed_paths") or []):
        return 7

    registry = load(REGISTRY)
    if registry.get("schema") != "stegverse.repo-heartbeat-federation/v0.1":
        return 8
    expected_rows = registry.get("required_participants") or []
    if not expected_rows:
        return 9

    now = datetime.now(timezone.utc)
    manifests: dict[str, dict] = {}
    duplicates: set[str] = set()
    if MANIFEST_DIR.is_dir():
        for path in sorted(MANIFEST_DIR.glob("*.json")):
            try:
                value = load(path)
            except Exception:
                continue
            repo_id = value.get("repo_id")
            if not isinstance(repo_id, str):
                continue
            if repo_id in manifests:
                duplicates.add(repo_id)
            else:
                manifests[repo_id] = value

    rows: list[dict] = []
    by_id: dict[str, dict] = {}
    for expected in expected_rows:
        repo_id = expected["repo_id"]
        manifest = manifests.get(repo_id)
        row = {
            "repo_id": repo_id,
            "organization": expected["organization"],
            "repository": expected["repository"],
            "participant_class": expected["participant_class"],
            "required": bool(expected.get("required")),
            "manifest_present": manifest is not None,
            "manifest_valid": False,
            "fresh": False,
            "status": "MISSING",
            "errors": [],
            "dependency_losses": [],
            "sequence": None,
            "commit_sha": None,
            "ref": None,
            "release_tag": None,
            "runtime_id": None,
            "handoff_hash": None,
            "fresh_until": None,
        }
        if repo_id in duplicates:
            row["status"] = "FAILED"
            row["errors"].append("DUPLICATE_MANIFEST")
        elif manifest is not None:
            valid, errors, stale = validate_manifest(manifest, expected, now)
            row["manifest_valid"] = valid
            row["fresh"] = valid and not stale
            row["errors"] = errors + (["STALE"] if stale else [])
            row["status"] = manifest.get("status") if valid and not stale else ("STALE" if valid else "FAILED")
            for key in ("sequence", "commit_sha", "ref", "release_tag", "runtime_id", "handoff_hash", "fresh_until"):
                row[key] = manifest.get(key)
        rows.append(row)
        by_id[repo_id] = row

    for expected in expected_rows:
        repo_id = expected["repo_id"]
        manifest = manifests.get(repo_id) or {}
        row = by_id[repo_id]
        for dep in manifest.get("dependencies") or []:
            dep_id = dep.get("repo_id")
            if dep.get("required") is not True or dep_id not in by_id:
                continue
            dep_row = by_id[dep_id]
            if not dep_row["manifest_valid"] or not dep_row["fresh"] or dep_row["status"] in {"FAILED", "BLOCKED", "RETIRED", "MISSING", "STALE"}:
                row["dependency_losses"].append(dep_id)
        if row["dependency_losses"] and row["status"] not in {"FAILED", "MISSING", "STALE"}:
            row["status"] = "BLOCKED"
            row["errors"].append("REQUIRED_DEPENDENCY_LOSS")

    missing = sorted(row["repo_id"] for row in rows if row["required"] and not row["manifest_present"])
    stale = sorted(row["repo_id"] for row in rows if row["required"] and row["status"] == "STALE")
    failed = sorted(row["repo_id"] for row in rows if row["required"] and row["status"] in {"FAILED", "BLOCKED", "RETIRED"})
    healthy = sorted(row["repo_id"] for row in rows if row["manifest_valid"] and row["fresh"] and row["status"] in {"READY", "DEGRADED"} and not row["dependency_losses"])
    complete = not missing and not stale and not failed and len(healthy) == len([r for r in rows if r["required"]])

    topology = {
        "schema": "stegverse.repo-heartbeat-topology/v0.1",
        "heartbeat_epoch": epoch,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "participants": rows,
    }
    topology_hash = canonical_hash(topology)
    transition = "REPO_FEDERATION_COVERAGE_COMPLETE" if complete else "REPO_FEDERATION_COVERAGE_GAP"
    state = "COMPLETED" if complete else "BLOCKED"
    blocker = None if complete else {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": "One or more required repository heartbeat participants are missing, stale, invalid, failed, blocked, retired, or have lost a required dependency.",
        "solution_required": True,
        "may_remain_blocked": True,
        "workaround_candidates": [
            "Install the normalized repository heartbeat manifest adapter in missing critical repositories.",
            "Refresh stale manifests from the repository/runtime that owns the signal.",
            "Repair failed required dependencies and allow the central heartbeat to recompute topology."
        ],
        "next_solution_action": "ENROLL_OR_REFRESH_REQUIRED_REPO_HEARTBEAT_PARTICIPANTS"
    }
    receipt = {
        "schema": "stegverse.repo-heartbeat-federation-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "state": state,
        "required_count": len([r for r in rows if r["required"]]),
        "healthy_count": len(healthy),
        "missing": missing,
        "stale": stale,
        "failed_or_dependency_blocked": failed,
        "healthy": healthy,
        "topology": topology,
        "topology_sha256": topology_hash,
        "coverage_complete": complete,
        "fail_closed": True,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "authority_effect": "NONE_COVERAGE_EVIDENCE_ONLY",
        "blocker": blocker,
    }
    receipt_path = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if complete else "REPO_FEDERATION_COVERAGE_RECHECK",
        "expected_next_earliest_epoch": None if complete else epoch + 1,
        "expected_next_latest_epoch": None if complete else epoch + 1,
        "checkpoint_ref": f"receipts/repo-heartbeat-federation/{EXPECTED_TASK}.json",
        "evidence_refs": [
            "control/repo-heartbeat-federation.json",
            "schemas/repo-heartbeat-manifest.schema.json",
            f"receipts/repo-heartbeat-federation/{EXPECTED_TASK}.json"
        ],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "repo_heartbeat_federation"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
