"""Organization claim custody: every allocation attempt is a retained transition.

Covers SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001 items S7-2a/b/c,
F024-03/04 and F24-01..03. Each test materializes its own source and runtime
roots and its own supplied ledger roots; nothing here reads or writes the
committed control files or any host-derived location.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


consumer = load_module("org_claim_custody_consumer", "scripts/consume_org_claim_allocator_request.py")
allocator = load_module("org_claim_custody_allocator", "scripts/allocate_claims.py")
dispatcher = load_module("org_claim_custody_dispatcher", "scripts/dispatch_resident_execution_requests.py")
bootstrap = load_module("org_claim_custody_bootstrap", "scripts/bootstrap_sovereign_runtime.py")

TARGETED_REL = Path("control/resident-execution-request.d/org-claim-allocator-sdk-manifest-001.json")
UNTARGETED_REL = Path("control/resident-execution-request.d/org-claim-allocator-001.json")
LEDGER_FILES = (
    ".stegverse/transition-ledger/emit.py",
    ".stegverse/transition-ledger/contract.json",
    ".stegverse/transition-ledger/org-contract.json",
    "org-kernel/kernel.py",
    "org-kernel/node_store.py",
    "resident-runtime/ledger_store.py",
    "resident-runtime/aggregate_repo_transition.py",
    "data/canonical-task-records/SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001.json",
    "control/claims-active.json",
    "control/queue.json",
)
PROTECTED = [f"TASK-2026-00{n:02d}" for n in range(7, 13)]


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Env:
    """One source checkout, one ephemeral runtime and the supplied ledger roots."""

    def __init__(self, base: Path, *, generation: int | None = 7, requests=(TARGETED_REL,),
                 org_ledger: Path | None = None, repo_ledger: Path | None = None, source: Path | None = None,
                 runtime_name: str = "runtime"):
        self.base = base
        self.source = source or base / "source"
        if source is None:
            (self.source / "tasks").mkdir(parents=True)
            for path in sorted((ROOT / "tasks").glob("TASK-*.json")):
                shutil.copy(path, self.source / "tasks" / path.name)
            for rel in LEDGER_FILES:
                (self.source / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, self.source / rel)
        self.runtime = base / runtime_name
        (self.runtime / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / consumer.ALLOCATOR_REL, self.runtime / consumer.ALLOCATOR_REL)
        for rel in requests:
            (self.runtime / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.runtime / rel)
        if generation is not None:
            (self.runtime / "control").mkdir(parents=True, exist_ok=True)
            (self.runtime / "control/claims-active.json").write_text(json.dumps(
                {"schema": "stegverse.org-claims/v1", "generation": generation, "claims": []}), encoding="utf-8")
        self.org = org_ledger or base / "org-ledger"
        self.org.mkdir(parents=True, exist_ok=True)
        self.repo = repo_ledger or base / f"{runtime_name}-repo-ledger"

    def consume(self, runner=subprocess.run, env=None, **kwargs):
        return consumer.consume(self.source, self.runtime, repo_ledger_root=kwargs.pop("repo", self.repo),
                                org_ledger_root=kwargs.pop("org", self.org), runner=runner,
                                env=env or {"PATH": os.environ.get("PATH", "/usr/bin:/bin")})

    def custody(self):
        return consumer.ledger_custody(self.source, self.repo, self.org)

    def chain(self):
        return consumer.verify_organization_chain(self.custody())

    def grants(self):
        return consumer.chain_grants(self.chain())

    def claims(self):
        return json.loads((self.runtime / "control/claims-active.json").read_text(encoding="utf-8"))

    def task(self, task_id):
        return json.loads((self.runtime / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))

    def seed_grant(self, task_id: str, fence: int):
        """Append a prior grant through the same custody path the consumer uses."""
        evidence = {"disposition": "ALLOW", "task_id": task_id, "fencing_token": fence,
                    "claim_scope_sha256": "0" * 64, "organization_head_sha256": None,
                    "cosv_task_vector": None, "request_sha256": None, "failed_predicate": None}
        return consumer.record_transition(
            self.custody(), consumer.GRANTED, f"ORGANIZATION-WORKER-CLAIM-GRANTED-{task_id}-G{fence}",
            "sha256:" + "1" * 64, evidence, organization=True,
            identity=("task_id", "fencing_token"))


class OrgClaimCustodyTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.base = Path(self._td.name)
        self.committed = {rel: sha_file(ROOT / rel) for rel in
                          ["control/claims-active.json", "control/queue.json",
                           *[f"tasks/{t}.json" for t in PROTECTED]]}

    def tearDown(self):
        # Nothing in this module may touch the committed control files.
        for rel, digest in self.committed.items():
            self.assertEqual(sha_file(ROOT / rel), digest, rel)
        self._td.cleanup()

    # S7-2b -----------------------------------------------------------------
    def test_manifest_targeted_claim_without_eligible_task_returns_typed_non_allow(self):
        task = json.loads((ROOT / "tasks/TASK-2026-0013.json").read_text(encoding="utf-8"))
        tasks = {"TASK-2026-0013": task, "TASK-2026-0007": {"task_id": "TASK-2026-0007", "status": "queued"}}
        self.assertEqual(allocator.evaluate_target("TASK-2026-0013", tasks, [])[1], None)
        self.assertEqual(allocator.evaluate_target("TASK-2026-9999", tasks, [])[1], "TARGET_TASK_NOT_QUEUED")
        self.assertEqual(allocator.evaluate_target(
            "TASK-2026-0013", {**tasks, "TASK-2026-0013": {**task, "status": "active"}}, [])[1], "TARGET_TASK_NOT_QUEUED")
        self.assertEqual(allocator.evaluate_target(
            "TASK-2026-0013", {**tasks, "TASK-2026-0013": {**task, "dependencies": ["TASK-2026-0007"]}}, [])[1],
            "DEPENDENCIES_INCOMPLETE")
        bare = json.loads(json.dumps(task))
        for request in bare["requirements"]["mandatory"]:
            request["scope"]["dependency_surfaces"] = []
        self.assertEqual(allocator.evaluate_target("TASK-2026-0013", {**tasks, "TASK-2026-0013": bare}, [])[1],
                         "NOT_ADMISSIBLE")
        held = dict(task["requirements"]["mandatory"][0], task_id="TASK-2026-0099")
        self.assertEqual(allocator.evaluate_target("TASK-2026-0013", tasks, [held])[1], "CONFLICTS_WITH_HELD_CLAIM")

        env = Env(self.base)
        (env.runtime / "control/claims-active.json").write_text(json.dumps(
            {"schema": "stegverse.org-claims/v1", "generation": 7, "claims": [held]}), encoding="utf-8")
        result = env.consume()
        self.assertEqual(result["disposition"], "DENY")
        self.assertEqual(result["transition_class"], "ORGANIZATION_WORKER_CLAIM_REFUSED")
        self.assertEqual(result["failed_predicate"], "CONFLICTS_WITH_HELD_CLAIM")
        self.assertIsNone(result["fencing_token"])
        self.assertTrue(result["organization_receipt_appended"])
        self.assertEqual(env.task("TASK-2026-0013")["status"], "queued")
        self.assertEqual(env.grants(), [])

    def _run_allocator_in_process(self, root: Path, argv: list[str]) -> str:
        fixed = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)

        class Frozen(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed

        patches = {"TASKS": root / "tasks", "CLAIMS_PATH": root / "control/claims-active.json",
                   "QUEUE_PATH": root / "control/queue.json", "EVENTS_PATH": root / "events/org-events.jsonl",
                   "LOCK_PATH": root / "control/claims-allocator.lock", "datetime": Frozen}
        out = io.StringIO()
        with mock.patch.multiple(allocator, **patches), contextlib.redirect_stdout(out):
            self.assertEqual(allocator.main(argv), 0)
        return out.getvalue()

    def test_untargeted_allocator_selection_semantics_unchanged(self):
        roots = []
        for name in ("untargeted", "targeted"):
            root = self.base / name
            shutil.copytree(ROOT / "tasks", root / "tasks", ignore=shutil.ignore_patterns("checkin-pending"))
            (root / "control").mkdir(parents=True)
            for rel in ("control/claims-active.json", "control/queue.json"):
                shutil.copy(ROOT / rel, root / rel)
            roots.append(root)
        plain = json.loads(self._run_allocator_in_process(roots[0], []))
        # Exactly today's result shape, ranking and generation step.
        self.assertEqual(list(plain), ["selected", "queued", "blocked_missing_dependency_declaration", "state",
                                       "authority_effect"])
        self.assertEqual(plain["selected"], "TASK-2026-0007")
        self.assertEqual(plain["queued"][-1], "TASK-2026-0013")
        claims = json.loads((roots[0] / "control/claims-active.json").read_text(encoding="utf-8"))
        self.assertEqual(claims["generation"], 3)
        # Targeting the task the ranking picked writes byte-identical state.
        targeted = json.loads(self._run_allocator_in_process(roots[1], ["--task", "TASK-2026-0007"]))
        self.assertEqual(targeted["selected"], "TASK-2026-0007")
        for rel in ("control/claims-active.json", "control/queue.json", "tasks/TASK-2026-0007.json",
                    "events/org-events.jsonl"):
            self.assertEqual((roots[0] / rel).read_bytes(), (roots[1] / rel).read_bytes(), rel)
        # A plan writes nothing.
        before = {p: p.read_bytes() for p in roots[1].rglob("*.json")}
        planned = json.loads(self._run_allocator_in_process(roots[1], ["--plan", "--task", "TASK-2026-0013"]))
        self.assertEqual(planned["state"], "ALLOCATION_PLANNED")
        self.assertEqual(planned["selected"], "TASK-2026-0013")
        self.assertEqual({p: p.read_bytes() for p in roots[1].rglob("*.json")}, before)

    # S7-2a / F024-03 / F24-01 ------------------------------------------------
    def test_no_duplicate_fence_across_ephemeral_rematerialization_and_retry(self):
        a = Env(self.base, generation=7)
        first = a.consume()
        self.assertEqual(first["disposition"], "ALLOW")
        self.assertEqual(first["fencing_token"], 8)
        # Same claim again from the same runtime.
        self.assertEqual(a.consume(), first)
        # A fresh ephemeral runtime materialized from the checkout (generation 2)
        # sharing the organization ledger replays the grant at its fence.
        b = Env(self.base, generation=None, source=a.source, org_ledger=a.org, runtime_name="runtime-b")
        replay = b.consume()
        self.assertEqual(replay["disposition"], "ALLOW")
        self.assertEqual(replay["fencing_token"], 8)
        self.assertTrue(replay["replayed_prior_grant"])
        self.assertEqual(replay["organization_receipt_sha256"], first["organization_receipt_sha256"])
        self.assertEqual(b.claims()["generation"], 8)
        # An untargeted fresh runtime behind the issued fences issues nothing.
        c = Env(self.base, generation=None, requests=(UNTARGETED_REL,), source=a.source, org_ledger=a.org,
                runtime_name="runtime-c")
        behind = c.consume()
        self.assertEqual(behind["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")
        self.assertEqual(c.claims()["generation"], 2)
        fences = [row["boundary_evidence"]["fencing_token"] for row in a.grants()]
        self.assertEqual(fences, [8])

    def test_ledger_head_unknown_cannot_issue_next_fence(self):
        cases = {}
        absent = Env(self.base / "absent")
        shutil.rmtree(absent.org)
        cases["absent"] = absent
        orphan = Env(self.base / "orphan")
        (orphan.org / "receipts").mkdir()
        (orphan.org / "receipts/deadbeef.json").write_text("{}", encoding="utf-8")
        cases["orphan"] = orphan
        tampered = Env(self.base / "tampered")
        tampered.seed_grant("TASK-2026-9999", 9)
        receipt = next((tampered.org / "receipts").glob("*.json"))
        row = json.loads(receipt.read_text(encoding="utf-8"))
        row["boundary_evidence"]["fencing_token"] = 1
        receipt.write_text(json.dumps(row), encoding="utf-8")
        cases["tampered"] = tampered
        for name, env in cases.items():
            result = env.consume()
            self.assertEqual(result["disposition"], "FAIL_CLOSED", name)
            self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_UNVERIFIED", name)
            self.assertFalse(result["fence_issued"], name)
            self.assertFalse(result["organization_receipt_appended"], name)
            self.assertEqual(env.claims()["generation"], 7, name)
            self.assertEqual(env.task("TASK-2026-0013")["status"], "queued", name)
        # Not supplied at all: refused before anything is materialized.
        bare = Env(self.base / "unsupplied")
        refused = consumer.consume(bare.source, bare.runtime, env={"PATH": "/bin"})
        self.assertEqual(refused["failed_predicate"], "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertFalse((bare.runtime / "tasks").exists())

    def test_floor7_does_not_replace_verified_org_head(self):
        env = Env(self.base, generation=9)
        env.seed_grant("TASK-2026-9999", 9)
        result = env.consume()
        self.assertEqual(result["fencing_token"], 10)
        self.assertNotEqual(result["fencing_token"], 8)
        behind = Env(self.base / "behind", generation=8)
        behind.seed_grant("TASK-2026-9999", 9)
        self.assertEqual(behind.consume()["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")

    def test_same_claim_retry_returns_exact_prior_receipt(self):
        env = Env(self.base)
        first = env.consume()
        receipts_before = sorted(p.name for p in (env.org / "receipts").glob("*.json"))
        second = env.consume()
        self.assertEqual(second, first)
        self.assertEqual(sorted(p.name for p in (env.org / "receipts").glob("*.json")), receipts_before)
        self.assertEqual(env.claims()["generation"], 8)
        record = env.runtime / consumer.CONSUMPTION_DIR / f"{first['transition_id']}.json"
        self.assertEqual(json.loads(record.read_text(encoding="utf-8")), first)

    def test_denied_and_failed_claims_retain_immutable_disposition(self):
        env = Env(self.base, generation=7)
        held = dict(json.loads((ROOT / "tasks/TASK-2026-0013.json").read_text())["requirements"]["mandatory"][0],
                    task_id="TASK-2026-0099")
        (env.runtime / "control/claims-active.json").write_text(json.dumps(
            {"schema": "stegverse.org-claims/v1", "generation": 7, "claims": [held]}), encoding="utf-8")
        denied = env.consume()
        self.assertEqual(denied, env.consume())
        record = env.runtime / consumer.CONSUMPTION_DIR / f"{denied['transition_id']}.json"
        with self.assertRaisesRegex(RuntimeError, "write_once_collision"):
            consumer.write_once(record, {**denied, "disposition": "ALLOW"})
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["disposition"], "DENY")
        failed_env = Env(self.base / "failed", generation=3)
        failed = failed_env.consume()
        self.assertEqual(failed["disposition"], "FAIL_CLOSED")
        self.assertEqual(failed, failed_env.consume())
        refused = [row for row in env.chain()["receipts"]
                   if row["boundary_evidence"]["operation"] == "ORGANIZATION_WORKER_CLAIM_REFUSED"]
        self.assertEqual(len(refused), 1)
        projection = json.loads((env.runtime / consumer.RECEIPT_REL).read_text(encoding="utf-8"))
        self.assertTrue(projection["projection_only"])

    def test_claim_organization_receipt_precedes_task_active_projection(self):
        env = Env(self.base)
        observed = []

        def runner(command, **kwargs):
            if "--fencing-token" in command:
                grants = env.grants()
                observed.append((len(grants), env.task("TASK-2026-0013")["status"], env.claims()["generation"]))
            return subprocess.run(command, **kwargs)

        result = env.consume(runner=runner)
        self.assertEqual(observed, [(1, "queued", 7)])
        self.assertEqual(env.task("TASK-2026-0013")["status"], "active")
        self.assertTrue(result["organization_receipt_precedes_projection"])

    def test_task_0007_0012_preserved_without_unauthorized_status_change(self):
        env = Env(self.base)
        result = env.consume()
        self.assertEqual(result["claim_task_id"], "TASK-2026-0013")
        for task_id in PROTECTED:
            source = json.loads((ROOT / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))
            runtime = env.task(task_id)
            if task_id == "TASK-2026-0011":
                # The only change is the supersession TASK-2026-0012 declares.
                self.assertEqual(runtime["status"], "proposed")
                self.assertIn("superseded", runtime["flags"])
                runtime = {k: v for k, v in runtime.items() if k != "flags"}
                runtime["status"] = source["status"]
            self.assertEqual(runtime, source, task_id)
        self.assertEqual({c["task_id"] for c in env.claims()["claims"]}, {"TASK-2026-0013"})

    def test_no_host_clock_or_host_path_affects_governed_claim_or_answer(self):
        answers = []
        for name, stamp in (("one", "1999-01-01"), ("two", "2041-06-30")):
            env = Env(self.base / name)
            home = self.base / name / "home"
            host = {"PATH": os.environ.get("PATH", "/bin"), "HOME": str(home),
                    "XDG_STATE_HOME": str(home / "state"), "XDG_CONFIG_HOME": str(home / "config"),
                    "LOCALAPPDATA": str(home / "local"), "TZ": stamp}
            result = env.consume(env=host)
            self.assertFalse(home.exists())
            evidence = env.grants()[0]["boundary_evidence"]
            answers.append(({k: result[k] for k in ("disposition", "transition_id", "fencing_token",
                                                     "claim_scope_sha256", "cosv_task_vector",
                                                     "organization_head_sha256")}, evidence))
        self.assertEqual(answers[0], answers[1])
        text = (ROOT / "scripts/consume_org_claim_allocator_request.py").read_text(encoding="utf-8")
        for forbidden in ("Path.home", "XDG_STATE_HOME", "LOCALAPPDATA", "datetime.now", "time.time"):
            self.assertNotIn(forbidden, text)

    def test_workflow_allocator_runner_local_no_persisted_authority(self):
        text = (ROOT / ".github/workflows/org-control-plane-validate.yml").read_text(encoding="utf-8")
        self.assertIn("permissions: {}", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("--org-ledger-root", text)
        self.assertNotIn("STEGVERSE_ORG_LEDGER_ROOT", text)
        root = self.base / "runner"
        shutil.copytree(ROOT / "tasks", root / "tasks", ignore=shutil.ignore_patterns("checkin-pending"))
        (root / "control").mkdir(parents=True)
        for rel in ("control/claims-active.json", "control/queue.json"):
            shutil.copy(ROOT / rel, root / rel)
        self._run_allocator_in_process(root, [])
        # The bare allocator writes runner-local projection only: no ledger, no receipt.
        written = {p.relative_to(root).parts[0] for p in root.rglob("*") if p.is_file()}
        self.assertEqual(written, {"tasks", "control", "events"})

    def test_resident_request_is_not_claim_authority(self):
        for rel in (UNTARGETED_REL, TARGETED_REL):
            value = json.loads((ROOT / rel).read_text(encoding="utf-8"))
            self.assertFalse(value["request_grants_claim_authority"])
            self.assertTrue(value["allocator_remains_claim_authority"])
            self.assertEqual(value["authority_effect"], "NONE_REQUEST_ONLY")
            consumer.validate_request(value)
            with self.assertRaisesRegex(RuntimeError, "may not grant claim authority"):
                consumer.validate_request({**value, "request_grants_claim_authority": True})
        env = Env(self.base)
        result = env.consume()
        self.assertFalse(result["request_granted_claim_authority"])
        self.assertTrue(result["allocator_remains_claim_authority"])
        self.assertEqual(result["transition_class"], "ORGANIZATION_WORKER_CLAIM_GRANTED")

    def test_claim_generation_reconciles_from_organization_receipts_not_checkout_projection(self):
        env = Env(self.base, generation=None)
        env.seed_grant("TASK-2026-9999", 8)
        result = env.consume()
        # The checkout projection says generation 2; it never yields fence 3.
        self.assertEqual(result["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")
        self.assertEqual(env.claims()["generation"], 2)
        ahead = Env(self.base / "ahead", generation=8)
        ahead.seed_grant("TASK-2026-9999", 8)
        self.assertEqual(ahead.consume()["fencing_token"], 9)

    def test_task_claim_cannot_reuse_task_2026_0011_fence7(self):
        env = Env(self.base, generation=7)
        self.assertEqual(env.consume()["fencing_token"], 8)
        low = Env(self.base / "low", generation=6)
        self.assertEqual(low.consume()["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")
        # The floor is read from its provenance record, not hardcoded.
        moved = Env(self.base / "moved", generation=11)
        floor_path = moved.source / "tasks/TASK-2026-0012.json"
        value = json.loads(floor_path.read_text(encoding="utf-8"))
        value["predecessor_provenance"]["allocator_fence"] = 11
        floor_path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(moved.consume()["fencing_token"], 12)

    def test_task_scope_registry_home_not_claim_target(self):
        record = json.loads((ROOT / "data/canonical-task-records/"
                             "SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001.json").read_text(encoding="utf-8"))
        task = json.loads((ROOT / "tasks/TASK-2026-0013.json").read_text(encoding="utf-8"))
        self.assertEqual(record["registry_home"], "StegVerse-Labs/.github")
        self.assertEqual(record["targets"]["repositories"], ["StegVerse-org/.github", "StegVerse-org/StegVerse-SDK"])
        self.assertNotIn(record["registry_home"], record["targets"]["repositories"])
        self.assertEqual(record["allocator_projection"]["task_id"], "TASK-2026-0013")
        self.assertEqual(record["cosv_task_vector"], "71000000100126")
        claimed = [r["repository"]["full_name"] for r in task["requirements"]["mandatory"]]
        self.assertEqual(claimed, record["targets"]["repositories"])
        self.assertNotIn("supersedes", task)
        self.assertEqual(task["canonical_task_record"],
                         "data/canonical-task-records/SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001.json")
        for request in task["requirements"]["mandatory"]:
            self.assertEqual(request["scope"]["dependency_surfaces"],
                             ["stegverse-org:manifest-route-transition-disposition"])

    def test_claim_receipt_binds_exact_task_cosv_scope_and_org_head(self):
        env = Env(self.base, generation=9)
        env.seed_grant("TASK-2026-9999", 9)
        head = env.chain()["head_sha256"]
        result = env.consume()
        evidence = env.grants()[-1]["boundary_evidence"]
        task = json.loads((ROOT / "tasks/TASK-2026-0013.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["task_id"], "TASK-2026-0013")
        self.assertEqual(evidence["cosv_task_vector"], "71000000100126")
        self.assertEqual(evidence["claim_scope_sha256"], consumer.stable_hash(task["requirements"]["mandatory"]))
        self.assertEqual(evidence["organization_head_sha256"], head)
        self.assertEqual(evidence["fencing_token"], 10)
        self.assertEqual(result["transition_id"], "ORGANIZATION-WORKER-CLAIM-GRANTED-TASK-2026-0013-G10")
        source = json.loads(next(
            p for p in (env.org / "source-receipts").glob("*.json")
            if json.loads(p.read_text())["transition_id"] == result["transition_id"]).read_text())
        self.assertEqual(source["evidence"]["chain_max_fence"], 9)
        self.assertEqual(source["evidence"]["provenance_floor"]["fence"], 7)

    def test_failed_attempt_yields_actionable_fail_closed_with_predicate(self):
        env = Env(self.base, generation=3)
        result = env.consume()
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["transition_class"], "ORGANIZATION_WORKER_CLAIM_FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")
        self.assertTrue(result["required_evidence_or_repair"])
        self.assertEqual(result["retry_entrypoint"], consumer.RETRY_ENTRYPOINT)
        self.assertTrue(result["organization_receipt_appended"])
        row = env.chain()["receipts"][-1]
        self.assertEqual(row["boundary_evidence"]["disposition"], "FAIL_CLOSED")
        self.assertEqual(row["boundary_evidence"]["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")
        self.assertEqual(env.claims()["generation"], 3)

    def test_empty_verified_chain_uses_floor_plus_one_and_cites_provenance(self):
        env = Env(self.base, generation=7)
        self.assertEqual(env.chain(), {"head_sha256": None, "receipts": []})
        result = env.consume()
        self.assertEqual(result["fencing_token"], 8)
        source = json.loads(next((env.org / "source-receipts").glob("*.json")).read_text())
        floor = source["evidence"]["provenance_floor"]
        self.assertEqual(floor["fence"], 7)
        self.assertEqual(floor["provenance"], "tasks/TASK-2026-0012.json#predecessor_provenance.allocator_fence")
        self.assertEqual(floor["allocator_task"], "TASK-2026-0011")
        self.assertEqual(source["evidence"]["chain_max_fence"], 0)
        self.assertIsNone(source["evidence"]["organization_head_sha256"])

    # F024-04 / A6 ------------------------------------------------------------
    def test_dispatcher_does_not_forward_host_location_variables(self):
        values = {"PATH": "/bin", "XDG_STATE_HOME": "/s", "XDG_CONFIG_HOME": "/c", "LOCALAPPDATA": "/l",
                  "STEGVERSE_ORG_LEDGER_ROOT": "/org", "STEGVERSE_REPO_LEDGER_ROOT": "/repo"}
        clean = dispatcher.clean_exec_env(values)
        for name in ("XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA"):
            self.assertNotIn(name, clean)
        runtime = self.base / "runtime"
        (runtime / "scripts").mkdir(parents=True)
        (runtime / "scripts/consume_org_claim_allocator_request.py").write_text("# consumer\n", encoding="utf-8")
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs["env"]))
            return subprocess.CompletedProcess(command, 0, stdout='{"state":"NO_REQUEST"}\n', stderr="")

        dispatcher.dispatch(ROOT, runtime, runner=runner, env=values, only_consumers=("org_claim_allocator",))
        command, child_env = calls[0]
        self.assertEqual(command[command.index("--repo-ledger-root") + 1], "/repo")
        self.assertEqual(command[command.index("--org-ledger-root") + 1], "/org")
        for name in ("XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA"):
            self.assertNotIn(name, child_env)

    def test_bootstrap_requires_supplied_runtime_root(self):
        for env in ({}, {"HOME": "/h", "XDG_STATE_HOME": "/s", "LOCALAPPDATA": "/l"}):
            with self.assertRaisesRegex(RuntimeError, "runtime_location_required_from_materializer"):
                bootstrap.default_runtime_root(env)
        self.assertEqual(bootstrap.default_runtime_root({"STEGVERSE_HEARTBEAT_ROOT": str(self.base)}),
                         self.base.resolve())
        text = (ROOT / "scripts/bootstrap_sovereign_runtime.py").read_text(encoding="utf-8")
        body = text[text.index("def default_runtime_root("):text.index("def default_node_marker(")]
        for forbidden in ("XDG_STATE_HOME", "LOCALAPPDATA", "Library", ".local", "Path.home"):
            self.assertNotIn(forbidden, body)


if __name__ == "__main__":
    unittest.main()
