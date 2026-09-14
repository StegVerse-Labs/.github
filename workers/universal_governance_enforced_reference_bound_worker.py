#!/usr/bin/env python3
"""Exact-source wrapper for the existing Universal Governance resident worker.

This preserves the existing task/worker/adapter authority chain. It adds only
source-content binding and v2 receipt validation before completion can be
reported.
"""
from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
import sys

from workers import universal_governance_enforced_reference_worker as base

REQUIRED_STEGCORE_COMMIT = "7cbef555608f7e154ae575dcbd5b4e65fbf0c85c"
EXPECTED_GIT_BLOBS = {
    "scripts/run_universal_governance_reference_boundary.py": "c2e41385801498db23de2dc7d4ac0699b37e8abb",
    "src/stegcore/fresh_commit_binding.py": "c0eb3c3e6f1a86c33ebc774576b42e389c3aa2bd",
    "src/stegcore/external_adapter_steggate_execution.py": "78acc068361aa0d2bae7e0c5eaecd693ee07722b",
    "src/stegcore/universal_governance_consequence_evidence.py": "5759f37d0f6b5b8ff092f63ce9f6c857ae6f6962",
}
REQUIRED_V2_TRUE = (
    "reference_enforced_boundary_observed",
    "bypass_negative_control_passed",
    "alternate_consequence_path_closed",
    "stale_binding_rejected",
    "fresh_binding_required",
    "fresh_binding_single_use",
)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def validate_stegcore_source(root: Path) -> dict[str, str]:
    observed: dict[str, str] = {}
    for rel, expected in EXPECTED_GIT_BLOBS.items():
        path = root / rel
        if not path.is_file():
            raise base.SourceUnavailable(f"required merged StegCore source file missing: {rel}")
        actual = git_blob_sha(path)
        observed[rel] = actual
        if actual != expected:
            raise base.SourceUnavailable(
                f"local StegCore source not bound to {REQUIRED_STEGCORE_COMMIT}: {rel}"
            )
    return observed


def validate_v2_runner_receipt(root: Path) -> dict:
    runner = base.read_json(
        root / "stegcore-reference" / "receipts" / "reference-boundary.latest.json"
    )
    if runner.get("schema") != "stegcore.universal-governance-reference-boundary-receipt.v2":
        raise RuntimeError("fresh-binding v2 runner receipt required")
    if any(runner.get(key) is not True for key in REQUIRED_V2_TRUE):
        raise RuntimeError("fresh-binding v2 predicates not fully observed")
    if runner.get("final_target_mutation_count") != 1:
        raise RuntimeError("fresh-binding target mutation count is not exactly one")
    if runner.get("real_external_system_enforced_activation") is not False:
        raise RuntimeError("fresh-binding runner overclaimed external activation")
    return runner


def execute(invocation: dict) -> dict:
    stegcore, _ = base.require_sources()
    observed_blobs = validate_stegcore_source(stegcore)
    receipt = base.execute(invocation)
    root = base.bound_root()
    runner = validate_v2_runner_receipt(root)
    receipt.update({
        "required_stegcore_commit": REQUIRED_STEGCORE_COMMIT,
        "stegcore_source_git_blobs": observed_blobs,
        "alternate_consequence_path_closed": True,
        "stale_binding_rejected": True,
        "fresh_binding_required": True,
        "fresh_binding_single_use": True,
        "final_target_mutation_count": 1,
        "runner_receipt_schema": runner["schema"],
    })
    out = root / "receipts" / "latest.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    try:
        invocation = json.loads(sys.stdin.readline())
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be object")
        receipt = execute(invocation)
        print(json.dumps(base.completed_response(receipt), sort_keys=True))
    except base.SourceUnavailable as exc:
        print(json.dumps(base.handoff_response(exc), sort_keys=True))
    except Exception as exc:
        print(json.dumps(base.blocked_response(exc), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
