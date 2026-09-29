#!/usr/bin/env python3
"""Reject bare unknown/unobserved findings in canonical task record state.

`ECOSYSTEM_STATE_TRANSITION_DISPOSITION_INVARIANT.md` requires that a task
"advances to the next *actual* actionable non-ALLOW disposition or a proven
ALLOW result; it never terminates with an unlabeled 'blocker', silent unknown or
passive observation request", and that "No vague `BLOCKED`, `UNKNOWN` or
`NOT_OBSERVED` may stand alone as a final finding".

`scripts/validate_transition_disposition.py` already enforces that on
transition-disposition receipts. Nothing enforced it on a canonical task
record's own state, so a record could carry `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`
as a standing status - which reads as a passive observation request and implies
an external machine is awaited. No such machine exists: every action is
manifest-directed and state-transition dependent, and
`data/task-registry-global-invariants.json` holds
`remote_computer_is_machine_dependency: false`.

A record may still say a thing has not happened. It must say so as an
actionable non-ALLOW disposition naming the predicate that is unsatisfied and
the edge that would satisfy it, carrying the same fields a receipt must carry.

Non-authorizing. This validates supplied source only; it mints no receipt,
confers no admission and observes no runtime.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_transition_disposition import (  # noqa: E402
    NON_ALLOW,
    NON_ALLOW_REQUIRED,
)

RECORD_ROOT = Path("data/canonical-task-records")
# Blocks that assert the record's own standing findings. Other blocks carry
# their own vocabularies - a substrate review's PENDING_EVIDENCE and a
# dependency's PENDING are defined dispositions there, not bare unknowns - so
# this rule deliberately does not reach them.
FINDING_BLOCKS = ("current_truth", "runtime_observation", "goal_chart")
# A standing status that asserts absence without naming what would resolve it.
BARE_FINDING = re.compile(r"^(UNKNOWN|BLOCKED|UNOBSERVED|NOT_OBSERVED)(_[A-Z0-9_]*)?$")
OBSERVATION_SUFFIX = re.compile(
    r"(NOT_AUTHENTICALLY_OBSERVED|NOT_OBSERVED|NOT_PROVEN|_UNKNOWN)$"
)


def _is_bare_finding(value: str) -> bool:
    return bool(BARE_FINDING.match(value) or OBSERVATION_SUFFIX.search(value))


def validate_record(record: dict, task_id: str) -> list[str]:
    """Return one error per bare finding in the record's standing-state blocks.

    A bare finding is flagged wherever it appears in those blocks: a
    `runtime_observation` entry or a goal-chart state reading
    NOT_AUTHENTICALLY_OBSERVED is the same passive observation request in a
    different field.
    """
    errors: list[str] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            if node.get("disposition") in NON_ALLOW:
                missing = [f for f in NON_ALLOW_REQUIRED if not str(node.get(f, "")).strip()]
                if missing:
                    errors.append(
                        f"{task_id}: NON_ALLOW_REPAIR_REQUIRED {path} "
                        f"missing {', '.join(missing)}"
                    )
                return
            for key, value in sorted(node.items()):
                walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")
        elif isinstance(node, str) and _is_bare_finding(node):
            errors.append(
                f"{task_id}: STOP_BARE_UNACTIONABLE_FINDING {path}={node} "
                "- state an actionable non-ALLOW disposition with "
                + ", ".join(NON_ALLOW_REQUIRED)
            )

    # A block named for observation asserts that something is awaited. Nothing
    # is: every action is manifest-directed, and no external machine waits.
    if isinstance(record.get("runtime_observation"), dict):
        errors.append(
            f"{task_id}: STOP_PASSIVE_OBSERVATION_BLOCK runtime_observation "
            "- actions are manifest-directed state transitions; record the "
            "actual attempted transition and its disposition instead"
        )
    for block in FINDING_BLOCKS:
        if block in record:
            walk(record[block], block)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(RECORD_ROOT))
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero when any record carries a bare finding")
    args = parser.parse_args()

    failures: list[str] = []
    records = sorted(Path(args.root).glob("*.json"))
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        failures.extend(validate_record(record, record.get("task_id", path.stem)))

    for line in failures:
        print(line)
    print(
        f"TASK_RECORD_ACTIONABLE_DISPOSITION_AUDIT records={len(records)} "
        f"conforming={len(records) - len({f.split(':')[0] for f in failures})} "
        f"bare_findings={len(failures)}"
    )
    return 1 if failures and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
