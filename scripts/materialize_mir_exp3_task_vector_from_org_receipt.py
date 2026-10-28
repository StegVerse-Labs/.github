#!/usr/bin/env python3
"""Materialize the Experiment 3 task-vector transition from its organization receipt.

The durable queue entry
control/resident-execution-request.d/mir-exp3-task-vector-org-receipt-001.json
declares the transition of control/task-vectors/MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003.json
from SOURCE_ONLY_ACTIVE to EMITTED. Its trigger is the organization receipt that
StegVerse-org/.github organization-ledger-transition.yml appends to
refs/stegverse/organization-ledger when the owner merges StegVerse-org/.github#198,
read back as a stegverse.organization-ledger-readback/v1 result.

No receiver, listener, external machine or Master Records response is awaited
(DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION). Until a readback is supplied
the transition is FAIL_CLOSED ORGANIZATION_RECEIPT_NOT_APPENDED. A readback whose
canonical manifest or organization transition id does not match is refused with
the six non-ALLOW fields. This script reads supplied records only: it never mints
a receipt, and a fixture readback never becomes evidence.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
GOAL = "MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003"
COSV = "50000000100000"
VECTOR_REL = Path("control/task-vectors/MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003.json")
QUEUE_REL = Path("control/resident-execution-request.d/mir-exp3-task-vector-org-receipt-001.json")
ENTRYPOINT = "scripts/materialize_mir_exp3_task_vector_from_org_receipt.py"
FROM_STATE = "SOURCE_ONLY_ACTIVE"
TO_STATE = "EMITTED"
LEDGER_REPOSITORY = "StegVerse-org/.github"
LEDGER_REF = "refs/stegverse/organization-ledger"
LEDGER_PRODUCER = "StegVerse-org/.github:.github/workflows/organization-ledger-transition.yml"
TRANSITION_REQUEST_ID = "MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003-001"
TRANSITION_REQUEST_PR = "https://github.com/StegVerse-org/.github/pull/198"
CANONICAL_MANIFEST_SHA256 = "f0fa715e6a25e7fbf57cf4075ff664751b7606cab93ecdbb59f560e90ae510c6"
ORGANIZATION_TRANSITION_ID = "ORGANIZATION-SDK-MANIFEST-INGRESS-d7f860f157ae325e"
READBACK_SCHEMA = "stegverse.organization-ledger-readback/v1"
RESULT_SCHEMA = "stegverse.mir-exp3-task-vector-materialization/v1"
FIXTURE_MARKER = "_fixture_not_evidence"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")

# Readback fields the transition binds, with the value each must carry.
# None means "present and well formed", checked separately below.
BOUND_RECEIPT_FIELDS = {
    "schema": READBACK_SCHEMA,
    "disposition": "ALLOW",
    "ingress_refused": False,
    "ingress_receipt_in_chain": True,
    "ingress_receipt_bound_to_manifest": True,
    "every_receipt_verifies_against_its_body": True,
    "every_source_receipt_retained_and_verifies": True,
    "master_records_awaited": False,
    "canonical_manifest_sha256": CANONICAL_MANIFEST_SHA256,
    "organization_transition_id": ORGANIZATION_TRANSITION_ID,
    "ingress_organization_receipt_sha256": None,
    "head_receipt_sha256": None,
}


def non_allow(failure_code: str, failed_predicate: str, repair: str,
              evidence_refs: list[str] | None = None, **extra: Any) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "task_id": GOAL,
        "cosv_task_vector": COSV,
        "disposition": "FAIL_CLOSED",
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": ENTRYPOINT,
        "owning_existing_goal": GOAL,
        "next_attempt": "on org#198 merge; materialized from the receipt readback",
        "evidence_refs": evidence_refs or ["SOURCE_RECORD_ONLY:" + str(QUEUE_REL)],
        "consequence_committed": False,
        "authority_effect": "NONE",
        **extra,
    }


def pending() -> dict[str, Any]:
    """The queue entry's disposition while no receipt has been read back."""
    return non_allow(
        "ORGANIZATION_RECEIPT_NOT_APPENDED",
        "EXP3_ORGANIZATION_RECEIPT_READ_BACK_FROM_ORGANIZATION_LEDGER",
        "The owner merges " + TRANSITION_REQUEST_PR + "; " + LEDGER_PRODUCER
        + " appends the organization receipt for canonical manifest "
        + CANONICAL_MANIFEST_SHA256 + " to " + LEDGER_REF + "; supply the "
        + READBACK_SCHEMA + " result for organization_transition_id "
        + ORGANIZATION_TRANSITION_ID + " and the ledger commit to this materializer.",
        evidence_refs=[TRANSITION_REQUEST_PR, "SOURCE_RECORD_ONLY:" + str(QUEUE_REL)],
    )


def readback_errors(readback: Any) -> list[tuple[str, str]]:
    """Return (failure_code, failed_predicate) pairs for every binding the readback breaks."""
    if not isinstance(readback, Mapping):
        return [("ORGANIZATION_RECEIPT_READBACK_INVALID", "READBACK_IS_A_JSON_OBJECT")]
    errors: list[tuple[str, str]] = []
    if readback.get("canonical_manifest_sha256") != CANONICAL_MANIFEST_SHA256:
        errors.append(("ORGANIZATION_RECEIPT_CANONICAL_MISMATCH",
                       "READBACK_CANONICAL_MANIFEST_SHA256_EQUALS_" + CANONICAL_MANIFEST_SHA256))
    if readback.get("organization_transition_id") != ORGANIZATION_TRANSITION_ID:
        errors.append(("ORGANIZATION_RECEIPT_TRANSITION_ID_MISMATCH",
                       "READBACK_ORGANIZATION_TRANSITION_ID_EQUALS_" + ORGANIZATION_TRANSITION_ID))
    for key, expected in BOUND_RECEIPT_FIELDS.items():
        if key in ("canonical_manifest_sha256", "organization_transition_id"):
            continue
        value = readback.get(key)
        ok = (isinstance(value, str) and bool(HEX64.fullmatch(value))) if expected is None \
            else (value is expected if isinstance(expected, bool) else value == expected)
        if not ok:
            errors.append(("ORGANIZATION_RECEIPT_READBACK_INVALID",
                           "READBACK_FIELD_" + key.upper() + "_BOUND"))
    return errors


def materialize(vector: Mapping[str, Any], readback: Any, ledger_commit: Any,
                *, allow_fixture: bool = False) -> dict[str, Any]:
    """Given a read-back organization receipt, produce the task-vector update.

    Returns an ALLOW result carrying the updated vector, or a six-field
    FAIL_CLOSED. The input vector is never mutated. A readback marked as a
    fixture is refused unless allow_fixture is set, and even then the result
    is SYNTHETIC_TEST and may not be written.
    """
    fixture = isinstance(readback, Mapping) and bool(readback.get(FIXTURE_MARKER))
    if fixture and not allow_fixture:
        return non_allow("ORGANIZATION_RECEIPT_IS_FIXTURE", "READBACK_IS_NOT_A_FIXTURE",
                         "Supply the readback produced from a fresh fetch of " + LEDGER_REF
                         + "; a fixture is never evidence.")
    errors = readback_errors(readback)
    if errors:
        code, predicate = errors[0]
        return non_allow(code, predicate,
                         "Supply the " + READBACK_SCHEMA + " result for organization_transition_id "
                         + ORGANIZATION_TRANSITION_ID + " over canonical manifest "
                         + CANONICAL_MANIFEST_SHA256 + "; refused readbacks are not materialized.",
                         binding_errors=[p for _, p in errors])
    if not isinstance(ledger_commit, str) or not HEX40.fullmatch(ledger_commit):
        return non_allow("ORGANIZATION_LEDGER_COMMIT_INVALID", "LEDGER_COMMIT_IS_40_HEX",
                         "Supply the " + LEDGER_REF + " commit the readback was taken from.")
    if vector.get("task_id") != GOAL or vector.get("vector") != COSV:
        return non_allow("TASK_VECTOR_IDENTITY_MISMATCH", "VECTOR_IS_" + GOAL + "_" + COSV,
                         "Materialize only " + str(VECTOR_REL) + ".")
    receipt = readback["ingress_organization_receipt_sha256"]
    receipt_ref = (LEDGER_REPOSITORY + "@" + LEDGER_REF + ":" + ledger_commit
                   + ":receipts/" + receipt + ".json")
    transition = {
        "from_state": FROM_STATE,
        "to_state": TO_STATE,
        "trigger": "ORGANIZATION_RECEIPT_READ_BACK",
        "queue_entry_ref": str(QUEUE_REL),
        "organization_ledger_repository": LEDGER_REPOSITORY,
        "organization_ledger_ref": LEDGER_REF,
        "organization_ledger_commit": ledger_commit,
        "organization_transition_id": ORGANIZATION_TRANSITION_ID,
        "organization_receipt_sha256": receipt,
        "organization_ledger_head_receipt_sha256": readback["head_receipt_sha256"],
        "canonical_manifest_sha256": CANONICAL_MANIFEST_SHA256,
        "transition_request_id": TRANSITION_REQUEST_ID,
        "master_records_awaited": False,
    }
    current = vector.get("vector_state")
    if current == TO_STATE:
        if vector.get("state_transition") == transition:
            return {"schema": RESULT_SCHEMA, "task_id": GOAL, "disposition": "ALLOW",
                    "state": "ALREADY_MATERIALIZED", "vector": dict(vector),
                    "evidence_class": "SYNTHETIC_TEST" if fixture else "SOURCE_IMPLEMENTED",
                    "authority_effect": "NONE"}
        return non_allow("TASK_VECTOR_ALREADY_MATERIALIZED_FROM_ANOTHER_RECEIPT",
                         "VECTOR_STATE_TRANSITION_EQUALS_SUPPLIED_RECEIPT",
                         "The vector already records a different organization receipt; reconcile it first.")
    if current != FROM_STATE:
        return non_allow("TASK_VECTOR_NOT_IN_SOURCE_STATE", "VECTOR_STATE_IS_" + FROM_STATE,
                         "Materialize only from " + FROM_STATE + ".")
    updated = copy.deepcopy(dict(vector))
    updated["vector_state"] = TO_STATE
    updated["state_transition"] = transition
    refs = list(updated.get("evidence_refs") or [])
    for ref in (TRANSITION_REQUEST_PR, receipt_ref):
        if ref not in refs:
            refs.append(ref)
    updated["evidence_refs"] = refs
    updated["authority_effect"] = "NONE"
    return {"schema": RESULT_SCHEMA, "task_id": GOAL, "disposition": "ALLOW",
            "state": "MATERIALIZED", "vector": updated,
            "evidence_class": "SYNTHETIC_TEST" if fixture else "SOURCE_IMPLEMENTED",
            "fixture_only": fixture, "authority_effect": "NONE"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readback", type=Path,
                        help="stegverse.organization-ledger-readback/v1 JSON read back from a fresh fetch")
    parser.add_argument("--ledger-commit", help="refs/stegverse/organization-ledger commit read")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true", help="write the updated vector")
    args = parser.parse_args(argv)
    if args.readback is None:
        print(json.dumps(pending(), indent=2, sort_keys=True))
        return 2
    vector_path = args.root / VECTOR_REL
    vector = json.loads(vector_path.read_text(encoding="utf-8"))
    readback = json.loads(args.readback.read_text(encoding="utf-8"))
    result = materialize(vector, readback, args.ledger_commit)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["disposition"] != "ALLOW":
        return 2
    if args.write and result["state"] == "MATERIALIZED":
        vector_path.write_text(json.dumps(result["vector"], indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
