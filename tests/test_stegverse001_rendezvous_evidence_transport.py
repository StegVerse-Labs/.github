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

    def test_worker_is_sovereign_local_primary_and_hosted_fallback_only(self):
        source = WORKER.read_text(encoding="utf-8")
        self.assertIn('LOCAL_RENDEZVOUS_BASES = ("http://127.0.0.1:8000", "http://localhost:8000")', source)
        self.assertIn('"resident_rendezvous_primary_transport": "SOVEREIGN_LOCAL_RESIDENT"', source)
        self.assertIn('"hosted_rendezvous_role": "FALLBACK_ONLY"', source)
        self.assertIn("for base in local_candidates:", source)
        self.assertIn("return _fetch_evidence_from_reachable_base(bound, base, node_ref)", source)
        self.assertIn("Hosted transport is fallback only", source)
        self.assertLess(source.index("for base in local_candidates:"), source.index("Hosted transport is fallback only"))

    def test_reachable_local_state_cannot_fall_through_to_hosted_transport(self):
        source = WORKER.read_text(encoding="utf-8")
        self.assertIn('if payload.get("state") == "NO_EVIDENCE":\n        return None', source)
        self.assertIn("reachable sovereign resident discovery response invalid", source)
        self.assertIn("reachable sovereign resident discovery authority boundary invalid", source)
        self.assertIn("reachable resident discovery lost custody evidence endpoint", source)
        self.assertIn("configured resident node ref disagrees with sovereign local discovery", source)

    def test_worker_recomputes_proof_digest_and_requires_canonical_node_ref(self):
        source = WORKER.read_text(encoding="utf-8")
        self.assertIn('CANONICAL_NODE_REF = re.compile(r"^SV-NODE-[0-9a-f]{24}$")', source)
        self.assertIn("_canonical_sha256_uri(proof)", source)
        self.assertIn("resident rendezvous evidence proof digest mismatch", source)
        self.assertIn("heartbeat_granted_authority", source)
        self.assertIn("historical_state_retroactively_authorized", source)

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
