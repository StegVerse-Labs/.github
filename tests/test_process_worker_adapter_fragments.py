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
