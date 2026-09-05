from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/dispatch_resident_execution_requests.py"
SPEC = importlib.util.spec_from_file_location("resident_dispatcher_quantum", MODULE_PATH)
assert SPEC and SPEC.loader
DISPATCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISPATCHER)


class QuantumResilienceDispatchBindingTests(unittest.TestCase):
    def test_quantum_awareness_registered_before_protected_consumers(self) -> None:
        by_name = dict(DISPATCHER.CONSUMERS)
        self.assertEqual(by_name["quantum_resilience_awareness"], "scripts/consume_quantum_resilience_awareness_request.py")
        order = [name for name, _ in DISPATCHER.CONSUMERS]
        q = order.index("quantum_resilience_awareness")
        for protected in DISPATCHER.QUANTUM_AWARENESS_PROTECTED:
            self.assertLess(q, order.index(protected))

    def test_quantum_awareness_missing_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(DISPATCHER.quantum_awareness_ready(Path(td)))


if __name__ == "__main__":
    unittest.main()
