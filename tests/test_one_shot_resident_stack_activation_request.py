from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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
      "tt":("TT",None),
      "rtg":("RTG",None),
      "gtg":("GTG",None),
      "ae":("AE",None),
      "stegindex":("StegIndex","scripts/preflight.py"),
    }
    roots={}
    for name,(folder,rel) in specs.items():
        root=base/folder
        if rel is None:
            (root/".git").mkdir(parents=True,exist_ok=True)
        else:
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
      "STEGVERSE_STEGINDEX_SOURCE_ROOT":str(roots["stegindex"]),
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
        for flag in ("--master-records-root","--micro-node-root","--tt-root","--rtg-root","--gtg-root","--ae-root","--stegindex-root"):
            assert flag in calls[0]

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


def test_missing_pinned_sv002_source_root_is_retryable_without_execution():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots); env.pop("STEGVERSE_AE_ROOT")
        out=M.consume(source,runtime,env=env)
        assert out["state"]=="SOURCE_ROOTS_PENDING"
        assert out["runtime_execution_attempted"] is False
        assert out["missing_source_roots"]==["ae"]

def test_repo_root_map_can_resolve_all_pinned_sv002_roots():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); roots=make_roots(base); env=env_for(roots)
        for key in ("STEGVERSE_MICRO_NODE_RUNTIME_ROOT","STEGVERSE_TT_ROOT","STEGVERSE_RTG_ROOT","STEGVERSE_GTG_ROOT","STEGVERSE_AE_ROOT"):
            env.pop(key)
        env["STEGVERSE_REPO_ROOTS_JSON"]=json.dumps({
          "StegVerse-002/micro-node-runtime":str(roots["micro_node"]),
          "Admissible-Existence/TT":str(roots["tt"]),
          "Admissible-Existence/RTG":str(roots["rtg"]),
          "Admissible-Existence/GTG":str(roots["gtg"]),
          "Admissible-Existence/AE":str(roots["ae"]),
        })
        resolved,missing=M.resolve_roots(env)
        assert missing==[]
        assert resolved["micro_node"]==roots["micro_node"].resolve()
        assert resolved["tt"]==roots["tt"].resolve()
        assert resolved["rtg"]==roots["rtg"].resolve()
        assert resolved["gtg"]==roots["gtg"].resolve()
        assert resolved["ae"]==roots["ae"].resolve()


def test_nested_reentry_is_fenced_while_outer_activation_runs():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots)
        script=runtime/"scripts/activate_resident_stack.py"; script.parent.mkdir(parents=True,exist_ok=True); script.write_text("# activate\n")
        nested=[]
        def no_nested_activation(command,**kwargs):
            raise AssertionError("nested activation must not execute")
        def outer_runner(command,**kwargs):
            nested.append(M.consume(source,runtime,no_nested_activation,env))
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"COMPLETE"})+"\n",stderr="")
        out=M.consume(source,runtime,outer_runner,env)
        assert out["state"]=="COMPLETED"
        assert nested[0]["state"]=="ACTIVATION_IN_PROGRESS"
        assert nested[0]["runtime_execution_attempted"] is False
        assert not (runtime/M.FENCE_REL).exists()

def test_dead_owner_fence_is_reclaimed_and_activation_runs():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); req=write_request(runtime)
        roots=make_roots(base); env=env_for(roots)
        script=runtime/"scripts/activate_resident_stack.py"; script.parent.mkdir(parents=True,exist_ok=True); script.write_text("# activate\n")
        fence=runtime/M.FENCE_REL; fence.parent.mkdir(parents=True,exist_ok=True)
        fence.write_text(json.dumps({
          "schema":"stegverse.one-shot-resident-stack-activation-fence/v1",
          "request_sha256":M.stable(req),"owner_pid":99999999,"state":"IN_PROGRESS"
        }))
        calls=[]
        def runner(command,**kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"COMPLETE"})+"\n",stderr="")
        with mock.patch.object(M,"process_alive",return_value=False):
            out=M.consume(source,runtime,runner,env)
        assert out["state"]=="COMPLETED"
        assert len(calls)==1
        assert not fence.exists()

def test_activation_failure_releases_reentry_fence_for_retry():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots)
        script=runtime/"scripts/activate_resident_stack.py"; script.parent.mkdir(parents=True,exist_ok=True); script.write_text("# activate\n")
        def runner(command,**kwargs):
            return SimpleNamespace(returncode=1,stdout=json.dumps({"state":"INCOMPLETE"})+"\n",stderr="")
        out=M.consume(source,runtime,runner,env)
        assert out["state"]=="ATTEMPT_RECORDED"
        assert out["retry_allowed"] is True
        assert not (runtime/M.FENCE_REL).exists()


def test_completed_activation_immediately_invokes_sv001_progression_when_materialized():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots)
        activate=runtime/"scripts/activate_resident_stack.py"; activate.parent.mkdir(parents=True,exist_ok=True); activate.write_text("# activate\n")
        progression=runtime/M.PROGRESSION_REL; progression.write_text("# progression\n")
        calls=[]
        def runner(command,**kwargs):
            name=Path(command[1]).name; calls.append(name)
            if name=="activate_resident_stack.py":
                return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"COMPLETE"})+"\n",stderr="")
            return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"SV001_AUTONOMY_EXECUTION_COMPLETED"})+"\n",stderr="")
        out=M.consume(source,runtime,runner,env)
        assert calls==["activate_resident_stack.py","run_stegverse001_activation_progression.py"]
        assert out["state"]=="COMPLETED"
        assert out["activation_complete"] is True
        assert out["immediate_sv001_progression"]["attempted"] is True
        assert out["immediate_sv001_progression"]["result"]["state"]=="SV001_AUTONOMY_EXECUTION_COMPLETED"

def test_missing_stegindex_source_root_is_retryable_without_execution():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots); env.pop("STEGVERSE_STEGINDEX_SOURCE_ROOT")
        out=M.consume(source,runtime,env=env)
        assert out["state"]=="SOURCE_ROOTS_PENDING"
        assert out["runtime_execution_attempted"] is False
        assert out["missing_source_roots"]==["stegindex"]

def test_repo_root_map_can_resolve_stegindex():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); roots=make_roots(base); env=env_for(roots); env.pop("STEGVERSE_STEGINDEX_SOURCE_ROOT")
        env["STEGVERSE_REPO_ROOTS_JSON"]=json.dumps({"StegVerse-Labs/StegIndex":str(roots["stegindex"])})
        resolved,missing=M.resolve_roots(env)
        assert missing==[]
        assert resolved["stegindex"]==roots["stegindex"].resolve()


def test_completed_receipt_reobserves_stegindex_root_without_reexecution():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir()
        req=write_request(runtime); roots=make_roots(base); env=env_for(roots)
        receipt=runtime/M.RECEIPT_REL; receipt.parent.mkdir(parents=True,exist_ok=True)
        receipt.write_text(json.dumps({
          "schema":"stegverse.resident-execution-request-consumption/v1",
          "state":"COMPLETED",
          "request_id":"R1",
          "request_sha256":M.stable(req),
          "task_id":M.TASK_ID,
          "activation_complete":True
        }))
        calls=[]
        def runner(command,**kwargs):
            calls.append(command)
            raise AssertionError("completed activation must not re-execute")
        out=M.consume(source,runtime,runner,env)
        assert out["state"]=="ALREADY_CONSUMED"
        assert out["runtime_execution_attempted"] is False
        assert out["source_root_resolution_observed"] is True
        assert out["stegindex_source_root_resolved"] is True
        assert "stegindex" in out["resolved_source_roots"]
        assert out["missing_source_roots"]==[]
        assert calls==[]
        persisted=json.loads(receipt.read_text())
        assert persisted["stegindex_source_root_resolved"] is True

def test_attempt_receipt_records_secret_free_source_root_resolution():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir(); write_request(runtime)
        roots=make_roots(base); env=env_for(roots)
        script=runtime/"scripts/activate_resident_stack.py"; script.parent.mkdir(parents=True,exist_ok=True); script.write_text("# activate\n")
        def runner(command,**kwargs):
            return SimpleNamespace(returncode=1,stdout=json.dumps({"state":"INCOMPLETE"})+"\n",stderr="")
        out=M.consume(source,runtime,runner,env)
        assert out["state"]=="ATTEMPT_RECORDED"
        assert out["source_root_resolution_observed"] is True
        assert out["stegindex_source_root_resolved"] is True
        assert "stegindex" in out["resolved_source_roots"]
        assert all("/" not in key for key in out["resolved_source_roots"])
