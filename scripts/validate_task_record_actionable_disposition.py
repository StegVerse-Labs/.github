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
    non_allow_missing,
)
from registry_gate_findings import evaluation, finding  # noqa: E402

GATE = "TASK_RECORD_ACTIONABLE_DISPOSITION"
REPAIR = ("state an actionable non-ALLOW disposition carrying "
          + ", ".join(NON_ALLOW_REQUIRED))

RECORD_ROOT = Path("data/canonical-task-records")
# Blocks that assert the record's own standing findings. Other blocks carry
# their own vocabularies - a substrate review's PENDING_EVIDENCE and a
# dependency's PENDING are defined dispositions there, not bare unknowns - so
# this rule deliberately does not reach them. `runtime_resolution` and
# `status_reason` state the same standing runtime status under another name
# (StegVerse-Labs/.github#3012 O2).
FINDING_BLOCKS = ("current_truth", "runtime_observation", "goal_chart",
                  "runtime_resolution", "status_reason")
# A key that quotes history rather than asserting standing state: a retained
# prior value (`superseded_*`), a history list, a dated review snapshot
# (`*_YYYYMMDD`) or an evidence reference list. A token quoted there is
# evidence of what was once recorded, not a passive status.
HISTORICAL_KEY = re.compile(r"(^superseded_|history|_\d{8}$|evidence_refs$)")
# A standing status that asserts absence without naming what would resolve it.
BARE_FINDING = re.compile(r"^(UNKNOWN|BLOCKED|UNOBSERVED|NOT_OBSERVED)(_[A-Z0-9_]*)?$")
# The suffix forms of the same passive findings, including their YET and
# UN-prefixed spellings (`*_NOT_YET_OBSERVED`, `*_STILL_UNOBSERVED`,
# `*_NOT_YET_PROVEN`, `*_UNPROVEN`): each reads as the same passive
# observation request (StegVerse-Labs/.github#3012 K1).
OBSERVATION_SUFFIX = re.compile(
    r"(NOT_(YET_)?(AUTHENTICALLY_)?OBSERVED|_UNOBSERVED|NOT_(YET_)?PROVEN"
    r"|_UNPROVEN|_UNKNOWN)$"
)


# A field whose value is the predicate that gates progression: the predicate a
# transition or goal-chart step requires, a failed/unresolved/required/next/
# first predicate, a remaining or completion predicate list, a required
# sequence, or a gate. `expected_evidence_predicates` and other evidence lists
# are labels Master Records reconciliation matches, so they are not reached.
PROGRESSION_PREDICATE_KEY = re.compile(
    r"^(predicate|predicates|failed_predicate|ref"
    r"|[a-z_]*(unresolved|required|next|first|remaining|completion)[a-z_]*predicates?"
    r"|required_reusable_sequence|gates?|[a-z_]+_gates?)$"
)
# An affirmative observer predicate: progression waits for something to be
# observed. Runtime reality is the Organization receipt appended under lock, and
# a post-closure observer gate is prohibited (task-registry-global-invariants
# `post_closure_authentic_observer_gate_allowed: false`), so the gate names
# ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:<transition> instead
# (StegVerse-Labs/.github#3012). The negative spellings are OBSERVATION_SUFFIX.
AFFIRMATIVE_OBSERVER = re.compile(r"_OBSERVED$")
APPEND_PREDICATE = "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK"


def _is_bare_finding(value: str) -> bool:
    return bool(BARE_FINDING.match(value) or OBSERVATION_SUFFIX.search(value))


def _names_affirmative_observer(value: str) -> bool:
    """True when any predicate token in `value` (`A AND B` too) is an observer."""
    return any(
        AFFIRMATIVE_OBSERVER.search(token) and not OBSERVATION_SUFFIX.search(token)
        for token in value.split()
    )


def validate_progression_predicates(record: dict, task_id: str) -> list[str]:
    """Return one error per progression-predicate field naming an observer.

    The whole record is walked, because progression predicates sit in
    transition graphs, dependency lists and reconciliation blocks as well as in
    FINDING_BLOCKS. A RETIRED record gates nothing, a dependency `ref` counts
    only on a RUNTIME_PREDICATE or state dependency, and the HISTORICAL_KEY and
    typed non-ALLOW exclusions are the same as validate_record's.
    """
    if record.get("coordination_state") == "RETIRED":
        return []
    errors: list[str] = []

    def walk(node: object, path: str, gating: bool) -> None:
        if isinstance(node, dict):
            if node.get("disposition") in NON_ALLOW:
                return
            ref_gates = "kind" in node and "dependency_id" in node
            for key, value in sorted(node.items()):
                if HISTORICAL_KEY.search(key):
                    continue
                child_gating = bool(PROGRESSION_PREDICATE_KEY.match(key)) and (
                    key != "ref" or ref_gates)
                walk(value, f"{path}.{key}" if path else key, child_gating)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]", gating)
        elif gating and isinstance(node, str) and _names_affirmative_observer(node):
            errors.append(
                f"{task_id}: STOP_AFFIRMATIVE_OBSERVER_PREDICATE {path}={node} "
                f"- gate on {APPEND_PREDICATE}:<transition> naming the same "
                "transition, keeping the prior value as superseded_* history"
            )

    walk(record, "", False)
    return errors


def validate_record(record: dict, task_id: str) -> list[str]:
    """Return one error per bare finding in the record's standing-state blocks.

    A bare finding is flagged wherever it appears in those blocks: a
    `runtime_observation` entry or a goal-chart state reading
    NOT_AUTHENTICALLY_OBSERVED is the same passive observation request in a
    different field. Not flagged: a token inside a typed non-ALLOW record
    (judged by its own required fields instead) or under a HISTORICAL_KEY.
    """
    errors: list[str] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            if node.get("disposition") in NON_ALLOW:
                missing = non_allow_missing(node)
                if missing:
                    errors.append(
                        f"{task_id}: NON_ALLOW_REPAIR_REQUIRED {path} "
                        f"missing {', '.join(missing)}"
                    )
                return
            for key, value in sorted(node.items()):
                if HISTORICAL_KEY.search(key):
                    continue
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

    # The violation is a value that awaits, not a block whose name mentions
    # observation: such a block mostly holds binding references, which are
    # legitimate. The walk below flags the awaiting values wherever they sit.
    for block in FINDING_BLOCKS:
        if block in record:
            walk(record[block], block)
    return errors + validate_progression_predicates(record, task_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(RECORD_ROOT))
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero when any record carries a bare finding")
    parser.add_argument("--findings", action="store_true",
                        help="emit Healer-intake findings instead of prose")
    args = parser.parse_args()

    failures: list[str] = []
    rows: list[dict] = []
    records = sorted(Path(args.root).glob("*.json"))
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        task_id = record.get("task_id", path.stem)
        for line in validate_record(record, task_id):
            failures.append(line)
            code, _, detail = line.partition(" ")[2].partition(" ")
            rows.append(finding(
                gate=GATE, task_id=task_id, predicate_id=code.strip(),
                detail=detail.strip() or line, evidence=[str(path)],
                repair=REPAIR,
                retry_entrypoint=f"{Path(__file__).name} --strict",
            ))

    if args.findings:
        print(json.dumps(evaluation(GATE, rows), indent=2, sort_keys=True))
    else:
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
