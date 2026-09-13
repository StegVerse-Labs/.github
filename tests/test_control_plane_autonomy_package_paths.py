from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_control_plane_source_package",
    ROOT / "scripts/build_control_plane_source_package.py",
)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class ControlPlaneAutonomyPackagePathTests(unittest.TestCase):
    def test_default_package_carries_stale_resident_recovery_chain(self) -> None:
        required = {
            "control/resident-execution-request.d/healer-sovereign-scheduler-001.json",
            "scripts/refresh_sovereign_worker_runtime_source.py",
            "scripts/install_sovereign_worker_source_refresh_service.py",
            "scripts/dispatch_resident_execution_requests.py",
            "scripts/refresh_and_dispatch_resident_requests.py",
            "scripts/refresh_and_execute_resident_task.py",
            "scripts/consume_healer_sovereign_scheduler_request.py",
            "source-bundles/reusable-task-registry.d/RT-SOVEREIGN-SOURCE-REFRESH-001.json",
            "source-bundles/reusable-task-registry.d/RT-REUSABLE-TASK-SCHEDULER-001.json",
        }
        self.assertTrue(required.issubset(set(subject.DEFAULT_PATHS)))
        package = subject.build(ROOT, subject.DEFAULT_PATHS)
        included = {row["path"] for row in package["manifest"]["files"]}
        self.assertTrue(required.issubset(included))
        self.assertEqual(package["component_id"], "stegverse.control-plane")
        self.assertEqual(package["authority_effect"], "NONE_SOURCE_TRANSPORT_ONLY")
        self.assertFalse(package["credential_material_included"])


if __name__ == "__main__":
    unittest.main()
