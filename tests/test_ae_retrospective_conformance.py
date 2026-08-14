from __future__ import annotations
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "control" / "admissible-existence-retrospective-conformance.json"

class AERetrospectiveConformanceTests(unittest.TestCase):
    def setUp(self):
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        self.entries = {x["task_id"]: x for x in data["entries"]}
        self.report = data

    def test_exact_effective_denominator(self):
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_ae_retrospective_conformance.py")], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("effective_tasks=26 classified=26", p.stdout)

    def test_no_non_tvtvc_runtime_authority(self):
        self.assertEqual(self.report["credential_authority"], "TV/TVC")
        self.assertFalse(self.report["github_token_runtime_authority"])

    def test_local_model_remains_admissible(self):
        for task_id in ("SHWP-DURABLE-RUNTIME-ACTIVATION", "SHWP-ECOSYSTEM-CHAT-INFERENCE-001", "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"):
            self.assertEqual(self.entries[task_id]["capability_id"], "stegverse:capability:sovereign-local-model:v1")
            self.assertEqual(self.entries[task_id]["phase"], "ADMISSIBLE")

    def test_source_generation_is_declared_not_activated(self):
        entry = self.entries["SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001"]
        self.assertEqual(entry["capability_id"], "stegverse:capability:formalism-source-generation:v1")
        self.assertEqual(entry["phase"], "DECLARED")
        self.assertEqual(entry["task_relationship"], "develops_capability")
        self.assertEqual(entry["result"], "PASS")

    def test_trade_paths_remain_admissible(self):
        self.assertEqual(self.entries["STEGFIN-CONTINUITY-CARRIER-007"]["phase"], "ADMISSIBLE")
        self.assertEqual(self.entries["SHWP-STEGFIN-SOVEREIGN-TRADING-001"]["capability_id"], "stegverse:capability:stegfin-sovereign-internal-trading:v1")
        self.assertEqual(self.entries["SHWP-STEGFIN-SOVEREIGN-TRADING-001"]["phase"], "ADMISSIBLE")

    def test_heartbeat_semantic_debt_is_visible(self):
        for task_id in ("SHWP-DURABLE-RUNTIME-ACTIVATION", "SHWP-REPO-HEARTBEAT-FEDERATION-001"):
            self.assertEqual(self.entries[task_id]["result"], "REVIEW_REQUIRED")
            self.assertIn("heartbeat", self.entries[task_id]["rationale"].lower())

if __name__ == "__main__": unittest.main()
