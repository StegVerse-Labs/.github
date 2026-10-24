#!/usr/bin/env python3
"""Report-and-receipt wrapper for validate_canonical_work_coordination.py.

The canonical work coordination validator has no CI caller: the
Cross-Task Coordination Validation workflow triggers on canonical registry
paths but never ran it. This wrapper lets that workflow observe it without
changing any required check. It runs the validator exactly as
scripts/finalize_runtime_profile_map_cycle.py does (repo root, no arguments),
then emits a status-only observation receipt to stdout and, when
GITHUB_STEP_SUMMARY is set, to the job summary.

Disposition is the validator's own: PASS on exit 0, otherwise FAIL_CLOSED with
the standard six fields (failure_code, failed_predicate,
required_evidence_or_repair, retry_entrypoint, owning_existing_goal,
next_attempt). By default the observed FAIL_CLOSED is reported, not enforced
(exit 0, blocking=false), because the registry is known to fail it; pass
--enforce to exit 1 on FAIL_CLOSED. If the validator cannot be run or the
report cannot be written, the wrapper itself fails closed (exit 1) in every
mode: reporting must not turn a failure into a pass.

Read-only and non-authorizing: it appends no event ledger, mints no admitted
receipt, confers no admission and writes only stdout and the job summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_canonical_work_coordination.py"
SCHEMA = "stegverse.canonical-work-coordination-validation-observation/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = ("Cross-Task Coordination Validation / validate: "
                    "python scripts/report_canonical_work_coordination_validation.py")
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
VALIDATOR_FAIL_CLOSED = "CANONICAL_WORK_COORDINATION_VALIDATOR_FAIL_CLOSED"
WRAPPER_ERROR = "CANONICAL_WORK_COORDINATION_VALIDATION_REPORT_ERROR"


def observe(validator: Path, cwd: Path, python: str = sys.executable) -> dict:
    completed = subprocess.run([python, str(validator)], cwd=cwd, text=True, capture_output=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    lines = [line for line in output.splitlines() if line.strip()]
    receipt = {
        "schema": SCHEMA,
        "validator": "scripts/validate_canonical_work_coordination.py",
        "invocation": "python scripts/validate_canonical_work_coordination.py (repo root, no args)",
        "validator_exit_code": completed.returncode,
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "authority_effect": "NONE_READ_ONLY",
        "event_ledger_written": False,
    }
    if completed.returncode == 0:
        receipt.update(disposition="PASS", first_line=lines[0] if lines else "")
        return receipt
    first_line = next((line for line in lines if line.startswith("FAIL_CLOSED")), lines[-1] if lines else "")
    receipt.update(
        disposition="FAIL_CLOSED",
        first_line=first_line,
        failure_code=VALIDATOR_FAIL_CLOSED,
        failed_predicate=first_line or f"validator exit {completed.returncode} with no output",
        required_evidence_or_repair=("repair the source contract named in failed_predicate; "
                                     "this report modifies nothing"),
        retry_entrypoint=RETRY_ENTRYPOINT,
        owning_existing_goal=OWNING_GOAL,
        next_attempt="re-run on the next change to a watched canonical registry or validator path",
    )
    return receipt


def summary_markdown(receipt: dict) -> str:
    rows = ["### Canonical work coordination validator (observation)", "",
            f"- disposition: `{receipt.get('disposition')}`",
            f"- blocking: `{receipt.get('blocking')}`",
            f"- validator_exit_code: `{receipt.get('validator_exit_code')}`",
            f"- first_line: `{receipt.get('first_line', '')}`"]
    rows += [f"- {key}: `{receipt[key]}`" for key in SIX_FIELDS if key in receipt]
    return "\n".join(rows) + "\n\n"


def wrapper_error(exc: BaseException) -> dict:
    return {
        "schema": SCHEMA, "disposition": "FAIL_CLOSED", "blocking": True,
        "failure_code": WRAPPER_ERROR,
        "failed_predicate": f"report wrapper could not observe the validator: {type(exc).__name__}: {exc}",
        "required_evidence_or_repair": "restore scripts/validate_canonical_work_coordination.py and a runnable interpreter",
        "retry_entrypoint": RETRY_ENTRYPOINT, "owning_existing_goal": OWNING_GOAL,
        "next_attempt": "re-run after the wrapper error is repaired",
        "authority_effect": "NONE_READ_ONLY", "event_ledger_written": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--enforce", action="store_true", help="exit 1 when the validator fails closed")
    parser.add_argument("--validator", type=Path, default=VALIDATOR, help=argparse.SUPPRESS)
    parser.add_argument("--cwd", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if not args.validator.is_file():
            raise FileNotFoundError(str(args.validator))
        receipt = observe(args.validator, args.cwd)
        receipt["blocking"] = bool(args.enforce)
    except Exception as exc:  # the wrapper itself fails closed
        receipt = wrapper_error(exc)
    exit_code = 1 if receipt.get("failure_code") == WRAPPER_ERROR else 0
    if receipt["disposition"] == "FAIL_CLOSED" and args.enforce:
        exit_code = 1
    try:
        print(json.dumps(receipt, indent=2, sort_keys=True))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as handle:
                handle.write(summary_markdown(receipt))
    except Exception as exc:
        print(f"could not write the report: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if receipt["disposition"] == "FAIL_CLOSED":
        print(f"::warning title=Canonical work coordination validator::{receipt.get('first_line') or receipt['failed_predicate']}")
        for key in SIX_FIELDS:
            print(f"{key}={receipt.get(key, '')}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
