from __future__ import annotations

import importlib.util
import inspect
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "refresh_heartbeat_transition_receipt.py"
spec = importlib.util.spec_from_file_location("transition_release", SCRIPT)
release = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(release)


class WorkerTaskCapableEventShapeTests(unittest.TestCase):
    def test_canonical_worker_event_epoch_is_task_capable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "events" / "worker-runtime.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "schema": "stegverse.heartbeat-runtime-event/v0.2",
                "epoch": 31,
                "event_type": "worker_registry_fragments_applied",
                "authority_effect": False,
            }) + "\n", encoding="utf-8")
            self.assertTrue(release.task_capable_worker_cycle_observed(root, {}, 31))

    def test_observer_shim_event_remains_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "events" / "worker-runtime.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "epoch": 31,
                "event_type": "worker_carrier_reference_observed",
                "task_adapters_invoked": 0,
                "authority_effect": False,
            }) + "\n", encoding="utf-8")
            self.assertFalse(release.task_capable_worker_cycle_observed(root, {}, 31))

    def test_legacy_carrier_epoch_field_remains_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "events" / "worker-runtime.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "carrier_epoch": 31,
                "event_type": "worker_response_observed",
                "authority_effect": False,
            }) + "\n", encoding="utf-8")
            self.assertTrue(release.task_capable_worker_cycle_observed(root, {}, 31))

    def test_task_capable_observer_is_downstream_only(self) -> None:
        source = inspect.getsource(release.task_capable_worker_cycle_observed)
        self.assertNotIn("sample_state", source)
        self.assertNotIn("derive_reference", source)
        self.assertNotIn("CarrierHeartbeatRuntime", source)
        self.assertNotIn("claim_id =", source)
        self.assertNotIn("fencing_token =", source)


if __name__ == "__main__":
    unittest.main()
