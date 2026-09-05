from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/consume_astra_class_resilience_awareness_request.py"
SPEC = importlib.util.spec_from_file_location("astra_runtime_awareness_consumer", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AstraClassResilienceRuntimeAwarenessTests(unittest.TestCase):
    def materialize_inputs(self, runtime: Path) -> None:
        files = [
            "control/astra-class-adversarial-resilience-contract.json",
            "control/resident-execution-request.d/astra-class-resilience-sv001-awareness-001.json",
            "control/resident-execution-request.d/astra-class-resilience-sv002-awareness-001.json",
            "control/resident-execution-request.d/astra-class-resilience-sv011-awareness-001.json",
        ]
        for rel in files:
            src = ROOT / rel
            dst = runtime / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def test_materializes_all_three_standing_directives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            self.materialize_inputs(runtime)
            result = MODULE.consume(ROOT, runtime)
            self.assertEqual(result["state"], "COMPLETED")
            self.assertTrue(result["runtime_awareness_materialized"])
            self.assertTrue(result["standing_directive_active"])
            self.assertEqual(result["entity_count"], 3)
            for slug in ("stegverse-001", "stegverse-002", "sv-011"):
                state = json.loads((runtime / "runtime-state/entity-awareness" / f"{slug}.json").read_text())
                self.assertEqual(state["state"], "ACTIVE")
                self.assertTrue(state["standing_directive_active"])
                self.assertFalse(state["capability_confers_authority"])
                self.assertEqual(state["credential_authority"], "TV/TVC")
                self.assertEqual(state["worker_runtime"], "WorkerCoordinator")
                receipt = json.loads((runtime / "receipts/sovereign-host/astra-class-resilience" / f"{slug}.latest.json").read_text())
                self.assertEqual(receipt["state"], "COMPLETED")
                self.assertTrue(receipt["runtime_awareness_materialized"])
                self.assertEqual(receipt["authority_effect"], "NONE_AWARENESS_MATERIALIZATION_ONLY")

            second = MODULE.consume(ROOT, runtime)
            self.assertEqual(second["state"], "COMPLETED")
            self.assertTrue(all(row["state"] == "ALREADY_CONSUMED" for row in second["entities"]))

    def test_fails_closed_if_capability_is_given_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            self.materialize_inputs(runtime)
            contract_path = runtime / "control/astra-class-adversarial-resilience-contract.json"
            contract = json.loads(contract_path.read_text())
            contract["authority_invariants"]["capability_confers_authority"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "authority invariant mismatch"):
                MODULE.consume(ROOT, runtime)


if __name__ == "__main__":
    unittest.main()
