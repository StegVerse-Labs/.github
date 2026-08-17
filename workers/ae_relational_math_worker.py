#!/usr/bin/env python3
"""Bounded StegVerse worker for the AE-AUTO-0011 relational-mathematics lane.

The worker never fetches source, accepts credentials, publishes, releases, tags,
or modifies another repository. It operates only on an already-materialized
Admissible-Existence/AE checkout and emits a local StegVerse receipt.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

GOAL_ID = "AE-AUTO-0011"
REPO_ID = "Admissible-Existence/AE"


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    configured = os.environ.get("STEGVERSE_AE_ROOT")
    if configured:
        roots.append(Path(configured).expanduser())
    home = Path.home()
    roots.extend([
        home / ".stegverse" / "workloads" / "Admissible-Existence" / "AE",
        home / "stegverse" / "Admissible-Existence" / "AE",
        Path("/srv/stegverse/Admissible-Existence/AE"),
        Path("/opt/stegverse/Admissible-Existence/AE"),
    ])
    seen: set[str] = set()
    result: list[Path] = []
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            result.append(root)
            seen.add(key)
    return result


def verify_root(root: Path) -> bool:
    required = [
        root / "AE_MIRROR_HANDOFF.md",
        root / "data" / "autonomous_goal_queue.json",
        root / "data" / "autonomous_standing.json",
        root / "data" / "autonomous_goal_seeds" / "AE-AUTO-0011.json",
        root / "tools" / "enqueue_state_manifold_relational_governance.py",
        root / "tools" / "check_state_manifold_relational_governance.py",
        root / "docs" / "STATE_MANIFOLD_RELATIONAL_GOVERNANCE_MATHEMATICS.md",
    ]
    return root.is_dir() and all(path.is_file() for path in required)


def run(root: Path, *args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, *args], cwd=root, text=True,
        capture_output=True, check=False, timeout=120,
        env={**os.environ, "PYTHONNOUSERSITE": "1"},
    )
    return {
        "argv": [sys.executable, *args],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def git_head(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            capture_output=True, check=False, timeout=10,
        )
        return completed.stdout.strip() if completed.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> int:
    root = next((path for path in candidate_roots() if verify_root(path)), None)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if root is None:
        receipt = {
            "schema": "stegverse.ae-relational-math-worker-receipt/v1",
            "goal_id": GOAL_ID,
            "repository": REPO_ID,
            "observed_at": now,
            "state": "BLOCKED",
            "reason": "AE_LOCAL_SOURCE_NOT_MATERIALIZED",
            "next_solution_action": "materialize the canonical Admissible-Existence/AE repository on an authorized StegVerse local workload path",
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_used": False,
        }
        print(json.dumps(receipt, sort_keys=True))
        return 2

    steps = [
        run(root, "tools/enqueue_state_manifold_relational_governance.py"),
        run(root, "tools/check_autonomous_goal_queue.py", "data/autonomous_goal_queue.json"),
        run(root, "tools/check_state_manifold_relational_governance.py", "data/state_manifold_relational_governance_cases.json"),
    ]
    success = all(step["returncode"] == 0 for step in steps)
    queue = json.loads((root / "data" / "autonomous_goal_queue.json").read_text(encoding="utf-8"))
    goal = next((item for item in queue.get("goals", []) if item.get("id") == GOAL_ID), None)
    receipt = {
        "schema": "stegverse.ae-relational-math-worker-receipt/v1",
        "goal_id": GOAL_ID,
        "repository": REPO_ID,
        "observed_at": now,
        "source_head": git_head(root),
        "source_root_hash": canonical_hash(str(root.resolve())),
        "state": "PASS" if success else "FAILED",
        "active_goal_id": queue.get("active_goal_id"),
        "goal_status": goal.get("status") if isinstance(goal, dict) else "MISSING",
        "steps": steps,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
        "foreign_repository_mutation_performed": False,
        "publication_performed": False,
        "release_performed": False,
    }
    receipt["receipt_hash"] = canonical_hash(receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
