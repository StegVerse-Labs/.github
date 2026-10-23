"""scripts/adjacency_ruling_conditions.py: consumed-source pin (P) and owner routing (R). E0: stdlib + local git."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("adjacency_ruling_conditions_under_test",
                                              ROOT / "scripts" / "adjacency_ruling_conditions.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
RULING = ROOT / "control" / "adjacency-rulings" / "GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001.json"
OWNER = "OWNER-TASK-001"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def git(root: Path, *args: str) -> str:
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z", "PATH": "/usr/bin:/bin"}
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()


class Fixture:
    """owner commit with two consumed files; subject commit adding the finish test (optionally editing a file)."""

    def __init__(self, tmp: Path, *, edit_consumed: bool = False, test_carries_pin: bool = True):
        self.root = tmp
        git(tmp, "init", "-q")
        (tmp / "gate").mkdir()
        (tmp / "gate" / "step.yml").write_text("run: exit 1\n", encoding="utf-8")
        (tmp / "gate" / "reader.py").write_text("def read():\n    return 'FAIL_CLOSED'\n", encoding="utf-8")
        git(tmp, "add", "gate")
        git(tmp, "commit", "-q", "-m", "owner")
        self.pin_commit = git(tmp, "rev-parse", "HEAD")
        self.files = {rel: hashlib.sha256((tmp / rel).read_bytes()).hexdigest() for rel in ("gate/step.yml", "gate/reader.py")}
        (tmp / "tests").mkdir()
        carried = f"PIN = {json.dumps({'commit': self.pin_commit, 'files': self.files})}\n" if test_carries_pin else "PIN = {}\n"
        (tmp / "tests" / "test_fp.py").write_text(carried, encoding="utf-8")
        if edit_consumed:
            (tmp / "gate" / "reader.py").write_text("def read():\n    return 'ALLOW'\n", encoding="utf-8")
        git(tmp, "add", "-A")
        git(tmp, "commit", "-q", "-m", "subject")
        self.head = git(tmp, "rev-parse", "HEAD")

    def ruling(self) -> dict:
        paths = sorted(self.files)
        return {
            "schema": "stegverse.adjacency-ruling/v1",
            "subject": {"finish_point": {"acceptance_test": "o/r:tests/test_fp.py::C::t", "repository": "o/r",
                                         "source_commit": self.head}},
            "candidates": [{"task_id": OWNER, "finish_point_paths": paths}, {"task_id": "OTHER-001", "finish_point_paths": []}],
            "consumes_dependencies": [{"task_id": OWNER, "pinned_source": {"repository": "o/r", "commit": self.pin_commit,
                                                                           "files": dict(self.files)}}],
            "protected_paths": [{"repository": "o/r", "owner_task_id": OWNER, "paths": paths,
                                 "on_modification": {"disposition": "FAIL_CLOSED", "failure_code": "OWNER_OWNED_EDIT",
                                                     "routed_to": OWNER}}],
        }


class AdjacencyRulingConditions(unittest.TestCase):
    def assertRefused(self, body: dict, code: str, owner: str = M.OWNING_GOAL) -> None:
        self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
        self.assertEqual(body["failure_code"], code, body)
        for field in SIX:
            self.assertTrue(body[field], field)
        self.assertEqual(body["owning_existing_goal"], owner)

    def test_pinned_and_routed_consumes_dependency_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            body = M.verify(fx.ruling(), fx.root)
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["pins"][0]["condition_pin"], "HELD")

    def test_subject_edit_of_a_protected_path_fails_closed_routed_to_the_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp), edit_consumed=True)
            body = M.verify(fx.ruling(), fx.root)
            change = M.check_change(fx.ruling(), fx.root, fx.pin_commit, fx.head)
        self.assertRefused(body, "OWNER_OWNED_EDIT", OWNER)
        self.assertEqual(body["detail"], {"modified": ["gate/reader.py"]})
        self.assertRefused(change, "OWNER_OWNED_EDIT", OWNER)

    def test_change_outside_protected_paths_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            body = M.check_change(fx.ruling(), fx.root, fx.pin_commit, fx.head)
        self.assertEqual(body["disposition"], "ALLOW", body)

    def test_wrong_pinned_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            ruling = fx.ruling()
            ruling["consumes_dependencies"][0]["pinned_source"]["files"]["gate/step.yml"] = "0" * 64
            body = M.verify(ruling, fx.root)
        self.assertRefused(body, "ADJACENCY_RULING_CONSUMED_PIN_DIGEST_DIVERGES")

    def test_finish_test_that_does_not_carry_the_pin_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp), test_carries_pin=False)
            body = M.verify(fx.ruling(), fx.root)
        self.assertRefused(body, "ADJACENCY_RULING_FINISH_TEST_DOES_NOT_ENFORCE_PIN")

    def test_unavailable_pinned_commit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            ruling = fx.ruling()
            ruling["consumes_dependencies"][0]["pinned_source"]["commit"] = "1" * 40
            ruling["protected_paths"][0]["paths"] = sorted(fx.files)
            body = M.verify(ruling, fx.root)
        self.assertRefused(body, "ADJACENCY_RULING_CONSUMED_PIN_COMMIT_UNAVAILABLE")

    def test_relied_paths_without_pin_or_route_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            no_pin = fx.ruling()
            no_pin["consumes_dependencies"][0].pop("pinned_source")
            no_pin["protected_paths"] = []
            unrouted = fx.ruling()
            unrouted["protected_paths"][0]["paths"] = ["gate/step.yml"]
            misrouted = fx.ruling()
            misrouted["protected_paths"][0]["on_modification"]["routed_to"] = "SOMEONE-ELSE"
            self.assertRefused(M.verify(no_pin, fx.root), "ADJACENCY_RULING_RELIED_PATHS_UNPINNED")
            self.assertRefused(M.verify(unrouted, fx.root), "ADJACENCY_RULING_PROTECTED_PATHS_UNROUTED")
            self.assertRefused(M.verify(misrouted, fx.root), "ADJACENCY_RULING_PROTECTED_PATHS_MALFORMED")

    def test_committed_governance_ruling_is_well_formed_for_both_conditions(self) -> None:
        ruling = json.loads(RULING.read_text(encoding="utf-8"))
        _fp, pins, routes = M.structure(copy.deepcopy(ruling))
        structural = "SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001"
        self.assertEqual(sorted(pins), [structural])
        self.assertRegex(pins[structural]["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(sorted(pins[structural]["files"]), [".github/workflows/governance-gate.yml", "stegverse/governance_gate.py"])
        self.assertEqual([(r["owner_task_id"], r["on_modification"]["failure_code"]) for r in routes],
                         [(structural, "STRUCTURAL_OWNED_EDIT")])


if __name__ == "__main__":
    unittest.main()
