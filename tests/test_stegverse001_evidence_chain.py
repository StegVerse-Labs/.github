from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("chain",ROOT/"scripts/continue_stegverse001_evidence_chain.py")
M=importlib.util.module_from_spec(S); assert S.loader; S.loader.exec_module(M)

def test_missing_sv001_receipt_is_retryable():
    with tempfile.TemporaryDirectory() as td:
        r=M.continue_chain(ROOT,Path(td)/"missing.json",Path(td)/"mr",Path(td)/"sv")
        assert r["state"]=="SV001_RECEIPT_NOT_OBSERVED"
        assert r["retry_allowed"] is True

def test_missing_master_records_source_is_retryable():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); src=base/"source.json"; src.write_text(json.dumps({"receipt_hash":"sha256:"+"1"*64}))
        with mock.patch.object(M,"locate_master_records",return_value=(None,[])):
            r=M.continue_chain(ROOT,src,base/"mr",base/"sv")
        assert r["state"]=="MASTER_RECORDS_SOURCE_NOT_MATERIALIZED"
        assert r["retry_allowed"] is True

def test_runtime_source_floor_constants_are_exact():
    assert M.REQUIRED_MASTER_RECORDS_ANCESTOR=="d593c920c1630aa5da20cc2622196f8676a74afd"
    assert M.REQUIRED_SV002_ANCESTOR=="786323f16e36346c69b2215894086515d7b1d58e"
