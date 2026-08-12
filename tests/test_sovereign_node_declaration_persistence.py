from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "sovereign_runtime_activation_worker.py"


class SovereignNodeDeclarationPersistenceTests(unittest.TestCase):
    def test_explicit_authorized_declaration_is_persisted_without_secret_authority(self) -> None:
        invocation = {
            "schema": "stegverse.worker-invocation/v0.1",
            "heartbeat_epoch": 30,
            "task": {
                "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                "claim_id": "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18",
                "worker_id": "sovereign-runtime-activation-worker",
                "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                "heartbeat_timing": {"fencing_token": 18},
            },
            "handoff": {
                "execution": {
                    "required_capabilities": [
                        "runtime_observation",
                        "continuous_process_execution",
                        "durable_state_reconstruction",
                        "bounded_repository_mutation",
                    ],
                    "allowed_paths": ["receipts/sovereign-runtime-activation/**"],
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(home),
                "XDG_STATE_HOME": str(root / "state"),
                "STEGVERSE_SOVEREIGN_NODE": "1",
            }
            completed = subprocess.run(
                [sys.executable, str(WORKER)],
                cwd=tmp,
                input=json.dumps(invocation) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            marker = home / ".stegverse" / "node.json"
            self.assertTrue(marker.is_file())
            declaration = json.loads(marker.read_text(encoding="utf-8"))
            self.assertTrue(declaration["declared"])
            self.assertEqual(declaration["credential_authority"], "TV/TVC")
            self.assertFalse(declaration["github_token_required"])
            self.assertFalse(declaration["third_party_runtime_required"])
            self.assertEqual(
                declaration["authority_effect"],
                "PERSIST_EXISTING_NODE_DECLARATION_ONLY",
            )

    def test_no_declaration_is_never_manufactured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            env = {"PATH": os.environ.get("PATH", ""), "HOME": str(home)}
            script = (
                "import importlib.util, pathlib; "
                f"p=pathlib.Path({str(WORKER)!r}); "
                "s=importlib.util.spec_from_file_location('g18', p); "
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                "assert m.persist_authorized_node_declaration() is None"
            )
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=tmp,
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse((home / ".stegverse" / "node.json").exists())


if __name__ == "__main__":
    unittest.main()
