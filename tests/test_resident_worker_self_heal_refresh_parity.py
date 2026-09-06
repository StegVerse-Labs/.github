from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "refresh_sovereign_worker_runtime_source",
    ROOT / "scripts/refresh_sovereign_worker_runtime_source.py",
)
assert SPEC and SPEC.loader
refresh_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh_mod)


class ResidentWorkerSelfHealRefreshParityTests(unittest.TestCase):
    def test_self_heal_module_is_part_of_static_local_refresh(self) -> None:
        rel = Path("scripts/repair_resident_worker_presence.py")
        self.assertIn(rel, refresh_mod.STATIC_FILES)

    def test_refresh_materializes_self_heal_without_copying_mutable_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            for rel in (
                "heartbeat_runtime",
                "workers",
                "handoffs",
                "authorizations",
                "schemas",
                "cost-basis",
                "management",
                "state_language",
                "source-bundles",
                "review-packages",
                "scripts",
                "control/worker-registry.d",
                "control/process-worker-adapters.d",
                "control/task-vectors",
                "control/resident-execution-request.d",
            ):
                (source / rel).mkdir(parents=True, exist_ok=True)
            (source / "heartbeat_runtime/worker_runtime.py").write_text("# worker\n", encoding="utf-8")
            (source / "heartbeat_runtime/intr_derived_carrier.py").write_text("# carrier\n", encoding="utf-8")
            (source / "scripts/run_worker_runtime.py").write_text("# runner\n", encoding="utf-8")
            (source / "scripts/repair_resident_worker_presence.py").write_text("SELF_HEAL='canonical'\n", encoding="utf-8")
            (source / "control/worker-registry.json").write_text("{}\n", encoding="utf-8")
            (source / "control/process-worker-adapters.json").write_text("{}\n", encoding="utf-8")
            for rel in refresh_mod.STATIC_FILES + refresh_mod.CONTROL_FILES:
                path = source / rel
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("# fixture\n", encoding="utf-8")

            receipt = refresh_mod.refresh(source, runtime)
            materialized = runtime / "scripts/repair_resident_worker_presence.py"
            self.assertTrue(materialized.is_file())
            self.assertEqual(materialized.read_text(encoding="utf-8"), "SELF_HEAL='canonical'\n")
            self.assertIn("scripts/repair_resident_worker_presence.py", receipt["copied_static_paths"])
            self.assertTrue(receipt["mutable_runtime_state_preserved"])
            self.assertFalse(receipt["network_fetch_performed"])
            self.assertEqual(receipt["authority_effect"], "NONE_LOCAL_SOURCE_REFRESH")


if __name__ == "__main__":
    unittest.main()
