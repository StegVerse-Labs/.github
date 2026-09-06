#!/usr/bin/env python3
"""Resolve the current meaning of a retained StegVerse machine-preflight receipt.

Historical receipts remain immutable evidence. A sibling ``*.supersession.json`` may
change current admissibility only when it validates as an explicit, non-authorizing
successor for that exact receipt. Malformed or mismatched supersession state fails
closed rather than silently reviving the historical result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SUPERSESSION_SCHEMA = "stegverse.preflight-supersession/v1"
OUTPUT_SCHEMA = "stegverse.preflight-current-resolution/v1"


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"UNREADABLE_JSON:{path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _repo_relative(root: Path, path: Path) -> str:
    root = root.resolve()
    path = path.resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("PREFLIGHT_RECEIPT_OUTSIDE_ROOT") from exc


def resolve_current_preflight(root: Path, receipt_ref: str) -> dict[str, Any]:
    root = Path(root).resolve()
    receipt_path = (root / receipt_ref).resolve()
    normalized_ref = _repo_relative(root, receipt_path)
    historical = _read_object(receipt_path)
    historical_state = historical.get("state")
    historical_verdict = historical.get("verdict")

    supersession_path = receipt_path.with_name(receipt_path.stem + ".supersession.json")
    if not supersession_path.exists():
        current_pass = historical_state == "PASS" and historical_verdict in (None, "PASS")
        return {
            "schema": OUTPUT_SCHEMA,
            "receipt_ref": normalized_ref,
            "historical_state": historical_state,
            "historical_verdict": historical_verdict,
            "supersession_ref": None,
            "current_disposition": "PASS" if current_pass else "HISTORICAL_PREFLIGHT_NOT_PASS",
            "current_admissible": bool(current_pass),
            "runtime_truth_inferred": False,
            "execution_admission_inferred": False,
            "authority_effect": "NONE_PREFLIGHT_RESOLUTION_ONLY",
        }

    supersession = _read_object(supersession_path)
    if supersession.get("schema") != SUPERSESSION_SCHEMA:
        raise ValueError("SUPERSESSION_SCHEMA_MISMATCH")
    if supersession.get("supersedes") != normalized_ref:
        raise ValueError("SUPERSESSION_TARGET_MISMATCH")
    authority_effect = str(supersession.get("authority_effect") or "")
    if not authority_effect.startswith("NONE"):
        raise ValueError("SUPERSESSION_AUTHORITY_ESCALATION")
    if supersession.get("runtime_truth_inferred") is not False:
        raise ValueError("SUPERSESSION_RUNTIME_TRUTH_INFERENCE_FORBIDDEN")
    if supersession.get("execution_admission_inferred") is not False:
        raise ValueError("SUPERSESSION_EXECUTION_ADMISSION_INFERENCE_FORBIDDEN")
    disposition = supersession.get("current_disposition")
    if not isinstance(disposition, str) or not disposition.strip():
        raise ValueError("SUPERSESSION_CURRENT_DISPOSITION_REQUIRED")

    return {
        "schema": OUTPUT_SCHEMA,
        "receipt_ref": normalized_ref,
        "historical_state": historical_state,
        "historical_verdict": historical_verdict,
        "supersession_ref": _repo_relative(root, supersession_path),
        "supersession_id": supersession.get("supersession_id"),
        "current_disposition": disposition,
        "current_admissible": False,
        "runtime_truth_inferred": False,
        "execution_admission_inferred": False,
        "authority_effect": "NONE_PREFLIGHT_RESOLUTION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--require-current-pass", action="store_true")
    args = parser.parse_args()
    try:
        resolved = resolve_current_preflight(Path(args.root), args.receipt)
    except ValueError as exc:
        print(json.dumps({"schema": OUTPUT_SCHEMA, "error": str(exc), "current_admissible": False}, sort_keys=True))
        return 2
    print(json.dumps(resolved, indent=2, sort_keys=True))
    if args.require_current_pass and not resolved["current_admissible"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
