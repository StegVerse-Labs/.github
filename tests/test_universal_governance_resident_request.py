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
    def test_clean_env_forwards_only_nonsecret_source_locators(self):
        env = clean_env({
            "PATH": "/usr/bin",
            "STEGVERSE_STEGCORE_SOURCE_ROOT": "/local/stegcore",
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/local/master-records",
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "GITHUB_ACTIONS": "true",
            "OPENAI_API_KEY": "forbidden",
        })
        self.assertEqual(env["STEGVERSE_STEGCORE_SOURCE_ROOT"], "/local/stegcore")
        self.assertEqual(env["STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"], "/local/master-records")
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("GITHUB_ACTIONS", env)
        self.assertNotIn("OPENAI_API_KEY", env)

    def test_consumer_invokes_only_targeted_existing_task_path(self):
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

            observed = runtime / "receipts/universal-governance-enforced-reference/latest.json"
            observed.parent.mkdir(parents=True)
            observed.write_text(json.dumps({
                "reference_enforced_boundary_observed": True,
                "bypass_negative_control_passed": True,
                "master_records_custody_accepted": True,
                "real_external_system_enforced_activation": False,
            }), encoding="utf-8")

            calls = []
            def runner(command, **kwargs):
                calls.append((command, kwargs))
                payload = {
                    "execution_result": {
                        "state": "COMPLETED",
                        "transition_id": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED",
                    }
                }
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload) + "\n", stderr="")

            receipt = consume(
                source,
                runtime,
                runner=runner,
                env={
                    "PATH": "/usr/bin",
                    "STEGVERSE_STEGCORE_SOURCE_ROOT": "/local/stegcore",
                    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/local/master-records",
                    "GITHUB_TOKEN": "forbidden",
                },
            )
            self.assertEqual(receipt["state"], "COMPLETED")
            self.assertTrue(receipt["reference_enforced_boundary_observed"])
            self.assertTrue(receipt["bypass_negative_control_passed"])
            self.assertTrue(receipt["master_records_custody_accepted"])
            self.assertFalse(receipt["real_external_system_enforced_activation"])
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertIn("--task-id", command)
            self.assertIn(TARGET_TASK, command)
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertTrue((runtime / CONSUMPTION_REL).is_file())


if __name__ == "__main__":
    unittest.main()
