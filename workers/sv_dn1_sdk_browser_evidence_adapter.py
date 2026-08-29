#!/usr/bin/env python3
"""Validate an authentic SV-DN-1 browser bundle and expose legacy upstream state."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

BUNDLE_ENV = "STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE"
BOUND_ENV = "STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_BOUND = Path.home() / ".stegverse" / "state" / "sv-dn1-sdk-first-round"
WORKER = Path(__file__).with_name("sv_dn1_sdk_first_round_worker.py")
POLICY_ID = "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001"
TRANSPORT_PROFILE = "stegverse.universal-intr.adjacent-hop/v1"


def canonical(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, (int, float)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(canonical(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canonical(value[k]) for k in sorted(value)) + "}"
    raise TypeError(type(value).__name__)


def sha256(value: Any) -> str:
    raw = value if isinstance(value, str) else canonical(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_bundle(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"browser observation bundle not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("browser observation bundle must be an object")
    return value


def replay(rows: list[dict[str, Any]]) -> str | None:
    previous = None
    for index, row in enumerate(rows, 1):
        if row.get("schema") != "stegos.web_bootstrap_journal_entry.v1":
            raise RuntimeError("journal schema mismatch")
        if row.get("sequence") != index:
            raise RuntimeError("journal sequence gap")
        if row.get("previous_entry_sha256") != previous:
            raise RuntimeError("journal previous-entry hash mismatch")
        receipt_hash = sha256(row.get("receipt"))
        if receipt_hash != row.get("receipt_sha256"):
            raise RuntimeError("journal receipt hash mismatch")
        check = {
            "schema": row["schema"],
            "sequence": row["sequence"],
            "previous_entry_sha256": row.get("previous_entry_sha256"),
            "receipt": row.get("receipt"),
            "receipt_sha256": row.get("receipt_sha256"),
        }
        entry_hash = sha256(check)
        if entry_hash != row.get("entry_sha256"):
            raise RuntimeError("journal entry hash mismatch")
        previous = entry_hash
    return previous


def validate(bundle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if bundle.get("schema") != "stegverse.sv-dn1.browser-resident-observation-bundle/v3":
        raise RuntimeError("unexpected browser observation bundle schema")
    if bundle.get("state") != "OBSERVED" or bundle.get("observation_class") != "AUTHENTIC_ESTABLISHED_STEGVERSE_WEB_NODE":
        raise RuntimeError("bundle is not an authentic observed established-node run")
    rows = bundle.get("continued_receipts")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("continued receipt journal missing")
    tail = replay(rows)
    report = bundle.get("journal_replay") or {}
    if report.get("state") != "PASS" or report.get("entries") != len(rows) or report.get("tail_sha256") != tail:
        raise RuntimeError("journal replay report mismatch")

    resident = bundle.get("resident_receipt") or {}
    capture = bundle.get("source_capture") or {}
    exchange = bundle.get("semantic_exchange") or {}
    intr = bundle.get("intr_receipt") or {}
    claim = bundle.get("claim_entry") or {}
    terminal = bundle.get("terminal_entry") or {}
    reconstruction = bundle.get("reconstruction_entry") or {}

    if resident.get("state") != "COMPLETE" or resident.get("transition_id") != "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE":
        raise RuntimeError("resident receipt is not complete")
    if capture.get("raw_sha256") != resident.get("raw_response_sha256"):
        raise RuntimeError("resident/source raw digest mismatch")
    if exchange.get("exchange_id") != resident.get("semantic_exchange_id"):
        raise RuntimeError("resident/exchange identity mismatch")
    if intr.get("state") != "COMPLETE" or intr.get("route_id") != "SV-DN-1-HF-PUBLIC":
        raise RuntimeError("InTr receipt is not complete")
    if intr.get("exchange_id") != exchange.get("exchange_id"):
        raise RuntimeError("InTr/exchange identity mismatch")
    claims = intr.get("claims") or {}
    if claims.get("universal_intr_policy_id") != POLICY_ID or intr.get("transport_profile") != TRANSPORT_PROFILE:
        raise RuntimeError("Universal InTr policy/profile mismatch")
    if claims.get("boundary_from") != "EXTERNAL_SYSTEM" or claims.get("boundary_to") != "STEGOS_ECOSYSTEM":
        raise RuntimeError("Universal InTr boundary mismatch")
    if intr.get("destination_validation") != "PASS" or intr.get("lineage_verified") is not True:
        raise RuntimeError("InTr destination/lineage validation failed")
    tx_hash = (exchange.get("far_side_receipt") or {}).get("transformation_hash")
    if not tx_hash or intr.get("previous_receipt_hash") != tx_hash or intr.get("source_transform_hash") != tx_hash:
        raise RuntimeError("Interlock/InTr previous-receipt lineage mismatch")
    if claims.get("sdk_admitted") is not False or claims.get("runtime_activation_claimed") is not False or claims.get("production_interlock_runtime_activated") is not False:
        raise RuntimeError("pre-SDK bundle overclaims activation/admission")
    if terminal.get("receipt", {}).get("claim_entry_sha256") != claim.get("entry_sha256"):
        raise RuntimeError("claim/terminal linkage mismatch")
    if reconstruction.get("receipt", {}).get("terminal_entry_sha256") != terminal.get("entry_sha256"):
        raise RuntimeError("terminal/reconstruction linkage mismatch")
    if reconstruction.get("receipt", {}).get("state") != "PASS" or reconstruction.get("receipt", {}).get("same_execution") is not True:
        raise RuntimeError("reconstruction did not prove same execution")
    return resident, capture, exchange, intr


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(bundle_path: Path, bound: Path) -> tuple[Path, Path]:
    bundle = load_bundle(bundle_path)
    resident, capture, exchange, intr = validate(bundle)
    root = bound / "upstream-adapter"
    resident_root = root / "resident"
    intr_root = root / "intr"
    write_json(resident_root / "receipts/latest.json", resident)
    write_json(resident_root / "observed/source-capture.json", capture)
    write_json(resident_root / "observed/exchange.json", exchange)
    write_json(intr_root / "receipts/latest.json", intr)
    write_json(root / "adapter-receipt.json", {
        "schema": "stegverse.sv-dn1.browser-evidence-adapter-receipt/v1",
        "state": "COMPLETE",
        "source_bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        "journal_tail_sha256": (bundle.get("journal_replay") or {}).get("tail_sha256"),
        "node_id": (bundle.get("node_registration") or {}).get("node_id"),
        "device_continuity_id": (bundle.get("node_registration") or {}).get("device_continuity_id"),
        "existing_node_reused": True,
        "new_node_identity_minted": False,
        "authority_effect": "NONE",
    })
    return resident_root, intr_root


def main() -> int:
    raw = str(os.getenv(BUNDLE_ENV) or "").strip()
    if not raw:
        os.execv(sys.executable, [sys.executable, str(WORKER)])
        return 0
    bound = Path(os.getenv(BOUND_ENV) or DEFAULT_BOUND).expanduser().resolve()
    resident_root, intr_root = materialize(Path(raw).expanduser().resolve(), bound)
    env = dict(os.environ)
    env["STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT"] = str(resident_root)
    env["STEGVERSE_SV_DN1_INTR_STATE_ROOT"] = str(intr_root)
    return subprocess.call([sys.executable, str(WORKER)], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
