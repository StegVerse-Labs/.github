#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REGISTRY = ROOT / "control" / "workflow-surface-registry.json"

ALLOWED_CLASSIFICATIONS = {
    "KEEP_STABLE_DISPATCHER",
    "KEEP_STANDALONE_EXCEPTION",
    "CONSOLIDATE_INTO_STABLE_DISPATCHER",
    "TRANSFER_TO_STEGVERSE_WORKER",
    "ELIMINATE",
    "REVIEW_REQUIRED",
    "BLOCKED_ACTIVE_OWNERSHIP",
}


def fail(message: str) -> None:
    raise SystemExit("WORKFLOW_SURFACE_HYGIENE_FAIL: " + message)


def main() -> int:
    if not REGISTRY.exists():
        fail("missing control/workflow-surface-registry.json")
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if payload.get("credential_authority") != "TV/TVC":
        fail("credential_authority must remain TV/TVC")
    if payload.get("non_tv_tvc_secret_or_token_allowed") is not False:
        fail("non-TV/TVC secret/token allowance must be false")

    entries = payload.get("surfaces")
    if not isinstance(entries, list) or not entries:
        fail("registry surfaces must be a non-empty list")

    registered: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            fail("surface entries must be objects")
        path = entry.get("path")
        classification = entry.get("classification")
        owner = entry.get("owner")
        reason = entry.get("reason")
        if not isinstance(path, str) or not path.startswith(".github/workflows/"):
            fail(f"invalid workflow path: {path!r}")
        if path in registered:
            fail(f"duplicate registry path: {path}")
        if classification not in ALLOWED_CLASSIFICATIONS:
            fail(f"invalid classification for {path}: {classification!r}")
        if not isinstance(owner, str) or not owner.strip():
            fail(f"missing owner for {path}")
        if not isinstance(reason, str) or not reason.strip():
            fail(f"missing reason for {path}")
        registered[path] = entry

    actual = {
        str(path.relative_to(ROOT))
        for path in WORKFLOWS.iterdir()
        if path.is_file() and path.suffix in {".yml", ".yaml"}
    }
    expected = set(registered)
    missing = sorted(expected - actual)
    unregistered = sorted(actual - expected)
    if missing:
        fail("registry contains absent workflows: " + ", ".join(missing))
    if unregistered:
        fail("unregistered workflow files: " + ", ".join(unregistered))

    removed = payload.get("removed_in_batch_1", [])
    still_present = sorted(path for path in removed if (ROOT / path).exists())
    if still_present:
        fail("removed workflow reappeared without reconciliation: " + ", ".join(still_present))

    unresolved = sorted(
        path for path, entry in registered.items()
        if entry["classification"] in {"REVIEW_REQUIRED", "BLOCKED_ACTIVE_OWNERSHIP"}
    )
    print(json.dumps({
        "status": "PASS_REGISTERED_SURFACES",
        "registered_count": len(registered),
        "actual_count": len(actual),
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_allowed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
