from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_canonical_task_prohibits_connected_device_runtime_gate():
    record = load_json("data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json")
    policy = record["runtime_requirements"]["runtime_surface_policy"]
    assert policy["current_device_label_informational_only"] is True
    assert policy["device_confirmation_required"] is False
    assert policy["device_discovery_required"] is False
    assert policy["device_presence_probe_required"] is False
    assert policy["remote_connected_device_required"] is False
    assert policy["remote_desktop_commander_required"] is False
    assert policy["second_user_operated_device_required"] is False
    assert policy["absence_of_connected_device_is_blocker"] is False
    assert policy["device_identity_mints_authority"] is False


def test_executable_handoff_and_registry_preserve_same_invariant():
    handoff = load_json("handoffs/SV-KV-AI-PERSISTENCE-001.json")
    policy = handoff["execution"]["runtime_surface_policy"]
    assert all(policy[key] is False for key in (
        "device_confirmation_required",
        "device_discovery_required",
        "device_presence_probe_required",
        "remote_connected_device_required",
        "remote_desktop_commander_required",
        "second_user_operated_device_required",
        "absence_of_connected_device_is_blocker",
        "device_identity_mints_authority",
    ))
    assert policy["current_device_label_informational_only"] is True

    registry = load_json("control/worker-registry.d/kv-ai-memory-resident-001.json")
    admission = registry["tasks"][0]["admission"]
    for key in (
        "device_confirmation_required",
        "device_discovery_required",
        "device_presence_probe_required",
        "remote_connected_device_required",
        "remote_desktop_commander_required",
        "second_user_operated_device_required",
        "absence_of_connected_device_is_blocker",
    ):
        assert admission[key] is False


def test_resident_request_does_not_wait_for_device_presence():
    request = load_json("control/resident-execution-request.d/kv-ai-memory-resident-001.json")
    for key in (
        "second_machine_required",
        "device_confirmation_required",
        "device_discovery_required",
        "device_presence_probe_required",
        "remote_connected_device_required",
        "remote_desktop_commander_required",
        "absence_of_connected_device_is_blocker",
    ):
        assert request[key] is False


def test_handoff_and_readme_do_not_make_rdc_or_device_presence_a_gate():
    handoff = (ROOT / "docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "device discovery/presence/RDC gate: PROHIBITED" in handoff
    assert "Remote Desktop Commander requirement: NOT_APPLICABLE" in handoff
    assert "absence of connected-device result is blocker: false" in handoff

    # Repository-wide README already states current-device presence is not an authority
    # source and does not contain a KV-memory connected-device/RDC prerequisite.
    assert "Running on a user's iPhone does not by itself make a transition human-owned." in readme
    kv_section = readme.split("### Fenced Personal-KV AI memory resident execution", 1)[1].split("### Bounded StegSocials Universal InTr ingress", 1)[0]
    assert "Remote Desktop Commander" not in kv_section
    assert "connected device required" not in kv_section.lower()
    assert "second machine required" not in kv_section.lower()
