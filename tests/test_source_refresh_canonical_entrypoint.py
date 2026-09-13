from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_worker_source_refresh_service",
    ROOT / "scripts/install_sovereign_worker_source_refresh_service.py",
)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class SourceRefreshCanonicalEntrypointTests(unittest.TestCase):
    def test_watcher_executes_refresh_from_canonical_source_not_stale_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "canonical-source"
            runtime = base / "resident-runtime"
            packages = base / "packages"
            source.mkdir()
            runtime.mkdir()
            service, path_unit = subject.render_units(
                source_root=source,
                runtime_root=runtime,
                python=Path("/usr/bin/python3"),
                source_package_root=packages,
            )
            canonical_refresh = source.resolve() / "scripts/refresh_sovereign_worker_runtime_source.py"
            stale_runtime_refresh = runtime.resolve() / "scripts/refresh_sovereign_worker_runtime_source.py"
            self.assertIn(str(canonical_refresh), service)
            self.assertNotIn(str(stale_runtime_refresh), service)
            self.assertIn(f"--source-root \"{source.resolve()}\"", service)
            self.assertIn(f"--runtime-root \"{runtime.resolve()}\"", service)
            self.assertIn(str(runtime.resolve() / "scripts/dispatch_resident_execution_requests.py"), service)
            self.assertIn(f"PathChanged={source.resolve() / 'scripts'}", path_unit)

    def test_render_still_rejects_collapsed_source_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(ValueError):
                subject.render_units(
                    source_root=root,
                    runtime_root=root,
                    python=Path("/usr/bin/python3"),
                )


if __name__ == "__main__":
    unittest.main()
