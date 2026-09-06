from __future__ import annotations

import unittest

from scripts import dispatch_resident_execution_requests as dispatcher
from scripts import refresh_and_dispatch_resident_requests as bridge


class SV002AwarenessTargetedBridgeTests(unittest.TestCase):
    def test_existing_awareness_consumers_are_targetable_without_new_dispatcher(self):
        expected = {
            "astra_class_resilience_awareness": "scripts/consume_astra_class_resilience_awareness_request.py",
            "quantum_resilience_awareness": "scripts/consume_quantum_resilience_awareness_request.py",
        }
        registered = dict(dispatcher.CONSUMERS)
        for selector, consumer in expected.items():
            self.assertIn(selector, bridge.ALLOWED_TARGET_CONSUMERS)
            self.assertEqual(registered.get(selector), consumer)

    def test_awareness_selectors_preserve_exact_one_selector_bridge_contract(self):
        self.assertEqual(len(set(bridge.ALLOWED_TARGET_CONSUMERS)), len(bridge.ALLOWED_TARGET_CONSUMERS))
        self.assertEqual(bridge.DISPATCHER_REL.as_posix(), "scripts/dispatch_resident_execution_requests.py")
        self.assertNotEqual(bridge.TARGET_CONSUMER, "astra_class_resilience_awareness")
        self.assertNotEqual(bridge.TARGET_CONSUMER, "quantum_resilience_awareness")


if __name__ == "__main__":
    unittest.main()
