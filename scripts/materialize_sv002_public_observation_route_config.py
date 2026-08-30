#!/usr/bin/env python3
"""Materialize non-secret route config for StegVerse-002 public observation receiver."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
DEFAULT=Path.home()/".stegverse/config/sv002-public-observe-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")
class Pending(RuntimeError): pass
def roots(env):
    out={}; raw=env.get("STEGVERSE_REPO_ROOTS_JSON","").strip()
    if raw:
        for repo,path in json.loads(raw).items():
            p=Path(path).expanduser().resolve()
            if p.is_dir(): out[repo]=p
    for key,repo in (("STEGVERSE_STEGOS_ROOT","StegVerse-Labs/StegOS"),("STEGVERSE_SITE_ROOT","StegVerse-Labs/Site")):
        if env.get(key):
            p=Path(env[key]).expanduser().resolve()
            if p.is_dir(): out[repo]=p
    return out
def node():
    for p in NODE_MARKERS:
        if p.is_file():
            v=json.loads(p.read_text())
            if v.get("declared") is not True: raise Pending("sovereign node not declared")
            if v.get("credential_authority")!="TV/TVC": raise RuntimeError("node credential authority drift")
            ident=str(v.get("node_id") or v.get("node_ref") or v.get("boundary_identity_ref") or "").strip()
            if not ident: raise Pending("node boundary identity unavailable")
            return ident
    raise Pending("declared sovereign node marker unavailable")
def materialize(env=None,output=None):
    e=dict(os.environ if env is None else env); r=roots(e); stegos=r.get("StegVerse-Labs/StegOS")
    if not stegos: raise Pending("local StegOS source root unavailable")
    runtime=Path(e.get("STEGVERSE_HEARTBEAT_ROOT","")).expanduser().resolve()
    if not str(e.get("STEGVERSE_HEARTBEAT_ROOT","")).strip() or not runtime.is_dir(): raise Pending("resident runtime root unavailable")
    port=int(e.get("STEGVERSE_SV002_OBSERVE_INTR_PORT","8766"))
    if port<1024 or port>65535: raise Pending("observation port outside admitted range")
    cfg={"schema":"stegverse.sv002-public-observe-route-config/v1","stegos_root":str(stegos),"runtime_root":str(runtime),"host":"127.0.0.1","port":port,"allowed_origin":"https://stegverse.org","boundary_identity_ref":node(),"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","public_tls_terminated_by":"STEGVERSE_SHARED_SERVICE_GATEWAY","second_machine_required":False,"authority_effect":"NONE_CONFIG_ONLY"}
    target=(output or Path(e.get("STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG","") or DEFAULT)).expanduser().resolve(); target.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(cfg,indent=2,sort_keys=True)+"\n"
    if target.exists() and target.read_text()==data: return {"state":"UNCHANGED","path":str(target),"config":cfg}
    with tempfile.NamedTemporaryFile("w",dir=target.parent,delete=False) as f: f.write(data); tmp=Path(f.name)
    os.chmod(tmp,0o600); tmp.replace(target); return {"state":"MATERIALIZED","path":str(target),"config":cfg}
def main():
    try: print(json.dumps({"schema":"stegverse.sv002-public-observe-route-config-materialization/v1",**materialize()},sort_keys=True)); return 0
    except Pending as exc: print(json.dumps({"schema":"stegverse.sv002-public-observe-route-config-materialization/v1","state":"PREDICATE_PENDING","reason":str(exc),"authority_effect":"NONE"},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
