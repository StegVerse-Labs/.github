from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workers/stegclaw_p4_profiled_resident_execution.py"
ORG_WORKER = ROOT / "workers/organization_local_resident_boundary_executor.py"
REFRESH = ROOT / "scripts/refresh_sovereign_worker_runtime_source.py"
REFRESH_BASE = ROOT / "scripts/refresh_sovereign_worker_runtime_source_base.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class StegClawP4ProfiledResidentExecutionTests(unittest.TestCase):
    def test_packet_is_exactly_subject_bound_and_non_authorizing(self):
        m = load(DISPATCH, "stegclaw_p4_dispatch")
        packet = m.packet()
        self.assertEqual("DATA-CONTINUATION-STEGCLAW-P4", packet["payload"]["subject_task_id"])
        self.assertEqual("runtime-node:data-continuation-stegclaw-p4", packet["payload"]["runtime_node_profile_id"])
        self.assertEqual(m.sha256_uri(packet["payload"]), packet["payload_hash"])
        self.assertEqual("TV/TVC", packet["credential_authority"])
        self.assertEqual("NONE", packet["github_token_runtime_authority"])
        self.assertFalse(packet["request_grants_execution_authority"])
        self.assertFalse(packet["carrier_grants_execution_authority"])
        self.assertFalse(packet["canonical_state_change_authorized"])

    def test_exact_organization_local_receipt_satisfies_p4_executor_predicate_only(self):
        m = load(DISPATCH, "stegclaw_p4_dispatch_receipt")
        expected = m.packet()
        receipt = {
            "schema":"stegverse.organization-local-boundary.receipt/v1",
            "task_id":m.ORG_TASK,
            "packet_id":m.PACKET_ID,
            "payload_hash":expected["payload_hash"],
            "ingress_packet_sha256":m.sha256_uri(expected),
            "disposition":"ACCEPTED_LOCAL_BOUNDARY",
            "credential_authority":"TV/TVC",
            "github_token_runtime_authority":"NONE",
            "canonical_state_changed":False,
            "external_side_effect_performed":False,
            "authority_effect":"NONE",
            "claim_id":"ORG-CLAIM-G7",
            "fencing_token":7,
        }
        self.assertTrue(m.verified(receipt, expected))
        receipt["packet_id"] = "other"
        self.assertFalse(m.verified(receipt, expected))

    def test_consumed_ingress_moves_out_of_live_queue_without_losing_bytes(self):
        m = load(ORG_WORKER, "org_boundary_queue")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ingress = root / "ingress" / "one.json"
            consumed = root / "consumed"
            ingress.parent.mkdir(parents=True)
            ingress.write_bytes(b'{"x":1}\n')
            destination = m.archive_consumed_ingress(ingress, consumed)
            self.assertFalse(ingress.exists())
            self.assertEqual(b'{"x":1}\n', destination.read_bytes())

    def test_worker_bridge_is_covered_by_both_resident_refreshes(self):
        for path in (REFRESH, REFRESH_BASE):
            text = path.read_text(encoding="utf-8")
            self.assertIn('Path("workers")', text)
        self.assertTrue(DISPATCH.is_file())


if __name__ == "__main__":
    unittest.main()
