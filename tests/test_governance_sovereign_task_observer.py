# Validation-only branch trigger; do not merge.
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from heartbeat_runtime.blocker_policy import validate_worker_response_blocker
from heartbeat_runtime.worker_runtime import WorkerCoordinator

ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "workers" / "governance_sovereign_task_observer_worker.py"
HANDOFF_PATH = ROOT / "handoffs" / "GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001.json"
REGISTRY_FRAGMENT_PATH = ROOT / "control" / "worker-registry.d" / "governance-sovereign-task-observer-001.json"
ADAPTER_FRAGMENT_PATH = ROOT / "control" / "process-worker-adapters.d" / "governance-sovereign-task-observer-001.json"
COST_BASIS_PATH = ROOT / "cost-basis" / "worker-runtime" / "governance-sovereign-task-observer.json"
spec = importlib.util.spec_from_file_location("governance_sovereign_task_observer_worker", WORKER_PATH)
worker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(worker)


class GovernanceSovereignTaskObserverTests(unittest.TestCase):
    def build_source(self, root: Path, include_decision: bool = False) -> None:
        (root / "automation").mkdir(parents=True)
        (root / "scripts").mkdir(parents=True)
        (root / "docs" / "governance").mkdir(parents=True)
        (root / "evidence" / "cge-decision-issuer-architecture").mkdir(parents=True)
        (root / "GOVERNANCE_MIRROR_HANDOFF.md").write_text("Governance\n", encoding="utf-8")
        (root / "docs" / "governance" / "CGE_DECISION_ISSUER_ARCHITECTURE_MIRROR_HANDOFF.md").write_text("CGE\n", encoding="utf-8")
        registry = {
            "registry_version": "1.0.0",
            "owner": "StegVerse-Labs/Governance",
            "tasks": [{
                "id": "CGE-DECISION-ISSUER-ARCHITECTURE-OWNERSHIP-001",
                "title": "watch",
                "organization": "StegVerse-Labs",
                "repository": "Governance",
                "path": "docs/governance/CGE_DECISION_ISSUER_ARCHITECTURE_MIRROR_HANDOFF.md",
                "mode": "evidence_watch",
                "prerequisites": [],
                "completion_condition": {
                    "type": "file_exists",
                    "path": "evidence/cge-decision-issuer-architecture/latest.json"
                },
                "evidence_path": "evidence/cge-decision-issuer-architecture/latest.json",
                "status": "blocked"
            }]
        }
        (root / "automation" / "governance_task_registry.json").write_text(json.dumps(registry), encoding="utf-8")
        script = root / "scripts" / "run_governance_tasks.py"
        script.write_text(
            "import argparse,json,pathlib\n"
            "p=argparse.ArgumentParser(); p.add_argument('--receipt',required=True); a=p.parse_args()\n"
            "root=pathlib.Path(__file__).resolve().parents[1]\n"
            "decision=root/'evidence/cge-decision-issuer-architecture/latest.json'\n"
            "state='completed' if decision.is_file() else 'blocked'\n"
            "out={'registry_version':'1.0.0','repository':'StegVerse-Labs/Governance','validation_status':'pass','validation_errors':[],'tasks':[{'id':'CGE-DECISION-ISSUER-ARCHITECTURE-OWNERSHIP-001','state':state}]}\n"
            "path=pathlib.Path(a.receipt); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out))\n",
            encoding="utf-8",
        )
        if include_decision:
            (root / "evidence" / "cge-decision-issuer-architecture" / "latest.json").write_text("{}\n", encoding="utf-8")

    def invocation(self) -> dict:
        return {
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "SHWP-GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001-G7",
            },
            "handoff": {
                "authority": {
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "non_tv_tvc_secret_or_token_allowed": False,
                    "repository_writeback_authority": False,
                    "heartbeat_grants_execution_authority": False,
                }
            },
        }

    def clean_env(self, *, home: Path, source: Path | None = None, bound_state: Path | None = None) -> dict[str, str]:
        values = {
            "HOME": str(home),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        }
        if source is not None:
            values[worker.ROOT_ENV] = str(source)
        if bound_state is not None:
            values[worker.BOUND_STATE_ENV] = str(bound_state)
        return values

    def marker(self, path: Path) -> None:
        path.write_text(json.dumps({
            "declared": True,
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "declaration_source": "unit-test",
        }), encoding="utf-8")

    def test_blocked_cge_watch_is_valid_sovereign_observation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            home = base / "home"
            source = base / "Governance"
            bound_state = base / "bound-state"
            home.mkdir(); source.mkdir(); bound_state.mkdir()
            self.build_source(source, include_decision=False)
            marker = base / "node.json"; self.marker(marker)
            with patch.dict(os.environ, self.clean_env(home=home, source=source, bound_state=bound_state), clear=True), patch.object(worker, "NODE_MARKERS", (marker,)):
                receipt = worker.execute(self.invocation())
            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertEqual(receipt["source_discovery_mode"], "explicit")
            self.assertEqual(receipt["cge_architecture_watch_state"], "blocked")
            self.assertFalse(receipt["architecture_decision_receipt_observed"])
            self.assertFalse(receipt["github_token_used"])
            self.assertFalse(receipt["repository_writeback_performed"])
            self.assertFalse(receipt["heartbeat_effect"])
            self.assertTrue((bound_state / "observed" / "latest.json").is_file())
            self.assertTrue((bound_state / "receipts" / "latest.json").is_file())
            self.assertFalse((home / ".stegverse" / "receipts" / "governance-sovereign-task-observer-latest.json").exists())

    def test_canonical_local_source_path_is_discovered_without_env_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            home = base / "home"
            source = home / ".stegverse" / "source" / "Governance"
            bound_state = base / "bound-state"
            home.mkdir(); source.mkdir(parents=True); bound_state.mkdir()
            self.build_source(source, include_decision=False)
            marker = base / "node.json"; self.marker(marker)
            with patch.dict(os.environ, self.clean_env(home=home, bound_state=bound_state), clear=True), patch.object(worker, "NODE_MARKERS", (marker,)):
                receipt = worker.execute(self.invocation())
            self.assertEqual(receipt["source_root"], str(source.resolve()))
            self.assertEqual(receipt["source_discovery_mode"], "canonical_local_path")
            self.assertEqual(receipt["cge_architecture_watch_state"], "blocked")

    def test_incomplete_canonical_candidate_is_not_selected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            home = base / "home"
            incomplete = home / ".stegverse" / "source" / "Governance"
            incomplete.mkdir(parents=True)
            (incomplete / "GOVERNANCE_MIRROR_HANDOFF.md").write_text("incomplete\n", encoding="utf-8")
            with patch.dict(os.environ, {"HOME": str(home)}, clear=True):
                self.assertIsNone(worker.find_source_root())

    def test_missing_source_yields_handoff_ready_not_duplicate_resolution(self) -> None:
        response = worker.source_wait_response(worker.SourceUnavailable("source pending"))
        validate_worker_response_blocker(response)
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertEqual(response["transition_sequence"], 1)
        self.assertNotIn("blocker", response)
        self.assertIn("TVC-PRIVATE-SOURCE-READ-001", response["evidence_refs"][0])

    def test_real_observer_defect_emits_valid_sandbox_resolution_contract(self) -> None:
        response = worker.blocked_response(RuntimeError("observer contract defect"))
        validate_worker_response_blocker(response)
        self.assertEqual(response["state"], "BLOCKED")
        self.assertEqual(response["transition_sequence"], 1)
        self.assertFalse(response["blocker"]["resolvable_by_current_worker"])
        self.assertIn("sandbox", response["blocker"]["next_solution_action"].lower())
        self.assertTrue(any(ref.startswith("resolution-contract:v1:") for ref in response["evidence_refs"]))

    def test_completed_response_matches_runtime_state_machine(self) -> None:
        response = worker.completed_response({"local_receipt_ref": "receipts/latest.json"})
        validate_worker_response_blocker(response)
        self.assertEqual(response["state"], "COMPLETED")
        self.assertEqual(response["transition_sequence"], 2)
        self.assertEqual(response["evidence_refs"], ["receipts/latest.json"])

    def test_hosted_environment_is_rejected(self) -> None:
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute(self.invocation())

    def test_github_token_environment_is_rejected(self) -> None:
        with patch.dict(os.environ, {"GITHUB_TOKEN": "forbidden"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment"):
                worker.execute(self.invocation())

    def test_invocation_cannot_grant_writeback_or_heartbeat_authority(self) -> None:
        bad = self.invocation()
        bad["handoff"]["authority"]["repository_writeback_authority"] = True
        with self.assertRaisesRegex(RuntimeError, "write back"):
            worker.validate_invocation(bad)
        bad = self.invocation()
        bad["handoff"]["authority"]["heartbeat_grants_execution_authority"] = True
        with self.assertRaisesRegex(RuntimeError, "heartbeat may not grant"):
            worker.validate_invocation(bad)

    def test_executable_handoff_registry_adapter_and_cost_basis_are_runtime_compatible(self) -> None:
        handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
        fragment = json.loads(REGISTRY_FRAGMENT_PATH.read_text(encoding="utf-8"))
        adapter_fragment = json.loads(ADAPTER_FRAGMENT_PATH.read_text(encoding="utf-8"))
        cost_basis = json.loads(COST_BASIS_PATH.read_text(encoding="utf-8"))
        task = fragment["tasks"][0]
        worker_row = fragment["workers"][0]
        adapter_row = adapter_fragment["adapters"][0]
        runtime = WorkerCoordinator(ROOT, adapters={adapter_row["adapter_ref"]: object()})

        self.assertEqual(handoff["schema"], "stegverse.executable-handoff/v0.1")
        self.assertTrue(runtime._execution_authorized(handoff))
        budget, basis = runtime._expiry_budget(task)
        self.assertEqual(budget, 16)
        self.assertEqual(basis, "TASK_CLASS_COST_BASIS")
        selected = runtime._worker_for(task, {"workers": [worker_row]})
        self.assertIsNotNone(selected)
        self.assertEqual(selected["worker_id"], worker.WORKER_ID)
        self.assertEqual(adapter_row["type"], "process_json_bound_state_v0.1")
        self.assertEqual(adapter_row["bound_state_allowed_paths"], ["observed/**", "receipts/**"])
        self.assertEqual(cost_basis["cost_estimate"]["external_cost_usd"], 0)
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])


if __name__ == "__main__":
    unittest.main()
