#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_stegbrowser_runtime_consumption_receipts.py"
TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
TVC_SHA = "aef6b6f5dc99d2a531718ca475d20858ae8e68a6"

spec = importlib.util.spec_from_file_location("receipt_check", SCRIPT)
receipt_check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(receipt_check)


def write_json(root: Path, rel: str, value: dict) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


class StegBrowserRuntimeReceiptReachabilityTests(unittest.TestCase):
    def test_missing_receipts_are_not_bindable_and_do_not_authorize(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = receipt_check.inspect(Path(tmp))
        self.assertEqual(result["state"], "RUNTIME_RECEIPTS_NOT_BINDABLE")
        self.assertFalse(result["completion_evidence_observed"])
        self.assertEqual(
            set(result["missing_receipts"]),
            {"canonical_work_consumption", "evidence_custody", "tvc_source_promotion", "owner_ingress"},
        )
        self.assertFalse(result["claim_or_fence_minted"])
        self.assertFalse(result["scheduler_invoked"])
        self.assertFalse(result["runtime_request_consumed"])
        self.assertEqual(result["github_token_runtime_authority"], "NONE")
        self.assertEqual(result["authority_effect"], "NONE_RECEIPT_REACHABILITY_INSPECTION_ONLY")

    def test_valid_receipts_are_bindable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                "receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json",
                {
                    "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
                    "state": "COMPLETED",
                    "task_id": TASK_ID,
                    "credential_material_present": False,
                    "github_token_runtime_authority": "NONE",
                    "second_machine_required": False,
                },
            )
            write_json(
                root,
                "receipts/sovereign-host/stegbrowser-runtime-consumption-evidence-custody.latest.json",
                {
                    "schema": "stegverse.stegbrowser-runtime-consumption-evidence-custody/v1",
                    "state": "EXACT_EPHEMERAL_EVIDENCE_RETAINED_IN_EXISTING_RESIDENT_RUNTIME",
                    "task_id": TASK_ID,
                    "cosv_task_vector": COSV,
                    "evidence": [{"exact_bytes_retained": True, "sha256": "abc"}],
                    "credential_material_present": False,
                    "github_token_runtime_authority": "NONE",
                },
            )
            write_json(
                root,
                "receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json",
                {
                    "state": "ATTEMPT_RECORDED",
                    "outcome": "STAGED",
                    "exact_sha": TVC_SHA,
                    "credential_material_present": False,
                    "network_source_fetch_performed": False,
                },
            )
            write_json(
                root,
                "var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json",
                {"state": "OWNER_INGRESS_READY_OBSERVED", "simultaneous_listener_observation": True},
            )
            result = receipt_check.inspect(root)
        self.assertEqual(result["state"], "RUNTIME_RECEIPTS_VALID_AND_BINDABLE")
        self.assertTrue(result["completion_evidence_observed"])
        self.assertEqual(result["missing_receipts"], [])
        self.assertEqual(result["invalid_receipts"], [])

    def test_invalid_tvc_receipt_blocks_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                "receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json",
                {
                    "state": "ATTEMPT_RECORDED",
                    "outcome": "STAGED",
                    "exact_sha": "wrong",
                    "credential_material_present": False,
                    "network_source_fetch_performed": False,
                },
            )
            result = receipt_check.inspect(root)
        self.assertEqual(result["state"], "RUNTIME_RECEIPTS_NOT_BINDABLE")
        self.assertIn("tvc_source_promotion", result["invalid_receipts"])
        self.assertEqual(result["checks"]["tvc_source_promotion"]["reason"], "TVC_SHA_MISMATCH")


if __name__ == "__main__":
    unittest.main()
