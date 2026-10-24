"""Fix 4 Labs adoption: the byte-identical caller of the SDK route installer.

Structural checks only; the evaluation itself is the exact-head run of the SDK
reusable workflow this caller references. No SDK import, no network, no clock.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALLER = ROOT / ".github/workflows/universal-intr-route-installation.yml"
REQUEST = ROOT / "control/universal-intr-route-installation-request.json"
ADOPTION = ROOT / "control/universal-intr-route-installation-adoption.json"
REGISTRY = ROOT / "control/workflow-surface-registry.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
INSTALLERS = (
    "canonical_work", "erl_active_research", "kv_ai_memory", "site_publication",
    "stegbrowser", "stegsocials_bounded", "tvc_recipient_admission_sign",
)


class CallerWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = CALLER.read_text(encoding="utf-8")

    def test_pins_one_sdk_commit_for_uses_and_sdk_ref(self):
        uses = re.findall(r"uses: StegVerse-org/StegVerse-SDK/\.github/workflows/"
                          r"universal-intr-route-installation\.yml@([0-9a-f]{40})\n", self.text)
        refs = re.findall(r"sdk_ref: ([0-9a-f]{40})\n", self.text)
        self.assertEqual(len(uses), 1)
        self.assertEqual(uses, refs)

    def test_is_evaluation_only(self):
        self.assertIn("permissions:\n  contents: read\n", self.text)
        for forbidden in ("secrets", "write", "workflow_dispatch", "GITHUB_TOKEN", "token"):
            self.assertNotIn(forbidden, self.text.split("\non:\n", 1)[1])

    def test_names_no_organization_consumer_or_router_value(self):
        body = self.text.split("\non:\n", 1)[1]
        for org in ("StegVerse-Labs", "SV-LLM", "SV-011", "GCAT", "Admissible", "StegGhost", "StegVerse-002"):
            self.assertNotIn(org, body)
        self.assertNotIn("stegbrowser", body.lower())
        self.assertIn("request_path: control/universal-intr-route-installation-request.json\n", body)

    def test_is_registered(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        rows = [row for row in registry["surfaces"] if row["path"] == str(CALLER.relative_to(ROOT))]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["classification"], "KEEP_STANDALONE_EXCEPTION")


class RequestAndAdoptionTests(unittest.TestCase):
    def test_request_is_one_installation_request_with_a_supplied_epoch(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["schema"], "stegverse.universal-intr-route-installation-request/v1")
        self.assertEqual(request["consumer_id"], "stegbrowser")
        self.assertEqual(request["route"]["route_id"], "stegverse.route.stegbrowser.v1")
        self.assertEqual(request["route"]["routing_surface"], "EXISTING_UNIVERSAL_INTR")
        self.assertRegex(request["hb_epoch"], r"^[0-9]+$")
        self.assertGreaterEqual(int(request["hb_epoch"]), 32)
        self.assertEqual(request["router"]["path"], "workers/universal_intr_profiled_ingress.py")
        self.assertRegex(request["router"]["predecessor_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_every_non_allow_carries_the_six_fields(self):
        adoption = json.loads(ADOPTION.read_text(encoding="utf-8"))
        self.assertEqual(sorted(adoption["consumers"]), sorted(INSTALLERS))
        dispositions = []
        for consumer_id, row in adoption["consumers"].items():
            dispositions.append(row)
            if "installer_retirement" in row:
                dispositions.append(row["installer_retirement"])
            if consumer_id == "stegbrowser":
                self.assertEqual(row["disposition"], "ALLOW")
            else:
                self.assertEqual((row["disposition"], row["failure_code"], row["route_id"]),
                                 ("FAIL_CLOSED", "EDGE_CONSUMER_ROUTE_NOT_PUBLISHED", None))
        dispositions.append(adoption["role_version_record"])
        for row in dispositions:
            if row["disposition"] != "ALLOW":
                for field in SIX:
                    self.assertTrue(row.get(field), (field, row))

    def test_no_installer_is_retired_while_its_runtime_path_is_unreconciled(self):
        adoption = json.loads(ADOPTION.read_text(encoding="utf-8"))
        for consumer_id, row in adoption["consumers"].items():
            retained = row.get("installer_retained")
            if retained is not None:
                self.assertTrue((ROOT / retained).is_file(), retained)
                continue
            self.assertEqual(consumer_id, "stegbrowser")
            self.assertEqual(row["disposition"], "ALLOW")  # non-authorizing SDK fixture assessment
            self.assertEqual(row["installer_retirement"]["disposition"], "FAIL_CLOSED")
            retired = ROOT / row["retired_installer"]
            successor = ROOT / row["materialization_successor"]
            self.assertFalse(retired.exists(), retired)
            self.assertTrue(successor.is_file(), successor)
            source = successor.read_text(encoding="utf-8")
            self.assertIn("from stegverse.universal_intr_route_installer import evaluate_installation", source)
            self.assertNotIn("from install_stegbrowser_universal_intr_route", source)


if __name__ == "__main__":
    unittest.main()
