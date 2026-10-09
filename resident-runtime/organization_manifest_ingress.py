#!/usr/bin/env python3
"""`ORGANIZATION_SDK_MANIFEST_INGRESS` -- receive a submitted SDK manifest here.

The capability overlay says where a registered capability is received:
`org-runtime/interlock-intr.json` binds `sdk-manifest-ingress` /
`SDK:ManifestIngress` / `SUBMIT_MANIFEST` to a receiving operation this
repository owns. That binding resolved a destination and stopped there. Nothing
drove a submission into it, so `organization_receipt_observed` stayed false on
every handoff and the crossing never happened.

This is the receiving operation. The organization resolves its own destination
from its own boundary document -- it is not handed one, and it does not fetch
one, because `repository_endpoint_rule` makes this repository the owner of
organization communication and a document supplied by a caller would let the
caller name its own organization.

The sequence is the one the binding declares, in that order:

    derive_execution_request(manifest, this organization's boundary)
    resident-runtime/sdk_manifest_crossing.py::cross       admission
    org-boundary/runtime/process_boundary.py               processing
    .stegverse/transition-ledger/emit.py::append           repository receipt
    resident-runtime/aggregate_repo_transition.py::aggregate_transition
                                                           organization receipt
    stegverse.manifest_state_transition_runtime.admit_runtime_result

The two ledger levels are both written, in that order, because the transition
occurs in this repository and the organization ledger's job is to consume a
receipt from the level below. One writer standing in for both levels is what
`preserves_repo_receipt: true` has nothing to preserve from, and it leaves
organization replay resting on a receipt the same call minted, where
`ORGANIZATION_REPLAY_MUST_REQUIRE_ONLY_VERIFIED_REPO_RECEIPTS_AND_ORG_RECEIPTS`
asks for a verified repository receipt underneath.

Two resolutions happen at two boundaries and must not be confused. The overlay
resolves *organization* ingress: which organization receives this capability,
and on what operation. `completion.egress` then resolves which *internal*
endpoint of that organization serves the declared surface. The SDK's
`completion_egress_controls_outbound_organization_routing: false` is about the
first; it does not make a manifest's declared internal surface unreadable once
the manifest has arrived.

The organization never grades its own result. It reports what it observed and
hands that to the SDK's own `admit_runtime_result`, which is the authority on
whether a runtime result closes the transition. A refusal is returned verbatim,
naming its own predicate, rather than being retried into a success.

A refusal is also recorded. A state transition is the disposition of an intended
action, not only a successful one: a submission that arrived and was refused is
a transition whose disposition is DENY, and `organization_scope_rule` makes no
exception for it. Every refusal path through `receive` -- an unresolvable
destination, a capability bound elsewhere, a crossing this manifest cannot
drive, a far side that refused, a boundary chain that does not reconstruct --
appends a repository receipt and the organization receipt that consumes it,
under `ORGANIZATION_SDK_MANIFEST_INGRESS_REFUSED`. Before this they returned a
refusal and wrote nothing, which made a held or retried submission
indistinguishable from one that never arrived.

`organization_receipt_observed` stays false on a refusal regardless. It means an
admitted crossing was observed, and a refusal receipt is not that; a caller
reading one as the other would treat a refused submission as a completed
transition. The refusal's own digests are returned under their own names.

Nothing here grants authority. The organization appends its own receipt, which
is its own runtime reality; it publishes for custody separately and does not
claim an observed Master Records organization record it has not seen.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from stegverse.manifest_contract import validate_ingress_manifest
from stegverse.manifest_state_transition_runtime import (
    RESULT_SCHEMA,
    admit_runtime_result,
    derive_execution_request,
)
from stegverse.route_resolution import route_from_manifest

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "org-runtime/interlock-intr.json"

OPERATION_ID = "ORGANIZATION_SDK_MANIFEST_INGRESS"
OWNER_REPOSITORY = "StegVerse-Labs/.github"
PROFILE_ID = "sdk-manifest-ingress"
PROFILE_NAME = "SDK:ManifestIngress"
OPERATION = "SUBMIT_MANIFEST"
RESULT_SCHEMA_ORG = "stegverse.organization-manifest-ingress-result/v1"
REFUSAL_SCHEMA = "stegverse.organization-manifest-ingress-refusal-record/v1"
GOVERNANCE_REQUEST_SCHEMA = "stegverse.org-governance-decision-request/v1"

#: The intended action every submission carries, whatever its disposition.
#:
#: A state transition is the disposition of an intended action, not only a
#: successful one. `organization_scope_rule` is that every state transition
#: occurring within the organization emits an organization receipt, and a
#: refused submission is one: it arrived, it was dispositioned, and nothing
#: recorded it. Refusing and keeping no record makes a held or retried
#: submission indistinguishable from one that never arrived.
INTENDED_ACTION = "RECEIVE_A_SUBMITTED_SDK_MANIFEST"
REFUSED_CLASS = "ORGANIZATION_SDK_MANIFEST_INGRESS_REFUSED"
# The organization ledger is its own runtime reality locus, so replay of this
# transition terminates on this chain. That is the contract's own replay_rule,
# not a claim about any higher level.
ORGANIZATION_REPLAY = "PASS"
# The rule that recomputes these receipts is this file at the revision that
# wrote them. Binding that revision into each organization receipt lets a
# verifier fetch the exact rule, rather than whatever the file says today.
RECOMPUTATION_RULE_PATH = "resident-runtime/organization_manifest_ingress.py"
_REVISION = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
#: The only fields projected to a CI step summary. Every one is a digest, an
#: identifier or a revision: nothing a receipt carries as evidence, and nothing
#: secret. The full result stays where the run already keeps it.
STEP_SUMMARY_FIELDS = ("receipt_id", "receipt_sha256", "recomputation_rule_ref",
                       "run_id", "commit")
RETRY_ENTRYPOINT = "resident-runtime/organization_manifest_ingress.py::receive"
#: A repository receipt written and an organization append that raised is a
#: partial commit. It is returned as this typed disposition, never as an
#: exception: the repository level did commit, and an escaping exception would
#: let a caller read the submission as one nothing recorded.
APPEND_NOT_COMMITTED = "ORGANIZATION_APPEND_NOT_COMMITTED"
APPEND_NOT_COMMITTED_PREDICATE = "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK"
APPEND_OWNING_GOAL = "ORGANIZATION-BATCH-CUSTODY-REPLAY-001"
UNOBSERVED = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
PARENT_MANIFEST_INVALID_PREDICATE = "MANIFEST_DECLARED_ORGANIZATION_BATCH_PARENT_MANIFEST_IS_VALID"


def recomputation_rule_ref(environ: Mapping[str, str] | None = None,
                           root: Path = ROOT) -> str:
    """`OWNER_REPOSITORY@<sha>:<this file>`, or fail closed.

    In Actions the revision is `GITHUB_SHA`; elsewhere it is the checkout's own
    `HEAD`. A revision that resolves from neither is not guessed: a receipt
    naming a rule nobody can fetch cannot be recomputed, so none is written.
    """
    environ = os.environ if environ is None else environ
    revision = (environ.get("GITHUB_SHA") or "").strip().lower()
    if not revision:
        try:
            revision = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                text=True, check=True, timeout=30).stdout.strip().lower()
        except (OSError, subprocess.SubprocessError):
            revision = ""
    if not _REVISION.match(revision):
        raise RuntimeError("RECOMPUTATION_RULE_REVISION_UNRESOLVABLE")
    return f"{OWNER_REPOSITORY}@{revision}:{RECOMPUTATION_RULE_PATH}"


def step_summary_projection(result: Mapping[str, Any],
                            environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The non-secret fields of one receipt, for `$GITHUB_STEP_SUMMARY`.

    Live receipts are never committed to branches; this projection is what a run
    shows in its summary instead.
    """
    environ = os.environ if environ is None else environ
    received = result.get("received")
    return {
        "receipt_id": (result.get("organization_transition_id") if received
                       else result.get("refusal_transition_id")),
        "receipt_sha256": (result.get("organization_receipt_sha256") if received
                           else result.get("refusal_organization_receipt_sha256")),
        "recomputation_rule_ref": result.get("recomputation_rule_ref"),
        "run_id": environ.get("GITHUB_RUN_ID"),
        "commit": environ.get("GITHUB_SHA"),
    }


def write_step_summary(result: Mapping[str, Any],
                       environ: Mapping[str, str] | None = None) -> bool:
    """Append the projection to `$GITHUB_STEP_SUMMARY` when a run provides one."""
    environ = os.environ if environ is None else environ
    target = environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return False
    projection = step_summary_projection(result, environ)
    lines = ["### Organization manifest-ingress receipt", "",
             "| field | value |", "| --- | --- |"]
    lines += [f"| {key} | `{projection[key]}` |" for key in STEP_SUMMARY_FIELDS]
    with open(target, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return True


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


crossing_module = _module("sdk_manifest_crossing", "resident-runtime/sdk_manifest_crossing.py")
repository_ledger = _module("repo_transition_emit", ".stegverse/transition-ledger/emit.py")
organization_ledger = _module("aggregate_repo_transition",
                              "resident-runtime/aggregate_repo_transition.py")
role_conformance = _module("organization_role_conformance",
                           "resident-runtime/organization_role_conformance.py")
# The batch parent manifest is validated by its owner, the same module the
# organization append imports by name when it releases a packet.
if str(ROOT / "resident-runtime") not in sys.path:
    sys.path.insert(0, str(ROOT / "resident-runtime"))
import organization_batch_custody as batch_custody  # noqa: E402


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def boundary() -> dict[str, Any]:
    """This organization's own Interlock/InTr boundary document."""
    return json.loads(BOUNDARY.read_text(encoding="utf-8"))


def submitted_capability(manifest: Any) -> dict[str, Any]:
    """What the submission itself declared it wanted processed, or nulls.

    Read defensively, because some refusals happen before the manifest is known
    to be well formed. A submission that declared nothing records nulls rather
    than being omitted: the distinction between "declared nothing" and "we did
    not record it" is the whole value of having the field.
    """
    processing = (manifest or {}).get("processing") if isinstance(manifest, Mapping) else None
    processing = processing if isinstance(processing, Mapping) else {}
    return {
        "submitted_processing_capability": processing.get("capability"),
        "submitted_route_id": processing.get("route_id"),
        "submitted_capability_is_as_declared_by_the_submission": True,
    }


def refusal_record(failed_predicate: str, detail: str,
                   manifest: Any) -> dict[str, Any]:
    """What a refused submission records.

    The manifest reaches the chain by digest only. Nothing an admitted crossing
    would have produced appears here -- no resolved service, no boundary receipt
    chain, no runtime result -- because the organization produced none, and a
    record naming them would read as a submission that was received.

    What a refusal *does* carry is which capability's receiving operation
    refused, and what the submission declared it wanted. Those are not things an
    admitted crossing produced -- the first is a constant of this operation and
    the second is the submitter's own declaration -- and without them a
    capability that only ever refuses is indistinguishable from one nothing has
    ever exercised. `destination_resolution_source` is deliberately *not* here:
    a refusal resolved no destination, and marking it as a record that did would
    put it in a population measured for target and scope fields it correctly
    lacks.
    """
    return {
        "schema": REFUSAL_SCHEMA,
        "receiving_operation": OPERATION_ID,
        "profile_id": PROFILE_ID,
        "operation": OPERATION,
        **submitted_capability(manifest),
        "intended_action": INTENDED_ACTION,
        "disposition": "DENY",
        "transition_is_the_disposition_of_the_intended_action": True,
        "failed_predicate": failed_predicate,
        "detail": detail,
        "refusal_is_verbatim": True,
        "submitted_manifest_sha256": "sha256:" + sha(
            dict(manifest) if isinstance(manifest, Mapping) else manifest),
        "received": False,
        "retry_is_a_transition_not_a_lost_signal": True,
        "authority_effect": "NONE_REFUSAL_RECORD_ONLY",
    }


def _repository_receipt_read_back(receipt: Mapping[str, Any]) -> str | None:
    """The repository receipt's digest, only if the store returns those exact bytes.

    The receipt returned by the append is what the call *meant* to write; the
    one read back from the repository ledger store by its own digest is what
    was written. Anything short of an identical, self-verifying row is `None`.
    """
    try:
        digest = receipt["receipt_sha256"]
        store = repository_ledger.ledger_store.PosixLedgerStore(repository_ledger.lr())
        stored = store.get(repository_ledger.ledger_store.receipt_key(digest))
        body = {key: value for key, value in stored.items() if key != "receipt_sha256"}
        if stored != dict(receipt) or repository_ledger.sha(body) != digest:
            return None
        return digest
    except Exception:  # noqa: BLE001 -- any failure to read is "not observed"
        return None


def _organization_receipt_read_back(source_sha256: Any) -> tuple[Any, str | None]:
    """Whether the organization ledger holds a receipt consuming `source_sha256`.

    Read from the ledger's own HEAD and receipts directory. Every receipt read
    must verify against its own digest; a ledger that cannot be read or does
    not verify is unobserved, not uncommitted.
    """
    try:
        root = organization_ledger.ledger_root()
        head_path = root / "HEAD.json"
        head = organization_ledger.load(head_path) if head_path.exists() else None
        if head is not None and not isinstance(head.get("receipt_sha256"), str):
            return UNOBSERVED, None
        found = None
        receipts = root / "receipts"
        for path in sorted(receipts.glob("*.json")) if receipts.is_dir() else []:
            row = organization_ledger.load(path)
            body = dict(row)
            claimed = body.pop("receipt_sha256", None)
            if not isinstance(claimed, str) or claimed != organization_ledger.sha(body) \
                    or path.stem != claimed.split(":", 1)[-1]:
                return UNOBSERVED, None
            if row.get("source_transition_sha256") == source_sha256:
                found = claimed
        if head is not None and not (receipts / (head["receipt_sha256"].split(":", 1)[-1] + ".json")).is_file():
            return UNOBSERVED, None
        return (True, found) if found else (False, None)
    except Exception:  # noqa: BLE001 -- any failure to read is "not observed"
        return UNOBSERVED, None


def organization_append_not_committed(transition_id: str, repository_receipt: Mapping[str, Any],
                                      exc: BaseException, *, hb_epoch: int | None,
                                      rule_ref: str) -> dict[str, Any]:
    """The typed disposition of a repository receipt whose organization append raised.

    Each level reports only what was read back from its own store. The
    repository level is never reported uncommitted -- its append returned --
    so at worst it is unobserved; both levels are never claimed uncommitted.
    The organization *runtime* transition did not complete either way: the
    append raised before returning its record.
    """
    repository_sha256 = _repository_receipt_read_back(repository_receipt)
    organization_committed, organization_sha256 = _organization_receipt_read_back(
        repository_receipt.get("receipt_sha256") if isinstance(repository_receipt, Mapping) else None)
    variable = getattr(exc, "variable", None)
    evidence_refs = [f"transition_id:{transition_id}", f"recomputation_rule_ref:{rule_ref}",
                     f"organization_append_error_class:{type(exc).__name__}"]
    if repository_sha256:
        evidence_refs.append("repository_ledger:" + repository_ledger.ledger_store.receipt_key(repository_sha256))
    if organization_sha256:
        evidence_refs.append("organization_ledger:receipts/" + organization_sha256.split(":", 1)[-1] + ".json")
    record = {
        "schema": RESULT_SCHEMA_ORG,
        "organization": "StegVerse-Labs",
        "receiving_operation": OPERATION_ID,
        "disposition": "FAIL_CLOSED",
        "received": False,
        "failure_code": APPEND_NOT_COMMITTED,
        "failed_predicate": APPEND_NOT_COMMITTED_PREDICATE,
        "detail": f"{type(exc).__name__}: {exc}",
        "transition_id": transition_id,
        "repository_receipt_committed": True if repository_sha256 else UNOBSERVED,
        "organization_receipt_committed": organization_committed,
        "organization_runtime_transition_committed": False,
        "organization_receipt_observed": False,
        "required_evidence_or_repair": (
            "supply the organization ledger root as " + variable if variable else
            "repair the organization append's failure (" + type(exc).__name__
            + ") and resubmit the same manifest"),
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": APPEND_OWNING_GOAL,
        "next_attempt": {
            "entrypoint": RETRY_ENTRYPOINT,
            "resubmit": "THE_SAME_MANIFEST_WITH_THE_SAME_HB_EPOCH",
            # The resubmission finds the retained repository receipt and
            # completes the organization level from it, at its epoch.
            "repository_level_exact_retry": "RECORDED_RECEIPT_REUSED_NOT_DUPLICATED",
            "organization_level_exact_retry": "EXACT_SOURCE_REUSED_NOT_DUPLICATED",
            "awaits_an_external_machine": False,
        },
        "evidence_refs": evidence_refs,
        "recomputation_rule_ref": rule_ref,
        "hb_epoch": hb_epoch,
        "authority_effect": "NONE_REFUSAL_ONLY",
    }
    if repository_sha256:
        record["repository_receipt_sha256"] = repository_sha256
    if organization_sha256:
        record["organization_receipt_sha256"] = organization_sha256
    return record


def _append_both_levels(transition_id: str, transition_class: str, predecessor: str,
                        successor: str, evidence: Mapping[str, Any],
                        organization_evidence: Mapping[str, Any], *, hb_epoch: int | None,
                        parent_manifest: Mapping[str, Any] | None,
                        rule_ref: str,
                        idempotent_on: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Repository receipt first, then the organization append that consumes it.

    The organization append is the ledger's own owner,
    `aggregate_transition`, under its own lock. With `idempotent_on` a
    transition the repository chain already records is returned rather than
    minted again (a mismatch raises `ledger_receipt_collision` before anything
    is written). The organization receipt takes its epoch from the repository
    receipt it consumes, so one ingress carries one heartbeat epoch at both
    levels, and a replay completing a partial commit carries the first
    attempt's. If the organization append raises, the result is the typed
    partial-commit record.
    """
    repository_receipt = repository_ledger.append(
        transition_id, transition_class, predecessor, successor, dict(evidence),
        "NONE", hb_epoch=hb_epoch, idempotent_on=idempotent_on)
    hb_epoch = repository_receipt["hb_reference"]["epoch"]
    try:
        organization_receipt = organization_ledger.aggregate_transition(
            receipt=repository_receipt,
            org_transition_class="REPO_STATE_PROPAGATION",
            predecessor_org_state_sha256=predecessor,
            successor_org_state_sha256=successor,
            boundary_evidence=dict(organization_evidence),
            authority_effect="NONE",
            hb_epoch=hb_epoch,
            parent_manifest=dict(parent_manifest) if parent_manifest is not None else None)
    except Exception as exc:  # noqa: BLE001 -- the partial commit is the disposition
        return {"transition_id": transition_id, "repository_receipt": repository_receipt,
                "organization_receipt": None,
                "not_committed": organization_append_not_committed(
                    transition_id, repository_receipt, exc, hb_epoch=hb_epoch,
                    rule_ref=rule_ref)}
    return {"transition_id": transition_id, "repository_receipt": repository_receipt,
            "organization_receipt": organization_receipt, "not_committed": None}


def parent_manifest_applicability(request: Mapping[str, Any]) -> tuple[dict[str, Any] | None,
                                                                        dict[str, Any]]:
    """The governing batch parent manifest this admitted request declares, if any.

    Returns `(parent_manifest, organization_evidence)`. A request declaring no
    part of an organization batch is not governed by one, and its organization
    receipt says so and names what was absent. A request declaring any part
    must validate in full: a malformed or mismatched declaration raises the
    owner's own typed failure code, before anything is appended.
    """
    absent = batch_custody.organization_batch_parent_manifest_absent_predicate(request)
    if absent is not None:
        return None, {"parent_manifest_applicable": False,
                      "parent_manifest_absent_predicate": absent}
    return batch_custody.organization_batch_parent_manifest(request), {}


def _record_refusal(record: Mapping[str, Any], hb_epoch: int | None,
                    rule_ref: str, parent_manifest: Mapping[str, Any] | None = None,
                    organization_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Append a refusal at both levels, in the order the replay rule requires.

    The repository ledger records it first and the organization ledger consumes
    that receipt, exactly as an admitted submission is recorded. One writer
    standing in for both levels would leave `preserves_repo_receipt` with
    nothing to preserve -- a refusal is not an exception to that.
    """
    predecessor = record["submitted_manifest_sha256"]
    successor = "sha256:" + sha(dict(record))
    transition_id = "ORGANIZATION-SDK-MANIFEST-INGRESS-REFUSED-" + sha(dict(record))[:16]
    # A refusal is identified by its own record, so the same refusal delivered
    # again returns the receipts already recorded rather than a second pair.
    return _append_both_levels(
        transition_id, REFUSED_CLASS, predecessor, successor, record,
        {"receiving_operation": OPERATION_ID,
         "intended_action": INTENDED_ACTION,
         "disposition": "DENY",
         "failed_predicate": record["failed_predicate"],
         "recomputation_rule_ref": rule_ref,
         **dict(organization_evidence or {})},
        hb_epoch=hb_epoch, parent_manifest=parent_manifest, rule_ref=rule_ref,
        idempotent_on=("failed_predicate", "detail"))


def _refused(failed_predicate: str, detail: str, *, manifest: Any, rule_ref: str,
             hb_epoch: int | None = None, parent_manifest: Mapping[str, Any] | None = None,
             organization_evidence: Mapping[str, Any] | None = None,
             **extra: Any) -> dict[str, Any]:
    record = refusal_record(failed_predicate, detail, manifest)
    appended = _record_refusal(record, hb_epoch, rule_ref, parent_manifest,
                               organization_evidence)
    if appended["not_committed"] is not None:
        # The refusal reached the repository ledger and not the organization
        # ledger. Its own predicate is kept under its own name.
        return {**appended["not_committed"],
                "refusal_failed_predicate": failed_predicate,
                "refusal_detail": detail,
                "refusal_transition_class": REFUSED_CLASS,
                "refusal_transition_id": appended["transition_id"],
                "refusal_recorded": False,
                **extra}
    return {
        "schema": RESULT_SCHEMA_ORG,
        "organization": "StegVerse-Labs",
        "receiving_operation": OPERATION_ID,
        "disposition": "FAIL_CLOSED",
        "received": False,
        "failed_predicate": failed_predicate,
        "detail": detail,
        # The refusal is recorded at both levels. `organization_receipt_observed`
        # stays false regardless: it means an admitted crossing was observed, and
        # a refusal receipt is not that. A caller reading it as one would treat a
        # refused submission as a completed transition.
        "organization_receipt_observed": False,
        "refusal_recorded": True,
        "refusal_transition_class": REFUSED_CLASS,
        "refusal_intended_action": INTENDED_ACTION,
        "refusal_transition_id": appended["transition_id"],
        "recomputation_rule_ref": rule_ref,
        "refusal_repository_receipt_sha256":
            appended["repository_receipt"]["receipt_sha256"],
        "refusal_organization_receipt_sha256":
            appended["organization_receipt"]["receipt_sha256"],
        "authority_effect": "NONE_REFUSAL_ONLY",
        **extra,
    }


def bound_here(request: Mapping[str, Any]) -> dict[str, Any]:
    """Confirm the SDK resolved this capability to this operation, in this repository.

    The resolution comes back on the request. Reading it rather than assuming it
    means a manifest bound to another organization is refused here instead of
    being received by the wrong receiver.
    """
    resolution = request.get("manifest_declared_destination")
    if not isinstance(resolution, Mapping):
        raise ValueError("ORGANIZATION_INGRESS_RESOLUTION_ABSENT_FROM_REQUEST")
    if (resolution.get("profile_id"), resolution.get("profile_name"),
            resolution.get("operation")) != (PROFILE_ID, PROFILE_NAME, OPERATION):
        raise ValueError("ORGANIZATION_INGRESS_RESOLVED_A_DIFFERENT_CAPABILITY")
    receiving = resolution.get("receiving_operation")
    if not isinstance(receiving, Mapping):
        raise ValueError("ORGANIZATION_RECEIVING_OPERATION_ABSENT")
    if receiving.get("owner_repository") != OWNER_REPOSITORY:
        raise ValueError("ORGANIZATION_RECEIVING_OPERATION_OWNED_ELSEWHERE")
    if receiving.get("operation_id") != OPERATION_ID:
        raise ValueError("ORGANIZATION_RECEIVING_OPERATION_IS_NOT_THIS_ONE")
    return dict(receiving)


def reconstruct_closures(crossing: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Recompute every boundary receipt from its own subject, and chain them.

    The boundary reports `RECONSTRUCTED`. Repeating its computation here is what
    makes that reportable rather than merely asserted: each receipt's digest is
    recomputed from the packet, the service, the payload digest, its kind and
    its declared predecessor, and a receipt whose declared digest or id does not
    match what the subject produces fails the whole chain closed.
    """
    receipts = crossing.get("boundary_receipts")
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("BOUNDARY_RECEIPT_CHAIN_ABSENT")
    base = {"packet_id": crossing["ingress_packet_id"],
            "service_id": crossing["resolved_service_id"],
            "payload_hash": crossing["payload_hash"]}
    closures: list[dict[str, Any]] = []
    previous_id: str | None = None
    previous_digest: str | None = None
    for receipt in receipts:
        kind = receipt.get("kind")
        if not isinstance(kind, str) or not kind:
            raise ValueError("BOUNDARY_RECEIPT_KIND_INVALID")
        if receipt.get("previous_receipt_id") != previous_id:
            raise ValueError("BOUNDARY_RECEIPT_CHAIN_PREDECESSOR_MISMATCH:" + kind)
        digest = sha({**base, "kind": kind, "previous_receipt_id": previous_id})
        if receipt.get("evidence_hash") != digest:
            raise ValueError("BOUNDARY_RECEIPT_RECONSTRUCTION_MISMATCH:" + kind)
        if receipt.get("receipt_id") != kind.lower() + "-" + digest[:24]:
            raise ValueError("BOUNDARY_RECEIPT_ID_NOT_DERIVED_FROM_ITS_EVIDENCE:" + kind)
        closure = {"transition_id": kind, "state": "RECORDED",
                   "reconstruction_status": "PASS",
                   "required_evidence_validation_status": "PASS",
                   "receipt_sha256": digest, "reconstructed_receipt_sha256": digest}
        if previous_digest is not None:
            closure["predecessor_receipt_sha256"] = previous_digest
        closures.append(closure)
        previous_id, previous_digest = receipt["receipt_id"], digest
    if previous_id != crossing.get("terminal_receipt_id"):
        raise ValueError("BOUNDARY_TERMINAL_RECEIPT_DOES_NOT_CLOSE_THE_CHAIN")
    return closures


#: The fields of a crossing that name the packets carrying one delivery. They are
#: transport: a redelivery of the same manifest is carried by other packets, and
#: that does not make it another transition.
DELIVERY_FIELDS = ("ingress_packet_id", "egress_packet_id")


def delivery_evidence(crossing: Mapping[str, Any]) -> dict[str, Any]:
    """The packets that carried this delivery, as the crossing names them."""
    return {field: crossing[field] for field in DELIVERY_FIELDS}


def recorded_delivery_evidence(prior: Mapping[str, Any]) -> dict[str, Any]:
    """The delivery a recorded transition was committed under, re-derived from its receipt.

    The repository receipt carries that delivery's crossing inline. Its boundary
    receipt chain is reconstructed again here and must close on the receipt's
    own closures and recorded successor, so the packet ids returned are the ones
    the recorded transition was actually carried by, not ones taken on the
    record's word.
    """
    evidence = prior.get("evidence") if isinstance(prior.get("evidence"), Mapping) else {}
    crossing = evidence.get("crossing")
    if not isinstance(crossing, Mapping) or any(field not in crossing for field in DELIVERY_FIELDS):
        raise ValueError("RECORDED_DELIVERY_EVIDENCE_ABSENT")
    closures = reconstruct_closures(crossing)
    if (evidence.get("transition_closures") != closures
            or prior.get("successor_state_sha256") != "sha256:" + closures[-1]["receipt_sha256"]):
        raise ValueError("RECORDED_DELIVERY_EVIDENCE_DOES_NOT_RECONSTRUCT")
    return delivery_evidence(crossing)


def delivery_attempt(crossing: Mapping[str, Any], recorded: Mapping[str, Any]) -> dict[str, Any]:
    """This delivery's packets, reported beside the transition and never part of its identity.

    Its boundary receipt chain was reconstructed from its own packet before
    anything was appended, so the ids are independently verifiable. When the
    transition was already recorded under another delivery, the receipt keeps
    the packets that committed it and this delivery is reported here only.
    """
    this_delivery = delivery_evidence(crossing)
    return {**this_delivery,
            "boundary_receipt_chain_reconstructed_independently": True,
            "transition_identity_role": "NON_IDENTITY_DELIVERY_EVIDENCE",
            "recorded_delivery": dict(recorded),
            "is_the_recorded_delivery": this_delivery == dict(recorded)}


def ingress_transition_id(request: Mapping[str, Any],
                          conformance: Mapping[str, Any] | None = None) -> str:
    """The transition id: the request, and for role conformance its evaluation.

    Nothing the carrier chose enters it. A role-conformance evaluation is part
    of the transition's identity: an exact retry against the same source is the
    same transition, and a resubmission after the source changed is a new one
    rather than a collision with the first.
    """
    transition_id = "ORGANIZATION-SDK-MANIFEST-INGRESS-" + request["request_sha256"][:16]
    if conformance is not None:
        transition_id += "-" + sha(conformance)[:16]
    return transition_id


def transition_evidence(request: Mapping[str, Any], crossing: Mapping[str, Any],
                        closures: list[dict[str, Any]]) -> dict[str, Any]:
    """What this ingress transition is evidenced by, inline.

    Replay reads these bytes rather than following a reference, because a
    reachability promise is not evidence.
    """
    return {
        "receiving_operation": OPERATION_ID,
        "profile_id": PROFILE_ID,
        "profile_name": PROFILE_NAME,
        "operation": OPERATION,
        "destination_resolution_source": request.get("destination_resolution_source"),
        "request_sha256": request["request_sha256"],
        "wire_manifest_sha256": request["wire_manifest_sha256"],
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "graph_id": request["graph_id"],
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "crossing": {key: value for key, value in crossing.items() if key != "egress"},
        "transition_closures": closures,
    }


def runtime_result(request: Mapping[str, Any], closures: list[dict[str, Any]],
                   organization_receipt: Mapping[str, Any],
                   decision: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """What this organization observed, in the shape the SDK validates.

    `manifest_receipt_id` is the organization receipt's own digest. The receipt
    is the organization's runtime reality, so the result is bound to the receipt
    that exists rather than to an identifier minted for the occasion.
    """
    return {
        "schema": RESULT_SCHEMA,
        "state": "COMPLETE",
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "graph_id": request["graph_id"],
        "canonical_task_id": request["canonical_task_id"],
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "resolved_ordered_transitions": [closure["transition_id"] for closure in closures],
        "transition_closures": closures,
        "replay_status": ORGANIZATION_REPLAY,
        "reconstruction_status": "PASS",
        "terminal_state": {"records_only": True, "continued_authority": False},
        "manifest_receipt_id": organization_receipt["receipt_sha256"],
        **governance_fields(request, decision),
    }


def governance_fields(request: Mapping[str, Any], decision: Mapping[str, Any] | None) -> dict[str, Any]:
    """The governance decision, in the shape the SDK admits, recorded in org records only.

    Only a governance request carries a decision. The disposition is the one the
    organization's governance endpoint returned; nothing here grades it.
    """
    if request.get("processing_capability") != "governance":
        return {}
    disposition = (decision or {}).get("disposition")
    if disposition not in {"ALLOW", "DENY", "FAIL_CLOSED"}:
        disposition = "FAIL_CLOSED"
    return {
        "disposition": disposition,
        "state": "COMPLETE" if disposition == "ALLOW" else disposition,
        "terminal": disposition != "ALLOW",
        "communication_terminal": False,
        "failed_predicate": None if disposition == "ALLOW" else (
            (decision or {}).get("reason") or "GOVERNANCE_DECISION_ABSENT"),
        "governance_decision": dict(decision) if decision else None,
        "request_sha256": request["request_sha256"],
        "wire_manifest_sha256": request["wire_manifest_sha256"],
        "records_authority": "ORGANIZATION_RECORDS_ONLY",
        "publisher_executed": False,
        "site_propagation_executed": False,
    }


def request_digest(value: Any) -> str:
    """A governance request's digest, in the encoding both organizations bind it with."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def governance_request_payload(request: Mapping[str, Any], decision_request: Mapping[str, Any],
                               transition_id: str) -> dict[str, Any]:
    """The work request that carries a governance request to the organization that decides it.

    `ecosystem.work.request` is answered with an acknowledgement, and the
    communication id is what the closure correlates on, so the crossing is
    closable by construction.

    It carries the admitted manifest's own `processing` declaration. The
    deciding organization's governance endpoint is an internal endpoint, and
    an internal endpoint refuses a packet that declares no admitted capability
    bound to a route rather than letting the addressed row select processing.
    """
    return {
        "communication_id": "governance:" + request["request_sha256"],
        "message_class": "ecosystem.work.request",
        "processing": {"capability": request["processing_capability"],
                       "route_id": request["route_id"]},
        "subject": "governance.decision",
        "requested_action": "DECIDE_GOVERNANCE_ADMISSIBILITY",
        "audience": "TARGET",
        "target_organization": decision_request["deciding_organization"],
        "target_count": 1,
        "body": {
            "schema": GOVERNANCE_REQUEST_SCHEMA,
            "origin_organization": "StegVerse-Labs",
            "sdk_request_sha256": request["request_sha256"],
            "canonical_manifest_sha256": request["canonical_manifest_sha256"],
            "ingress_transition_id": transition_id,
            "governance_request": decision_request["governance_request"],
            "governance_request_sha256": decision_request["governance_request_sha256"],
        },
    }


def request_governance_decision(request: Mapping[str, Any], crossing: Mapping[str, Any],
                                receiving: Mapping[str, Any], *, transition_id: str,
                                repository_receipt: Mapping[str, Any],
                                organization_receipt: Mapping[str, Any],
                                standing: Mapping[str, Any], mesh_root: Path | None,
                                hb_epoch: int | None, rule_ref: str,
                                replayed: bool = False) -> dict[str, Any]:
    """Emit the governance request to the organization that decides it, and record the emission.

    Nothing waits. The emission is a transition here, recorded at both levels by
    the egress boundary; the decision is a transition there; its return is a
    third, recorded here when it arrives. A receiver that is not running leaves
    the frame in the mesh, which is the durable queue.
    """
    decision_request = crossing.get("application_result") or {}
    base = {
        "schema": RESULT_SCHEMA_ORG,
        "organization": "StegVerse-Labs",
        "receiving_operation": OPERATION_ID,
        "received": True,
        "owner_repository": OWNER_REPOSITORY,
        "resolved_service_id": crossing["resolved_service_id"],
        "destination_resolution_source": request["destination_resolution_source"],
        "destination_resolution_environment_inputs": [],
        "receiving_operation_declared": dict(receiving),
        "request_sha256": request["request_sha256"],
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "intr_admission_observed": True,
        "far_side_transition_observed": True,
        "boundary_receipt_chain_reconstructed_independently": True,
        "organization_receipt_observed": True,
        "organization_receipt_sha256": organization_receipt["receipt_sha256"],
        "organization_transition_id": transition_id,
        "transition_replayed": replayed,
        "recomputation_rule_ref": rule_ref,
        "repository_receipt_observed": True,
        "repository_receipt_sha256": repository_receipt["receipt_sha256"],
        "records_authority": "ORGANIZATION_RECORDS_ONLY",
        "master_records_organization_record_observed": False,
    }
    if (decision_request.get("schema") != GOVERNANCE_REQUEST_SCHEMA
            or decision_request.get("governance_request_sha256") != request_digest(decision_request.get("governance_request"))):
        return {**base, "disposition": "FAIL_CLOSED",
                "failed_predicate": "GOVERNANCE_REQUEST_IS_BOUND_TO_THE_SUBMITTED_MANIFEST",
                "detail": "the governance processor returned no request bound to this manifest",
                "retry_entrypoint": "resident-runtime/organization_manifest_ingress.py::receive",
                "authority_effect": "NONE_REFUSAL_ONLY"}

    egress = _module("organization_egress_boundary", "resident-runtime/organization_egress_boundary.py")
    emitted = egress.emit(decision_request["deciding_organization"],
                          governance_request_payload(request, decision_request, transition_id),
                          standing=dict(standing), capability="governance",
                          transition_reference="ecosystem.transition.governance.v1",
                          mesh_root=mesh_root, hb_epoch=hb_epoch)
    emission = {key: emitted.get(key) for key in (
        "emission_transition_class", "emission_repository_receipt_sha256",
        "emission_organization_receipt_sha256")}
    if emitted["disposition"] != "ALLOW":
        # Recorded by the egress boundary as a refused emission. The ingress
        # transition stands; the request did not leave, and says why.
        return {**base, **emission, "disposition": "FAIL_CLOSED",
                "failed_predicate": emitted.get("failed_predicate"),
                "detail": emitted.get("detail"),
                "governance_decision_state": "REQUEST_NOT_EMITTED",
                "required_evidence_or_repair": (
                    "materialize this node with its federation mesh location"
                    if "mesh_location_required" in str(emitted.get("detail"))
                    else "satisfy the egress boundary's failed predicate: "
                         + str(emitted.get("failed_predicate"))),
                "retry_entrypoint": "resident-runtime/organization_manifest_ingress.py::receive",
                "authority_effect": "NONE_REFUSAL_ONLY"}
    return {**base, **emission,
            "disposition": "ALLOW",
            "governance_decision_state": "REQUESTED_OF_DECIDING_ORGANIZATION",
            "deciding_organization": emitted["destination_organization"],
            "deciding_service": emitted["destination_service"],
            "decision_authority": decision_request["decision_authority"],
            "decision_authority_repository": decision_request["decision_authority_repository"],
            "evaluator_imported_in_this_organization": False,
            "governance_request_packet_id": emitted["packet_id"],
            "governance_communication_id": emitted["communication_id"],
            "governance_request_sha256": decision_request["governance_request_sha256"],
            "awaits_the_decision": False,
            "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
            "sdk_admission": "AT_DECISION_RETURN",
            "decision_return_entrypoint": "resident-runtime/governance_decision_return.py::return_decision",
            "authority_effect": "NONE_RECEIVING_OPERATION_ONLY"}


def role_conformance_disposition(crossing: Mapping[str, Any]) -> dict[str, Any]:
    """The conformance evaluation the crossing returned, bound to the manifest it carried.

    The evaluation is the organization's own adapter reading its own source.
    A result that is not that adapter's schema, not bound to the manifest
    digest this crossing carried, or carries no terminal disposition is not
    used: the transition is then FAIL_CLOSED, naming that.
    """
    result = crossing.get("application_result")
    if (not isinstance(result, Mapping) or result.get("schema") != role_conformance.RESULT_SCHEMA
            or result.get("manifest_sha256") != crossing.get("manifest_sha256")
            or result.get("disposition") not in {"ALLOW", "DENY", "FAIL_CLOSED"}):
        return {"disposition": "FAIL_CLOSED",
                "failed_predicate": "ROLE_CONFORMANCE_EVALUATION_IS_BOUND_TO_THE_SUBMITTED_MANIFEST",
                "detail": "the conformance processor returned no evaluation bound to this manifest",
                "retry_entrypoint": RETRY_ENTRYPOINT}
    return {key: result[key] for key in (
        "disposition", "failed_predicate", "detail", "issuer", "destination_organization",
        "manifest_binding", "target_role_version_id", "target_contract_digest", "target_reference",
        "compared_files", "differing_files", "required_evidence_or_repair", "retry_entrypoint",
        "next_attempt", "source_mutated") if key in result}


def role_conformance_result(request: Mapping[str, Any], crossing: Mapping[str, Any],
                            conformance: Mapping[str, Any], *, transition_id: str,
                            repository_receipt: Mapping[str, Any],
                            organization_receipt: Mapping[str, Any],
                            rule_ref: str, replayed: bool) -> dict[str, Any]:
    """The terminal disposition the organization ledger now holds for this request.

    The append is the transition: ALLOW, DENY and FAIL_CLOSED are each
    committed, and nothing further is observed or awaited.
    """
    return {
        "schema": RESULT_SCHEMA_ORG,
        "organization": "StegVerse-Labs",
        "receiving_operation": OPERATION_ID,
        "received": True,
        **dict(conformance),
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "request_sha256": request["request_sha256"],
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "resolved_service_id": crossing["resolved_service_id"],
        "intr_admission_observed": True,
        "far_side_transition_observed": True,
        "boundary_receipt_chain_reconstructed_independently": True,
        "organization_receipt_observed": True,
        "organization_receipt_sha256": organization_receipt["receipt_sha256"],
        "organization_transition_id": transition_id,
        "transition_replayed": replayed,
        "recomputation_rule_ref": rule_ref,
        "repository_receipt_observed": True,
        "repository_receipt_sha256": repository_receipt["receipt_sha256"],
        "organization_receipt_preserves_repository_receipt":
            organization_receipt["repo_receipt_sha256"] == repository_receipt["receipt_sha256"],
        "disposition_committed_in_organization_ledger": True,
        "owning_existing_goals": [role_conformance.AUTHORIZED_ISSUER_TASK_ID, APPEND_OWNING_GOAL],
        "master_records_organization_record_observed": False,
        "authority_effect": "NONE_RECEIVING_OPERATION_ONLY",
    }


#: The predicates an organization-role conformance manifest is admitted on by
#: the pinned SDK, in the order they are checked, before the organization's own
#: issuer, destination, binding, version and file-digest predicates.
ROLE_CONFORMANCE_SHAPE_PREDICATE = "SDK_ADMITS_THE_ROLE_CONFORMANCE_MANIFEST_SHAPE"
ROLE_CONFORMANCE_ROUTE_PREDICATE = "SDK_RESOLVES_THE_DECLARED_ROLE_CONFORMANCE_ROUTE"
ROLE_CONFORMANCE_DERIVATION_PREDICATE = "SDK_DERIVES_THE_ROLE_CONFORMANCE_REQUEST_FROM_ITS_EXTENSION"


def declares_role_conformance(manifest: Any) -> bool:
    """Whether the submission asks, in any shape, for organization-role conformance."""
    if not isinstance(manifest, Mapping):
        return False
    processing = manifest.get("processing") if isinstance(manifest.get("processing"), Mapping) else {}
    extensions = manifest.get("extensions") if isinstance(manifest.get("extensions"), Mapping) else {}
    route = extensions.get(role_conformance.ROUTE_DECLARATION_EXTENSION)
    return (processing.get("capability") == role_conformance.CAPABILITY
            or processing.get("route_id") == role_conformance.ROUTE_ID
            or (isinstance(route, Mapping) and route.get("route_id") == role_conformance.ROUTE_ID)
            or role_conformance.REQUEST_EXTENSION in extensions
            or role_conformance.CAPABILITY in manifest)


def admit_role_conformance_shape(manifest: Mapping[str, Any]) -> tuple[str, str] | None:
    """None when the pinned SDK admits this as a role-conformance manifest; else (predicate, detail).

    The SDK is the authority on the shape: `validate_ingress_manifest` admits
    the wire manifest (and refuses the request as a top-level field),
    `route_from_manifest` resolves `extensions.stegverse_route` to the published
    route, and `derive_execution_request` derives the request from
    `extensions.stegverse_organization_role_conformance_request`. Only then are
    the organization's own predicates evaluated.
    """
    try:
        canonical = validate_ingress_manifest(manifest)
    except ValueError as exc:
        return ROLE_CONFORMANCE_SHAPE_PREDICATE, str(exc)
    try:
        route = route_from_manifest(canonical)
    except ValueError as exc:
        return ROLE_CONFORMANCE_ROUTE_PREDICATE, str(exc)
    declared = (route.get("route_id"), route.get("processor_capability"))
    if declared != (role_conformance.ROUTE_ID, role_conformance.CAPABILITY):
        return ROLE_CONFORMANCE_ROUTE_PREDICATE, (
            f"declared route {declared[0]} ({declared[1]}) is not "
            f"{role_conformance.ROUTE_ID} ({role_conformance.CAPABILITY})")
    try:
        request = derive_execution_request(manifest)
    except ValueError as exc:
        return ROLE_CONFORMANCE_DERIVATION_PREDICATE, str(exc)
    graph = request.get("state_graph") if isinstance(request.get("state_graph"), Mapping) else {}
    if ((request.get("route_id"), request.get("processing_capability"))
            != (role_conformance.ROUTE_ID, role_conformance.CAPABILITY)
            or graph.get("request") != role_conformance.manifest_request(manifest)):
        return ROLE_CONFORMANCE_DERIVATION_PREDICATE, (
            "the derived request is not the role-conformance request the manifest carries")
    return None


def receive(manifest: Mapping[str, Any], *, registry: Mapping[str, Any], standing: Mapping[str, Any] | None = None,
            packet_id: str = "organization-sdk-manifest-ingress",
            hb_epoch: int | None = None, mesh_root: Path | None = None) -> dict[str, Any]:
    """Receive a submitted manifest on this organization's ingress operation.

    `mesh_root` is the federation mesh the node was materialized with. Only a
    capability another organization decides needs it: the request leaves on it.
    """
    # Resolved before anything is appended: an unresolvable revision fails
    # closed here, with no receipt written that could not name its rule.
    rule_ref = recomputation_rule_ref()
    refused = functools.partial(_refused, manifest=manifest, hb_epoch=hb_epoch,
                                rule_ref=rule_ref)
    # A role-conformance manifest is admitted by the pinned SDK on its published
    # route before anything else: a shape the SDK does not admit is refused and
    # recorded with the SDK's own reason, never reinterpreted here.
    if declares_role_conformance(manifest):
        inadmissible = admit_role_conformance_shape(manifest)
        if inadmissible is not None:
            return refused(*inadmissible)
        # Standing on this route is the destination's declaration for its
        # authorized issuer, read from the registry row that admits the route.
        # Neither the issuer nor the consumer supplies it: none declared is the
        # crossing's own refusal, and a supplied standing is admitted only when
        # it is exactly the declaration.
        declared, gap = role_conformance.declared_standing(manifest, registry)
        if declared is None:
            return refused("CROSSING_IS_DRIVABLE_FROM_THE_MANIFEST_AS_DECLARED",
                           "CROSSING_REQUIRES_DECLARED_STANDING:" + gap)
        if standing is not None and dict(standing) != declared:
            return refused("CROSSING_IS_DRIVABLE_FROM_THE_MANIFEST_AS_DECLARED",
                           "CROSSING_REQUIRES_DECLARED_STANDING:the submission supplied standing "
                           "other than the destination's declaration for its issuer")
        standing = declared
    try:
        request = derive_execution_request(manifest, boundary())
    except ValueError as exc:
        return refused("ORGANIZATION_RESOLVES_ITS_OWN_INGRESS_DESTINATION", str(exc))
    try:
        receiving = bound_here(request)
    except ValueError as exc:
        return refused("CAPABILITY_IS_BOUND_TO_THIS_RECEIVING_OPERATION", str(exc),
                       request_sha256=request.get("request_sha256"))

    # Whether a governing batch parent manifest applies is decided from the
    # admitted request, before anything is appended. A declaration that does
    # not validate is refused with its owner's own failure code.
    try:
        parent_manifest, organization_evidence = parent_manifest_applicability(request)
    except ValueError as exc:
        return refused(PARENT_MANIFEST_INVALID_PREDICATE, str(exc), failure_code=str(exc),
                       request_sha256=request.get("request_sha256"))
    refused = functools.partial(refused, parent_manifest=parent_manifest,
                                organization_evidence=organization_evidence)

    try:
        crossing = crossing_module.cross(manifest, registry=dict(registry), standing=standing, packet_id=packet_id)
    except SystemExit as exc:
        # The crossing refuses a manifest it cannot drive as declared -- no
        # egress, a non-InTr transport, an unresolvable surface, no declared
        # standing. Those are dispositions of this submission, so they are
        # recorded here rather than leaving the operation by exception with
        # nothing written.
        return refused("CROSSING_IS_DRIVABLE_FROM_THE_MANIFEST_AS_DECLARED", str(exc))
    if not crossing.get("crossing_completed"):
        # The far side refused. That is its disposition to state, not something
        # this operation rewrites into an admission -- but the submission still
        # arrived here, so the refusal is recorded.
        return refused("ADMITTED_CROSSING_REACHES_ITS_INTERNAL_ENDPOINT",
                       str(crossing.get("far_side_disposition")),
                       request_sha256=request["request_sha256"],
                       resolved_service_id=crossing.get("resolved_service_id"),
                       crossing=crossing)

    try:
        closures = reconstruct_closures(crossing)
    except ValueError as exc:
        return refused("BOUNDARY_RECEIPT_CHAIN_RECONSTRUCTS_INDEPENDENTLY", str(exc),
                       request_sha256=request["request_sha256"])

    # The transition occurred in this repository, so the repository ledger
    # records it first and the organization ledger consumes that receipt. The
    # organization authoring its own source receipt and then recording it as its
    # own was one writer standing in for two levels: it left
    # `preserves_repo_receipt` with nothing to preserve, and left organization
    # replay resting on a receipt the same call had just minted, when the
    # replay rule asks for verified repo receipts beneath the organization ones.
    # A role-conformance request's disposition is the organization's own source
    # evaluated against the target digests, so it is committed in the
    # organization receipt itself.
    conformance = None
    ingress_evidence = dict(organization_evidence)
    if request.get("processing_capability") == role_conformance.CAPABILITY:
        conformance = role_conformance_disposition(crossing)
        ingress_evidence.update({
            "role_conformance_disposition": conformance["disposition"],
            "role_conformance_failed_predicate": conformance.get("failed_predicate"),
            "role_conformance_target_role_version_id": conformance.get("target_role_version_id"),
            "role_conformance_target_contract_digest": conformance.get("target_contract_digest"),
            "role_conformance_differing_files": [
                row["path"] for row in conformance.get("differing_files") or []],
            "role_conformance_evaluation_sha256": "sha256:" + sha(conformance)})
    transition_id = ingress_transition_id(request, conformance)
    predecessor_state = "sha256:" + request["canonical_manifest_sha256"]
    successor_state = "sha256:" + closures[-1]["receipt_sha256"]
    #
    # The transition id is derived from the request, so one manifest is one
    # transition however many times it is delivered. A delivery the chain
    # already records returns the recorded receipts instead of minting more:
    # identity is the id, the canonical manifest it starts from and the full
    # request digest; the same id over anything else is a collision. A run that
    # recorded the repository receipt and stopped before the organization
    # receipt is completed here, from the retained repository receipt, rather
    # than recorded twice.
    chain = repository_ledger.ledger_store.PosixLedgerStore(repository_ledger.lr())
    # The successor state is the last closure of the crossing that carried the
    # manifest, and a redelivery is carried again: another packet, another
    # closure. The repository ledger compares the successor on every exact
    # retry, so a redelivery of the request already recorded names the
    # successor that delivery recorded rather than its own carrier's. A
    # different request under this id keeps its own successor and collides.
    # The lookup is read again after a collision once, because a concurrent
    # delivery of the same request may have recorded it in between.
    #
    # The packet ids are the same kind of carrier fact. The organization
    # receipt names the packets that committed the transition, and an exact
    # retry there compares its whole boundary evidence, so a redelivery names
    # the recorded delivery's packets -- re-derived from the recorded
    # repository receipt, not taken from it -- and reports its own packets
    # beside the result as non-identity delivery evidence. Everything else the
    # organization receipt binds (receiving operation, resolved service, rule,
    # disposition, authority effect, successor) is still compared in full.
    evidence = transition_evidence(request, crossing, closures)
    for resolution in range(2):
        prior = repository_ledger.recorded(
            chain, chain.get(repository_ledger.ledger_store.HEAD_KEY),
            transition_id, OPERATION_ID)
        replayed = prior is not None
        recorded_delivery = delivery_evidence(crossing)
        if replayed and (prior.get("evidence") or {}).get("request_sha256") == request["request_sha256"]:
            successor_state = prior["successor_state_sha256"]
            try:
                recorded_delivery = recorded_delivery_evidence(prior)
            except ValueError as exc:
                return refused("RECORDED_DELIVERY_RECONSTRUCTS_INDEPENDENTLY", str(exc),
                               request_sha256=request["request_sha256"])
        try:
            appended = _append_both_levels(
                transition_id, OPERATION_ID,
                predecessor_state, successor_state, evidence,
                {"receiving_operation": OPERATION_ID,
                 "resolved_service_id": crossing["resolved_service_id"],
                 **recorded_delivery,
                 "recomputation_rule_ref": rule_ref,
                 **ingress_evidence},
                hb_epoch=hb_epoch, parent_manifest=parent_manifest, rule_ref=rule_ref,
                idempotent_on=("request_sha256",))
            break
        except ValueError as exc:
            if str(exc) != "ledger_receipt_collision":
                raise
            if resolution:
                return refused("ONE_TRANSITION_ID_BINDS_ONE_MANIFEST", str(exc),
                               request_sha256=request["request_sha256"])
    delivery = delivery_attempt(crossing, recorded_delivery)
    if appended["not_committed"] is not None:
        return {**appended["not_committed"],
                "request_sha256": request["request_sha256"],
                "intr_admission_observed": True,
                "far_side_transition_observed": True,
                "transition_replayed": replayed,
                "delivery_attempt": delivery}
    repository_receipt = appended["repository_receipt"]
    organization_receipt = appended["organization_receipt"]
    # Everything after the repository receipt takes its epoch from that receipt,
    # so a replay rebuilds the same organization receipt and the same outbound
    # frame rather than ones stamped with whatever epoch this attempt carried.
    hb_epoch = repository_receipt["hb_reference"]["epoch"]

    if conformance is not None:
        return {**role_conformance_result(
            request, crossing, conformance, transition_id=transition_id,
            repository_receipt=repository_receipt, organization_receipt=organization_receipt,
            rule_ref=rule_ref, replayed=replayed), "delivery_attempt": delivery}

    # Governance is decided by the organization that owns StegCore. The ingress
    # transition above occurred here and is recorded; the request now leaves
    # through this organization's egress, and the SDK is handed the decision
    # when it returns, not before.
    if request.get("processing_capability") == "governance":
        return {**request_governance_decision(
            request, crossing, receiving, transition_id=transition_id,
            repository_receipt=repository_receipt, organization_receipt=organization_receipt,
            standing=crossing_module.manifest_standing(manifest, standing),
            mesh_root=mesh_root, hb_epoch=hb_epoch, rule_ref=rule_ref, replayed=replayed),
            "delivery_attempt": delivery}

    # The SDK decides whether this closes the transition. Its refusal is the
    # answer, returned as it was given.
    try:
        admitted = admit_runtime_result(
            manifest, request, runtime_result(request, closures, organization_receipt,
                           crossing.get("application_result")))
    except ValueError as exc:
        return {
            "schema": RESULT_SCHEMA_ORG,
            "organization": "StegVerse-Labs",
            "receiving_operation": OPERATION_ID,
            "disposition": "FAIL_CLOSED",
            "received": True,
            "failed_predicate": "SDK_ADMITS_THE_ORGANIZATION_RUNTIME_RESULT",
            "detail": str(exc),
            # The receipt was appended before the SDK was asked. The organization
            # ledger is its own runtime reality authority, so a refusal upstream
            # does not unmake a transition that occurred here.
            "organization_receipt_observed": True,
            "organization_receipt_sha256": organization_receipt["receipt_sha256"],
            "organization_transition_id": transition_id,
            "recomputation_rule_ref": rule_ref,
            "repository_receipt_sha256": repository_receipt["receipt_sha256"],
            "request_sha256": request["request_sha256"],
            "delivery_attempt": delivery,
            "authority_effect": "NONE_REFUSAL_ONLY",
        }

    return {
        "schema": RESULT_SCHEMA_ORG,
        "organization": "StegVerse-Labs",
        "receiving_operation": OPERATION_ID,
        "disposition": "ALLOW",
        "received": True,
        "owner_repository": OWNER_REPOSITORY,
        "resolved_service_id": crossing["resolved_service_id"],
        "destination_resolution_source": request["destination_resolution_source"],
        "destination_resolution_environment_inputs": [],
        "receiving_operation_declared": receiving,
        "request_sha256": request["request_sha256"],
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "intr_admission_observed": True,
        "far_side_transition_observed": True,
        "boundary_receipt_chain_reconstructed_independently": True,
        "transition_closures": closures,
        "delivery_attempt": delivery,
        "organization_receipt_observed": True,
        "organization_receipt_sha256": organization_receipt["receipt_sha256"],
        "organization_transition_id": transition_id,
        "transition_replayed": replayed,
        "recomputation_rule_ref": rule_ref,
        # Both levels, so a reader can see the organization consumed a receipt
        # from the level below rather than one it wrote itself.
        "repository_receipt_observed": True,
        "repository_receipt_sha256": repository_receipt["receipt_sha256"],
        "repository": repository_receipt["repository"],
        "organization_receipt_preserves_repository_receipt":
            organization_receipt["repo_receipt_sha256"] == repository_receipt["receipt_sha256"],
        "replay_requires_only_verified_repo_and_organization_receipts": True,
        "sdk_admitted_result": admitted,
        # Custody is published separately and is not awaited here:
        # `propagation_gates_organization_runtime_reality` is false and Master
        # Records `may_be_awaited_by_a_transition` is false.
        "master_records_organization_record_observed": False,
        "master_records_propagation_entrypoint":
            "resident-runtime/submit_org_transition_to_master_records.py",
        "authority_effect": "NONE_RECEIVING_OPERATION_ONLY",
    }


#: The durable intr-outbox route a role-conformance request is held on until
#: this organization consumes it: `<durable root>/intr-outbox/<route>/*.json`,
#: the same layout as every other intr-outbox route.
ROLE_CONFORMANCE_OUTBOX_ROUTE = "organization-role-conformance"
OUTBOX_EVENT_SCHEMA = "stegverse.intr-outbox-manifest-event/v1"
OUTBOX_CONSUMPTION_SCHEMA = "stegverse.organization-manifest-ingress-outbox-consumption/v1"
LEDGER_ROOT_VARIABLES = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")


def consume_outbox(durable_root: Path, *, registry: Mapping[str, Any],
                   route: str = ROLE_CONFORMANCE_OUTBOX_ROUTE, mesh_root: Path | None = None,
                   environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Receive every manifest event held on one intr-outbox route.

    Consumed by event: an empty or absent route is NO_EVENT, and holding is
    never itself a disposition. Each event is one `receive`, so each commits
    its own terminal disposition, and redelivering an event is the exact retry
    the ledgers already make idempotent. Nothing is received until the
    materializer has supplied both ledger roots; until then the events stay
    where they are and nothing is appended.
    """
    environ = os.environ if environ is None else environ
    base = {"schema": OUTBOX_CONSUMPTION_SCHEMA, "route": route, "authority_effect": "NONE"}
    outbox = Path(durable_root) / "intr-outbox" / route
    events = sorted(outbox.glob("*.json")) if outbox.is_dir() else []
    if not events:
        return {**base, "state": "NO_EVENT", "event_count": 0}
    missing = [name for name in LEDGER_ROOT_VARIABLES if not (environ.get(name) or "").strip()]
    if missing:
        return {**base, "state": "FAIL_CLOSED", "event_count": len(events),
                "failed_predicate": "ledger_location_required_from_materializer",
                "missing_ledger_roots": missing, "appended": False,
                "required_evidence_or_repair": "supply " + " and ".join(missing),
                "events_retained": True}
    results = []
    for path in events:
        row: dict[str, Any] = {"event": path.name}
        try:
            raw = path.read_bytes()
            event = json.loads(raw)
            row["event_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        except (OSError, ValueError):
            event = None
        if (not isinstance(event, Mapping) or event.get("schema") != OUTBOX_EVENT_SCHEMA
                or event.get("route") != route or not isinstance(event.get("manifest"), Mapping)):
            # No manifest, so nothing is attempted and nothing is appended.
            results.append({**row, "disposition": "FAIL_CLOSED",
                            "failed_predicate": "OUTBOX_EVENT_CARRIES_A_MANIFEST_ON_THIS_ROUTE",
                            "appended": False})
            continue
        result = receive(event["manifest"], registry=registry, standing=event.get("standing"),
                         packet_id=str(event.get("packet_id") or f"{route}:{path.stem}"),
                         hb_epoch=event.get("hb_epoch"), mesh_root=mesh_root)
        results.append({**row, **{key: result.get(key) for key in (
            "disposition", "failed_predicate", "received", "organization_receipt_sha256",
            "repository_receipt_sha256", "organization_transition_id", "transition_replayed",
            "refusal_organization_receipt_sha256", "refusal_transition_id", "differing_files")
            if key in result}})
    return {**base, "state": "CONSUMED", "event_count": len(events), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Receive a submitted SDK manifest on this organization's ingress operation.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path)
    source.add_argument("--outbox-root", type=Path,
                        help="durable state root whose intr-outbox/"
                             + ROLE_CONFORMANCE_OUTBOX_ROUTE + " events are received")
    parser.add_argument("--registry", type=Path, required=True,
                        help="materialized capability map supplied by the organization boundary")
    parser.add_argument("--standing", type=Path, default=None,
                        help="JSON declaring mode, node_ref and the predecessor key; "
                             "required unless the manifest declares its own chain position")
    parser.add_argument("--packet-id", default="organization-sdk-manifest-ingress")
    parser.add_argument("--hb-epoch", type=int, default=None,
                        help="heartbeat epoch; derived from the host clock, and marked as "
                             "derived, when absent")
    parser.add_argument("--mesh-root", type=Path, default=None,
                        help="federation mesh this node was materialized with; a governance "
                             "request leaves on it")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if args.outbox_root is not None:
        try:
            consumed = consume_outbox(args.outbox_root,
                                      registry=json.loads(args.registry.read_text(encoding="utf-8")),
                                      mesh_root=args.mesh_root)
        except RuntimeError as exc:
            consumed = {"schema": OUTBOX_CONSUMPTION_SCHEMA, "state": "FAIL_CLOSED",
                        "failed_predicate": str(exc), "receipt_written": False}
        rendered = json.dumps(consumed, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered)
        print(json.dumps(consumed, sort_keys=True))
        return 0 if consumed["state"] in {"NO_EVENT", "CONSUMED"} else 1
    try:
        result = receive(
            json.loads(args.manifest.read_text(encoding="utf-8")),
            registry=json.loads(args.registry.read_text(encoding="utf-8")),
            standing=(json.loads(args.standing.read_text(encoding="utf-8"))
                      if args.standing else None),
            packet_id=args.packet_id, hb_epoch=args.hb_epoch, mesh_root=args.mesh_root)
    except RuntimeError as exc:
        # Nothing was appended: the receipt could not name its own rule.
        print(json.dumps({"disposition": "FAIL_CLOSED", "failed_predicate": str(exc),
                          "receipt_written": False}, sort_keys=True))
        return 1
    # The full result stays in --out; the run summary carries only digests,
    # identifiers and revisions.
    write_step_summary(result)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("transition_closures", "sdk_admitted_result", "crossing")},
                     sort_keys=True))
    return 0 if result.get("disposition") == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
