from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/stegverse001_evidence_chain_continuation_worker.py"
ADAPTER = ROOT / "control/process-worker-adapters.d/stegverse001-evidence-chain-continuation-001.json"
HANDOFF = ROOT / "handoffs/STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001.json"


class Sv001RendezvousEvidenceTransportTests(unittest.TestCase):
    def test_worker_reads_only_existing_non_authorizing_evidence_endpoint(self):
        source = WORKER.read_text(encoding="utf-8")
        self.assertIn("/api/resident-rendezvous/v1/evidence/site-governed-custody", source)
        self.assertIn("NONE_EVIDENCE_ONLY", source)
        self.assertIn("observed/site-master-records-custody.latest.json", source)
        self.assertNotIn("watch_stegverse001_autonomy_receipt.py", source)
        self.assertNotIn("consume_stegverse001_bounded_autonomy_request.py", source)

    def test_adapter_passes_only_rendezvous_location_and_node_identity(self):
        adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))["adapters"][0]
        allow = adapter["env_allowlist"]
        self.assertIn("STEGVERSE_RESIDENT_RENDEZVOUS_URL", allow)
        self.assertIn("STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF", allow)
        self.assertIn("observed/**", adapter["bound_state_allowed_paths"])
        self.assertNotIn("GITHUB_TOKEN", allow)
        self.assertNotIn("GH_TOKEN", allow)

    def test_handoff_admits_observation_service_not_gateway_authority(self):
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        self.assertEqual(handoff["execution"]["allowed_services"], ["resident-rendezvous-site-custody-evidence-read"])
        self.assertTrue(handoff["authority"]["bounded_local_observation_authority"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])


if __name__ == "__main__":
    unittest.main()
