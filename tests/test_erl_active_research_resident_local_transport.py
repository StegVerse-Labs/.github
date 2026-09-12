from __future__ import annotations

import hashlib
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


class ERLResidentLocalTransportTests(unittest.TestCase):
    def test_transport_validator_accepts_exact_resident_local_headers(self):
        mod = load("workers/erl_active_research_transport.py", "erl_transport")
        body = b'{"schema":"stegverse.erl.active-research-intr-binding/v1"}'
        result = mod.validate_headers(
            {
                "Content-Type": "application/json",
                "X-StegVerse-Transport": "InTr",
                "X-StegVerse-Transport-Origin": mod.ORIGIN,
                "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
            },
            body,
        )
        self.assertEqual(result["origin"], mod.ORIGIN)
        self.assertIsNone(result["authorization_id"])
        self.assertEqual(result["payload_sha256_uri"], "sha256:" + hashlib.sha256(body).hexdigest())

    def test_transport_validator_rejects_tvc_authorization_claim(self):
        mod = load("workers/erl_active_research_transport.py", "erl_transport_reject_auth")
        body = b"{}"
        with self.assertRaisesRegex(ValueError, "cannot_claim_tvc_relay_authorization"):
            mod.validate_headers(
                {
                    "Content-Type": "application/json",
                    "X-StegVerse-Transport": "InTr",
                    "X-StegVerse-Transport-Origin": mod.ORIGIN,
                    "X-StegVerse-Authorization-Id": "RELAY-EGRESS-AUTH-FORBIDDEN",
                    "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
                },
                body,
            )

    def test_resident_local_input_requires_only_binding_and_loopback_ingress(self):
        mod = load(
            "scripts/materialize_erl_active_research_intr_resident_local_input.py",
            "erl_local_input",
        )
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            binding_rel = Path("intr-payloads/erl-active-research/SRC-1.binding.json")
            binding = runtime / binding_rel
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text("{}\n", encoding="utf-8")
            receipt = {
                "schema": mod.BINDING_RECEIPT_SCHEMA,
                "state": "BINDING_MATERIALIZED_AWAITING_AUTHENTIC_INTR_SUBMISSION",
                "task_id": mod.TASK_ID,
                "binding_ref": binding_rel.as_posix(),
            }
            receipt_path = runtime / mod.BINDING_RECEIPT_REL
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            result = mod.materialize(
                runtime,
                env={mod.INGRESS_URL_ENV: "http://127.0.0.1:43123/intr/materialization"},
            )
            self.assertEqual(result["state"], "INPUT_MATERIALIZED")
            self.assertFalse(result["tvc_authorization_required"])
            value = json.loads((runtime / mod.OUTPUT_REL).read_text(encoding="utf-8"))
            self.assertEqual(value["transport_origin"], mod.TRANSPORT_ORIGIN)
            self.assertFalse(value["transport_credential_required"])
            self.assertNotIn("tvc_relay_authorization_id", value)
            body = dict(value)
            claimed = body.pop("input_hash")
            self.assertEqual(claimed, mod.sha_uri(body))

    def test_resident_local_input_waits_only_for_ingress(self):
        mod = load(
            "scripts/materialize_erl_active_research_intr_resident_local_input.py",
            "erl_local_input_wait",
        )
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            binding_rel = Path("intr-payloads/erl-active-research/SRC-1.binding.json")
            binding = runtime / binding_rel
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text("{}\n", encoding="utf-8")
            receipt = {
                "schema": mod.BINDING_RECEIPT_SCHEMA,
                "state": "BINDING_MATERIALIZED_AWAITING_AUTHENTIC_INTR_SUBMISSION",
                "task_id": mod.TASK_ID,
                "binding_ref": binding_rel.as_posix(),
            }
            receipt_path = runtime / mod.BINDING_RECEIPT_REL
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            result = mod.materialize(runtime, env={})
            self.assertEqual(result["state"], "INGRESS_NOT_MATERIALIZED")
            self.assertEqual(result["missing_inputs"], [mod.INGRESS_URL_ENV])
            self.assertFalse(result["tvc_authorization_required"])


if __name__ == "__main__":
    unittest.main()
