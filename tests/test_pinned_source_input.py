"""A pinned source tree as a declared verification input (StegVerse-org/.github#163, P1).

Offline: the source repository is a local git repository built here, so nothing is fetched from the network. Each
refusal is FAIL_CLOSED with the six fields; nothing is skipped.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pinned_source_input as psi  # noqa: E402
import test_set_selection as sel  # noqa: E402
import test_suite_baseline_drift as drift  # noqa: E402

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout.strip()


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pinned-input-"))
        self.src = self.tmp / "src"
        (self.src / "fakesdk").mkdir(parents=True)
        (self.src / "fakesdk/__init__.py").write_text("VALUE = 'pinned'\n")
        (self.src / "fakesdk/sub.py").write_text("X = 1\n")
        (self.src / "unrelated").mkdir()
        (self.src / "unrelated/secret.txt").write_text("not declared\n")
        git(self.src, "init", "-q")
        git(self.src, "add", "-A")
        git(self.src, "commit", "-q", "-m", "one")
        self.commit = git(self.src, "rev-parse", "HEAD")
        self.manifest = self.tmp / "manifest.json"
        self.manifest.write_text(json.dumps({"schema": psi.SCHEMA, "input": "fakesdk", "repository": str(self.src),
                                             "exports": {"PYTHONPATH": "{root}", "FAKESDK_REQUIRED": "1"}}))
        text = json.dumps(psi.author_pin(self.manifest, "p1", self.src, self.commit, ["fakesdk"],
                                         json.loads(self.manifest.read_text())), indent=1, sort_keys=True)
        self.manifest.write_text(text)

    def tearDown(self) -> None:
        subprocess.run(["rm", "-rf", str(self.tmp)], check=False)

    def materialize(self) -> Path:
        dest = self.tmp / "in"
        psi.materialize(self.manifest, "p1", dest, str(self.src))
        return dest / "tree"

    def refused(self, fn, code: str) -> dict:
        with self.assertRaises(psi.PinRefused) as ctx:
            fn()
        record = ctx.exception.record
        self.assertEqual(code, record["failure_code"])
        self.assertEqual("FAIL_CLOSED", record["disposition"])
        for k in SIX:
            self.assertTrue(record[k], k)
        self.assertIn("#163", record["owning_existing_goal"])
        return record


class MaterializeTests(Fixture):
    def test_only_the_declared_modules_are_extracted_and_every_file_matches(self) -> None:
        tree = self.materialize()
        self.assertTrue((tree / "fakesdk/__init__.py").is_file())
        self.assertFalse((tree / "unrelated").exists())
        receipt = json.loads((tree.parent / "receipt.json").read_text())
        self.assertEqual(("ALLOW", self.commit, 2), (receipt["disposition"], receipt["commit"],
                                                      receipt["files_verified"]))
        self.assertEqual("E0", receipt["lowest_supported_mode"])

    def test_a_file_that_differs_is_refused(self) -> None:
        tree = self.materialize()
        (tree / "fakesdk/sub.py").write_text("X = 2\n")
        record = self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_SHA256_MISMATCH")
        self.assertEqual(["fakesdk/sub.py"], record["differ"])

    def test_an_undeclared_or_absent_file_is_refused(self) -> None:
        tree = self.materialize()
        (tree / "fakesdk/extra.py").write_text("")
        self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_UNDECLARED_FILE")
        (tree / "fakesdk/extra.py").unlink()
        (tree / "fakesdk/sub.py").unlink()
        self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_DECLARED_FILE_ABSENT")

    def test_a_hand_edited_manifest_is_refused(self) -> None:
        m = json.loads(self.manifest.read_text())
        m["pins"]["p1"]["modules"]["fakesdk"]["file_sha256"]["fakesdk/sub.py"] = "0" * 64
        self.manifest.write_text(json.dumps(m))
        self.refused(self.materialize, "PINNED_INPUT_MANIFEST_SEAL_MISMATCH")

    def test_an_undeclared_pin_is_refused(self) -> None:
        self.refused(lambda: psi.materialize(self.manifest, "nope", self.tmp / "x", str(self.src)),
                     "PINNED_INPUT_PIN_UNDECLARED")

    def test_a_commit_the_source_cannot_serve_is_refused(self) -> None:
        m = json.loads(self.manifest.read_text())
        m["pins"]["p1"]["commit"] = "1" * 40
        self.manifest.write_text(json.dumps(psi.sealed(m)))
        self.refused(self.materialize, "PINNED_INPUT_FETCH_FAILED")

    def test_a_moved_tree_is_refused(self) -> None:
        m = json.loads(self.manifest.read_text())
        m["pins"]["p1"]["tree"] = "2" * 40
        self.manifest.write_text(json.dumps(psi.sealed(m)))
        self.refused(self.materialize, "PINNED_INPUT_TREE_MISMATCH")


class SelectorInputTests(Fixture):
    def check(self, **extra) -> dict:
        return {"kind": "pinned_source", "manifest": str(self.manifest), "pin": "p1", "env": "FAKESDK_PIN",
                "module": "fakesdk", **extra}

    def test_available_only_when_verified_and_imported_from_the_pinned_root(self) -> None:
        tree = self.materialize()
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {"FAKESDK_PIN": str(tree)})
        self.assertTrue(ok, detail)
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {})
        self.assertFalse(ok)
        self.assertIn("FAKESDK_PIN unset", detail)
        (tree / "fakesdk/sub.py").write_text("X = 3\n")
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {"FAKESDK_PIN": str(tree)})
        self.assertFalse(ok)
        self.assertIn("FAIL_CLOSED PINNED_INPUT_SHA256_MISMATCH", detail)

    def with_shim(self, body: str = "ORIGIN = __file__\n") -> Path:
        shim = self.tmp / "shims/fakereq/__init__.py"
        shim.parent.mkdir(parents=True, exist_ok=True)
        shim.write_text(body)
        base = json.loads(self.manifest.read_text())
        self.manifest.write_text(json.dumps(psi.author_pin(self.manifest, "p1", self.src, self.commit, ["fakesdk"],
                                                           base, ["fakereq=shims/fakereq/__init__.py"])))
        return shim

    def test_a_shim_is_sha256_pinned_loaded_after_the_tree_and_only_for_a_set_that_declares_it(self) -> None:
        self.with_shim()
        tree = self.materialize()
        env = {"FAKESDK_PIN": str(tree)}
        exported = psi.exports(self.manifest, "p1", tree)["PYTHONPATH"].split(os.pathsep)
        self.assertEqual([str(tree), str(tree.parent / "shim")], exported)   # the tree first, the shim after it
        ok, detail = sel.input_available(self.tmp, {"check": self.check(shims=["fakereq"])}, sys.executable, env)
        self.assertTrue(ok, detail)
        self.assertIn("shims ['fakereq'] sha256-matched and loaded", detail)
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, env)
        self.assertFalse(ok)
        self.assertIn("FAIL_CLOSED PINNED_INPUT_SHIM_NOT_DECLARED_BY_THE_SET", detail)

    def test_a_shim_that_differs_is_refused_at_materialize_and_at_verify(self) -> None:
        shim = self.with_shim()
        tree = self.materialize()
        (tree.parent / "shim/fakereq/__init__.py").write_text("ORIGIN = 'tampered'\n")
        self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_SHIM_SHA256_MISMATCH")
        ok, detail = sel.input_available(self.tmp, {"check": self.check(shims=["fakereq"])}, sys.executable,
                                         {"FAKESDK_PIN": str(tree)})
        self.assertFalse(ok)
        self.assertIn("FAIL_CLOSED PINNED_INPUT_SHIM_SHA256_MISMATCH", detail)
        shim.write_text("ORIGIN = 'edited after pinning'\n")
        self.refused(lambda: psi.materialize(self.manifest, "p1", self.tmp / "again", str(self.src)),
                     "PINNED_INPUT_SHIM_SHA256_MISMATCH")

    def test_an_undeclared_shim_beside_a_pin_without_shims_is_refused(self) -> None:
        tree = self.materialize()
        (tree.parent / "shim/requests").mkdir(parents=True)
        (tree.parent / "shim/requests/__init__.py").write_text("")
        self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_SHIM_SHA256_MISMATCH")


class RequestsStandInTests(unittest.TestCase):
    """The committed urllib stand-in for pin 0028cab9 (loaded by path, under a private name: never as `requests`)."""

    PATH = ROOT / ".stegverse/verification-inputs/shims/stegverse-sdk-0028cab9/requests/__init__.py"

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("p1_163_requests_stand_in", cls.PATH)
        cls.shim = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.shim)
        import http.server
        import threading

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                status, out = {"/ok": (200, json.dumps({"echo": json.loads(body), "auth": self.headers.get("X-T")})),
                               "/bad": (502, "upstream"), "/notjson": (200, "<html>")}[self.path]
                self.send_response(status)
                self.end_headers()
                self.wfile.write(out.encode())

            def log_message(self, *a):  # noqa: D401
                pass

        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_post_sends_json_and_headers_and_returns_the_parsed_body(self) -> None:
        r = self.shim.post(self.base + "/ok", json={"a": 1}, headers={"X-T": "t"}, timeout=5)
        r.raise_for_status()
        self.assertEqual((200, True, {"echo": {"a": 1}, "auth": "t"}), (r.status_code, r.ok, r.json()))

    def test_a_4xx_or_5xx_raises_from_raise_for_status_as_a_request_exception(self) -> None:
        r = self.shim.post(self.base + "/bad", json={}, timeout=5)
        self.assertEqual((502, "upstream"), (r.status_code, r.text))
        with self.assertRaises(self.shim.RequestException) as ctx:
            r.raise_for_status()
        self.assertIsInstance(ctx.exception, self.shim.HTTPError)

    def test_invalid_json_is_a_value_error_and_an_unreachable_host_a_request_exception(self) -> None:
        with self.assertRaises(ValueError):
            self.shim.post(self.base + "/notjson", json={}, timeout=5).json()
        import socket
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        with self.assertRaises(self.shim.RequestException):
            self.shim.post(f"http://127.0.0.1:{port}/", json={}, timeout=5)

    def test_anything_outside_the_covered_calls_is_an_attribute_error(self) -> None:
        for name in ("get", "Session", "put", "adapters"):
            with self.assertRaises(AttributeError) as ctx:
                getattr(self.shim, name)
            self.assertIn("outside the scope", str(ctx.exception))


class RunGroupTests(unittest.TestCase):
    def test_each_group_runs_in_its_own_process_with_only_its_exports(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tests").mkdir()
            (root / "tests/__init__.py").write_text("")
            (root / "tests/test_g.py").write_text(
                "import os, unittest\n"
                "class A(unittest.TestCase):\n"
                "    def test_unpinned(self):\n"
                "        self.assertNotIn('P1_PIN', os.environ)\n"
                "class B(unittest.TestCase):\n"
                "    def test_pinned(self):\n"
                "        self.assertEqual('x', os.environ['P1_PIN'])\n")
            selection = {"runner": "unittest", "run": {"tests": [], "deselect": []}, "run_groups": [
                {"id": "no-pinned-input", "inputs": [], "env": {}, "tests": ["tests.test_g.A"], "deselect": []},
                {"id": "sdk", "inputs": ["sdk"], "env": {"P1_PIN": "x"}, "tests": ["tests.test_g.B"],
                 "deselect": []}]}
            out = root / "out.txt"
            cwd = os.getcwd()
            os.chdir(root)
            try:
                status = sel.run_groups(selection, out, None)
            finally:
                os.chdir(cwd)
            text = out.read_text()
            self.assertEqual(0, status, text)
            self.assertEqual(2, text.count(sel.GROUP_MARKER))
            results, counts, ran = drift.unittest_results(text)
            self.assertEqual(2, ran)            # Ran is added up over the groups, not the last one only
            self.assertEqual({"ok"}, set(results.values()))

    def test_pytest_counts_are_added_up_per_group(self) -> None:
        text = (f"{drift.GROUP_MARKER}a inputs=- tests=1\n1 passed, 1 skipped in 0.1s\n"
                f"{drift.GROUP_MARKER}b inputs=sdk tests=1\n2 passed in 0.1s\n")
        _rows, counts, _nodes = drift.pytest_verification(ROOT, text, None, "r", "g")
        self.assertEqual({"passed": 3, "skipped": 1}, counts)

    def test_a_test_is_judged_in_the_group_that_ran_it_pinned_first(self) -> None:
        drift.RUN_GROUPS[:] = [
            {"id": "no-pinned-input", "inputs": [], "env": {}, "tests": ["tests/test_x.py"]},
            {"id": "sdk", "inputs": ["sdk"], "env": {"PYTHONPATH": "/pinned"}, "tests": ["tests/test_x.py::Real"]}]
        try:
            self.assertEqual("sdk", drift.group_of("tests/test_x.py::Real::test_a")["id"])
            self.assertEqual("no-pinned-input", drift.group_of("tests/test_x.py::Other::test_b")["id"])
            self.assertEqual("/pinned", drift.group_env("tests/test_x.py::Real::test_a")["PYTHONPATH"])
        finally:
            drift.RUN_GROUPS[:] = []


class ThisRepositoryTests(unittest.TestCase):
    def test_every_sdk_input_of_the_spec_is_a_pinned_source_of_the_committed_manifest(self) -> None:
        spec = json.loads((ROOT / ".stegverse/test-set-spec.json").read_text())
        pins = [d["check"] for n, d in spec["inputs"].items() if n.startswith("stegverse-sdk")]
        self.assertTrue(pins)
        for check in pins:
            self.assertEqual("pinned_source", check["kind"])
            manifest, pin = psi.load_manifest(ROOT / check["manifest"], check["pin"], "test")
            self.assertEqual("https://github.com/StegVerse-org/StegVerse-SDK", manifest["repository"])
            self.assertEqual(40, len(pin["commit"]))
            self.assertTrue(pin["commit"].startswith(check["pin"]))
            for mod in pin["modules"].values():
                self.assertEqual(psi.module_digest(mod["file_sha256"]), mod["sha256"])
            self.assertNotIn("runtime_requires_importable", pin)   # nothing is required of the job's interpreter
            self.assertEqual(sorted(check.get("shims", [])), sorted(pin.get("shims", {})))
            for shim in pin.get("shims", {}).values():
                blob = (ROOT / check["manifest"]).parent.joinpath(shim["path"]).read_bytes()
                self.assertEqual(shim["sha256"], hashlib.sha256(blob).hexdigest())


if __name__ == "__main__":
    unittest.main()
