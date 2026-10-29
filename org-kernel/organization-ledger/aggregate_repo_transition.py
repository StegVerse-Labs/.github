#!/usr/bin/env python3
"""Append organization receipts with serialized, durable HEAD publication.

The organization ledger is local sovereign state. This emitter neither performs
InTr transport nor grants transition authority.

Admission is governed by the `consumes` list in the organization ledger
contract, not by a single hard-coded schema. Every state transition occurring
within the organization emits an organization receipt, so a canonical governed
state transition manifested through Interlock/InTr is admitted on its own
terms and bound by its own canonical digest.

The exact source transition receipt is retained under `source-receipts/` in
the same store transaction as the organization receipt and HEAD, so the
organization ledger can replay a source transition without the ledger that
emitted it (contract: preserves_source_transition_receipt).

The predecessor organization state is an explicit sha256 digest, FROM_HEAD or
GENESIS. FROM_HEAD binds the current HEAD receipt digest and is resolved inside
each compare-and-swap attempt, so a contended append cannot bind a stale
predecessor. GENESIS opens an empty chain and is accepted only while HEAD is
absent; a chain is never opened by default.
"""
from contextlib import nullcontext
import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_store import HEAD_KEY, RECEIPT_PREFIX, SOURCE_PREFIX, open_store, parse_locator, receipt_key, source_key  # noqa: E402

_HERE = Path(__file__).resolve().parent
_common_spec = importlib.util.spec_from_file_location("ledger_common", _HERE / "ledger_common.py")
common = importlib.util.module_from_spec(_common_spec)
_common_spec.loader.exec_module(common)  # noqa: E402
ROOT = common.consumer_root(common.legacy_root_of(__file__))
C = common.load_contract("org-contract.json", ROOT)
RETRY = common.entrypoint(__file__, "append")

_spec = importlib.util.spec_from_file_location("kernel", common.kernel_path(ROOT))
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)  # noqa: E402



SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")

FROM_HEAD = "FROM_HEAD"
GENESIS = "GENESIS"


# P1-FC-5: every refusal below carries the six fields. Its SystemExit code is the
# original message, so existing callers behave as before, and ``.refusal`` is the record.
_REPAIR = {
    "ORG_LEDGER_HEAD_MISSING_WITH_EXISTING_RECEIPTS": "restore HEAD.json naming the newest receipt; a chain is never re-opened over receipts",
    "ORG_LEDGER_UNPUBLISHED_OR_ORPHAN_RECEIPTS_RECOVERY_REQUIRED": "recover or remove the receipts unreachable from HEAD by an explicit recovery transition",
    "ORG_LEDGER_ORPHAN_SOURCE_RECEIPTS_RECOVERY_REQUIRED": "recover or remove the source receipts no organization receipt names",
    "ORG_LEDGER_APPEND_CONTENTION_EXHAUSTED": "128 compare-and-swap attempts lost to concurrent writers; nothing was written",
    "ORGANIZATION_SOURCE_RECEIPT_SCHEMA_MISMATCH": "submit a source receipt whose schema is listed in org-contract.json consumes",
    "REPO_OUTSIDE_ORGANIZATION": "submit a repository receipt from a repository inside this organization",
    "REPO_RECEIPT_HASH_MISMATCH": "submit the repository receipt byte-for-byte as minted",
}


def _refused(message):
    code = common.failure_code_of(message)
    return common.LedgerRefusal(message, failure_code=code, retry_entrypoint=RETRY,
                                required_evidence_or_repair=_REPAIR.get(code))


class OrgLedgerAppendRefused(common.LedgerRefusal):
    """A refused append, carrying its disposition and failed predicate.

    A SystemExit, so command-line use and existing callers behave as before,
    while a caller that records dispositions reads them from the exception.
    Nothing is written when this is raised.
    """

    retry_entrypoint = RETRY

    def __init__(self, disposition, failed_predicate):
        super().__init__(failed_predicate, disposition=disposition, failure_code=failed_predicate,
                         failed_predicate=failed_predicate, retry_entrypoint=RETRY,
                         required_evidence_or_repair=("declare GENESIS only on an empty ledger, otherwise FROM_HEAD"
                                                      if "GENESIS" in failed_predicate else None))
        self.disposition = disposition
        self.failed_predicate = failed_predicate


def require_state_digest(field, value):
    """A field named *_sha256 must carry one, or the chain records a claim it cannot check."""
    if not isinstance(value, str) or not SHA256_REF.match(value):
        raise _refused("ORG_LEDGER_" + field.upper() + "_NOT_A_SHA256_DIGEST")
    return value


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class LedgerLocationRequired(ValueError):
    """No ledger root was supplied; nothing is appended and nothing is derived."""

    failed_predicate = "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"

    def __init__(self, variable):
        super().__init__("ledger_location_required_from_materializer: " + variable)
        self.variable = variable


# A ledger location is supplied by the materializer, and the organization root
# is owner-designated (StegVerse-org/LLM-adapter#368). Until one is supplied,
# every append refuses with the six fields of a non-ALLOW.
LOCATION_FAILURE_CODE = "LEDGER_LOCATION_NOT_SUPPLIED"
LOCATION_OWNING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"


def location_next_attempt(variable):
    return ("rerun once " + variable + " is supplied; nothing was appended, "
            "so retry the same receipt unchanged")


def location_refusal(exc):
    """The append attempt's own disposition when no ledger root was supplied."""
    return {
        "schema": "stegverse.organization-ledger-append-refusal/v1",
        "organization": C["organization"],
        "disposition": "FAIL_CLOSED",
        "failed_predicate": exc.failed_predicate,
        "failure_code": LOCATION_FAILURE_CODE,
        "required_evidence_or_repair": "supply the organization ledger root as " + exc.variable,
        "retry_entrypoint": RETRY,
        "owning_existing_goal": common.owning_existing_goal(LOCATION_OWNING_GOAL),
        "next_attempt": location_next_attempt(exc.variable),
        "consequence_committed": False,
        "authority_effect": "NONE_REFUSAL_ONLY",
    }


def sha(value):
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def ledger_root():
    """The organization ledger root, as supplied to this execution.

    The ledger is the organization's runtime reality, so its location is
    supplied by whatever materialized this execution, exactly as the mesh is.
    It is never derived from the host: a home directory belongs to whichever
    machine happens to run this, and a chain written there is discarded with
    an ephemeral execution while appearing to have been appended. With no
    supplied root the append fails closed at this boundary.

    A supplied `git+<repository>#<ref>` names a git ref rather than a
    directory (see `ledger_store.parse_locator`). Which location is the
    organization's ledger is never decided here.
    """
    override = os.getenv("STEGVERSE_ORG_LEDGER_ROOT")
    if override:
        try:
            return parse_locator(override)
        except ValueError as exc:
            if hasattr(exc, "refusal"):
                raise common.locator_refusal(exc, RETRY) from None
            raise
    raise LedgerLocationRequired("STEGVERSE_ORG_LEDGER_ROOT")


def load(path):
    return common.loads_finite(Path(path).read_text(), RETRY)


def verify_required_evidence(receipt):
    """Require exact inline canonical evidence bytes for organization-local replay.

    Organization replay must terminate on this chain alone, so a canonical state
    transition carries its own evidence bytes rather than a reachability promise.
    """
    manifest = receipt.get("required_evidence_manifest")
    if not isinstance(manifest, list):
        raise _refused("canonical required evidence manifest missing")
    seen = set()
    for item in manifest:
        if not isinstance(item, dict):
            raise _refused("canonical evidence entry invalid")
        for key in ("evidence_id", "evidence_type", "origin_transition_id",
                    "encoding", "sha256", "content"):
            if key not in item:
                raise _refused("canonical evidence field missing: " + key)
        identity = item["evidence_id"]
        if not isinstance(identity, str) or not identity or identity in seen:
            raise _refused("canonical evidence identity invalid")
        seen.add(identity)
        if (not isinstance(item["evidence_type"], str) or not item["evidence_type"]
                or item["origin_transition_id"] != receipt.get("transition_id")):
            raise _refused("canonical evidence transition binding invalid")
        encoding = item["encoding"]
        content = item["content"]
        if encoding == "canonical-json":
            raw = canon(content)
        elif encoding == "utf-8" and isinstance(content, str):
            raw = content.encode("utf-8")
        elif encoding == "base64" and isinstance(content, str):
            try:
                raw = base64.b64decode(content.encode("ascii"), validate=True)
            except (ValueError, UnicodeError) as exc:
                raise _refused("canonical evidence base64 invalid") from exc
        else:
            raise _refused("canonical evidence encoding invalid")
        digest = item["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or hashlib.sha256(raw).hexdigest() != digest:
            raise _refused("canonical required evidence digest mismatch")


def verify_source(receipt):
    """Verify a source transition receipt this organization's contract consumes.

    The contract's `consumes` list is the admission gate. Every state transition
    occurring within the organization emits an organization receipt, so a
    canonical governed transition is admitted on its own terms: it is bound by
    its own canonical digest and keeps its own schema and transition id, rather
    than being relabelled as a repository transition it is not.
    """
    schema = receipt.get("schema")
    allowed = C.get("consumes")
    if isinstance(allowed, str):
        allowed = [allowed]
    if schema not in (allowed or []):
        raise _refused("organization source receipt schema mismatch")
    transition_id = receipt.get("transition_id")
    if not isinstance(transition_id, str) or not transition_id:
        raise _refused("organization source transition id invalid")
    if schema == "stegverse.repo-transition-receipt/v1":
        repository = str(receipt.get("repository", ""))
        if not repository.startswith(C["organization"] + "/"):
            raise _refused("repo outside organization")
        claimed = receipt.get("receipt_sha256")
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        if claimed != sha(body):
            raise _refused("repo receipt hash mismatch")
        return {
            "source_receipt_schema": schema,
            "source_transition_sha256": claimed,
            "source_transition_id": transition_id,
            "source_repository": repository,
            "repo_receipt_sha256": claimed,
            "repo_transition_id": transition_id,
            "canonical_state_transition_receipt_sha256": None,
            "subject_or_correlation_id": None,
        }
    verify_required_evidence(receipt)
    digest = sha(receipt)
    return {
        "source_receipt_schema": schema,
        "source_transition_sha256": digest,
        "source_transition_id": transition_id,
        "source_repository": None,
        "repo_receipt_sha256": None,
        "repo_transition_id": None,
        "canonical_state_transition_receipt_sha256": digest,
        "subject_or_correlation_id": receipt.get("subject_or_correlation_id"),
    }


def _validate_existing_head(store):
    head = store.get(HEAD_KEY)
    if head is None:
        # A missing HEAD with existing receipts requires explicit recovery;
        # never silently fork or reset the organization chain.
        if store.list_prefix(RECEIPT_PREFIX):
            raise _refused("ORG_LEDGER_HEAD_MISSING_WITH_EXISTING_RECEIPTS")
        return None
    previous = head.get("receipt_sha256")
    if not isinstance(previous, str) or not previous.startswith("sha256:"):
        raise _refused("ORG_LEDGER_HEAD_INVALID")
    receipt = store.get(receipt_key(previous))
    if receipt is None:
        raise _refused("ORG_LEDGER_HEAD_RECEIPT_MISSING")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    if receipt.get("receipt_sha256") != previous or sha(body) != previous:
        raise _refused("ORG_LEDGER_HEAD_RECEIPT_HASH_MISMATCH")
    # A receipt written before a crash but not published as HEAD must not be
    # silently bypassed. Detect all unreachable receipts before appending.
    reachable = set()
    cursor = previous
    while cursor:
        if cursor in reachable:
            raise _refused("ORG_LEDGER_PREDECESSOR_CYCLE")
        reachable.add(cursor)
        record = store.get(receipt_key(cursor))
        if record is None:
            raise _refused("ORG_LEDGER_PREDECESSOR_MISSING")
        record_body = dict(record)
        record_body.pop("receipt_sha256", None)
        if record.get("receipt_sha256") != cursor or sha(record_body) != cursor:
            raise _refused("ORG_LEDGER_PREDECESSOR_HASH_MISMATCH")
        cursor = record.get("previous_receipt_sha256")
    if store.list_prefix(RECEIPT_PREFIX) != {receipt_key(digest) for digest in reachable}:
        raise _refused("ORG_LEDGER_UNPUBLISHED_OR_ORPHAN_RECEIPTS_RECOVERY_REQUIRED")
    # A retained source copy is published only through the receipt that names
    # it. Ledgers written before retention existed simply have none.
    sources = {source_key(store.get(receipt_key(digest))["source_transition_sha256"])
               for digest in reachable
               if isinstance(store.get(receipt_key(digest)).get("source_transition_sha256"), str)}
    if not store.list_prefix(SOURCE_PREFIX) <= sources:
        raise _refused("ORG_LEDGER_ORPHAN_SOURCE_RECEIPTS_RECOVERY_REQUIRED")
    return previous


def recorded(store, head, source_transition_sha256):
    """The organization receipt this chain already holds for a source receipt."""
    cursor = (head or {}).get("receipt_sha256")
    while cursor:
        receipt = store.get(receipt_key(cursor))
        if receipt is None:
            return None
        if receipt.get("source_transition_sha256") == source_transition_sha256:
            return receipt
        cursor = receipt.get("previous_receipt_sha256")
    return None


def append(source_receipt, org_transition_class, predecessor_state, successor_state,
           boundary_evidence, authority_effect, hb_epoch=None, store=None, idempotent=False):
    # Admission is decided before the append lock is taken; an inadmissible
    # source receipt never contends for the organization ledger.
    common.reject_non_finite(boundary_evidence, RETRY, "boundary_evidence")  # D-11: before admission, epoch or any write
    common.reject_non_finite(source_receipt, RETRY, "source_receipt")
    source = verify_source(source_receipt)
    if predecessor_state not in (FROM_HEAD, GENESIS):
        require_state_digest("predecessor_org_state_sha256", predecessor_state)
    require_state_digest("successor_org_state_sha256", successor_state)
    retained = {source_key(source["source_transition_sha256"]): source_receipt}
    # Ordering is a heartbeat count, not a clock reading. The tick is supplied by
    # the manifest or dispatch; there is no host-clock derivation.
    # P1-FC-4: the epoch is supplied or the append is refused with six fields; no clock is read.
    heartbeat = common.supplied_hb_reference(kernel, hb_epoch, RETRY)
    target = store or open_store(ledger_root())
    target.initialize()
    # The storage substrate owns serialization. A lost comparison writes
    # nothing, so a retry cannot strand an orphan receipt.
    for _attempt in range(128):
        guard = target.exclusive() if hasattr(target, "exclusive") else nullcontext()
        with guard:
            expected_head = target.get(HEAD_KEY)
            previous = (expected_head or {}).get("receipt_sha256")
            _validate_existing_head(target)
            # A source receipt is consumed once. With `idempotent` the chain is
            # read at the HEAD this attempt compares against: a receipt already
            # consuming this exact source is returned instead of a second one
            # minted, and one consuming it under another class is a collision.
            if idempotent:
                prior = recorded(target, expected_head, source["source_transition_sha256"])
                if prior is not None:
                    if prior.get("org_transition_class") != org_transition_class:
                        raise ValueError("ledger_receipt_collision")
                    return prior
            # Resolved against the HEAD this attempt will compare against, so a
            # retry after a lost comparison re-resolves rather than reusing it.
            if predecessor_state == FROM_HEAD:
                if expected_head is None:
                    raise OrgLedgerAppendRefused("FAIL_CLOSED", "ORG_LEDGER_GENESIS_NOT_DECLARED")
                predecessor = previous
            elif predecessor_state == GENESIS:
                if expected_head is not None:
                    raise OrgLedgerAppendRefused("DENY", "ORG_LEDGER_GENESIS_ON_NON_EMPTY_LEDGER")
                predecessor = None
            else:
                predecessor = predecessor_state
        body = {
            "schema": "stegverse.organization-transition-receipt/v1",
            "organization": C["organization"],
            **source,
            "org_transition_class": org_transition_class,
            "predecessor_org_state_sha256": predecessor,
            "successor_org_state_sha256": successor_state,
            "boundary_evidence": boundary_evidence,
            "authority_effect": authority_effect,
            "hb_reference": heartbeat,
            "previous_receipt_sha256": previous,
        }
        if predecessor_state == GENESIS:
            body["chain_genesis"] = True
        digest = sha(body)
        receipt = {**body, "receipt_sha256": digest}
        key = receipt_key(digest)
        new_head = {
            "organization": C["organization"],
            "receipt_sha256": digest,
            "receipt_path": target.locator(key),
        }
        if target.append_transaction(key, receipt, expected_head, new_head, immutable=retained):
            return receipt
    raise _refused("ORG_LEDGER_APPEND_CONTENTION_EXHAUSTED")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-receipt")
    parser.add_argument("--transition-receipt")
    parser.add_argument("--org-transition-class", default=None)
    parser.add_argument("--predecessor-org-state-sha256", required=True,
                        help="sha256 digest, FROM_HEAD (bind the current HEAD), or GENESIS (open an empty chain)")
    parser.add_argument("--successor-org-state-sha256", required=True)
    parser.add_argument("--boundary-evidence-json", default="{}")
    parser.add_argument("--authority-effect", default="NONE")
    parser.add_argument("--hb-epoch", type=str, default=None,
                        help="supplied heartbeat epoch (digits, >= 32); required, never derived from a clock")
    args = parser.parse_args()
    source_path = args.transition_receipt or args.repo_receipt
    if not source_path:
        raise _refused("transition receipt required")
    try:
        receipt = load(source_path)
        default_class = ("REPO_STATE_PROPAGATION"
                         if receipt.get("schema") == "stegverse.repo-transition-receipt/v1"
                         else "ORGANIZATION_STATE_TRANSITION")
        result = append(receipt, args.org_transition_class or default_class,
                        args.predecessor_org_state_sha256, args.successor_org_state_sha256,
                        common.loads_finite(args.boundary_evidence_json, RETRY), args.authority_effect,
                        hb_epoch=args.hb_epoch)
    except LedgerLocationRequired as exc:
        print(json.dumps(location_refusal(exc), sort_keys=True))
        raise SystemExit(1)
    except common.LedgerRefusal as exc:
        print(json.dumps(exc.refusal, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
