from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import observe_gadi_current_iphone_discovery_receipt as module

NODE = "SV-NODE-0123456789abcdef01234567"


class GADICurrentIphoneDiscoveryReceiptTests(unittest.TestCase):
    def wrapper(self, *, state: str = "EVIDENCE_AVAILABLE") -> dict:
        evidence = {
            "schema": module.retained_projector.SOURCE_SCHEMA,
            "state": "LOCAL_DISCOVERY_OBSERVED",
            "task_id": module.retained_projector.SOURCE_TASK_ID,
            "cosv": module.retained_projector.SOURCE_COSV,
            "execution_surface": "CURRENT_USER_IPHONE",
            "node_ref": NODE,
            "node_origin": "STEGBROWSER_RESIDENT",
            "heartbeat_grants_authority": False,
            "endpoint": "http://127.0.0.1:8000",
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_COMPONENT_EVIDENCE_ONLY",
            "intr_admission_observed": False,
            "workercoordinator_claim_observed": False,
            "canonical_request_consumption_observed": False,
            "discovery": {
                "schema": module.retained_projector.DISCOVERY_SCHEMA,
                "state": "AVAILABLE",
                "target_node_ref": NODE,
                "gateway_execution_authority": "NONE",
                "credential_authority": "TV/TVC",
                "discovery_grants_authority": False,
                "authority_effect": "NONE_DISCOVERY_ONLY",
            },
            "source_device_hb_reference": "HB32",
            "current_observed_hb_reference": "HB32",
        }
        body_digest = module.retained_projector._sha_uri(evidence)
        evidence["receipt_sha256"] = body_digest
        evidence["retained_node_state_generation"] = 1
        evidence["retained_node_state_commitment"] = "a" * 64
        evidence["retained_node_transition_sequence"] = 1
        evidence["retained_node_transition_commitment"] = "b" * 64
        evidence["retained_node_lineage_bound"] = True
        evidence["envelope_sha256"] = module.retained_projector._sha_uri(evidence)
        return {
            "schema": module.FETCH_SCHEMA,
            "state": state,
            "target_node_ref": NODE,
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "evidence_grants_authority": False,
            "authority_effect": "NONE_EVIDENCE_READ_ONLY",
            "evidence": evidence if state == "EVIDENCE_AVAILABLE" else None,
        }

    def test_wrapper_reuses_canonical_retained_node_projector(self) -> None:
        with patch.object(module.retained_projector, "project", wraps=module.retained_projector.project) as project:
            value = module._validate_wrapper(self.wrapper(), NODE)
        self.assertEqual(value["state"], "EVIDENCE_AVAILABLE")
        self.assertEqual(value["_projected"]["node_ref"], NODE)
        project.assert_called_once()

    def test_wrapper_rejects_authority_drift(self) -> None:
        value = self.wrapper()
        value["evidence_grants_authority"] = True
        with self.assertRaisesRegex(ValueError, "may not grant authority"):
            module._validate_wrapper(value, NODE)

    def test_no_evidence_is_valid_observation_but_not_success(self) -> None:
        value = module._validate_wrapper(self.wrapper(state="NO_EVIDENCE"), NODE)
        self.assertEqual(value["state"], "NO_EVIDENCE")
        self.assertIsNone(value["evidence"])

    def test_observe_writes_read_only_current_receipt_readback(self) -> None:
        projected = module.retained_projector.project(self.wrapper()["evidence"])
        wrapper = self.wrapper()
        wrapper["_projected"] = projected
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            with patch.object(module, "_probe", return_value=("REACHABLE", b"exact", wrapper)) as probe:
                result = module.observe(runtime, NODE)
            self.assertEqual(result["state"], "CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED")
            self.assertEqual(result["target_node_ref"], NODE)
            self.assertEqual(result["authority_effect"], "NONE_EVIDENCE_READ_ONLY")
            self.assertFalse(result["execution_authority_granted"])
            self.assertFalse(result["hosted_fallback_used"])
            self.assertEqual(probe.call_args.args[:2], ("http://127.0.0.1:8000", NODE))
            self.assertTrue((runtime / module.OUTPUT_REL).is_file())

    def test_unreachable_or_no_evidence_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            with patch.object(module, "_probe", return_value=("UNAVAILABLE", None, None)):
                result = module.observe(runtime, NODE)
            self.assertEqual(result["state"], "CURRENT_IPHONE_RECEIPT_READBACK_UNOBSERVED_FAIL_CLOSED")
            self.assertFalse(result["execution_authority_granted"])

    def test_observer_has_only_local_get_evidence_surface(self) -> None:
        text = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("https://", text)
        self.assertIn('Request(url, method="GET"', text)
        self.assertNotIn('method="POST"', text)
        self.assertIn("NONE_EVIDENCE_READ_ONLY", text)
        self.assertIn("materialize_gadi_retained_node_discovery", text)


if __name__ == "__main__":
    unittest.main()
