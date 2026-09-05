from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/consume_quantum_resilience_awareness_request.py"
SPEC = importlib.util.spec_from_file_location("quantum_awareness", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _runtime(tmp_path: Path) -> Path:
    runtime = tmp_path / "runtime"
    for rel in [MODULE.CONTRACT_REL, MODULE.CENSUS_REL]:
        target = runtime / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    for spec in MODULE.ENTITY_SPECS.values():
        rel = MODULE.REQUEST_DIR / spec["request"]
        target = runtime / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    return runtime


def test_materializes_three_entity_states_and_receipts(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    result = MODULE.consume(ROOT, runtime)
    assert result["state"] == "COMPLETED"
    assert result["entity_count"] == 3
    assert result["runtime_awareness_materialized"] is True
    assert result["standing_directive_active"] is True
    assert result["pqc_deployment_claim"] is False
    for spec in MODULE.ENTITY_SPECS.values():
        state = json.loads((runtime / MODULE.STATE_DIR / f"{spec['slug']}.json").read_text())
        receipt = json.loads((runtime / MODULE.RECEIPT_DIR / f"{spec['slug']}.latest.json").read_text())
        assert state["state"] == "ACTIVE"
        assert state["quantum_capability_confers_authority"] is False
        assert state["pqc_validity_confers_transition_authority"] is False
        assert receipt["runtime_awareness_materialized"] is True
        assert receipt["authority_effect"] == "NONE_AWARENESS_MATERIALIZATION_ONLY"
    second = MODULE.consume(ROOT, runtime)
    assert all(row["state"] == "ALREADY_CONSUMED" for row in second["entities"])


def test_contract_authority_flip_fails_closed(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    path = runtime / MODULE.CONTRACT_REL
    contract = json.loads(path.read_text())
    contract["authority"]["quantum_capability_confers_authority"] = True
    path.write_text(json.dumps(contract))
    with pytest.raises(RuntimeError, match="authority invariant"):
        MODULE.consume(ROOT, runtime)
