#!/usr/bin/env python3
"""Project an already-receipted governed StegOS actuator output into GADI evidence.

This adapter does not execute an actuator, mint authority, create credentials, or
infer an effect. It only validates an already-observed, pre-authorized governed
output receipt and projects the fields required by the GADI resident bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
OUT_REL = Path("state/gadi-resident-execution/source/actuator-observation.json")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("FAIL_CLOSED: governed output receipt must be a JSON object")
    return value


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(receipt: dict[str, Any], *, receipt_sha256: str) -> dict[str, Any]:
    require(receipt.get("task_id") in {None, PARENT_TASK_ID, TASK_ID}, "task identity mismatch")
    require(receipt.get("preauthorized_controlled_surface") is True, "actuator surface not pre-authorized/controlled")
    require(receipt.get("credential_material_exposed") is not True, "credential exposure reported")
    require(receipt.get("authority_effect") in {None, "NONE", "NONE_EXECUTION_EVIDENCE_ONLY"}, "authority drift")
    require(nonempty(receipt.get("receipt_pointer")), "governed output receipt pointer missing")
    require(nonempty(receipt.get("authority_reference")), "governed output authority reference missing")
    require(nonempty(receipt.get("target_node")), "governed output target node missing")
    require(nonempty(receipt.get("mode")), "governed output mode missing")
    require(nonempty(receipt.get("source")), "governed output source missing")
    require(nonempty(receipt.get("risk_class")), "governed output risk class missing")
    for field in ("execution_subject", "control_surface", "target_class", "observed_state"):
        require(nonempty(receipt.get(field)), f"{field} missing")
    require(nonempty(receipt.get("runtime_binding_ref")), "runtime binding missing")
    require(nonempty(receipt.get("intr_decision_ref")), "InTr decision reference missing")

    return {
        "schema": "stegverse.gadi-controlled-actuator-observation/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "execution_subject": receipt["execution_subject"],
        "control_surface": receipt["control_surface"],
        "target_class": receipt["target_class"],
        "runtime_binding_ref": receipt["runtime_binding_ref"],
        "intr_decision_ref": receipt["intr_decision_ref"],
        "observed_state": receipt["observed_state"],
        "effect_observed": bool(receipt.get("effect_observed", False)),
        "reassessment_required": bool(receipt.get("reassessment_required", True)),
        "stop_condition_observed": bool(receipt.get("stop_condition_observed", False)),
        "governed_output": {
            "target_node": receipt["target_node"],
            "mode": receipt["mode"],
            "source": receipt["source"],
            "duration": receipt.get("duration"),
            "risk_class": receipt["risk_class"],
            "authority_reference": receipt["authority_reference"],
            "receipt_pointer": receipt["receipt_pointer"],
            "source_receipt_sha256": receipt_sha256,
        },
        "actuator_executed_by_adapter": False,
        "authority_minted": False,
        "execution_claimed": False,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()

    receipt_path = args.receipt.expanduser().resolve()
    require(receipt_path.is_file(), "governed output receipt missing")
    observation = project(load(receipt_path), receipt_sha256=sha256(receipt_path))
    out = args.runtime_root.expanduser().resolve() / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name("." + out.name + ".tmp")
    tmp.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(json.dumps(observation, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
