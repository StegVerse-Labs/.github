from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    path = ROOT / "scripts/submit_erl_active_research_intr_binding_local.py"
    spec = importlib.util.spec_from_file_location("erl_runtime_proof", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(mod):
    request = {
        "operation_id": "ERL-ACTIVE-RESEARCH-PROOF",
        "packet_id": "INTR-0123456789abcdef01234567",
        "payload_hash": "sha256:" + "a" * 64,
    }
    operation_hash = mod.sha_uri(
        {
            "operation_id": request["operation_id"],
            "packet_id": request["packet_id"],
            "payload_hash": request["payload_hash"],
        }
    )

    def hop(index, prior):
        body = {
            "schema": "stegverse.intr.hop_receipt/v1",
            "receipt_id": f"ERL-PROOF-{index}",
            "packet_id": request["packet_id"],
            "hop_index": index,
            "direction": "FORWARD",
            "from_role": mod.FULL_PATH[index - 1],
            "to_role": mod.FULL_PATH[index],
            "operation_hash": operation_hash,
            "payload_hash": request["payload_hash"],
            "prior_receipt_hash": prior,
            "boundary_identity_ref": f"resident://proof-{index}",
            "boundary_verification": "VERIFIED",
            "transition_state": "FORWARDED",
            "secret_plaintext_present": False,
            "authority_transfer": False,
            "recorded_at": "2026-09-12T17:00:00Z",
        }
        return {**body, "receipt_hash": mod.sha_uri(body)}

    hop1 = hop(1, None)
    hop2 = hop(2, hop1["receipt_hash"])
    terminal_body = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "materialization_id": "INTR-MAT-0123456789abcdef01234567",
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "b" * 64,
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "payload_hash": request["payload_hash"],
        "payload_ref": "runtime-local:proof.json",
        "destination": {"boundary": "KV", "subsystem": "KnowledgeVault:Interlock"},
        "boundary_path": ["DEVICE_SYSTEM", "KV"],
        "downstream_owner_ref": "StegVerse-Labs/continuity-vault-kit#79",
        "prior_transport_receipt_hash": hop2["receipt_hash"],
        "erl_full_path": mod.FULL_PATH,
        "erl_upstream_receipt_hashes": [hop1["receipt_hash"], hop2["receipt_hash"]],
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
    terminal = {**terminal_body, "request_hash": mod.sha_uri(terminal_body)}
    response = {
        "hop_receipts": [hop1, hop2],
        "terminal_materialization_request": terminal,
    }
    return request, response


class ERLRuntimeProofHardeningTests(unittest.TestCase):
    def test_recomputes_hop_and_terminal_hashes(self):
        mod = load()
        request, response = fixture(mod)
        result = mod.verify_admission_proof(response, request)
        self.assertEqual(result["proof_verification"], "VERIFIED")
        self.assertEqual(result["upstream_receipt_hashes"], [r["receipt_hash"] for r in response["hop_receipts"]])
        self.assertEqual(result["terminal_request_hash"], response["terminal_materialization_request"]["request_hash"])
        self.assertEqual(result["ingress_response_hash"], mod.sha_uri(response))

    def test_rejects_tampered_hop_receipt_hash(self):
        mod = load()
        request, response = fixture(mod)
        response["hop_receipts"][0]["receipt_hash"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(RuntimeError, "receipt_hash_mismatch"):
            mod.verify_admission_proof(response, request)

    def test_rejects_tampered_terminal_request_hash(self):
        mod = load()
        request, response = fixture(mod)
        response["terminal_materialization_request"]["request_hash"] = "sha256:" + "e" * 64
        with self.assertRaisesRegex(RuntimeError, "terminal_request_hash_mismatch"):
            mod.verify_admission_proof(response, request)


if __name__ == "__main__":
    unittest.main()
