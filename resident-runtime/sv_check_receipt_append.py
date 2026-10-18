#!/usr/bin/env python3
"""``sv_check_receipt`` -- append one NWI-S1 check receipt to the organization ledger.

The NWI-S1 verifier (SV-LLM/.github#46) emits a ``stegverse.sv_check_receipt.v1``
receipt at an exact head. It becomes a ledger receipt only when this writer
operation appends it to refs/stegverse/organization-ledger
(REQUIRED_CHECK_RECEIPTS_ARE_S1_VERIFIER_OUTPUTS_APPENDED_BY_ORG_WRITER).

Layout. These are the existing receipts, unchanged:
  * repository receipt (``stegverse.repo-transition-receipt/v1``, emit.py): ``$.evidence`` IS the check
    receipt, a complete and valid sv-check-receipt.v1 object, self-identified by ``$.evidence.schema``.
    No other marker or field is added.
  * organization receipt (``stegverse.organization-transition-receipt/v1``, aggregate_repo_transition.py):
    ``boundary_evidence.operation == "sv_check_receipt"``. Its ``repo_receipt_sha256`` names the repository
    receipt, which the organization ledger keeps beside it at ``source-receipts/<hex>.json``
    (ledger_store.source_key). The organization receipt itself is at ``receipts/<hex>.json``.
  * Time: ``hb_reference`` comes from kernel.hb_reference(epoch=<supplied int >= 32>), so derived_from_clock
    is False. This operation never lets the emitter read a clock: an absent or invalid epoch fails closed
    before anything is written.

The append path is intr_destination_ingress._append (repository append, then
aggregate_transition), under the writer workflow's ORGANIZATION_LEDGER_LOCK
concurrency group. Validation happens before any write. Every refusal is a
six-field FAIL_CLOSED with consequence_committed false, and nothing is written
for it. Stdlib only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

OPERATION_ID = "sv_check_receipt"
TRANSITION_CLASS = "SV_CHECK_RECEIPT_APPEND"
PROFILE_ID = "org-ledger-writer"
CHECK_RECEIPT_SCHEMA_ID = "stegverse.sv_check_receipt.v1"
CHECK_RECEIPT_SCHEMA_PATH = ROOT / "schemas" / "sv-check-receipt.v1.schema.json"
RESULT_SCHEMA = "stegverse.org-sv-check-receipt-append-result/v1"
READBACK_SCHEMA = "stegverse.org-sv-check-receipt-readback/v1"
OWNING_GOAL = "StegVerse-org/.github#163 (REQUIRED_CHECK_RECEIPTS_ARE_S1_VERIFIER_OUTPUTS_APPENDED_BY_ORG_WRITER)"
RETRY = "resident-runtime/sv_check_receipt_append.py::append_check_receipt"
HB_ANCHOR_EPOCH = 32  # org-kernel/kernel.py HB_ANCHOR_EPOCH
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
IDEMPOTENT_ON = ("schema", "check_id", "disposition", "change_digest", "head_sha", "hb_epoch", "verifier_ref")
_ANNOTATIONS = {"$id", "$schema", "title", "description"}
_KEYWORDS = {"type", "required", "properties", "additionalProperties", "const", "enum", "pattern",
             "minLength", "allOf", "if", "then"}


def _module(name: str, relative: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ingress = _module("intr_destination_ingress_sv_check", "resident-runtime/intr_destination_ingress.py")
sha = ingress.sha
CHECK_RECEIPT_SCHEMA = json.loads(CHECK_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
if CHECK_RECEIPT_SCHEMA.get("$id") != CHECK_RECEIPT_SCHEMA_ID:
    raise SystemExit("pinned sv-check-receipt schema id mismatch")


class SchemaUnsupported(Exception):
    pass


def schema_errors(instance: Any, schema: Mapping[str, Any], pointer: str = "") -> list[str]:
    """Validate against the pinned sv-check-receipt.v1 schema (the JSON Schema subset it uses). An unknown keyword
    raises instead of being skipped silently, so a schema change cannot loosen this check unnoticed."""
    unknown = set(schema) - _KEYWORDS - _ANNOTATIONS
    if unknown:
        raise SchemaUnsupported(", ".join(sorted(unknown)))
    out: list[str] = []
    t = schema.get("type")
    if t == "object" and not isinstance(instance, dict):
        return [pointer + ": type object"]
    if t == "string" and not isinstance(instance, str):
        return [pointer + ": type string"]
    if t not in (None, "object", "string"):
        raise SchemaUnsupported("type " + str(t))
    if "const" in schema and instance != schema["const"]:
        out.append(pointer + ": const")
    if "enum" in schema and instance not in schema["enum"]:
        out.append(pointer + ": enum")
    if isinstance(instance, str):
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            out.append(pointer + ": pattern")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append(pointer + ": minLength")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                out.append(pointer + "/" + key + ": required")
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                out += schema_errors(value, props[key], pointer + "/" + key)
            elif schema.get("additionalProperties") is False:
                out.append(pointer + "/" + key + ": additionalProperties")
    for sub in schema.get("allOf", []):
        out += schema_errors(instance, sub, pointer)
    if "if" in schema:
        if not schema_errors(instance, schema["if"], pointer):
            out += schema_errors(instance, schema.get("then", {}), pointer)
    return out


def refusal(code: str, predicate: str, repair: str, next_attempt: str, **detail: Any) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "operation": OPERATION_ID, "disposition": "FAIL_CLOSED",
            "failure_code": code, "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": RETRY, "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt,
            "consequence_committed": False, "authority_effect": "NONE_REFUSAL_ONLY", **detail}


def check_payload(receipt: Any) -> dict[str, Any] | None:
    """None when `receipt` is a complete, valid, self-identified sv-check-receipt.v1; otherwise the refusal."""
    if not isinstance(receipt, dict) or receipt.get("schema") != CHECK_RECEIPT_SCHEMA_ID:
        return refusal("LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT", "ORGANIZATION_LEDGER_EVIDENCE_IS_A_SELF_IDENTIFYING_CHECK_RECEIPT",
                       "supply the NWI-S1 verifier's receipt object whose $.schema is " + CHECK_RECEIPT_SCHEMA_ID,
                       "after the verifier's receipt is supplied as emitted; nothing was written")
    try:
        errors = schema_errors(receipt, CHECK_RECEIPT_SCHEMA)
    except SchemaUnsupported as exc:
        return refusal("SV_CHECK_RECEIPT_SCHEMA_UNSUPPORTED", "CHECK_RECEIPT_VALIDATES_AGAINST_PINNED_SCHEMA",
                       "the pinned schema uses a keyword this validator does not implement: " + str(exc),
                       "after the validator covers the pinned schema; nothing was written")
    if errors:
        return refusal("LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT", "CHECK_RECEIPT_VALIDATES_AGAINST_PINNED_SCHEMA",
                       "supply a complete, valid " + CHECK_RECEIPT_SCHEMA_ID + " receipt (schemas/sv-check-receipt.v1.schema.json)",
                       "after the verifier re-emits a valid receipt; nothing was written", schema_errors=errors)
    return None


def _epoch_refusal(hb_epoch: Any) -> dict[str, Any] | None:
    if type(hb_epoch) is not int or hb_epoch < HB_ANCHOR_EPOCH:
        return refusal("HB_EPOCH_UNSUPPLIED_OR_INVALID", "HB_EPOCH_IS_SUPPLIED_NOT_CLOCK_DERIVED",
                       "supply hb_epoch as an integer >= 32 with the dispatch; it is never derived from a clock",
                       "after the epoch is supplied; nothing was written", hb_epoch=repr(hb_epoch))
    return None


def append_check_receipt(receipt: Any, *, hb_epoch: Any) -> dict[str, Any]:
    """Append `receipt` as the repository receipt's $.evidence and aggregate it into the organization ledger."""
    bad = _epoch_refusal(hb_epoch) or check_payload(receipt)
    if bad is not None:
        return bad
    payload_sha256 = sha(receipt)
    packet_id = payload_sha256.split(":", 1)[1]
    successor = sha({"operation": OPERATION_ID, "check_receipt_sha256": payload_sha256,
                     "check_id": receipt["check_id"], "disposition": receipt["disposition"],
                     "change_digest": receipt["change_digest"], "head_sha": receipt["head_sha"]})
    boundary = {"operation": OPERATION_ID, "profile_id": PROFILE_ID, "disposition": receipt["disposition"],
                "check_id": receipt["check_id"], "check_receipt_sha256": payload_sha256,
                "change_digest": receipt["change_digest"], "head_sha": receipt["head_sha"]}
    try:
        # Resolve both stores before the first write, so a missing ledger location refuses with nothing written.
        ingress.repository_ledger.repository_store()
        ingress.organization_ledger.organization_store()
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - every resolver refusal is reported, none is retried
        return refusal("ORGANIZATION_LEDGER_LOCATION_UNRESOLVED", "WRITER_LEDGER_LOCATIONS_ARE_SUPPLIED",
                       "supply the repository and organization ledger locations the writer workflow declares",
                       "after the ledger locations resolve; nothing was written", detail=f"{type(exc).__name__}: {exc}")
    try:
        appended, replayed = ingress._append(
            TRANSITION_CLASS, packet_id, dict(receipt), hb_epoch,
            predecessor=payload_sha256, successor=successor, boundary_evidence=boundary,
            idempotent_on=IDEMPOTENT_ON)
    except ValueError as exc:
        if str(exc) == "ledger_receipt_collision":
            return refusal("CHECK_RECEIPT_PACKET_COLLISION", "ONE_PACKET_ID_BINDS_ONE_CHECK_RECEIPT",
                           "the recorded transition for this receipt digest stands; nothing new is minted",
                           "none; the recorded receipt is the evidence", detail=str(exc))
        return refusal("ORGANIZATION_LEDGER_APPEND_REFUSED", "CHECK_RECEIPT_APPEND_COMPLETES_AT_BOTH_LEVELS",
                       "repair the refusal the ledger reported; the writer publishes only when both receipts exist",
                       "after the ledger refusal is repaired", detail=f"{type(exc).__name__}: {exc}")
    repository = appended["repository_receipt"]
    organization = appended["organization_receipt"]
    for row in (repository, organization):
        hb = row.get("hb_reference") or {}
        if hb.get("derived_from_clock") is not False or type(hb.get("epoch")) is not int or hb["epoch"] < HB_ANCHOR_EPOCH:
            return refusal("HB_EPOCH_SOURCE_UNOBSERVED", "HB_EPOCH_IS_SUPPLIED_NOT_CLOCK_DERIVED",
                           "the stored receipt carries no supplied epoch; the writer workflow publishes nothing for this run",
                           "re-dispatch with a supplied epoch", receipt_sha256=row.get("receipt_sha256"))
    return {
        "schema": RESULT_SCHEMA,
        "operation": OPERATION_ID,
        "disposition": "ALLOW",
        "transition_class": TRANSITION_CLASS,
        "transition_replayed": replayed,
        "check_receipt_sha256": payload_sha256,
        "check_id": receipt["check_id"],
        "check_disposition": receipt["disposition"],
        "repository_receipt_sha256": repository["receipt_sha256"],
        "organization_receipt_sha256": organization["receipt_sha256"],
        "organization_receipt_key": ingress.repository_ledger.ledger_store.receipt_key(organization["receipt_sha256"]),
        "repository_receipt_source_key": ingress.repository_ledger.ledger_store.source_key(repository["receipt_sha256"]),
        "hb_epoch": repository["hb_reference"]["epoch"],
        "organization_receipt_preserves_repository_receipt": organization.get("repo_receipt_sha256") == repository["receipt_sha256"],
        "consequence_committed": True,
        "authority_effect": "NONE",
    }


def _self_verifies(doc: Any) -> bool:
    return isinstance(doc, dict) and doc.get("receipt_sha256") == sha({k: v for k, v in doc.items() if k != "receipt_sha256"})


def bind_check_receipt(location: str, result: Mapping[str, Any]) -> dict[str, Any]:
    """Read the appended pair back from `location` (a fresh fetch of the ref): sealed, in place, linked, self-identified."""
    store_mod = ingress.repository_ledger.ledger_store
    store = store_mod.open_store(store_mod.parse_locator(location))
    org_sha = result.get("organization_receipt_sha256")
    repo_sha = result.get("repository_receipt_sha256")
    org = store.get(store_mod.receipt_key(org_sha)) if isinstance(org_sha, str) else None
    repo = store.get(store_mod.source_key(repo_sha)) if isinstance(repo_sha, str) else None
    checks = {
        "organization_receipt_sealed": _self_verifies(org) and org.get("receipt_sha256") == org_sha,
        "repository_receipt_sealed_beside_it": _self_verifies(repo) and repo.get("receipt_sha256") == repo_sha,
        "organization_receipt_names_repository_receipt": isinstance(org, dict) and org.get("repo_receipt_sha256") == repo_sha,
        "operation_is_sv_check_receipt": isinstance(org, dict) and (org.get("boundary_evidence") or {}).get("operation") == OPERATION_ID,
        "evidence_is_a_valid_check_receipt": isinstance(repo, dict) and check_payload(repo.get("evidence")) is None,
        "evidence_is_the_appended_receipt": isinstance(repo, dict) and sha(repo.get("evidence")) == result.get("check_receipt_sha256"),
        "epoch_supplied_not_clock": all(isinstance(r, dict) and (r.get("hb_reference") or {}).get("derived_from_clock") is False
                                        for r in (org, repo)),
    }
    if not all(checks.values()):
        failed = sorted(k for k, v in checks.items() if not v)
        return {"schema": READBACK_SCHEMA, "disposition": "FAIL_CLOSED", "failure_code": "SV_CHECK_RECEIPT_READBACK_FAILED",
                "failed_predicate": failed[0].upper(), "required_evidence_or_repair": "the fresh fetch must hold the sealed pair: "
                + ", ".join(failed), "retry_entrypoint": "resident-runtime/sv_check_receipt_append.py::bind_check_receipt",
                "owning_existing_goal": OWNING_GOAL, "next_attempt": "after a fresh fetch of the published ref",
                "checks": checks, "readback_writes": False, "authority_effect": "NONE_READBACK_ONLY"}
    return {"schema": READBACK_SCHEMA, "disposition": "ALLOW", "location": location, "checks": checks,
            "organization_receipt_sha256": org_sha, "repository_receipt_sha256": repo_sha,
            "readback_writes": False, "authority_effect": "NONE_READBACK_ONLY"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--check-receipt", type=Path, required=True, help="the verifier's sv-check-receipt.v1 JSON file")
    a.add_argument("--hb-epoch", required=True, help="supplied epoch, ASCII digits >= 32; never from a clock")
    a.add_argument("--out", type=Path, default=None)
    r = sub.add_parser("readback")
    r.add_argument("--location", required=True)
    r.add_argument("--result", type=Path, required=True)
    r.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if args.cmd == "append":
        epoch = int(args.hb_epoch) if re.fullmatch(r"[0-9]+", args.hb_epoch or "") else args.hb_epoch
        try:
            receipt = json.loads(args.check_receipt.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            out = refusal("LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT", "ORGANIZATION_LEDGER_EVIDENCE_IS_A_SELF_IDENTIFYING_CHECK_RECEIPT",
                          "supply the verifier's receipt as one JSON object", "after a readable receipt is supplied; nothing was written",
                          detail=f"{type(exc).__name__}: {exc}")
        else:
            out = append_check_receipt(receipt, hb_epoch=epoch)
    else:
        out = bind_check_receipt(args.location, json.loads(args.result.read_text(encoding="utf-8")))
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0 if out.get("disposition") == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
