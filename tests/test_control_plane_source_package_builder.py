from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from workers import control_plane_source_package as controlpkg

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_control_plane_source_package", ROOT / "scripts/build_control_plane_source_package.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ControlPlaneSourcePackageBuilderTests(unittest.TestCase):
    def test_builder_emits_valid_allowlisted_delta(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "workers/example.py"
            target.parent.mkdir(parents=True)
            target.write_text("value = 1\n", encoding="utf-8")
            package = mod.build(root, ("workers/example.py",))
        verified = controlpkg.validate_package(package)
        self.assertEqual(package["component_id"], "stegverse.control-plane")
        self.assertFalse(package["credential_material_included"])
        self.assertEqual(package["authority_effect"], "NONE_SOURCE_TRANSPORT_ONLY")
        self.assertEqual(verified["manifest"]["file_count"], 1)

    def test_builder_rejects_non_allowlisted_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "README.md"
            target.write_text("no\n", encoding="utf-8")
            with self.assertRaises(controlpkg.ControlPlaneSourcePackageError):
                mod.build(root, ("README.md",))


if __name__ == "__main__":
    unittest.main()
