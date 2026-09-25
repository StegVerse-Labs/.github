"""Source-only reconciliation guard for existing ephemeral external AI and org-first custody."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001"


def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


class ExternalAIOrgFirstTests(unittest.TestCase):
    def test_task_matches_registry_without_altering_cosv(self):
        record = read("data/canonical-task-records/"+TASK+".json")
        registry = read("data/canonical-task-registry.json")
        found = [x for x in registry["tasks"] if x["task_id"] == TASK]
        self.assertEqual(found, [record])
        self.assertEqual(record["coordination_state"], "PROPOSED")
        self.assertEqual(len(record["blockers"]), 3)
        self.assertIsNone(record["worker_claim"]["claim_ref"])
        vec = read("control/task-vectors/"+TASK+".json")
        self.assertEqual(vec["vector"], "10100000103000")
        self.assertEqual(vec["exact_metrics"]["blocker_count"], len(record["blockers"]))

    def test_org_first_replay_and_independent_master_records_scope(self):
        p = read("data/ephemeral-external-ai-reusable-component-profile.v1.json")
        org = read("control/organization-batch-custody-replay-contract.json")
        self.assertTrue(p["org_receipt_first"]["local_replay_must_work_without_master_records_online"])
        self.assertIn("ORGANIZATION_SEQUENCE", org["org_replay_scope"])
        self.assertIn("CROSS_ORGANIZATION", org["master_records_replay_scope"])
        self.assertEqual(p["master_records_custody"]["existing_owner"], org["task_id"])
        self.assertEqual(p["master_records_custody"]["normal_mode"], "BOUNDED_CONTIGUOUS_ORGANIZATION_BATCH_AFTER_LOCAL_ORG_RECEIPT_SEQUENCE")
        self.assertEqual(p["master_records_custody"]["direct_exception"], "EXPLICIT_TRANSITION_CONTRACT_REQUIRES_IMMEDIATE_MASTER_RECORDS_ACK")
        self.assertIn("MASTER_RECORDS_NOT_TRANSITION_AUTHORITY", p["master_records_custody"]["nonclaims"])

    def test_a3_is_not_generic_external_provider_start_gate(self):
        p = read("data/ephemeral-external-ai-reusable-component-profile.v1.json")
        self.assertEqual(p["execution_path_selection"]["first"], "RECONCILE_CURRENT_ORG_LEVEL_RECEIPTS_AND_EXISTING_STEGBROWSER_CAPABILITY")
        self.assertEqual(p["execution_path_selection"]["historical_a3_invocation"], "SOURCE_REFRESH_REQUIRED_ONLY_IF_EXACT_SELECTED_EXISTING_INVOCATION_CONTRACT_REQUIRES_IT")
        self.assertFalse(p["execution_path_selection"]["requires_new_runtime"])
        self.assertFalse(p["execution_path_selection"]["requires_second_user_device"])
        self.assertFalse(p["execution_path_selection"]["native_mykv_prerequisite_for_nonprivate_input"])
        record = read("data/canonical-task-records/"+TASK+".json")
        self.assertIn("NOT a universal", record["blockers"][0]["reason"])

    def test_provider_specific_adapter_terminates_before_browser_teardown(self):
        p = read("data/ephemeral-external-ai-reusable-component-profile.v1.json")
        b = p["boundary"]
        self.assertIn("provider_specific_payload_projection", b["llm_adapter_owns"])
        self.assertIn("terminal_session_destruction", b["stegbrowser_owns"])
        self.assertEqual(b["api_adapter_handoff"], "STEGBROWSER_TO_LLM_ADAPTER_ON_BOUND_PROVIDER_REQUEST_AND_AUTHENTIC_INGRESS_ALLOW")
        self.assertEqual(b["adapter_selection"], "ONLY_WHEN_MANIFEST_SELECTED_OPERATION_REQUIRES_PROVIDER_TRANSLATION")
        self.assertFalse(b["web_ui_login_equivalent_to_approved_api_provider_call"])
        self.assertEqual({x["provider"] for x in p["providers"]}, {"openai", "anthropic"})
        claude = next(x for x in p["providers"] if x["provider"] == "anthropic")
        self.assertTrue(claude["claude_code_tool_execution_extra_proof_required"])

    def test_unauthorized_promotion_prohibited(self):
        p = read("data/ephemeral-external-ai-reusable-component-profile.v1.json")
        r = p["release_criteria"]
        self.assertEqual(r["live_openai"], "UNVERIFIED")
        self.assertEqual(r["live_anthropic"], "UNVERIFIED")
        self.assertEqual(r["governed_site_publication"], "NOT_AUTHORIZED")
        self.assertEqual(p["authority_effect"], "NONE_SOURCE_CONTRACT_ONLY")


if __name__ == "__main__":
    unittest.main()
