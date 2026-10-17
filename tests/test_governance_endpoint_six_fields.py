"""H34 (GOVERNANCE_DECISION_RECORD_LACKS_SIX_FIELDS): a non-ALLOW governance decision
carries the six actionable fields of the Organization Role conformance standard
(item 5), at the decision and in the organization receipt, and a supplied heartbeat
epoch reaches both ledger receipts instead of being derived from the host clock.

Reuses the harness of tests/test_governance_endpoint.py (StegCore stub, ledger roots
redirected per test). No new dependency.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "governance_endpoint_harness", Path(__file__).with_name("test_governance_endpoint.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
MATRIX_STUB = base.STUB.replace(
    '''return {"disposition": "DENY", "canonical_three_layer_reason": "signal.inputs_incomplete",
                "request": self.fields}''',
    '''return {"disposition": "DENY", "canonical_three_layer_reason": "signal.inputs_incomplete",
                "matrix": [
                    {"predicate": "signal.present", "state": "PASS", "reason": "ok", "authority_surface": "signal"},
                    {"predicate": "execution.actor_authority_current", "state": "UNKNOWN",
                     "reason": "actor authority not established", "authority_surface": "execution"},
                    {"predicate": "signal.missing_inputs", "state": "FAIL",
                     "reason": "missing authenticated_current_grant", "authority_surface": "signal"}],
                "request": self.fields}''')
ALLOW_STUB = base.STUB.replace('"disposition": "DENY"', '"disposition": "ALLOW"')


class GovernanceSixFieldTests(unittest.TestCase):
    # The base suite's fixtures only; its tests are not re-run here.
    VARIABLES = base.GovernanceEndpointTests.VARIABLES
    setUp = base.GovernanceEndpointTests.setUp
    with_stegcore = base.GovernanceEndpointTests.with_stegcore
    without_stegcore = base.GovernanceEndpointTests.without_stegcore
    ledger = base.GovernanceEndpointTests.ledger

    def use_stub(self, text):
        (Path(self.stub_path) / "stegcore" / "steggate.py").write_text(text)
        self.with_stegcore()

    def assert_six(self, record):
        for key in SIX:
            self.assertIsInstance(record.get(key), str, key)
            self.assertTrue(record[key].strip(), key)

    def test_a_deny_carries_the_six_fields_naming_the_failed_matrix_predicate(self):
        self.use_stub(MATRIX_STUB)
        decision = base.K.dispatch(base.ROOT, base.packet(base.work_request({"signal": {}})), heartbeat_reference=base.CARRIER)["application_result"]
        self.assertEqual(decision["disposition"], "DENY")
        self.assert_six(decision)
        self.assertEqual(decision["failure_code"], "signal.inputs_incomplete")
        self.assertEqual(decision["failed_predicate"], "signal.missing_inputs")  # FAIL outranks UNKNOWN
        self.assertIn("missing authenticated_current_grant", decision["required_evidence_or_repair"])
        self.assertEqual(decision["unsatisfied_predicates"],
                         ["signal.missing_inputs", "execution.actor_authority_current"])
        self.assertEqual(decision["owning_existing_goal"], "UNDECLARED_BY_REQUEST")
        self.assertIn("organization-governance-decision.yml", decision["retry_entrypoint"])

    def test_the_organization_receipt_carries_the_six_fields(self):
        self.use_stub(MATRIX_STUB)
        base.K.dispatch(base.ROOT, base.packet(base.work_request({"signal": {}})), heartbeat_reference=base.CARRIER)
        organization = self.ledger("STEGVERSE_ORG_LEDGER_ROOT")
        self.assertEqual(len(organization), 1)
        self.assert_six(organization[0]["boundary_evidence"])
        self.assertEqual(organization[0]["boundary_evidence"]["disposition"], "DENY")

    def test_fail_closed_paths_carry_the_six_fields(self):
        self.without_stegcore()
        decision = base.K.dispatch(base.ROOT, base.packet(base.work_request({"signal": {}})), heartbeat_reference=base.CARRIER)["application_result"]
        self.assertEqual(decision["disposition"], "FAIL_CLOSED")
        self.assert_six(decision)
        self.assertEqual(decision["failure_code"], "GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE")
        self.assertEqual(decision["failed_predicate"], "GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE")
        self.with_stegcore()
        mismatch = base.K.dispatch(base.ROOT, base.packet(base.work_request({"signal": {"x": 1}}, digest="0" * 64)), heartbeat_reference=base.CARRIER)["application_result"]
        self.assert_six(mismatch)
        self.assertEqual(mismatch["failure_code"], "GOVERNANCE_REQUEST_DIGEST_MISMATCH")

    def test_a_declared_owning_goal_is_carried_not_invented(self):
        self.use_stub(MATRIX_STUB)
        payload = base.work_request({"signal": {}})
        payload["body"]["owning_existing_goal"] = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"
        decision = base.K.dispatch(base.ROOT, base.packet(payload), heartbeat_reference=base.CARRIER)["application_result"]
        self.assertEqual(decision["owning_existing_goal"], "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001")

    def test_an_allow_carries_no_failure_fields(self):
        self.use_stub(ALLOW_STUB)
        decision = base.K.dispatch(base.ROOT, base.packet(base.work_request({"signal": {}})), heartbeat_reference=base.CARRIER)["application_result"]
        self.assertEqual(decision["disposition"], "ALLOW")
        for key in SIX + ("unsatisfied_predicates",):
            self.assertNotIn(key, decision)
        self.assertEqual(decision["authority_effect"], "NONE_DECISION_ONLY")

    def run_adapter(self, *extra):
        envelope = self.work / "packet.json"
        envelope.write_text(json.dumps(base.packet(base.work_request({"signal": {}}))))
        out = self.work / "out.json"
        completed = subprocess.run([sys.executable, str(base.ROOT / "resident-runtime/governance_endpoint.py"),
                                    "--packet", str(envelope), "--out", str(out), *extra],
                                   cwd=base.ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(out.read_text())

    def test_a_supplied_hb_epoch_reaches_both_receipts(self):
        self.use_stub(MATRIX_STUB)
        self.run_adapter("--hb-epoch", "1000")
        repository = self.ledger("STEGVERSE_REPO_LEDGER_ROOT")
        organization = self.ledger("STEGVERSE_ORG_LEDGER_ROOT")
        self.assertEqual(repository[0]["hb_reference"]["epoch"], 1000)
        self.assertIs(repository[0]["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(organization[0]["hb_reference"]["epoch"], 1000)
        self.assertIs(organization[0]["hb_reference"]["derived_from_clock"], False)

    def test_without_hb_epoch_the_receipts_say_the_reference_was_derived(self):
        self.use_stub(MATRIX_STUB)
        self.run_adapter()
        repository = self.ledger("STEGVERSE_REPO_LEDGER_ROOT")
        self.assertIs(repository[0]["hb_reference"]["derived_from_clock"], True)


if __name__ == "__main__":
    unittest.main()
