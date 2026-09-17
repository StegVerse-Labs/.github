from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_reusable_task_construct.py"
TASK_ID = "SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001"
COSV = "50000000107001"
RT_ID = "RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001"


def load_module():
    spec = importlib.util.spec_from_file_location("materialize_reusable_task_construct", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_child_pointer_resolves_from_canonical_index_shard() -> None:
    module = load_module()
    aggregate = json.loads((ROOT / "control" / "task-vector-index.json").read_text(encoding="utf-8"))
    assert not any(row.get("task_id") == TASK_ID for row in aggregate["tasks"])

    effective = module.load_effective_cosv_index()
    rows = [row for row in effective["tasks"] if row.get("task_id") == TASK_ID]
    assert len(rows) == 1
    assert rows[0]["vector"] == COSV
    assert rows[0]["source_state_vector_ref"] == f"control/task-vectors/{TASK_ID}.json"
    assert rows[0]["authority_effect"] == "NONE"

    args = argparse.Namespace(
        reusable_task_id=RT_ID,
        invocation_id=f"{TASK_ID}:TVC-RUNTIME-BINDING-001",
        parameters_json=json.dumps({
            "purpose": "activate the existing TVC runtime path for the already-staged frozen corpus requests",
            "provider_operation_route": "https://tvc.stegverse.org/v1/provider-operation",
            "network_source_fetch_allowed": False,
            "second_user_operated_device_required": False,
        }),
        task_id=TASK_ID,
        cosv_task_vector=COSV,
        output=None,
    )
    manifest = module.build_manifest(args)
    assert manifest["task_id"] == TASK_ID
    assert manifest["cosv_task_vector"] == COSV
    assert manifest["reusable_task_id"] == RT_ID
    assert manifest["automation_plan"]["single_trigger"] is True
    assert manifest["automation_plan"]["manual_coordination_between_machine_admissible_internal_steps_required"] is False
    assert manifest["automation_plan"]["declared_runner_refs"] == ["scripts/run_tvc_runtime_boundary_reusable.py"]
    assert manifest["authority"]["credential_authority"] == "TV/TVC"
    assert manifest["authority"]["github_token_runtime_authority"] == "NONE"


def test_child_pointer_vector_mismatch_fails_closed() -> None:
    module = load_module()
    effective = module.load_effective_cosv_index()
    with pytest.raises(SystemExit, match="task_id/COSV vector binding mismatch"):
        module.verify_task_pointer(TASK_ID, "00000000000000", effective)
