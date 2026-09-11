from __future__ import annotations

import json
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from scripts import consume_site_publication_intr_materialization_request as mod


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def request():
    body = {
        "schema": mod.REQUEST_SCHEMA,
        "materialization_id": "INTR-MAT-" + "a" * 24,
        "state": mod.REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": mod.OPERATION_ID,
        "packet_id": "INTR-" + "b" * 24,
        "payload_hash": "sha256:" + "2" * 64,
        "payload_ref": "artifact://site-publication-manifest/" + "2" * 64,
        "destination": mod.DESTINATION,
        "boundary_path": mod.BOUNDARY_PATH,
        "downstream_owner_ref": mod.DOWNSTREAM_OWNER,
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
    return {**body, "request_hash": "sha256:" + sha256(canonical(body)).hexdigest()}


class SitePublicationConsumerTests(unittest.TestCase):
    def test_valid_request_yields_candidate_only(self):
        req = request()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / mod.REQUEST_DIR
            directory.mkdir(parents=True)
            (directory / f"{req['materialization_id']}.json").write_text(json.dumps(req), encoding="utf-8")
            receipt = mod.consume(root, req["materialization_id"])
            self.assertEqual(receipt["state"], "VALIDATED_FOR_EVENT_EPHEMERAL_RUNTIME_MATERIALIZATION")
            self.assertFalse(receipt["runtime_materialization_attempted"])
            self.assertFalse(receipt["public_https_profile_observed"])
            self.assertFalse(receipt["final_publication_transition_admitted"])
            self.assertFalse(receipt["render_allowed"])

    def test_hosted_or_authorizing_mutation_rejected(self):
        req = request()
        req["always_on_receiver_required"] = True
        body = dict(req)
        body.pop("request_hash")
        req["request_hash"] = "sha256:" + sha256(canonical(body)).hexdigest()
        with self.assertRaises(ValueError):
            mod.validate_request(req)

    def test_payload_ref_must_bind_exact_manifest_hash(self):
        req = request()
        req["payload_ref"] = "artifact://site-publication-manifest/" + "3" * 64
        body = dict(req)
        body.pop("request_hash")
        req["request_hash"] = "sha256:" + sha256(canonical(body)).hexdigest()
        with self.assertRaises(ValueError):
            mod.validate_request(req)


if __name__ == "__main__":
    unittest.main()
