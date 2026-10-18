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
  * Time: ``hb_reference`` comes from kernel.hb_reference(epoch=<supplied int >= 32>) (org-kernel/kernel.py:68-74,
    the storage location), so derived_from_clock is False. The append epoch and the check receipt's own
    ``hb_epoch`` must both pass the shared rule org-kernel/kernel.py::supplied_epoch_failure (L236-269, blob
    ffec5d64, SHARED_RULE_SHA256 726248a5...) and must be equal. Unobserved -> FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED,
    absent/null/UNKNOWN_NOT_AUTHENTICALLY_OBSERVED -> FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED; any other malformed or
    different value -> DENY HB_EPOCH_MISMATCH; in both cases before anything is written. A clock-derived epoch (only
    possible on a stored hb_reference) is FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED. A clock epoch is never written.
  * Command: a check whose command P1's row SV-CHANGE-REQUIRED-CHECKS-001 (vendored at
    tests/vendor/p1_7d940851/required-checks.json, blob 42405012) does not declare is FAIL_CLOSED CHECK_COMMAND_UNDECLARED before any append. The one exception is the verifier's
    own FAIL_CLOSED CHECK_COMMAND_UNDECLARED receipt, which is P1's rule (sv_work_items.validate_check_receipt).

The append path is intr_destination_ingress._append (repository append, then
aggregate_transition), under the writer workflow's ORGANIZATION_LEDGER_LOCK
concurrency group. Validation happens before any write. Every refusal is a
six-field FAIL_CLOSED with consequence_committed false, and nothing is written
for it. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
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
# P1's schemas/sv-check-receipt.v1.schema.json, single-sourced as the Lane D vendored copy pinned to P1 #3264 head
# 7d940851, blob 070f13f4 (this PR touches no P1 path).
CHECK_RECEIPT_SCHEMA_PATH = ROOT / "tests" / "vendor" / "p1_7d940851" / "sv-check-receipt.v1.schema.json"
CHECK_RECEIPT_SCHEMA_BLOB = "070f13f468558ca08aa5162a8f34431608fc1404"
RESULT_SCHEMA = "stegverse.org-sv-check-receipt-append-result/v1"
EPOCH_MISMATCH = "HB_EPOCH_MISMATCH"
READBACK_SCHEMA = "stegverse.org-sv-check-receipt-readback/v1"
OWNING_GOAL = "StegVerse-org/.github#163 (REQUIRED_CHECK_RECEIPTS_ARE_S1_VERIFIER_OUTPUTS_APPENDED_BY_ORG_WRITER)"
RETRY = "resident-runtime/sv_check_receipt_append.py::append_check_receipt"
HB_ANCHOR_EPOCH = 32  # org-kernel/kernel.py HB_ANCHOR_EPOCH
# P1's row SV-CHANGE-REQUIRED-CHECKS-001 (data/sv-work-items/required-checks.json), single-sourced as a Lane D vendored
# copy pinned to P1 #3264 head 7d940851, blob 42405012; this PR does not touch P1's path or depend on #3264 landing.
REQUIRED_CHECKS_PATH = ROOT / "tests" / "vendor" / "p1_7d940851" / "required-checks.json"
REQUIRED_CHECKS_BLOB = "424050129f4ddfa7e14aac61c68c7037f075a709"
P1_REQUIRED_CHECKS_PATH = "data/sv-work-items/required-checks.json"
CHECK_COMMAND_PREDICATE = "CHECK_HAS_OFFLINE_COMMAND"
EPOCH_SOURCE_PREDICATE = "ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH"
EPOCH_TIE_PREDICATE = "CHECK_RECEIPT_HB_EPOCH_EQUALS_APPEND_HB_EPOCH"
# sha256 of org-kernel/kernel.py::supplied_epoch_failure (L236-269 at blob ffec5d64): from "def supplied_epoch_failure"
# to the next top-level def, trailing whitespace stripped (the segment rule of P1 sv_work_items.supplied_epoch_rule_sha256).
SHARED_RULE_SHA256 = "726248a585904b52cfe2eec1754e7ce582f67d6b501bd664bb7bee80bce9b7ef"
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
kernel = ingress.repository_ledger.kernel
REQUIRED_CHECKS = json.loads(REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))


def supplied_epoch_rule_sha256(source: str) -> str | None:
    if "def supplied_epoch_failure" not in source:
        return None
    a = source.index("def supplied_epoch_failure")
    b = source.find("\ndef ", a + 5)
    return hashlib.sha256(source[a:b if b >= 0 else len(source)].rstrip().encode("utf-8")).hexdigest()


KERNEL_RULE_SHA256 = supplied_epoch_rule_sha256((ROOT / "org-kernel" / "kernel.py").read_text(encoding="utf-8"))
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
                       "supply a complete, valid " + CHECK_RECEIPT_SCHEMA_ID + " receipt (P1 schemas/sv-check-receipt.v1.schema.json, vendored blob 070f13f4)",
                       "after the verifier re-emits a valid receipt; nothing was written", schema_errors=errors)
    return None


def command_declared(check_id: str, row: Mapping[str, Any] = REQUIRED_CHECKS) -> bool:
    """P1's rule (sv_work_items.command_declared @7d940851): argv (a non-empty list), or a verifier built-in
    {verifier_builtin == check_id, verifier_ref, predicate} with command_paths empty."""
    c = (row.get("checks") or {}).get(check_id) or {}
    oc = c.get("offline_command")
    if isinstance(oc, list) and oc:
        return True
    return (isinstance(oc, dict) and all(isinstance(oc.get(k), str) and oc[k].strip()
                                         for k in ("verifier_builtin", "verifier_ref", "predicate"))
            and c.get("command_paths") == [] and oc["verifier_builtin"] == check_id)


def _command_refusal(receipt: Mapping[str, Any]) -> dict[str, Any] | None:
    if command_declared(receipt["check_id"]):
        return None
    if receipt["disposition"] == "FAIL_CLOSED" and receipt.get("failure_code") == "CHECK_COMMAND_UNDECLARED":
        return None  # the verifier's own six-field refusal for an undeclared command is the receipt to ledger
    return refusal("CHECK_COMMAND_UNDECLARED", CHECK_COMMAND_PREDICATE,
                   "the row " + P1_REQUIRED_CHECKS_PATH + "#checks." + receipt["check_id"] + " (vendored blob 42405012)" + " declares no offline "
                   "command; the only receipt that can be appended for it is the verifier's FAIL_CLOSED CHECK_COMMAND_UNDECLARED",
                   "after the row declares the command, or the verifier emits CHECK_COMMAND_UNDECLARED; nothing was written",
                   check_id=receipt["check_id"], receipt_disposition=receipt["disposition"])


def _unobserved(detail: str, **extra: Any) -> dict[str, Any]:
    return refusal("HB_EPOCH_SOURCE_UNOBSERVED", EPOCH_SOURCE_PREDICATE,
                   "supply the append epoch as an integer and carry the same supplied epoch in the check receipt; both must "
                   "pass org-kernel/kernel.py::supplied_epoch_failure (SHARED_RULE_SHA256 " + SHARED_RULE_SHA256 + ")",
                   "after a supplied epoch is observed on both; nothing was written",
                   detail=detail, shared_rule_sha256=SHARED_RULE_SHA256, epoch_storage="org-kernel/kernel.py:68-74 hb_reference.epoch",
                   **extra)


UNKNOWN_SENTINEL = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"


def _mismatch(detail: str, **extra: Any) -> dict[str, Any]:
    out = refusal(EPOCH_MISMATCH, EPOCH_TIE_PREDICATE,
                  "append the receipt at the epoch it carries: hb_epoch input (an int) = $.evidence.hb_epoch (ASCII digits), "
                  "both passing org-kernel/kernel.py::supplied_epoch_failure (SHARED_RULE_SHA256 " + SHARED_RULE_SHA256 + ")",
                  "re-dispatch with the receipt's own supplied epoch; nothing was written",
                  detail=detail, shared_rule_sha256=SHARED_RULE_SHA256, **extra)
    out["disposition"] = "DENY"
    return out


def _epoch_refusal(receipt: Mapping[str, Any], hb_epoch: Any) -> dict[str, Any] | None:
    """The epoch tie (orchestrator ruling, refined 15:59Z):
      FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED: the append epoch or the receipt's hb_epoch is absent, null or the sentinel
        UNKNOWN_NOT_AUTHENTICALLY_OBSERVED; or the loaded kernel rule is not the pinned shared rule.
      DENY HB_EPOCH_MISMATCH: any other value failing the shared rule (bool, float, coerced text, < 32), an append epoch
        that is not an int, a receipt epoch that is not ASCII text (as P1 verify_admission_hb_epoch), or unequal values.
    A clock-derived epoch can only appear on a stored hb_reference (the sealed source); see _stored_epoch_refusal."""
    if KERNEL_RULE_SHA256 != SHARED_RULE_SHA256:
        return _unobserved("org-kernel/kernel.py::supplied_epoch_failure is not the pinned shared rule",
                           kernel_rule_sha256=KERNEL_RULE_SHA256)
    mine = receipt.get("hb_epoch")
    for side, value in (("append epoch", hb_epoch), ("check receipt hb_epoch", mine)):
        if value is None or value == UNKNOWN_SENTINEL:
            return _unobserved(side + " is absent, null or " + UNKNOWN_SENTINEL, side=side, value=repr(value))
    bad = kernel.supplied_epoch_failure(hb_epoch)
    if bad is not None or type(hb_epoch) is not int:
        return _mismatch("append epoch " + repr(hb_epoch) + ": " + (bad[0] + ": " + bad[1] if bad else "not an int"),
                         hb_epoch=repr(hb_epoch), receipt_hb_epoch=repr(mine))
    bad = kernel.supplied_epoch_failure(mine)
    if bad is not None or not isinstance(mine, str):
        return _mismatch("check receipt hb_epoch " + repr(mine) + ": " + (bad[0] + ": " + bad[1] if bad else "not ASCII text"),
                         hb_epoch=hb_epoch, receipt_hb_epoch=repr(mine))
    if int(mine) != hb_epoch:
        return _mismatch("the receipt's epoch differs from the append epoch", hb_epoch=hb_epoch, receipt_hb_epoch=mine)
    return None


def _stored_epoch_refusal(row: Any, hb_epoch: int) -> dict[str, Any] | None:
    """A stored receipt: sealed, and hb_reference.epoch (kernel.py:68-74) an int that passes the shared rule with its
    reference (derived_from_clock exactly false) and equals the append epoch. This is the sealed source side: unsealed,
    clock-derived or non-int -> FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED (as P1 base_ledger_head_epoch -> None and the
    readback-slot refusals of verify_admission_hb_epoch); a different int -> DENY HB_EPOCH_MISMATCH."""
    if not _self_verifies(row):
        return _unobserved("a stored receipt does not verify against its body")
    hb = row.get("hb_reference")
    ep = hb.get("epoch") if isinstance(hb, dict) else None
    if type(ep) is not int or kernel.supplied_epoch_failure(ep, hb) is not None or hb.get("derived_from_clock") is not False:
        return _unobserved("a stored hb_reference.epoch is not a supplied int epoch", receipt_sha256=row.get("receipt_sha256"))
    if ep != hb_epoch:
        out = refusal(EPOCH_MISMATCH, EPOCH_TIE_PREDICATE, "the stored receipt carries another epoch than this append",
                      "none; the recorded receipt stands", receipt_sha256=row.get("receipt_sha256"), stored_epoch=ep, hb_epoch=hb_epoch)
        out["disposition"] = "DENY"
        return out
    return None


def append_check_receipt(receipt: Any, *, hb_epoch: Any) -> dict[str, Any]:
    """Append `receipt` as the repository receipt's $.evidence and aggregate it into the organization ledger."""
    if not isinstance(receipt, dict) or receipt.get("schema") != CHECK_RECEIPT_SCHEMA_ID:
        return check_payload(receipt)
    bad = _epoch_refusal(receipt, hb_epoch) or check_payload(receipt) or _command_refusal(receipt)
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
        bad = _stored_epoch_refusal(row, hb_epoch)
        if bad is not None:
            bad["consequence_committed"] = "LOCAL_ONLY_NOT_PUBLISHED"  # the writer workflow pushes nothing after a refusal
            return bad
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
