from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = ROOT / "scripts/dispatch_resident_execution_requests.py"
SPEC = importlib.util.spec_from_file_location("resident_dispatcher", DISPATCHER_PATH)
assert SPEC and SPEC.loader
DISPATCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISPATCHER)


class AstraClassResilienceDispatchBindingTests(unittest.TestCase):
    def test_awareness_consumer_is_registered_before_protected_entities(self) -> None:
        by_name = dict(DISPATCHER.CONSUMERS)
        self.assertEqual(
            by_name["astra_class_resilience_awareness"],
            "scripts/consume_astra_class_resilience_awareness_request.py",
        )
        order = [name for name, _ in DISPATCHER.CONSUMERS]
        awareness_index = order.index("astra_class_resilience_awareness")
        for protected in DISPATCHER.AWARENESS_PROTECTED:
            self.assertLess(awareness_index, order.index(protected))

    def test_protected_entity_dispatch_fails_closed_without_awareness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            self.assertFalse(DISPATCHER.standing_awareness_ready(runtime))
            selected = DISPATCHER.select_consumers(("stegverse001_bounded_autonomy",))
            self.assertEqual(selected[0][0], "stegverse001_bounded_autonomy")

    def test_all_three_requests_preserve_non_authority(self) -> None:
        specs = {
            "astra-class-resilience-sv001-awareness-001.json": "StegVerse-001",
            "astra-class-resilience-sv002-awareness-001.json": "StegVerse-002",
            "astra-class-resilience-sv011-awareness-001.json": "SV-011",
        }
        for filename, entity_id in specs.items():
            req = json.loads((ROOT / "control/resident-execution-request.d" / filename).read_text())
            self.assertEqual(req["entity_id"], entity_id)
            self.assertEqual(req["state"], "REQUESTED")
            self.assertTrue(req["standing_directive"])
            self.assertEqual(req["credential_authority"], "TV/TVC")
            self.assertEqual(req["github_token_runtime_authority"], "NONE")
            self.assertFalse(req["heartbeat_grants_execution_authority"])
            self.assertFalse(req["request_granted_authority"])
            self.assertFalse(req["second_machine_required"])


if __name__ == "__main__":
    unittest.main()
