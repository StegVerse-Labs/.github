from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from workers import erl_active_research_intr_profile as erl
from scripts import install_erl_active_research_universal_intr_route as installer


def binding() -> dict:
    envelope = {
        "schema": erl.ENVELOPE_SCHEMA,
        "group_id": "ACTIVE-CYBER",
        "source_id": "CISA-IRAN",
        "source_url": "https://example.invalid/source",
        "required_storage_lane": "02_Research/ERL",
        "finding_authorized": False,
        "publication_authorized": False,
    }
    payload_hash = erl.sha_uri(envelope)
    intent = {
        "schema": erl.INTENT_SCHEMA,
        "protocol": "InTr",
        "operation_id": "ERL-ACTIVE-RESEARCH-test",
        "packet_id": "INTR-0123456789abcdef01234567",
        "payload_hash": payload_hash,
        "prior_transport_receipt_hash": None,
        "source": {"boundary": "EXTERNAL_SYSTEM", "subsystem": "ERL:ActiveResearchExternalSource"},
        "destination": {"boundary": "KV", "subsystem": "KnowledgeVault:ERL"},
        "boundary_path": list(erl.FULL_PATH),
        "interlock_required": True,
        "transport_semantics": {},
        "authority": {"authority_transfer": False, "transport_grants_execution_authority": False, "credential_authority": "TV/TVC"},
        "receipt_chain": {"required": True, "receipt_schema": erl.RECEIPT_SCHEMA, "payload_plaintext_in_receipts": False, "prior_hash_required_after_first_hop": True},
    }
    request_body = {
        "schema": erl.REQUEST_SCHEMA,
        "materialization_id": "INTR-MAT-0123456789abcdef01234567",
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": erl.INTENT_SCHEMA,
        "transport_protocol": "InTr",
        "transport_intent_hash": erl.sha_uri(intent),
        "operation_id": intent["operation_id"],
        "packet_id": intent["packet_id"],
        "payload_hash": payload_hash,
        "payload_ref": "erl://active-research/test",
        "destination": dict(intent["destination"]),
        "boundary_path": list(erl.FULL_PATH),
        "downstream_owner_ref": "StegVerse-Labs/Executive_Rhetoric_Ledger:active-research-kv-consumer",
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    request = {**request_body, "request_hash": erl.sha_uri(request_body)}
    body = {
        "schema": erl.BINDING_SCHEMA,
        "group_id": envelope["group_id"],
        "source_id": envelope["source_id"],
        "acquisition_envelope": envelope,
        "acquisition_envelope_sha256": payload_hash,
        "transport_intent": intent,
        "materialization_request": request,
        "expected_runtime_receipt_schema": erl.RECEIPT_SCHEMA,
        "expected_runtime_receipt_count": 3,
        "expected_boundary_path": list(erl.FULL_PATH),
        "runtime_receipts_present": False,
        "transport_execution_claimed": False,
        "finding_authorized": False,
        "publication_authorized": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return {**body, "binding_hash": erl.sha_uri(body)}


class ProfileTests(unittest.TestCase):
    def test_admission_preserves_identity_and_projects_existing_terminal_owner(self):
        value = binding()
        with tempfile.TemporaryDirectory() as tmp:
            result = erl.admit(runtime_root=Path(tmp), payload=value, transport_payload_sha256=erl.sha_uri(erl.canonical(value)))
            self.assertEqual([r["hop_index"] for r in result["hop_receipts"]], [1, 2])
            self.assertEqual(result["hop_receipts"][1]["prior_receipt_hash"], result["hop_receipts"][0]["receipt_hash"])
            terminal = result["terminal_materialization_request"]
            self.assertEqual(terminal["boundary_path"], erl.TERMINAL_PATH)
            self.assertEqual(terminal["destination"], erl.TERMINAL_DESTINATION)
            self.assertEqual(terminal["downstream_owner_ref"], erl.TERMINAL_OWNER)
            self.assertEqual(terminal["prior_transport_receipt_hash"], result["hop_receipts"][1]["receipt_hash"])
            self.assertEqual(terminal["packet_id"], value["transport_intent"]["packet_id"])
            self.assertEqual(terminal["operation_id"], value["transport_intent"]["operation_id"])
            self.assertEqual(terminal["payload_hash"], value["transport_intent"]["payload_hash"])
            self.assertFalse(result["terminal_runtime_receipt_present"])
            self.assertFalse(result["provider_operation_reexecution_authorized"])

    def test_rejects_skipped_boundary(self):
        value = binding()
        value["transport_intent"]["boundary_path"] = ["EXTERNAL_SYSTEM", "DEVICE_SYSTEM", "KV"]
        with self.assertRaisesRegex(ValueError, "erl_boundary_path_invalid"):
            erl.validate_binding(value)

    def test_rejects_authority_transfer(self):
        value = binding()
        value["transport_intent"]["authority"]["authority_transfer"] = True
        with self.assertRaisesRegex(ValueError, "erl_intent_authority_invalid"):
            erl.validate_binding(value)

    def test_write_once_collision_fails_closed(self):
        value = binding()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            erl.admit(runtime_root=root, payload=value, transport_payload_sha256="sha256:" + "a" * 64)
            target = root / erl.ERL_RECEIPT_DIR / (value["materialization_request"]["materialization_id"] + ".json")
            altered = json.loads(target.read_text())
            altered["packet_id"] = "changed"
            target.write_text(json.dumps(altered, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(ValueError, "erl_write_once_collision"):
                erl.admit(runtime_root=root, payload=value, transport_payload_sha256="sha256:" + "a" * 64)


class InstallerTests(unittest.TestCase):
    def test_transform_is_idempotent_and_reuses_shared_listener(self):
        source = '''from workers.sv002_intr_materialization_consumer import (  # noqa: E402\n    DESTINATION as SV002_DESTINATION,\n    DOWNSTREAM_OWNER as SV002_OWNER,\n    scrubbed_env as sv002_scrubbed_env,\n    validate_request as validate_sv002_request,\n)\nPROFILES={"profiles": ["HIL:Ingress", "SV002:PublicObservation"],}\nclass ThreadingHTTPServer: pass\nresult = hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)\n'''
        once = installer.transform(source)
        twice = installer.transform(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("ThreadingHTTPServer"), 1)
        self.assertIn("erl_active_research.admit", once)
        self.assertIn('"ERL:ActiveResearch"', once)


if __name__ == "__main__":
    unittest.main()
