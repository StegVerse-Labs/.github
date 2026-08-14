from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.run_heartbeat_runtime import _adapter_entries, load_adapters


class ProcessWorkerAdapterFragmentTests(unittest.TestCase):
    def test_fragment_is_loaded_after_base_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            control = root / "control"
            fragments = control / "process-worker-adapters.d"
            fragments.mkdir(parents=True)
            (control / "process-worker-adapters.json").write_text(json.dumps({
                "schema": "stegverse.process-worker-adapters/v0.1",
                "adapters": [{
                    "adapter_ref": "process:base-v1",
                    "command": ["python", "base.py"],
                    "cwd": ".",
                    "enabled": True,
                    "env_allowlist": [],
                    "timeout_seconds": 1,
                }],
            }), encoding="utf-8")
            (fragments / "z-fragment.json").write_text(json.dumps({
                "schema": "stegverse.process-worker-adapter-fragment/v0.1",
                "fragment_id": "Z",
                "adapters": [{
                    "adapter_ref": "process:fragment-v1",
                    "command": ["python", "fragment.py"],
                    "cwd": ".",
                    "enabled": True,
                    "env_allowlist": [],
                    "timeout_seconds": 1,
                }],
            }), encoding="utf-8")
            refs = [entry["adapter_ref"] for entry in _adapter_entries(root)]
            self.assertEqual(refs, ["process:base-v1", "process:fragment-v1"])
            self.assertEqual(set(load_adapters(root)), {"process:base-v1", "process:fragment-v1"})

    def test_bound_state_fragment_loads_without_exposing_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fragments = root / "control" / "process-worker-adapters.d"
            fragments.mkdir(parents=True)
            state_root = root / "state"
            entry = {
                "adapter_ref": "process:bound-v1",
                "command": ["python", "worker.py"],
                "cwd": ".",
                "enabled": True,
                "env_allowlist": [],
                "timeout_seconds": 1,
                "type": "process_json_bound_state_v0.1",
                "bound_state_root": str(state_root),
                "bound_state_allowed_paths": ["outbox/**", "inbox/**"],
            }
            (fragments / "bound.json").write_text(json.dumps({
                "schema": "stegverse.process-worker-adapter-fragment/v0.1",
                "fragment_id": "BOUND",
                "adapters": [entry],
            }), encoding="utf-8")
            adapter = load_adapters(root)["process:bound-v1"]
            description = adapter.describe()
            self.assertEqual(description["adapter_type"], "process_json_bound_state_v0.1")
            self.assertEqual(description["bound_state_allowed_paths"], ["outbox/**", "inbox/**"])
            self.assertFalse(description["bound_state_authoritative_path_exposed_to_worker"])
            self.assertEqual(description["env_allowlist"], [])

    def test_relative_bound_state_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fragments = root / "control" / "process-worker-adapters.d"
            fragments.mkdir(parents=True)
            (fragments / "bound.json").write_text(json.dumps({
                "schema": "stegverse.process-worker-adapter-fragment/v0.1",
                "fragment_id": "BOUND",
                "adapters": [{
                    "adapter_ref": "process:bound-v1",
                    "command": ["python", "worker.py"],
                    "cwd": ".",
                    "enabled": True,
                    "env_allowlist": [],
                    "timeout_seconds": 1,
                    "type": "process_json_bound_state_v0.1",
                    "bound_state_root": "relative/spool",
                    "bound_state_allowed_paths": ["outbox/**"],
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "bound_state_root must resolve to an absolute host path"):
                load_adapters(root)

    def test_duplicate_enabled_adapter_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            control = root / "control"
            fragments = control / "process-worker-adapters.d"
            fragments.mkdir(parents=True)
            entry = {
                "adapter_ref": "process:duplicate-v1",
                "command": ["python", "worker.py"],
                "cwd": ".",
                "enabled": True,
                "env_allowlist": [],
                "timeout_seconds": 1,
            }
            (control / "process-worker-adapters.json").write_text(json.dumps({
                "schema": "stegverse.process-worker-adapters/v0.1", "adapters": [entry]
            }), encoding="utf-8")
            (fragments / "duplicate.json").write_text(json.dumps({
                "schema": "stegverse.process-worker-adapter-fragment/v0.1",
                "fragment_id": "DUP",
                "adapters": [entry],
            }), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "duplicate enabled adapter_ref"):
                load_adapters(root)

    def test_wrong_fragment_schema_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fragments = root / "control" / "process-worker-adapters.d"
            fragments.mkdir(parents=True)
            (fragments / "bad.json").write_text(json.dumps({"schema": "wrong", "adapters": []}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "unsupported process worker adapter fragment"):
                _adapter_entries(root)


if __name__ == "__main__":
    unittest.main()
