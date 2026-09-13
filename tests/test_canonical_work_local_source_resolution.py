from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py"
SPEC = importlib.util.spec_from_file_location("canonical_work_consumer", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def materialize_minimum_source(root: Path) -> None:
    (root / "data/canonical-task-records").mkdir(parents=True, exist_ok=True)
    registry = root / "data/canonical-task-registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text("{}\n", encoding="utf-8")
    for rel in MOD.MATERIALIZE:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source\n", encoding="utf-8")


def test_complete_supplied_source_is_preferred() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        source = base / "source"
        runtime = base / "runtime"
        runtime.mkdir()
        materialize_minimum_source(source)
        resolved = MOD.resolve_local_canonical_source(source, runtime, {})
        assert resolved == source.resolve()


def test_runtime_source_falls_back_to_existing_local_canonical_locator() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        source = base / "source"
        runtime = base / "runtime"
        runtime.mkdir()
        materialize_minimum_source(source)
        resolved = MOD.resolve_local_canonical_source(
            runtime,
            runtime,
            {"STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source)},
        )
        assert resolved == source.resolve()


def test_incomplete_runtime_without_local_locator_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "runtime"
        runtime.mkdir()
        try:
            MOD.resolve_local_canonical_source(runtime, runtime, {})
        except RuntimeError as exc:
            assert "STEGVERSE_HEARTBEAT_SOURCE_ROOT" in str(exc)
        else:
            raise AssertionError("expected fail-closed local source resolution")
