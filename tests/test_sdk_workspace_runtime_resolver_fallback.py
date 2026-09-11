from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "resolve_task_runtime_candidates",
    SCRIPTS / "resolve_task_runtime_candidates.py",
)
assert spec and spec.loader
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)

TASK_ID = "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004"
RECORDS = ROOT / "data" / "canonical-task-records"


def test_resolver_falls_back_to_dedicated_canonical_record() -> None:
    task = resolver.find_task({"tasks": []}, TASK_ID, RECORDS)
    assert task["task_id"] == TASK_ID
    assert task["runtime_requirements"]["capabilities"] == ["resident_request_dispatch"]
    assert task["runtime_requirements"]["mutation_required"] is False
    assert task["runtime_requirements"]["current_observation_required"] is True


def test_duplicate_aggregate_identity_fails_closed(tmp_path: Path) -> None:
    duplicate = {"task_id": TASK_ID, "runtime_requirements": {}}
    registry = {"tasks": [duplicate, dict(duplicate)]}
    try:
        resolver.find_task(registry, TASK_ID, tmp_path)
    except RuntimeError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate aggregate identities must fail closed")


def test_standalone_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    (tmp_path / f"{TASK_ID}.json").write_text(
        json.dumps({"task_id": "WRONG-ID", "runtime_requirements": {}}),
        encoding="utf-8",
    )
    try:
        resolver.find_task({"tasks": []}, TASK_ID, tmp_path)
    except RuntimeError as exc:
        assert "identity mismatch" in str(exc)
    else:
        raise AssertionError("mismatched standalone identity must fail closed")
