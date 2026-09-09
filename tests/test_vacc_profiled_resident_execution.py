from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/vacc_profiled_resident_execution.py"


def load_worker():
    spec = importlib.util.spec_from_file_location("vacc_profiled_resident_execution", WORKER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class VaccProfiledResidentExecutionTests(unittest.TestCase):
    def test_verified_response_requires_same_execution_custody_and_exact_hash(self):
        m = load_worker()
        response = {
            "schema":"stegverse.va_claims.runtime/v1",
            "response":"A grounded answer.",
            "session_id":"vacc-profiled-runtime-proof",
            "route":"service_connection",
            "citations":[],
            "answer_receipt_hash":"a",
            "execution_receipt_hash":"b",
            "reconstruction_receipt_hash":"c",
            "provider_usage_custody_recorded":True,
            "provider_usage_reconstruction_pass":True,
            "transition_reconstruction_pass":True,
            "same_execution":True,
            "authority_effect":False,
            "activation_effect":False,
            "filing_active":False,
            "private_document_context_used":False,
            "github_token_required":False,
            "credential_requirement":"NONE",
            "reference_model_fallback_renderer_used":False,
        }
        response["response_hash"] = m.stable_hash(response)
        self.assertTrue(m.response_verified(response))
        response["same_execution"] = False
        self.assertFalse(m.response_verified(response))

    def test_live_runtime_executes_exact_vacc_bound_probe_and_retains_receipt(self):
        m = load_worker()
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            state_path = runtime / "receipts/ecosystem-chat-sovereign-inference/va_conversational_runtime_process.json"
            state_path.parent.mkdir(parents=True)
            state = {
                "schema":"stegverse.va-conversational-runtime-process/v1",
                "state":"LIVE_VERIFIED",
                "credential_authority":"TV/TVC",
                "credential_requirement":"NONE",
                "github_token_required":False,
                "endpoint":"http://127.0.0.1:54321",
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")
            response = {
                "schema":"stegverse.va_claims.runtime/v1",
                "response":"A grounded answer.",
                "session_id":"vacc-profiled-runtime-proof",
                "route":"service_connection",
                "citations":[],
                "answer_receipt_hash":"a",
                "execution_receipt_hash":"b",
                "reconstruction_receipt_hash":"c",
                "provider_usage_custody_recorded":True,
                "provider_usage_reconstruction_pass":True,
                "transition_reconstruction_pass":True,
                "same_execution":True,
                "authority_effect":False,
                "activation_effect":False,
                "filing_active":False,
                "private_document_context_used":False,
                "github_token_required":False,
                "credential_requirement":"NONE",
                "reference_model_fallback_renderer_used":False,
            }
            response["response_hash"] = m.stable_hash(response)
            with mock.patch.object(m, "require_resident_env"), mock.patch.object(m, "post_probe", return_value=response):
                result = m.execute(ROOT, runtime)
            self.assertEqual("VACC_PROFILED_RESIDENT_REQUEST_EXECUTED", result["state"])
            self.assertEqual(m.TASK_ID, result["task_id"])
            self.assertEqual(m.PROFILE_ID, result["runtime_node_profile_id"])
            self.assertTrue(result["same_execution"])
            self.assertTrue((runtime / m.OUTPUT_REL).is_file())

    def test_missing_runtime_advances_existing_ecosystem_parent_instead_of_creating_second_path(self):
        m = load_worker()
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            with mock.patch.object(m, "require_resident_env"), mock.patch.object(m, "advance_parent_runtime", return_value={"state":"PARENT_RUNTIME_VISITED"}) as advance:
                result = m.execute(ROOT, runtime)
            self.assertEqual("VACC_PROFILED_PARENT_RUNTIME_PENDING", result["state"])
            advance.assert_called_once()
            self.assertFalse(result["github_token_required"])


if __name__ == "__main__":
    unittest.main()
