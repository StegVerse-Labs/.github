#!/usr/bin/env python3
"""Autonomous portable dispatch must prove the current original request was consumed."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import refresh_and_dispatch_resident_requests as bridge  # noqa: E402


class AutonomousProgressionPortableConsumptionBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name)
        self.task = bridge.AUTONOMOUS_PROGRESSION_TASK_ID
        self.receipt = {
            "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
            "task_id": self.task,
            "state": "COMPLETED",
            "request_sha256": "original-request-digest",
            "bootstrap_receipt_ref": "original-bootstrap-receipt",
            "credential_material_present": False,
            "network_source_fetch_performed": False,
        }
        self.path = self.runtime / bridge.AUTONOMOUS_PROGRESSION_CONSUMPTION_REL
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def dispatch(self, request_sha="original-request-digest", bootstrap_ref="original-bootstrap-receipt", state="COMPLETED"):
        return {"outcomes": [{
            "consumer": "canonical_work_coordination",
            "attempted": True,
            "result": {"canonical_work_request_set": {"outcomes": [{
                "task_id": self.task,
                "state": state,
                "request_sha256": request_sha,
                "bootstrap_receipt_ref": bootstrap_ref,
            }]}},
        }]}

    def observe(self, dispatch):
        return bridge.canonical_work_goal_consumption_evidence(
            self.runtime, "canonical_work_coordination", self.task, dispatch
        )

    def test_original_goal_must_have_exact_receipt(self):
        receipt, digest, required, valid, matched = self.observe(self.dispatch())
        self.assertTrue(required)
        self.assertIsNone(receipt)
        self.assertIsNone(digest)
        self.assertFalse(valid)
        self.assertFalse(matched)

    def test_current_matching_consumption_is_valid(self):
        self.path.write_text(json.dumps(self.receipt), encoding="utf-8")
        receipt, digest, required, valid, matched = self.observe(self.dispatch())
        self.assertTrue(required)
        self.assertTrue(valid)
        self.assertTrue(matched)
        self.assertEqual(receipt["task_id"], self.task)
        self.assertEqual(len(digest), 64)

    def test_stale_or_unrelated_consumption_fails(self):
        self.path.write_text(json.dumps(self.receipt), encoding="utf-8")
        for dispatch in (
            self.dispatch(request_sha="other-request"),
            self.dispatch(bootstrap_ref="other-bootstrap"),
            self.dispatch(state="ATTEMPT_RECORDED"),
            {"outcomes": []},
        ):
            with self.subTest(dispatch=dispatch):
                _, _, required, valid, matched = self.observe(dispatch)
                self.assertTrue(required)
                self.assertFalse(valid)
                self.assertFalse(matched)

    def test_forged_or_nonterminal_receipt_fails(self):
        for key, value in (
            ("task_id", "OTHER-TASK"),
            ("state", "ATTEMPT_RECORDED"),
            ("credential_material_present", True),
            ("network_source_fetch_performed", True),
        ):
            with self.subTest(key=key):
                forged = dict(self.receipt, **{key: value})
                self.path.write_text(json.dumps(forged), encoding="utf-8")
                _, _, required, valid, _ = self.observe(self.dispatch())
                self.assertTrue(required)
                self.assertFalse(valid)

    def test_other_goal_is_not_affected(self):
        _, _, required, valid, matched = bridge.canonical_work_goal_consumption_evidence(
            self.runtime, "canonical_work_coordination", "OTHER-TASK", self.dispatch()
        )
        self.assertFalse(required)
        self.assertTrue(valid)
        self.assertTrue(matched)


if __name__ == "__main__":
    unittest.main()
