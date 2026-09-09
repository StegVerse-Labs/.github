#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TRACKED_KEYS = {
    "profile_ref", "runtime_node_profile_id", "node_ref", "node_id", "genesis_hash",
    "source_device_hb_reference", "current_observed_hb_reference", "state_generation",
    "state_commitment", "transition_commitment", "prior_transition_commitment",
}


def canonical_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def git_head(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    completed = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    value = completed.stdout.strip().lower()
    return value if completed.returncode == 0 and len(value) == 40 else None


def new_run_id(now: datetime | None = None) -> str:
    at = now or datetime.now(timezone.utc)
    return "global-runtime-" + at.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]


def evidence_paths(profile: Mapping[str, Any]) -> list[Path]:
    binding = profile.get("execution_binding") or {}
    paths: list[Path] = []
    for key in ("receipt", "subject_receipt"):
        value = binding.get(key)
        if isinstance(value, str) and value.strip():
            paths.append(Path(value))
    return paths


def _collect_tracked(value: Any, found: dict[str, Any]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in TRACKED_KEYS and key not in found and isinstance(item, (str, int, float, bool)):
                found[key] = item
            _collect_tracked(item, found)
    elif isinstance(value, list):
        for item in value:
            _collect_tracked(item, found)


def snapshot_profile(runtime: Path, profile: Mapping[str, Any]) -> dict[str, Any]:
    refs = []
    merged: dict[str, Any] = {}
    for rel in evidence_paths(profile):
        path = runtime / rel
        row = {"path": str(rel), "present": path.is_file(), "sha256": canonical_sha256(path)}
        if path.is_file():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                tracked: dict[str, Any] = {}
                _collect_tracked(value, tracked)
                row["tracked"] = tracked
                for key, item in tracked.items():
                    merged.setdefault(key, item)
            except Exception as exc:
                row["parse_error"] = type(exc).__name__
        refs.append(row)
    return {
        "task_id": profile.get("task_id"),
        "profile_id": profile.get("profile_id"),
        "evidence_refs": refs,
        "tracked": merged,
    }


def freeze_context(source: Path, runtime: Path, profile_registry: Path, projection: Path, profiles: list[Mapping[str, Any]]) -> dict[str, Any]:
    started = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "schema": "stegverse.runtime-convergence-measurement-context/v1",
        "run_id": new_run_id(started),
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "source_git_head": git_head(source),
        "profile_registry_sha256": canonical_sha256(profile_registry),
        "projection_sha256": canonical_sha256(projection),
        "measurement_only": True,
        "same_run_remediation_allowed": False,
        "automatic_retry_after_first_failure": False,
        "historical_pass_distinct_from_current_run_pass": True,
        "baseline": [snapshot_profile(runtime, profile) for profile in profiles],
    }


def finish_context(context: Mapping[str, Any], runtime: Path, profiles: list[Mapping[str, Any]]) -> dict[str, Any]:
    completed = datetime.now(timezone.utc).replace(microsecond=0)
    result = dict(context)
    result["completed_at"] = completed.isoformat().replace("+00:00", "Z")
    result["after"] = [snapshot_profile(runtime, profile) for profile in profiles]
    return result
