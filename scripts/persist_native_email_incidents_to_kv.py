#!/usr/bin/env python3
"""Persist normalized native-email failure incidents into an already-materialized KnowledgeVault.

This writer is deliberately narrow. It does not mount providers, resolve credentials,
or create a second ingestion path. The caller supplies an already-materialized KV root.
Records are append-only, deterministic, exact-byte read back, and keyed by incident plus
its exact Gmail observation-ref set so replay is idempotent without overwriting history.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

KV_RELATIVE_ROOT = Path("05_Projects/StegVerse/Operations/GitHubFailureEmail")
SCHEMA = "stegverse.kv.github-failure-email-observation/v1"
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
COSV_TASK_VECTOR = "10100000100000"


class NativeEmailKVPersistenceError(RuntimeError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise NativeEmailKVPersistenceError(reason)


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_uri(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _safe_component(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    require(bool(cleaned), "incident_id_not_filename_safe")
    return cleaned[:96]


def validate_kv_root(kv_root: str | os.PathLike[str]) -> Path:
    root = Path(kv_root).expanduser().resolve()
    require(root.is_dir(), "kv_root_not_materialized")
    require(root.name == "KnowledgeVault" or (root / "_System").exists() or (root / "00_Inbox").exists(), "kv_root_not_knowledgevault")
    return root


def normalize_record(incident: Mapping[str, Any]) -> dict[str, Any]:
    require(isinstance(incident, Mapping), "incident_object_required")
    incident_id = incident.get("incident_id")
    require(isinstance(incident_id, str) and bool(incident_id), "incident_id_required")
    refs = incident.get("observation_refs")
    require(isinstance(refs, list) and refs and all(isinstance(ref, str) and ref for ref in refs), "observation_refs_required")
    refs = sorted(set(refs))
    record = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "cosv_task_vector": COSV_TASK_VECTOR,
        "incident_id": incident_id,
        "kind": incident.get("kind"),
        "normalized_repository": incident.get("normalized_repository"),
        "normalized_workflow": incident.get("normalized_workflow"),
        "normalized_error_signature": incident.get("normalized_error_signature"),
        "observation_count": len(refs),
        "observation_refs": refs,
        "source_provider": "GMAIL",
        "source_class": "GITHUB_OPERATIONAL_EMAIL",
        "state": "OBSERVED_NOT_EXECUTION_EVIDENCE",
        "task_ingress_required": bool(incident.get("task_ingress_required", True)),
        "email_observation_is_execution_evidence": False,
        "incident_proposal_mints_execution_authority": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_STORAGE_EVIDENCE_ONLY",
    }
    require(all(isinstance(record[key], str) and record[key] for key in ("normalized_repository", "normalized_workflow", "normalized_error_signature")), "normalized_incident_fields_required")
    return record


def persist_incident(incident: Mapping[str, Any], *, kv_root: str | os.PathLike[str]) -> dict[str, Any]:
    root = validate_kv_root(kv_root)
    record = normalize_record(incident)
    payload = canonical_bytes(record)
    observation_digest = hashlib.sha256("\n".join(record["observation_refs"]).encode("utf-8")).hexdigest()[:16]
    filename = f"{_safe_component(record['incident_id'])}-{observation_digest}.json"
    destination_dir = (root / KV_RELATIVE_ROOT).resolve()
    require(destination_dir == root or root in destination_dir.parents, "kv_destination_escaped_root")
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / filename

    if destination.exists():
        existing = destination.read_bytes()
        require(existing == payload, "kv_write_once_collision")
        result = "NOOP_EXISTING_IDENTICAL"
    else:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(destination, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                destination.unlink(missing_ok=True)
            finally:
                raise
        result = "STORED_VERIFIED"

    readback = destination.read_bytes()
    require(readback == payload, "kv_exact_byte_readback_mismatch")
    return {
        "schema": "stegverse.kv.github-failure-email-write-receipt/v1",
        "state": "KV_STORED_VERIFIED",
        "result": result,
        "incident_id": record["incident_id"],
        "observation_refs": record["observation_refs"],
        "relative_path": str(KV_RELATIVE_ROOT / filename),
        "record_hash": sha256_uri(payload),
        "exact_byte_readback_verified": True,
        "credential_material_present": False,
        "authority_effect": "NONE_STORAGE_EVIDENCE_ONLY",
    }


def persist_incidents(incidents: list[dict[str, Any]], *, kv_root: str | os.PathLike[str]) -> list[dict[str, Any]]:
    return [persist_incident(incident, kv_root=kv_root) for incident in incidents]
