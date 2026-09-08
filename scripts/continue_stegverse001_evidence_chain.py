#!/usr/bin/env python3
"""Observe the post-terminal SV001 evidence chain without performing custody mutation.

The canonical current-iPhone Site runtime owns the machine-governed custody
transition. This observer never calls the legacy Master Records watcher/importer
as a way to create custody. It accepts downstream custody/reconstruction only
when a retained contemporaneous root-InTr ALLOW is present and bound to the exact
canonical G23 source receipt.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_SV002_ANCESTOR = "786323f16e36346c69b2215894086515d7b1d58e"
CANONICAL_G23_SHA = "sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35"
CANONICAL_G23_TRANSITION = "SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED"
MR_TRANSITION = "SV001_MASTER_RECORDS_CUSTODY_AND_RECONSTRUCTION"
MR_INTR_SCHEMA = "stegverse.master-records.sv001-custody-intr-admission/v1"
DEFAULT_SOURCE_RECEIPT = Path.home() / ".stegverse/state/stegverse001-bounded-autonomy/receipts/latest.json"
DEFAULT_MASTER_RECORDS_STATE = Path.home() / ".stegverse/master-records/stegverse001-bounded-autonomy"
DEFAULT_SV002_STATE = Path.home() / ".stegverse/state/sv002-adversarial-observation"
DEFAULT_INTR_ADMISSION = Path.home() / ".stegverse/state/sv001-master-records-governance/admission.latest.json"
SV002_REQUIRED_FILES = (
    "scripts/evaluate_sv002_adversarial_observation.py",
    "fixtures/sv002-adversarial-observation/cases.v1.json",
)
CANONICAL_CURRENT_IPHONE_AUTHORIZATION_SOURCE = "EXTERNAL_WORKERCOORDINATOR_TVC_BOUND_ENVELOPE"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def authorized_execution_state(source: dict[str, Any]) -> bool | str:
    legacy = source.get("authorized_execution", "NOT_ESTABLISHED")
    if legacy is True:
        return True
    if legacy is False:
        return False
    if source.get("authorized_execution_source") == CANONICAL_CURRENT_IPHONE_AUTHORIZATION_SOURCE:
        return True
    return "NOT_ESTABLISHED"


def validate_canonical_source(source: dict[str, Any]) -> None:
    if source.get("transition_id") != CANONICAL_G23_TRANSITION:
        raise RuntimeError("canonical G23 transition identity mismatch")
    if source.get("receipt_hash") != CANONICAL_G23_SHA:
        raise RuntimeError("canonical G23 receipt hash mismatch")


def validate_intr_admission(admission: dict[str, Any]) -> None:
    checks = {
        "schema": admission.get("schema") == MR_INTR_SCHEMA,
        "state": admission.get("state") == "INGRESS_ADMITTED",
        "decision": admission.get("governance_decision") == "ALLOW",
        "transition": admission.get("transition_id") == MR_TRANSITION,
        "source": admission.get("source_receipt_sha256") == CANONICAL_G23_SHA,
        "current": admission.get("current_governance_decision_observed") is True,
        "human_checkpoint": admission.get("human_approval_checkpoint_inserted") is False,
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    if failed:
        raise RuntimeError("contemporaneous root-InTr admission invalid: " + ",".join(failed))


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False, timeout=20)


def validate_sv002_source(source_root: Path) -> dict[str, Any]:
    root = source_root.resolve()
    head = _git(root, "rev-parse", "HEAD")
    ancestor = _git(root, "merge-base", "--is-ancestor", REQUIRED_SV002_ANCESTOR, "HEAD")
    clean = _git(root, "status", "--porcelain")
    files = all((root / path).is_file() for path in SV002_REQUIRED_FILES)
    return {
        "path": str(root),
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "clean_worktree": clean.returncode == 0 and clean.stdout.strip() == "",
        "required_ancestor_present": ancestor.returncode == 0,
        "required_files_present": files,
        "valid": head.returncode == 0 and ancestor.returncode == 0 and clean.returncode == 0 and clean.stdout.strip() == "" and files,
    }


def _load_evaluator(source_root: Path):
    path = source_root / "scripts/evaluate_sv002_adversarial_observation.py"
    spec = importlib.util.spec_from_file_location("sv002_runtime_evaluator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("SV002 evaluator import unavailable")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def continue_chain(
    source_root: Path,
    source_receipt: Path = DEFAULT_SOURCE_RECEIPT,
    master_records_state: Path = DEFAULT_MASTER_RECORDS_STATE,
    sv002_state: Path = DEFAULT_SV002_STATE,
    intr_admission: Path = DEFAULT_INTR_ADMISSION,
) -> dict[str, Any]:
    base = {
        "schema": "stegverse.sv001-evidence-chain-continuation/v2",
        "custody_mutation_performed_by_observer": False,
        "prior_receipt_authorizes_next_transition": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    if not source_receipt.is_file():
        return {**base, "state": "SV001_RECEIPT_NOT_OBSERVED", "retry_allowed": True}

    source = load(source_receipt)
    try:
        validate_canonical_source(source)
    except RuntimeError as exc:
        return {**base, "state": "SV001_CANONICAL_SOURCE_INVALID", "retry_allowed": False, "reason": str(exc)}

    if not intr_admission.is_file():
        return {
            **base,
            "state": "CURRENT_INTR_ADMISSION_NOT_OBSERVED",
            "retry_allowed": True,
            "expected_admission_ref": str(intr_admission),
            "required_transition": MR_TRANSITION,
        }
    admission = load(intr_admission)
    try:
        validate_intr_admission(admission)
    except RuntimeError as exc:
        return {**base, "state": "CURRENT_INTR_ADMISSION_INVALID", "retry_allowed": False, "reason": str(exc)}

    intake_path = master_records_state / "receipts/stegverse001-bounded-autonomy/resident-intake.latest.json"
    recon_path = master_records_state / "receipts/stegverse001-bounded-autonomy/reconstruction.latest.json"
    if not intake_path.is_file() or not recon_path.is_file():
        return {
            **base,
            "state": "MASTER_RECORDS_GOVERNED_CUSTODY_NOT_OBSERVED",
            "retry_allowed": True,
            "intr_admission": admission,
        }

    intake = load(intake_path)
    reconstruction = load(recon_path)
    if intake.get("state") != "PASS" or reconstruction.get("state") != "PASS":
        return {
            **base,
            "state": "MASTER_RECORDS_RECONSTRUCTION_PENDING",
            "retry_allowed": True,
            "intr_admission": admission,
            "master_records_intake": intake,
            "master_records_reconstruction": reconstruction,
        }
    if intake.get("source_receipt_sha256") != CANONICAL_G23_SHA or reconstruction.get("source_receipt_sha256") != CANONICAL_G23_SHA:
        return {**base, "state": "MASTER_RECORDS_SOURCE_BINDING_MISMATCH", "retry_allowed": False}

    sv_source = validate_sv002_source(source_root)
    if not sv_source["valid"]:
        return {**base, "state": "SV002_SOURCE_NOT_CURRENT", "retry_allowed": True, "sv002_source": sv_source}

    evaluator = _load_evaluator(source_root)
    authorized_execution = authorized_execution_state(source)
    observation_valid = reconstruction.get("source_receipt_sha256") == source.get("receipt_hash")
    baseline_inputs = {
        "master_records_custody": "PASS",
        "reconstruction_state": "PASS",
        "observation_valid": observation_valid,
        "output_correct": source.get("state") == "COMPLETED",
        "authorized_execution": authorized_execution,
    }
    baseline = evaluator.evaluate(baseline_inputs)
    fixture_set = load(source_root / "fixtures/sv002-adversarial-observation/cases.v1.json")
    fixture_results = []
    for case in fixture_set.get("cases", []):
        actual = evaluator.evaluate(case["inputs"])["disposition"]
        fixture_results.append({
            "case_id": case["case_id"],
            "expected": case["expected_disposition"],
            "actual": actual,
            "pass": actual == case["expected_disposition"],
        })
    fixtures_pass = len(fixture_results) == 12 and all(item["pass"] for item in fixture_results)
    target_established = baseline["disposition"] == "OBSERVED" and fixtures_pass and observation_valid
    out = {
        **base,
        "state": "PASS" if target_established else "REVIEW_REQUIRED",
        "retry_allowed": not target_established,
        "source_receipt_sha256": source.get("receipt_hash"),
        "intr_admission": admission,
        "master_records_reconstruction_hash": reconstruction.get("reconstruction_hash"),
        "master_records_reconstruction_state": reconstruction.get("state"),
        "sv002_baseline_disposition": baseline,
        "adversarial_fixture_results": fixture_results,
        "adversarial_fixture_suite_pass": fixtures_pass,
        "target_property": "ADVERSARIALLY_CREDIBLE_OBSERVATION",
        "target_property_established": target_established,
        "frozen_experiment_condition": "v0.3 FROZEN",
        "frozen_findings_modified": False,
        "network_source_fetch_performed": False,
        "repository_writeback_performed": False,
    }
    target = sv002_state / "receipts/stegverse001.latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, default=DEFAULT_SOURCE_RECEIPT)
    parser.add_argument("--master-records-state", type=Path, default=DEFAULT_MASTER_RECORDS_STATE)
    parser.add_argument("--sv002-state", type=Path, default=DEFAULT_SV002_STATE)
    parser.add_argument("--intr-admission", type=Path, default=Path(os.getenv("STEGVERSE_SV001_INTR_ADMISSION_RECEIPT") or DEFAULT_INTR_ADMISSION))
    args = parser.parse_args()
    result = continue_chain(args.source_root, args.source_receipt, args.master_records_state, args.sv002_state, args.intr_admission)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {
        "PASS",
        "SV001_RECEIPT_NOT_OBSERVED",
        "CURRENT_INTR_ADMISSION_NOT_OBSERVED",
        "MASTER_RECORDS_GOVERNED_CUSTODY_NOT_OBSERVED",
        "MASTER_RECORDS_RECONSTRUCTION_PENDING",
        "SV002_SOURCE_NOT_CURRENT",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
