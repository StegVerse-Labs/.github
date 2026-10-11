from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_cosv_index_shards.py"
OWNER_ITEMS = ROOT / "tests" / "fixtures" / "cosv-task-vector-index-owner-items.json"

spec = importlib.util.spec_from_file_location("materialize_cosv_index_shards", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TASK = "UNIT-COSV-INDEX-TASK-001"
VECTOR = "71000000111111"


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def vector_record(task_id: str = TASK, vector: str = VECTOR, **overrides) -> dict:
    record = {
        "identity": f"StegVerse-Labs/.github:task:{task_id}",
        "profile": "task.v1",
        "level": "task",
        "vector": vector,
        "evidence_refs": [f"handoffs/{task_id}.json"],
        "observed_at": "2026-10-11T00:00:00Z",
        "exact_metrics": {"symbol_order": "LRUIVGOCMTBEAP", "lifecycle": "COMPLETE"},
    }
    record.update(overrides)
    return record


class RepositoryCheckTests(unittest.TestCase):
    """The effective index must be complete for every derivable vectorized task.

    Owner items (registry tasks without a resolvable machine source and
    pre-existing rows whose source fails verify_task_pointer parity) are
    ratcheted in the fixture; anything new fails closed here.
    """

    def run_check(self, *extra: str) -> tuple[int, dict]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--check", *extra],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def test_check_mode_is_clean_against_repository_modulo_acknowledged_owner_items(self) -> None:
        code, receipt = self.run_check("--owner-items", str(OWNER_ITEMS))
        self.assertEqual(receipt["authority_effect"], "NONE")
        self.assertFalse(receipt["claims_runtime_transition"])
        self.assertEqual(receipt["added"], [], "vectorized registry task without an effective COSV index row")
        self.assertEqual(receipt["normalized"], [])
        self.assertEqual(receipt["skipped_fail_closed"], [])
        self.assertEqual(receipt["existing_row_defects"], [])
        self.assertEqual(receipt["stale_owner_items"], [])
        self.assertEqual(receipt["status"], "OK")
        self.assertEqual(code, 0)

    def test_owner_items_fixture_is_a_ratchet_of_owner_predicates_only(self) -> None:
        fixture = json.loads(OWNER_ITEMS.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema"], mod.OWNER_ITEMS_SCHEMA)
        self.assertEqual(fixture["authority_effect"], "NONE")
        keys = [(item["task_id"], item["predicate"]) for item in fixture["items"]]
        self.assertEqual(keys, sorted(set(keys)))
        allowed = {"SOURCE_REF_ABSENT", "VECTOR_SOURCE_NOT_MATERIALIZED", "VECTOR_IDENTITY_MISMATCH", "VECTOR_VALUE_MISMATCH"}
        for _, predicate in keys:
            self.assertIn(predicate, allowed)

    def test_bare_check_mode_reports_owner_items_and_fails(self) -> None:
        code, receipt = self.run_check()
        fixture = json.loads(OWNER_ITEMS.read_text(encoding="utf-8"))
        live = {(x["task_id"], x["predicate"]) for x in receipt["skipped_fail_closed"] + receipt["existing_row_defects"]}
        self.assertEqual(live, {(i["task_id"], i["predicate"]) for i in fixture["items"]})
        self.assertEqual(code, 1 if live else 0)

    @staticmethod
    def conventional_source_predicate(task_id: str, rows: list[tuple[str, dict]]) -> str | None:
        """The materializer's derivation predicate applied to the conventional source path.

        Returns None when ``control/task-vectors/<task_id>.json`` would bind the
        task (identity, vector parity with the single registry vector, record
        completeness), otherwise the fail-closed predicate or a reason to skip.
        """
        conventional = f"control/task-vectors/{task_id}.json"
        if not (ROOT / conventional).is_file():
            return "CONVENTIONAL_SOURCE_ABSENT"
        declared = {r["cosv_task_vector"] for _, r in rows if isinstance(r.get("cosv_task_vector"), str) and r["cosv_task_vector"]}
        embedded = {v for _, r in rows if (v := mod.embedded_vector(r))}
        vectors = sorted(declared | embedded)
        if len(vectors) != 1:
            return "DECLARED_VECTOR_AMBIGUOUS" if vectors else "REGISTRY_VECTOR_ABSENT"
        predicate, _ = mod.inspect_source(ROOT, task_id, conventional, vectors[0])
        if predicate is None:
            predicate, _ = mod.inspect_record_completeness(ROOT, conventional)
        return predicate

    def test_closable_conventional_sources_are_bound_on_every_registry_surface(self) -> None:
        """Issue #3012 ratchet: no SOURCE_REF_ABSENT owner item may be deterministically closable.

        A vectorized registry task without an effective index row whose
        conventional ``control/task-vectors/<task_id>.json`` already passes the
        derivation predicate needs no owner action: binding the ref on every
        registry surface that carries the task closes it. Such a task must
        therefore not exist unbound, so the owner-items fixture cannot regrow
        with closable items. Surfaces are bound key-for-key (aggregate row and
        canonical shard alike, as #3110 requires) with the identical ref.
        """
        effective = mod.load_effective_index(ROOT)
        closable_unbound: dict[str, list[str]] = {}
        for task_id, rows in sorted(mod.collect_declarations(ROOT).items()):
            if task_id in effective:
                continue
            if self.conventional_source_predicate(task_id, rows) is not None:
                continue
            conventional = f"control/task-vectors/{task_id}.json"
            unbound = [ref for ref, row in rows if row.get("source_state_vector_ref") != conventional]
            if unbound:
                closable_unbound[task_id] = unbound
        self.assertEqual(
            closable_unbound,
            {},
            "closable SOURCE_REF_ABSENT items: bind source_state_vector_ref to the conventional source on every listed surface and re-run scripts/materialize_cosv_index_shards.py",
        )

    @staticmethod
    def indexed_source_predicate(task_id: str, row: dict) -> str | None:
        """The materializer's derivation predicate applied to an effective index row's own source.

        Returns None when the row's ``source_state_vector_ref`` resolves to a
        task.v1 task-level record identified as ``:task:<task_id>`` whose vector
        equals the row vector (verify_task_pointer parity) and which is a
        complete COSV record (what the index completeness test requires of
        every registry-bound source), otherwise the fail-closed predicate.
        """
        ref = row.get("source_state_vector_ref")
        if not isinstance(ref, str) or not ref:
            return "SOURCE_REF_ABSENT"
        vector = row.get("vector") if isinstance(row.get("vector"), str) else row.get("cosv_task_vector")
        predicate, _ = mod.inspect_source(ROOT, task_id, ref, vector)
        if predicate is None:
            predicate, _ = mod.inspect_record_completeness(ROOT, ref)
        return predicate

    @staticmethod
    def vector_declaring_surfaces(rows: list[tuple[str, dict]], vector: str) -> list[tuple[str, dict]] | None:
        """Registry surfaces that declare a COSV vector for the task.

        Returns None when any surface declares a vector other than ``vector``:
        such a task is a registry/index VECTOR_VALUE_MISMATCH owner item and
        binding a source on it would deepen the disagreement, not close it.
        """
        surfaces: list[tuple[str, dict]] = []
        for ref, row in rows:
            declared = {row.get("cosv_task_vector"), mod.embedded_vector(row)} - {None, ""}
            if not declared:
                continue
            if declared != {vector}:
                return None
            surfaces.append((ref, row))
        return surfaces

    def test_indexed_tasks_with_verified_sources_are_bound_on_every_vectorized_registry_surface(self) -> None:
        """Issue #3012: an indexed task whose source verifies must name it on every registry surface.

        A task with an effective index row whose ``source_state_vector_ref``
        passes the derivation predicate has a deterministic binding: the index
        already resolves it. Every registry surface that declares the task's
        COSV vector (aggregate row and canonical shard alike, as #3110 requires
        key-for-key agreement) must therefore carry that identical ref, so no
        surface silently depends on the index for a source it could name.
        Surfaces that declare no vector are not vectorized and out of scope
        (a bare ref without a vector is the materializer's
        REGISTRY_VECTOR_ABSENT shape); a task whose surfaces disagree with the
        index vector is excluded as a VECTOR_VALUE_MISMATCH owner item.
        """
        effective = mod.load_effective_index(ROOT)
        declarations = mod.collect_declarations(ROOT)
        unbound: dict[str, list[str]] = {}
        for task_id, (_, row) in sorted(effective.items()):
            rows = declarations.get(task_id)
            if not rows or self.indexed_source_predicate(task_id, row) is not None:
                continue
            surfaces = self.vector_declaring_surfaces(rows, row["vector"])
            if surfaces is None:
                continue
            missing = [ref for ref, r in surfaces if r.get("source_state_vector_ref") != row["source_state_vector_ref"]]
            if missing:
                unbound[task_id] = missing
        self.assertEqual(
            unbound,
            {},
            "indexed tasks whose source verifies: bind the index row's source_state_vector_ref on every listed surface, identical value, directly after cosv_task_vector",
        )

    def test_issue_3012_indexed_tasks_bound_on_every_vectorized_surface_are_pinned(self) -> None:
        bound = {
            "GADI-001",
            "GADI-RESIDENT-EXECUTION-001",
            "GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001",
            "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001",
            "GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001",
            "GP10-COMMERCIAL-RESPONSE-VALIDATION-001",
            "HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001",
            "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001",
            "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001",
            "MIR-TVC-PROVIDER-ROUNDTRIP-001",
            "ORG-GITHUB-FLEET-FUNCTIONALIZATION-001",
            "PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001",
            "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001",
            "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
            "SS-ERL-KV-PROPAGATION-VERIFICATION-001",
            "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001",
            "STEG-BROWSER-RUNTIME-CONSUMPTION-001",
            "STEGAGENTS-GOVERNED-RUNTIME-001",
            "STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001",
            "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001",
            "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
            "STEGOS-LOCAL-AI-ENTITY-CHATGPT-001",
            "STEGOS-LOCAL-AI-ENTITY-CLAUDE-CODE-001",
            "STEGVERSE-BUSINESS-OPPORTUNITY-ENGINE-PILOT-001",
            "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001",
            "STRIPE-GODADDY-PROVIDER-EQUIVALENCE-001",
        }
        declarations = mod.collect_declarations(ROOT)
        effective = mod.load_effective_index(ROOT)
        for task_id in sorted(bound):
            origin, row = effective[task_id]
            self.assertIsNone(self.indexed_source_predicate(task_id, row), task_id)
            self.assertEqual(row["source_state_vector_ref"], f"control/task-vectors/{task_id}.json", task_id)
            surfaces = self.vector_declaring_surfaces(declarations[task_id], row["vector"])
            self.assertTrue(surfaces, task_id)
            for ref, surface in surfaces:
                self.assertEqual(surface.get("source_state_vector_ref"), row["source_state_vector_ref"], f"{task_id} unbound on {ref}")
                keys = list(surface)
                if "cosv_task_vector" in keys:
                    self.assertEqual(keys.index("source_state_vector_ref"), keys.index("cosv_task_vector") + 1, f"{task_id} ref not directly after cosv_task_vector on {ref}")
            if origin == "aggregate" and any(ref == "data/canonical-task-registry.json" for ref, _ in surfaces):
                # The canonical registry now binds the task, so the aggregate row
                # must name it as the registry surface it resolves from.
                self.assertEqual(row["registry_ref"], "data/canonical-task-registry.json", task_id)

    def test_issue_3012_bound_tasks_carry_the_conventional_ref_on_every_surface(self) -> None:
        bound = {
            "MYKV-HEALTHCARE-TRANSACTION-EVIDENCE-001",
            "MYKV-PERSONAL-DATA-BACKUP-001",
            "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001",
            "SS-ERL-AUTHENTIC-INTR-EXECUTION-EVIDENCE-002",
            "SS-EVIDENCE-COMPARISON-001",
            "SS-KV-SKAP-SOCIAL-RELEASE-001",
            "STEGOS-AI-PREEXECUTION-RUNTIME-PROOF-001",
        }
        declarations = mod.collect_declarations(ROOT)
        effective = mod.load_effective_index(ROOT)
        fixture = json.loads(OWNER_ITEMS.read_text(encoding="utf-8"))
        acknowledged = {item["task_id"] for item in fixture["items"]}
        for task_id in sorted(bound):
            conventional = f"control/task-vectors/{task_id}.json"
            rows = declarations[task_id]
            self.assertIsNone(self.conventional_source_predicate(task_id, rows), task_id)
            for ref, row in rows:
                self.assertEqual(row.get("source_state_vector_ref"), conventional, f"{task_id} unbound on {ref}")
                self.assertEqual(row.get("cosv_task_vector"), effective[task_id][1]["vector"], f"{task_id} vector drift on {ref}")
            origin, index_row = effective[task_id]
            self.assertEqual(origin, f"control/task-vector-index.d/{task_id}.json", task_id)
            self.assertEqual(index_row["source_state_vector_ref"], conventional, task_id)
            self.assertEqual((index_row["vector_state"], index_row["authority_effect"]), ("EMITTED", "NONE"), task_id)
            self.assertNotIn(task_id, acknowledged, f"{task_id} is bound and must not remain an owner item")


class TempTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write(
            self.root / "control" / "task-vector-index.json",
            {"profile": "task.v1", "authority_effect": "NONE", "tasks": []},
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def registry(self, task: dict, *, path: str = "data/canonical-task-records/" + TASK + ".json") -> None:
        write(self.root / path, {"task_id": TASK, **task})

    def run_mod(self, *argv: str) -> tuple[int, dict]:
        import contextlib
        import io

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = mod.main(["--root", str(self.root), *argv])
        return code, json.loads(out.getvalue())

    def single_failure(self, receipt: dict) -> dict:
        self.assertEqual(receipt["added"], [])
        self.assertEqual(len(receipt["skipped_fail_closed"]), 1, receipt)
        self.assertFalse((self.root / "control" / "task-vector-index.d" / f"{TASK}.json").exists())
        return receipt["skipped_fail_closed"][0]

    def test_derives_full_shape_shard_from_matching_source(self) -> None:
        self.registry(
            {
                "repository": "StegVerse-Labs/.github",
                "cosv_task_vector": VECTOR,
                "source_state_vector_ref": f"control/task-vectors/{TASK}.json",
                "handoff_ref": f"handoffs/{TASK}.json",
            }
        )
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        code, receipt = self.run_mod("--check")
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "DRIFT")
        self.assertEqual(receipt["added"], [TASK])
        self.assertFalse((self.root / "control" / "task-vector-index.d").exists())

        code, receipt = self.run_mod()
        self.assertEqual(code, 0)
        self.assertEqual(receipt["added"], [TASK])
        shard = json.loads((self.root / "control" / "task-vector-index.d" / f"{TASK}.json").read_text(encoding="utf-8"))
        self.assertEqual(
            shard,
            {
                "schema": "stegverse.cosv-task-vector-index-entry/v1",
                "task_id": TASK,
                "repository": "StegVerse-Labs/.github",
                "registry_ref": f"data/canonical-task-records/{TASK}.json",
                "source_state_vector_ref": f"control/task-vectors/{TASK}.json",
                "cosv_task_vector": VECTOR,
                "vector": VECTOR,
                "vector_state": "EMITTED",
                "profile": "task.v1",
                "authority_effect": "NONE",
                "handoff_ref": f"handoffs/{TASK}.json",
            },
        )
        self.assertEqual(list(shard), ["schema", "task_id", "repository", "registry_ref", "source_state_vector_ref", "cosv_task_vector", "vector", "vector_state", "profile", "authority_effect", "handoff_ref"])

        code, receipt = self.run_mod("--check")
        self.assertEqual((code, receipt["status"], receipt["added"]), (0, "OK", []))

    def test_binding_surface_is_the_registry_that_names_the_source(self) -> None:
        # Canonical aggregate declares the vector; the worker registry shard carries the machine binding.
        write(self.root / "data" / "canonical-task-registry.json", {"tasks": [{"task_id": TASK, "repository": "StegVerse-Labs/.github", "cosv_task_vector": VECTOR}]})
        write(
            self.root / "control" / "worker-registry.d" / "unit.json",
            {"tasks": [{"task_id": TASK, "source_state_vector_ref": f"control/task-vectors/{TASK}.json", "machine_readable_state": {"cosv": {"vector": VECTOR}}}]},
        )
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        code, receipt = self.run_mod()
        self.assertEqual(receipt["added"], [TASK], receipt)
        shard = json.loads((self.root / "control" / "task-vector-index.d" / f"{TASK}.json").read_text(encoding="utf-8"))
        self.assertEqual(shard["registry_ref"], "control/worker-registry.d/unit.json")
        self.assertEqual(shard["repository"], "StegVerse-Labs/.github")

    def test_source_ref_absent_fails_closed_even_with_conventional_file(self) -> None:
        self.registry({"cosv_task_vector": VECTOR})
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        code, receipt = self.run_mod("--check")
        failure = self.single_failure(receipt)
        self.assertEqual(failure["predicate"], "SOURCE_REF_ABSENT")
        self.assertTrue(failure["conventional_source_present"])
        self.assertEqual((code, receipt["status"]), (1, "FAIL_CLOSED"))

    def test_source_ref_conflict_fails_closed(self) -> None:
        write(self.root / "data" / "canonical-task-registry.json", {"tasks": [{"task_id": TASK, "cosv_task_vector": VECTOR, "source_state_vector_ref": "control/task-vectors/a.json"}]})
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": "control/task-vectors/b.json"})
        _, receipt = self.run_mod("--check")
        self.assertEqual(self.single_failure(receipt)["predicate"], "SOURCE_REF_CONFLICT")

    def test_registry_vector_absent_fails_closed(self) -> None:
        self.registry({"source_state_vector_ref": f"control/task-vectors/{TASK}.json"})
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        _, receipt = self.run_mod("--check")
        self.assertEqual(self.single_failure(receipt)["predicate"], "REGISTRY_VECTOR_ABSENT")

    def test_vector_source_not_materialized_fails_closed(self) -> None:
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": f"control/task-vectors/{TASK}.json"})
        _, receipt = self.run_mod("--check")
        self.assertEqual(self.single_failure(receipt)["predicate"], "VECTOR_SOURCE_NOT_MATERIALIZED")

    def test_vector_source_escaping_root_fails_closed(self) -> None:
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": "../outside.json"})
        write(self.root.parent / "outside.json", vector_record())
        try:
            _, receipt = self.run_mod("--check")
            self.assertEqual(self.single_failure(receipt)["predicate"], "VECTOR_SOURCE_NOT_MATERIALIZED")
        finally:
            (self.root.parent / "outside.json").unlink()

    def test_vector_identity_mismatch_fails_closed(self) -> None:
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": f"control/task-vectors/{TASK}.json"})
        for bad in (
            {"identity": "StegVerse-Labs/.github:task:OTHER-001"},
            {"level": None},
            {"profile": "repo.v1"},
        ):
            write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record(**bad))
            _, receipt = self.run_mod("--check")
            self.assertEqual(self.single_failure(receipt)["predicate"], "VECTOR_IDENTITY_MISMATCH", bad)

    def test_vector_value_mismatch_fails_closed(self) -> None:
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": f"control/task-vectors/{TASK}.json"})
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record(vector="71000000111110"))
        _, receipt = self.run_mod("--check")
        self.assertEqual(self.single_failure(receipt)["predicate"], "VECTOR_VALUE_MISMATCH")

        # Registry surfaces disagreeing with each other is also a value mismatch.
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        write(self.root / "data" / "canonical-task-registry.json", {"tasks": [{"task_id": TASK, "cosv_task_vector": "71000000111110"}]})
        _, receipt = self.run_mod("--check")
        self.assertEqual(self.single_failure(receipt)["predicate"], "VECTOR_VALUE_MISMATCH")

    def test_vector_source_incomplete_fails_closed_for_new_derivations_only(self) -> None:
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": f"control/task-vectors/{TASK}.json"})
        for incomplete in (
            {"exact_metrics": {"lifecycle": "COMPLETE"}},
            {"observed_at": None},
            {"evidence_refs": []},
        ):
            record = vector_record(**incomplete)
            if incomplete.get("observed_at", "x") is None:
                record.pop("observed_at")
            write(self.root / "control" / "task-vectors" / f"{TASK}.json", record)
            _, receipt = self.run_mod("--check")
            self.assertEqual(self.single_failure(receipt)["predicate"], "VECTOR_SOURCE_INCOMPLETE", incomplete)

        # An existing row bound to the same incomplete record is still a valid runtime pointer.
        write(
            self.root / "control" / "task-vector-index.d" / f"{TASK}.json",
            {
                "schema": "stegverse.cosv-task-vector-index-entry/v1",
                "task_id": TASK,
                "registry_ref": f"data/canonical-task-records/{TASK}.json",
                "source_state_vector_ref": f"control/task-vectors/{TASK}.json",
                "vector": VECTOR,
                "vector_state": "EMITTED",
                "authority_effect": "NONE",
            },
        )
        code, receipt = self.run_mod("--check")
        self.assertEqual((code, receipt["status"], receipt["existing_row_defects"]), (0, "OK", []))

    def test_existing_vector_only_shard_is_normalized_only_when_source_matches(self) -> None:
        shard_path = self.root / "control" / "task-vector-index.d" / f"{TASK}.json"
        shard = {
            "schema": "stegverse.cosv-task-vector-index-entry/v1",
            "task_id": TASK,
            "registry_ref": f"data/canonical-task-records/{TASK}.json",
            "source_state_vector_ref": f"control/task-vectors/{TASK}.json",
            "cosv_task_vector": VECTOR,
            "handoff_ref": f"handoffs/{TASK}.json",
        }
        write(shard_path, shard)
        self.registry({"cosv_task_vector": VECTOR, "source_state_vector_ref": f"control/task-vectors/{TASK}.json"})

        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record(level=None))
        code, receipt = self.run_mod("--normalize-shards")
        self.assertEqual(receipt["normalized"], [])
        self.assertEqual([x["predicate"] for x in receipt["existing_row_defects"]], ["VECTOR_IDENTITY_MISMATCH"])
        self.assertEqual(json.loads(shard_path.read_text(encoding="utf-8")), shard)

        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        code, receipt = self.run_mod("--check")
        self.assertEqual(code, 1)
        self.assertEqual([x["predicate"] for x in receipt["existing_row_defects"]], ["INDEX_ROW_VECTOR_ABSENT"])
        code, receipt = self.run_mod("--normalize-shards")
        self.assertEqual((code, receipt["normalized"]), (0, [TASK]))
        normalized = json.loads(shard_path.read_text(encoding="utf-8"))
        self.assertEqual(list(normalized), ["schema", "task_id", "registry_ref", "source_state_vector_ref", "cosv_task_vector", "vector", "vector_state", "authority_effect", "handoff_ref"])
        self.assertEqual((normalized["vector"], normalized["vector_state"], normalized["authority_effect"]), (VECTOR, "EMITTED", "NONE"))
        code, receipt = self.run_mod("--check")
        self.assertEqual((code, receipt["status"]), (0, "OK"))

    def test_aggregate_rows_are_never_rewritten(self) -> None:
        aggregate = self.root / "control" / "task-vector-index.json"
        payload = {
            "profile": "task.v1",
            "authority_effect": "NONE",
            "tasks": [{"task_id": TASK, "registry_ref": "x", "source_state_vector_ref": f"control/task-vectors/{TASK}.json", "cosv_task_vector": VECTOR}],
        }
        write(aggregate, payload)
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        before = aggregate.read_text(encoding="utf-8")
        code, receipt = self.run_mod("--normalize-shards")
        self.assertEqual(receipt["normalized"], [])
        self.assertEqual([x["predicate"] for x in receipt["existing_row_defects"]], ["INDEX_ROW_VECTOR_ABSENT"])
        self.assertEqual(aggregate.read_text(encoding="utf-8"), before)

    def test_live_worker_coverage_counters_are_checked_and_rewritten_from_the_effective_index(self) -> None:
        write(self.root / "control" / "worker-registry.json", {"tasks": [{"task_id": TASK}, {"task_id": "UNIT-TERMINAL-001"}]})
        write(self.root / "control" / "worker-registry.d" / "unit.json", {"tasks": [{"task_id": "UNIT-ACTIVE-UNVECTORIZED-001"}, {"task_id": TASK}]})
        write(
            self.root / "control" / "task-vector-index.d" / f"{TASK}.json",
            {
                "schema": "stegverse.cosv-task-vector-index-entry/v1",
                "task_id": TASK,
                "registry_ref": f"data/canonical-task-records/{TASK}.json",
                "source_state_vector_ref": f"control/task-vectors/{TASK}.json",
                "vector": VECTOR,
                "vector_state": "EMITTED",
                "authority_effect": "NONE",
            },
        )
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        coverage_path = self.root / "control" / "cosv-live-worker-coverage.json"
        stale = {
            "schema": "stegverse.cosv-live-worker-coverage/v1",
            "unique_task_ids_global_plus_fragments": 1,
            "canonically_indexed_task_ids": 1,
            "completed_only_historical_unvectorized_task_count": 1,
            "superseded_historical_unvectorized_task_count": 0,
            "active_unvectorized_unique_task_ids": 0,
            "active_worker_task_ids_missing_canonical_cosv": [],
            "terminal_historical_unvectorized_task_ids": ["UNIT-TERMINAL-001"],
            "superseded_historical_unvectorized_task_ids": [],
            "organization_active_unvectorized_task_ids": 2,
            "total_active_unvectorized_unique_task_ids": 2,
            "authority_effect": "NONE",
        }
        write(coverage_path, stale)

        code, receipt = self.run_mod("--check")
        self.assertEqual((code, receipt["status"]), (1, "DRIFT"))
        self.assertEqual(receipt["existing_row_defects"], [])
        self.assertEqual(
            {(x["surface"], x["field"]) for x in receipt["coverage_drift"]},
            {
                ("control/cosv-live-worker-coverage.json", "unique_task_ids_global_plus_fragments"),
                ("control/cosv-live-worker-coverage.json", "active_unvectorized_unique_task_ids"),
                ("control/cosv-live-worker-coverage.json", "active_worker_task_ids_missing_canonical_cosv"),
                ("control/cosv-live-worker-coverage.json", "total_active_unvectorized_unique_task_ids"),
            },
        )
        self.assertEqual(receipt["coverage"]["live_worker"]["active_worker_task_ids_missing_canonical_cosv"], ["UNIT-ACTIVE-UNVECTORIZED-001"])
        self.assertEqual(receipt["coverage"]["live_worker"]["total_active_unvectorized_unique_task_ids"], 3)
        self.assertEqual(json.loads(coverage_path.read_text(encoding="utf-8")), stale)

        # Write mode without --coverage reports the drift but leaves the file alone.
        code, receipt = self.run_mod()
        self.assertEqual((code, receipt["status"], receipt["coverage"]["written"]), (0, "DRIFT", []))
        self.assertEqual(json.loads(coverage_path.read_text(encoding="utf-8")), stale)

        code, receipt = self.run_mod("--coverage")
        self.assertEqual((code, receipt["status"], receipt["coverage"]["written"]), (0, "OK", ["control/cosv-live-worker-coverage.json"]))
        rewritten = json.loads(coverage_path.read_text(encoding="utf-8"))
        self.assertEqual(list(rewritten), list(stale), "key order preserved")
        self.assertEqual(rewritten["unique_task_ids_global_plus_fragments"], 3)
        self.assertEqual(rewritten["canonically_indexed_task_ids"], 1)
        self.assertEqual(rewritten["completed_only_historical_unvectorized_task_count"], 1)
        self.assertEqual(rewritten["active_unvectorized_unique_task_ids"], 1)
        self.assertEqual(rewritten["active_worker_task_ids_missing_canonical_cosv"], ["UNIT-ACTIVE-UNVECTORIZED-001"])
        self.assertEqual(rewritten["total_active_unvectorized_unique_task_ids"], 3)
        self.assertEqual(rewritten["terminal_historical_unvectorized_task_ids"], ["UNIT-TERMINAL-001"], "owner facts are never derived")
        self.assertEqual(rewritten["organization_active_unvectorized_task_ids"], 2)

        code, receipt = self.run_mod("--check")
        self.assertEqual((code, receipt["status"], receipt["coverage_drift"]), (0, "OK", []))

        # A historical id that is no longer an unindexed worker task breaks the partition.
        rewritten["terminal_historical_unvectorized_task_ids"] = [TASK]
        write(coverage_path, rewritten)
        code, receipt = self.run_mod("--check")
        self.assertEqual(code, 1)
        self.assertIn("historical_unvectorized_task_ids", {x["field"] for x in receipt["coverage_drift"]})

    def test_aggregate_index_coverage_block_is_checked_but_never_written(self) -> None:
        aggregate = self.root / "control" / "task-vector-index.json"
        write(
            aggregate,
            {
                "profile": "task.v1",
                "authority_effect": "NONE",
                "coverage": {"indexed_vectorized_tasks": 1, "local_cosv_record_tasks": 1, "external_owner_projection_tasks": 0},
                "tasks": [
                    {"task_id": TASK, "registry_ref": "x", "source_state_vector_ref": f"control/task-vectors/{TASK}.json", "vector": VECTOR, "vector_state": "EMITTED", "authority_effect": "NONE"},
                    {"task_id": "UNIT-EXTERNAL-001", "registry_ref": "x", "source_state_vector_ref": "external/UNIT-EXTERNAL-001.json", "vector": VECTOR, "vector_state": "EMITTED", "authority_effect": "NONE"},
                ],
            },
        )
        write(self.root / "control" / "task-vectors" / f"{TASK}.json", vector_record())
        write(self.root / "external" / "UNIT-EXTERNAL-001.json", vector_record(task_id="UNIT-EXTERNAL-001"))
        before = aggregate.read_text(encoding="utf-8")
        code, receipt = self.run_mod("--check", "--coverage")
        self.assertEqual((code, receipt["status"]), (1, "DRIFT"))
        self.assertEqual(
            [(x["field"], x["stored"], x["derived"]) for x in receipt["coverage_drift"]],
            [("indexed_vectorized_tasks", 1, 2), ("external_owner_projection_tasks", 0, 1)],
        )
        code, receipt = self.run_mod("--coverage")
        self.assertEqual((code, receipt["status"], receipt["coverage"]["written"]), (0, "DRIFT", []))
        self.assertEqual(aggregate.read_text(encoding="utf-8"), before)

    def test_owner_items_defer_acknowledged_predicates_and_flag_stale_entries(self) -> None:
        self.registry({"cosv_task_vector": VECTOR})
        owner = self.root / "owner-items.json"
        write(owner, {"schema": mod.OWNER_ITEMS_SCHEMA, "items": [{"task_id": TASK, "predicate": "SOURCE_REF_ABSENT"}]})
        code, receipt = self.run_mod("--check", "--owner-items", str(owner))
        self.assertEqual((code, receipt["status"]), (0, "OK"))
        self.assertEqual(receipt["deferred_owner_items"], [{"task_id": TASK, "predicate": "SOURCE_REF_ABSENT"}])

        # A different predicate for the same task is not covered.
        write(owner, {"schema": mod.OWNER_ITEMS_SCHEMA, "items": [{"task_id": TASK, "predicate": "VECTOR_VALUE_MISMATCH"}]})
        code, receipt = self.run_mod("--check", "--owner-items", str(owner))
        self.assertEqual(code, 1)
        self.assertEqual([x["predicate"] for x in receipt["skipped_fail_closed"]], ["SOURCE_REF_ABSENT"])
        self.assertEqual(receipt["stale_owner_items"], [f"{TASK}:VECTOR_VALUE_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
