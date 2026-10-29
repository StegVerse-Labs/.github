"""Tests for scripts/worker_claim_grant_projection_transition.py (stdlib unittest, no network)."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wcgp", ROOT / "scripts/worker_claim_grant_projection_transition.py")
T = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(T)

ORG = "StegVerse-Labs"
TASK = "TASK-2099-0001"
GOAL = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"


_LABEL = object()


ISSUER = "StegVerse-Labs/.github"

# The Organization ledger as the allocator writes it: a repository receipt per transition, consumed by the
# existing Organization append (aggregate_transition), which retains the exact source bytes beside the receipt.
# tests/__init__.py and tests/conftest.py declare the POSIX ledger locus for the run.
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as LEDGER  # noqa: E402


def repository_receipt(transition_id, transition_class, evidence, *, epoch=900000, repository=ISSUER):
    body = {
        "schema": "stegverse.repo-transition-receipt/v1", "repository": repository, "transition_id": transition_id,
        "transition_class": transition_class, "predecessor_state_sha256": "sha256:" + "0" * 64,
        "successor_state_sha256": "sha256:" + hashlib.sha256(transition_id.encode()).hexdigest(),
        "evidence": evidence, "authority_effect": "NONE",
        "hb_reference": {"epoch": epoch, "generation": epoch, "derived_from_clock": False},
        "previous_receipt_sha256": None,
    }
    return {**body, "receipt_sha256": T.sha(body)}


def stray_receipt(task, fence):
    body = {"schema": T.ORG_RECEIPT_SCHEMA, "organization": ORG,
            "source_transition_id": f"ORGANIZATION-WORKER-CLAIM-GRANTED-{task}-G{fence}",
            "boundary_evidence": {"operation": T.GRANTED, "disposition": "ALLOW", "task_id": task, "fencing_token": fence},
            "hb_reference": {"epoch": 900000, "derived_from_clock": False}, "previous_receipt_sha256": None}
    return {**body, "receipt_sha256": T.sha(body)}


class Fixture:
    def __init__(self, test: unittest.TestCase):
        self.dir = Path(tempfile.mkdtemp())
        test.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.base = self.dir / "base"
        for rel in ("control/worker-registry.json", "tasks/TASK-2026-0012.json", T.ORG_CONTRACT, T.REPO_CONTRACT):
            (self.base / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.base / rel)
        (self.base / "tasks" / f"{TASK}.json").write_text(json.dumps(
            {"task_id": TASK, "canonical_task_record": f"data/canonical-task-records/{GOAL}.json"}))
        self.ledger = self.dir / "ledger"
        self.chain = []

    def append(self, operation, task, fence, *, epoch=900000, from_clock=False, transition_id=None,
               transition_class=None, repository=ISSUER, source_evidence=None, custody_authentication=_LABEL):
        transition_id = transition_id or f"ORGANIZATION-WORKER-CLAIM-GRANTED-{task}-G{fence}"
        evidence = {"disposition": "ALLOW", "task_id": task, "fencing_token": fence,
                    "claim_scope_sha256": "a" * 64, "organization_head_sha256": "b" * 64,
                    # what scripts/consume_org_claim_allocator_request.py records (CARRIED_IF_RECORDED)
                    "custody_authentication": "HASH_CHAIN_CONTINUITY_ONLY"}
        if custody_authentication is None:
            evidence.pop("custody_authentication")
        elif custody_authentication is not _LABEL:
            evidence["custody_authentication"] = custody_authentication
        source = repository_receipt(transition_id, transition_class or operation,
                                    evidence if source_evidence is None else source_evidence,
                                    epoch=epoch, repository=repository)
        receipt = LEDGER.aggregate_transition(
            source, ledger=self.ledger, org_transition_class="REPO_STATE_PROPAGATION",
            predecessor_org_state_sha256=source["predecessor_state_sha256"],
            successor_org_state_sha256=source["successor_state_sha256"],
            boundary_evidence={"operation": operation, **evidence}, authority_effect="NONE",
            hb_epoch=None if from_clock else epoch)
        self.chain.append(receipt)
        return receipt

    def grant(self, fence=8, **kw):
        if not self.chain:
            self.append("ORGANIZATION_GENESIS", "-", 0, transition_id="GENESIS")
        return self.append(T.GRANTED, TASK, fence, **kw)

    def source_path(self, receipt):
        return self.ledger / LEDGER.ledger_store.source_key(receipt["source_transition_sha256"])

    def registry(self, tree=None):
        return json.loads(((tree or self.base) / T.WORKER_REGISTRY).read_text())

    def request(self, receipt, **overrides):
        req = {"schema": T.REQUEST_SCHEMA, "request_id": "WCGP-TEST-001", "allocator_task_id": TASK,
               "canonical_task_id": GOAL, "observed_worker_registry_generation": self.registry()["generation"],
               "organization_receipt_sha256": receipt["receipt_sha256"], "organization_receipt": receipt,
               "authority_effect": "NONE_PROJECTION_ONLY", **overrides}
        path = self.dir / "request.json"
        path.write_text(json.dumps(req))
        return path

    def run(self, mode, request, head=None, ledger=True):
        return T.run(mode, request, self.base, head, str(self.ledger) if ledger else None)


class ProjectionTest(unittest.TestCase):
    def setUp(self):
        self.f = Fixture(self)

    def assertRefused(self, body, code):
        self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
        self.assertEqual(body["failure_code"], code, body)
        for key in T.SIX_FIELDS:
            self.assertTrue(body.get(key), key)
        self.assertFalse(body["consequence_committed"])

    def test_plan_allow_generation_exclusive_of_fence(self):
        prev = self.f.registry()["generation"]
        body = self.f.run("plan", self.f.request(self.f.grant(8)))
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["evidence"]["successor_worker_registry_generation"], max(prev + 1, 9))
        for flag in ("workercoordinator_domain_fence_minted", "allocator_fence_reissued", "generation_lowered",
                     "clock_read", "organization_ledger_appended"):
            self.assertIs(body[flag], False)

    def test_high_fence_lifts_generation_above_fence(self):
        body = self.f.run("plan", self.f.request(self.f.grant(500)))
        self.assertEqual(body["evidence"]["successor_worker_registry_generation"], 501)

    def test_plan_writes_nothing(self):
        before = (self.f.base / T.WORKER_REGISTRY).read_bytes()
        self.f.run("plan", self.f.request(self.f.grant()))
        self.assertEqual(before, (self.f.base / T.WORKER_REGISTRY).read_bytes())

    def test_apply_projects_row_and_preserves_everything_else(self):
        before = self.f.registry()
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        receipt = self.f.grant(8, epoch=912345)
        body = self.f.run("apply", self.f.request(receipt), head=head)
        self.assertEqual(body["disposition"], "ALLOW", body)
        after = self.f.registry(head)
        self.assertEqual(after["updated_at"], before["updated_at"])  # no clock
        self.assertEqual(after["tasks"][:-1], before["tasks"])
        row = after["tasks"][-1]
        self.assertEqual(row["task_id"], GOAL)
        self.assertEqual(row["claim_id"], f"ORGANIZATION-WORKER-CLAIM-GRANTED-{TASK}-G8")
        self.assertEqual(row["assignment_timer"]["fencing_token"], 8)
        self.assertEqual(row["assignment_timer"]["fence_domain"], "ORGANIZATION_CLAIM_ALLOCATOR")
        self.assertEqual(row["assignment_timer"]["start_epoch"], 912345)
        self.assertEqual(row["assignment_timer"]["grant_receipt_sha256"], receipt["receipt_sha256"])
        self.assertEqual(body["evidence"]["source_transition_sha256"], receipt["source_transition_sha256"])
        self.assertEqual(body["evidence"]["source_repository"], ISSUER)
        self.assertIsNone(row["worker_id"])

    def test_apply_then_verify_allow_and_replay_is_idempotent(self):
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        request = self.f.request(self.f.grant())
        self.assertEqual(self.f.run("apply", request, head=head)["disposition"], "ALLOW")
        self.assertEqual(self.f.run("verify", request, head=head)["disposition"], "ALLOW")
        applied = (head / T.WORKER_REGISTRY).read_bytes()
        replay = T.run("plan", request, head, None, str(self.f.ledger))
        self.assertEqual(replay["disposition"], "ALLOW", replay)
        self.assertTrue(replay["evidence"]["replayed"])
        T.run("apply", request, head, None, str(self.f.ledger))
        self.assertEqual(applied, (head / T.WORKER_REGISTRY).read_bytes())

    def test_verify_refuses_hand_edit(self):
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        request = self.f.request(self.f.grant())
        self.f.run("apply", request, head=head)
        reg = self.f.registry(head)
        reg["tasks"][-1]["assignment_timer"]["fencing_token"] = 99
        (head / T.WORKER_REGISTRY).write_text(json.dumps(reg, indent=2) + "\n")
        self.assertRefused(self.f.run("verify", request, head=head), "PROJECTION_BYTES_DIVERGE")

    def test_without_ledger_fails_closed(self):
        self.assertRefused(self.f.run("plan", self.f.request(self.f.grant()), ledger=False),
                           "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED")

    def test_tampered_receipt(self):
        receipt = copy.deepcopy(self.f.grant())
        receipt["boundary_evidence"]["fencing_token"] = 9
        self.assertRefused(self.f.run("plan", self.f.request(receipt)), "GRANT_RECEIPT_DIGEST_MISMATCH")

    def test_receipt_not_on_chain(self):
        self.f.grant()
        stray = stray_receipt(TASK, 12)
        self.assertRefused(self.f.run("plan", self.f.request(stray)), "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED")

    def test_broken_chain(self):
        receipt = self.f.grant()
        (self.f.ledger / LEDGER.ledger_store.receipt_key(self.f.chain[0]["receipt_sha256"])).unlink()
        self.assertRefused(self.f.run("plan", self.f.request(receipt)), "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED")

    def assertChainSelfConsistent(self):
        # The refusal below is the source receipt's, not the Organization chain's: the chain alone still verifies.
        self.assertTrue(T.read_chain(T.open_store(str(self.f.ledger)), ORG))

    def test_missing_source_receipt_refused(self):
        receipt = self.f.grant()
        self.f.source_path(receipt).unlink()
        self.assertChainSelfConsistent()
        self.assertRefused(self.f.run("plan", self.f.request(receipt)), "GRANT_SOURCE_RECEIPT_UNVERIFIED")

    def test_tampered_source_receipt_refused(self):
        receipt = self.f.grant()
        path = self.f.source_path(receipt)
        source = json.loads(path.read_text())
        source["evidence"]["fencing_token"] = 9
        path.write_text(json.dumps(source))
        self.assertChainSelfConsistent()
        self.assertRefused(self.f.run("plan", self.f.request(receipt)), "GRANT_SOURCE_RECEIPT_UNVERIFIED")

    def test_source_receipt_must_carry_the_issuers_grant(self):
        # Each retained source verifies on its own and the Organization chain recomputes, but the source the
        # allocator recorded is not this grant: another class, fence, disposition, repository or a clock epoch.
        granted = {"disposition": "ALLOW", "task_id": TASK, "fencing_token": 8}
        for name, kw in {
            "class": {"transition_class": "ORGANIZATION_WORKER_CLAIM_REFUSED"},
            "fence": {"source_evidence": {**granted, "fencing_token": 7}},
            "disposition": {"source_evidence": {**granted, "disposition": "DENY"}},
            "task": {"source_evidence": {**granted, "task_id": "TASK-2099-0002"}},
            "repository": {"repository": "StegVerse-Labs/another-repository"},
        }.items():
            with self.subTest(name):
                self.f = Fixture(self)
                receipt = self.f.grant(8, **kw)
                self.assertChainSelfConsistent()
                self.assertRefused(self.f.run("plan", self.f.request(receipt)), "GRANT_SOURCE_ISSUER_EVIDENCE_MISMATCH")

    def test_not_a_grant(self):
        self.f.grant()
        other = self.f.append("ORGANIZATION_WORKER_CLAIM_DENIED", TASK, 9)
        self.assertRefused(self.f.run("plan", self.f.request(other)), "RECEIPT_NOT_A_CLAIM_GRANT")

    def test_fence_at_floor(self):
        self.assertRefused(self.f.run("plan", self.f.request(self.f.grant(7))), "FENCE_AT_OR_BELOW_PROVENANCE_FLOOR")

    def test_clock_derived_epoch_refused(self):
        self.assertRefused(self.f.run("plan", self.f.request(self.f.grant(8, from_clock=True))),
                           "GRANT_EPOCH_NOT_CARRIER_SUPPLIED")

    def test_superseded_grant(self):
        first = self.f.grant(8)
        self.f.grant(9)
        self.assertRefused(self.f.run("plan", self.f.request(first)), "GRANT_SUPERSEDED_ON_CHAIN")

    def test_stale_generation(self):
        receipt = self.f.grant()
        request = self.f.request(receipt, observed_worker_registry_generation=self.f.registry()["generation"] - 1)
        self.assertRefused(self.f.run("plan", request), "WORKER_REGISTRY_GENERATION_NOT_OBSERVED_TIP")

    def _seed_row(self, row):
        reg = self.f.registry()
        reg["tasks"].append(row)
        (self.f.base / T.WORKER_REGISTRY).write_text(json.dumps(reg, indent=2) + "\n")

    def test_fence_reissue_refused(self):
        self._seed_row({"task_id": "OTHER-GOAL-001", "goal_id": "OTHER-GOAL-001", "claim_id": "X", "state": "CLAIM_GRANTED_PROJECTED",
                        "assignment_timer": {"fence_domain": "ORGANIZATION_CLAIM_ALLOCATOR", "fencing_token": 8,
                                             "grant_receipt_sha256": "sha256:" + "c" * 64}})
        self.assertRefused(self.f.run("plan", self.f.request(self.f.grant(8))), "FENCE_REISSUED")

    def test_task_already_held(self):
        self._seed_row({"task_id": GOAL, "goal_id": GOAL, "claim_id": "SHWP-X-G3", "state": "ACTIVE", "assignment_timer": None})
        self.assertRefused(self.f.run("plan", self.f.request(self.f.grant())), "TASK_ALREADY_HELD_IN_WORKER_REGISTRY")

    def test_allocator_task_must_project_canonical_task(self):
        receipt = self.f.grant()
        self.assertRefused(self.f.run("plan", self.f.request(receipt, canonical_task_id="SOME-OTHER-GOAL-001")),
                           "ALLOCATOR_TASK_UNRESOLVED")

    def test_schema_refusal(self):
        receipt = self.f.grant()
        self.assertRefused(self.f.run("plan", self.f.request(receipt, authority_effect="GRANTS_CLAIM")),
                           "PROJECTION_REQUEST_SCHEMA_INVALID")

    def test_projected_grant_mints_no_lease_or_expiry(self):
        # Expiry is WorkerCoordinator's (heartbeat_runtime/assignment_timer.py): the projection carries
        # the allocator fence and carrier epoch only, and mints no lease, heartbeat or expiry bound.
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        self.assertEqual(self.f.run("apply", self.f.request(self.f.grant(8)), head=head)["disposition"], "ALLOW")
        row = self.f.registry(head)["tasks"][-1]
        self.assertIsNone(row["lease"])
        self.assertIsNone(row["heartbeat_timing"])
        self.assertFalse({"expires_at", "expiry_basis", "heartbeat_due_at"} & set(row["assignment_timer"]))

    def test_unadmitted_canonical_task_is_not_advanced_by_a_projected_grant(self):
        # The projection writes the WorkerCoordinator row only; the canonical projector still refuses a
        # PROPOSED (unadmitted) task, so a GRANTED receipt never admits a task.
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        body = self.f.run("apply", self.f.request(self.f.grant(8)), head=head)
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["authority_effect"], "NONE_PROJECTION_ONLY")
        spec = importlib.util.spec_from_file_location("canonical_projector",
                                                      ROOT / "scripts/project_worker_claim_into_canonical_task.py")
        projector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(projector)
        registry = {"generation": 1, "tasks": [{"task_id": GOAL, "coordination_state": "PROPOSED"}]}
        with self.assertRaises(SystemExit) as refused:
            projector.project(registry, self.f.registry(head), GOAL)
        self.assertIn("FAIL_CLOSED", str(refused.exception))
        self.assertIn("admitted", str(refused.exception))
        self.assertEqual(registry["tasks"][0], {"task_id": GOAL, "coordination_state": "PROPOSED"})

    # --- P1: a worker-registry edit that carries no manifest may not add or change a projected row
    def _head_with(self, mutate):
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        reg = self.f.registry(head)
        mutate(reg)
        (head / T.WORKER_REGISTRY).write_text(json.dumps(reg, indent=2) + "\n")
        return head

    def test_guard_refuses_a_projected_row_without_a_manifest(self):
        head = self._head_with(lambda reg: reg["tasks"].append(
            {"task_id": GOAL, "goal_id": GOAL, "claim_id": f"ORGANIZATION-WORKER-CLAIM-GRANTED-{TASK}-G8",
             "state": "CLAIM_GRANTED_PROJECTED",
             "assignment_timer": {"fence_domain": "ORGANIZATION_CLAIM_ALLOCATOR", "fencing_token": 8}}))
        self.assertRefused(T.guard(self.f.base, head), "PROJECTED_ROW_WITHOUT_MANIFEST")

    def test_guard_refuses_a_state_only_projection_without_a_manifest(self):
        head = self._head_with(lambda reg: reg["tasks"].append(
            {"task_id": GOAL, "goal_id": GOAL, "claim_id": "X", "state": "CLAIM_GRANTED_PROJECTED",
             "assignment_timer": None}))
        self.assertRefused(T.guard(self.f.base, head), "PROJECTED_ROW_WITHOUT_MANIFEST")

    def test_guard_refuses_removing_or_editing_a_projected_row_without_a_manifest(self):
        head = self.f.dir / "applied"
        shutil.copytree(self.f.base, head)
        self.assertEqual(self.f.run("apply", self.f.request(self.f.grant()), head=head)["disposition"], "ALLOW")
        edited = self.f.dir / "edited"
        shutil.copytree(head, edited)
        reg = self.f.registry(edited)
        reg["tasks"][-1]["assignment_timer"]["fencing_token"] = 99
        (edited / T.WORKER_REGISTRY).write_text(json.dumps(reg, indent=2) + "\n")
        self.assertRefused(T.guard(head, edited), "PROJECTED_ROW_WITHOUT_MANIFEST")
        self.assertRefused(T.guard(head, self.f.base), "PROJECTED_ROW_WITHOUT_MANIFEST")

    def test_guard_allows_registry_edits_that_touch_no_projected_row(self):
        def bump(reg):
            reg["generation"] = reg["generation"] + 1
        body = T.guard(self.f.base, self._head_with(bump))
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["mode"], "guard")

    def test_guard_fails_closed_on_an_unreadable_registry(self):
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        (head / T.WORKER_REGISTRY).write_text("{not json")
        self.assertRefused(T.guard(self.f.base, head), "PROJECTION_INTERNAL_ERROR")

    def test_workflow_guards_registry_edits_that_carry_no_manifest(self):
        text = (ROOT / ".github/workflows/worker-claim-grant-projection-transition.yml").read_text()
        no_manifest = text.split('if [ -z "$changed" ]; then', 1)[1].split("\n          fi\n", 1)[0]
        self.assertIn("scripts/worker_claim_grant_projection_transition.py guard", no_manifest)
        self.assertIn('--base "$RUNNER_TEMP/base" --head .', no_manifest)
        self.assertNotIn('"disposition":"ALLOW"', no_manifest)

    # --- P2: the chain proves hash continuity only; a grant may not claim more, and the row says so
    def test_overstated_custody_authentication_refused(self):
        for label in ("AUTHENTICATED_ORGANIZATION_CUSTODY", "hash_chain_continuity_only", True, 1, ["HASH_CHAIN_CONTINUITY_ONLY"]):
            with self.subTest(label=label):
                f = Fixture(self)
                body = T.run("plan", f.request(f.grant(8, custody_authentication=label)), f.base, None, str(f.ledger))
                self.assertRefused(body, "GRANT_CUSTODY_AUTHENTICATION_OVERSTATED")

    def test_projected_row_and_evidence_carry_the_continuity_only_label(self):
        for label in (_LABEL, None):  # recorded, and a grant written before the label existed
            with self.subTest(label=label):
                f = Fixture(self)
                head = f.dir / "head"
                shutil.copytree(f.base, head)
                body = T.run("apply", f.request(f.grant(8, custody_authentication=label)), f.base, head, str(f.ledger))
                self.assertEqual(body["disposition"], "ALLOW", body)
                self.assertEqual(body["evidence"]["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")
                timer = f.registry(head)["tasks"][-1]["assignment_timer"]
                self.assertEqual(timer["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")

    def test_script_reads_no_clock(self):
        tree = ast.parse((ROOT / "scripts/worker_claim_grant_projection_transition.py").read_text())
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                    for a in getattr(n, "names", [])} | {n.module.split(".")[0] for n in ast.walk(tree)
                                                         if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {"time", "datetime"}, imported)

    def test_contract_lists_every_refusal_code(self):
        contract = json.loads((ROOT / "contracts/worker-claim-grant-projection-transition.v1.json").read_text())
        source = (ROOT / "scripts/worker_claim_grant_projection_transition.py").read_text()
        for code in contract["dispositions"]["FAIL_CLOSED"]:
            self.assertIn(f'"{code}"', source, code)
        self.assertEqual(contract["dispositions"]["six_fields"], list(T.SIX_FIELDS))


# --- The grant as the allocator records it on the declared Organization ledger (refs/stegverse/organization-ledger)
# Every grant below is produced by the repository's real ledger code: the repository receipt by
# .stegverse/transition-ledger/emit.py append and the Organization receipt by aggregate_transition, on a Git
# ledger store on the declared ref in a temporary bare repository, with the context
# consume_org_claim_allocator_request.record_transition builds (carrier hb_epoch as #3241 passes it). No
# production ledger ref is touched. Receipts are written by hand only where a test shows they are refused.
def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EMIT = _load("wcgp_repository_ledger", ".stegverse/transition-ledger/emit.py")
AGG = _load("wcgp_organization_ledger", "resident-runtime/aggregate_repo_transition.py")
ALLOC = _load("wcgp_allocator", "scripts/consume_org_claim_allocator_request.py")
REF = "refs/stegverse/organization-ledger"
# The repository's own declaration (store git on REF), which production reads.
DECLARED_LOCUS = json.loads((ROOT / T.ORG_CONTRACT).read_text())["organization_ledger"]


def declare_repository_locus(test: unittest.TestCase) -> None:
    """Run under org-contract.json's own Organization ledger declaration (OL-1b), under either runner.

    tests/__init__.py and tests/conftest.py declare {store: posix} for suites that supply a POSIX root;
    these tests hold Git stores on the declared ref, as tests marked repository_ledger_locus do. Every
    aggregator copy (the one imported above, the one the verifier reads through, and any loaded during
    the test) carries the repository's own declaration. Test-only, restored after the test.
    """
    loader = importlib.machinery.SourceFileLoader
    inner = loader.exec_module

    def exec_and_declare(self, module):
        inner(self, module)
        if callable(getattr(module, "declared_ledger_locus", None)) and isinstance(getattr(module, "C", None), dict):
            module.C["organization_ledger"] = copy.deepcopy(DECLARED_LOCUS)

    loader.exec_module = exec_and_declare
    test.addCleanup(setattr, loader, "exec_module", inner)
    for module in {id(m): m for m in (AGG, LEDGER, sys.modules.get("aggregate_repo_transition")) if m}.values():
        test.addCleanup(module.C.__setitem__, "organization_ledger", module.C.get("organization_ledger"))
        module.C["organization_ledger"] = copy.deepcopy(DECLARED_LOCUS)


def _bare(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-q", str(path)], check=True)
    return path


class AllocatorLedger:
    """A repository ledger and a Git Organization ledger on the declared ref, written by the real code."""

    def __init__(self, directory: Path, *, posix: bool = False):
        self.posix = posix
        if posix:  # a POSIX root, which the repository's declaration (store git) does not admit
            self.store = AGG.ledger_store.PosixLedgerStore(directory / "organization")
            self.locator = str(directory / "organization")
        else:
            self.git_dir = _bare(directory / "organization.git")
            self.store = AGG.ledger_store.GitLedgerStore(self.git_dir, REF, custody="PRIVATE")
            self.locator = f"git+{self.git_dir}#{REF}"
        self.repository = EMIT.ledger_store.PosixLedgerStore(directory / "repository")
        self.chain = []

    def record(self, operation, task, fence, *, epoch=900000):
        """consume_org_claim_allocator_request.record_transition, with the carrier epoch (#3241)."""
        disposition = ALLOC.DISPOSITION.get(operation, "ALLOW")
        transition_id = f"{operation.replace('_', '-')}-{task}-G{fence}"
        evidence = {"disposition": disposition, "task_id": task, "fencing_token": fence,
                    "claim_scope_sha256": "a" * 64,
                    "organization_head_sha256": self.chain[-1]["receipt_sha256"] if self.chain else None,
                    "custody_authentication": ALLOC.CUSTODY_AUTHENTICATION}
        repository_receipt = EMIT.append(
            transition_id, operation, "sha256:" + "0" * 64,
            "sha256:" + ALLOC.stable_hash({"transition_id": transition_id, "evidence": evidence}),
            evidence, "NONE", hb_epoch=epoch, store=self.repository)
        recorded = repository_receipt["evidence"]
        declared = AGG.C["organization_ledger"]
        if self.posix:  # the aggregator writes a POSIX root only under a declared {store: posix}
            AGG.C["organization_ledger"] = {"store": "posix"}
        try:
            receipt = AGG.aggregate_transition(
                repository_receipt, ledger=self.store, org_transition_class="REPO_STATE_PROPAGATION",
                predecessor_org_state_sha256=repository_receipt["predecessor_state_sha256"],
                successor_org_state_sha256=repository_receipt["successor_state_sha256"],
                boundary_evidence={"operation": operation, **{k: recorded.get(k) for k in ALLOC.CARRIED},
                                   **{k: recorded[k] for k in ALLOC.CARRIED_IF_RECORDED if k in recorded}},
                authority_effect="NONE", hb_epoch=epoch)
        finally:
            AGG.C["organization_ledger"] = declared
        self.chain.append(receipt)
        return receipt

    def overwrite(self, key, value):
        """Commit `value` at `key` on the ref, bypassing the aggregator, as a rogue ref writer would."""
        self.store.publish({}, {key: value}, key)

    def put_receipt(self, body, *, head=True):
        """Write a receipt straight into the ref (and move HEAD to it), bypassing the aggregator."""
        receipt = {**body, "receipt_sha256": T.sha(body)}
        self.overwrite(AGG.ledger_store.receipt_key(receipt["receipt_sha256"]), receipt)
        if head:
            current = self.store.get(AGG.ledger_store.HEAD_KEY)
            self.overwrite(AGG.ledger_store.HEAD_KEY, {**current, "receipt_sha256": receipt["receipt_sha256"]})
            self.chain.append(receipt)
        return receipt


def forged(previous, task, fence):
    """A receipt shaped like a grant that only hash-chain continuity vouches for (no retained source)."""
    body = {
        "schema": T.ORG_RECEIPT_SCHEMA, "organization": ORG,
        "source_transition_id": f"ORGANIZATION-WORKER-CLAIM-GRANTED-{task}-G{fence}",
        "org_transition_class": T.GRANTED,
        "boundary_evidence": {"operation": T.GRANTED, "disposition": "ALLOW", "task_id": task, "fencing_token": fence,
                              "claim_scope_sha256": "a" * 64, "custody_authentication": T.CUSTODY_AUTHENTICATION},
        "authority_effect": "NONE",
        "hb_reference": {"epoch": 900000, "generation": 900000, "derived_from_clock": False},
        "observed_at": "wall-clock-non-ordering",
        "previous_receipt_sha256": previous,
    }
    return body


class AllocatorLedgerFixture(Fixture):
    def __init__(self, test: unittest.TestCase):
        declare_repository_locus(test)
        super().__init__(test)
        self.allocator = AllocatorLedger(self.dir)
        self.chain = self.allocator.chain

    def grant(self, fence=8, **kw):
        if not self.chain:  # a non-grant receipt first, so the grant is not the chain root
            self.allocator.record(ALLOC.REFUSED, "TASK-2099-0000", 0)
        return self.allocator.record(T.GRANTED, TASK, fence, **kw)

    def run(self, mode, request, head=None, ledger=True):
        return T.run(mode, request, self.base, head, self.allocator.locator if ledger else None)


class AllocatorReadbackTest(unittest.TestCase):
    """A grant on the declared ledger is projected only if its retained source reads back through the
    existing verifier and records the whole grant (R6, R9)."""

    def setUp(self):
        self.f = AllocatorLedgerFixture(self)

    assertRefused = ProjectionTest.assertRefused

    def assertSourceRefused(self, body, predicate):
        self.assertRefused(body, "GRANT_SOURCE_RECEIPT_UNVERIFIED")
        self.assertEqual(body["failed_predicate"], predicate, body)
        self.assertEqual(body["organization_readback_refusal"]["failed_predicate"], predicate, body)
        self.assertNotIn("derived_files", body)

    def test_allow_carries_the_verified_readback_and_its_custody_basis(self):
        body = self.f.run("plan", self.f.request(self.f.grant(8)))
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["evidence"]["organization_readback"], "VERIFIED")
        basis = body["evidence"]["organization_readback_custody_basis"]
        # generation 0 reports the receipt's own unauthenticated basis, never custody authority (Q74-01)
        self.assertEqual(basis, AGG.CUSTODY_AUTHORITY_BASIS_GENERATION_0)
        self.assertIn("UNAUTHENTICATED", basis)
        self.assertEqual(body["evidence"]["custody_authentication"], "HASH_CHAIN_CONTINUITY_ONLY")

    def test_grant_only_hash_chain_continuity_vouches_for_is_refused(self):
        self.f.grant(8)
        receipt = self.f.allocator.put_receipt(forged(self.f.chain[-1]["receipt_sha256"], TASK, 9))
        head = self.f.dir / "head"
        shutil.copytree(self.f.base, head)
        before = (head / T.WORKER_REGISTRY).read_bytes()
        body = self.f.run("apply", self.f.request(receipt), head=head)
        self.assertSourceRefused(body, "STATE_RECEIPT_SHA256_ABSENT")
        self.assertEqual(before, (head / T.WORKER_REGISTRY).read_bytes())  # no row projected

    def test_grant_borrowing_a_real_source_for_another_fence_is_refused(self):
        real = self.f.grant(8)
        body = {k: v for k, v in real.items() if k != "receipt_sha256"}
        body.update(previous_receipt_sha256=real["receipt_sha256"],
                    source_transition_id=f"ORGANIZATION-WORKER-CLAIM-GRANTED-{TASK}-G9",
                    boundary_evidence={**real["boundary_evidence"], "fencing_token": 9})
        receipt = self.f.allocator.put_receipt(body)
        self.assertSourceRefused(self.f.run("plan", self.f.request(receipt)), "ORGANIZATION_SOURCE_RECEIPT_INVALID")

    def test_grant_evidence_differing_from_its_retained_source_is_refused(self):
        # Beyond fence, task and disposition: every key record_transition carries into boundary_evidence.
        for key, value in (("claim_scope_sha256", "f" * 64), ("organization_head_sha256", "sha256:" + "f" * 64),
                           ("custody_authentication", None)):
            with self.subTest(key=key):
                f = AllocatorLedgerFixture(self)
                real = f.grant(8)
                body = {k: v for k, v in real.items() if k != "receipt_sha256"}
                evidence = {**real["boundary_evidence"], key: value}
                if value is None:
                    evidence.pop(key)  # CARRIED_IF_RECORDED: the source recorded it, the receipt dropped it
                body.update(previous_receipt_sha256=real["receipt_sha256"], boundary_evidence=evidence)
                refused = f.run("plan", f.request(f.allocator.put_receipt(body)))
                self.assertRefused(refused, "GRANT_SOURCE_ISSUER_EVIDENCE_MISMATCH")
                self.assertIn(f"evidence.{key}", refused["detail"])

    def test_grant_on_a_forked_ledger_is_refused(self):
        receipt = self.f.grant(8)
        sibling = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        sibling["observed_at"] = "a second writer"
        self.f.allocator.put_receipt(sibling, head=False)  # a second child of the grant's predecessor
        self.assertSourceRefused(self.f.run("plan", self.f.request(receipt)), "ORGANIZATION_CUSTODY_FORK_DETECTED")

    def test_grant_on_an_undeclared_posix_root_is_refused(self):
        (self.f.dir / "posix").mkdir()
        ledger = AllocatorLedger(self.f.dir / "posix", posix=True)
        ledger.record(ALLOC.REFUSED, "TASK-2099-0000", 0)
        receipt = ledger.record(T.GRANTED, TASK, 8)
        body = T.run("plan", self.f.request(receipt), self.f.base, None, ledger.locator)
        self.assertSourceRefused(body, "ORGANIZATION_LEDGER_LOCUS_MISMATCH")


if __name__ == "__main__":
    unittest.main()
