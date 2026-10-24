"""Hermetic tests for scripts/icv_distribution_offline_install.py and the ICV
distribution pins (StegVerse-Labs/.github#3183 workstream B).

No network: acquisition is exercised with an in-memory opener. The real pinned
bytes are exercised by the consolidated-source-validators step instead.
"""
from __future__ import annotations

import io
import json
import os
import socket
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import icv_distribution_offline_install as icv  # noqa: E402

PINS = ROOT / "distribution" / "icv" / "package-pins.v1.json"
MATRIX = ROOT / "distribution" / "icv" / "compatibility-matrix.v1.json"
CENSUS_REPOS = {
    "Infrastructure-Continuity-Ventures/.github",
    "Infrastructure-Continuity-Ventures/infrastructure-continuity-core-lite",
    "Infrastructure-Continuity-Ventures/infrastructure-continuity-demo",
    "Infrastructure-Continuity-Ventures/infrastructure-continuity-docs",
    "Infrastructure-Continuity-Ventures/infrastructure-continuity-engine",
    "Infrastructure-Continuity-Ventures/infrastructure-continuity-jurisdictions",
    "Infrastructure-Continuity-Ventures/infrastructure-continuity-workflows",
}


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def make_pin(src: Path, version: str, files: dict[str, str], **extra) -> dict:
    write_tree(src, files)
    write_tree(src, {"LICENSE": "MIT License\n"})
    pin = {
        "package": "demo-pkg", "import_name": "demopkg", "version": version,
        "source_repository": "Example/demo", "commit": "0" * 40,
        "requires_python": ">=3.8", "runtime_dependencies": [],
        "license_declared": {"spdx": "MIT"},
        "rights_clearance": "CLEARED_AS_DECLARED_MIT_NOT_A_LEGAL_DETERMINATION",
        "lifecycle_test": True,
        "manifest_blobs": {"LICENSE": icv.git_blob_sha(b"MIT License\n")},
        "install_files": {rel: icv.git_blob_sha(text.encode()) for rel, text in files.items()},
        "package_roots": [{"path": "demopkg", "tree": icv.git_tree_sha(src / "demopkg")}],
    }
    pin.update(extra)
    return pin


class Hashing(unittest.TestCase):
    def test_blob_sha_matches_git(self):
        self.assertEqual(icv.git_blob_sha(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")
        self.assertEqual(icv.git_blob_sha(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_tree_sha_matches_git_write_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_tree(root, {"pkg/__init__.py": "a = 1\n", "pkg/sub/mod.py": "b = 2\n", "run.sh": "#!/bin/sh\n"})
            os.chmod(root / "run.sh", 0o755)
            # `git write-tree` of this layout
            self.assertEqual(icv.git_tree_sha(root), "aee345e9a8c8808a465d42665dbe167c7cbf77e8")


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.src1, self.src2, self.site = base / "v1", base / "v2", base / "prefix" / "site-packages"
        self.v1 = make_pin(self.src1, "1.0", {"demopkg/__init__.py": "V = '1.0'\n", "demopkg/old.py": "x = 1\n"})
        self.v2 = make_pin(self.src2, "2.0", {"demopkg/__init__.py": "V = '2.0'\n", "demopkg/new.py": "y = 2\n"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_import_uninstall_leaves_nothing(self):
        result = icv.install(self.v1, self.src1, self.site)
        self.assertEqual(result["files_placed"], 2 + 4)
        info = self.site / "demo_pkg-1.0.dist-info"
        self.assertTrue((info / "RECORD").is_file())
        self.assertEqual(json.loads((info / "PINNED_SOURCE.json").read_text())["commit"], "0" * 40)
        self.assertTrue(icv.import_smoke(self.v1, self.site)["imported_from"].endswith("demopkg/__init__.py"))
        icv.uninstall(self.site, "demo-pkg")
        self.assertEqual(list(self.site.rglob("*")), [])

    def test_second_install_is_refused(self):
        icv.install(self.v1, self.src1, self.site)
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.install(self.v1, self.src1, self.site)
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_ALREADY_INSTALLED")

    def test_tampered_source_fails_closed_and_places_nothing(self):
        (self.src1 / "demopkg" / "old.py").write_text("x = 'tampered'\n", encoding="utf-8")
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.install(self.v1, self.src1, self.site)
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_PINNED_BYTES_MISMATCH")
        self.assertEqual(set(ctx.exception.fields), set(icv.SIX))
        self.assertFalse(self.site.exists())

    def test_extra_file_in_package_root_fails_tree_check(self):
        write_tree(self.src1, {"demopkg/injected.py": "evil = 1\n"})
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.verify_source(self.v1, self.src1)
        self.assertIn("demopkg/", ctx.exception.fields["required_evidence_or_repair"])

    def test_not_cleared_package_is_never_installed(self):
        pin = dict(self.v1, rights_clearance="NOT_CLEARED", lifecycle_test=False,
                   fail_closed={k: k.upper() for k in icv.SIX})
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.install(pin, self.src1, self.site)
        self.assertEqual(ctx.exception.fields["failure_code"], "FAILURE_CODE")
        self.assertFalse(self.site.exists())

    def test_python_floor_is_enforced(self):
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.check_requires_python({"requires_python": ">=3.11"}, (3, 9, 0))
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_PYTHON_BELOW_DECLARED_FLOOR")
        icv.check_requires_python({"requires_python": ">=3.9"}, (3, 9, 0))
        with self.assertRaises(icv.FailClosed):
            icv.check_requires_python({"requires_python": "~=3.9"}, (3, 12, 0))

    def test_modified_install_blocks_uninstall_without_removing_anything(self):
        icv.install(self.v1, self.src1, self.site)
        (self.site / "demopkg" / "old.py").write_text("x = 'edited'\n", encoding="utf-8")
        before = sorted(p.relative_to(self.site) for p in self.site.rglob("*"))
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.uninstall(self.site, "demo-pkg")
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_INSTALLED_FILES_MODIFIED")
        self.assertEqual(sorted(p.relative_to(self.site) for p in self.site.rglob("*")), before)

    def test_upgrade_replaces_version_and_removes_old_only_files(self):
        icv.install(self.v1, self.src1, self.site)
        result = icv.upgrade(self.v1, self.v2, self.src2, self.site)
        self.assertEqual(result["removed_from_version_only_files"], 1)
        self.assertFalse((self.site / "demopkg" / "old.py").exists())
        self.assertTrue((self.site / "demopkg" / "new.py").exists())
        self.assertFalse((self.site / "demo_pkg-1.0.dist-info").exists())
        self.assertTrue((self.site / "demo_pkg-2.0.dist-info").is_dir())
        icv.uninstall(self.site, "demo-pkg")
        self.assertEqual(list(self.site.rglob("*")), [])

    def test_upgrade_needs_the_from_version(self):
        with self.assertRaises(icv.FailClosed) as ctx:
            icv.upgrade(self.v1, self.v2, self.src2, self.site)
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_UPGRADE_FROM_STATE_ABSENT")

    def test_network_is_disabled_during_offline_phases(self):
        with icv.network_disabled():
            with self.assertRaises(OSError):
                socket.create_connection(("127.0.0.1", 9))
            with self.assertRaises(OSError):
                socket.socket()
        socket.socket().close()


def tarball(members: dict[str, bytes], comment: str | None) -> bytes:
    buffer = io.BytesIO()
    pax = {"comment": comment} if comment else {}
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.PAX_FORMAT, pax_headers=pax) as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Acquire(unittest.TestCase):
    pin = {"source_repository": "Example/demo", "commit": "a" * 40}

    def test_acquire_extracts_single_root(self):
        data = tarball({"demo-aaa/demopkg/__init__.py": b"V = 1\n"}, "a" * 40)
        with tempfile.TemporaryDirectory() as tmp:
            src = icv.acquire(self.pin, Path(tmp), opener=lambda url, timeout: FakeResponse(data))
            self.assertEqual((src / "demopkg" / "__init__.py").read_bytes(), b"V = 1\n")

    def test_commit_mismatch_fails_closed(self):
        data = tarball({"demo-bbb/x.py": b"1\n"}, "b" * 40)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(icv.FailClosed) as ctx:
            icv.acquire(self.pin, Path(tmp), opener=lambda url, timeout: FakeResponse(data))
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_ARCHIVE_COMMIT_MISMATCH")

    def test_path_escape_fails_closed(self):
        data = tarball({"demo-aaa/../../evil.py": b"1\n"}, "a" * 40)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(icv.FailClosed) as ctx:
            icv.acquire(self.pin, Path(tmp), opener=lambda url, timeout: FakeResponse(data))
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_ARCHIVE_PATH_ESCAPE")

    def test_network_failure_fails_closed(self):
        def opener(url, timeout):
            raise OSError("offline")
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(icv.FailClosed) as ctx:
            icv.acquire(self.pin, Path(tmp), opener=opener)
        self.assertEqual(ctx.exception.fields["failure_code"], "ICV_SOURCE_ACQUISITION_FAILED")


class PinsAndMatrix(unittest.TestCase):
    def setUp(self):
        self.pins = icv.load_pins(PINS)
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_every_package_has_cited_license_evidence(self):
        for pin in self.pins["packages"]:
            self.assertTrue(pin["license_declared"]["evidence"], pin["package"])
            self.assertRegex(pin["commit"], r"^[0-9a-f]{40}$")
            for sha in pin.get("manifest_blobs", {}).values():
                self.assertRegex(sha, r"^[0-9a-f]{40}$")

    def test_only_declared_licenses_are_cleared(self):
        for pin in self.pins["packages"]:
            if icv.cleared(pin):
                self.assertNotIn("UNKNOWN", pin["license_declared"]["spdx"])
                self.assertTrue(pin["install_files"])
            else:
                self.assertEqual(pin["rights_clearance"], "NOT_CLEARED")
                self.assertEqual(pin["license_declared"]["spdx"], "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
                self.assertEqual(set(pin["fail_closed"]), set(icv.SIX))

    def test_icv_repositories_stay_fail_closed(self):
        icv_repos = self.pins["icv_repositories"]
        self.assertEqual(set(icv_repos["repositories"]), CENSUS_REPOS)
        self.assertIs(icv_repos["bytes_observed"], False)
        self.assertEqual(icv_repos["classification"], "B")
        self.assertEqual(set(icv_repos["fail_closed"]), set(icv.SIX))

    def test_upgrade_paths_reference_cleared_pins(self):
        for path in self.pins["upgrade_paths"]:
            self.assertTrue(icv.cleared(icv.find_pin(self.pins, path["package"], path["from"])))
            self.assertTrue(icv.cleared(icv.find_pin(self.pins, path["package"], path["to"])))

    def test_matrix_rows_match_pins(self):
        rows = {(r["package"], r["version"]): r for r in self.matrix["rows"]}
        self.assertEqual(set(rows), {(p["package"], p["version"]) for p in self.pins["packages"]})
        for pin in self.pins["packages"]:
            row = rows[(pin["package"], pin["version"])]
            self.assertEqual(row["license_declared"], pin["license_declared"]["spdx"])
            self.assertEqual(row["python_classifiers_declared"], pin.get("python_classifiers", []))
            self.assertEqual(row["offline_lifecycle"] == "EXERCISED", icv.cleared(pin))

    def test_expected_ok_rejects_a_passing_refusal(self):
        receipts = [{"step": "rights-gate", "package": "x", "version": "1", "disposition": "PASS"}]
        self.assertFalse(icv.expected_ok(receipts, self.pins))


if __name__ == "__main__":
    unittest.main()
