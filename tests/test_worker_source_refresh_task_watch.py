from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_worker_source_refresh_service_test",
    ROOT / "scripts/install_sovereign_worker_source_refresh_service.py",
)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class WorkerSourceRefreshTaskWatchTests(unittest.TestCase):
    def test_rendered_path_unit_watches_organization_task_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            packages = base / "packages"
            source.mkdir()
            runtime.mkdir()
            service, path_unit = MOD.render_units(
                source_root=source,
                runtime_root=runtime,
                python=Path("/usr/bin/python3"),
                source_package_root=packages,
            )
            self.assertIn(f"PathChanged={source / 'tasks'}", path_unit)
            self.assertIn("dispatch_resident_execution_requests.py", service)
            self.assertNotIn("GITHUB_TOKEN", service)
            self.assertNotIn("git fetch", service)


if __name__ == "__main__":
    unittest.main()
