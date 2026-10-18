"""Offline tests for the registry admission transition evaluator."""
from __future__ import annotations

import copy
import unittest

from scripts import evaluate_registry_admission_request as adm

REGISTRY = {"generation": 319, "tasks": [{"task_id": "EXISTING-TASK-001"}]}
SHARDS = {"data/canonical-task-records/EXISTING-TASK-001.json"}


def request(**updates):
    row = {"schema": adm.RECORD_SCHEMA, "task_id": "NEW-TASK-001",
           "targets": {"repositories": ["StegVerse-org/StegVerse-SDK"], "paths": ["stegverse/tier_pricing.py"]}}
    value = {"schema": adm.REQUEST_SCHEMA, "request_id": "ADMIT-NEW-TASK-001", "task_id": "NEW-TASK-001",
             "task_row": row, "shard_path": "data/canonical-task-records/NEW-TASK-001.json",
             "proposed_generation": 320, "observed_live_generation": 319,
             "owning_existing_goal": "StegVerse-org/.github#164"}
    value.update(updates)
    return value


def resolver(present=("stegverse/tier_pricing.py",), unobservable=False):
    def resolve(repo, path):
        if unobservable:
            return None
        return path in present
    return resolve


class RegistryAdmissionRequestTests(unittest.TestCase):
    def refused(self, decision, disposition, code):
        self.assertEqual(decision["disposition"], disposition)
        self.assertEqual(decision["failure_code"], code)
        for field in adm.SIX_FIELDS:
            self.assertTrue(isinstance(decision[field], str) and decision[field].strip(), field)
        self.common(decision)

    def common(self, decision):
        self.assertFalse(decision["registry_written"])
        self.assertFalse(decision["ledger_appended"])
        body = dict(decision)
        self.assertEqual(body.pop("decision_sha256"), adm.canonical_sha256(body))

    def test_allow_new_row_at_tip_plus_one_with_resolving_paths(self):
        d = adm.evaluate(request(), REGISTRY, SHARDS, resolver())
        self.assertEqual(d["disposition"], "ALLOW")
        self.assertEqual((d["live_generation"], d["proposed_generation"]), (319, 320))
        self.assertEqual(d["target_paths"], [{"path": "stegverse/tier_pricing.py", "resolved": True}])
        self.assertFalse(any(f in d for f in adm.SIX_FIELDS))
        self.common(d)

    def test_allow_row_without_target_paths(self):
        req = request()
        req["task_row"].pop("targets")
        self.assertEqual(adm.evaluate(req, REGISTRY, SHARDS, resolver(unobservable=True))["disposition"], "ALLOW")

    def test_deny_generation_not_tip_plus_one(self):
        for gen in (319, 321, 318):
            with self.subTest(gen=gen):
                self.refused(adm.evaluate(request(proposed_generation=gen), REGISTRY, SHARDS, resolver()), "DENY", adm.NOT_TIP_PLUS_ONE)

    def test_deny_duplicate_task_id(self):
        req = request(task_id="EXISTING-TASK-001", shard_path="data/canonical-task-records/EXISTING-TASK-001.json")
        req["task_row"]["task_id"] = "EXISTING-TASK-001"
        self.refused(adm.evaluate(req, REGISTRY, SHARDS, resolver()), "DENY", "TASK_ID_NOT_UNIQUE")

    def test_deny_existing_shard(self):
        self.refused(adm.evaluate(request(), REGISTRY, SHARDS | {"data/canonical-task-records/NEW-TASK-001.json"}, resolver()), "DENY", "SHARD_ALREADY_EXISTS")

    def test_deny_wrong_shard_path(self):
        self.refused(adm.evaluate(request(shard_path="data/other.json"), REGISTRY, SHARDS, resolver()), "DENY", "SHARD_PATH_INVALID")

    def test_deny_row_id_mismatch(self):
        req = request()
        req["task_row"]["task_id"] = "OTHER-TASK-001"
        self.refused(adm.evaluate(req, REGISTRY, SHARDS, resolver()), "DENY", "TASK_ROW_ID_MISMATCH")

    def test_deny_row_schema(self):
        req = request()
        req["task_row"]["schema"] = "x"
        self.refused(adm.evaluate(req, REGISTRY, SHARDS, resolver()), "DENY", "TASK_ROW_SCHEMA_INVALID")

    def test_deny_unresolved_target_path(self):
        req = request()
        req["task_row"]["targets"]["paths"].append("stegverse/cost_component_registry.py")
        self.refused(adm.evaluate(req, REGISTRY, SHARDS, resolver()), "DENY", "TARGET_PATHS_UNRESOLVED")

    def test_deny_paths_without_repository(self):
        req = request()
        req["task_row"]["targets"]["repositories"] = []
        self.refused(adm.evaluate(req, REGISTRY, SHARDS, resolver()), "DENY", "TARGET_REPOSITORIES_INVALID")

    def test_fail_closed_paths_not_observable(self):
        self.refused(adm.evaluate(request(), REGISTRY, SHARDS, resolver(unobservable=True)), "FAIL_CLOSED", "TARGET_PATHS_NOT_OBSERVABLE")

    def test_fail_closed_registry_unreadable(self):
        self.refused(adm.evaluate(request(), None, SHARDS, resolver()), "FAIL_CLOSED", "REGISTRY_GENERATION_UNREADABLE")

    def test_fail_closed_malformed_request(self):
        self.refused(adm.evaluate(request(schema="x"), REGISTRY, SHARDS, resolver()), "FAIL_CLOSED", "ADMISSION_REQUEST_SCHEMA_INVALID")
        self.refused(adm.evaluate(request(proposed_generation=True), REGISTRY, SHARDS, resolver()), "FAIL_CLOSED", "ADMISSION_REQUEST_FIELD_MISSING")
        self.refused(adm.evaluate([], REGISTRY, SHARDS, resolver()), "FAIL_CLOSED", "ADMISSION_REQUEST_UNREADABLE")

    def test_evaluation_does_not_mutate_inputs(self):
        req, reg = request(), copy.deepcopy(REGISTRY)
        before = (copy.deepcopy(req), copy.deepcopy(reg))
        adm.evaluate(req, reg, set(SHARDS), resolver())
        self.assertEqual((req, reg), before)


if __name__ == "__main__":
    unittest.main()
