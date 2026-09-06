from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_sovereign_control_plane_bundle.py"
spec = importlib.util.spec_from_file_location("package_sovereign_control_plane_bundle", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class RuntimePresenceMasterRecordsBundleFloorTests(unittest.TestCase):
    def test_master_records_floor_contains_runtime_presence_custody_merge(self) -> None:
        self.assertEqual(
            module.MASTER_RECORDS_SV001_SOURCE_FLOOR,
            "8e33b3e95d3d9e34387fe393031f44bebcdb5d57",
        )
        self.assertIn(
            "scripts/intake_resident_runtime_presence.py",
            module.MASTER_RECORDS_SV001_PROTECTED_PATHS,
        )
        self.assertIn(
            "schemas/resident_runtime_presence_custody.schema.json",
            module.MASTER_RECORDS_SV001_PROTECTED_PATHS,
        )

    def test_bundle_rejects_master_records_root_without_presence_importer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source"
            mr = Path(td) / "master-records"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            for rel in (
                "scripts/watch_stegverse001_autonomy_receipt.py",
                "scripts/import_stegverse001_autonomy_receipt.py",
            ):
                path = mr / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# legacy\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "Master Records source root invalid"):
                module.build_bundle(root, Path(td) / "bundle.zip", master_records_root=mr)


if __name__ == "__main__":
    unittest.main()
