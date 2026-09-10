from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

from workers import control_plane_source_package as controlpkg

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_control_plane_source_package", ROOT / "scripts/build_control_plane_source_package.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_builder_emits_valid_allowlisted_delta() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        target = root / "workers/example.py"
        target.parent.mkdir(parents=True)
        target.write_text("value = 1\n", encoding="utf-8")
        package = mod.build(root, ("workers/example.py",))
    verified = controlpkg.validate_package(package)
    assert package["component_id"] == "stegverse.control-plane"
    assert package["credential_material_included"] is False
    assert package["authority_effect"] == "NONE_SOURCE_TRANSPORT_ONLY"
    assert verified["manifest"]["file_count"] == 1


def test_builder_rejects_non_allowlisted_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        target = root / "README.md"
        target.write_text("no\n", encoding="utf-8")
        try:
            mod.build(root, ("README.md",))
        except controlpkg.ControlPlaneSourcePackageError:
            return
    raise AssertionError("non-allowlisted path should fail closed")
