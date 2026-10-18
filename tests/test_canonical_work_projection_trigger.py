"""canonical-work-projection-trigger: request -> fence -> projection -> receipts.

Every case runs against a temporary registry and temporary ledgers; the real
data/canonical-task-registry.json is never written.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_work_projection_trigger.py"
PROJECTION = ROOT / "scripts" / "apply_admitted_canonical_work_projection.py"
WORKFLOW = ROOT / ".github" / "workflows" / "canonical-work-projection-trigger.yml"
GOVERNANCE = ROOT / ".github" / "workflows" / "organization-governance-decision.yml"

_spec = importlib.util.spec_from_file_location("canonical_work_projection_trigger", SCRIPT)
trigger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trigger)

TASK_ID = "TASK-FIXTURE-PROJECTION-001"
CORRELATION = "corr-fixture-projection-001"
MAT = "INTR-MAT-" + "0" * 24


def ingress(**overrides):
    value = {"schema": trigger.projection.INGRESS_SCHEMA, "state": "INGRESS_ADMITTED",
             "authority_effect": "INGRESS_TRANSITION_ONLY", "claim_or_fence_minted": False,
             "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
             "materialization_id": MAT, "request_hash": "sha256:" + "1" * 64,
             "payload_hash": "sha256:" + "2" * 64, "operation_id": "op-fixture"}
    value.update(overrides)
    return value


def consumption(**overrides):
    value = {"schema": trigger.projection.CONSUMPTION_SCHEMA, "state": "INGRESS_BOUND_COORDINATION_PROJECTED",
             "claim_or_fence_minted": False, "materialization_id": MAT,
             "request_hash": "sha256:" + "1" * 64, "payload_hash": "sha256:" + "2" * 64,
             "operation_id": "op-fixture", "task_id": TASK_ID, "correlation_id": CORRELATION,
             "ingress_receipt_ref": "runtime://receipts/canonical-work-intr-ingress/" + MAT}
    value.update(overrides)
    return value


def request(request_id="cwp-fixture-001", generation=7, **overrides):
    value = {"schema": trigger.REQUEST_SCHEMA, "request_id": request_id, "task_id": TASK_ID,
             "observed_registry_generation": generation, "hb_epoch": "33",
             "ingress_receipt": ingress(), "consumption_receipt": consumption(),
             "authority_effect": "NONE_REQUEST_ONLY"}
    value.update(overrides)
    return value


class Workspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.registry = self.dir / "registry.json"
        self.shards = self.dir / "shards"
        self.shards.mkdir()
        self.registry.write_text(json.dumps({
            "generation": 7, "status": "FIXTURE", "nonclaims": [], "human_actions": [],
            "tasks": [{"task_id": TASK_ID, "correlation_id": CORRELATION, "coordination_state": "PROPOSED"}],
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.requests = self.dir / "requests"
        self.requests.mkdir()

    def write_request(self, value, name=None):
        path = self.requests / f"{name or value.get('request_id', 'unnamed')}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def decide(self, paths, apply=False):
        return trigger.evaluate(paths, registry_path=self.registry, task_shards=self.shards, apply=apply)

    def assertRefused(self, result, code):
        self.assertEqual(result["disposition"], "FAIL_CLOSED", result)
        self.assertEqual(result["failure_code"], code, result)
        for key in trigger.SIX_FIELDS:
            self.assertTrue(isinstance(result.get(key), str) and result[key], key)
        self.assertIs(result["consequence_committed"], False)


class DecisionTests(Workspace):
    def test_plan_allows_and_writes_nothing(self):
        before = self.registry.read_bytes()
        result = self.decide([self.write_request(request())])
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["projected_generation"], 8)
        self.assertEqual(result["generation_fence"]["disposition"], "ALLOW")
        self.assertIs(result["written"], False)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_apply_writes_exactly_what_the_projection_script_writes(self):
        path = self.write_request(request())
        req = json.loads(path.read_text())
        (self.dir / "i.json").write_text(json.dumps(req["ingress_receipt"]))
        (self.dir / "c.json").write_text(json.dumps(req["consumption_receipt"]))
        expected = self.dir / "expected.json"
        subprocess.run([sys.executable, str(PROJECTION), "--registry", str(self.registry),
                        "--task-shards", str(self.shards), "--ingress-receipt", str(self.dir / "i.json"),
                        "--consumption-receipt", str(self.dir / "c.json"), "--output", str(expected)],
                       check=True)
        result = self.decide([path], apply=True)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(self.registry.read_bytes(), expected.read_bytes())
        self.assertEqual(json.loads(self.registry.read_text())["generation"], 8)
        self.assertEqual(result["generation_set_by"], "apply_admitted_canonical_work_projection.project")

    def test_a_replay_of_an_applied_request_is_not_projected_twice(self):
        path = self.write_request(request())
        self.decide([path], apply=True)
        applied = self.registry.read_bytes()
        result = self.decide([path], apply=True)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["applicability"], "REPLAY_ALREADY_PROJECTED")
        self.assertEqual(self.registry.read_bytes(), applied)

    def test_a_stale_generation_is_a_fence_mismatch(self):
        result = self.decide([self.write_request(request(generation=6))])
        self.assertRefused(result, "REGISTRY_GENERATION_FENCE_MISMATCH")
        self.assertIn("session_mutation_generation_fence", result["evidence"])

    def test_unadmitted_work_is_refused(self):
        for bad in (ingress(state="INGRESS_PENDING"), ingress(claim_or_fence_minted=True),
                    ingress(credential_authority="GITHUB_TOKEN")):
            result = self.decide([self.write_request(request(ingress_receipt=bad))])
            self.assertRefused(result, "CANONICAL_WORK_PROJECTION_NOT_ADMITTED")

    def test_an_unknown_task_is_refused(self):
        result = self.decide([self.write_request(request(
            task_id="TASK-ABSENT-001", consumption_receipt=consumption(task_id="TASK-ABSENT-001")))])
        self.assertRefused(result, "CANONICAL_WORK_PROJECTION_NOT_ADMITTED")

    def test_a_missing_manifest_is_refused(self):
        self.assertRefused(self.decide([]), "CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT")
        self.assertRefused(self.decide([self.requests / "gone.json"]), "CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT")

    def test_more_than_one_request_per_push_is_refused(self):
        a = self.write_request(request("cwp-a-001"))
        b = self.write_request(request("cwp-b-001"))
        self.assertRefused(self.decide([a, b]), "CANONICAL_WORK_PROJECTION_BATCH_NOT_SINGULAR")

    def test_malformed_requests_are_refused(self):
        cases = [request(schema="other/v1"), request(authority_effect="EXECUTE"),
                 request(observed_registry_generation="7"), request(ingress_receipt=None),
                 request(consumption_receipt=consumption(task_id="OTHER"))]
        for value in cases:
            self.assertRefused(self.decide([self.write_request(value)]), "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")
        self.assertRefused(self.decide([self.write_request(request(), name="mismatched-name")]),
                           "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")
        broken = self.requests / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        self.assertRefused(self.decide([broken]), "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")

    def test_the_epoch_is_supplied_never_read_from_a_clock(self):
        value = request()
        del value["hb_epoch"]
        self.assertRefused(self.decide([self.write_request(value)]), "HB_EPOCH_NOT_SUPPLIED")
        for bad in ("31", "0", "+33", 33.0, True):
            result = self.decide([self.write_request(request(hb_epoch=bad))])
            self.assertRefused(result, "HB_EPOCH_INVALID")
            self.assertIs(result["derived_from_clock"], False)
        self.assertEqual(self.decide([self.write_request(request(hb_epoch="32"))])["disposition"], "ALLOW")

    def test_the_cli_exits_nonzero_with_the_six_fields_on_stderr(self):
        path = self.write_request(request(generation=5))
        done = subprocess.run([sys.executable, str(SCRIPT), "evaluate", "--mode", "plan", "--request", str(path),
                               "--registry", str(self.registry), "--task-shards", str(self.shards)],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        for key in trigger.SIX_FIELDS:
            self.assertIn(key + "=", done.stderr)
        none = subprocess.run([sys.executable, str(SCRIPT), "evaluate", "--mode", "plan", "--allow-none"],
                              capture_output=True, text=True)
        self.assertEqual(none.returncode, 0, none.stderr)
        self.assertEqual(json.loads(none.stdout)["applicability"], "NOT_APPLICABLE")


class LedgerTests(Workspace):
    def setUp(self):
        super().setUp()
        names = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")
        previous = {n: os.environ.get(n) for n in names}
        for n in names:
            os.environ[n] = str(self.dir / n.lower())

        def restore():
            for n, v in previous.items():
                os.environ.pop(n, None) if v is None else os.environ.__setitem__(n, v)
        self.addCleanup(restore)

    def receipts(self, variable, schema):
        return [r for r in (json.loads(p.read_text()) for p in Path(os.environ[variable]).rglob("*.json"))
                if r.get("schema") == schema]

    def test_an_allow_and_a_refusal_are_each_recorded_at_both_levels(self):
        refused = self.decide([self.write_request(request("cwp-stale-001", generation=1))])
        allowed = self.decide([self.write_request(request())], apply=True)
        for result, cls in ((allowed, trigger.APPLIED_CLASS), (refused, trigger.REFUSED_CLASS)):
            recorded = trigger.record(result, "33")
            self.assertEqual(recorded["transition_class"], cls)
            self.assertIs(recorded["organization_receipt_preserves_repository_receipt"], True)
        repo = self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1")
        org = self.receipts("STEGVERSE_ORG_LEDGER_ROOT", "stegverse.organization-transition-receipt/v1")
        self.assertEqual(sorted(r["transition_class"] for r in repo), sorted([trigger.APPLIED_CLASS, trigger.REFUSED_CLASS]))
        self.assertEqual(len(org), 2)
        stale, = [r for r in repo if r["transition_class"] == trigger.REFUSED_CLASS]
        for key in trigger.SIX_FIELDS:
            self.assertIn(key, stale["evidence"])
        self.assertEqual(stale["hb_reference"]["epoch"], 33)

    def test_recording_the_same_decision_twice_mints_one_receipt(self):
        result = self.decide([self.write_request(request())])
        first, second = trigger.record(result, "33"), trigger.record(result, "40")
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])

    def test_record_refuses_without_a_supplied_epoch(self):
        result = self.decide([self.write_request(request())])
        with self.assertRaises(ValueError):
            trigger.record(result, None)


class WorkflowShapeTests(unittest.TestCase):
    def test_push_trigger_mirrors_the_governance_decision_trigger(self):
        text, governance = WORKFLOW.read_text(), GOVERNANCE.read_text()
        self.assertIn("  push:\n    branches: [main]\n    paths:\n      - '.stegverse/governance-decision-requests/**'", governance)
        self.assertIn("  push:\n    branches: [main]\n    paths:\n      - '.stegverse/canonical-work-projection-requests/*.json'", text)
        self.assertNotIn("workflow_dispatch", text)
        self.assertNotIn("--force", text)
        self.assertNotIn("secrets.", text)
        self.assertIn("check_registry_generation_fence.py --mode push", text)
        self.assertIn("group: ${{ github.event_name == 'push' && 'organization-ledger'", text)

    def test_the_workflow_is_registered(self):
        registry = json.loads((ROOT / "control" / "workflow-surface-registry.json").read_text())
        paths = {s["path"] for s in registry["surfaces"]}
        self.assertIn(".github/workflows/canonical-work-projection-trigger.yml", paths)


if __name__ == "__main__":
    unittest.main()
