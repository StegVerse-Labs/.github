#!/usr/bin/env python3
"""Stage exact HIL ESRL artifact bytes for canonical intake and reconciliation.

This helper is deliberately non-canonical and non-mutating with respect to task state.
It reads the supplied physical artifact bytes, validates them against the existing G25
request-consumption receipt, builds the already-defined reconciliation proposal, and
optionally writes only staging outputs. It never edits the task vector, worker registry,
COSV, runtime state, or downstream evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.intake_hil_browser_esrl_evidence import (
    CANONICAL_RECEIPT_REL,
    load_object,
    validate_artifact,
)
from scripts.reconcile_hil_esrl_acceptance import build_proposal

TASK_VECTOR_REL = Path("control/task-vectors/SHWP-HIL-SOVEREIGN-RECEIVER-001.json")
WORKER_REGISTRY_REL = Path("control/worker-registry.d/hil-sovereign-receiver-001.json")
STAGING_SCHEMA = "stegverse.hil-esrl-exact-byte-staging/v1"
INTAKE_REL = Path("hil-browser-esrl-evidence-intake.json")
PROPOSAL_REL = Path("hil-esrl-acceptance-reconciliation-proposal.json")
MANIFEST_REL = Path("hil-esrl-exact-byte-staging-manifest.json")


class StagingError(RuntimeError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise StagingError(reason)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage(*, repo_root: Path, artifact_path: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = repo_root.resolve()
    source = artifact_path.resolve()
    _require(source.is_file(), "artifact_file_required")

    # Read the physical artifact once. Every later operation uses these same bytes.
    artifact_bytes = source.read_bytes()
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    try:
        artifact = json.loads(artifact_bytes.decode("utf-8"))
    except Exception as exc:
        raise StagingError(f"artifact_json_invalid:{type(exc).__name__}:{exc}") from exc
    _require(isinstance(artifact, dict), "artifact_object_required")

    canonical = load_object(root / CANONICAL_RECEIPT_REL)
    intake_receipt = validate_artifact(artifact, canonical)
    intake_receipt["source_artifact_sha256"] = "sha256:" + artifact_sha256
    intake_receipt["canonical_request_consumption_ref"] = str(CANONICAL_RECEIPT_REL)

    task_vector = load_object(root / TASK_VECTOR_REL)
    worker_registry = load_object(root / WORKER_REGISTRY_REL)
    proposal = build_proposal(
        intake=intake_receipt,
        task_vector=task_vector,
        worker_registry=worker_registry,
    )

    result: dict[str, Any] = {
        "schema": STAGING_SCHEMA,
        "state": "READY_FOR_EXACT_BYTE_CANONICAL_INTAKE",
        "task_id": intake_receipt["task_id"],
        "lease_id": intake_receipt["lease_id"],
        "source_artifact_sha256": intake_receipt["source_artifact_sha256"],
        "source_artifact_size": len(artifact_bytes),
        "intake_state": intake_receipt["state"],
        "reconciliation_state": proposal["state"],
        "previous_vector": proposal["previous_vector"],
        "proposed_vector": proposal["proposed_vector"],
        "remaining_blockers": proposal["remaining_blockers"],
        "next_runtime_stage": proposal["next_runtime_stage"],
        "canonical_mutation_performed": False,
        "runtime_mutation_performed": False,
        "authority_effect": "NONE_STAGING_ONLY",
    }

    if output_dir is not None:
        out = output_dir.resolve()
        out.mkdir(parents=True, exist_ok=True)
        exact_name = f"hil-esrl-lease-open-{artifact_sha256}.json"
        exact_path = out / exact_name
        exact_path.write_bytes(artifact_bytes)
        _require(exact_path.read_bytes() == artifact_bytes, "staged_exact_bytes_mismatch")
        _write_json(out / INTAKE_REL, intake_receipt)
        _write_json(out / PROPOSAL_REL, proposal)
        result["staged_exact_artifact"] = exact_name
        result["staged_intake_receipt"] = str(INTAKE_REL)
        result["staged_reconciliation_proposal"] = str(PROPOSAL_REL)
        _write_json(out / MANIFEST_REL, result)

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        result = stage(repo_root=args.repo_root, artifact_path=args.artifact, output_dir=args.output_dir)
    except Exception as exc:
        print(json.dumps({
            "schema": STAGING_SCHEMA,
            "state": "FAIL_CLOSED",
            "reason": f"{type(exc).__name__}:{exc}",
            "canonical_mutation_performed": False,
            "runtime_mutation_performed": False,
            "authority_effect": "NONE",
        }, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
