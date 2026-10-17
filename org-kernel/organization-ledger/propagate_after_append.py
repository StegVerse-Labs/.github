#!/usr/bin/env python3
"""Carry this repository's receipts onto the organization chain right after an append.

This is wiring, not a second propagator: it calls the component's own
`propagate_repository_receipts.propagate()` in-process (digest-pinned in
component-manifest.json like every other module) for the one repository whose
ledger the run just appended to.

- **Epoch.** `--hb-epoch` is text and goes through the shared validator
  (`ledger_common.require_supplied_epoch`, ASCII digits, >= 32) *before*
  propagation is loaded or reached. The validated int is handed over
  in-process. Nothing re-coerces it, and no clock is read.
- **No rollback, no block.** The existing contract is that each
  organization append is its own committed receipt (CAS under the ledger
  lock), and a refused propagation writes nothing (its `LedgerRefusal` is
  raised before `append`). A second run is a no-op for receipts already
  carried. So a propagation refusal never removes or blocks the receipt
  the run already appended. It is reported as six-field FAIL_CLOSED (exit
  1). The workflow still publishes and reads back, and then fails the run
  on the recorded refusal.
- **Refusals.** A `LedgerRefusal` is printed as `json.dumps(exc.refusal)`,
  unchanged. A plain `SystemExit(str)` (or the writer's
  `LedgerLocationRequired`) gets the six fields here.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


common = _load("ledger_common")
RETRY = common.entrypoint(__file__, "main")
PREDICATE = "REPOSITORY_RECEIPTS_PROPAGATE_AFTER_THE_APPEND"


def six_fields(message: str, code: str | None = None) -> dict:
    return {
        "schema": "stegverse.organization-repository-propagation-refusal/v1",
        "disposition": "FAIL_CLOSED",
        "failure_code": code or common.failure_code_of(message) or "REPOSITORY_PROPAGATION_REFUSED",
        "failed_predicate": PREDICATE,
        "detail": str(message),
        "required_evidence_or_repair": "repair what propagation refused (" + str(message) + ") and run the propagation again; "
                                       "the receipt already appended stands and is not rolled back",
        "retry_entrypoint": RETRY,
        "owning_existing_goal": common.owning_existing_goal(),
        "next_attempt": "rerun propagate_after_append.py with the same --hb-epoch; receipts already carried are skipped",
        "consequence_committed": False,
        "authority_effect": "NONE_REFUSAL_ONLY",
    }


def run(repository: str, repository_ledger_root: Path, hb_epoch) -> dict:
    """Validate the epoch, then propagate in-process. Raises LedgerRefusal / SystemExit / ValueError on refusal."""
    epoch = common.require_supplied_epoch(hb_epoch, RETRY)       # '+33' is refused here, before propagation loads
    propagation = _load("propagate_repository_receipts")
    return propagation.propagate(repository, repository_root=repository_ledger_root, hb_epoch=epoch)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", required=True, help="owner/name of the repository whose ledger was appended")
    parser.add_argument("--repository-ledger-root", type=Path, required=True,
                        help="that repository's ledger, materialized from the appended ref")
    parser.add_argument("--hb-epoch", type=str, default=None, help="the run's supplied epoch, as text")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        result, code = run(args.repository, args.repository_ledger_root, args.hb_epoch), 0
    except SystemExit as exc:
        # A LedgerRefusal carries its six fields as `.refusal` (read off the exception, not by class:
        # each module loads ledger_common on its own, so the class objects differ). Printed unchanged.
        refusal = getattr(exc, "refusal", None)
        if isinstance(refusal, dict):
            result, code = refusal, 1
        elif isinstance(exc.code, str):
            result, code = six_fields(exc.code), 1
        else:
            raise
    except ValueError as exc:   # LedgerLocationRequired and other writer ValueErrors
        result, code = six_fields(str(exc), getattr(exc, "failed_predicate", None)), 1
    text = json.dumps(result, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
