"""The organization runtime surface is a committed transition cycle (B-P40).

`runtime_boundary.py validate` passes only when `org-runtime/activation.json`
declares `runtime_execution_surface: COMMITTED_TRANSITION_CYCLE`. The prior
activation, which declared `SOVEREIGN_RESIDENT_PROCESS` and listed "resident
process identity" as required evidence, is refused: `runtime_transition_bound`
is False and the boundary is not valid, so this validator paired with the prior
activation fails closed rather than accepting either surface.

The activation is redirected to a temporary file; the repository copy is read,
never written.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION = ROOT / "org-runtime/activation.json"


def _module():
    spec = importlib.util.spec_from_file_location("runtime_boundary_transition_bound",
                                                  ROOT / "org-runtime/runtime_boundary.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prior_activation(current: dict) -> dict:
    """The activation as it stood before B-P40: only these two values differ."""
    prior = json.loads(json.dumps(current))
    prior["runtime_execution_surface"] = "SOVEREIGN_RESIDENT_PROCESS"
    prior["required_runtime_evidence"] = ["resident process identity" if item == "committed request digest in the cycle record"
                                          else item for item in prior["required_runtime_evidence"]]
    return prior


class RuntimeTransitionBoundTests(unittest.TestCase):
    def setUp(self):
        self.runtime_boundary = _module()
        self.current = json.loads(ACTIVATION.read_text(encoding="utf-8"))

    def validate_with(self, activation: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "activation.json"
            path.write_text(json.dumps(activation), encoding="utf-8")
            self.runtime_boundary.ACT = path
            try:
                return self.runtime_boundary.validate()
            finally:
                self.runtime_boundary.ACT = ACTIVATION

    def test_repository_activation_is_a_committed_transition_cycle(self):
        self.assertEqual(self.current["runtime_execution_surface"], "COMMITTED_TRANSITION_CYCLE")
        self.assertIn("committed request digest in the cycle record", self.current["required_runtime_evidence"])
        self.assertNotIn("resident process identity", self.current["required_runtime_evidence"])
        result = self.runtime_boundary.validate()
        self.assertNotIn("runtime_sovereign", result["checks"])
        self.assertIs(result["checks"]["runtime_transition_bound"], True)
        self.assertIs(result["valid"], True)
        self.assertEqual(result["authority_effect"], "NONE_VALIDATION_ONLY")

    def test_prior_sovereign_resident_activation_fails_closed(self):
        prior = prior_activation(self.current)
        self.assertEqual(prior["runtime_execution_surface"], "SOVEREIGN_RESIDENT_PROCESS")
        self.assertIn("resident process identity", prior["required_runtime_evidence"])
        result = self.validate_with(prior)
        self.assertIs(result["checks"]["runtime_transition_bound"], False)
        self.assertIs(result["valid"], False)
        self.assertEqual(result["authority_effect"], "NONE_VALIDATION_ONLY")

    def test_absent_surface_fails_closed(self):
        absent = {key: value for key, value in self.current.items() if key != "runtime_execution_surface"}
        result = self.validate_with(absent)
        self.assertIs(result["checks"]["runtime_transition_bound"], False)
        self.assertIs(result["valid"], False)


if __name__ == "__main__":
    unittest.main()
