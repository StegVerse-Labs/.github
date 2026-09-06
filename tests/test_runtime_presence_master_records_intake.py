from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "repair_resident_worker_presence.py"
spec = importlib.util.spec_from_file_location("repair_presence", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write_presence(runtime: Path) -> None:
    path = runtime / mod.PRESENCE_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema": "stegverse.hb-runtime-presence-resident-observability/v1",
        "runtime_root": str(runtime),
        "resident": {"node_id": "resident-1", "present_worker_runtime_observed": True, "worker_cycle_fresh": True},
        "heartbeat_reference": {"heartbeat_grants_authority": False},
        "authority": {
            "credential_authority": "TV/TVC",
            "hb_authority_effect": "NONE_REFERENCE_ONLY",
            "projection_authority_effect": "NONE_OBSERVATION_ONLY",
            "github_token_runtime_authority": "NONE",
        },
    }) + "\n", encoding="utf-8")


class RuntimePresenceMasterRecordsIntakeTests(unittest.TestCase):
    def test_missing_master_records_root_is_non_authorizing_skip(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {}, clear=True):
            runtime = Path(td)
            write_presence(runtime)
            result = mod._persist_presence_master_records_intake(runtime)
            self.assertEqual(result["state"], "MASTER_RECORDS_ROOT_NOT_DECLARED")
            self.assertFalse(result["cross_task_reuse_authorized"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertEqual(result["github_token_runtime_authority"], "NONE")

    def test_missing_importer_is_observable_not_runtime_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            mr = root / "mr"
            runtime.mkdir(); mr.mkdir()
            write_presence(runtime)
            with mock.patch.dict(os.environ, {"STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(mr)}, clear=True):
                result = mod._persist_presence_master_records_intake(runtime)
            self.assertEqual(result["state"], "MASTER_RECORDS_IMPORTER_NOT_MATERIALIZED")
            self.assertTrue((runtime / mod.PRESENCE_RECEIPT).is_file())

    def test_exact_presence_is_submitted_without_secret_env(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            mr = root / "mr"
            importer = mr / mod.MR_IMPORTER
            runtime.mkdir(); importer.parent.mkdir(parents=True)
            write_presence(runtime)
            importer.write_text(
                "import argparse,json,os\n"
                "p=argparse.ArgumentParser();p.add_argument('--repo-root');p.add_argument('--source');a=p.parse_args()\n"
                "assert 'GITHUB_TOKEN' not in os.environ\n"
                "src=json.load(open(a.source))\n"
                "print(json.dumps({'state':'COMPLETED','custody_id':'RUNTIME-PRESENCE-abc','custody_ref':'custody/runtime-presence/x.json','runtime_root':src['runtime_root'],'resident_node_id':src['resident']['node_id'],'present_worker_runtime_observed':src['resident']['present_worker_runtime_observed'],'cross_task_reuse_authorized':False,'credential_authority':'TV/TVC','github_token_runtime_authority':'NONE','authority_effect':'NONE_INTAKE_RECEIPT_ONLY'}))\n",
                encoding="utf-8",
            )
            env = {"STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(mr), "GITHUB_TOKEN": "must-not-propagate", "PATH": os.environ.get("PATH", "")}
            with mock.patch.dict(os.environ, env, clear=True):
                result = mod._persist_presence_master_records_intake(runtime)
            self.assertEqual(result["state"], "COMPLETED")
            self.assertEqual(result["resident_node_id"], "resident-1")
            self.assertFalse(result["cross_task_reuse_authorized"])
            self.assertTrue((runtime / mod.PRESENCE_MR_INTAKE_RECEIPT).is_file())

    def test_invalid_importer_authority_fails_closed_without_deleting_presence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            mr = root / "mr"
            importer = mr / mod.MR_IMPORTER
            runtime.mkdir(); importer.parent.mkdir(parents=True)
            write_presence(runtime)
            importer.write_text(
                "import json\nprint(json.dumps({'state':'COMPLETED','cross_task_reuse_authorized':True,'credential_authority':'TV/TVC','github_token_runtime_authority':'NONE','authority_effect':'NONE_INTAKE_RECEIPT_ONLY'}))\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(mr), "PATH": os.environ.get("PATH", "")}, clear=True):
                result = mod._persist_presence_master_records_intake(runtime)
            self.assertEqual(result["state"], "FAIL_CLOSED_INVALID_MASTER_RECORDS_INTAKE")
            self.assertTrue((runtime / mod.PRESENCE_RECEIPT).is_file())
            self.assertFalse(result["cross_task_reuse_authorized"])


if __name__ == "__main__":
    unittest.main()
