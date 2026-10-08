"""Organization claim custody: every allocation attempt is a retained transition.

Covers SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001 items S7-2a/b/c,
F024-03/04, F24-01..03 and R27-01..03. Each test materializes its own source and runtime
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


def seed_rooted_chain(source: Path, org_root: Path, repo_root: Path) -> dict:
    """Root the organization chain with a prior recorded refusal, through the existing emitters.

    No genesis is synthesized: the root is an ordinary DENY transition appended
    by the repository emitter and consumed by the organization aggregation.
    """
    custody = consumer.ledger_custody(source, repo_root, org_root)
    evidence = {"disposition": "DENY", "task_id": "NONE", "request_sha256": "0" * 64,
                "failed_predicate": "NO_ELIGIBLE_TASK", "fencing_token": None, "fence_issued": False,
                "organization_head_sha256": None, "consequence_committed": False}
    return consumer.record_transition(
        custody, consumer.REFUSED, "ORGANIZATION-WORKER-CLAIM-REFUSED-prior-attempt",
        "sha256:" + "0" * 64, evidence, organization=True,
        identity=("task_id", "request_sha256", "failed_predicate"))


class Env:
    """One source checkout, one ephemeral runtime and the supplied ledger roots."""

    def __init__(self, base: Path, *, generation: int | None = 7, requests=(TARGETED_REL,),
                 org_ledger: Path | None = None, repo_ledger: Path | None = None, source: Path | None = None,
                 runtime_name: str = "runtime", seed: bool = True):
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
        (self.org / "receipts").mkdir(parents=True, exist_ok=True)
        self.repo = repo_ledger or base / f"{runtime_name}-repo-ledger"
        if org_ledger is None and seed:
            # A non-empty chain rooted by a prior transition; an empty one never mints.
            seed_rooted_chain(self.source, self.org, base / f"{runtime_name}-seed-repo-ledger")

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
        orphan = Env(self.base / "orphan", seed=False)
        (orphan.org / "receipts").mkdir(exist_ok=True)
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
            self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED", name)
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
        refused = [row for row in env.chain()["receipts"][1:]  # after the seeded root
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
        template = None
        for name, stamp in (("one", "1999-01-01"), ("two", "2041-06-30")):
            env = Env(self.base / name, seed=template is None)
            if template is None:
                template = self.base / "seeded-org-ledger"
                shutil.copytree(env.org, template)
            else:
                # The same rooted chain, so the organization head is the same input.
                shutil.rmtree(env.org)
                shutil.copytree(template, env.org)
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
        value["predecessor_provenance"]["allocator_generation"] = 11
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

    def test_rooted_chain_without_grants_uses_floor_plus_one_and_cites_provenance(self):
        env = Env(self.base, generation=7)
        head = env.chain()["head_sha256"]
        self.assertEqual(env.grants(), [])
        result = env.consume()
        self.assertEqual(result["fencing_token"], 8)
        source = json.loads(next(
            p for p in (env.org / "source-receipts").glob("*.json")
            if json.loads(p.read_text())["transition_id"] == result["transition_id"]).read_text())
        floor = source["evidence"]["provenance_floor"]
        self.assertEqual(floor["fence"], 7)
        self.assertEqual(floor["provenance"], "tasks/TASK-2026-0012.json#predecessor_provenance.allocator_fence")
        self.assertEqual(floor["allocator_task"], "TASK-2026-0011")
        self.assertEqual(source["evidence"]["chain_max_fence"], 0)
        self.assertEqual(source["evidence"]["organization_head_sha256"], head)

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

    # RESPONSE-026 acceptance guards ------------------------------------------
    def test_empty_directory_or_unvalidated_head_cannot_issue_fence(self):
        empty = Env(self.base / "empty", seed=False)
        shutil.rmtree(empty.org / "receipts")
        dangling = Env(self.base / "dangling", seed=False)
        (dangling.org / "HEAD.json").write_text(json.dumps(
            {"organization": "StegVerse-Labs", "receipt_sha256": "sha256:" + "a" * 64}), encoding="utf-8")
        foreign = Env(self.base / "foreign")
        foreign.seed_grant("TASK-2026-9999", 9)
        head = json.loads((foreign.org / "HEAD.json").read_text())
        (foreign.org / "HEAD.json").write_text(json.dumps({**head, "organization": "StegVerse-org"}), encoding="utf-8")
        for name, env in (("empty", empty), ("dangling", dangling), ("foreign", foreign)):
            result = env.consume()
            self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED", name)
            self.assertFalse(result["fence_issued"], name)
            self.assertFalse(result["organization_receipt_appended"], name)
            self.assertEqual(env.claims()["generation"], 7, name)

    def test_missing_or_conflicting_predecessor_claim_evidence_fails_closed(self):
        missing = Env(self.base / "missing")
        (missing.source / "tasks/TASK-2026-0012.json").unlink()
        inconsistent = Env(self.base / "inconsistent")
        path = inconsistent.source / "tasks/TASK-2026-0012.json"
        value = json.loads(path.read_text())
        value["predecessor_provenance"]["allocator_generation"] = 6
        path.write_text(json.dumps(value), encoding="utf-8")
        unrecorded = Env(self.base / "unrecorded")
        (unrecorded.runtime / consumer.GRANT_DIR).mkdir(parents=True)
        (unrecorded.runtime / consumer.GRANT_DIR / "TASK-2026-0009-G9.json").write_text(json.dumps(
            {"task_id": "TASK-2026-0009", "fencing_tokens": [9]}), encoding="utf-8")
        stolen = Env(self.base / "stolen")
        (stolen.runtime / consumer.GRANT_DIR).mkdir(parents=True)
        (stolen.runtime / consumer.GRANT_DIR / "TASK-2026-0008-G7.json").write_text(json.dumps(
            {"task_id": "TASK-2026-0008", "fencing_tokens": [7]}), encoding="utf-8")
        cited = Env(self.base / "cited")
        cited.seed_grant("TASK-2026-9999", 9)
        (cited.runtime / consumer.GRANT_DIR).mkdir(parents=True)
        (cited.runtime / consumer.GRANT_DIR / "TASK-2026-9999-G9.json").write_text(json.dumps(
            {"task_id": "TASK-2026-9999", "fencing_tokens": [9],
             "organization_receipt_sha256": "sha256:" + "b" * 64}), encoding="utf-8")
        for name, env in (("missing", missing), ("inconsistent", inconsistent), ("unrecorded", unrecorded),
                          ("stolen", stolen), ("cited", cited)):
            result = env.consume()
            self.assertEqual(result["disposition"], "FAIL_CLOSED", name)
            self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED", name)
            self.assertFalse(result["fence_issued"], name)
            self.assertEqual(env.task("TASK-2026-0013")["status"], "queued", name)
        # The predecessor's own fence in its own evidence is consistent history.
        own = Env(self.base / "own")
        (own.runtime / consumer.GRANT_DIR).mkdir(parents=True)
        (own.runtime / consumer.GRANT_DIR / "TASK-2026-0011-G7.json").write_text(json.dumps(
            {"task_id": "TASK-2026-0011", "fencing_tokens": [7],
             "provenance_floor_sha256": sha_file(own.source / "tasks/TASK-2026-0012.json")}), encoding="utf-8")
        self.assertEqual(own.consume()["fencing_token"], 8)
        # A runtime registry ahead of the verified history is not a new origin.
        ahead = Env(self.base / "ahead", generation=9)
        self.assertEqual(ahead.consume()["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED")

    def test_replay_returns_exact_receipt_without_second_fence(self):
        env = Env(self.base)
        first = env.consume()
        head = env.chain()["head_sha256"]
        for _ in range(3):
            self.assertEqual(env.consume(), first)
        self.assertEqual(env.chain()["head_sha256"], head)
        self.assertEqual([r["boundary_evidence"]["fencing_token"] for r in env.grants()], [8])

    def test_concurrent_materialization_cannot_duplicate_fence(self):
        import threading
        first = Env(self.base, runtime_name="runtime-a")
        second = Env(self.base, source=first.source, org_ledger=first.org, runtime_name="runtime-b")
        request_path = second.runtime / TARGETED_REL
        request = json.loads(request_path.read_text())
        request["target_task_id"] = "TASK-2026-0007"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        barrier = threading.Barrier(2)
        results = {}

        def run(name, env):
            barrier.wait()
            results[name] = env.consume()

        threads = [threading.Thread(target=run, args=(n, e)) for n, e in (("a", first), ("b", second))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(120)
        fences = [row["boundary_evidence"]["fencing_token"] for row in first.grants()]
        self.assertEqual(fences, [8])
        self.assertEqual(sorted(r["disposition"] for r in results.values()), ["ALLOW", "FAIL_CLOSED"])
        loser = next(r for r in results.values() if r["disposition"] == "FAIL_CLOSED")
        self.assertEqual(loser["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")

    def test_organization_receipt_precedes_active_projection(self):
        self.test_claim_organization_receipt_precedes_task_active_projection()

    def test_target_selector_does_not_bypass_admissibility(self):
        env = Env(self.base)
        path = env.source / "tasks/TASK-2026-0013.json"
        value = json.loads(path.read_text())
        for request in value["requirements"]["mandatory"]:
            request["scope"]["dependency_surfaces"] = []
        path.write_text(json.dumps(value), encoding="utf-8")
        request_path = env.runtime / TARGETED_REL
        request = json.loads(request_path.read_text())
        request["source_catalog_floor"]["task_id"] = "TASK-2026-0012"
        request["source_catalog_floor"]["requested_at"] = "2026-09-13T23:40:00Z"
        request["source_catalog_floor"]["repository_full_name"] = "StegVerse-Labs/Site"
        request["source_catalog_floor"]["required_dependency_surface"] = "site:current-iphone-kv-testflight-static-bootstrap"
        task12 = json.loads((ROOT / "tasks/TASK-2026-0012.json").read_text())
        request["source_catalog_floor"]["scope_sha256"] = consumer.stable_hash(
            task12["requirements"]["mandatory"][0]["scope"])
        request_path.write_text(json.dumps(request), encoding="utf-8")
        result = env.consume()
        self.assertEqual(result["disposition"], "DENY")
        self.assertEqual(result["failed_predicate"], "NOT_ADMISSIBLE")
        self.assertEqual(env.grants(), [])
        self.assertEqual(env.task("TASK-2026-0013")["status"], "queued")

    def test_no_host_derived_runtime_root_or_external_machine_gate(self):
        with self.assertRaisesRegex(RuntimeError, "runtime_location_required_from_materializer"):
            bootstrap.default_runtime_root({"HOME": "/h", "XDG_STATE_HOME": "/s"})
        text = (ROOT / "scripts/consume_org_claim_allocator_request.py").read_text(encoding="utf-8")
        for forbidden in ("urllib", "import socket", "import requests", "http://", "https://", "time.sleep", "Path.home"):
            self.assertNotIn(forbidden, text)
        for rel in (UNTARGETED_REL, TARGETED_REL):
            value = json.loads((ROOT / rel).read_text())
            self.assertFalse(value["second_machine_required"])
            self.assertFalse(value["heartbeat_grants_execution_authority"])
            self.assertFalse(value["network_source_fetch_allowed"])
        result = Env(self.base).consume()
        self.assertFalse(result["second_machine_required"])
        self.assertFalse(result["network_source_fetch_performed"])

    def test_all_attempted_actions_are_manifest_bound_and_terminally_dispositioned(self):
        allow = Env(self.base / "allow")
        deny = Env(self.base / "deny")
        held = dict(json.loads((ROOT / "tasks/TASK-2026-0013.json").read_text())["requirements"]["mandatory"][0],
                    task_id="TASK-2026-0099")
        (deny.runtime / "control/claims-active.json").write_text(json.dumps(
            {"schema": "stegverse.org-claims/v1", "generation": 7, "claims": [held]}), encoding="utf-8")
        failed = Env(self.base / "failed", generation=3)
        for env, disposition in ((allow, "ALLOW"), (deny, "DENY"), (failed, "FAIL_CLOSED")):
            result = env.consume()
            request_sha = consumer.stable_hash(json.loads((env.runtime / TARGETED_REL).read_text()))
            self.assertEqual(result["disposition"], disposition)
            self.assertEqual(result["request_sha256"], request_sha)
            store = env.custody()["repository_store"]
            receipts = [store.get(key) for key in store.list_prefix("receipts/")]
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]["evidence"]["disposition"], disposition)
            self.assertEqual(receipts[0]["evidence"]["request_sha256"], request_sha)
            self.assertEqual(receipts[0]["transition_class"],
                             {"ALLOW": consumer.GRANTED, "DENY": consumer.REFUSED,
                              "FAIL_CLOSED": consumer.FAIL_CLOSED}[disposition])
            org_rows = env.chain()["receipts"][1:]  # after the seeded root
            self.assertEqual([r["boundary_evidence"]["disposition"] for r in org_rows], [disposition])
            records = list((env.runtime / consumer.CONSUMPTION_DIR).glob("*.json"))
            self.assertEqual(len(records), 1)
            self.assertIn(json.loads(records[0].read_text())["state"], {"ATTEMPT_RECORDED", "FAIL_CLOSED"})

    def test_source_CI_never_promoted_to_runtime(self):
        env = Env(self.base)
        outputs = [json.dumps(env.consume(), sort_keys=True)]
        outputs += [p.read_text() for p in env.runtime.rglob("*.json") if "receipts" in p.parts]
        outputs += [p.read_text() for p in env.org.rglob("*.json")]
        for rel in ("scripts/consume_org_claim_allocator_request.py", "scripts/allocate_claims.py",
                    "tasks/TASK-2026-0013.json", str(TARGETED_REL)):
            outputs.append((ROOT / rel).read_text(encoding="utf-8"))
        for text in outputs:
            self.assertNotIn("SANDBOX_RUNTIME_OBSERVED", text)
            self.assertNotIn('"runtime_observed": true', text)
            self.assertNotIn('"runtime_execution_inferred": true', text)
        record = json.loads((ROOT / "data/canonical-task-records/"
                             "SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001.json").read_text())
        self.assertEqual(record["completion"], {"claimed": False, "validated": False, "runtime_observed": False})
        self.assertFalse(json.loads((ROOT / "tasks/TASK-2026-0013.json").read_text())
                         ["authority"]["runtime_execution_inferred"])


    # R27-01 / RESPONSE-029 ---------------------------------------------------
    def _assert_unverified_without_fence(self, env, result, name):
        self.assertEqual(result["disposition"], "FAIL_CLOSED", name)
        self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED", name)
        self.assertFalse(result["fence_issued"], name)
        self.assertFalse(result["organization_receipt_appended"], name)
        self.assertEqual(env.claims()["generation"], 7, name)
        self.assertEqual(env.task("TASK-2026-0013")["status"], "queued", name)

    def test_nonempty_hash_chain_without_credential_not_authentic_custody(self):
        env = Env(self.base)
        self.assertEqual(env.chain()["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")
        result = env.consume()
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")
        # The allocator, not the chain, remains the only claim authority.
        self.assertEqual(result["authority_effect"], "CANONICAL_ALLOCATOR_ONLY_IF_SELECTED")
        self.assertTrue(result["allocator_remains_claim_authority"])
        org_evidence = env.grants()[-1]["boundary_evidence"]
        self.assertEqual(org_evidence["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")
        store = env.custody()["repository_store"]
        repo = [store.get(k) for k in store.list_prefix("receipts/")]
        self.assertEqual([r["evidence"]["custody_authentication"] for r in repo
                          if r["transition_class"] == consumer.GRANTED], ["HASH_CHAIN_CONTINUITY_ONLY"])
        retained = json.loads((env.runtime / result["claim_grant_evidence"]["generation_receipt"]).read_text())
        self.assertEqual(retained["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")
        self.assertEqual(result["claim_grant_evidence"]["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")
        outputs = [json.dumps(result)] + [p.read_text() for p in env.org.rglob("*.json")]
        outputs += [p.read_text() for p in env.runtime.rglob("*.json") if "receipts" in p.parts]
        outputs.append((ROOT / "scripts/consume_org_claim_allocator_request.py").read_text(encoding="utf-8"))
        for text in outputs:
            self.assertNotIn("AUTHENTIC_ORGANIZATION_CUSTODY", text)
        # A grant labelled as anything more than continuity is refused.
        overstated = Env(self.base / "overstated", generation=9)
        custody = overstated.custody()
        consumer.record_transition(
            custody, consumer.GRANTED, "ORGANIZATION-WORKER-CLAIM-GRANTED-TASK-2026-9999-G9", "sha256:" + "1" * 64,
            {"disposition": "ALLOW", "task_id": "TASK-2026-9999", "fencing_token": 9, "claim_scope_sha256": "0" * 64,
             "custody_authentication": "AUTHENTIC_" + "ORGANIZATION_CUSTODY"},
            organization=True, identity=("task_id", "fencing_token"))
        refused = overstated.consume()
        self.assertEqual(refused["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED")
        self.assertFalse(refused["fence_issued"])

    def test_empty_chain_claim_refused_without_dummy_genesis(self):
        env = Env(self.base, seed=False)
        result = env.consume()
        self._assert_unverified_without_fence(env, result, "empty")
        self.assertEqual(result["detail"], "organization chain empty: no authenticated genesis")
        # Nothing was synthesized: the chain is still empty and a retry still refuses.
        self.assertFalse((env.org / "HEAD.json").exists())
        self.assertEqual(list((env.org / "receipts").glob("*.json")), [])
        self.assertEqual(env.consume()["detail"], "organization chain empty: no authenticated genesis")
        self.assertFalse((env.org / "HEAD.json").exists())
        with self.assertRaises(consumer.ClaimFailClosed):
            env.chain()

    def test_uninitialized_empty_receipts_directory_is_not_authenticated_genesis(self):
        for name, prepare in (("initialized", lambda org: None),
                              ("bare", lambda org: shutil.rmtree(org / "receipts"))):
            env = Env(self.base / name, seed=False)
            prepare(env.org)
            result = env.consume()
            self._assert_unverified_without_fence(env, result, name)
            self.assertEqual(result["detail"], "organization chain empty: no authenticated genesis", name)
            self.assertEqual(list(env.org.rglob("receipts/*.json")), [], name)

    def test_authenticated_empty_genesis_binds_exact_organization_identity(self):
        empty = Env(self.base / "empty", seed=False)
        self._assert_unverified_without_fence(empty, empty.consume(), "empty")
        # A rooted, continuous chain written for one organization is refused by another.
        for name in ("head", "receipts"):
            env = Env(self.base / name)
            contract = env.source / ".stegverse/transition-ledger/org-contract.json"
            value = json.loads(contract.read_text())
            value["organization"] = "StegVerse-org"
            contract.write_text(json.dumps(value), encoding="utf-8")
            if name == "receipts":
                # HEAD names the consumer's organization; the receipts do not.
                head = json.loads((env.org / "HEAD.json").read_text())
                (env.org / "HEAD.json").write_text(json.dumps({**head, "organization": "StegVerse-org"}),
                                                   encoding="utf-8")
            result = env.consume()
            self._assert_unverified_without_fence(env, result, name)
            self.assertIn("organization", result["detail"], name)

    def test_repository_only_refusal_not_counted_as_organization_readback(self):
        env = Env(self.base, seed=False)
        result = env.consume()
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertTrue(result["repository_disposition_retained"])
        self.assertTrue(result["repository_receipt_sha256"])
        self.assertFalse(result["organization_disposition_retained"])
        self.assertEqual(result["organization_readback"], "NOT_PERFORMED")
        self.assertIsNone(result["organization_receipt_sha256"])
        self.assertIsNone(result["evidence_refs"]["organization_receipt_sha256"])
        self.assertEqual(result["retry_entrypoint"], consumer.RETRY_ENTRYPOINT)
        self.assertTrue((env.runtime / result["evidence_refs"]["consumption_record"]).is_file())
        # A refusal the organization did record is read back from its ledger root.
        recorded = Env(self.base / "recorded", generation=3).consume()
        self.assertTrue(recorded["organization_disposition_retained"])
        self.assertEqual(recorded["organization_readback"], "VERIFIED")

    # R27-02 -----------------------------------------------------------------
    def _retain(self, env, name, value):
        (env.runtime / consumer.GRANT_DIR).mkdir(parents=True, exist_ok=True)
        (env.runtime / consumer.GRANT_DIR / name).write_text(json.dumps(value), encoding="utf-8")

    def test_post_floor_grant_missing_org_receipt_sha_fails_closed(self):
        missing = Env(self.base / "missing", generation=9)
        missing.seed_grant("TASK-2026-9999", 9)
        self._retain(missing, "TASK-2026-9999-G9.json",
                     {"task_id": "TASK-2026-9999", "fencing_tokens": [9], "claim_scope_sha256": "0" * 64})
        result = missing.consume()
        self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED")
        self.assertIn("without its organization receipt", result["detail"])
        self.assertFalse(result["fence_issued"])
        self.assertEqual(missing.task("TASK-2026-0013")["status"], "queued")
        bound = Env(self.base / "bound", generation=9)
        receipt = bound.seed_grant("TASK-2026-9999", 9)["organization_receipt"]["receipt_sha256"]
        self._retain(bound, "TASK-2026-9999-G9.json",
                     {"task_id": "TASK-2026-9999", "fencing_tokens": [9], "claim_scope_sha256": "0" * 64,
                      "organization_receipt_sha256": receipt})
        self.assertEqual(bound.consume()["fencing_token"], 10)

    def test_post_floor_receipt_task_fence_scope_match(self):
        cases = {"task": {"task_id": "TASK-2026-0008"}, "fence": {"fencing_tokens": [10]},
                 "scope": {"claim_scope_sha256": "f" * 64}, "scope_absent": {"claim_scope_sha256": None}}
        for name, change in cases.items():
            env = Env(self.base / name, generation=9)
            receipt = env.seed_grant("TASK-2026-9999", 9)["organization_receipt"]["receipt_sha256"]
            value = {"task_id": "TASK-2026-9999", "fencing_tokens": [9], "claim_scope_sha256": "0" * 64,
                     "organization_receipt_sha256": receipt, **change}
            self._retain(env, "evidence.json", value)
            result = env.consume()
            self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED", name)
            self.assertIn("differs from organization receipt", result["detail"], name)
            self.assertFalse(result["fence_issued"], name)
            self.assertEqual(env.claims()["generation"], 9, name)
        # The consumer's own retained evidence carries exactly what the chain granted.
        env = Env(self.base / "own")
        first = env.consume()
        retained = json.loads((env.runtime / first["claim_grant_evidence"]["generation_receipt"]).read_text())
        granted = env.grants()[-1]
        self.assertEqual(retained["organization_receipt_sha256"], granted["receipt_sha256"])
        self.assertEqual(retained["claim_scope_sha256"], granted["boundary_evidence"]["claim_scope_sha256"])
        self.assertEqual(env.consume(), first)

    def test_legacy_predecessor_floor_evidence_is_immutable_and_scope_bound(self):
        task11 = json.loads((ROOT / "tasks/TASK-2026-0011.json").read_text(encoding="utf-8"))
        floor_sha = sha_file(ROOT / "tasks/TASK-2026-0012.json")
        scope = consumer.stable_hash(task11["requirements"]["mandatory"])
        accepted = {
            "bound": {"task_id": "TASK-2026-0011", "fencing_tokens": [7], "provenance_floor_sha256": floor_sha},
            "bound_scoped": {"task_id": "TASK-2026-0011", "fencing_tokens": [7], "provenance_floor_sha256": floor_sha,
                             "claim_scope_sha256": scope},
        }
        refused = {
            "unbound": {"task_id": "TASK-2026-0011", "fencing_tokens": [7]},
            "wrong_record": {"task_id": "TASK-2026-0011", "fencing_tokens": [7], "provenance_floor_sha256": "e" * 64},
            "wrong_task": {"task_id": "TASK-2026-0008", "fencing_tokens": [7], "provenance_floor_sha256": floor_sha},
            "below_floor_other_task": {"task_id": "TASK-2026-0008", "fencing_tokens": [5],
                                       "provenance_floor_sha256": floor_sha},
            "wrong_scope": {"task_id": "TASK-2026-0011", "fencing_tokens": [7], "provenance_floor_sha256": floor_sha,
                            "claim_scope_sha256": "f" * 64},
        }
        for name, value in accepted.items():
            env = Env(self.base / name)
            self._retain(env, "TASK-2026-0011-G7.json", value)
            self.assertEqual(env.consume()["fencing_token"], 8, name)
        for name, value in refused.items():
            env = Env(self.base / name)
            self._retain(env, "legacy.json", value)
            result = env.consume()
            self.assertEqual(result["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED", name)
            self.assertTrue(result["detail"].startswith("PREDECESSOR_PROVENANCE_IMMUTABLE: "), name)
            self.assertFalse(result["fence_issued"], name)
            self.assertEqual(env.task("TASK-2026-0013")["status"], "queued", name)
        # The floor record moved since the evidence was bound: the evidence no longer binds.
        moved = Env(self.base / "moved")
        self._retain(moved, "TASK-2026-0011-G7.json", accepted["bound"])
        path = moved.source / "tasks/TASK-2026-0012.json"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assertEqual(moved.consume()["failed_predicate"], "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED")

    # R27-03 / EVIDENCE_DISPOSITION -------------------------------------------
    def test_org_append_failure_retry_reuses_repository_receipt(self):
        env = Env(self.base)
        org_before = sorted(p.name for p in (env.org / "receipts").glob("*.json"))
        head_before = env.chain()["head_sha256"]
        original = consumer.ledger_custody
        appends = []

        def failing_once(*args, **kwargs):
            custody = original(*args, **kwargs)
            organization = custody["organization_ledger"]
            locked = organization._aggregate_transition_locked

            def append(receipt, **context):
                appends.append(receipt["transition_class"])
                if len(appends) == 1:
                    raise OSError("organization ledger unavailable")
                return locked(receipt, **context)

            organization._aggregate_transition_locked = append
            return custody

        with mock.patch.object(consumer, "ledger_custody", side_effect=failing_once):
            failed = env.consume()
        self.assertEqual(appends, [consumer.GRANTED])
        self.assertEqual(failed["disposition"], "FAIL_CLOSED")
        self.assertEqual(failed["failed_predicate"], "ORGANIZATION_APPEND_FAILED")
        self.assertFalse(failed["fence_issued"])
        self.assertIsNone(failed["fencing_token"])
        self.assertTrue(failed["repository_disposition_retained"])
        self.assertFalse(failed["organization_disposition_retained"])
        self.assertEqual(failed["organization_readback"], "NOT_PERFORMED")
        self.assertFalse(failed["organization_receipt_appended"])
        self.assertIsNone(failed["organization_receipt_sha256"])
        self.assertEqual(failed["retry_entrypoint"], consumer.RETRY_ENTRYPOINT)
        unpropagated = failed["unpropagated_repository_receipt_sha256"]
        self.assertEqual(failed["evidence_refs"]["unpropagated_repository_receipt_sha256"], unpropagated)
        self.assertTrue((env.runtime / failed["evidence_refs"]["consumption_record"]).is_file())
        # No active projection, no runtime claims-active advance, no fence.
        self.assertEqual(env.task("TASK-2026-0013")["status"], "queued")
        self.assertEqual(env.claims(), {"schema": "stegverse.org-claims/v1", "generation": 7, "claims": []})
        self.assertFalse((env.runtime / consumer.GRANT_DIR).exists())
        self.assertEqual(sorted(p.name for p in (env.org / "receipts").glob("*.json")), org_before)
        self.assertEqual(env.chain()["head_sha256"], head_before)
        self.assertEqual(env.grants(), [])
        store = env.custody()["repository_store"]
        granted = [store.get(k) for k in store.list_prefix("receipts/")
                   if store.get(k)["transition_class"] == consumer.GRANTED]
        self.assertEqual([r["receipt_sha256"] for r in granted], [unpropagated])

        replay = env.consume()
        self.assertEqual(appends, [consumer.GRANTED])  # the retry used the unpatched append
        self.assertEqual(replay["disposition"], "ALLOW")
        self.assertEqual(replay["fencing_token"], 8)
        self.assertEqual(replay["repository_receipt_sha256"], unpropagated)
        self.assertEqual(replay["organization_readback"], "VERIFIED")
        grants = env.grants()
        self.assertEqual([g["boundary_evidence"]["fencing_token"] for g in grants], [8])
        self.assertEqual(grants[0]["source_transition_sha256"], unpropagated)
        self.assertEqual(len(list((env.org / "receipts").glob("*.json"))), len(org_before) + 1)
        granted = [store.get(k) for k in store.list_prefix("receipts/")
                   if store.get(k)["transition_class"] == consumer.GRANTED]
        self.assertEqual(len(granted), 1)
        self.assertEqual(env.task("TASK-2026-0013")["status"], "active")
        self.assertEqual(env.claims()["generation"], 8)
        self.assertEqual(env.consume(), replay)
        self.assertEqual([g["boundary_evidence"]["fencing_token"] for g in env.grants()], [8])

if __name__ == "__main__":
    unittest.main()
