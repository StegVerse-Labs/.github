from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv001_progression",ROOT/"scripts/run_stegverse001_activation_progression.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

def bridge_receipt(consumer,result):
    return {
      "target_consumer":consumer,
      "dispatch_receipt":{
        "selection_scope":"EXACT_SELECTOR",
        "selected_consumers":[consumer],
        "consumer_count":1,
        "outcomes":[{"consumer":consumer,"result":result,"state":result.get("state"),"attempted":True}]
      }
    }

def test_nonterminal_stage1_stops_before_sv001_execution():
    calls=[]
    def bridge(source,runtime,*,target_consumer,env=None):
        calls.append(target_consumer)
        return bridge_receipt(target_consumer,{"state":"SOURCE_ROOTS_PENDING","activation_complete":False})
    with tempfile.TemporaryDirectory() as td:
        out=MOD.run(Path(td)/"source",Path(td)/"runtime",bridge=bridge)
    assert calls==[MOD.STAGE1]
    assert out["state"]=="STACK_ACTIVATION_INCOMPLETE"
    assert out["stage2_executed"] is False
    assert out["next_required_machine_transition"]=="MATERIALIZE_REQUIRED_LOCAL_SOURCE_ROOTS_AND_REEXECUTE_STAGE1"

def test_completed_stage1_executes_sv001_once_and_terminalizes():
    calls=[]
    def bridge(source,runtime,*,target_consumer,env=None):
        calls.append(target_consumer)
        if target_consumer==MOD.STAGE1:
            return bridge_receipt(target_consumer,{"state":"COMPLETED","activation_complete":True})
        return bridge_receipt(target_consumer,{
          "state":"COMPLETED",
          "terminal_execution_observed":True,
          "downstream_evidence":{"state":"PASS"}
        })
    with tempfile.TemporaryDirectory() as td:
        runtime=Path(td)/"runtime"
        out=MOD.run(Path(td)/"source",runtime,bridge=bridge)
        assert (runtime/MOD.RECEIPT_REL).is_file()
    assert calls==[MOD.STAGE1,MOD.STAGE2]
    assert out["state"]=="SV001_AUTONOMY_EXECUTION_COMPLETED"
    assert out["next_required_machine_transition"]=="CONTINUE_MASTER_RECORDS_AND_SV002_SUCCESSORS"

def test_already_consumed_stage1_may_advance_but_does_not_reactivate_stack():
    calls=[]
    def bridge(source,runtime,*,target_consumer,env=None):
        calls.append(target_consumer)
        if target_consumer==MOD.STAGE1:
            return bridge_receipt(target_consumer,{"state":"ALREADY_CONSUMED","activation_complete":True,"runtime_execution_attempted":False})
        return bridge_receipt(target_consumer,{"state":"ALREADY_CONSUMED","terminal_execution_observed":True,"autonomy_execution_retried":False})
    with tempfile.TemporaryDirectory() as td:
        out=MOD.run(Path(td)/"source",Path(td)/"runtime",bridge=bridge)
    assert calls==[MOD.STAGE1,MOD.STAGE2]
    assert out["state"]=="SV001_AUTONOMY_EXECUTION_COMPLETED"
    assert out["stage1_result"]["runtime_execution_attempted"] is False
    assert out["stage2_result"]["autonomy_execution_retried"] is False

def test_stage2_nonterminal_names_execution_repair_not_evidence_watch():
    def bridge(source,runtime,*,target_consumer,env=None):
        if target_consumer==MOD.STAGE1:
            return bridge_receipt(target_consumer,{"state":"COMPLETED","activation_complete":True})
        return bridge_receipt(target_consumer,{"state":"LEASE_PENDING","terminal_execution_observed":False})
    with tempfile.TemporaryDirectory() as td:
        out=MOD.run(Path(td)/"source",Path(td)/"runtime",bridge=bridge)
    assert out["state"]=="SV001_AUTONOMY_EXECUTION_INCOMPLETE"
    assert out["next_required_machine_transition"]=="EXECUTE_TVC_LEASE_ISSUANCE_PATH_AND_REEXECUTE_STAGE2"
    assert out["looping_or_polling_performed"] is False

def test_wrong_selector_receipt_fails_closed():
    receipt=bridge_receipt("wrong",{"state":"COMPLETED"})
    try:
        MOD.selected_result(receipt,MOD.STAGE1)
    except RuntimeError as e:
        assert "target mismatch" in str(e)
    else:
        raise AssertionError("wrong target accepted")
