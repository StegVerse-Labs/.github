from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "resolve_gadi_resident_runtime_sources.py"
spec = importlib.util.spec_from_file_location("gadi_source_resolver", PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def test_existing_staged_sources_are_preserved_without_locator_manifest(tmp_path):
    for name, rel in module.TARGETS.items():
        write_json(tmp_path / rel, {"name": name})
    result = module.resolve(tmp_path)
    assert result["state"] == "SOURCE_RESOLUTION_COMPLETE"
    assert result["locator_manifest_observed"] is False
    assert result["resolved_count"] == 4
    assert result["network_fetch_performed"] is False


def test_locator_manifest_copies_exact_local_bytes(tmp_path):
    sources = {
        "stegos_command": "native/stegos-command.json",
        "intr_admission": "native/intr-admission.json",
        "worker_claim": "native/worker-claim.json",
        "actuator_observation": "native/actuator-observation.json",
    }
    for name, rel in sources.items():
        write_json(tmp_path / rel, {"source": name, "value": 1})
    write_json(
        tmp_path / module.LOCATOR_REL,
        {
            "schema": "stegverse.gadi-resident-runtime-source-locators/v1",
            "task_id": module.TASK_ID,
            "parent_task_id": module.PARENT_TASK_ID,
            "network_fetch_allowed": False,
            "sources": sources,
        },
    )
    result = module.resolve(tmp_path)
    assert result["state"] == "SOURCE_RESOLUTION_COMPLETE"
    assert result["resolved_count"] == 4
    for name, target_rel in module.TARGETS.items():
        source_bytes = (tmp_path / sources[name]).read_bytes()
        assert (tmp_path / target_rel).read_bytes() == source_bytes
        assert result["resolved"][name]["sha256"] == module.digest(tmp_path / target_rel)


def test_unsafe_locator_fails_closed(tmp_path):
    write_json(
        tmp_path / module.LOCATOR_REL,
        {
            "schema": "stegverse.gadi-resident-runtime-source-locators/v1",
            "task_id": module.TASK_ID,
            "parent_task_id": module.PARENT_TASK_ID,
            "network_fetch_allowed": False,
            "sources": {
                "stegos_command": "../outside.json",
                "intr_admission": "native/intr.json",
                "worker_claim": "native/claim.json",
                "actuator_observation": "native/actuator.json",
            },
        },
    )
    result = module.resolve(tmp_path)
    assert result["state"] == "SOURCE_RESOLUTION_BLOCKED_FAIL_CLOSED"
    assert "STEGOS_COMMAND_LOCATOR_MISSING_OR_UNSAFE" in result["blockers"]
    assert result["network_fetch_performed"] is False


def test_network_fetch_permission_is_rejected(tmp_path):
    write_json(
        tmp_path / module.LOCATOR_REL,
        {
            "schema": "stegverse.gadi-resident-runtime-source-locators/v1",
            "task_id": module.TASK_ID,
            "parent_task_id": module.PARENT_TASK_ID,
            "network_fetch_allowed": True,
            "sources": {},
        },
    )
    result = module.resolve(tmp_path)
    assert result["state"] == "SOURCE_RESOLUTION_BLOCKED_FAIL_CLOSED"
    assert "NETWORK_SOURCE_FETCH_FORBIDDEN" in result["blockers"]
