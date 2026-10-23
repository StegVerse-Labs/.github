"""Adjacency-ruling input to the collision check-in (scripts/adjacency_ruling.py), both ways, E0, no network.

A ruling is never trusted: each test changes observed state (records, the finish-point source) or the ruling
itself and checks the recomputation, not the ruling's claims, decides.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KV_REQUEST = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "i1-goal-manifests" / "KV-SKAP-VAULT-FUNCTIONAL-001.request.json"
KV_RULING = ROOT / "control" / "adjacency-rulings" / "KV-SKAP-VAULT-FUNCTIONAL-001.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ar = _load("adjacency_ruling_under_test", "scripts/adjacency_ruling.py")
transition = _load("transition_under_test_for_ruling", "scripts/canonical_task_registration_transition.py")


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def make_repo(files: dict[str, str]) -> tuple[Path, str]:
    root = Path(tempfile.mkdtemp(prefix="fp-repo-"))
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "fixture")
    return root, git(root, "rev-parse", "HEAD")


OWN_TEST = ("import subprocess\nfrom runtime import vault\n"
            "def test_x():\n    subprocess.run(['python', '-m', 'runtime.vault'])\n")
FILES = {"tests/test_fp.py": OWN_TEST, "runtime/vault.py": "import json\n",
         "runtime/task_registry_binding.py": "X = 1\n", "runtime/helper.py": "Y = 2\n"}


def candidate(task_id="CAND-A-001", components=("task-registry", "custody-projection"), refs=()):
    return {"schema": "stegverse.canonical-task-record/v1", "task_id": task_id, "parent_task_id": None,
            "root_correlation_id": task_id, "coordination_state": "ACTIVE",
            "targets": {"repositories": ["Org/fp"], "components": list(components)},
            "source_refs": list(refs), "adjacent_task_refs": []}


def request(components=("vault-module", "consent-receipt"), deps=("CAND-A-001",),
            test="Org/fp:tests/test_fp.py::test_x"):
    record = {"task_id": "SUBJ-001", "parent_task_id": None, "root_correlation_id": "SUBJ-001",
              "targets": {"repositories": ["Org/fp"], "components": list(components)},
              "dependencies": [{"dependency_id": f"TASK-{d}", "kind": "TASK", "state": "UNRESOLVED", "ref": d} for d in deps],
              "adjacent_task_refs": ["CAND-A-001"]}
    return {"task_id": "SUBJ-001", "record": record,
            "sealed_scope": {"scope": {"finish_point": {"acceptance_test": test}}}}


def ruling(commit, req, cands, consumes=("CAND-A-001",)):
    body = {"schema": ar.SCHEMA, "task_id": "SUBJ-001", "ruling_class": "D", "ruling": "ADJACENT_NOT_DUPLICATE",
            "ruled_by": "Coordination (test)",
            "subject": {"components": sorted(req["record"]["targets"]["components"]),
                        "finish_point": {"acceptance_test": req["sealed_scope"]["scope"]["finish_point"]["acceptance_test"],
                                         "repository": "Org/fp", "source_commit": commit}},
            "candidates": [{"task_id": c["task_id"], "components": sorted(c["targets"]["components"]),
                            "finish_point_paths": []} for c in cands],
            "consumes_dependencies": [{"task_id": t} for t in consumes], "evidence_digest": ""}
    body["evidence_digest"] = ar.ruling_digest(body)
    return body


class AdjacencyRulingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="ruling-base-"))
        shutil.copytree(ROOT / "scripts", self.base / "scripts")
        (self.base / ar.RECORDS).mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.base, True)

    def put(self, record) -> None:
        (self.base / ar.RECORDS / f"{record['task_id']}.json").write_text(json.dumps(record), encoding="utf-8")

    def fp(self, files=None):
        root, commit = make_repo(files or FILES)
        self.addCleanup(shutil.rmtree, root, True)
        return root, commit

    def refused(self, verdict, code):
        self.assertEqual(verdict["disposition"], "FAIL_CLOSED", verdict)
        self.assertEqual(verdict["failure_code"], code, verdict)
        for field in SIX:
            self.assertTrue(verdict[field], field)

    # -- ALLOW ------------------------------------------------------------------------------------------------
    def test_conditions_recompute_and_allow(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        self.assertEqual(sorted(verdict["finish_point"]["closure"]),
                         ["runtime/vault.py", "tests/test_fp.py"])
        self.assertEqual(verdict["candidates"][0]["condition_b"], "HELD")
        self.assertFalse(verdict["clock_read"] or verdict["network_used"] or verdict["llm_used"])

    def test_subprocess_module_string_is_in_the_closure(self) -> None:
        files = dict(FILES, **{"tests/test_fp.py": "import subprocess\nsubprocess.run(['python','-m','runtime.helper'])\n"})
        root, commit = self.fp(files)
        self.assertIn("runtime/helper.py", ar.static_closure(root, "tests/test_fp.py"))

    # -- (b) recomputed ---------------------------------------------------------------------------------------
    def test_b_fails_when_the_test_reaches_a_module_named_for_a_candidate_component(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp(dict(FILES, **{"tests/test_fp.py": "from runtime import task_registry_binding\n"}))
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"][0]["component"], "task-registry")

    def test_b_fails_when_the_test_reaches_a_path_the_candidate_names(self) -> None:
        cand = candidate(refs=["Org/fp/runtime/helper.py"])
        self.put(cand)
        root, commit = self.fp(dict(FILES, **{"runtime/vault.py": "from runtime import helper\n"}))
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"][0]["reason"], "PATH_NAMED_BY_CANDIDATE_RECORD")

    def test_b_needs_the_source_at_the_pinned_commit(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request()
        good = ruling(commit, req, [cand])
        self.refused(ar.verify(good, req, self.base, None), "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE")
        (root / "runtime" / "vault.py").write_text("from runtime import task_registry_binding\n", encoding="utf-8")
        git(root, "commit", "-qam", "drift")
        self.refused(ar.verify(good, req, self.base, root), "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE")

    # -- (b) dynamic loads in the closure: resolved from constants, or FAIL_CLOSED ---------------------------
    RUN_GATE = ("import importlib\nfrom pathlib import Path\n"
                "def _sdk_module(name):\n    return importlib.import_module(f'pkg.{name}')\n"
                "def run_gate(manifest):\n    validator = _sdk_module('structural_validator_candidate')\n"
                "    return validator.check(manifest)\n")

    def gate_files(self, gate=None, test="from pkg import gate\ndef test_x():\n    gate.run_gate({})\n"):
        return dict(FILES, **{"tests/test_fp.py": test, "pkg/__init__.py": "", "pkg/gate.py": gate or self.RUN_GATE,
                              "pkg/structural_validator_candidate.py": "def check(m):\n    return m\n",
                              "pkg/other.py": "Z = 3\n", "pkg/tables_a.py": "", "pkg/tables_b.py": "",
                              "scripts/loaded.py": "", "pkg/sibling.py": "", "pkg/run_me.py": "", "pkg/exec_me.py": ""})

    def test_run_gate_by_name_load_is_in_the_closure_and_fails_b(self) -> None:
        root, commit = self.fp(self.gate_files())
        closure = ar.static_closure(root, "tests/test_fp.py")
        self.assertIn("pkg/structural_validator_candidate.py", closure)
        self.assertNotIn("pkg/other.py", closure)
        cand = candidate(components=("structural-validator", "validator-inventory"))
        self.put(cand)
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"][0]["path"], "pkg/structural_validator_candidate.py")

    def test_run_gate_load_with_unrelated_candidate_still_allows(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp(self.gate_files())
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        self.assertIn("pkg/structural_validator_candidate.py", verdict["finish_point"]["closure"])

    def test_constant_tables_paths_runpy_exec_and_aliases_resolve(self) -> None:
        gate = ("import importlib, importlib.util as iu, runpy\nfrom importlib import import_module as im\n"
                "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
                "MODULES = ('pkg.tables_a', 'pkg.tables_b')\nNAMES = {'x': 'pkg.other'}\n"
                "def load_all():\n    for m in MODULES:\n        importlib.import_module(m)\n"
                "    im(NAMES['x'])\n    __import__('pkg.' + 'sibling')\n"
                "    iu.spec_from_file_location('l', ROOT / 'scripts' / 'loaded.py')\n"
                "    runpy.run_path(str(Path(__file__).with_name('run_me.py')))\n"
                "    exec(compile(open(ROOT / 'pkg' / 'exec_me.py').read(), 'e', 'exec'))\n"
                "    exec('import pkg.structural_validator_candidate')\n")
        root, _ = self.fp(self.gate_files(gate))
        closure = ar.static_closure(root, "tests/test_fp.py")
        for rel in ("pkg/tables_a.py", "pkg/tables_b.py", "pkg/other.py", "pkg/sibling.py", "scripts/loaded.py",
                    "pkg/run_me.py", "pkg/exec_me.py", "pkg/structural_validator_candidate.py"):
            self.assertIn(rel, closure, rel)

    def assert_unresolved(self, gate, test=None) -> None:
        cand = candidate()
        self.put(cand)
        files = self.gate_files(gate) if test is None else self.gate_files(gate, test)
        root, commit = self.fp(files)
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_RULING_FINISH_POINT_CLOSURE_UNRESOLVED")
        self.assertEqual(verdict["detail"][0]["path"], "pkg/gate.py")

    def test_data_driven_binding_fails_closed_never_disjoint(self) -> None:
        self.assert_unresolved("import importlib\ndef _load(binding):\n"
                               "    module_name, fn = binding.rsplit('.', 1)\n"
                               "    return importlib.import_module(module_name)\n"
                               "def run_gate(route):\n    return _load(route['binding'])\n")

    def test_public_loader_parameter_fails_closed(self) -> None:
        self.assert_unresolved("import importlib\ndef load(name):\n    return importlib.import_module(name)\n"
                               "def run_gate(m):\n    return load('pkg.other')\n")

    def test_private_loader_reached_from_another_module_fails_closed(self) -> None:
        cand = candidate()
        self.put(cand)
        test = "from pkg import gate\nfrom pkg.gate import _sdk_module\ndef test_x():\n    _sdk_module('other')\n"
        root, commit = self.fp(self.gate_files(test=test))
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_RULING_FINISH_POINT_CLOSURE_UNRESOLVED")
        self.assertEqual(verdict["detail"][0]["path"], "tests/test_fp.py")

    def test_exec_of_runtime_text_and_env_paths_fail_closed(self) -> None:
        self.assert_unresolved("import os, runpy\ndef run_gate(src):\n    exec(src)\n")
        self.assert_unresolved("import os, runpy\ndef run_gate():\n    runpy.run_path(os.environ['P'])\n")

    def test_reassigned_module_constant_fails_closed(self) -> None:
        self.assert_unresolved("import importlib\nNAME = 'pkg.other'\ndef _f():\n    global NAME\n    NAME = input()\n"
                               "def run_gate():\n    importlib.import_module(NAME)\n")

    # -- (a) recomputed ---------------------------------------------------------------------------------------
    def test_a_fails_on_a_shared_component_even_if_the_ruling_omits_it(self) -> None:
        cand = candidate(components=("task-registry", "consent-receipt"))
        self.put(cand)
        root, commit = self.fp()
        req = request()
        claimed = ruling(commit, req, [cand])
        self.refused(ar.verify(claimed, req, self.base, root), "ADJACENCY_CONDITION_A_NOT_HELD")
        lying = copy.deepcopy(claimed)
        lying["candidates"][0]["components"] = ["task-registry"]
        lying["evidence_digest"] = ar.ruling_digest(lying)
        self.refused(ar.verify(lying, req, self.base, root), "ADJACENCY_RULING_COMPONENTS_DIVERGE")

    def test_a_fails_on_shared_lineage(self) -> None:
        cand = candidate()
        cand["parent_task_id"] = "SUBJ-001"
        self.put(cand)
        root, commit = self.fp()
        req = request()
        self.refused(ar.verify(ruling(commit, req, [cand]), req, self.base, root), "ADJACENCY_CONDITION_A_NOT_HELD")

    def test_a_candidate_without_declared_components_is_not_vacuously_adjacent(self) -> None:
        cand = candidate(components=())
        self.put(cand)
        root, commit = self.fp()
        req = request()
        self.refused(ar.verify(ruling(commit, req, [cand]), req, self.base, root),
                     "ADJACENCY_RULING_CANDIDATE_COMPONENTS_UNDECLARED")

    # -- (c) --------------------------------------------------------------------------------------------------
    def test_c_fails_when_the_consumes_dependency_is_not_recorded(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request(deps=())
        self.refused(ar.verify(ruling(commit, req, [cand]), req, self.base, root), "ADJACENCY_CONDITION_C_NOT_HELD")

    # -- the ruling itself ------------------------------------------------------------------------------------
    def test_ruling_integrity_class_and_scope(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request()
        good = ruling(commit, req, [cand])
        tampered = copy.deepcopy(good)
        tampered["ruled_by"] = "someone else"
        self.refused(ar.verify(tampered, req, self.base, root), "ADJACENCY_RULING_DIGEST_MISMATCH")
        dup = copy.deepcopy(good)
        dup["ruling"] = "DUPLICATE"
        dup["evidence_digest"] = ar.ruling_digest(dup)
        self.refused(ar.verify(dup, req, self.base, root), "ADJACENCY_RULING_NOT_CLASS_D_ADJACENT")
        self.refused(ar.verify({"schema": "x"}, req, self.base, root), "ADJACENCY_RULING_SCHEMA_INVALID")
        prose = request(test="Org/fp tests/test_fp.py and more, run somewhere")
        self.refused(ar.verify(ruling(commit, prose, [cand]), prose, self.base, root),
                     "ADJACENCY_RULING_FINISH_POINT_NOT_ADDRESSABLE")
        self.put(candidate("CAND-B-001", components=("other",)))
        self.refused(ar.verify(good, req, self.base, root, [{"task_id": "SUBJ-001", "head_disposition": "COORDINATE_CONVERGENCE",
                     "evidence": {"collision_candidate_ids": ["CAND-A-001", "CAND-B-001"]}}]),
                     "ADJACENCY_RULING_DOES_NOT_COVER_CHECKIN")
        self.refused(ar.verify(good, req, self.base, root, [{"task_id": "SUBJ-001", "head_disposition": "STOP_COLLISION",
                     "evidence": {"collision_candidate_ids": ["CAND-A-001"], "hard_collision_task_ids": ["CAND-A-001"]}}]),
                     "ADJACENCY_RULING_CANNOT_CLEAR_HARD_COLLISION")
        self.refused(ar.verify(good, req, self.base, root, [{"task_id": "OTHER-001", "head_disposition": "COORDINATE_CONVERGENCE",
                     "evidence": {"collision_candidate_ids": ["CAND-A-001"]}}]),
                     "ADJACENCY_RULING_DOES_NOT_COVER_CHECKIN")


class TransitionWithRulingTests(unittest.TestCase):
    """The real KV request through the real transition against this tree; the finish-point source is a local
    fixture repository at a pinned commit that mirrors the real test's import shape."""

    def fixture(self, vault_source: str) -> tuple[Path, Path]:
        root, commit = make_repo({
            "tests/test_kv_skap_vault_finish_point.py": "from runtime import kv_skap_vault as kv\n",
            "runtime/kv_skap_vault.py": vault_source,
            "runtime/secret_field_policy.py": "X = 1\n",
            "runtime/task_registry_event_sovereign_kv_binding.py": "Y = 1\n"})
        self.addCleanup(shutil.rmtree, root, True)
        rul = json.loads(KV_RULING.read_text(encoding="utf-8"))
        rul["subject"]["finish_point"]["source_commit"] = commit
        rul["evidence_digest"] = ar.ruling_digest(rul)
        path = root.parent / f"{root.name}.ruling.json"
        path.write_text(json.dumps(rul), encoding="utf-8")
        self.addCleanup(path.unlink, True)
        return root, path

    def test_without_a_ruling_the_kv_plan_stays_coordinate_convergence(self) -> None:
        body = transition.run("plan", KV_REQUEST, ROOT)
        self.assertEqual(body["disposition"], "FAIL_CLOSED")
        self.assertEqual(body["failure_code"], "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE")

    def test_a_recomputed_ruling_lets_the_kv_plan_continue(self) -> None:
        root, path = self.fixture("from runtime.secret_field_policy import X\n")
        body = transition.run("plan", KV_REQUEST, ROOT, None, path, root)
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertTrue(body["evidence"]["collision_checkin"].startswith("CONTINUE_BY_VERIFIED_ADJACENCY_RULING"))
        self.assertEqual(body["evidence"]["successor_registry_generation"], body["evidence"]["predecessor_registry_generation"] + 1)
        self.assertEqual(body["evidence"]["adjacency_ruling"]["disposition"], "ALLOW")

    def test_the_same_ruling_fails_closed_when_the_test_reaches_the_sovereign_binding(self) -> None:
        root, path = self.fixture("from runtime import task_registry_event_sovereign_kv_binding\n")
        body = transition.run("plan", KV_REQUEST, ROOT, None, path, root)
        self.assertEqual(body["disposition"], "FAIL_CLOSED")
        self.assertEqual(body["failure_code"], "ADJACENCY_CONDITION_B_NOT_HELD")
        for field in SIX:
            self.assertTrue(body[field])

    def test_committed_kv_ruling_is_sealed_and_covers_the_checkin_candidates(self) -> None:
        rul = json.loads(KV_RULING.read_text(encoding="utf-8"))
        self.assertEqual(rul["evidence_digest"], ar.ruling_digest(rul))
        req = json.loads(KV_REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(rul["subject"]["finish_point"]["acceptance_test"],
                         req["sealed_scope"]["scope"]["finish_point"]["acceptance_test"])
        self.assertEqual({c["task_id"] for c in rul["candidates"]},
                         {"SS-KV-SKAP-SOCIAL-RELEASE-001", "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
                          "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001"})


if __name__ == "__main__":
    unittest.main()
