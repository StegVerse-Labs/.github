from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FALLBACK = Path("scripts/run_sovereign_ephemeral_console.py")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bootstrap = load("bootstrap_sovereign_runtime_dependency_parity", ROOT / "scripts/bootstrap_sovereign_runtime.py")
install = load("install_sovereign_heartbeat_service_dependency_parity", ROOT / "scripts/install_sovereign_heartbeat_service.py")
refresh = load("refresh_sovereign_worker_runtime_source_dependency_parity", ROOT / "scripts/refresh_sovereign_worker_runtime_source.py")


class G18EphemeralDependencyParityTests(unittest.TestCase):
    def test_all_resident_source_surfaces_require_or_copy_existing_fallback(self) -> None:
        self.assertIn(FALLBACK, set(bootstrap.REQUIRED_SOURCE_FILES))
        self.assertIn(FALLBACK.as_posix(), set(install.COPY_FILES))
        self.assertIn(FALLBACK, set(refresh.STATIC_FILES))

    def test_bootstrap_eligibility_fails_closed_when_fallback_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            runtime = root / "runtime"
            for rel in bootstrap.REQUIRED_SOURCE_FILES:
                if rel == FALLBACK:
                    continue
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n" if path.suffix == ".json" else "# test\n", encoding="utf-8")
            result = bootstrap.local_eligibility(source, runtime, env={})
            self.assertFalse(result["canonical_source_complete"])
            self.assertFalse(result["eligible"])
            self.assertFalse(result["required_source_files"][str(FALLBACK)])

    def test_local_refresh_rejects_source_missing_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            runtime = root / "runtime"
            required = (
                Path("heartbeat_runtime/worker_runtime.py"),
                Path("heartbeat_runtime/intr_derived_carrier.py"),
                Path("scripts/run_worker_runtime.py"),
                Path("control/worker-registry.json"),
                Path("control/process-worker-adapters.json"),
            )
            for rel in required:
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n" if path.suffix == ".json" else "# test\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "run_sovereign_ephemeral_console.py"):
                refresh._validate_roots(source, runtime)

    def test_materialization_copies_fallback_and_fails_when_source_omits_it(self) -> None:
        self.assertIn(FALLBACK.as_posix(), install.COPY_FILES)
        source_text = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
        self.assertIn('target_root / "scripts" / "run_sovereign_ephemeral_console.py"', source_text)


if __name__ == "__main__":
    unittest.main()
