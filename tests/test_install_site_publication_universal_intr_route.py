from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INSTALL_SPEC = importlib.util.spec_from_file_location(
    "install_site_publication_universal_intr_route",
    ROOT / "scripts" / "install_site_publication_universal_intr_route.py",
)
installer = importlib.util.module_from_spec(INSTALL_SPEC)
assert INSTALL_SPEC and INSTALL_SPEC.loader
INSTALL_SPEC.loader.exec_module(installer)

INGRESS_SPEC = importlib.util.spec_from_file_location(
    "site_publication_intr_ingress",
    ROOT / "workers" / "site_publication_intr_ingress.py",
)
ingress = importlib.util.module_from_spec(INGRESS_SPEC)
assert INGRESS_SPEC and INGRESS_SPEC.loader
INGRESS_SPEC.loader.exec_module(ingress)


def request() -> dict:
    body = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "materialization_id": "INTR-MAT-" + "a" * 24,
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": "SITE_PUBLICATION_EVENT",
        "packet_id": "INTR-" + "b" * 24,
        "payload_hash": "sha256:" + "2" * 64,
        "payload_ref": "artifact://site-publication-manifest/" + "2" * 64,
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegOS:SitePublicationRuntime"},
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": "StegVerse-Labs/StegOS:canonical-runtime-lane",
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
    body["request_hash"] = ingress.sha_uri(body)
    return body


class SitePublicationRouteTests(unittest.TestCase):
    def test_transform_is_fail_closed_and_idempotent(self) -> None:
        source = (ROOT / "workers" / "universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
        transformed = installer.transform(source)
        self.assertIn("site_publication_intr_ingress", transformed)
        self.assertIn('"StegOS:SitePublicationRuntime"', transformed)
        self.assertIn("site_publication.admit(", transformed)
        self.assertEqual(installer.transform(transformed), transformed)

    def test_candidate_ingress_does_not_claim_runtime(self) -> None:
        req = request()
        with tempfile.TemporaryDirectory() as tmp:
            receipt = ingress.admit(runtime_root=Path(tmp), payload=req, transport_payload_sha256="3" * 64)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED_CANDIDATE_ONLY")
            self.assertFalse(receipt["runtime_materialization_attempted"])
            self.assertFalse(receipt["runtime_execution_observed"])
            self.assertFalse(receipt["public_https_profile_observed"])
            self.assertFalse(receipt["final_publication_transition_admitted"])
            self.assertFalse(receipt["render_allowed"])
            stored = json.loads((Path(tmp) / "intr-materialization" / f"{req['materialization_id']}.json").read_text())
            self.assertEqual(stored["request_hash"], req["request_hash"])

    def test_wrong_destination_fails(self) -> None:
        req = request()
        req["destination"] = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "HIL:Ingress"}
        req["request_hash"] = ingress.sha_uri({k: v for k, v in req.items() if k != "request_hash"})
        with self.assertRaisesRegex(ValueError, "site_publication_destination_mismatch"):
            ingress.validate_request(req)


if __name__ == "__main__":
    unittest.main()
