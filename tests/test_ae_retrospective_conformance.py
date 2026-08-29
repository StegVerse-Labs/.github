from __future__ import annotations
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "control" / "admissible-existence-retrospective-conformance.json"
FRAGMENT_DIR = ROOT / "control" / "admissible-existence-retrospective-conformance.d"


def effective_entries():
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    entries = list(data["entries"])
    if FRAGMENT_DIR.exists():
        for path in sorted(FRAGMENT_DIR.glob("*.json")):
            fragment = json.loads(path.read_text(encoding="utf-8"))
            if fragment.get("schema") == "stegverse.admissible-existence-retrospective-conformance-fragment/v1":
                entries.extend(fragment.get("entries", []))
    return data, entries


class AERetrospectiveConformanceTests(unittest.TestCase):
    def setUp(self):
        data, entries = effective_entries()
        self.entries = {x["task_id"]: x for x in entries}
        self.report = data

    def test_exact_effective_denominator(self):
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_ae_retrospective_conformance.py")], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        expected = len(self.entries)
        self.assertIn(f"effective_tasks={expected} classified={expected}", p.stdout)

    def test_no_non_tvtvc_runtime_authority(self):
        self.assertEqual(self.report["credential_authority"], "TV/TVC")
        self.assertFalse(self.report["github_token_runtime_authority"])

    def test_local_model_remains_admissible(self):
        for task_id in ("SHWP-DURABLE-RUNTIME-ACTIVATION", "SHWP-ECOSYSTEM-CHAT-INFERENCE-001", "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"):
            self.assertEqual(self.entries[task_id]["capability_id"], "stegverse:capability:sovereign-local-model:v1")
            self.assertEqual(self.entries[task_id]["phase"], "ADMISSIBLE")

    def test_source_generation_is_admissible_not_activated(self):
        entry = self.entries["SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001"]
        self.assertEqual(entry["capability_id"], "stegverse:capability:formalism-source-generation:v1")
        self.assertEqual(entry["phase"], "ADMISSIBLE")
        self.assertEqual(entry["task_relationship"], "integrates_capability")
        self.assertEqual(entry["result"], "PASS")
        executor = self.entries["SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001"]
        self.assertEqual(executor["capability_id"], "stegverse:capability:formalism-source-generation:v1")
        self.assertEqual(executor["phase"], "ADMISSIBLE")
        self.assertNotEqual(executor["phase"], "ACTIVATED")
        self.assertEqual(executor["task_relationship"], "integrates_capability")
        self.assertEqual(executor["result"], "PASS")

    def test_uap_public_research_is_admissible_non_promoting(self):
        entry = self.entries["SHWP-ERL-UAP-MEDIA-001"]
        self.assertEqual(entry["capability_id"], "stegverse:capability:erl-uap-public-source-acquisition:v1")
        self.assertEqual(entry["phase"], "ADMISSIBLE")
        self.assertEqual(entry["task_relationship"], "integrates_capability")
        self.assertEqual(entry["result"], "PASS")

    def test_trade_paths_remain_admissible(self):
        self.assertEqual(self.entries["STEGFIN-CONTINUITY-CARRIER-007"]["phase"], "ADMISSIBLE")
        self.assertEqual(self.entries["SHWP-STEGFIN-SOVEREIGN-TRADING-001"]["capability_id"], "stegverse:capability:stegfin-sovereign-internal-trading:v1")
        self.assertEqual(self.entries["SHWP-STEGFIN-SOVEREIGN-TRADING-001"]["phase"], "ADMISSIBLE")

    def test_heartbeat_semantic_debt_is_visible(self):
        for task_id in ("SHWP-DURABLE-RUNTIME-ACTIVATION", "SHWP-REPO-HEARTBEAT-FEDERATION-001"):
            self.assertEqual(self.entries[task_id]["result"], "REVIEW_REQUIRED")
            self.assertIn("heartbeat", self.entries[task_id]["rationale"].lower())

    def test_tv_tvc_resident_proof_is_non_authorizing_runtime_support(self):
        entry = self.entries["SHWP-TV-TVC-RESIDENT-PROOF-001"]
        self.assertEqual(entry["ae_impact"], "NONE")
        self.assertIsNone(entry["phase"])
        self.assertEqual(entry["result"], "PASS")

if __name__ == "__main__": unittest.main()
