from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SITE-PUBLICATION-INTR-CONSUMER-001"


def load_worker():
    path = ROOT / "workers/site_publication_intr_consumer_worker.py"
    spec = importlib.util.spec_from_file_location("site_publication_worker_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SitePublicationWorkerRegistrationTests(unittest.TestCase):
    def test_registration_requires_fresh_independent_fence_without_preclaim(self) -> None:
        registry = json.loads((ROOT / "control/worker-registry.d/site-publication-intr-consumer-001.json").read_text())
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/site-publication-intr-consumer-001.json").read_text())
        handoff = json.loads((ROOT / "handoffs/SITE-PUBLICATION-INTR-CONSUMER-001.json").read_text())
        vector = json.loads((ROOT / "control/task-vectors/SITE-PUBLICATION-INTR-CONSUMER-001.json").read_text())
        task = registry["tasks"][0]
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertIsNone(task["claim_id"])
        self.assertIsNone(task["heartbeat_timing"])
        self.assertIsNone(task["lease"])
        self.assertEqual(task["admission"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertTrue(task["admission"]["fresh_fence_required"])
        self.assertFalse(task["admission"]["heartbeat_grants_execution_authority"])
        self.assertFalse(task["admission"]["event_materialization_grants_authority"])
        self.assertEqual(registry["authority_effect"], "NONE_REGISTRATION_ONLY")
        self.assertEqual(adapter["adapters"][0]["command"], ["python", "workers/site_publication_intr_consumer_worker.py"])
        self.assertEqual(adapter["adapters"][0]["env_allowlist"], ["STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID"])
        self.assertEqual(handoff["state"], "HANDOFF_READY")
        self.assertIsNone(handoff["task"]["fencing_token"])
        self.assertFalse(handoff["completion"]["runtime_observation_claimed"])
        self.assertFalse(handoff["completion"]["final_publication_transition_admitted"])
        self.assertEqual(vector["vector"], "50000000102000")
        self.assertFalse(vector["exact_metrics"]["activated"])

    def test_worker_source_requires_claim_and_fence(self) -> None:
        source = (ROOT / "workers/site_publication_intr_consumer_worker.py").read_text()
        self.assertIn('task.get("claim_id")', source)
        self.assertIn('get("fencing_token")', source)
        self.assertIn("return 3", source)
        self.assertIn("SITE_PUBLICATION_EVENT_CANDIDATE_VALIDATED", source)
        self.assertNotIn("final_publication_transition_admitted\": True", source)

    def _write_admitted_fixture(self, mod, root: Path, *, authority_effect: str = "NONE_INGRESS_CANDIDATE_ONLY"):
        materialization_id = "INTR-MAT-0e1ba4786b0ea8a00e1f166e"
        queue = root / "intr-materialization" / f"{materialization_id}.json"
        queue.parent.mkdir(parents=True)
        queue.write_text(json.dumps({"materialization_id": materialization_id}) + "\n")
        latest = root / mod.INGRESS_LATEST
        latest.parent.mkdir(parents=True)
        latest.write_text(json.dumps({
            "schema": mod.INGRESS_SCHEMA,
            "state": mod.INGRESS_STATE,
            "materialization_id": materialization_id,
            "queue_ref": str(queue),
            "exact_request_validated": True,
            "write_once_persisted": True,
            "request_grants_execution_authority": False,
            "claim_or_fence_minted": False,
            "authority_effect": authority_effect,
        }) + "\n")
        return materialization_id, queue

    def test_worker_resolves_exact_materialization_from_local_admitted_ingress(self) -> None:
        mod = load_worker()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            materialization_id, _ = self._write_admitted_fixture(mod, root)
            resolved, source = mod.resolve_admitted_materialization(root)
            self.assertEqual(resolved, materialization_id)
            self.assertEqual(source, "LOCAL_ADMITTED_INGRESS_RECEIPT")
            resolved, source = mod.resolve_admitted_materialization(root, materialization_id)
            self.assertEqual(resolved, materialization_id)
            self.assertEqual(source, "LOCAL_ADMITTED_INGRESS_RECEIPT")

    def test_worker_fails_closed_on_explicit_binding_conflict_or_missing_queue(self) -> None:
        mod = load_worker()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            _, queue = self._write_admitted_fixture(mod, root)
            resolved, source = mod.resolve_admitted_materialization(root, "INTR-MAT-aaaaaaaaaaaaaaaaaaaaaaaa")
            self.assertIsNone(resolved)
            self.assertEqual(source, "EXPLICIT_MATERIALIZATION_BINDING_CONFLICT")
            queue.unlink()
            resolved, source = mod.resolve_admitted_materialization(root)
            self.assertIsNone(resolved)
            self.assertEqual(source, "ADMITTED_INGRESS_QUEUE_BINDING_INVALID")

    def test_worker_rejects_ingress_receipt_with_authorizing_effect(self) -> None:
        mod = load_worker()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            self._write_admitted_fixture(mod, root, authority_effect="EXECUTION_AUTHORITY")
            resolved, source = mod.resolve_admitted_materialization(root)
            self.assertIsNone(resolved)
            self.assertEqual(source, "ADMITTED_INGRESS_RECEIPT_NOT_ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
