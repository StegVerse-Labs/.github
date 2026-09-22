#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from canonical_state_transition_custody import (
    build_state_receipt,
    require_predecessor_master_records_closure,
    sha256_uri,
    submit_state_receipt,
)

CONTRACT_SCHEMA = "stegverse.conversation-evidence-service-performance-publication-contract/v1"
PACKAGE_SCHEMA = "stegverse.conversation-evidence-ingestion-package/v1"
AUTH_STATES = {
    "UNVERIFIED","SOURCE_EXPORT_VERIFIED","PARTICIPANT_ATTESTED",
    "COUNTERPARTY_ACKNOWLEDGED","PLATFORM_CORROBORATED","CONFLICTING_EVIDENCE",
}
FINDING_STATES = {
    "NOT_EVALUATED","PERFORMANCE_SUPPORTED","PARTIAL_PERFORMANCE_SUPPORTED",
    "NONPERFORMANCE_SUPPORTED","CONTESTED","INSUFFICIENT_EVIDENCE",
}
TRANSITION_ID = "CONVERSATION_EVIDENCE_INGESTED"

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def write_once_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)

def write_once_json(path: Path, value: Mapping[str, Any]) -> None:
    write_once_bytes(path, (json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))

def _required_string(obj: Mapping[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key}_required")
    return value

def build_ingestion_package(source: Mapping[str, Any], attachment_bytes: Mapping[str, bytes]) -> dict[str, Any]:
    record_id = _required_string(source, "record_id")
    capture_method = _required_string(source, "capture_method")
    source_platform = _required_string(source, "source_platform")
    source_locator = _required_string(source, "source_locator_or_export_identity")
    captured_at = _required_string(source, "captured_at")
    conversation_start = _required_string(source, "conversation_start")
    conversation_end = _required_string(source, "conversation_end")
    participants = source.get("participant_assertions")
    messages = source.get("message_sequence")
    transaction = source.get("transaction_binding")
    auth = source.get("authenticity")
    if not isinstance(participants, list) or not participants:
        raise ValueError("participant_assertions_required")
    if not isinstance(messages, list) or not messages:
        raise ValueError("message_sequence_required")
    if not isinstance(transaction, Mapping):
        raise ValueError("transaction_binding_required")
    if not isinstance(auth, Mapping) or auth.get("state") not in AUTH_STATES:
        raise ValueError("authenticity_state_invalid")
    finding_state = transaction.get("finding_state", "NOT_EVALUATED")
    if finding_state not in FINDING_STATES:
        raise ValueError("transaction_finding_state_invalid")

    normalized_messages = []
    attachment_manifest = []
    seen_ordinals = set()
    for message in messages:
        if not isinstance(message, Mapping):
            raise ValueError("message_invalid")
        ordinal = message.get("ordinal")
        if not isinstance(ordinal, int) or ordinal < 1 or ordinal in seen_ordinals:
            raise ValueError("message_ordinal_invalid")
        seen_ordinals.add(ordinal)
        speaker = _required_string(message, "speaker_assertion")
        exact = message.get("exact_content")
        if not isinstance(exact, str):
            raise ValueError("message_exact_content_required")
        row = {
            "ordinal": ordinal,
            "source_message_id": message.get("source_message_id"),
            "speaker_assertion": speaker,
            "timestamp_assertion": message.get("timestamp_assertion"),
            "timestamp_precision": message.get("timestamp_precision"),
            "exact_content": exact,
            "attachment_ids": list(message.get("attachment_ids") or []),
        }
        row["sha256"] = digest_bytes(canonical_json(row).encode("utf-8"))
        normalized_messages.append(row)

    normalized_messages.sort(key=lambda row: row["ordinal"])
    for attachment_id, raw in sorted(attachment_bytes.items()):
        if not isinstance(raw, (bytes, bytearray)):
            raise ValueError("attachment_bytes_required")
        referenced = [m["ordinal"] for m in normalized_messages if attachment_id in m["attachment_ids"]]
        if not referenced:
            raise ValueError(f"unreferenced_attachment:{attachment_id}")
        attachment_manifest.append({
            "attachment_id": attachment_id,
            "byte_length": len(raw),
            "sha256": digest_bytes(bytes(raw)),
            "message_ordinals": referenced,
            "capture_provenance": source_locator,
        })
    referenced_ids = {aid for m in normalized_messages for aid in m["attachment_ids"]}
    if referenced_ids != set(attachment_bytes.keys()):
        raise ValueError("attachment_reference_set_mismatch")

    original = {
        "record_id": record_id,
        "capture_method": capture_method,
        "source_platform": source_platform,
        "source_locator_or_export_identity": source_locator,
        "captured_at": captured_at,
        "conversation_start": conversation_start,
        "conversation_end": conversation_end,
        "participant_assertions": participants,
        "message_sequence": normalized_messages,
        "attachment_manifest": attachment_manifest,
    }
    original["original_bytes_sha256"] = digest_bytes(canonical_json(normalized_messages).encode("utf-8"))
    original["canonical_manifest_sha256"] = digest_bytes(canonical_json(original).encode("utf-8"))

    authenticity = {
        "record_id": record_id,
        "state": auth["state"],
        "verified_claims": list(auth.get("verified_claims") or []),
        "evidence_refs": list(auth.get("evidence_refs") or []),
        "authority_effect": "NONE_EVIDENCE_CLASSIFICATION_ONLY",
    }
    authenticity["sha256"] = digest_bytes(canonical_json(authenticity).encode("utf-8"))

    binding = {
        "record_id": record_id,
        "service_representation": transaction.get("service_representation"),
        "agreement_or_scope": transaction.get("agreement_or_scope"),
        "invoice_or_request": transaction.get("invoice_or_request"),
        "payment_evidence": transaction.get("payment_evidence"),
        "delivery_or_performance_evidence": transaction.get("delivery_or_performance_evidence"),
        "refund_or_remediation": transaction.get("refund_or_remediation"),
        "dispute_event": transaction.get("dispute_event"),
        "finding_state": finding_state,
        "finding_authority_effect": "NONE_NOT_ADJUDICATION",
    }
    binding["sha256"] = digest_bytes(canonical_json(binding).encode("utf-8"))

    package = {
        "schema": PACKAGE_SCHEMA,
        "record_id": record_id,
        "evidence_original": original,
        "authenticity_envelope": authenticity,
        "transaction_binding": binding,
        "authority_effect": "NONE_EVIDENCE_INGESTION_ONLY",
    }
    package["package_sha256"] = digest_bytes(canonical_json(package).encode("utf-8"))
    return package

def persist_ingestion_package(package: Mapping[str, Any], attachment_bytes: Mapping[str, bytes], root: Path) -> Path:
    record_id = _required_string(package, "record_id")
    record_root = root / record_id
    record_root.mkdir(parents=True, exist_ok=False)
    write_once_json(record_root / "package.json", package)
    for attachment_id, raw in attachment_bytes.items():
        write_once_bytes(record_root / "attachments" / attachment_id, bytes(raw))
    return record_root

def custody_ingestion(
    package: Mapping[str, Any],
    *,
    predecessor_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    record_id = _required_string(package, "record_id")
    prior_ref, predecessor_evidence = require_predecessor_master_records_closure(
        predecessor_receipt_sha256,
        successor_transition_id=TRANSITION_ID,
    )
    evidence_items = list(predecessor_evidence)
    for evidence_type, key in (
        ("CONVERSATION_EVIDENCE_ORIGINAL","evidence_original"),
        ("CONVERSATION_AUTHENTICITY_ENVELOPE","authenticity_envelope"),
        ("SERVICE_TRANSACTION_BINDING","transaction_binding"),
    ):
        content = package.get(key)
        if not isinstance(content, Mapping):
            raise ValueError(f"{key}_required")
        evidence_items.append({
            "evidence_id": f"{record_id}:{key}",
            "evidence_type": evidence_type,
            "origin_transition_id": TRANSITION_ID,
            "encoding": "canonical-json",
            "sha256": digest_bytes(canonical_json(content).encode("utf-8")),
            "content": dict(content),
        })
    receipt = build_state_receipt(
        transition_id=TRANSITION_ID,
        transition_sequence=1,
        subject_or_correlation_id=record_id,
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=prior_ref,
        resulting_state_ref_or_hash="sha256:" + _required_string(package, "package_sha256"),
        governance_decision_ref_where_applicable=None,
        transition_evidence={
            "transition": TRANSITION_ID,
            "package_sha256": package["package_sha256"],
            "publication_performed": False,
            "adjudication_performed": False,
            "authority_effect": "NONE",
        },
        required_evidence_manifest=evidence_items,
        proof_scope="CONVERSATION_EVIDENCE_INGESTION_ONLY",
        proof_ceiling="MASTER_RECORDS_CUSTODY_RECONSTRUCTION_ONLY",
    )
    result = submit_state_receipt(receipt)
    if not (
        result.get("state") == "RECORDED"
        and result.get("reconstruction_status") == "PASS"
        and result.get("required_evidence_validation_status") == "PASS"
        and result.get("receipt_sha256") == result.get("reconstructed_receipt_sha256")
    ):
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_INGESTION_CUSTODY_NOT_CLOSED","master_records":result,"authority_effect":"NONE"}
    return {"state":"RECORDED","receipt":receipt,"master_records":result,"authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY"}
