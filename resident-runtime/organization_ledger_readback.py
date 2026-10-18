#!/usr/bin/env python3
"""Read the organization ledger back and verify it, independently of the writer.

A transition is on the ledger only once a fresh read of the designated ref
holds it. This opens the ledger at the location it is given (for the
designated ref, a fresh fetch of ``refs/stegverse/organization-ledger``). It
walks the chain from HEAD and checks, for every receipt:

- its ``receipt_sha256`` is the digest of its own body;
- ``previous_receipt_sha256`` names the receipt before it, ending at genesis
  (null), so the chain has no gaps and no cycles;
- the source receipt it consumed is retained under ``source-receipts/`` and
  verifies against its own body.

``--repository-namespace`` also walks the repository chain kept in that
subtree of the same ref. Repository replay reads repository receipts only.

``--ingress-result`` (with ``--manifest`` for a refusal) checks that the
ingress's organization receipt is in the chain and is bound to the manifest:
an admitted receipt's predecessor state is the canonical manifest digest, a
refused one's is the submitted manifest's digest in ingress's own encoding.

``--closure-result`` checks that an intr-destination self-closure's repository
and organization receipts are those chains and both carry its
``communication_id``.

Authority (``authority_effect``) is a constraint variable on this read.
Dispositions here are evidence that the published ref does or does not hold
the chain. This read writes nothing. Stdlib and ``git`` only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_store import HEAD_KEY, open_store, parse_locator, receipt_key, source_key  # noqa: E402

RETRY = "resident-runtime/organization_ledger_readback.py::main"
ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / ".stegverse" / "transition-ledger" / "contract.json"


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value):
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def submitted_manifest_sha(manifest):
    """The digest ingress records for a refused manifest, in ingress's own encoding.

    `organization_manifest_ingress.refusal_record` hashes the submitted manifest
    with `json.dumps(sort_keys=True, separators=(",", ":"))` and the default
    `ensure_ascii=True`, then UTF-8. Receipts themselves are hashed by their
    writers with `ensure_ascii=False`, which `canon` keeps; only the refusal
    binding must match ingress, or a manifest carrying non-ASCII text cannot
    be bound.
    """
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def repository_namespace():
    """The repository subtree declared on the designated organization ledger ref."""
    location = json.loads(CONTRACT.read_text(encoding="utf-8"))["repository_ledger_location"]
    if location.get("new_ledger_root") is not False or not location.get("namespace"):
        raise ReadbackRefused(
            "REPOSITORY_LEDGER_STAYS_ON_THE_DESIGNATED_REF",
            "repository_ledger_location must name a namespace of the existing ref",
        )
    return location["namespace"]


class ReadbackRefused(Exception):
    def __init__(self, failed_predicate, detail):
        super().__init__(failed_predicate + ": " + detail)
        self.failed_predicate = failed_predicate
        self.detail = detail


def self_verifies(document):
    if not isinstance(document, dict):
        return False
    body = {key: value for key, value in document.items() if key != "receipt_sha256"}
    return document.get("receipt_sha256") == sha(body)


def readback(location, ingress_result=None, manifest=None):
    store = open_store(parse_locator(location))
    head = store.get(HEAD_KEY)
    if not isinstance(head, dict) or not head.get("receipt_sha256"):
        raise ReadbackRefused("ORGANIZATION_LEDGER_HEAD_PRESENT", "no HEAD at " + str(location))
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
            raise ReadbackRefused("SOURCE_RECEIPT_RETAINED_AND_VERIFIES", str(source_digest))
        chain.append(receipt)
        cursor = receipt.get("previous_receipt_sha256")
    chain.reverse()
    result = {
        "schema": "stegverse.organization-ledger-readback/v1",
        "location": str(location),
        "disposition": "ALLOW",
        "head_receipt_sha256": head["receipt_sha256"],
        "chain_length": len(chain),
        "genesis_receipt_sha256": chain[0]["receipt_sha256"],
        "chain": [{
            "receipt_sha256": row["receipt_sha256"],
            "previous_receipt_sha256": row.get("previous_receipt_sha256"),
            "source_transition_id": row.get("source_transition_id"),
            "communication_id": (row.get("boundary_evidence") or {}).get("communication_id"),
        } for row in chain],
        "every_receipt_verifies_against_its_body": True,
        "every_source_receipt_retained_and_verifies": True,
        "readback_writes": False,
        "authority_effect": "NONE_READBACK_ONLY",
    }
    if ingress_result is not None:
        # A refusal is recorded too, under its own name, and is bound to the
        # submitted manifest's digest rather than the canonical one.
        refused = ingress_result.get("refusal_organization_receipt_sha256") is not None
        digest = ingress_result.get("refusal_organization_receipt_sha256" if refused
                                    else "organization_receipt_sha256")
        receipt = next((row for row in chain if row["receipt_sha256"] == digest), None)
        if receipt is None:
            raise ReadbackRefused("INGRESS_RECEIPT_IS_IN_THE_ORGANIZATION_LEDGER", str(digest))
        if refused:
            manifest_state = submitted_manifest_sha(manifest) if manifest is not None else None
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
        })
    return result


def _repository_emitter():
    emit = ROOT / ".stegverse" / "transition-ledger" / "emit.py"
    spec = importlib.util.spec_from_file_location("repository_ledger_readback_emit", emit)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repository_readback(location, namespace):
    """Walk the repository subtree of the same ref. Organization receipts are not replay inputs."""
    emitter = _repository_emitter()
    locator = parse_locator(location)
    repository_location = str(locator) + ":" + namespace
    store = open_store(repository_location)
    organization_store = open_store(locator)
    head = store.get(HEAD_KEY)
    if not isinstance(head, dict) or not head.get("receipt_sha256"):
        raise ReadbackRefused("REPOSITORY_LEDGER_HEAD_PRESENT", "no HEAD at " + repository_location)
    try:
        chain = list(emitter.chain(store, head))
    except emitter.RepoLedgerChainBreak as exc:
        raise ReadbackRefused("REPOSITORY_CHAIN_VERIFIES", str(exc)) from None
    chain.reverse()
    for receipt in chain:
        retained = organization_store.get(source_key(receipt["receipt_sha256"]))
        if retained != receipt:
            raise ReadbackRefused(
                "REPOSITORY_RECEIPT_RETAINED_IN_ORGANIZATION_LEDGER",
                receipt["receipt_sha256"],
            )
    return {
        "location": repository_location,
        "namespace": namespace,
        "head_receipt_sha256": head["receipt_sha256"],
        "chain_length": len(chain),
        "genesis_receipt_sha256": chain[0]["receipt_sha256"],
        "chain": [{
            "receipt_sha256": row["receipt_sha256"],
            "previous_receipt_sha256": row.get("previous_receipt_sha256"),
            "transition_id": row.get("transition_id"),
            "transition_class": row.get("transition_class"),
            "communication_id": (row.get("evidence") or {}).get("communication_id"),
        } for row in chain],
        "every_receipt_verifies_against_its_body": True,
        "every_receipt_retained_in_organization_ledger": True,
        "replay_read_organization_receipts": False,
    }


def bind_closure(location, namespace, closure):
    """The self-closure's receipts are on the fresh ref and carry its communication_id."""
    if not isinstance(closure, dict):
        raise ReadbackRefused("CLOSURE_RESULT_IS_AN_OBJECT", type(closure).__name__)
    communication_id = closure.get("communication_id")
    if not isinstance(communication_id, str) or not communication_id.strip():
        raise ReadbackRefused(
            "CLOSURE_CARRIES_COMMUNICATION_ID", repr(communication_id))
    organization = readback(location)
    repository = repository_readback(location, namespace)
    organization_digest = closure.get("organization_receipt_sha256")
    repository_digest = closure.get("repository_receipt_sha256")
    if not any(row["receipt_sha256"] == organization_digest for row in organization["chain"]):
        raise ReadbackRefused(
            "CLOSURE_ORGANIZATION_RECEIPT_IS_IN_THE_ORGANIZATION_LEDGER",
            str(organization_digest),
        )
    if not any(row["receipt_sha256"] == repository_digest for row in repository["chain"]):
        raise ReadbackRefused(
            "CLOSURE_REPOSITORY_RECEIPT_IS_IN_THE_REPOSITORY_LEDGER",
            str(repository_digest),
        )
    locator = parse_locator(location)
    organization_store = open_store(locator)
    stored = organization_store.get(receipt_key(organization_digest)) or {}
    source = organization_store.get(source_key(repository_digest)) or {}
    boundary = stored.get("boundary_evidence") or {}
    evidence = source.get("evidence") or {}
    if stored.get("source_transition_sha256") != repository_digest:
        raise ReadbackRefused(
            "ORGANIZATION_RECEIPT_CONSUMES_THE_REPOSITORY_RECEIPT",
            str(repository_digest),
        )
    if boundary.get("communication_id") != communication_id or evidence.get("communication_id") != communication_id:
        raise ReadbackRefused("CLOSURE_COMMUNICATION_ID_IS_ON_BOTH_RECEIPTS", communication_id)
    if evidence.get("disposition") != closure.get("disposition"):
        raise ReadbackRefused(
            "CLOSURE_DISPOSITION_IS_THE_STORED_DISPOSITION",
            str(closure.get("disposition")),
        )
    organization["repository_ledger"] = repository
    organization["closure"] = {
        "communication_id": communication_id,
        "disposition": closure.get("disposition"),
        "organization_receipt_sha256": organization_digest,
        "repository_receipt_sha256": repository_digest,
        "organization_receipt_in_chain": True,
        "repository_receipt_in_chain": True,
        "communication_id_on_repository_receipt": True,
        "communication_id_on_organization_receipt": True,
    }
    return organization


def _refusal(location, exc):
    return {
        "schema": "stegverse.organization-ledger-readback/v1",
        "location": str(location),
        "disposition": "FAIL_CLOSED",
        "failure_code": "ORGANIZATION_LEDGER_READBACK_FAILED",
        "failed_predicate": getattr(exc, "failed_predicate", "ORGANIZATION_LEDGER_READS_BACK"),
        "required_evidence_or_repair": getattr(exc, "detail", str(exc)),
        "retry_entrypoint": RETRY,
        "consequence_committed": False,
        "readback_writes": False,
        "authority_effect": "NONE_READBACK_ONLY",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--location", required=True, help="ledger locator, e.g. git+<repo>#<ref>")
    parser.add_argument("--repository-namespace", default=None,
                        help="also read the repository chain kept in this subtree of the same ref")
    parser.add_argument("--closure-result", type=Path, default=None,
                        help="self-closure result whose receipts and communication_id must be on the ref")
    parser.add_argument("--ingress-result", type=Path, default=None,
                        help="ingress result whose organization receipt must be on the ref and bound to its manifest")
    parser.add_argument("--manifest", type=Path, default=None,
                        help="the submitted manifest; binds a recorded refusal to it")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    namespace = args.repository_namespace
    try:
        ingress = json.loads(args.ingress_result.read_text(encoding="utf-8")) if args.ingress_result else None
        manifest = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
        if args.closure_result is not None:
            if not namespace:
                namespace = repository_namespace()
            closure = json.loads(args.closure_result.read_text(encoding="utf-8"))
            result, code = bind_closure(args.location, namespace, closure), 0
        elif namespace:
            result = readback(args.location, ingress, manifest)
            result["repository_ledger"] = repository_readback(args.location, namespace)
            code = 0
        else:
            result, code = readback(args.location, ingress, manifest), 0
    except (ReadbackRefused, ValueError, RuntimeError, FileNotFoundError, OSError) as exc:
        result, code = _refusal(args.location, exc), 1
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
