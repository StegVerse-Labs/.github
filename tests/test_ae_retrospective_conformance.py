from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "control" / "admissible-existence-retrospective-conformance.json"


class AERetrospectiveConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.entries = {entry["task_id"]: entry for entry in self.report["entries"]}

    def test_exact_effective_denominator_is_classified(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_ae_retrospective_conformance.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("effective_tasks=25 classified=25", proc.stdout)

    def test_no_non_tvtvc_runtime_authority(self) -> None:
        self.assertEqual(self.report["credential_authority"], "TV/TVC")
        self.assertFalse(self.report["github_token_runtime_authority"])
        for entry in self.entries.values():
            self.assertEqual(entry["credential_authority"], "TV/TVC")
            self.assertFalse(entry["github_token_runtime_authority"])

    def test_local_model_is_admissible_not_falsely_activated(self) -> None:
        for task_id in (
            "SHWP-DURABLE-RUNTIME-ACTIVATION",
            "SHWP-ECOSYSTEM-CHAT-INFERENCE-001",
            "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28",
        ):
            entry = self.entries[task_id]
            self.assertEqual(entry["capability_id"], "stegverse:capability:sovereign-local-model:v1")
            self.assertEqual(entry["phase"], "ADMISSIBLE")
            self.assertIsNone(entry["activation_proof_ref"])

    def test_trade_tasks_remain_admissible_until_real_proof(self) -> None:
        for task_id in (
            "STEGFIN-LIVE-ENTRY-003",
            "STEGFIN-CONTINUITY-CARRIER-007",
            "STEGFIN-LIVE-PRETRADE-005",
            "SHWP-STEGFIN-SOVEREIGN-TRADING-001",
        ):
            entry = self.entries[task_id]
            self.assertEqual(entry["capability_id"], "stegverse:capability:stegfin-base-pretrade:v1")
            self.assertEqual(entry["phase"], "ADMISSIBLE")
            self.assertIsNone(entry["activation_proof_ref"])

    def test_heartbeat_architecture_corrections_are_not_silently_passed(self) -> None:
        for task_id in ("SHWP-DURABLE-RUNTIME-ACTIVATION", "SHWP-REPO-HEARTBEAT-FEDERATION-001"):
            entry = self.entries[task_id]
            self.assertEqual(entry["result"], "REVIEW_REQUIRED")
            text = " ".join(entry["blockers"] + [entry["rationale"]]).lower()
            self.assertIn("heartbeat", text)


if __name__ == "__main__":
    unittest.main()
