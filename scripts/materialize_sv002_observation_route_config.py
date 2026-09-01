#!/usr/bin/env python3
"""Materialize non-secret route config for the StegVerse-002 observation receiver."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT=Path.home()/".stegverse/config/sv002-public-observation-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")
class PredicatePending(RuntimeError): pass

REPO_REQUIREMENTS={
    "StegVerse-Labs/StegOS":("stegos/universal_intr_transport.py",),
    "StegVerse-002/micro-node-runtime":(
        "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json",
    ),
}

def _valid_repo(repo:str,path:Path,*,require_git:bool)->bool:
    required=REPO_REQUIREMENTS.get(repo,())
    return (
        path.is_dir()
        and all((path/rel).is_file() for rel in required)
        and (not require_git or (path/".git").exists())
    )

def _canonical_repo_candidates(repo:str,env:dict[str,str])->list[Path]:
    org,name=repo.split("/",1)
    home=Path(env.get("HOME") or str(Path.home())).expanduser()
    return [
        (home/".stegverse/repos"/org/name).resolve(),
        (Path("/var/lib/stegverse/source")/org/name).resolve(),
        (Path("/srv/stegverse/repos")/org/name).resolve(),
        (Path("/opt/stegverse/repos")/org/name).resolve(),
    ]

def _roots(env:dict[str,str])->dict[str,Path]:
    out={}
    raw=env.get("STEGVERSE_REPO_ROOTS_JSON","").strip()
    if raw:
        value=json.loads(raw)
        if not isinstance(value,dict): raise PredicatePending("STEGVERSE_REPO_ROOTS_JSON must be object")
        for repo,path in value.items():
            if isinstance(repo,str) and isinstance(path,str):
                p=Path(path).expanduser().resolve()
                if _valid_repo(repo,p,require_git=False): out[repo]=p
    direct={"StegVerse-Labs/StegOS":"STEGVERSE_STEGOS_ROOT","StegVerse-002/micro-node-runtime":"STEGVERSE_MICRO_NODE_RUNTIME_ROOT"}
    for repo,key in direct.items():
        raw=env.get(key,"").strip()
        if raw:
            p=Path(raw).expanduser().resolve()
            if _valid_repo(repo,p,require_git=False): out[repo]=p
    for repo in REPO_REQUIREMENTS:
        if repo in out:
            continue
        found=[]
        for candidate in _canonical_repo_candidates(repo,env):
            if candidate not in found and _valid_repo(repo,candidate,require_git=True):
                found.append(candidate)
        if len(found)==1:
            out[repo]=found[0]
    return out

def _runtime_root(env:dict[str,str], *, script_root:Path|None=None)->Path:
    raw=env.get("STEGVERSE_HEARTBEAT_ROOT","").strip()
    if raw:
        runtime=Path(raw).expanduser().resolve()
        if runtime.is_dir():
            return runtime
        raise PredicatePending("resident runtime root not materialized")
    root=(script_root or Path(__file__).resolve().parents[1]).expanduser().resolve()
    if root.is_dir() and not (root/".git").exists() and (root/"workers").is_dir() and (root/"control").is_dir():
        return root
    raise PredicatePending("resident runtime root unavailable")

def _node()->dict[str,Any]:
    for p in NODE_MARKERS:
        if p.is_file():
            v=json.loads(p.read_text(encoding="utf-8"))
            if v.get("declared") is not True: raise PredicatePending("sovereign node not declared")
            if v.get("credential_authority")!="TV/TVC": raise RuntimeError("node credential authority drift")
            return v
    raise PredicatePending("declared sovereign node marker unavailable")

def materialize(env:dict[str,str]|None=None,output:Path|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env); roots=_roots(values)
    stegos=roots.get("StegVerse-Labs/StegOS"); micro=roots.get("StegVerse-002/micro-node-runtime")
    if not stegos: raise PredicatePending("local StegOS source root unavailable")
    if not micro: raise PredicatePending("local StegVerse-002/micro-node-runtime source root unavailable")
    if not (micro/"experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json").is_file(): raise PredicatePending("StegVerse-002 construction provenance not materialized")
    runtime=_runtime_root(values)
    node=_node(); identity=str(node.get("node_id") or node.get("node_ref") or node.get("boundary_identity_ref") or "").strip()
    if not identity: raise PredicatePending("node boundary identity unavailable")
    try: port=int(values.get("STEGVERSE_SV002_OBSERVE_PORT","8766"))
    except ValueError as exc: raise PredicatePending("SV002 observation port invalid") from exc
    if port<1024 or port>65535: raise PredicatePending("SV002 observation port outside admitted range")
    master_receipt=str(values.get("STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT","")).strip()
    config={"schema":"stegverse.sv002-public-observation-route-config/v1","stegos_root":str(stegos),"micro_node_root":str(micro),"runtime_root":str(runtime),"host":"127.0.0.1","port":port,"allowed_origin":"https://stegverse.org","boundary_identity_ref":identity,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","public_tls_terminated_by":"STEGVERSE_SHARED_SERVICE_GATEWAY","second_machine_required":False,"authority_effect":"NONE_CONFIG_ONLY"}
    if master_receipt:
        config["master_records_reconstruction_receipt"]=str(Path(master_receipt).expanduser().resolve())
    target=(output or Path(values.get("STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG","") or DEFAULT_OUTPUT)).expanduser().resolve(); target.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(config,indent=2,sort_keys=True)+"\n"
    if target.exists() and target.read_text(encoding="utf-8")==serialized: return {"state":"UNCHANGED","path":str(target),"config":config}
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=target.parent,delete=False) as f: f.write(serialized); tmp=Path(f.name)
    os.chmod(tmp,0o600); tmp.replace(target); return {"state":"MATERIALIZED","path":str(target),"config":config}

def main()->int:
    try:
        result=materialize(); print(json.dumps({"schema":"stegverse.sv002-public-observation-route-config-materialization/v1",**result},sort_keys=True)); return 0
    except PredicatePending as exc:
        print(json.dumps({"schema":"stegverse.sv002-public-observation-route-config-materialization/v1","state":"PREDICATE_PENDING","reason":str(exc),"authority_effect":"NONE"},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
