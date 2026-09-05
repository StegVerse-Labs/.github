from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

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


class QuantumResilienceRuntimeAwarenessTests(unittest.TestCase):
    def test_materializes_three_entity_states_and_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = _runtime(Path(td))
            result = MODULE.consume(ROOT, runtime)
            self.assertEqual(result["state"], "COMPLETED")
            self.assertEqual(result["entity_count"], 3)
            self.assertTrue(result["runtime_awareness_materialized"])
            self.assertTrue(result["standing_directive_active"])
            self.assertFalse(result["pqc_deployment_claim"])
            for spec in MODULE.ENTITY_SPECS.values():
                state = json.loads((runtime / MODULE.STATE_DIR / f"{spec['slug']}.json").read_text())
                receipt = json.loads((runtime / MODULE.RECEIPT_DIR / f"{spec['slug']}.latest.json").read_text())
                self.assertEqual(state["state"], "ACTIVE")
                self.assertFalse(state["quantum_capability_confers_authority"])
                self.assertFalse(state["pqc_validity_confers_transition_authority"])
                self.assertTrue(receipt["runtime_awareness_materialized"])
                self.assertEqual(receipt["authority_effect"], "NONE_AWARENESS_MATERIALIZATION_ONLY")
            second = MODULE.consume(ROOT, runtime)
            self.assertTrue(all(row["state"] == "ALREADY_CONSUMED" for row in second["entities"]))

    def test_contract_authority_flip_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = _runtime(Path(td))
            path = runtime / MODULE.CONTRACT_REL
            contract = json.loads(path.read_text())
            contract["authority"]["quantum_capability_confers_authority"] = True
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(RuntimeError, "authority invariant"):
                MODULE.consume(ROOT, runtime)


if __name__ == "__main__":
    unittest.main()
