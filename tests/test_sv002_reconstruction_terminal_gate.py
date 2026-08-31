from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workers import sv002_self_characterization_worker as worker


class SV002ReconstructionTerminalGateTests(unittest.TestCase):
    def build_completed_state(self, root: Path) -> dict:
        root.mkdir(parents=True, exist_ok=True)
        execution = {
            "schema": "stegverse.self-characterization-execution-receipt/v0.2",
            "state": "COMPLETED",
            "principal_run_started": True,
            "principal_run_completed": True,
            "model_id": "resident-principal",
            "authority_transfer_assumed": False,
            "authority_effect_resolution": "DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS",
            "transition_effect_state": "PENDING_TRANSITION_ELEMENT_EVALUATION",
        }
        for name in worker.PRINCIPAL_REQUIRED_ARTIFACTS:
            path = root / name
            if name == "EXPERIMENT_EXECUTION_RECEIPT.json":
                path.write_text(json.dumps(execution), encoding="utf-8")
            elif name.endswith(".json"):
                path.write_text("{}\n", encoding="utf-8")
            else:
                path.write_text("self characterization\n", encoding="utf-8")
        return execution

    def test_completed_principal_state_is_reusable_without_live_process(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "state"
            expected = self.build_completed_state(root)
            observed = worker.load_completed_principal_state(root)
            self.assertEqual(observed, expected)

    def test_missing_transition_effects_prevents_completed_state_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "state"
            self.build_completed_state(root)
            (root / "TRANSITION_EFFECTS.json").unlink()
            self.assertIsNone(worker.load_completed_principal_state(root))

    def test_reconstruction_is_terminal_only_on_exact_pass_receipt(self):
        self.assertTrue(worker.reconstruction_terminal({
            "state": "PASS",
            "receipt": {"status": "PASS", "reconstruction": "PASS"},
        }))
        for value in (
            {"state": "PENDING"},
            {"state": "FAIL", "receipt": {"status": "FAIL", "reconstruction": "FAIL"}},
            {"state": "PASS", "receipt": {"status": "PASS", "reconstruction": "FAIL"}},
            {"state": "PASS", "receipt": None},
        ):
            self.assertFalse(worker.reconstruction_terminal(value))

    def test_worker_checks_existing_principal_before_fresh_runtime_discovery(self):
        source = Path(worker.__file__).read_text(encoding="utf-8")
        reuse = source.index("existing_result = load_completed_principal_state(state_root)")
        discovery = source.index("micro, micro_seen = find_repo(")
        self.assertLess(reuse, discovery)
        self.assertIn("principal_execution_repeated\": False", source)


if __name__ == "__main__":
    unittest.main()
