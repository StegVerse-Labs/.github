import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_constructor():
    path = ROOT / "scripts" / "materialize_reusable_task_construct.py"
    spec = importlib.util.spec_from_file_location("reusable_construct", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_canonical_work_cosv_pointer_resolves_for_existing_reusable_dispatch():
    mod = load_constructor()
    index = mod.load_effective_cosv_index()
    rows = [x for x in index["tasks"] if x.get("task_id") == "STEGVERSE-CANONICAL-WORK-COORDINATION-001"]
    assert len(rows) == 1
    assert rows[0]["vector"] == "10100000100000"
    assert rows[0]["vector_state"] == "EMITTED"
    assert rows[0]["authority_effect"] == "NONE"
    mod.verify_task_pointer(
        "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
        "10100000100000",
        index,
    )
