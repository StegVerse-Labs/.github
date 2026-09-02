from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv001_consumer_order",ROOT/"scripts/consume_stegverse001_bounded_autonomy_request.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

def write_sv001_request(runtime:Path):
    p=runtime/MOD.REQUEST_REL; p.parent.mkdir(parents=True,exist_ok=True)
    req={"schema":"stegverse.resident-execution-request/v1","request_id":"SV001-R1","state":"REQUESTED","task_id":MOD.TASK_ID}
    p.write_text(json.dumps(req)); return req

def write_one_shot_request(runtime:Path):
    p=runtime/MOD.ONE_SHOT_REQUEST_REL; p.parent.mkdir(parents=True,exist_ok=True)
    req={"schema":"stegverse.resident-execution-request/v1","request_id":"STACK-R1","state":"REQUESTED","task_id":MOD.ONE_SHOT_TASK_ID}
    p.write_text(json.dumps(req)); return req

def test_current_stack_sv001_is_blocked_until_one_shot_activation_complete():
    with tempfile.TemporaryDirectory() as td:
        runtime=Path(td)/"runtime"; source=Path(td)/"source"; runtime.mkdir(); source.mkdir()
        write_sv001_request(runtime); write_one_shot_request(runtime)
        calls=[]
        def runner(*args,**kwargs):
            calls.append(args); raise AssertionError("SV001 executor must not run before stack activation")
        out=MOD.consume(source,runtime,runner)
        assert out["state"]=="STACK_ACTIVATION_PENDING"
        assert out["runtime_execution_attempted"] is False
        assert out["next_required_machine_transition"]=="EXECUTE_ONE_SHOT_RESIDENT_STACK_ACTIVATION"
        assert calls==[]

def test_matching_one_shot_completion_allows_sv001_execution():
    with tempfile.TemporaryDirectory() as td:
        runtime=Path(td)/"runtime"; source=Path(td)/"source"; runtime.mkdir(); source.mkdir()
        write_sv001_request(runtime); stack=write_one_shot_request(runtime)
        receipt=runtime/MOD.ONE_SHOT_RECEIPT_REL; receipt.parent.mkdir(parents=True,exist_ok=True)
        receipt.write_text(json.dumps({
          "schema":"stegverse.resident-execution-request-consumption/v1",
          "state":"COMPLETED",
          "request_sha256":MOD.stable(stack),
          "activation_complete":True
        }))
        refresh=runtime/"scripts/refresh_and_execute_resident_task.py"; refresh.parent.mkdir(parents=True,exist_ok=True); refresh.write_text("# refresh\n")
        def runner(command,**kwargs):
            return SimpleNamespace(returncode=0,stdout=json.dumps({
              "state":"COMPLETED","transition_id":"SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED"
            })+"\n",stderr="")
        out=MOD.consume(source,runtime,runner)
        assert out["state"]=="COMPLETED"
        assert out["terminal_execution_observed"] is True

def test_terminal_sv001_receipt_still_wins_over_later_stack_gate():
    with tempfile.TemporaryDirectory() as td:
        runtime=Path(td)/"runtime"; source=Path(td)/"source"; runtime.mkdir(); source.mkdir()
        req=write_sv001_request(runtime); write_one_shot_request(runtime)
        rp=runtime/MOD.RECEIPT_REL; rp.parent.mkdir(parents=True,exist_ok=True)
        rp.write_text(json.dumps({"request_sha256":MOD.stable(req),"terminal_execution_observed":True}))
        cont=runtime/"scripts/continue_stegverse001_evidence_chain.py"; cont.parent.mkdir(parents=True,exist_ok=True); cont.write_text("# continuation\n")
        def runner(command,**kwargs):
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"PASS","retry_allowed":False})+"\n",stderr="")
        out=MOD.consume(source,runtime,runner)
        assert out["state"]=="ALREADY_CONSUMED"
        assert out["autonomy_execution_retried"] is False
