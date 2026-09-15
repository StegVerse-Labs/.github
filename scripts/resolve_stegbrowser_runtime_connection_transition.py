#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_ID = "STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001"
PARENT_TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
MANIFEST_REF = "control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json"
SOURCE_REFRESH_RT = "RT-SOVEREIGN-SOURCE-REFRESH-001"
INTR_PROTOCOL_RT = "RT-INTR-PROTOCOL-ESTABLISH-001"


class TransitionResolutionError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TransitionResolutionError(message)


def resolve(observation: dict[str, Any]) -> dict[str, Any]:
    require(observation.get("schema") == "stegverse.intr-runtime-connection-transition-observation/v1", "transition_observation_schema_mismatch")
    require(observation.get("task_id") == TASK_ID, "task_id_mismatch")
    require(observation.get("parent_task_id") == PARENT_TASK_ID, "parent_task_id_mismatch")
    require(observation.get("cosv") == COSV, "cosv_mismatch")
    require(observation.get("manifest_ref") == MANIFEST_REF, "manifest_ref_mismatch")
    require(observation.get("authority_owner") == "Interlock/InTr", "transition_authority_mismatch")
    require(observation.get("authority_effect") == "OBSERVATION_ONLY", "observation_must_not_mint_authority")

    callable_value = observation.get("callable")
    refreshable_value = observation.get("refreshable")
    protocol_resolved = observation.get("applicable_protocol_resolved")
    require(isinstance(callable_value, bool), "callable_must_be_boolean")
    require(isinstance(refreshable_value, bool), "refreshable_must_be_boolean")
    require(isinstance(protocol_resolved, bool), "applicable_protocol_resolved_must_be_boolean")

    selected: list[str] = []
    if callable_value and refreshable_value:
        selected.append(SOURCE_REFRESH_RT)
    if callable_value and not protocol_resolved:
        selected.append(INTR_PROTOCOL_RT)

    if not callable_value:
        disposition = "NOT_CALLABLE_NO_EXECUTION_MATERIALIZATION"
    elif selected:
        disposition = "CALLABLE_SELECT_MATCHING_REUSABLE_CAPABILITIES"
    else:
        disposition = "CALLABLE_NO_PRE_INGRESS_REUSABLE_TASK_REQUIRED"

    return {
        "schema": "stegverse.stegbrowser-runtime-connection-resolution/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv": COSV,
        "manifest_ref": MANIFEST_REF,
        "authority_owner": "Interlock/InTr",
        "authority_effect": "NONE_SELECTION_ONLY",
        "callable": callable_value,
        "refreshable": refreshable_value,
        "applicable_protocol_resolved": protocol_resolved,
        "selected_reusable_tasks": selected,
        "disposition": disposition,
        "workercoordinator_claim_required_before_execution": callable_value,
        "intr_admission_required_before_transport": callable_value,
        "round_trip_1_payload_processing_allowed_by_this_resolution": False,
        "source_refresh_selected_only_when_callable_and_refreshable": SOURCE_REFRESH_RT in selected,
        "protocol_establishment_selected_only_when_callable_and_protocol_unresolved": INTR_PROTOCOL_RT in selected,
        "second_user_operated_device_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transition-observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    observation = json.loads(args.transition_observation.read_text(encoding="utf-8"))
    result = resolve(observation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
