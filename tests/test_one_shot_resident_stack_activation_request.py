from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("consumer",ROOT/"scripts/consume_one_shot_resident_stack_activation_request.py")
M=importlib.util.module_from_spec(S); assert S.loader; S.loader.exec_module(M)

def make_roots(base:Path):
    specs={
      "llm":("llm","scripts/stegdeploy_bootstrap.py"),
      "stegos":("StegOS","stegos/intr_backbone.py"),
      "kv":("continuity-vault-kit","runtime/kv_interlock_endpoint.py"),
      "healer":("StegVerse-Healer","app/dispatch_orchestrators.py"),
      "tv":("TV","scripts/tv_run_resident_operational_proof.py"),
      "tvc":("TVC","tools/hil_intr_lifecycle_intake.py"),
      "master_records":("orchestration","scripts/watch_stegverse001_autonomy_receipt.py"),
      "micro_node":("micro-node-runtime","tools/run_self_characterization_principal.py"),
      "tt":("TT",null),
      "rtg":("RTG",null),
      "gtg":("GTG",null),
      "ae":("AE",null),
    }
    roots={}
    for name,(folder,rel) in specs.items():
        root=base/folder; root.mkdir(parents=True,exist_ok=True)
        if rel:
            path=root/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text("# source\n")
        roots[name]=root
    return roots

def env_for(roots):
    return {
      "STEGVERSE_LLM_ADAPTER_ROOT":str(roots["llm"]),
      "STEGVERSE_STEGOS_ROOT":str(roots["stegos"]),
      "STEGVERSE_KV_SOURCE_ROOT":str(roots["kv"]),
      "STEGVERSE_HEALER_ROOT":str(roots["healer"]),
      "STEGVERSE_TV_ROOT":str(roots["tv"]),
      "STEGVERSE_TVC_ROOT":str(roots["tvc"]),
      "STEGVERSE_MASTER_RECORDS_ROOT":str(roots["master_records"]),
      "STEGVERSE_MICRO_NODE_RUNTIME_ROOT":str(roots["micro_node"]),
      "STEGVERSE_TT_ROOT":str(roots["tt"]),
      "STEGVERSE_RTG_ROOT":str(roots["rtg"]),
      "STEGVERSE_GTG_ROOT":str(roots["gtg"]),
      "STEGVERSE_AE_ROOT":str(roots["ae"]),
      "PATH":"/usr/bin",
    }

def write_request(runtime:Path):
    p=runtime/M.REQUEST_REL; p.parent.mkdir(parents=True,exist_ok=True)
    req={"schema":"stegverse.resident-execution-request/v1","request_id":"R1","state":"REQUESTED","task_id":M.TASK_ID}
    p.write_text(json.dumps(req)); return req

def test_missing_source_root_is_retryable_without_execution():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots); env.pop("STEGVERSE_MASTER_RECORDS_ROOT")
        out=M.consume(source,runtime,env=env)
        assert out["state"]=="SOURCE_ROOTS_PENDING"
        assert out["runtime_execution_attempted"] is False
        assert out["missing_source_roots"]==["master_records"]

def test_repo_root_map_can_resolve_master_records():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); roots=make_roots(base); env=env_for(roots); env.pop("STEGVERSE_MASTER_RECORDS_ROOT")
        env["STEGVERSE_REPO_ROOTS_JSON"]=json.dumps({"master-records/orchestration":str(roots["master_records"])})
        resolved,missing=M.resolve_roots(env)
        assert missing==[]
        assert resolved["master_records"]==roots["master_records"].resolve()

def test_complete_activation_is_exactly_once():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir()
        req=write_request(runtime); roots=make_roots(base); env=env_for(roots)
        script=runtime/"scripts/activate_resident_stack.py"; script.parent.mkdir(parents=True,exist_ok=True); script.write_text("# activate\n")
        calls=[]
        def runner(command,**kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"COMPLETE"})+"\n",stderr="")
        first=M.consume(source,runtime,runner,env)
        second=M.consume(source,runtime,runner,env)
        assert first["state"]=="COMPLETED"
        assert first["activation_complete"] is True
        assert second["state"]=="ALREADY_CONSUMED"
        assert second["runtime_execution_attempted"] is False
        assert len(calls)==1
        assert "--master-records-root" in calls[0]
        assert "--micro-node-root" in calls[0]
        assert "--tt-root" in calls[0]
        assert "--rtg-root" in calls[0]
        assert "--gtg-root" in calls[0]
        assert "--ae-root" in calls[0]

def test_incomplete_activation_remains_retryable():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots)
        script=runtime/"scripts/activate_resident_stack.py"; script.parent.mkdir(parents=True,exist_ok=True); script.write_text("# activate\n")
        def runner(command,**kwargs):
            return SimpleNamespace(returncode=1,stdout=json.dumps({"state":"INCOMPLETE"})+"\n",stderr="")
        out=M.consume(source,runtime,runner,env)
        assert out["state"]=="ATTEMPT_RECORDED"
        assert out["retry_allowed"] is True
        assert out["activation_complete"] is False


def test_missing_formal_root_is_retryable_without_execution():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots); env.pop("STEGVERSE_GTG_ROOT")
        out=M.consume(source,runtime,env=env)
        assert out["state"]=="SOURCE_ROOTS_PENDING"
        assert out["runtime_execution_attempted"] is False
        assert out["missing_source_roots"]==["gtg"]
