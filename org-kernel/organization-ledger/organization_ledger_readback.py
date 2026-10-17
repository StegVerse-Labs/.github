#!/usr/bin/env python3
"""Read the organization ledger back and verify it, independently of the writer.

A transition is runtime reality only once the organization ledger holds it, so
the evidence of an append is a readback from the ledger itself, not the
writer's own report. This opens the ledger at the location it is given (for the
designated ref, a fresh fetch of `refs/stegverse/organization-ledger`). It walks
the chain from HEAD and checks, for every receipt:

- its `receipt_sha256` is the digest of its own body;
- `previous_receipt_sha256` names the receipt before it, ending at genesis
  (null), so the chain has no gaps and no forks;
- the source receipt it consumed is retained under `source-receipts/` and
  verifies against its own body.

Given an ingress result (`--ingress-result`), it also checks that the result's
organization receipt is in the chain, and that it is bound to the submitted
manifest: its predecessor state is the canonical manifest digest.

Legacy segments (G4/H45). A ledger may declare, in its committed
org-contract.json under `source_receipt_retention.legacy_pre_retention_segment`,
the receipts written before source retention began. The declaration is
digest-bound (`declaration_sha256`: sha256 over the segment without that member,
as UTF-8 JSON with sort_keys=True, separators=(",", ":"), ensure_ascii=False; the
same canonical form as receipt hashing) and bound to the ledger commit at which the
segment ends (`ledger_tip_commit`). Every declared receipt must still self-hash
and chain-link. Only SOURCE_RECEIPT_RETAINED_AND_VERIFIES is waived, and only
for the declared receipts. The receipts after the segment are verified in full.
A ledger whose only failures are its declared legacy receipts reads back as
FAIL_CLOSED with failure_code DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED. A
declared segment is read only with --repository-namespace equal to the
consumer's contract.json namespace (REPOSITORY_NAMESPACE_MATCHES_THE_CONTRACT),
so each legacy receipt's named source is checked on the repository chain. That
result names exactly those receipts, each one as a six-field finding, and it is
never ALLOW. Nothing is re-minted. Without a declaration, the readback is
unchanged.

Every refusal carries the six fields of a non-ALLOW. Stdlib and `git` only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_store import HEAD_KEY, open_store, parse_locator, receipt_key, source_key  # noqa: E402

import importlib.util  # noqa: E402
_HERE = Path(__file__).resolve().parent
_common_spec = importlib.util.spec_from_file_location("ledger_common", _HERE / "ledger_common.py")
common = importlib.util.module_from_spec(_common_spec)
_common_spec.loader.exec_module(common)  # noqa: E402
ROOT = common.consumer_root(common.legacy_root_of(__file__))
RETRY = common.entrypoint(__file__, "main")
GOAL = common.owning_existing_goal("LLMA-DECLARED-PATH-CONFORMANCE-368")


# The one canonical form, used both for receipt self-hashes and for a legacy
# segment's declaration_sha256. It is pinned explicitly: UTF-8,
# sort_keys=True, separators=(",", ":"), ensure_ascii=False. This is the same
# form as aggregate_repo_transition.canon and emit.canon. ensure_ascii=True
# would give a different digest for any non-ASCII member (for example U+2026).
CANONICAL_JSON = {"encoding": "utf-8", "sort_keys": True, "separators": [",", ":"], "ensure_ascii": False}


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(value):
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


class ReadbackRefused(Exception):
    def __init__(self, failed_predicate, detail, failure_code=None, next_attempt=None):
        super().__init__(failed_predicate + ": " + detail)
        self.failed_predicate = failed_predicate
        self.detail = detail
        if failure_code:
            self.failure_code = failure_code
        if next_attempt:
            self.next_attempt = next_attempt


# --- Legacy segments (G4 / H45) -------------------------------------------------
WAIVABLE_PREDICATE = "SOURCE_RECEIPT_RETAINED_AND_VERIFIES"
# Self-hash and linkage are never waivable, whatever a declaration says.
INTEGRITY_PREDICATES = frozenset({
    "ORGANIZATION_RECEIPT_VERIFIES_AGAINST_ITS_BODY", "ORGANIZATION_LEDGER_CHAIN_IS_COMPLETE",
    "ORGANIZATION_LEDGER_CHAIN_IS_ACYCLIC", "ORGANIZATION_LEDGER_HEAD_PRESENT",
    "REPOSITORY_CHAIN_VERIFIES", "REPOSITORY_LEDGER_HEAD_PRESENT",
    "RECEIPT_SELF_HASH", "CHAIN_LINKAGE", "SELF_HASH", "LINKAGE",
})
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
SEGMENT_MEMBERS = ("receipts", "waived_predicate", "six_fields", "ledger_tip_commit",
                   "re_minted", "reported_as_source_retained", "declaration_sha256")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}", re.ASCII)
_COMMIT = re.compile(r"[0-9a-f]{40}", re.ASCII)
DECLARATION_NEXT = ("correct the committed legacy-segment declaration in org-contract.json "
                    "(source_receipt_retention.legacy_pre_retention_segment) and read back again; "
                    "nothing is written by the readback and no receipt is ever re-minted")


def _declaration_refused(code, predicate, detail):
    return ReadbackRefused(predicate, detail, failure_code=code, next_attempt=DECLARATION_NEXT)


def declaration_digest(segment):
    """sha256 of the segment without declaration_sha256, in CANONICAL_JSON (the receipt canonical form)."""
    return sha({k: v for k, v in segment.items() if k != "declaration_sha256"})


def legacy_segment_of(org_contract):
    """The declared legacy segment in a consumer's org-contract.json, or None."""
    if not org_contract:
        return None
    rule = org_contract.get("source_receipt_retention")
    if rule is None:
        return None
    if not isinstance(rule, dict):
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INVALID", "SOURCE_RECEIPT_RETENTION_IS_AN_OBJECT",
                                   "source_receipt_retention must be an object")
    return rule.get("legacy_pre_retention_segment")


def validate_legacy_segment(segment):
    """Static checks on a declaration. Refuses six-field; returns the segment."""
    if not isinstance(segment, dict):
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INVALID", "LEGACY_SEGMENT_IS_AN_OBJECT",
                                   "legacy_pre_retention_segment must be an object")
    missing = [m for m in SEGMENT_MEMBERS if m not in segment]
    if missing:
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INCOMPLETE", "LEGACY_SEGMENT_DECLARES_EVERY_REQUIRED_MEMBER",
                                   "legacy_pre_retention_segment lacks " + ", ".join(missing)
                                   + "; required: " + ", ".join(SEGMENT_MEMBERS))
    waived = segment["waived_predicate"]
    named = waived if isinstance(waived, list) else [waived]
    if any(w in INTEGRITY_PREDICATES or not isinstance(w, str) for w in named) or not named:
        raise _declaration_refused("LEGACY_SEGMENT_WAIVES_SELF_HASH_OR_LINKAGE", "LEGACY_SEGMENT_NEVER_WAIVES_SELF_HASH_OR_LINKAGE",
                                   "waived_predicate names " + json.dumps(waived)
                                   + "; only " + WAIVABLE_PREDICATE + " may be waived")
    if named != [WAIVABLE_PREDICATE]:
        raise _declaration_refused("LEGACY_SEGMENT_WAIVES_A_NON_WAIVABLE_PREDICATE", "LEGACY_SEGMENT_WAIVES_ONLY_SOURCE_RETENTION",
                                   "waived_predicate must be exactly " + json.dumps(WAIVABLE_PREDICATE)
                                   + ", got " + json.dumps(waived))
    receipts = segment["receipts"]
    if (not isinstance(receipts, list) or not receipts
            or any(not isinstance(r, str) or not _DIGEST.fullmatch(r) for r in receipts)
            or len(set(receipts)) != len(receipts)):
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INVALID", "LEGACY_SEGMENT_RECEIPTS_ARE_DISTINCT_SHA256_DIGESTS",
                                   "receipts must be a non-empty list of distinct sha256:<64 hex> digests in chain order")
    six = segment["six_fields"]
    if (not isinstance(six, dict) or set(six) != set(SIX_FIELDS)
            or any(not isinstance(six[f], str) or not six[f] for f in SIX_FIELDS)):
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INVALID", "LEGACY_SEGMENT_CARRIES_SIX_FIELDS",
                                   "six_fields must hold exactly " + ", ".join(SIX_FIELDS) + " as non-empty strings")
    if segment["re_minted"] is not False or segment["reported_as_source_retained"] is not False:
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INVALID", "LEGACY_SEGMENT_IS_NEVER_RE_MINTED_OR_REPORTED_RETAINED",
                                   "re_minted and reported_as_source_retained must both be false")
    tip = segment["ledger_tip_commit"]
    if not isinstance(tip, str) or not _COMMIT.fullmatch(tip):
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_INVALID", "LEGACY_SEGMENT_LEDGER_TIP_COMMIT_IS_40_HEX",
                                   "ledger_tip_commit must be the 40-hex ledger commit at which the segment ends")
    if segment["declaration_sha256"] != declaration_digest(segment):
        raise _declaration_refused("LEGACY_SEGMENT_DECLARATION_DIGEST_MISMATCH", "LEGACY_SEGMENT_DECLARATION_IS_DIGEST_BOUND",
                                   "declaration_sha256 must be " + declaration_digest(segment)
                                   + " (sha256 of the segment without declaration_sha256, as UTF-8 JSON with "
                                   "sort_keys=True, separators=(',', ':'), ensure_ascii=False)")
    return segment


def _git(repository, *args):
    return subprocess.run(["git", "-C", str(repository), *args], capture_output=True, text=True)


def _segment_tip_head(location, tip):
    """The organization HEAD receipt at the declared ledger commit, which must be on the ref read."""
    locator = parse_locator(location)
    if not hasattr(locator, "ref") or getattr(locator, "namespace", None):
        raise _declaration_refused("LEGACY_SEGMENT_TIP_COMMIT_UNVERIFIABLE", "LEGACY_SEGMENT_IS_BOUND_TO_A_LEDGER_COMMIT",
                                   "a legacy segment is bound to a git ledger commit; read it from a git+<repo>#<ref> locator")
    if _git(locator.repository, "merge-base", "--is-ancestor", tip, locator.ref).returncode != 0:
        raise _declaration_refused("LEGACY_SEGMENT_TIP_COMMIT_NOT_ON_THE_LEDGER_REF", "LEGACY_SEGMENT_TIP_COMMIT_IS_ON_THE_LEDGER_REF",
                                   "ledger_tip_commit " + tip + " is not " + locator.ref + " or one of its ancestors")
    shown = _git(locator.repository, "show", tip + ":" + HEAD_KEY)
    try:
        return json.loads(shown.stdout).get("receipt_sha256") if shown.returncode == 0 else None
    except ValueError:
        return None


def _apply_legacy_segment(location, segment, chain, failing):
    """Check a declared segment against the verified chain; return the legacy report."""
    order = [r["receipt_sha256"] for r in chain]
    declared = segment["receipts"]
    absent = [d for d in declared if d not in order]
    if absent:
        raise _declaration_refused("LEGACY_SEGMENT_NAMES_A_RECEIPT_NOT_IN_THE_CHAIN", "LEGACY_SEGMENT_RECEIPTS_ARE_IN_THE_CHAIN",
                                   "declared receipts not in the chain: " + ", ".join(absent))
    if order[:len(declared)] != declared:
        raise _declaration_refused("LEGACY_SEGMENT_NOT_A_CONTIGUOUS_PREFIX", "LEGACY_SEGMENT_IS_A_CONTIGUOUS_PREFIX_FROM_GENESIS",
                                   "declared " + ", ".join(declared) + " but the chain opens " + ", ".join(order[:len(declared)]))
    by_digest = {r["receipt_sha256"]: r for r in chain}
    retained_shape = [d for d in declared if "source_transition_sha256" in by_digest[d]]
    tip_head = _segment_tip_head(location, segment["ledger_tip_commit"])
    if retained_shape or tip_head != declared[-1]:
        raise _declaration_refused("LEGACY_SEGMENT_OVERLAPS_RETENTION", "LEGACY_SEGMENT_ENDS_BEFORE_SOURCE_RETENTION_BEGINS",
                                   "segment must end at the HEAD of ledger_tip_commit " + segment["ledger_tip_commit"]
                                   + " (HEAD there: " + str(tip_head) + ") and hold no receipt naming source_transition_sha256"
                                   + (" (does: " + ", ".join(retained_shape) + ")" if retained_shape else ""))
    undeclared = [d for d, _ in failing if d not in declared]
    if undeclared:
        raise ReadbackRefused(WAIVABLE_PREDICATE, "undeclared source-retention failures: " + ", ".join(undeclared),
                              failure_code="UNDECLARED_SOURCE_RECEIPT_RETENTION_FAILURE")
    unnamed = [d for d in declared if not _DIGEST.fullmatch(str(by_digest[d].get("repo_receipt_sha256")))]
    if unnamed:
        raise _declaration_refused("LEGACY_RECEIPT_NAMES_NO_SOURCE", "LEGACY_RECEIPT_NAMES_ITS_REPOSITORY_RECEIPT",
                                   "legacy receipts must name repo_receipt_sha256: " + ", ".join(unnamed))
    six = segment["six_fields"]
    findings = [dict({"receipt_sha256": d, "disposition": "FAIL_CLOSED",
                      "names_source_receipt_sha256": by_digest[d]["repo_receipt_sha256"],
                      "self_hash_verified": True, "chain_link_verified": True,
                      "source_receipt_retained": False, "re_minted": False}, **six) for d in declared]
    return {
        "declaration_sha256": segment["declaration_sha256"],
        "declaration_digest_canonicalization": dict(CANONICAL_JSON),
        "waived_predicate": WAIVABLE_PREDICATE,
        "receipts": list(declared),
        "ledger_tip_commit": segment["ledger_tip_commit"],
        "ledger_tip_commit_on_ref": True,
        "ledger_tip_commit_head_is_segment_end": True,
        "findings": findings,
        "fully_verified_receipts": order[len(declared):],
        "re_minted": False,
        "reported_as_source_retained": False,
    }


def self_verifies(document):
    body = {key: value for key, value in document.items() if key != "receipt_sha256"}
    return document.get("receipt_sha256") == sha(body)


NAMESPACE_PREDICATE = "REPOSITORY_NAMESPACE_MATCHES_THE_CONTRACT"


def _require_contract_namespace(repository_namespace, repo_contract):
    """A declared segment is read with the repository chain the consumer's contract.json names.

    The legacy receipts' named sources can be checked only on the repository
    chain, so a declared segment requires --repository-namespace, and it must be
    the namespace in contract.json (repository_ledger_location.namespace). The
    predicate name is SV-011's (PR #9 @8dcf892).
    """
    if repo_contract is None:
        try:
            repo_contract = common.load_contract("contract.json", ROOT)
        except (OSError, ValueError):
            repo_contract = {}
    expected = ((repo_contract or {}).get("repository_ledger_location") or {}).get("namespace")
    if not repository_namespace or repository_namespace != expected:
        raise ReadbackRefused(
            NAMESPACE_PREDICATE,
            "a declared legacy segment is read with --repository-namespace equal to contract.json "
            "repository_ledger_location.namespace (" + str(expected) + "); got " + str(repository_namespace),
            next_attempt="rerun the readback with --repository-namespace " + str(expected)
                         + "; nothing is written by it")


def readback(location, ingress_result=None, manifest=None, org_contract=None,
             repository_namespace=None, repo_contract=None):
    segment = legacy_segment_of(org_contract)
    if segment is not None:
        validate_legacy_segment(segment)
        _require_contract_namespace(repository_namespace, repo_contract)
    failing = []
    store = open_store(parse_locator(location))
    head = store.get(HEAD_KEY)
    if head is None:
        # failure_code names the condition; the predicate stays HEAD_PRESENT,
        # which recorded_for keys on and the writer's GENESIS path mirrors.
        raise ReadbackRefused("ORGANIZATION_LEDGER_HEAD_PRESENT", "no HEAD at " + location,
                              failure_code="ORGANIZATION_LEDGER_HEAD_ABSENT",
                              next_attempt="an empty ledger opens only through a manifest-directed GENESIS append; "
                                           "nothing is written by the readback")
    chain, cursor, seen = [], head.get("receipt_sha256"), set()
    while cursor is not None:
        if cursor in seen:
            raise ReadbackRefused("ORGANIZATION_LEDGER_CHAIN_IS_ACYCLIC", cursor)
        seen.add(cursor)
        receipt = store.get(receipt_key(cursor))
        if receipt is None:
            raise ReadbackRefused("ORGANIZATION_LEDGER_CHAIN_IS_COMPLETE", "missing " + cursor)
        if receipt.get("receipt_sha256") != cursor or not self_verifies(receipt):
            raise ReadbackRefused("ORGANIZATION_RECEIPT_VERIFIES_AGAINST_ITS_BODY", cursor)
        source_digest = receipt.get("source_transition_sha256")
        source = store.get(source_key(source_digest)) if source_digest else None
        if source is None or source.get("receipt_sha256") != source_digest or not self_verifies(source):
            if segment is None:
                raise ReadbackRefused("SOURCE_RECEIPT_RETAINED_AND_VERIFIES",
                                      _source_repair(receipt, source_digest))
            failing.append((cursor, source_digest))
        chain.append(receipt)
        cursor = receipt.get("previous_receipt_sha256")
    chain.reverse()
    legacy = _apply_legacy_segment(location, segment, chain, failing) if segment is not None else None
    result = {
        "schema": "stegverse.organization-ledger-readback/v1",
        "location": location,
        "disposition": "ALLOW",
        "head_receipt_sha256": head["receipt_sha256"],
        "chain_length": len(chain),
        "genesis_receipt_sha256": chain[0]["receipt_sha256"],
        "chain": [{"receipt_sha256": r["receipt_sha256"],
                   "previous_receipt_sha256": r.get("previous_receipt_sha256"),
                   "source_transition_id": r.get("source_transition_id"),
                   "predecessor_org_state_sha256": r.get("predecessor_org_state_sha256"),
                   "successor_org_state_sha256": r.get("successor_org_state_sha256")} for r in chain],
        "every_receipt_verifies_against_its_body": True,
        "every_source_receipt_retained_and_verifies": True,
        "authority_effect": "NONE_READBACK_ONLY",
    }
    if legacy is not None:
        # Never ALLOW: the whole-ledger predicate is false for the declared
        # receipts. Everything else was verified; the result names exactly them.
        six = segment["six_fields"]
        result.update({
            "disposition": "FAIL_CLOSED",
            "failure_code": "DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED",
            "failed_predicate": WAIVABLE_PREDICATE,
            "required_evidence_or_repair": (
                "receipts " + ", ".join(legacy["receipts"]) + " are a declared legacy pre-retention segment "
                "(declaration " + legacy["declaration_sha256"] + "); they self-hash and chain-link, and every "
                "other receipt and predicate verified; they are never re-minted. Declared repair: "
                + six["required_evidence_or_repair"]),
            "retry_entrypoint": six["retry_entrypoint"],
            "owning_existing_goal": six["owning_existing_goal"],
            "next_attempt": six["next_attempt"],
            "every_source_receipt_retained_and_verifies": False,
            "every_chain_link_verified": True,
            "undeclared_failures": [],
            "legacy_segment": legacy,
        })
    if ingress_result is not None:
        # A refusal is recorded too, under its own name, and is bound to the
        # submitted manifest's digest rather than the canonical one.
        refused = ingress_result.get("refusal_organization_receipt_sha256") is not None
        digest = ingress_result.get("refusal_organization_receipt_sha256" if refused
                                    else "organization_receipt_sha256")
        receipt = next((r for r in chain if r["receipt_sha256"] == digest), None)
        if receipt is None:
            raise ReadbackRefused("INGRESS_RECEIPT_IS_IN_THE_ORGANIZATION_LEDGER", str(digest))
        if refused:
            manifest_state = sha(manifest) if manifest is not None else None
        else:
            manifest_state = "sha256:" + str(ingress_result.get("canonical_manifest_sha256"))
        if not manifest_state or receipt.get("predecessor_org_state_sha256") != manifest_state:
            raise ReadbackRefused("RECEIPT_IS_BOUND_TO_THE_SUBMITTED_MANIFEST", str(manifest_state))
        result.update({
            "ingress_disposition": ingress_result.get("disposition"),
            "ingress_refused": refused,
            "ingress_organization_receipt_sha256": digest,
            "ingress_receipt_in_chain": True,
            "ingress_receipt_bound_to_manifest": True,
            "canonical_manifest_sha256": ingress_result.get("canonical_manifest_sha256"),
            "organization_transition_id": ingress_result.get("organization_transition_id"),
            "master_records_awaited": False,
        })
        if legacy is not None:
            result["ingress_receipt_in_fully_verified_suffix"] = digest in legacy["fully_verified_receipts"]
    return result


def _repository_emitter():
    """The repository ledger's own chain walker, so the readback verifies nodes the way the writer does."""
    import importlib.util
    emit = common.sibling("emit.py", _HERE, ROOT)
    spec = importlib.util.spec_from_file_location("repository_ledger_readback_emit", emit)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repository_readback(location, namespace, organization_result, ingress_result=None):
    """Read the repository chain kept in `namespace` of the same ref back and verify it.

    The repository ledger is durable only if its chain survives the run that
    wrote it, so this walks `repository-ledger/<repository>/HEAD.json` back
    through repository receipts alone -- never an organization receipt, as the
    repository replay rule requires -- and checks every node the way the
    emitter does. Each repository receipt in the chain must also be retained
    byte-for-byte by the organization ledger it was consumed into. Given an
    ingress result, the repository receipt it names must be in this chain and
    be the source the ingress's organization receipt consumed.
    """
    emitter = _repository_emitter()
    locator = parse_locator(location)
    repository_location = str(locator) + ":" + namespace
    store = open_store(repository_location)
    organization_store = open_store(locator)
    head = store.get(HEAD_KEY)
    if head is None:
        raise ReadbackRefused("REPOSITORY_LEDGER_HEAD_PRESENT", "no HEAD at " + repository_location)
    try:
        chain = list(emitter.chain(store, head))
    except emitter.RepoLedgerChainBreak as exc:
        raise ReadbackRefused("REPOSITORY_CHAIN_VERIFIES", str(exc)) from None
    chain.reverse()
    legacy = organization_result.get("legacy_segment") or {}
    legacy_sources = {f["names_source_receipt_sha256"]: f["receipt_sha256"] for f in legacy.get("findings", [])}
    repository_digests = {r["receipt_sha256"] for r in chain}
    off_chain = [s for s in legacy_sources if s not in repository_digests]
    if off_chain:
        raise ReadbackRefused("LEGACY_RECEIPT_SOURCE_IS_ON_THE_REPOSITORY_CHAIN", ", ".join(off_chain),
                              failure_code="LEGACY_RECEIPT_SOURCE_NOT_ON_THE_REPOSITORY_CHAIN")
    legacy_unretained = []
    for receipt in chain:
        retained = organization_store.get(source_key(receipt["receipt_sha256"]))
        if retained != receipt:
            if retained is None and receipt["receipt_sha256"] in legacy_sources:
                # The same declared gap seen from the repository side: the
                # source of a declared legacy receipt, verified on this chain.
                legacy_unretained.append(receipt["receipt_sha256"])
                continue
            raise ReadbackRefused("REPOSITORY_RECEIPT_RETAINED_IN_ORGANIZATION_LEDGER",
                                  receipt["receipt_sha256"])
    result = {
        "location": repository_location,
        "namespace": namespace,
        "head_receipt_sha256": head["receipt_sha256"],
        "chain_length": len(chain),
        "genesis_receipt_sha256": chain[0]["receipt_sha256"],
        "chain": [{"receipt_sha256": r["receipt_sha256"],
                   "previous_receipt_sha256": r.get("previous_receipt_sha256"),
                   "transition_id": r.get("transition_id"),
                   "transition_class": r.get("transition_class")} for r in chain],
        "every_receipt_verifies_against_its_body": True,
        "every_receipt_retained_in_organization_ledger": not legacy_unretained,
        "replay_read_organization_receipts": False,
    }
    if legacy:
        result["legacy_segment_sources_not_retained"] = legacy_unretained
        result["legacy_segment_sources_on_this_chain"] = True
    if ingress_result is not None:
        refused = ingress_result.get("refusal_organization_receipt_sha256") is not None
        digest = ingress_result.get("refusal_repository_receipt_sha256" if refused
                                    else "repository_receipt_sha256")
        organization_digest = organization_result["ingress_organization_receipt_sha256"]
        consumed = organization_store.get(receipt_key(organization_digest)) or {}
        if digest is None and ingress_result.get("disposition") == "ALREADY_RECORDED":
            # A request answered from the ledger appended nothing, so it names
            # only the organization receipt already binding its manifest. The
            # repository receipt is the one that receipt consumed; it must still
            # be in this chain, so a missing or foreign source fails closed below.
            digest = consumed.get("source_transition_sha256")
        if not any(r["receipt_sha256"] == digest for r in chain):
            raise ReadbackRefused("INGRESS_REPOSITORY_RECEIPT_IS_IN_THE_REPOSITORY_LEDGER", str(digest))
        if consumed.get("source_transition_sha256") != digest:
            raise ReadbackRefused("ORGANIZATION_RECEIPT_CONSUMES_THE_REPOSITORY_RECEIPT", str(digest))
        result.update({"ingress_repository_receipt_sha256": digest,
                       "ingress_repository_receipt_in_chain": True,
                       "consumed_by_organization_receipt_sha256": organization_digest})
    return result


def recorded_for(location, canonical_manifest_sha256, org_contract=None, repository_namespace=None,
                 repo_contract=None):
    """The verified receipt already binding this manifest, or None.

    One manifest is one transition. A request submitted again is answered from
    the ledger rather than appended a second time. This lookup needs chain
    integrity, so it uses the verified chain of a declared-legacy FAIL_CLOSED
    readback too; it never reports that ledger as ALLOW.
    """
    try:
        verified = readback(location, org_contract=org_contract, repository_namespace=repository_namespace,
                            repo_contract=repo_contract)
    except ReadbackRefused as exc:
        if exc.failed_predicate == "ORGANIZATION_LEDGER_HEAD_PRESENT":
            return None
        raise
    state = "sha256:" + canonical_manifest_sha256
    return next((r["receipt_sha256"] for r in verified["chain"]
                 if r["predecessor_org_state_sha256"] == state), None)


def _source_repair(receipt, source_digest):
    """What SOURCE_RECEIPT_RETAINED_AND_VERIFIES needs, naming the receipt; never 'None'."""
    named = ("names source receipt " + source_digest) if source_digest else "names no source receipt"
    return ("organization receipt " + str(receipt.get("receipt_sha256")) + " " + named + " that is retained "
            "and self-verifies; retain the source receipt under source-receipts/, or have the owner declare the "
            "pre-retention range as a legacy segment in org-contract.json (G4/H45); never re-mint")


def _repair_of(exc):
    """required_evidence_or_repair: the refusal's own text, never empty or 'None'."""
    detail = getattr(exc, "detail", None)
    text = detail if isinstance(detail, str) else str(exc)
    if text.strip() and text.strip() != "None":
        return text
    return ("repair what " + getattr(exc, "failed_predicate", "the readback") + " refused and fetch the ledger ref "
            "again; the readback writes nothing")


def _refusal(location, exc):
    fields = getattr(exc, "refusal", None)
    if isinstance(fields, dict):   # a ledger_store locator refusal: its own six fields, this entrypoint
        return {"schema": "stegverse.organization-ledger-readback/v1", "location": location,
                "disposition": "FAIL_CLOSED", **{k: fields[k] for k in ("failure_code", "failed_predicate",
                "required_evidence_or_repair", "owning_existing_goal", "next_attempt")},
                "retry_entrypoint": RETRY, "authority_effect": "NONE_READBACK_ONLY"}
    return {
        "schema": "stegverse.organization-ledger-readback/v1",
        "location": location,
        "disposition": "FAIL_CLOSED",
        "failure_code": getattr(exc, "failure_code", "ORGANIZATION_LEDGER_READBACK_FAILED"),
        "failed_predicate": getattr(exc, "failed_predicate", "ORGANIZATION_LEDGER_READS_BACK"),
        "required_evidence_or_repair": _repair_of(exc),
        "retry_entrypoint": RETRY,
        "owning_existing_goal": GOAL,
        "next_attempt": getattr(exc, "next_attempt",
                                "fetch the ledger ref again and rerun the readback; nothing is written by it"),
        "authority_effect": "NONE_READBACK_ONLY",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--location", required=True, help="ledger locator, e.g. git+<repo>#<ref>")
    parser.add_argument("--ingress-result", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None,
                        help="the submitted manifest; binds a recorded refusal to it")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--recorded-for", metavar="CANONICAL_MANIFEST_SHA256", default=None,
                        help="print the receipt already binding this manifest, or nothing")
    parser.add_argument("--repository-namespace", default=None,
                        help="also read back the repository chain kept in this subtree of the same ref")
    parser.add_argument("--org-contract", type=Path, default=None,
                        help="the consumer's org-contract.json (legacy-segment declaration); "
                             "default: the consumer checkout's .stegverse/transition-ledger/org-contract.json")
    args = parser.parse_args()
    contract_file = args.org_contract or common.contract_path("org-contract.json", ROOT)
    try:
        org_contract = json.loads(contract_file.read_text()) if contract_file.is_file() else None
    except ValueError:
        org_contract = {"source_receipt_retention": "unreadable org-contract.json"}
    if args.recorded_for:
        try:
            print(recorded_for(args.location, args.recorded_for, org_contract, args.repository_namespace) or "")
        except ReadbackRefused as exc:
            print(json.dumps(_refusal(args.location, exc), indent=2, sort_keys=True), file=sys.stderr)
            return 1
        return 0
    ingress = json.loads(args.ingress_result.read_text()) if args.ingress_result else None
    manifest = json.loads(args.manifest.read_text()) if args.manifest else None
    try:
        result = readback(args.location, ingress, manifest, org_contract, args.repository_namespace)
        code = 0 if result["disposition"] == "ALLOW" else 1
        if args.repository_namespace:
            result["repository_ledger"] = repository_readback(
                args.location, args.repository_namespace, result, ingress)
    except (ReadbackRefused, ValueError, RuntimeError, FileNotFoundError) as exc:
        result, code = _refusal(args.location, exc), 1
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n")
    print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
