from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


allocator = load_module("resident_org_allocator_test", "scripts/allocate_claims.py")
consumer = load_module("resident_org_allocator_consumer_test", "scripts/consume_org_claim_allocator_request.py")
LEDGER_EMITTER = ".stegverse/transition-ledger/emit.py"
# A carrier heartbeat epoch (kernel HB32 anchor is 32); supplied, never derived from a clock.
CARRIER_HB_EPOCH = 4096


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
        self.assertEqual(
            floor["scope_sha256"],
            "98096b5825e85dd558f9cb5a4e882002543d4c703cfa7981cd2d826c80c1a05b",
        )

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

    LEDGER_FILES = (
        ".stegverse/transition-ledger/emit.py",
        ".stegverse/transition-ledger/contract.json",
        ".stegverse/transition-ledger/org-contract.json",
        "org-kernel/kernel.py",
        "org-kernel/node_store.py",
        "resident-runtime/ledger_store.py",
        "resident-runtime/aggregate_repo_transition.py",
        "resident-runtime/organization_batch_custody.py",
        "tasks/TASK-2026-0012.json",
    )

    def _consume(self, source: Path, runtime: Path, **kwargs):
        ledgers = runtime.parent / "ledgers"
        (ledgers / "org" / "receipts").mkdir(parents=True, exist_ok=True)
        if not (ledgers / "org" / "HEAD.json").exists() and (source / LEDGER_EMITTER).is_file():
            # An empty chain never mints a fence: root it with a prior recorded
            # refusal through the existing emitters; no genesis is synthesized.
            consumer.record_transition(
                consumer.ledger_custody(source, ledgers / "seed-repo", ledgers / "org"), consumer.REFUSED,
                "ORGANIZATION-WORKER-CLAIM-REFUSED-prior-attempt", "sha256:" + "0" * 64,
                {"disposition": "DENY", "task_id": "NONE", "request_sha256": "0" * 64,
                 "failed_predicate": "NO_ELIGIBLE_TASK", "fencing_token": None, "consequence_committed": False},
                organization=True, identity=("task_id", "request_sha256", "failed_predicate"))
        kwargs.setdefault("hb_epoch", CARRIER_HB_EPOCH)
        return consumer.consume(source, runtime, repo_ledger_root=ledgers / "repo",
                                org_ledger_root=ledgers / "org", **kwargs)

    def _write_minimal_source(self, source: Path) -> None:
        for rel in self.LEDGER_FILES:
            (source / rel).parent.mkdir(parents=True, exist_ok=True)
            (source / rel).write_bytes((ROOT / rel).read_bytes())
        (source / "tasks").mkdir(parents=True, exist_ok=True)
        canonical = json.loads((ROOT / "tasks/TASK-2026-0008.json").read_text(encoding="utf-8"))
        (source / "tasks/TASK-2026-0008.json").write_text(
            json.dumps(canonical),
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
            (runtime / "control").mkdir(parents=True, exist_ok=True)
            (runtime / "control/claims-active.json").write_text(
                json.dumps({"schema": "stegverse.org-claims/v1", "generation": 7, "claims": []}), encoding="utf-8")
            allocator_path = runtime / consumer.ALLOCATOR_REL
            allocator_path.parent.mkdir(parents=True, exist_ok=True)
            allocator_path.write_bytes((ROOT / consumer.ALLOCATOR_REL).read_bytes())
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return subprocess.run(command, **kwargs)

            result = self._consume(source, runtime, runner=runner, env={"PATH": os.environ.get("PATH", "/bin"), "HOME": td})
            self.assertEqual(result["state"], "ATTEMPT_RECORDED")
            self.assertEqual(result["disposition"], "ALLOW")
            self.assertEqual(result["source_catalog_floor"]["state"], "SOURCE_CATALOG_FLOOR_SATISFIED")
            self.assertEqual(result["source_catalog_floor"]["task_id"], "TASK-2026-0008")
            self.assertEqual(result["source_catalog_floor"]["task_eligibility_effect"], "NONE")
            self.assertEqual(
                result["source_catalog_floor"]["scope_sha256"],
                "98096b5825e85dd558f9cb5a4e882002543d4c703cfa7981cd2d826c80c1a05b",
            )
            self.assertEqual(result["control_inputs"]["state"], "CONTROL_INPUTS_READY")
            self.assertFalse(result["control_inputs"]["runtime_task_state_overwritten"])
            self.assertIn("TASK-2026-0008.json", result["control_inputs"]["imported_task_files"])
            self.assertEqual(result["selected_task_id"], "TASK-2026-0008")
            self.assertTrue(result["claim_grant_occurred"])
            self.assertEqual(result["fencing_token"], 8)
            evidence = result["claim_grant_evidence"]
            self.assertEqual(evidence["state"], "CLAIM_GRANT_EVIDENCE_RETAINED")
            self.assertEqual(evidence["task_id"], "TASK-2026-0008")
            self.assertEqual(evidence["claim_registry_generation"], 8)
            self.assertTrue((runtime / evidence["generation_receipt"]).is_file())
            grant = json.loads((runtime / evidence["generation_receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(grant["state"], "CLAIM_GRANT_OBSERVED")
            self.assertEqual(grant["fencing_tokens"], [8])
            self.assertEqual(grant["dependency_surfaces"], ["site:stegos-de006-bound-inference-publication"])
            self.assertFalse(grant["observation_grants_claim_authority"])
            self.assertTrue(grant["allocator_remains_claim_authority"])
            self.assertEqual(grant["authority_effect"], "NONE_OBSERVATION_ONLY")
            latest = json.loads((runtime / evidence["latest_receipt"]).read_text(encoding="utf-8"))
            self.assertTrue(latest["projection_only"])
            self.assertEqual(latest["evidence_ref"], evidence["generation_receipt"])
            self.assertFalse(result["request_granted_claim_authority"])
            self.assertTrue(result["allocator_remains_claim_authority"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertFalse(result["github_token_required"])
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["second_machine_required"])
            self.assertEqual([c[0][2:] for c in calls], [["--plan"], ["--task", "TASK-2026-0008", "--fencing-token", "8"]])


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

            (runtime / "control").mkdir(parents=True, exist_ok=True)
            (runtime / "control/claims-active.json").write_text(
                json.dumps({"schema": "stegverse.org-claims/v1", "generation": 7, "claims": []}), encoding="utf-8")

            def runner(command, **kwargs):
                planned = "--plan" in command
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps({
                        "selected": "TASK-2026-0008",
                        "queued": ["TASK-2026-0008"],
                        "blocked_missing_dependency_declaration": [],
                        "claim_registry_generation": 7,
                        "requested_claims": [],
                        "state": "ALLOCATION_PLANNED" if planned else "ALLOCATION_COMPLETE",
                        "authority_effect": "CLAIM_AUTHORITY_ONLY_WHEN_SELECTED_BY_CANONICAL_ALLOCATOR",
                    }) + "\n",
                    stderr="",
                )

            with self.assertRaisesRegex(RuntimeError, "no retained canonical claim"):
                self._consume(source, runtime, runner=runner, env={"PATH": "/bin", "HOME": td})

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
                self._consume(
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
            for rel in self.LEDGER_FILES:
                if not rel.startswith("tasks/"):
                    (source / rel).parent.mkdir(parents=True, exist_ok=True)
                    (source / rel).write_bytes((ROOT / rel).read_bytes())
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
                self._consume(
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


    def test_old_task8_scope_digest_fails_before_allocator(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            self._write_minimal_source(source)
            task_path = source / "tasks/TASK-2026-0008.json"
            value = json.loads(task_path.read_text(encoding="utf-8"))
            scope = value["requirements"]["mandatory"][0]["scope"]
            scope["paths"] = [
                "stegos-bootstrap/index.html",
                "stegos-bootstrap/admitted-inference.js",
                "stegos-bootstrap/command-ingress.js",
                "stegos-bootstrap/command.html",
                "stegos-bootstrap/service-worker.js",
            ]
            task_path.write_text(json.dumps(value), encoding="utf-8")
            request_path = runtime / consumer.REQUEST_REL
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps(self.request()), encoding="utf-8")
            allocator_path = runtime / consumer.ALLOCATOR_REL
            allocator_path.parent.mkdir(parents=True, exist_ok=True)
            allocator_path.write_text("# canonical allocator\n", encoding="utf-8")
            calls = []
            with self.assertRaisesRegex(RuntimeError, "claim scope digest mismatch"):
                self._consume(
                    source,
                    runtime,
                    runner=lambda *a, **k: calls.append((a, k)),
                    env={"PATH": "/bin", "HOME": td},
                )
            self.assertEqual(calls, [])

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
            self.assertIn("org-claim-allocator-sdk-manifest-001.json", source)

    def test_task7_and_task8_site_claims_are_nonoverlapping(self):
        task7 = json.loads((ROOT / "tasks/TASK-2026-0007.json").read_text(encoding="utf-8"))
        task8 = json.loads((ROOT / "tasks/TASK-2026-0008.json").read_text(encoding="utf-8"))
        request7 = task7["requirements"]["mandatory"][0]
        request8 = task8["requirements"]["mandatory"][0]
        self.assertFalse(allocator.conflicts(request8, request7))
        self.assertTrue(allocator.dependency_surfaces(request7).isdisjoint(allocator.dependency_surfaces(request8)))


LEDGER_REF = "refs/stegverse/organization-ledger"
REPO_NAMESPACE = "repository-ledger/StegVerse-Labs/.github"
HOSTED = {"GITHUB_ACTIONS": "true", "CI": "true"}
LOCUS_VARIABLES = ("STEGVERSE_ORG_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_STORE", "STEGVERSE_ORG_LEDGER_GIT_REF",
                   "STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY")
# The repository's own Organization ledger declaration (store git), which the
# suite-wide POSIX test locus (tests/conftest.py, tests/__init__.py) replaces.
DECLARED_LOCUS = json.loads((ROOT / ".stegverse/transition-ledger/org-contract.json").read_text(
    encoding="utf-8"))["organization_ledger"]
custody_tests = load_module("resident_org_allocator_custody_fixtures", "tests/test_org_claim_custody.py")


def bare_repository(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-q", str(path)], check=True)
    return path


def ref_tip(node: Path, ref: str = LEDGER_REF) -> str | None:
    found = subprocess.run(["git", "--git-dir", str(node), "rev-parse", "-q", "--verify", ref],
                           capture_output=True, text=True)
    return found.stdout.strip() if found.returncode == 0 else None


def locator(node: Path, ref: str = LEDGER_REF) -> str:
    return "git+" + str(node) + "#" + ref + ":" + REPO_NAMESPACE


class EventEphemeralClaimMaterializationTests(unittest.TestCase):
    """The hosted event-ephemeral consumer, against the repository's own declared git store.

    No resident machine is awaited: the consumer runs where the request event
    lands, appends to the declared ref only, and leaves no chain on the host.
    The HOSTED_ENV refusal still holds for a POSIX repository root, an
    explicit Organization root, and a repository chain off the declared ref.
    """

    def setUp(self):
        loader = importlib.machinery.SourceFileLoader
        exec_module = loader.exec_module

        def exec_and_declare(loader_self, module):
            # Every aggregator copy loaded during the test carries the repository's declaration.
            exec_module(loader_self, module)
            contract = getattr(module, "C", None)
            if callable(getattr(module, "declared_ledger_locus", None)) and isinstance(contract, dict):
                contract["organization_ledger"] = dict(DECLARED_LOCUS)

        declared = mock.patch.object(loader, "exec_module", exec_and_declare)
        declared.start()
        self.addCleanup(declared.stop)
        self._td = tempfile.TemporaryDirectory()
        self.base = Path(self._td.name)
        self.node = bare_repository(self.base / "node.git")
        environment = {key: value for key, value in os.environ.items() if key not in LOCUS_VARIABLES}
        environment["STEGVERSE_ORG_LEDGER_GIT_DIR"] = str(self.node)
        patcher = mock.patch.dict(os.environ, environment, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._td.cleanup)
        self.env = custody_tests.Env(self.base / "claim", org_ledger=self.base / "unused-org-root")
        # Root the declared chain through the existing emitters; no genesis is synthesized.
        custody_tests.seed_rooted_chain(self.env.source, None, self.base / "seed-repo-ledger")
        self.seeded = ref_tip(self.node)
        self.assertIsNotNone(self.seeded)
        self.calls = []

    def runner(self, command, **kwargs):
        self.calls.append((command, kwargs))
        return subprocess.run(command, **kwargs)

    def hosted(self, **kwargs):
        kwargs.setdefault("hb_epoch", CARRIER_HB_EPOCH)
        return consumer.consume(self.env.source, self.env.runtime, runner=self.runner,
                                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **HOSTED}, **kwargs)

    def assert_refused_before_anything(self, **kwargs):
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            self.hosted(**kwargs)
        self.assertEqual(self.calls, [])
        self.assertEqual(ref_tip(self.node), self.seeded)
        self.assertFalse((self.env.runtime / "tasks").exists())

    def test_hosted_event_ephemeral_consumption_grants_on_the_declared_ref(self):
        self.assertTrue(consumer.event_ephemeral_materialization(self.env.source, locator(self.node), None))
        result = self.hosted(repo_ledger_root=locator(self.node))
        self.assertEqual(result["transition_class"], consumer.GRANTED, result)
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["fencing_token"], 8)
        self.assertEqual(result["organization_readback"], "VERIFIED")
        self.assertTrue(result["allocator_remains_claim_authority"])
        self.assertFalse(result["request_granted_claim_authority"])
        # The existing allocator ran, without the hosted markers in its environment.
        self.assertEqual([c[0][2:] for c in self.calls], [["--plan", "--task", "TASK-2026-0013"],
                                                           ["--task", "TASK-2026-0013", "--fencing-token", "8"]])
        for _, kwargs in self.calls:
            self.assertFalse(set(HOSTED) & set(kwargs["env"]))
        # Both receipts are on the declared ref: the Organization HEAD at the
        # root, the repository HEAD in its declared subtree. No host chain.
        custody = consumer.ledger_custody(self.env.source, locator(self.node), None, event_ephemeral=True)
        self.assertTrue(custody["shared_ref"])
        keys = custody["emitter"].ledger_store
        self.assertEqual(custody["organization_store"].get(keys.HEAD_KEY)["receipt_sha256"],
                         result["organization_receipt_sha256"])
        self.assertEqual(custody["repository_store"].get(keys.HEAD_KEY)["receipt_sha256"],
                         result["repository_receipt_sha256"])
        self.assertFalse(self.env.repo.exists())
        self.assertFalse(any(path.name.startswith("git+") for path in (Path.cwd(), self.base) for path in path.iterdir()))
        # Read back from a fresh fetch of the published ref.
        fresh = bare_repository(self.base / "fresh.git")
        subprocess.run(["git", "--git-dir", str(fresh), "fetch", "-q", str(self.node),
                        "+" + LEDGER_REF + ":" + LEDGER_REF], check=True)
        with mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_GIT_DIR": str(fresh)}):
            verdict = consumer.readback(self.env.source, locator(fresh), result)
        self.assertEqual(verdict["disposition"], "VERIFIED", verdict)
        self.assertEqual([row["organization_readback"] for row in verdict["attempts"]], ["VERIFIED"])
        self.assertEqual(verdict["authority_effect"], "NONE_READBACK_ONLY")
        # A second event replays the retained grant; no fence is reissued, nothing is appended.
        tip = ref_tip(self.node)
        again = self.hosted(repo_ledger_root=locator(self.node))
        self.assertEqual(again["fencing_token"], 8)
        self.assertEqual(again["organization_receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(ref_tip(self.node), tip)

    def test_readback_refuses_a_receipt_absent_from_the_fetched_ref(self):
        result = self.hosted(repo_ledger_root=locator(self.node))
        stale = bare_repository(self.base / "stale.git")
        subprocess.run(["git", "--git-dir", str(stale), "fetch", "-q", str(self.node),
                        "+" + self.seeded + ":" + LEDGER_REF], check=True)
        with mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_GIT_DIR": str(stale)}):
            verdict = consumer.readback(self.env.source, locator(stale), result)
        self.assertEqual(verdict["disposition"], "FAIL_CLOSED")
        self.assertTrue(verdict["attempts"][0]["organization_readback"].startswith("REFUSED:"))
        self.assertEqual(verdict["retry_entrypoint"], consumer.EVENT_EPHEMERAL_ENTRYPOINT)

    def test_hosted_refusal_holds_for_an_explicit_posix_root(self):
        self.assertFalse(consumer.event_ephemeral_materialization(
            self.env.source, locator(self.node), self.base / "explicit-org"))
        self.assert_refused_before_anything(repo_ledger_root=locator(self.node),
                                            org_ledger_root=self.base / "explicit-org")

    def test_hosted_refusal_holds_for_a_posix_repository_root(self):
        self.assertFalse(consumer.event_ephemeral_materialization(self.env.source, self.env.repo, None))
        self.assert_refused_before_anything(repo_ledger_root=self.env.repo)
        self.assertFalse(self.env.repo.exists())

    def test_hosted_refusal_holds_for_a_repository_chain_off_the_declared_ref(self):
        other = locator(self.node, "refs/stegverse/another-ledger")
        self.assertFalse(consumer.event_ephemeral_materialization(self.env.source, other, None))
        self.assert_refused_before_anything(repo_ledger_root=other)

    # H46 fence-floor repair (Lane D, STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 D1).
    def fresh_runtime(self, name: str, *, source_claims: list | None = None):
        """A runtime with no preserved claim registry, as the hosted workflow materializes it."""
        env = custody_tests.Env(self.base / name, generation=None, seed=False,
                                org_ledger=self.base / "unused-org-root")
        if source_claims is not None:
            path = env.source / "control/claims-active.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["claims"] = source_claims
            path.write_text(json.dumps(state), encoding="utf-8")
        return env

    def consume_hosted(self, env, **kwargs):
        kwargs.setdefault("hb_epoch", CARRIER_HB_EPOCH)
        return consumer.consume(env.source, env.runtime, repo_ledger_root=locator(self.node), runner=self.runner,
                                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **HOSTED}, **kwargs)

    def test_committed_claims_registry_is_behind_the_issued_fences(self):
        committed = json.loads((ROOT / "control/claims-active.json").read_text(encoding="utf-8"))
        floor = consumer.provenance_floor(ROOT)
        self.assertLess(committed["generation"], floor["fence"])
        self.assertEqual(committed.get("claims") or [], [])

    def test_event_ephemeral_rematerializes_a_stale_empty_source_registry_from_the_chain(self):
        env = self.fresh_runtime("fresh")
        source_bytes = (env.source / "control/claims-active.json").read_bytes()
        result = self.consume_hosted(env)
        self.assertEqual(result["transition_class"], consumer.GRANTED, result)
        self.assertEqual(result["fencing_token"], 8)
        self.assertEqual(result["organization_readback"], "VERIFIED")
        custody = consumer.ledger_custody(env.source, locator(self.node), None, event_ephemeral=True)
        keys = custody["emitter"].ledger_store
        receipt = custody["repository_store"].get(keys.receipt_key(result["repository_receipt_sha256"]))
        evidence = receipt["evidence"]
        basis = evidence["runtime_claims_generation_rematerialized"]
        self.assertEqual(basis["basis"], consumer.FENCE_FLOOR_REMATERIALIZATION_BASIS)
        self.assertEqual((basis["source_generation"], basis["rematerialized_generation"]), (2, 7))
        self.assertEqual((basis["chain_max_fence"], basis["provenance_floor_fence"]), (0, 7))
        self.assertEqual(evidence["runtime_claims_generation_observed"], 7)
        # The committed source registry is never edited; only the ephemeral runtime projection moved.
        self.assertEqual((env.source / "control/claims-active.json").read_bytes(), source_bytes)
        # A later event derives the generation from the chain again: no fence is reissued.
        again = self.consume_hosted(self.fresh_runtime("fresh-again"))
        self.assertEqual(again["fencing_token"], 8)
        self.assertEqual(again["organization_receipt_sha256"], result["organization_receipt_sha256"])

    def test_source_registry_holding_claims_is_not_rematerialized(self):
        held = {"task_id": "TASK-2026-0007", "lease": {"fencing_token": 2}}
        env = self.fresh_runtime("held", source_claims=[held])
        result = self.consume_hosted(env)
        self.assertEqual(result["transition_class"], consumer.FAIL_CLOSED, result)
        self.assertNotIn("generation_basis", env.claims())
        self.assertEqual(env.claims()["generation"], 2)

    def test_every_event_ephemeral_non_allow_carries_the_six_fields(self):
        result = self.consume_hosted(self.fresh_runtime("held6", source_claims=[{"task_id": "TASK-2026-0007"}]))
        for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                      "owning_existing_goal", "next_attempt"):
            self.assertTrue(result.get(field), field)
        self.assertEqual(result["retry_entrypoint"], consumer.EVENT_EPHEMERAL_ENTRYPOINT)

    def test_preserved_runtime_registry_behind_the_fences_still_fails_closed(self):
        env = custody_tests.Env(self.base / "preserved", generation=2, seed=False,
                                org_ledger=self.base / "unused-org-root")
        result = self.consume_hosted(env)
        self.assertEqual(result["transition_class"], consumer.FAIL_CLOSED, result)
        self.assertEqual(result["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")

    def test_event_ephemeral_grant_without_carrier_epoch_fails_closed(self):
        env = self.fresh_runtime("no-epoch")
        result = self.consume_hosted(env, hb_epoch=None)
        self.assertEqual(result["transition_class"], consumer.FAIL_CLOSED, result)
        self.assertEqual(result["failed_predicate"], consumer.GRANT_EPOCH_NOT_CARRIER_SUPPLIED)
        for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                      "owning_existing_goal", "next_attempt"):
            self.assertTrue(result.get(field), field)
        self.assertEqual(result["retry_entrypoint"], consumer.EVENT_EPHEMERAL_ENTRYPOINT)
        self.assertFalse(result["fence_issued"])
        self.assertIsNone(result["fencing_token"])
        custody = consumer.ledger_custody(env.source, locator(self.node), None, event_ephemeral=True)
        self.assertEqual(consumer.chain_grants(consumer.verify_organization_chain(custody)), [])
        # The ephemeral runtime projection is restored; nothing was issued.
        self.assertEqual(env.claims()["generation"], 2)

    def test_event_ephemeral_grant_carries_the_carrier_epoch_not_a_clock_reference(self):
        env = self.fresh_runtime("carrier")
        result = self.consume_hosted(env, hb_epoch=CARRIER_HB_EPOCH)
        self.assertEqual(result["transition_class"], consumer.GRANTED, result)
        self.assertEqual(result["fencing_token"], 8)
        custody = consumer.ledger_custody(env.source, locator(self.node), None, event_ephemeral=True)
        org_keys = custody["organization_ledger"].ledger_store
        grant = custody["organization_store"].get(org_keys.receipt_key(result["organization_receipt_sha256"]))
        repository = custody["repository_store"].get(
            custody["emitter"].ledger_store.receipt_key(result["repository_receipt_sha256"]))
        for receipt in (grant, repository):
            self.assertEqual(receipt["hb_reference"]["epoch"], CARRIER_HB_EPOCH)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)

    def test_hosted_workflow_synthesizes_no_heartbeat_epoch(self):
        # The hosted path has no carrier, so it supplies no epoch and derives none;
        # its grants are FAIL_CLOSED GRANT_EPOCH_NOT_CARRIER_SUPPLIED until a carrier does.
        text = "".join((ROOT / rel).read_text(encoding="utf-8") for rel in (
            ".github/workflows/organization-claim-allocator-transition.yml",
            ".github/workflows/organization-claim-allocator-transition-writer.yml"))
        for forbidden in ("--hb-epoch", "date +%s", "hb_reference(", "time.time", "datetime.now"):
            self.assertNotIn(forbidden, text)

    def test_workflow_refusals_carry_the_six_fields(self):
        text = "".join((ROOT / rel).read_text(encoding="utf-8") for rel in (
            ".github/workflows/organization-claim-allocator-transition.yml",
            ".github/workflows/organization-claim-allocator-transition-writer.yml"))
        refusals = [json.loads(line.strip()[len("echo '"):-1]) for line in text.splitlines()
                    if line.strip().startswith("echo '{\"disposition\":\"FAIL_CLOSED\"")]
        # 4 publishing refusals (writer-only workflow) + 2 pull_request dry-run refusals (PR-facing).
        self.assertEqual(len(refusals), 6)
        for refusal in refusals:
            for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                          "owning_existing_goal", "next_attempt"):
                self.assertIn(field, refusal)

    def test_event_ephemeral_requires_the_repository_chain_on_the_declared_store(self):
        elsewhere = bare_repository(self.base / "elsewhere.git")
        with self.assertRaises(consumer.OrganizationLedgerNotAdmitted) as raised:
            consumer.ledger_custody(self.env.source, locator(elsewhere), None, event_ephemeral=True)
        self.assertEqual(raised.exception.predicate, "EVENT_EPHEMERAL_REPOSITORY_LEDGER_NOT_ON_DECLARED_REF")
        result = self.hosted(repo_ledger_root=locator(elsewhere))
        self.assertEqual(result["failed_predicate"], "EVENT_EPHEMERAL_REPOSITORY_LEDGER_NOT_ON_DECLARED_REF")
        self.assertEqual(self.calls, [])
        self.assertIsNone(ref_tip(elsewhere))
        self.assertEqual(ref_tip(self.node), self.seeded)

    def test_organization_pin_is_not_carried_over_a_foreign_move(self):
        custody = consumer.ledger_custody(self.env.source, locator(self.node), None, event_ephemeral=True)
        store = custody["organization_store"]
        tree = subprocess.run(["git", "--git-dir", str(self.node), "rev-parse", self.seeded + "^{tree}"],
                              capture_output=True, text=True, check=True).stdout.strip()
        foreign = subprocess.run(
            ["git", "--git-dir", str(self.node), "-c", "user.name=f", "-c", "user.email=f@f.invalid",
             "commit-tree", tree, "-p", self.seeded, "-m", "foreign"],
            capture_output=True, text=True, check=True).stdout.strip()
        with store.exclusive():
            subprocess.run(["git", "--git-dir", str(self.node), "update-ref", LEDGER_REF, foreign, self.seeded],
                           check=True)
            # One parent, the pinned snapshot, but not this transition's repository receipt.
            self.assertFalse(consumer.adopt_repository_append(custody, self.seeded, {"receipt_sha256": "sha256:" + "f" * 64}))
            self.assertEqual(store._snapshot(), self.seeded)

    def test_clean_env_relaxes_only_the_event_ephemeral_materialization(self):
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            consumer.clean_env({"PATH": "/bin", **HOSTED})
        env = consumer.clean_env({"PATH": "/bin", "SECRET": "x", **HOSTED}, event_ephemeral=True)
        self.assertEqual(env, {"PATH": "/bin", "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
                               "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE"})

    def test_event_ephemeral_workflow_is_wired_to_the_declared_ref(self):
        # The publishing steps live in the writer-only workflow (never pull_request).
        rel = ".github/workflows/organization-claim-allocator-transition-writer.yml"
        workflow = (ROOT / rel).read_text(encoding="utf-8")
        for needle in ("control/resident-execution-request.d/org-claim-allocator-*.json", "workflow_dispatch",
                       "group: organization-ledger", "cancel-in-progress: false", "contents: write",
                       "LEDGER_REF: refs/stegverse/organization-ledger",
                       "scripts/consume_org_claim_allocator_request.py",
                       '--repo-ledger-root "git+$GITHUB_WORKSPACE#$LEDGER_REF:$REPO_LEDGER_NAMESPACE"',
                       "git merge-base --is-ancestor", 'git push origin "$LEDGER_REF:$LEDGER_REF"',
                       "--readback-result"):
            self.assertIn(needle, workflow)
        # No explicit Organization root, no secret, no added credential.
        self.assertNotIn("--org-ledger-root", workflow)
        self.assertNotIn("secrets.", workflow)
        registry = json.loads((ROOT / "control/workflow-surface-registry.json").read_text(encoding="utf-8"))
        self.assertIn(rel, [entry["path"] for entry in registry["surfaces"]])


if __name__ == "__main__":
    unittest.main()


    def test_task8_scope_matches_current_iphone_projection_and_stays_nonoverlapping_with_task7(self):
        task7 = json.loads((ROOT / "tasks/TASK-2026-0007.json").read_text(encoding="utf-8"))
        task8 = json.loads((ROOT / "tasks/TASK-2026-0008.json").read_text(encoding="utf-8"))
        request7 = task7["requirements"]["mandatory"][0]
        request8 = task8["requirements"]["mandatory"][0]
        expected_paths = {
            "stegos-bootstrap/index.html",
            "stegos-bootstrap/stegos-bootstrap.js",
            "stegos-bootstrap/admitted-inference.js",
            "stegos-bootstrap/service-worker.js",
            "stegos-bootstrap/command-ingress.js",
            "stegos-bootstrap/command.html",
            "stegos-bootstrap/kv-readiness-persistence.js",
            "stegos-bootstrap/kv-session-persistence.js",
            "stegos-bootstrap/workercoordinator-portable-checkout.js",
            "stegos-bootstrap/workercoordinator-portable-adapter.js",
            "stegos-bootstrap/workercoordinator-portable-sv001.json",
            "stegos-bootstrap/workercoordinator-portable-authority-contract.json",
            "stegos-bootstrap/tvc-sv001-portable-lease.js",
            "stegos-bootstrap/tvc-sv001-portable-lease-package.json",
            "stegos-bootstrap/tvc-sv001-portable-tv-request.json",
            "stegos-bootstrap/tvc-sv001-portable-lease-policy.json",
            "stegos-bootstrap/tvc-sv001-portable-lease-state.schema.json",
            "docs/STEGOS_DE006_BOUND_INFERENCE_PROJECTION_MIRROR_HANDOFF.md",
            "scripts/check_stegos_de006_bound_inference_projection.py",
            "data/tasks/SITE-STEGOS-DE006-BOUND-INFERENCE-932.json",
        }
        self.assertEqual(set(request8["scope"]["paths"]), expected_paths)
        self.assertIn("stegverse.workercoordinator-portable-authority-contract/v1", request8["scope"]["contracts"])
        self.assertIn("stegverse.tvc.sv001-portable-lease-package/v1", request8["scope"]["contracts"])
        self.assertIn("portable-workercoordinator-checkout-publication", request8["scope"]["capabilities"])
        self.assertIn("portable-tvc-sv001-lease-input-publication", request8["scope"]["capabilities"])
        self.assertEqual(request8["scope"]["dependency_surfaces"], ["site:stegos-de006-bound-inference-publication"])
        self.assertFalse(allocator.conflicts(request8, request7))
