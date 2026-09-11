from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("stegsocials_intr_builder", "scripts/build_stegsocials_bounded_intr_materialization.py")
ingress = load("stegsocials_intr_ingress", "workers/stegsocials_bounded_intr_ingress.py")
installer = load("stegsocials_intr_installer", "scripts/install_stegsocials_bounded_universal_intr_route.py")
canonical_installer = load("canonical_work_installer", "scripts/install_canonical_work_universal_intr_route.py")


def received() -> dict:
    intent = {
        "schema": "stegsocials.bounded-group-intr-execution-intent.v1",
        "stable_work_id": "SS-KV-SKAP-SOCIAL-RELEASE-001:group-001:use:1",
        "correlation_id": "SS-KV-SKAP-SOCIAL-RELEASE-001:group-001",
        "task_id": "SS-KV-SKAP-SOCIAL-RELEASE-001",
        "group_id": "group-001",
        "use_index": 1,
        "content_ref": "kv://02_Research/StegSocials/Drafts/LinkedIn/post-001.json",
        "content_hash": "sha256:" + "a" * 64,
        "platform": "linkedin",
        "account_ref": "linkedin://company/stegverse",
        "state_ref": "kv://03_Records/StegSocials/PostGroupState/group-001.json",
        "participant_approval_receipt_ref": "stegid://receipts/group-001",
        "credential_ref": "skap://social/linkedin/stegverse",
        "dependencies": ["Personal-KV", "TV/TVC", "StegBrowser"],
        "duplicate_convergence_key": "stegsocials:group-001:use:1",
        "requested_transition": "INGRESS_ADMITTED",
        "intr_admission_receipt_ref": None,
        "tv_tvc_skap_session_receipt_ref": None,
        "request_grants_execution_authority": False,
        "provider_operation_authorized": False,
        "secret_material_present": False,
        "raw_credential_material": None,
    }
    return {
        "schema": "stegverse.universal-work-interlock/v1",
        "work_id": intent["stable_work_id"],
        "correlation_id": intent["correlation_id"],
        "direction": "INGRESS",
        "state": "RECEIVED",
        "source": {"type": "RUNTIME_EVENT", "identity": intent["task_id"], "evidence_refs": [intent["participant_approval_receipt_ref"], intent["state_ref"], intent["content_ref"]]},
        "goal": "Admit one participant-authorized bounded StegSocials use for event-ephemeral governed execution without widening authority.",
        "organization": "StegVerse-Labs",
        "repository": "StegVerse-Labs/StegSocials",
        "component": "bounded-group-social-publication",
        "dependencies": list(intent["dependencies"]),
        "blockers": [],
        "convergence_refs": [intent["duplicate_convergence_key"]],
        "result_refs": [],
        "next_owner": "INTERLOCK_INTR",
        "human_action_required": False,
        "authority": {
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "heartbeat_granted_authority": False,
            "authority_effect": "NONE_RECEIVED_INGRESS_RECORD_ONLY",
            "interlock_self_grants_authority": False,
            "intr_self_grants_authority": False,
        },
        "recorded_at": datetime(2026, 9, 11, 4, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "bounded_social_intent": intent,
        "admission_receipt_ref": None,
        "runtime_admission_observed": False,
    }


class StegSocialsBoundedInTrAdmissionRouteTests(unittest.TestCase):
    def test_builder_binds_received_record_into_existing_universal_intr_shape(self) -> None:
        payload, request = builder.build(received())
        self.assertEqual(request["schema"], "stegverse.universal-intr-materialization-request/v1")
        self.assertEqual(request["destination"], {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegSocials:BoundedSocialIngress"})
        self.assertEqual(request["downstream_owner_ref"], "SS-KV-SKAP-SOCIAL-RELEASE-001")
        self.assertEqual(request["operation_id"], "BOUNDED_SOCIAL_INTR_INGRESS")
        self.assertFalse(request["request_grants_execution_authority"])
        self.assertFalse(request["transport_grants_execution_authority"])
        self.assertFalse(request["authority_transfer"])
        self.assertEqual(payload["group_id"], "group-001")
        self.assertEqual(payload["use_index"], 1)
        self.assertFalse(payload["runtime_admission_observed"])
        self.assertIsNone(payload["admission_receipt_ref"])
        ingress.validate_request(request)
        ingress.validate_payload(payload, request)

    def test_ingress_emits_admitted_receipt_only_after_exact_runtime_payload_validation(self) -> None:
        payload, request = builder.build(received())
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            payload_path = runtime / "intr-payloads/stegsocials-bounded-social" / f"{request['materialization_id']}.json"
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raw = json.dumps(request, sort_keys=True).encode("utf-8")

            def transport_validator(_headers, _body):
                return {"origin": "SOVEREIGN_NODE", "authorization_id": None, "payload_sha256": "f" * 64}

            receipt = ingress.admit(runtime_root=runtime, body=raw, headers={}, transport_validator=transport_validator)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["group_id"], "group-001")
            self.assertEqual(receipt["use_index"], 1)
            self.assertEqual(receipt["work_id"], received()["work_id"])
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["provider_operation_authorized"])
            self.assertFalse(receipt["admission_grants_publication_authority"])
            self.assertEqual(receipt["next_owner"], "TV/TVC_SKAP_SESSION_MATERIALIZATION")
            persisted = runtime / "receipts/sovereign-network/stegsocials-bounded-intr-ingress" / f"{request['materialization_id']}.json"
            self.assertTrue(persisted.is_file())
            repeated = ingress.admit(runtime_root=runtime, body=raw, headers={}, transport_validator=transport_validator)
            self.assertEqual(repeated["receipt_hash"], receipt["receipt_hash"])

    def test_builder_refuses_synthetic_admission_and_secret_drift(self) -> None:
        bad = received()
        bad["runtime_admission_observed"] = True
        with self.assertRaisesRegex(ValueError, "received_runtime_admission_observed_mismatch"):
            builder.build(bad)
        bad = received()
        bad["bounded_social_intent"]["secret_material_present"] = True
        with self.assertRaisesRegex(ValueError, "received_secret_material_forbidden"):
            builder.build(bad)

    def test_ingress_refuses_payload_hash_or_binding_drift(self) -> None:
        payload, request = builder.build(received())
        bad = dict(payload)
        bad["group_id"] = "group-other"
        with self.assertRaisesRegex(ValueError, "payload_hash_mismatch|group_use_binding_mismatch"):
            ingress.validate_payload(bad, request)
        bad_request = dict(request)
        bad_request["request_grants_execution_authority"] = True
        with self.assertRaisesRegex(ValueError, "stegsocials_request_grants_execution_authority_mismatch"):
            ingress.validate_request(bad_request)

    def test_route_installer_is_idempotent_and_composes_with_canonical_work(self) -> None:
        base = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
        installed = installer.transform(base)
        self.assertIn("StegSocials:BoundedSocialIngress", installed)
        self.assertIn("is_stegsocials_bounded(payload)", installed)
        self.assertEqual(installer.transform(installed), installed)
        self.assertEqual(installed.count("ThreadingHTTPServer"), base.count("ThreadingHTTPServer"))

        canonical_first = canonical_installer.transform(base)
        both = installer.transform(canonical_first)
        self.assertIn("CanonicalWork:Coordination", both)
        self.assertIn("StegSocials:BoundedSocialIngress", both)
        self.assertIn("is_canonical_work(payload)", both)
        self.assertIn("is_stegsocials_bounded(payload)", both)

        socials_first = installer.transform(base)
        both_reverse = canonical_installer.transform(socials_first)
        self.assertIn("CanonicalWork:Coordination", both_reverse)
        self.assertIn("StegSocials:BoundedSocialIngress", both_reverse)


if __name__ == "__main__":
    unittest.main()
