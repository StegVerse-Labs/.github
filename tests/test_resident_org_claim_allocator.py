from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


allocator = load_module("resident_org_allocator_test", "scripts/allocate_claims.py")
consumer = load_module("resident_org_allocator_consumer_test", "scripts/consume_org_claim_allocator_request.py")


class ResidentOrgClaimAllocatorTests(unittest.TestCase):
    def request(self) -> dict:
        return json.loads(
            (ROOT / "control/resident-execution-request.d/org-claim-allocator-001.json").read_text(encoding="utf-8")
        )

    def test_request_is_repeatable_intent_not_claim_authority(self):
        value = self.request()
        self.assertEqual(value["task_id"], "SHWP-ORG-CLAIM-ALLOCATOR-001")
        self.assertEqual(value["mode"], "CANONICAL_ORGANIZATION_CLAIM_ALLOCATION")
        self.assertTrue(value["repeat_on_resident_dispatch"])
        self.assertFalse(value["request_grants_claim_authority"])
        self.assertTrue(value["allocator_remains_claim_authority"])
        self.assertFalse(value["heartbeat_grants_execution_authority"])
        self.assertFalse(value["github_token_required"])
        self.assertFalse(value["network_source_fetch_allowed"])
        self.assertFalse(value["second_machine_required"])
        self.assertEqual(value["authority_effect"], "NONE_REQUEST_ONLY")
        floor = value["source_catalog_floor"]
        self.assertEqual(floor["task_id"], "TASK-2026-0008")
        self.assertEqual(floor["requested_at"], "2026-09-03T00:28:00Z")
        self.assertEqual(floor["repository_full_name"], "StegVerse-Labs/Site")
        self.assertEqual(floor["required_dependency_surface"], "site:stegos-de006-bound-inference-publication")
        self.assertEqual(floor["purpose"], "MINIMUM_SOURCE_CATALOG_FRESHNESS_ONLY")
        self.assertEqual(floor["task_eligibility_effect"], "NONE")

    def test_allocator_lock_blocks_live_concurrent_owner_without_granting_authority(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "allocator.lock"
            first = allocator.acquire_allocator_lock(path)
            try:
                self.assertTrue(first["acquired"])
                second = allocator.acquire_allocator_lock(path)
                self.assertFalse(second["acquired"])
                self.assertEqual(second["state"], "ALLOCATOR_BUSY")
                self.assertEqual(second["owner_pid"], os.getpid())
                self.assertEqual(second["authority_effect"], "NONE_SERIALIZATION_ONLY")
            finally:
                allocator.release_allocator_lock(path)
            self.assertFalse(path.exists())

    def _write_minimal_source(self, source: Path) -> None:
        (source / "tasks").mkdir(parents=True, exist_ok=True)
        (source / "tasks/TASK-2026-0008.json").write_text(
            json.dumps({
                "schema": "stegverse.org-task/v0.2",
                "task_id": "TASK-2026-0008",
                "organization": "StegVerse-Labs",
                "goal": "test",
                "status": "queued",
                "requirements": {
                    "mandatory": [{
                        "repository": {"full_name": "StegVerse-Labs/Site"},
                        "scope": {"dependency_surfaces": ["site:stegos-de006-bound-inference-publication"]},
                    }],
                    "optional": [],
                },
                "dependencies": [],
                "requested_at": "2026-09-03T00:28:00Z",
            }),
            encoding="utf-8",
        )
        (source / "control").mkdir(parents=True, exist_ok=True)
        (source / "control/claims-active.json").write_text(
            json.dumps({"schema": "stegverse.org-claims/v1", "generation": 0, "claims": []}),
            encoding="utf-8",
        )
        (source / "control/queue.json").write_text(
            json.dumps({"schema": "stegverse.org-queue/v1", "generation": 0, "ordered_task_ids": []}),
            encoding="utf-8",
        )

    def test_resident_consumer_invokes_existing_allocator_and_retains_authority_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            request_path = runtime / consumer.REQUEST_REL
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps(self.request()), encoding="utf-8")
            self._write_minimal_source(source)
            allocator_path = runtime / consumer.ALLOCATOR_REL
            allocator_path.parent.mkdir(parents=True, exist_ok=True)
            allocator_path.write_text("# canonical allocator\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                claim = {
                    "repository": {"full_name": "StegVerse-Labs/Site"},
                    "mode": "scoped_exclusive",
                    "scope": {
                        "dependency_surfaces": ["site:stegos-de006-bound-inference-publication"],
                        "contracts": [],
                        "release_surfaces": [],
                    },
                    "task_id": "TASK-2026-0008",
                    "lease": {
                        "expires_at": "2026-09-04T00:00:00Z",
                        "heartbeat_due_at": "2026-09-03T08:00:00Z",
                        "fencing_token": 7,
                        "service_class": "low_contention",
                    },
                }
                (runtime / "control/claims-active.json").write_text(
                    json.dumps({
                        "schema": "stegverse.org-claims/v1",
                        "generation": 7,
                        "claims": [claim],
                    }),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps({
                        "selected": "TASK-2026-0008",
                        "queued": ["TASK-2026-0008"],
                        "blocked_missing_dependency_declaration": [],
                        "state": "ALLOCATION_COMPLETE",
                        "authority_effect": "CLAIM_AUTHORITY_ONLY_WHEN_SELECTED_BY_CANONICAL_ALLOCATOR",
                    }) + "\n",
                    stderr="",
                )

            result = consumer.consume(source, runtime, runner=runner, env={"PATH": "/bin", "HOME": td})
            self.assertEqual(result["state"], "ATTEMPT_RECORDED")
            self.assertEqual(result["source_catalog_floor"]["state"], "SOURCE_CATALOG_FLOOR_SATISFIED")
            self.assertEqual(result["source_catalog_floor"]["task_id"], "TASK-2026-0008")
            self.assertEqual(result["source_catalog_floor"]["task_eligibility_effect"], "NONE")
            self.assertEqual(result["control_inputs"]["state"], "CONTROL_INPUTS_READY")
            self.assertFalse(result["control_inputs"]["runtime_task_state_overwritten"])
            self.assertIn("TASK-2026-0008.json", result["control_inputs"]["imported_task_files"])
            self.assertEqual(result["selected_task_id"], "TASK-2026-0008")
            self.assertTrue(result["claim_grant_occurred"])
            evidence = result["claim_grant_evidence"]
            self.assertEqual(evidence["state"], "CLAIM_GRANT_EVIDENCE_RETAINED")
            self.assertEqual(evidence["task_id"], "TASK-2026-0008")
            self.assertEqual(evidence["claim_registry_generation"], 7)
            self.assertTrue((runtime / evidence["generation_receipt"]).is_file())
            self.assertTrue((runtime / evidence["latest_receipt"]).is_file())
            grant = json.loads((runtime / evidence["latest_receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(grant["state"], "CLAIM_GRANT_OBSERVED")
            self.assertEqual(grant["fencing_tokens"], [7])
            self.assertEqual(grant["dependency_surfaces"], ["site:stegos-de006-bound-inference-publication"])
            self.assertFalse(grant["observation_grants_claim_authority"])
            self.assertTrue(grant["allocator_remains_claim_authority"])
            self.assertEqual(grant["authority_effect"], "NONE_OBSERVATION_ONLY")
            self.assertFalse(result["request_granted_claim_authority"])
            self.assertTrue(result["allocator_remains_claim_authority"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertFalse(result["github_token_required"])
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["second_machine_required"])
            self.assertEqual(len(calls), 1)


    def test_selected_task_without_post_allocation_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            request_path = runtime / consumer.REQUEST_REL
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps(self.request()), encoding="utf-8")
            self._write_minimal_source(source)
            allocator_path = runtime / consumer.ALLOCATOR_REL
            allocator_path.parent.mkdir(parents=True, exist_ok=True)
            allocator_path.write_text("# canonical allocator\n", encoding="utf-8")

            def runner(command, **kwargs):
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps({
                        "selected": "TASK-2026-0008",
                        "queued": ["TASK-2026-0008"],
                        "blocked_missing_dependency_declaration": [],
                        "state": "ALLOCATION_COMPLETE",
                        "authority_effect": "CLAIM_AUTHORITY_ONLY_WHEN_SELECTED_BY_CANONICAL_ALLOCATOR",
                    }) + "\n",
                    stderr="",
                )

            with self.assertRaisesRegex(RuntimeError, "no retained canonical claim"):
                consumer.consume(source, runtime, runner=runner, env={"PATH": "/bin", "HOME": td})

    def test_resident_consumer_rejects_hosted_environment_before_allocator_invocation(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            request_path = runtime / consumer.REQUEST_REL
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps(self.request()), encoding="utf-8")
            self._write_minimal_source(source)
            allocator_path = runtime / consumer.ALLOCATOR_REL
            allocator_path.parent.mkdir(parents=True, exist_ok=True)
            allocator_path.write_text("# canonical allocator\n", encoding="utf-8")
            calls = []
            with self.assertRaisesRegex(RuntimeError, "hosted environment"):
                consumer.consume(
                    source,
                    runtime,
                    runner=lambda *a, **k: calls.append((a, k)),
                    env={"PATH": "/bin", "GITHUB_ACTIONS": "true"},
                )
            self.assertEqual(calls, [])


    def test_stale_source_catalog_missing_task8_fails_before_allocator_or_runtime_materialization(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            request_path = runtime / consumer.REQUEST_REL
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps(self.request()), encoding="utf-8")
            (source / "tasks").mkdir(parents=True, exist_ok=True)
            (source / "control").mkdir(parents=True, exist_ok=True)
            (source / "control/claims-active.json").write_text(
                json.dumps({"schema": "stegverse.org-claims/v1", "generation": 0, "claims": []}),
                encoding="utf-8",
            )
            (source / "control/queue.json").write_text(
                json.dumps({"schema": "stegverse.org-queue/v1", "generation": 0, "ordered_task_ids": []}),
                encoding="utf-8",
            )
            allocator_path = runtime / consumer.ALLOCATOR_REL
            allocator_path.parent.mkdir(parents=True, exist_ok=True)
            allocator_path.write_text("# canonical allocator\n", encoding="utf-8")
            calls = []

            with self.assertRaisesRegex(RuntimeError, "STALE_SOURCE_CATALOG"):
                consumer.consume(
                    source,
                    runtime,
                    runner=lambda *a, **k: calls.append((a, k)),
                    env={"PATH": "/bin", "HOME": td},
                )

            self.assertEqual(calls, [])
            self.assertFalse((runtime / "tasks").exists())
            self.assertFalse((runtime / "control/claims-active.json").exists())


    def test_catalog_floor_does_not_require_task8_to_remain_queued(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            self._write_minimal_source(source)
            task_path = source / "tasks/TASK-2026-0008.json"
            value = json.loads(task_path.read_text(encoding="utf-8"))
            value["status"] = "completed"
            task_path.write_text(json.dumps(value), encoding="utf-8")
            result = consumer.validate_source_catalog_floor(source, self.request())
            self.assertEqual(result["state"], "SOURCE_CATALOG_FLOOR_SATISFIED")
            self.assertEqual(result["task_status_observed"], "completed")
            self.assertEqual(result["task_eligibility_effect"], "NONE")

    def test_task_catalog_import_is_append_only_and_preserves_runtime_status(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            self._write_minimal_source(source)
            (runtime / "tasks").mkdir(parents=True)
            runtime_task = json.loads((source / "tasks/TASK-2026-0008.json").read_text(encoding="utf-8"))
            runtime_task["status"] = "active"
            (runtime / "tasks/TASK-2026-0008.json").write_text(json.dumps(runtime_task), encoding="utf-8")
            result = consumer.materialize_org_control_inputs(source, runtime)
            persisted = json.loads((runtime / "tasks/TASK-2026-0008.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["status"], "active")
            self.assertIn("TASK-2026-0008.json", result["preserved_runtime_task_files"])
            self.assertFalse(result["runtime_task_state_overwritten"])

    def test_new_task_supersedes_only_queued_prior_task_not_active_prior_task(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            (source / "tasks").mkdir(parents=True)
            (source / "control").mkdir(parents=True)
            (runtime / "tasks").mkdir(parents=True)
            prior = {
                "schema": "stegverse.org-task/v0.2",
                "task_id": "TASK-2026-0006",
                "organization": "StegVerse-Labs",
                "goal": "prior",
                "status": "queued",
                "requirements": {"mandatory": [], "optional": []},
                "dependencies": [],
                "requested_at": "2026-08-21T04:00:00Z",
            }
            successor = {
                "schema": "stegverse.org-task/v0.2",
                "task_id": "TASK-2026-0008",
                "organization": "StegVerse-Labs",
                "goal": "successor",
                "status": "queued",
                "requirements": {"mandatory": [], "optional": []},
                "dependencies": [],
                "requested_at": "2026-09-03T00:28:00Z",
                "supersedes": "TASK-2026-0006",
            }
            (source / "tasks/TASK-2026-0006.json").write_text(json.dumps(prior), encoding="utf-8")
            (source / "tasks/TASK-2026-0008.json").write_text(json.dumps(successor), encoding="utf-8")
            (runtime / "tasks/TASK-2026-0006.json").write_text(json.dumps(prior), encoding="utf-8")
            (source / "control/claims-active.json").write_text(
                json.dumps({"schema": "stegverse.org-claims/v1", "generation": 0, "claims": []}),
                encoding="utf-8",
            )
            (source / "control/queue.json").write_text(
                json.dumps({"schema": "stegverse.org-queue/v1", "generation": 0, "ordered_task_ids": []}),
                encoding="utf-8",
            )

            result = consumer.materialize_org_control_inputs(source, runtime)
            retired = json.loads((runtime / "tasks/TASK-2026-0006.json").read_text(encoding="utf-8"))
            self.assertEqual(retired["status"], "proposed")
            self.assertIn("superseded", retired["flags"])
            self.assertIn("TASK-2026-0006", result["superseded_queued_task_ids"])

            active = dict(prior)
            active["status"] = "active"
            (runtime / "tasks/TASK-2026-0006.json").write_text(json.dumps(active), encoding="utf-8")
            result2 = consumer.materialize_org_control_inputs(source, runtime)
            preserved = json.loads((runtime / "tasks/TASK-2026-0006.json").read_text(encoding="utf-8"))
            self.assertEqual(preserved["status"], "active")
            self.assertIn("TASK-2026-0006", result2["supersession_deferred_active_task_ids"])

    def test_resident_dispatch_and_materialization_wiring_present(self):
        dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
        bootstrap = (ROOT / "scripts/bootstrap_sovereign_runtime.py").read_text(encoding="utf-8")
        installer = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
        refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        self.assertIn('("org_claim_allocator", "scripts/consume_org_claim_allocator_request.py")', dispatcher)
        for source in (bootstrap, installer, refresh):
            self.assertIn("consume_org_claim_allocator_request.py", source)
            self.assertIn("allocate_claims.py", source)
            self.assertIn("org-claim-allocator-001.json", source)

    def test_task7_and_task8_site_claims_are_nonoverlapping(self):
        task7 = json.loads((ROOT / "tasks/TASK-2026-0007.json").read_text(encoding="utf-8"))
        task8 = json.loads((ROOT / "tasks/TASK-2026-0008.json").read_text(encoding="utf-8"))
        request7 = task7["requirements"]["mandatory"][0]
        request8 = task8["requirements"]["mandatory"][0]
        self.assertFalse(allocator.conflicts(request8, request7))
        self.assertTrue(allocator.dependency_surfaces(request7).isdisjoint(allocator.dependency_surfaces(request8)))


if __name__ == "__main__":
    unittest.main()
