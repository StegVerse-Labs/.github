from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "workers" / "sovereign_node_repository_resolution_worker.py"
REQUIRED_RUNTIME_FILES = (
    Path("heartbeat_runtime/engine_v11.py"),
    Path("scripts/install_sovereign_heartbeat_service.py"),
    Path("scripts/verify_sovereign_runtime_activation.py"),
)


def invocation() -> dict:
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 31,
        "task": {
            "task_id": "ESCALATE-SHWP-DURABLE-RUNTIME-ACTIVATION-derived-test",
            "claim_id": "SHWP-ESCALATE-SHWP-DURABLE-RUNTIME-ACTIVATION-derived-test-G21",
            "worker_id": "sovereign-node-repository-resolution-worker-v1",
            "worker_instance_id": "sovereign-node-repository-resolution-worker-v1-HB31-G21",
            "heartbeat_timing": {"fencing_token": 21},
        },
        "handoff": {
            "execution": {
                "required_capabilities": ["repository_resolution", "sandbox_validation"],
                "allowed_paths": ["receipts/sovereign-runtime-activation/**"],
            }
        },
        "scope": {
            "required_capabilities": ["repository_resolution", "sandbox_validation"],
            "allowed_paths": ["receipts/sovereign-runtime-activation/**"],
        },
    }


class DerivedSovereignNodeDeclarationTests(unittest.TestCase):
    def make_runtime_source(self, target: Path) -> None:
        for relative in REQUIRED_RUNTIME_FILES:
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

    def test_nonhosted_canonical_local_runtime_derives_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "runtime-source"
            self.make_runtime_source(source_root)
            home = root / "home"
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(home),
                "XDG_STATE_HOME": str(root / "state"),
                "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source_root),
            }
            completed = subprocess.run(
                [sys.executable, str(RESOLVER)],
                cwd=root,
                input=json.dumps(invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "COMPLETED")
            self.assertEqual(response["transition_id"], "SOVEREIGN_NODE_DECLARATION_RESOLVED")
            marker = home / ".stegverse" / "node.json"
            self.assertTrue(marker.is_file())
            declaration = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(declaration["declaration_source"], "DERIVED_LOCAL_RUNTIME_ELIGIBILITY")
            self.assertTrue(declaration["canonical_runtime_complete"])
            self.assertTrue(declaration["durable_state_writable"])
            self.assertEqual(declaration["credential_authority"], "TV/TVC")
            self.assertFalse(declaration["github_token_required"])
            self.assertEqual(
                declaration["authority_effect"],
                "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
            )

    def test_hosted_environment_cannot_derive_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "runtime-source"
            self.make_runtime_source(source_root)
            home = root / "home"
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(home),
                "XDG_STATE_HOME": str(root / "state"),
                "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source_root),
                "GITHUB_ACTIONS": "true",
            }
            completed = subprocess.run(
                [sys.executable, str(RESOLVER)],
                cwd=root,
                input=json.dumps(invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "BLOCKED")
            self.assertFalse((home / ".stegverse" / "node.json").exists())

    def test_incomplete_local_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(home),
                "XDG_STATE_HOME": str(root / "state"),
                "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(root / "missing-source"),
            }
            completed = subprocess.run(
                [sys.executable, str(RESOLVER)],
                cwd=root,
                input=json.dumps(invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "BLOCKED")
            self.assertEqual(response["blocker"]["escalation_target"], "COMPONENT_AUTHORITY")
            self.assertFalse((home / ".stegverse" / "node.json").exists())


if __name__ == "__main__":
    unittest.main()
