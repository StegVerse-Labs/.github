"""Failure-map bridge from the continuation projection to StegHealth (issue #3039).

Covers the two Labs-side contract defects against StegHealth's
``tools/consume_ecosystem_failure_map.py`` and the default parent context:
the hint state string the consumer honours, and the per-failure
``source_task_context`` the consumer requires. StegHealth is not imported;
its required-field checks are restated here.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import native_email_continuation_transition as t  # noqa: E402
import reconcile_email_failure_incidents as r  # noqa: E402

MONITOR_TASK = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
MONITOR_VECTOR = "10100000100000"
SHA_A = "a" * 40


def msg(i: int, *, repo: str = "StegVerse-Labs/StegDB", sha: str = SHA_A, subject: str = "Run failed: lint") -> dict:
    return {"message_id": f"m{i:05d}", "repository": repo, "workflow": "lint",
            "head_sha": sha, "subject": subject, "internal_epoch": 1000}


def projected_receipt(rows: list[dict]) -> dict:
    state, _ = t.set_public_repositories(t.genesis(), ["StegVerse-Labs/StegDB"])
    state, _ = t.begin_cycle(state, 5000)
    state, _ = t.apply_page(state, 0, rows)
    state, _ = t.complete_pagination(state, has_more=False)
    return t.project_failure_map_receipt(state)


def steghealth_required_fields(failure_map: dict) -> None:
    """Restates consume_ecosystem_failure_map.py: consume() and source_task_context()."""
    assert failure_map.get("schema") == "stegverse.email-failure-map-for-steghealth/v1"
    assert failure_map.get("task_creation_owner") == "StegVerse-Labs/StegHealth"
    assert isinstance(failure_map.get("failures"), list)
    for failure in failure_map["failures"]:
        assert isinstance(failure, dict)
        assert failure.get("incident_id"), "incident_id required"
        context = failure.get("source_task_context")
        assert isinstance(context, dict), "source_task_context required"
        assert isinstance(context.get("task_id"), str) and context["task_id"], "source task id required"
        assert isinstance(context.get("lifecycle"), str) and context["lifecycle"], "source lifecycle required"
        cosv = context.get("cosv_task_vector")
        assert isinstance(cosv, str) and len(cosv) == 14 and cosv.isdigit(), "source COSV required"


class FailureMapBridgeTests(unittest.TestCase):
    def test_existing_hint_uses_the_consumer_state_string(self):
        incident = {"incident_id": "INC-EMAIL-1", "normalized_workflow": "lint"}
        tasks = [{"task_id": "FIX-001", "coordination_state": "ADMITTED", "systemic_incident_ref": "INC-EMAIL-1"}]
        vectors = [{"task_id": "FIX-001", "vector": "10100000111000"}]
        hint = r.existing_hint(incident, tasks, vectors)
        self.assertEqual(hint["state"], "EXACT_EXISTING_CORRECTIVE_TASK_HINT")
        self.assertEqual(hint["task_id"], "FIX-001")
        self.assertEqual(hint["cosv_task_vector"], "10100000111000")
        self.assertIsNone(r.existing_hint(incident, [{**tasks[0], "coordination_state": "CLOSED"}], vectors))

    def test_source_task_context_defaults_to_monitor_task_parent(self):
        receipt = projected_receipt([msg(1), msg(2, repo="Owner/private", sha="b" * 40)])
        registry = {"tasks": [{"task_id": MONITOR_TASK, "coordination_state": "PROPOSED"}]}
        failure_map = r.build_failure_map(receipt, registry, {"tasks": []}, "receipt.json")
        self.assertEqual(failure_map["failure_count"], 2)
        steghealth_required_fields(failure_map)
        for failure in failure_map["failures"]:
            self.assertIsNone(failure["existing_canonical_task_hint"])
            self.assertEqual(failure["source_task_context"],
                             {"task_id": MONITOR_TASK, "lifecycle": "PROPOSED", "cosv_task_vector": MONITOR_VECTOR})
            self.assertEqual(failure["source_task_context_basis"], r.CONTEXT_BASIS_DEFAULT)
        self.assertEqual(failure_map["source_task_context_default"],
                         {"task_id": MONITOR_TASK, "lifecycle": "PROPOSED", "cosv_task_vector": MONITOR_VECTOR})
        redacted = next(f for f in failure_map["failures"] if f["redacted"])
        self.assertEqual(redacted["repository"], "unknown-repo")
        self.assertEqual(redacted["repository_sha256"], t.repository_sha256("Owner/private"))
        self.assertNotIn("Owner/private", str(failure_map))

    def test_default_lifecycle_follows_registry_record_then_proposed(self):
        receipt = projected_receipt([msg(1)])
        admitted = {"tasks": [{"task_id": MONITOR_TASK, "coordination_state": "INGRESS_ADMITTED"}]}
        (failure,) = r.build_failure_map(receipt, admitted, {"tasks": []}, "x")["failures"]
        self.assertEqual(failure["source_task_context"]["lifecycle"], "INGRESS_ADMITTED")
        (failure,) = r.build_failure_map(receipt, {"tasks": []}, {"tasks": []}, "x")["failures"]
        self.assertEqual(failure["source_task_context"]["lifecycle"], "PROPOSED")

    def test_source_task_context_from_existing_hint(self):
        receipt = projected_receipt([msg(1)])
        incident_id = receipt["incidents"][0]["incident_id"]
        registry = {"tasks": [
            {"task_id": MONITOR_TASK, "coordination_state": "PROPOSED"},
            {"task_id": "FIX-001", "coordination_state": "ADMITTED", "systemic_incident_ref": incident_id},
        ]}
        vectors = {"tasks": [{"task_id": "FIX-001", "vector": "10100000111000"}]}
        (failure,) = r.build_failure_map(receipt, registry, vectors, "x")["failures"]
        self.assertEqual(failure["existing_canonical_task_hint"]["state"], "EXACT_EXISTING_CORRECTIVE_TASK_HINT")
        self.assertEqual(failure["source_task_context"],
                         {"task_id": "FIX-001", "lifecycle": "ADMITTED", "cosv_task_vector": "10100000111000"})
        self.assertEqual(failure["source_task_context_basis"], r.CONTEXT_BASIS_HINT)
        steghealth_required_fields(r.build_failure_map(receipt, registry, vectors, "x"))
        # A hint without a resolvable 14-digit vector cannot satisfy the
        # consumer; the context falls back to the default parent, visibly.
        (failure,) = r.build_failure_map(receipt, registry, {"tasks": []}, "x")["failures"]
        self.assertEqual(failure["existing_canonical_task_hint"]["task_id"], "FIX-001")
        self.assertEqual(failure["source_task_context"]["task_id"], MONITOR_TASK)
        self.assertEqual(failure["source_task_context_basis"], r.CONTEXT_BASIS_DEFAULT)
        steghealth_required_fields(r.build_failure_map(receipt, registry, {"tasks": []}, "x"))

    def test_cli_runs_consumer_with_relative_paths_and_surfaces_its_stderr(self):
        """The consumer runs with cwd=StegHealth; paths handed to it must not
        depend on the caller's cwd, and a consumer failure must say why."""
        stub = (
            "import argparse, json, pathlib, sys\n"
            "p = argparse.ArgumentParser(); p.add_argument('--failure-map'); p.add_argument('--state-root'); p.add_argument('--output')\n"
            "a = p.parse_args()\n"
            "fm = json.loads(pathlib.Path(a.failure_map).read_text())\n"
            "assert fm['schema'] == 'stegverse.email-failure-map-for-steghealth/v1'\n"
            "for f in fm['failures']:\n"
            "    c = f['source_task_context']; assert c['task_id'] and c['lifecycle'] and len(c['cosv_task_vector']) == 14\n"
            "if pathlib.Path(a.state_root, 'FAIL').exists(): sys.exit('consumer rejected: fixture failure')\n"
            "pathlib.Path(a.output).write_text(json.dumps({\n"
            "  'schema': 'steghealth.ecosystem-failure-remediation-handoff/v1', 'task_creation_owner': 'StegVerse-Labs/StegHealth',\n"
            "  'failure_count': len(fm['failures']), 'canonical_task_candidates': [],\n"
            "  'task_handoffs': [{'incident_id': f['incident_id'], 'task_id': 'STEGHEALTH-FAILURE-REMEDIATION-X', 'cosv_task_vector': '10100000111000',\n"
            "                     'next_action': 'INITIATE_CANONICAL_WORK_INGRESS'} for f in fm['failures']]}))\n")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            steghealth = root / "StegHealth"
            (steghealth / "tools").mkdir(parents=True)
            (steghealth / "tools/consume_ecosystem_failure_map.py").write_text(stub)
            (root / "receipt.json").write_text(json.dumps(projected_receipt([msg(1), msg(2, sha="b" * 40)])))
            (root / "registry.json").write_text(json.dumps({"generation": 1, "tasks": []}))
            (root / "vectors.json").write_text(json.dumps({"tasks": []}))
            env = {**os.environ, "STEGVERSE_STEGHEALTH_ROOT": str(steghealth)}
            cmd = [sys.executable, "-I", str(ROOT / "scripts/reconcile_email_failure_incidents.py"),
                   "--monitor-receipt", "receipt.json", "--registry", "registry.json",
                   "--vector-index", "vectors.json", "--vector-dir", "vectors", "--output", "out/handoff.json"]
            completed = subprocess.run(cmd, cwd=td, env=env, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((root / "out/handoff.json").read_text())
            self.assertEqual(result["state"], "STEGHEALTH_TASK_CREATION_COMPLETE", result)
            self.assertEqual(result["corrective_task_count"], 2)
            self.assertEqual({row["next_action"] for row in result["task_handoffs"]}, {"INITIATE_CANONICAL_WORK_INGRESS"})
            self.assertFalse(result["registry_changed"])
            self.assertEqual(result["failure_map_ref"], "out/handoff.failure-map.json")
            steghealth_required_fields(json.loads((root / "out/handoff.failure-map.json").read_text()))
            # A failing consumer is reported with its stderr, not silently.
            (steghealth / "FAIL").write_text("")
            completed = subprocess.run(cmd, cwd=td, env=env, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((root / "out/handoff.json").read_text())
            self.assertEqual(result["state"], "STEGHEALTH_OWNER_ATTEMPT_FAILED")
            self.assertIn("consumer rejected: fixture failure", result["stderr_tail"])

    def test_projected_receipt_round_trips_unchanged_through_the_mapper(self):
        receipt = projected_receipt([msg(i) for i in range(3)] + [msg(9, sha="c" * 40)])
        failure_map = r.build_failure_map(receipt, {"tasks": []}, {"tasks": []}, "receipt.json")
        self.assertEqual(failure_map["failure_count"], 2)
        steghealth_required_fields(failure_map)
        failure = next(f for f in failure_map["failures"] if f["observation_count"] == 3)
        self.assertEqual(failure["kind"], "GITHUB_FAILURE_EMAIL_CLUSTER")
        self.assertEqual(failure["repository"], "StegVerse-Labs/StegDB")
        self.assertEqual(failure["workflow"], "lint")
        self.assertEqual(failure["error_signature"], f"failure:lint@{SHA_A}")
        self.assertEqual(failure["observation_refs"], ["m00000", "m00001", "m00002"])
        self.assertEqual(failure["source_monitor_receipt_ref"], "receipt.json")


if __name__ == "__main__":
    unittest.main()
