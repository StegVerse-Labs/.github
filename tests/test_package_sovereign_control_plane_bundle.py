from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_sovereign_control_plane_bundle.py"
spec = importlib.util.spec_from_file_location("package_sovereign_control_plane_bundle", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class SovereignControlPlaneBundleTests(unittest.TestCase):
    def test_bundle_contains_bootstrap_and_non_authorizing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            (root / "scripts").mkdir(parents=True)
            (root / "control").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            (root / "scripts" / "run_worker_runtime.py").write_text("# worker\n", encoding="utf-8")
            (root / "control" / "worker-registry.json").write_text("{}\n", encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"

            receipt = module.build_bundle(root, output)

            self.assertTrue(output.is_file())
            self.assertFalse(receipt["network_fetch_required"])
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
            self.assertFalse(receipt["heartbeat_grants_execution_authority"])
            self.assertFalse(receipt["bundle_grants_authority"])
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("scripts/bootstrap_sovereign_runtime.py", names)
                self.assertIn(module.MANIFEST_NAME, names)
                manifest = json.loads(archive.read(module.MANIFEST_NAME))
            self.assertEqual(manifest["schema"], "stegverse.sovereign-control-plane-bundle/v1")
            self.assertFalse(manifest["bundle_grants_authority"])


if __name__ == "__main__":
    unittest.main()
