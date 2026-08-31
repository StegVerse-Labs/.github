from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "activate_resident_stack.py"
spec = importlib.util.spec_from_file_location("activate_resident_stack", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class ResidentStackActivationTests(unittest.TestCase):
    def test_hosted_surface_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "hosted execution surface rejected"):
            module.clean_env({"RENDER": "true"})

    def test_one_shot_sequence_packages_deploys_and_records_skap_successor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "control"
            llm = root / "llm"
            (source / "scripts").mkdir(parents=True)
            (llm / "scripts").mkdir(parents=True)
            (source / "scripts" / "package_sovereign_control_plane_bundle.py").write_text("# packager\n")
            (llm / "scripts" / "stegdeploy_bootstrap.py").write_text("# deploy\n")
            receipt_path = root / "activation.json"

            def runner(command, **kwargs):
                if "package_sovereign_control_plane_bundle.py" in str(command[1]):
                    output = Path(command[command.index("--output") + 1])
                    output.write_bytes(b"bundle")
                    return subprocess.CompletedProcess(
                        command, 0,
                        stdout=json.dumps({"bundle_sha256": "abc123"}) + "\n",
                        stderr="",
                    )
                if "stegdeploy_bootstrap.py" in str(command[1]):
                    deployment = {
                        "resident_control_plane_bootstrap": {
                            "attempted": True,
                            "state": "COMPLETE",
                            "result": {
                                "post_bootstrap_tvc_skap_successor": {
                                    "attempted": True,
                                    "state": "ACTIVE",
                                }
                            },
                        }
                    }
                    path = llm / ".stegdeploy" / "deployment-receipt.json"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(deployment) + "\n")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                raise AssertionError(command)

            receipt = module.activate(
                source,
                llm,
                health_url="http://127.0.0.1:8000/health",
                receipt_path=receipt_path,
                runner=runner,
                env={"PATH": "/usr/bin"},
            )
            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertTrue(receipt["g18_activation_complete"])
            self.assertTrue(receipt["tvc_skap_successor_attempted"])
            self.assertEqual(receipt["tvc_skap_successor_state"], "ACTIVE")
            self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
            self.assertFalse(receipt["orchestrator_grants_authority"])
            self.assertTrue(receipt_path.is_file())


if __name__ == "__main__":
    unittest.main()
