from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.consume_universal_governance_enforced_reference_request import (
    CONSUMPTION_REL,
    REQUEST_REL,
    TARGET_TASK,
    clean_env,
    consume,
)

class UniversalGovernanceResidentRequestTests(unittest.TestCase):
    def test_clean_env_forwards_only_declared_nonsecret_locators(self):
        env = clean_env({
            "PATH": "/usr/bin",
            "STEGVERSE_STEGCORE_SOURCE_ROOT": "/local/stegcore",
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/local/master-records",
            "UNRELATED_SECRET": "excluded",
        })
        self.assertEqual(env["STEGVERSE_STEGCORE_SOURCE_ROOT"], "/local/stegcore")
        self.assertEqual(env["STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"], "/local/master-records")
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertNotIn("UNRELATED_SECRET", env)

    def test_consumer_invokes_only_targeted_worker_path_and_requires_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            source = root / "source"
            runtime.mkdir()
            source.mkdir()
            request_src = Path(__file__).resolve().parents[1] / REQUEST_REL
            request_dst = runtime / REQUEST_REL
            request_dst.parent.mkdir(parents=True)
            request_dst.write_text(request_src.read_text(encoding="utf-8"), encoding="utf-8")
            entry = runtime / "scripts/refresh_and_execute_resident_task.py"
            entry.parent.mkdir(parents=True)
            entry.write_text("# stub\n", encoding="utf-8")

            evidence_root = root / "home/.stegverse/state/universal-governance-enforced-reference"
            observed = evidence_root / "receipts/latest.json"
            observed.parent.mkdir(parents=True)
            observed.write_text(json.dumps({
                "reference_enforced_boundary_observed": True,
                "bypass_negative_control_passed": True,
                "master_records_custody_accepted": True,
                "real_external_system_enforced_activation": False,
            }), encoding="utf-8")

            def runner(command, **kwargs):
                payload = {"execution_result": {
                    "state": "COMPLETED",
                    "transition_id": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED",
                    "evidence_refs": ["receipts/latest.json"],
                }}
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload) + "\n", stderr="")

            old_home = __import__("os").environ.get("HOME")
            __import__("os").environ["HOME"] = str(root / "home")
            try:
                receipt = consume(
                    source,
                    runtime,
                    runner=runner,
                    env={
                        "PATH": "/usr/bin",
                        "HOME": str(root / "home"),
                        "STEGVERSE_STEGCORE_SOURCE_ROOT": "/local/stegcore",
                        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/local/master-records",
                    },
                )
            finally:
                if old_home is None:
                    __import__("os").environ.pop("HOME", None)
                else:
                    __import__("os").environ["HOME"] = old_home

            self.assertEqual(receipt["state"], "COMPLETED")
            self.assertTrue(receipt["reference_enforced_boundary_observed"])
            self.assertTrue(receipt["bypass_negative_control_passed"])
            self.assertTrue(receipt["master_records_custody_accepted"])
            self.assertFalse(receipt["real_external_system_enforced_activation"])
            self.assertIn("--task-id", receipt["command"])
            self.assertIn(TARGET_TASK, receipt["command"])
            self.assertTrue((runtime / CONSUMPTION_REL).is_file())

    def test_consumer_is_registered_for_refresh_and_dispatch(self):
        from scripts.dispatch_resident_execution_requests import CONSUMERS
        from scripts.refresh_and_dispatch_resident_requests import ALLOWED_TARGET_CONSUMERS
        from scripts.refresh_sovereign_worker_runtime_source import STATIC_FILES

        self.assertIn(
            ("universal_governance_enforced_reference", "scripts/consume_universal_governance_enforced_reference_request.py"),
            CONSUMERS,
        )
        self.assertIn("universal_governance_enforced_reference", ALLOWED_TARGET_CONSUMERS)
        self.assertIn(
            Path("scripts/consume_universal_governance_enforced_reference_request.py"),
            STATIC_FILES,
        )

if __name__ == "__main__":
    unittest.main()
