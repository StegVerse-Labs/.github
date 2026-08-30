from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "cross_framework_current_basis_v04_worker",
    ROOT/"workers/cross_framework_current_basis_v04_worker.py",
)
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class CurrentBasisV04WorkerTests(unittest.TestCase):
    def test_frozen_identity_and_runtime_refs_are_exact(self):
        self.assertEqual(mod.FROZEN_SHA256,"07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f")
        self.assertEqual(mod.FROZEN_BLOB,"59d818a15fc7be732c97dae7d2174d8cfe9a7bab")
        self.assertEqual(mod.TASK_ID,"SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001")
        self.assertEqual(mod.RESULT_ROOT_REL.as_posix(),"receipts/cross-framework-current-basis-v04/result")

    def test_source_preflight_requires_clean_ancestor_and_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"repo"; root.mkdir()
            subprocess.run(["git","init","-q",str(root)],check=True)
            subprocess.run(["git","-C",str(root),"config","user.email","test@example.invalid"],check=True)
            subprocess.run(["git","-C",str(root),"config","user.name","Test"],check=True)
            (root/"required.txt").write_text("ok\n",encoding="utf-8")
            subprocess.run(["git","-C",str(root),"add","required.txt"],check=True)
            subprocess.run(["git","-C",str(root),"commit","-qm","initial"],check=True)
            head=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
            row=mod._source_ok(root,head,("required.txt",))
            self.assertTrue(row["selected"])
            (root/"required.txt").write_text("changed\n",encoding="utf-8")
            row=mod._source_ok(root,head,("required.txt",))
            self.assertFalse(row["selected"])
            self.assertFalse(row["clean_worktree"])

    def test_worker_source_contains_no_network_source_commands(self):
        source=(ROOT/"workers/cross_framework_current_basis_v04_worker.py").read_text(encoding="utf-8")
        for forbidden in ("git clone","git fetch","git pull","curl ","wget "):
            self.assertNotIn(forbidden,source)
        self.assertIn("--run-dir",source)
        self.assertIn("--custody-db",source)
        self.assertIn("RUN_COMPLETE.json",source)
        self.assertIn("external_side_effect",source)


if __name__=="__main__":
    unittest.main()
