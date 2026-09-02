from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("consumer",ROOT/"scripts/consume_stegverse001_bounded_autonomy_request.py")
M=importlib.util.module_from_spec(S); assert S.loader; S.loader.exec_module(M)

def write_request(runtime:Path):
    p=runtime/M.REQUEST_REL; p.parent.mkdir(parents=True,exist_ok=True)
    req={
      "schema":"stegverse.resident-execution-request/v1",
      "request_id":"R1","task_id":M.TASK_ID,"state":"REQUESTED"
    }
    p.write_text(json.dumps(req))
    return req

def test_already_consumed_retries_downstream_without_reexecuting_autonomy():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir()
        req=write_request(runtime)
        rp=runtime/M.RECEIPT_REL; rp.parent.mkdir(parents=True,exist_ok=True)
        rp.write_text(json.dumps({"request_sha256":M.stable(req),"terminal_execution_observed":True}))
        cont=runtime/"scripts/continue_stegverse001_evidence_chain.py"; cont.parent.mkdir(parents=True); cont.write_text("# continuation")
        calls=[]
        def runner(command,**kwargs):
            calls.append([Path(x).name if isinstance(x,str) else str(x) for x in command])
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"PASS","retry_allowed":False})+"\n",stderr="")
        out=M.consume(source,runtime,runner)
        assert out["state"]=="ALREADY_CONSUMED"
        assert out["autonomy_execution_retried"] is False
        assert out["downstream_evidence"]["state"]=="PASS"
        assert len(calls)==1
        assert "continue_stegverse001_evidence_chain.py" in calls[0]
        assert "refresh_and_execute_resident_task.py" not in calls[0]

def test_new_terminal_execution_triggers_downstream_once():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir()
        write_request(runtime)
        refresh=runtime/"scripts/refresh_and_execute_resident_task.py"; refresh.parent.mkdir(parents=True); refresh.write_text("# refresh")
        cont=runtime/"scripts/continue_stegverse001_evidence_chain.py"; cont.write_text("# continuation")
        calls=[]
        def runner(command,**kwargs):
            name=Path(command[1]).name; calls.append(name)
            if name=="refresh_and_execute_resident_task.py":
                body={"state":"COMPLETED","transition_id":"SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED"}
                return SimpleNamespace(returncode=0,stdout=json.dumps(body)+"\n",stderr="")
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"PASS","retry_allowed":False})+"\n",stderr="")
        out=M.consume(source,runtime,runner)
        assert out["state"]=="COMPLETED"
        assert out["terminal_execution_observed"] is True
        assert out["downstream_evidence"]["state"]=="PASS"
        assert calls==["refresh_and_execute_resident_task.py","continue_stegverse001_evidence_chain.py"]
