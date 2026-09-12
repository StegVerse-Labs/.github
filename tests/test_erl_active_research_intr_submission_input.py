from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ErlSubmissionInputMaterializerTests(unittest.TestCase):
    def setUp(self):
        self.mod = load(
            "scripts/materialize_erl_active_research_intr_submission_input.py",
            "erl_submission_input_materializer_test",
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_ready_binding_receipt(self):
        binding_rel = Path("intr-payloads/erl-active-research/SRC-1.binding.json")
        binding_path = self.runtime / binding_rel
        binding_path.parent.mkdir(parents=True, exist_ok=True)
        binding_path.write_text("{}\n", encoding="utf-8")
        receipt = {
            "schema": self.mod.BINDING_RECEIPT_SCHEMA,
            "state": "BINDING_MATERIALIZED_AWAITING_AUTHENTIC_INTR_SUBMISSION",
            "task_id": self.mod.TASK_ID,
            "binding_ref": binding_rel.as_posix(),
        }
        receipt_path = self.runtime / self.mod.BINDING_RECEIPT_REL
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        return binding_rel

    def test_waits_when_binding_not_materialized(self):
        result = self.mod.materialize(self.runtime, env={})
        self.assertEqual(result["state"], "BINDING_NOT_MATERIALIZED")
        self.assertFalse(result["input_materialized"])
        self.assertFalse((self.runtime / self.mod.OUTPUT_REL).exists())

    def test_waits_when_existing_tvc_authorization_or_ingress_missing(self):
        self.write_ready_binding_receipt()
        result = self.mod.materialize(self.runtime, env={})
        self.assertEqual(result["state"], "AUTHORIZATION_OR_INGRESS_NOT_MATERIALIZED")
        self.assertIn(self.mod.INGRESS_URL_ENV, result["missing_inputs"])
        self.assertIn(self.mod.AUTHORIZATION_ID_ENV, result["missing_inputs"])
        self.assertFalse(result["tvc_authorization_created"])
        self.assertFalse(result["listener_created"])

    def test_materializes_exact_runtime_local_input_from_existing_refs(self):
        binding_rel = self.write_ready_binding_receipt()
        env = {
            self.mod.INGRESS_URL_ENV: "http://127.0.0.1:43123/intr/materialization",
            self.mod.AUTHORIZATION_ID_ENV: "TVC-AUTH-EXISTING",
        }
        result = self.mod.materialize(self.runtime, env=env)
        self.assertEqual(result["state"], "INPUT_MATERIALIZED")
        self.assertTrue(result["input_materialized"])
        self.assertFalse(result["tvc_authorization_created"])
        self.assertFalse(result["listener_created"])
        value = json.loads((self.runtime / self.mod.OUTPUT_REL).read_text(encoding="utf-8"))
        self.assertEqual(value["binding_ref"], binding_rel.as_posix())
        self.assertEqual(value["ingress_url"], env[self.mod.INGRESS_URL_ENV])
        self.assertEqual(value["tvc_relay_authorization_id"], env[self.mod.AUTHORIZATION_ID_ENV])
        body = dict(value)
        claimed = body.pop("input_hash")
        self.assertEqual(claimed, self.mod.sha_uri(body))
        self.assertFalse(value["request_grants_execution_authority"])
        self.assertFalse(value["provider_operation_authorized"])

    def test_rejects_non_loopback_ingress(self):
        self.write_ready_binding_receipt()
        env = {
            self.mod.INGRESS_URL_ENV: "https://example.com/intr/materialization",
            self.mod.AUTHORIZATION_ID_ENV: "TVC-AUTH-EXISTING",
        }
        with self.assertRaisesRegex(RuntimeError, "loopback"):
            self.mod.materialize(self.runtime, env=env)


if __name__ == "__main__":
    unittest.main()
