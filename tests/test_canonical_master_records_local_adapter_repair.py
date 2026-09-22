from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workers" / "canonical_state_transition_custody.py"


def load_module():
    spec = importlib.util.spec_from_file_location("canonical_state_transition_custody_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("module_spec_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def receipt(module):
    return module.build_state_receipt(
        transition_id="TEST_LOCAL_CANONICAL_CUSTODY",
        transition_sequence=1,
        subject_or_correlation_id="TEST_ONLY_NOT_RUNTIME",
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=None,
        resulting_state_ref_or_hash="sha256:" + "1" * 64,
        governance_decision_ref_where_applicable=None,
        transition_evidence={"test_only": True},
        recorded_at="2026-09-18T00:00:00Z",
    )


def fake_master_records_root(tmp_path: Path) -> Path:
    root = tmp_path / "master-records" / "orchestration"
    services = root / "services"
    services.mkdir(parents=True)
    (services / "__init__.py").write_text("", encoding="utf-8")
    (services / "master_records_custody_api.py").write_text(
        "AUTHORITY_EFFECT='NONE_CUSTODY_RECONSTRUCTION_ONLY'\n",
        encoding="utf-8",
    )
    (services / "canonical_state_transition_custody.py").write_text(
        "import hashlib,json,os\n"
        "from pathlib import Path\n"
        "def record_receipt(base, receipt):\n"
        "    canonical=json.dumps(receipt,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')\n"
        "    digest=hashlib.sha256(canonical).hexdigest()\n"
        "    Path(os.environ['MASTER_RECORDS_DB']).write_bytes(canonical)\n"
        "    return {'schema':'stegverse.master-records.state-transition-custody-receipt/v1','state':'RECORDED',"
        "'receipt_sha256':digest,'reconstructed_receipt_sha256':digest,'reconstruction_status':'PASS',"
        "'master_record_ref':'master-record:state-transition:sha256:'+digest,"
        "'master_records_grants_transition_authority':False,'master_records_grants_execution_authority':False,"
        "'authority_effect':'NONE_CUSTODY_RECONSTRUCTION_ONLY'}\n",
        encoding="utf-8",
    )
    return root


class CanonicalMasterRecordsLocalAdapterRepairTests(unittest.TestCase):
    def test_calls_existing_state_transition_authority_without_schema_relabel(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp_path = Path(td)
            mr_root = fake_master_records_root(tmp_path)
            db = tmp_path / "durable" / "master-records.db"
            db.parent.mkdir()
            env = {
                "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(mr_root),
                "MASTER_RECORDS_DB": str(db),
                "MASTER_RECORDS_RECEIPT_KEY": "test-only-key",
                "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
            }
            state_receipt = receipt(module)
            with mock.patch.dict(os.environ, env, clear=False):
                result = module._submit_local(state_receipt)

            self.assertEqual(result["state"], "RECORDED")
            self.assertEqual(result["reconstruction_status"], "PASS")
            self.assertIs(result["master_records_grants_transition_authority"], False)
            retained = json.loads(db.read_text(encoding="utf-8"))
            self.assertEqual(retained, state_receipt)
            expected = hashlib.sha256(module.canonical_json(state_receipt).encode("utf-8")).hexdigest()
            self.assertEqual(result["receipt_sha256"], expected)
            self.assertEqual(result["reconstructed_receipt_sha256"], expected)

    def test_fails_closed_without_explicit_durable_authority_configuration(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            mr_root = fake_master_records_root(tmp_path)
            env = {
                "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(mr_root),
                "MASTER_RECORDS_DB": str(tmp_path / "master-records.db"),
                "MASTER_RECORDS_RECEIPT_KEY": "test-only-key",
            }
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertIsNone(module._submit_local(receipt(module)))

    def test_no_longer_uses_reusable_task_lifecycle_ingester(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("scripts/ingest_reusable_task_lifecycle.py", source)
        self.assertNotIn("scripts/reconstruct_reusable_task_lifecycle.py", source)
        self.assertIn("from services.canonical_state_transition_custody import record_receipt", source)
        self.assertIn("MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS", source)


if __name__ == "__main__":
    unittest.main()
