#!/usr/bin/env python3
"""Materialize non-secret loopback route config for evaluator InTr runtime."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT=Path.home()/".stegverse/config/evaluator-intr-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")

class PredicatePending(RuntimeError): pass

def _roots(env: dict[str,str])->dict[str,Path]:
    out={}
    raw=env.get("STEGVERSE_REPO_ROOTS_JSON","").strip()
    if raw:
        value=json.loads(raw)
        if not isinstance(value,dict): raise PredicatePending("STEGVERSE_REPO_ROOTS_JSON must be object")
        for repo,path in value.items():
            if isinstance(repo,str) and isinstance(path,str):
                p=Path(path).expanduser().resolve()
                if p.is_dir(): out[repo]=p
    direct_site=env.get("STEGVERSE_SITE_ROOT","").strip()
    direct_stegos=env.get("STEGVERSE_STEGOS_ROOT","").strip()
    if direct_site:
        p=Path(direct_site).expanduser().resolve()
        if p.is_dir(): out["StegVerse-Labs/Site"]=p
    if direct_stegos:
        p=Path(direct_stegos).expanduser().resolve()
        if p.is_dir(): out["StegVerse-Labs/StegOS"]=p
    return out

def _node()->dict[str,Any]:
    for p in NODE_MARKERS:
        if p.is_file():
            v=json.loads(p.read_text(encoding="utf-8"))
            if v.get("declared") is not True: raise PredicatePending("sovereign node not declared")
            if v.get("credential_authority")!="TV/TVC": raise RuntimeError("node credential authority drift")
            return {"path":str(p),"value":v}
    raise PredicatePending("declared sovereign node marker unavailable")

def materialize(env:dict[str,str]|None=None, output:Path|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    roots=_roots(values)
    site=roots.get("StegVerse-Labs/Site")
    stegos=roots.get("StegVerse-Labs/StegOS")
    if not site: raise PredicatePending("local Site source root unavailable")
    if not stegos: raise PredicatePending("local StegOS source root unavailable")
    runtime_raw=values.get("STEGVERSE_HEARTBEAT_ROOT","").strip()
    if not runtime_raw: raise PredicatePending("resident runtime root unavailable")
    runtime=Path(runtime_raw).expanduser().resolve()
    if not runtime.is_dir(): raise PredicatePending("resident runtime root not materialized")
    node=_node()
    node_value=node["value"]
    identity=str(node_value.get("node_id") or node_value.get("node_ref") or node_value.get("boundary_identity_ref") or "").strip()
    if not identity: raise PredicatePending("node boundary identity unavailable")
    port_raw=values.get("STEGVERSE_EVALUATOR_INTR_PORT","8765").strip()
    try: port=int(port_raw)
    except ValueError as exc: raise PredicatePending("evaluator InTr port invalid") from exc
    if port < 1024 or port > 65535: raise PredicatePending("evaluator InTr port outside admitted range")
    config={
      "schema":"stegverse.evaluator-intr-route-config/v1",
      "site_root":str(site),"stegos_root":str(stegos),"runtime_root":str(runtime),
      "host":"127.0.0.1","port":port,"allowed_origin":"https://stegverse.org",
      "boundary_identity_ref":identity,"window_seconds":int(values.get("STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS","60")),
      "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE",
      "public_tls_terminated_by":"STEGVERSE_SHARED_SERVICE_GATEWAY",
      "second_machine_required":False,"authority_effect":"NONE_CONFIG_ONLY"
    }
    target=(output or Path(values.get("STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG","") or DEFAULT_OUTPUT)).expanduser().resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(config,indent=2,sort_keys=True)+"\n"
    if target.exists() and target.read_text(encoding="utf-8")==serialized:
        return {"state":"UNCHANGED","path":str(target),"config":config}
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=target.parent,delete=False) as f:
        f.write(serialized); tmp=Path(f.name)
    os.chmod(tmp,0o600); tmp.replace(target)
    return {"state":"MATERIALIZED","path":str(target),"config":config}

def main()->int:
    try:
        result=materialize()
        print(json.dumps({"schema":"stegverse.evaluator-intr-route-config-materialization/v1",**result},sort_keys=True)); return 0
    except PredicatePending as exc:
        print(json.dumps({"schema":"stegverse.evaluator-intr-route-config-materialization/v1","state":"PREDICATE_PENDING","reason":str(exc),"authority_effect":"NONE"},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
