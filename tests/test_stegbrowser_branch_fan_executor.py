"""StegBrowser's fan execution has moved out of this worker.

This file used to assert that this worker executed the fan: translating a v2
journey into one v1 round trip per branch, minting each branch's ephemeral
lease, and calling the StegBrowser owner. None of that is authority -- it is
translation, lease data and orchestration -- so it moved to where the capability
is offered, stegverse.governed_llm_fan.

The branch requests the SDK produces were verified byte-identical to the ones
this worker produced, and that agreement is frozen as an SDK fixture captured
from this worker before it was removed, so a packet replays the same either way.

What this file asserts now is the other half of that move: the capability is
genuinely gone from here, and a manifest naming it is not silently unhandled.

Non-authorizing: source and disposition validation only. No browser runs, no
receipt is minted, no transition is admitted.
"""
import tempfile
import unittest
from pathlib import Path

from workers import manifest_state_transition_intr_ingress as mod

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/manifest_state_transition_intr_ingress.py"

SDK_OWNER = "stegverse.governed_llm_fan.run_governed_llm_fan"

REQUEST = {
    "processing_capability": "stegbrowser",
    "route_id": "stegverse.route.stegbrowser.v1",
    "state_graph": {"profile": "llm.v1"},
    "graph_id": "stegbrowser:test5-a",
    "canonical_task_id": "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001",
    "wire_manifest_sha256": "0" * 64,
    "canonical_manifest_sha256": "1" * 64,
    "request_sha256": "3" * 64,
}


class StegBrowserFanExecutionRelocated(unittest.TestCase):
    def setUp(self):
        self.source = WORKER.read_text(encoding="utf-8")

    # --- the execution is actually gone, not merely unreferenced -------------

    def test_the_worker_no_longer_calls_the_browser_owner(self):
        self.assertNotIn("execute_manifested_llm_browser_operation", self.source)
        self.assertNotIn("src.stegbrowser", self.source)

    def test_the_fan_translation_and_lease_minting_are_gone(self):
        for name in ("_execute_stegbrowser_llm", "_branch_operations",
                     "_stegbrowser_failure"):
            self.assertFalse(hasattr(mod, name), name)
        self.assertNotIn("ecosystem-ephemeral-lease", self.source)

    def test_no_capability_branch_dispatches_stegbrowser_here(self):
        self.assertNotIn('capability == "stegbrowser"', self.source)

    # --- and the manifest that names it is not silently unhandled -----------

    def test_a_stegbrowser_manifest_fails_closed_naming_the_new_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            result = mod._capability_dispatch_fail_closed(Path(directory), REQUEST)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(
            result["failed_predicate"],
            "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND")
        self.assertEqual(result["relocated_owner"], SDK_OWNER)
        self.assertIs(result["owner_relocated_out_of_this_worker"], True)

    def test_the_disposition_claims_no_closure_it_did_not_observe(self):
        """Fail-closed here is this profile's verdict, not a runtime claim."""
        with tempfile.TemporaryDirectory() as directory:
            result = mod._capability_dispatch_fail_closed(Path(directory), REQUEST)
        self.assertIs(result["organization_master_records_closure_observed"], False)
        self.assertIs(result["automatic_retry_permitted"], False)
        self.assertEqual(result["transition_id"], "INGRESS_ADMITTED")

    def test_the_relocation_map_names_a_real_sdk_entry_point(self):
        """A pointer nobody can follow is worse than no pointer."""
        self.assertEqual(mod.RELOCATED_CAPABILITY_OWNERS["stegbrowser"], SDK_OWNER)
        module, _, function = SDK_OWNER.rpartition(".")
        self.assertEqual(module, "stegverse.governed_llm_fan")
        self.assertEqual(function, "run_governed_llm_fan")

    def test_a_capability_with_no_owner_anywhere_still_fails_closed(self):
        """Relocation is an explanation, never a requirement for failing closed."""
        unknown = dict(REQUEST, processing_capability="not_a_capability")
        with tempfile.TemporaryDirectory() as directory:
            result = mod._capability_dispatch_fail_closed(Path(directory), unknown)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertIsNone(result["relocated_owner"])
        self.assertIs(result["owner_relocated_out_of_this_worker"], False)


if __name__ == "__main__":
    unittest.main()
