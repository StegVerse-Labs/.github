from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


consumer = load("sv002_consumer", "workers/sv002_intr_materialization_consumer.py")
ingress = load("universal_ingress", "workers/universal_intr_profiled_ingress.py")
hil_profile = load("hil_profile", "workers/hil_intr_profiled_ingress.py")


class SV002EventEphemeralTests(unittest.TestCase):
    def request(self):
        body = {
            "schema": consumer.REQUEST_SCHEMA,
            "materialization_id": "INTR-MAT-" + "a" * 24,
            "state": consumer.REQUEST_STATE,
            "transport_schema": "stegverse.universal-intr-transport/v1",
            "transport_protocol": "InTr",
            "transport_intent_hash": "sha256:" + "1" * 64,
            "operation_id": "SV002-PUBLIC-OBSERVE-test",
            "packet_id": "INTR-" + "2" * 24,
            "payload_hash": "sha256:" + "3" * 64,
            "payload_ref": "browser:SV002_PUBLIC_OBSERVE",
            "destination": consumer.DESTINATION,
            "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
            "downstream_owner_ref": consumer.DOWNSTREAM_OWNER,
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
        body["request_hash"] = consumer.digest_uri(body)
        return body

    def test_request_is_g18_independent_and_non_authorizing(self):
        request = self.request()
        consumer.validate_request(request)
        self.assertFalse(request["always_on_receiver_required"])
        self.assertFalse(request["request_grants_execution_authority"])
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(consumer.DOWNSTREAM_OWNER, "StegVerse-Labs/.github#493")

    def test_profile_preserves_hil_and_advertises_sv002(self):
        profile = ingress.profile(False)
        self.assertEqual(profile["profiles"], ["HIL:Ingress", "SV002:PublicObservation", "KV:KnowledgeVaultInterlock", "Publisher:ArtifactTransfer", "KV:PublisherArtifactImport"])
        self.assertFalse(profile["g18_required"])
        legacy = hil_profile.build_profile(tls_enabled=False)
        self.assertEqual(legacy["schema"], "stegverse.hil-intr-materialization-ingress-profile/v1")
        self.assertIn("SV002:PublicObservation", legacy["additional_materialization_profiles"])

    def test_sv002_ingress_writes_distinct_receipt_and_dispatches_without_authority(self):
        request = self.request()
        payload = request
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        headers = {
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
            "X-StegVerse-Authorization-Id": "TEST-BOUND-AUTH",
            "X-StegVerse-Payload-SHA256": ingress.hashlib.sha256(raw).hexdigest(),
            "Content-Type": "application/json",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(ingress, "_dispatch_sv002_consumer") as dispatch:
            dispatch.return_value = {"consumer_dispatch_attempted": True, "authority_effect": "NONE_DISPATCH_ONLY"}
            receipt = ingress.admit_sv002(runtime_root=Path(tmp), body=raw, headers=headers)
            self.assertEqual(receipt["schema"], ingress.SV002_RECEIPT_SCHEMA)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertFalse(receipt["g18_required"])
            self.assertFalse(receipt["observer_direct_relation_to_stegverse_002"])
            self.assertFalse(receipt["round_trip_claimed"])
            self.assertFalse(receipt["observation_round_trip_claimed"])
            self.assertFalse(receipt["claim_or_fence_minted"])
            dispatch.assert_called_once()

    def test_superseded_script_materialization_path_absent(self):
        self.assertFalse((ROOT / "scripts/consume_sv002_intr_materialization_request.py").exists())
        self.assertFalse((ROOT / "scripts/serve_sv002_intr_materialization_ingress.py").exists())
        bootstrap=(ROOT / "scripts/bootstrap_sovereign_runtime.py").read_text(encoding="utf-8")
        refresh=(ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        installer=(ROOT / "scripts/install_sovereign_worker_source_refresh_service.py").read_text(encoding="utf-8")
        for text in (bootstrap,refresh,installer):
            self.assertNotIn("consume_sv002_intr_materialization_request.py",text)
            self.assertNotIn("serve_sv002_intr_materialization_ingress.py",text)
        self.assertNotIn("sv002-intr-materialization",installer)


if __name__ == "__main__":
    unittest.main()
