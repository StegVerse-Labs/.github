from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-STEGNUTRITION-CONTINUATION-001"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def invocation() -> dict:
    handoff = load("handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json")
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 30,
        "task": {
            "task_id": TASK_ID,
            "claim_id": "CLAIM-STEGNUTRITION-TEST-G30",
            "worker_id": "stegnutrition-machine-continuation-worker",
            "worker_instance_id": "stegnutrition-machine-continuation-worker-HB30-G30",
            "heartbeat_timing": {"fencing_token": 30},
        },
        "handoff": handoff,
    }


def _worker_module():
    path = ROOT / "workers/stegnutrition_continuation_worker.py"
    spec = importlib.util.spec_from_file_location("stegnutrition_continuation_worker", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registry_fragment_has_unique_capability_and_no_token_requirement() -> None:
    fragment = load("control/worker-registry.d/stegnutrition-continuation-001.json")
    assert fragment["github_token_required"] is False
    task = fragment["tasks"][0]
    worker = fragment["workers"][0]
    assert task["task_id"] == TASK_ID
    assert task["state"] == "HANDOFF_READY"
    assert worker["adapter_ref"] == "process:stegnutrition-machine-continuation-v1"
    assert "stegnutrition_machine_continuation" in worker["capabilities"]


def test_process_adapter_allows_only_local_root_environment() -> None:
    adapters = load("control/process-worker-adapters.json")["adapters"]
    row = next(item for item in adapters if item["adapter_ref"] == "process:stegnutrition-machine-continuation-v1")
    assert row["command"] == ["python", "workers/stegnutrition_continuation_entrypoint.py"]
    assert row["env_allowlist"] == ["STEGVERSE_STEGNUTRITION_ROOT"]
    notes = " ".join(row["notes"]).lower()
    assert "no github token" in notes
    assert "remote source checkout" in notes
    assert "validates" in notes


def test_capability_profile_does_not_grant_general_code_or_github_authority() -> None:
    profiles = load("control/worker-capability-profiles.json")["profiles"]
    row = next(item for item in profiles if item["profile_id"] == "sovereign-runtime-worker-v1")
    assert "stegnutrition_machine_continuation" in row["allowed_capabilities"]
    assert "github_repository_write" not in row["allowed_capabilities"]
    assert "code_and_schema_implementation" not in row["allowed_capabilities"]


def test_worker_normalizes_canonical_v4_inventory() -> None:
    worker = _worker_module()
    inventory = {
        "schema": "stegnutrition.session-execution-inventory.v4",
        "completed_or_released": ["STEGNUTRITION-PORTION-GEOMETRY-004"],
        "implemented_pending_activation_or_real_evidence": [
            {"task_id": "STEGNUTRITION-SEMANTIC-VISION-012", "state": "REAL_DATA_BLOCKED"},
            {"task_id": "STEGNUTRITION-AUTO-PORTION-013", "state": "PARTIAL"},
            {"task_id": "STEGNUTRITION-REAL-BENCHMARK-DATA-014", "state": "HUMAN_BOUNDARY"},
            {"task_id": "STEGNUTRITION-PRODUCTION-PIPELINE-019", "state": "SOURCE_IMPLEMENTED"},
        ],
        "machine_owned_or_blocked": [
            {"task_id": "STEGNUTRITION-LIVE-VISUAL-ROUTE-015", "state": "BLOCKED"},
            {"task_id": "STEGNUTRITION-FULL-VALIDATION-016", "state": "BLOCKED"},
            {"task_id": "STEGNUTRITION-RELEASE-PROPAGATION-017", "state": "NOT_APPLICABLE"},
            {"task_id": "STEGNUTRITION-MACHINE-CONTINUATION-018", "state": "SOURCE_INSTALLED"},
        ],
    }
    rows = worker._inventory_rows(inventory)
    assert rows["STEGNUTRITION-PORTION-GEOMETRY-004"]["state"] == "COMPLETE_RELEASED"
    for task_id in (
        "STEGNUTRITION-SEMANTIC-VISION-012",
        "STEGNUTRITION-AUTO-PORTION-013",
        "STEGNUTRITION-REAL-BENCHMARK-DATA-014",
        "STEGNUTRITION-LIVE-VISUAL-ROUTE-015",
        "STEGNUTRITION-FULL-VALIDATION-016",
        "STEGNUTRITION-RELEASE-PROPAGATION-017",
        "STEGNUTRITION-MACHINE-CONTINUATION-018",
        "STEGNUTRITION-PRODUCTION-PIPELINE-019",
    ):
        assert task_id in rows


def test_filesystem_projection_tracks_current_stegnutrition_source_names(tmp_path: Path) -> None:
    worker = _worker_module()
    required = [
        "src/stegnutrition/semantic_food.py",
        "src/stegnutrition/semantic_eval.py",
        "scripts/train_semantic_food_local.py",
        "tests/test_semantic_food.py",
        "tests/test_semantic_eval.py",
        "src/stegnutrition/vision/scale.py",
        "src/stegnutrition/vision/auto_portion.py",
        "tests/test_auto_scale.py",
        "tests/test_auto_portion.py",
        "src/stegnutrition/pipeline.py",
        "tests/test_pipeline.py",
        "tasks/STEGNUTRITION-PRODUCTION-PIPELINE-019.json",
        "src/stegnutrition/benchmark_ingest.py",
        "scripts/ingest_weighed_photo_case.py",
        "tests/test_benchmark_ingest.py",
    ]
    for relative in required:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    projection = worker._filesystem_projection(tmp_path)
    assert projection["semantic_model_source_present"] is True
    assert projection["semantic_model_qualified_artifact_present"] is False
    assert projection["automatic_portion_surfaces_present"] is True
    assert projection["production_pipeline_surfaces_present"] is True
    assert projection["benchmark_ingestion_surfaces_present"] is True
    assert projection["real_weighed_benchmark_case_count"] == 0


def test_worker_fails_closed_without_local_stegnutrition_materialization(tmp_path: Path) -> None:
    receipt = ROOT / "receipts/stegnutrition-continuation" / f"{TASK_ID}.json"
    if receipt.exists():
        receipt.unlink()
    env = os.environ.copy()
    env.pop("STEGVERSE_STEGNUTRITION_ROOT", None)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    proc = subprocess.run(
        [sys.executable, "workers/stegnutrition_continuation_entrypoint.py"],
        cwd=ROOT,
        input=json.dumps(invocation()),
        text=True,
        capture_output=True,
        env=env,
        timeout=20,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["state"] == "BLOCKED"
    assert response["transition_id"] == "STEGNUTRITION_LOCAL_MATERIALIZATION_REQUIRED"
    assert response["blocker"]["solution_required"] is True
    assert "GitHub token" in response["blocker"]["workaround_candidates"][0]
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert stored["github_token_required"] is False
    assert stored["github_repository_fetch_performed"] is False
    receipt.unlink()
