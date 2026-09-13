import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "data" / "canonical-task-records" / "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json"
BINDING = ROOT / "control" / "source-bindings" / "stegbrowser-tvc-runtime-observer.json"
HANDOFF = ROOT / "docs" / "STEGBROWSER_EPHEMERAL_RUNTIME_BINDING_MIRROR_HANDOFF.md"

PRIMARY = "aef6b6f5dc99d2a531718ca475d20858ae8e68a6"
OBSERVER = "4c78f8653b8a5899350479d57c58e936b50e023a"


def test_observer_is_separately_immutable_bound_from_primary_runtime():
    task = json.loads(TASK.read_text(encoding="utf-8"))
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    projection = task["component_model_projection"]

    assert binding["task_id"] == task["task_id"]
    assert binding["cosv_task_vector"] == task["cosv_task_vector"]
    assert binding["component_id"] == "RTC-MANIFEST-001"
    assert binding["component_role"] == "RUNTIME_OBSERVATION_EVIDENCE_ONLY"
    assert binding["reference_mode"] == "IMMUTABLE_COMMIT"
    assert binding["primary_runtime_source_pin_preserved"] == PRIMARY
    assert binding["exact_sha"] == OBSERVER
    assert binding["observer_source_revision_separate"] is True
    assert binding["authority_effect"] == "NONE_SOURCE_BINDING_ONLY"

    assert projection["primary_runtime_source_pin"] == PRIMARY
    assert projection["runtime_observer_exact_sha"] == OBSERVER
    assert projection["observer_source_revision_separate"] is True
    assert projection["source_alignment_status"] == "SEPARATE_IMMUTABLE_OBSERVER_BINDING_APPLIED"


def test_runtime_handoff_no_longer_marks_observer_alignment_pending():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "EXACT_TVC_SOURCE_PIN_OBSERVER_ALIGNMENT = SATISFIED_BY_SEPARATE_IMMUTABLE_REUSABLE_COMPONENT_BINDING" in text
    assert "EXACT_TVC_SOURCE_PIN_OBSERVER_ALIGNMENT_PENDING" not in text
    assert PRIMARY in text
    assert OBSERVER in text
