from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_sovereign_runtime",
    ROOT / "scripts/bootstrap_sovereign_runtime.py",
)
assert SPEC and SPEC.loader
boot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(boot)


class ResidentSelfHealBootstrapSourcePreflightTests(unittest.TestCase):
    def test_self_heal_is_a_canonical_bootstrap_source_prerequisite(self) -> None:
        self.assertIn(
            Path("scripts/repair_resident_worker_presence.py"),
            boot.REQUIRED_SOURCE_FILES,
        )

    def test_missing_self_heal_fails_local_runtime_eligibility(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            for rel in boot.REQUIRED_SOURCE_FILES:
                if rel == Path("scripts/repair_resident_worker_presence.py"):
                    continue
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# fixture\n", encoding="utf-8")

            result = boot.local_eligibility(source, runtime, env={})
            self.assertFalse(result["canonical_source_complete"])
            self.assertFalse(result["eligible"])
            self.assertFalse(
                result["required_source_files"]["scripts/repair_resident_worker_presence.py"]
            )
            self.assertEqual(
                result["authority_effect"],
                "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
            )


if __name__ == "__main__":
    unittest.main()
