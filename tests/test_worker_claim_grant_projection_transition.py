"""Tests for scripts/worker_claim_grant_projection_transition.py (stdlib unittest, no network)."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
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


ISSUER = "StegVerse-Labs/.github"

# The Organization ledger as the allocator writes it: a repository receipt per transition, consumed by the
# existing Organization append (aggregate_transition), which retains the exact source bytes beside the receipt.
# tests/__init__.py and tests/conftest.py declare the POSIX ledger locus for the run.
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as LEDGER  # noqa: E402

# The repository emitter the allocator appends through: under #3290 an Organization append consumes only a
# source receipt on the materializer-supplied repository ledger, so each source is appended there first.
_EMIT_SPEC = importlib.util.spec_from_file_location("wcgp_repository_emitter", ROOT / ".stegverse/transition-ledger/emit.py")
EMITTER = importlib.util.module_from_spec(_EMIT_SPEC)
_EMIT_SPEC.loader.exec_module(EMITTER)


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
        self.repository_store = EMITTER.ledger_store.PosixLedgerStore(self.dir / "repository-ledger")
        self.chain = []

    def append(self, operation, task, fence, *, epoch=900000, from_clock=False, transition_id=None,
               transition_class=None, repository=ISSUER, source_evidence=None):
        transition_id = transition_id or f"ORGANIZATION-WORKER-CLAIM-GRANTED-{task}-G{fence}"
        evidence = {"disposition": "ALLOW", "task_id": task, "fencing_token": fence,
                    "claim_scope_sha256": "a" * 64, "organization_head_sha256": "b" * 64}
        recorded = evidence if source_evidence is None else source_evidence
        if repository == ISSUER:
            # The allocator's own repository receipt, on the repository ledger, as record_transition appends it.
            source = EMITTER.append(transition_id, transition_class or operation, "sha256:" + "0" * 64,
                                    "sha256:" + hashlib.sha256(transition_id.encode()).hexdigest(), recorded, "NONE",
                                    hb_epoch=epoch, store=self.repository_store)
        else:
            # Another repository's receipt: it is on no ledger this repository's materializer supplies.
            source = repository_receipt(transition_id, transition_class or operation, recorded,
                                        epoch=epoch, repository=repository)
        with LEDGER._materialized_repository_ledger(self.repository_store):
            receipt = LEDGER.aggregate_transition(
                source, ledger=self.ledger, org_transition_class="REPO_STATE_PROPAGATION",
                predecessor_org_state_sha256=source["predecessor_state_sha256"],
                successor_org_state_sha256=source["successor_state_sha256"],
                boundary_evidence={"operation": operation, **evidence}, authority_effect="NONE",
                hb_epoch=epoch)
        if from_clock:
            # No append can carry a clock-derived epoch (#3290 refuses it), so the receipt a host clock would
            # have produced is built by hand: the appended grant with a clock reference, digest recomputed.
            body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
            body["hb_reference"] = {**body["hb_reference"], "derived_from_clock": True,
                                    "sampled_unix_ns": 1_700_000_000_000_000_000}
            return {**body, "receipt_sha256": T.sha(body)}
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
        }.items():
            with self.subTest(name):
                self.f = Fixture(self)
                receipt = self.f.grant(8, **kw)
                self.assertChainSelfConsistent()
                self.assertRefused(self.f.run("plan", self.f.request(receipt)), "GRANT_SOURCE_ISSUER_EVIDENCE_MISMATCH")
        with self.subTest("repository"):
            # Another repository's source never reaches the Organization chain (#3290): the append itself
            # refuses it, so no grant over it exists to project.
            self.f = Fixture(self)
            self.f.grant(8)
            head = list(self.f.chain)
            with self.assertRaises(LEDGER.kernel.SuppliedEpochRefused) as raised:
                self.f.append(T.GRANTED, TASK, 9, repository="StegVerse-Labs/another-repository")
            self.assertEqual(raised.exception.refusal["failure_code"], "SPPA_CROSS_REPO_OBSERVATION_UNVERIFIED")
            self.assertIs(raised.exception.refusal["consequence_committed"], False)
            self.assertEqual(self.f.chain, head)

    def test_not_a_grant(self):
        self.f.grant()
        other = self.f.append("ORGANIZATION_WORKER_CLAIM_DENIED", TASK, 9)
        self.assertRefused(self.f.run("plan", self.f.request(other)), "RECEIPT_NOT_A_CLAIM_GRANT")

    def test_fence_at_floor(self):
        self.assertRefused(self.f.run("plan", self.f.request(self.f.grant(7))), "FENCE_AT_OR_BELOW_PROVENANCE_FLOOR")

    def test_clock_derived_epoch_refused(self):
        """Still proves a clock-derived grant epoch is refused. Under #3290 no Organization append can carry a
        clock-derived reference, so the fixture builds that receipt by hand (Fixture.append from_clock=True)."""
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


if __name__ == "__main__":
    unittest.main()
