from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


def _load_custody_module():
    package = types.ModuleType("heartbeat_runtime")
    package.__path__ = []
    oscillator = types.ModuleType("heartbeat_runtime.independent_oscillator")
    oscillator.current_reference = lambda now_ns: {
        "heartbeat_id": "HB-TEST",
        "epoch": 1,
        "generation": 1,
    }
    path = Path(__file__).resolve().parents[1] / "workers" / "canonical_state_transition_custody.py"
    spec = importlib.util.spec_from_file_location("canonical_state_transition_custody_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # The module under test stays registered; that shadows nothing real.
    sys.modules[spec.name] = module
    # The heartbeat_runtime stub is scoped to this exec only. Left in
    # sys.modules it shadows the real package for every test file that runs
    # after this one, failing them with "cannot import name ... from
    # heartbeat_runtime.independent_oscillator (unknown location)" -- the
    # empty __path__ showing through. The custody module binds
    # current_reference at import time, so it needs the stub only here.
    with patch.dict(sys.modules, {
        "heartbeat_runtime": package,
        "heartbeat_runtime.independent_oscillator": oscillator,
    }):
        spec.loader.exec_module(module)
    return module


custody_module = _load_custody_module()
CanonicalTransitionCustody = custody_module.CanonicalTransitionCustody


def recorded(digest: str) -> dict:
    return {
        "state": "RECORDED",
        "receipt_sha256": digest,
        "organization_receipt": {
            "schema": "stegverse.organization-transition-receipt/v1",
            "receipt_sha256": "sha256:" + digest,
        },
        "master_records_submission_performed": False,
        "master_records_role": "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY",
        "authority_effect": "NONE_ORGANIZATION_RECORDING_ONLY",
    }


class CanonicalTransitionPredecessorClosureTests(unittest.TestCase):
    def test_successor_consumes_immediately_preceding_organization_recorded_transition(self) -> None:
        custody = CanonicalTransitionCustody("subject-1")
        results = [recorded("a" * 64), recorded("b" * 64)]
        with patch(
            "canonical_state_transition_custody_under_test.submit_state_receipt",
            side_effect=results,
        ) as submit:
            first = custody.record(
                "TRANSITION-1",
                outcome="COMPLETED",
                evidence={"state": "FIRST"},
                resulting_state_ref_or_hash="sha256:" + "1" * 64,
            )
            custody.record(
                "TRANSITION-2",
                outcome="COMPLETED",
                evidence={"state": "SECOND"},
                resulting_state_ref_or_hash="sha256:" + "2" * 64,
                required_evidence_manifest=[{
                    "evidence_id": "domain-evidence",
                    "evidence_type": "DOMAIN_EVIDENCE",
                    "origin_transition_id": "TRANSITION-2",
                    "encoding": "canonical-json",
                    "sha256": "3" * 64,
                    "content": {"domain": True},
                }],
            )

        self.assertIsNone(first["receipt"]["prior_state_ref_or_hash"])
        successor = submit.call_args_list[1].args[0]
        self.assertEqual(successor["prior_state_ref_or_hash"], "sha256:" + "a" * 64)
        self.assertEqual(
            [item["evidence_type"] for item in successor["required_evidence_manifest"]],
            ["DOMAIN_EVIDENCE"],
        )
        self.assertEqual(custody.last_state_ref, "sha256:" + "b" * 64)

    def test_incomplete_organization_record_cannot_advance_successor_predecessor(self) -> None:
        custody = CanonicalTransitionCustody("subject-2")
        incomplete = {
            "state": "RECORDED",
            "receipt_sha256": "c" * 64,
            "master_records_submission_performed": False,
        }
        with patch(
            "canonical_state_transition_custody_under_test.submit_state_receipt",
            return_value=incomplete,
        ):
            with self.assertRaisesRegex(RuntimeError, "canonical_organization_record_not_returned"):
                custody.record(
                    "TRANSITION-1",
                    outcome="COMPLETED",
                    evidence={"state": "FIRST"},
                )
        self.assertIsNone(custody.last_state_ref)

    def test_resulting_domain_state_never_replaces_prior_recorded_transition_digest(self) -> None:
        custody = CanonicalTransitionCustody("subject-3")
        with patch(
            "canonical_state_transition_custody_under_test.submit_state_receipt",
            side_effect=[recorded("d" * 64), recorded("e" * 64)],
        ) as submit:
            custody.record(
                "TRANSITION-A",
                outcome="EXECUTED",
                evidence={"domain": "A"},
                resulting_state_ref_or_hash="domain-state:A",
            )
            custody.record(
                "TRANSITION-B",
                outcome="EXECUTED",
                evidence={"domain": "B"},
                resulting_state_ref_or_hash="domain-state:B",
            )
        successor = submit.call_args_list[1].args[0]
        self.assertEqual(successor["prior_state_ref_or_hash"], "sha256:" + "d" * 64)
        self.assertNotEqual(successor["prior_state_ref_or_hash"], "domain-state:A")


if __name__ == "__main__":
    unittest.main()
