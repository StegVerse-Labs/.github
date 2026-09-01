#!/usr/bin/env python3
"""Materialize the non-secret shared-Gateway route for Universal InTr."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path

DEFAULT_OUTPUT=Path.home()/".stegverse/config/universal-intr-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")
REQUIRED_PROFILES=("KV:KnowledgeVaultInterlock",)
class PredicatePending(RuntimeError): pass

def _node_identity()->str:
    for path in NODE_MARKERS:
        if not path.is_file(): continue
        value=json.loads(path.read_text(encoding="utf-8"))
        if value.get("declared") is not True: raise PredicatePending("sovereign node not declared")
        if value.get("credential_authority")!="TV/TVC": raise RuntimeError("node credential authority drift")
        identity=str(value.get("node_id") or value.get("node_ref") or value.get("boundary_identity_ref") or "").strip()
        if identity:return identity
    raise PredicatePending("declared sovereign node identity unavailable")

def materialize(env=None,output=None):
    values=dict(os.environ if env is None else env)
    runtime_raw=values.get("STEGVERSE_HEARTBEAT_ROOT","").strip()
    if not runtime_raw:raise PredicatePending("resident runtime root unavailable")
    runtime=Path(runtime_raw).expanduser().resolve()
    if not runtime.is_dir():raise PredicatePending("resident runtime root not materialized")
    port=int(values.get("STEGVERSE_UNIVERSAL_INTR_PORT",values.get("STEGVERSE_HIL_RECEIVER_PORT","8765")))
    if not 1024<=port<=65535:raise PredicatePending("Universal InTr port invalid")
    provider_binding=values.get("STEGVERSE_KV_PROVIDER_BINDING_PATH","").strip()
    provider_materialized_root=values.get("STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT","").strip()
    provider_session_file=values.get("STEGVERSE_TVC_PROVIDER_SESSION_FILE","").strip()
    config={
      "schema":"stegverse.universal-intr-route-config/v1",
      "runtime_root":str(runtime),
      "host":"127.0.0.1",
      "port":port,
      "loopback_url":f"http://127.0.0.1:{port}",
      "profile_path":"/intr/profile",
      "materialization_path":"/intr/materialization",
      "device_kv_result_path":"/intr/device-kv/result",
      "required_profiles":list(REQUIRED_PROFILES),
      "public_origin":"https://stegverse.org",
      "public_tls_terminated_by":"STEGVERSE_SHARED_SERVICE_GATEWAY",
      "boundary_identity_ref":_node_identity(),
      "event_triggered":True,
      "always_on_application_receiver_required":False,
      "second_user_device_required":False,
      "g18_required":False,
      "personal_kv_provider_binding_configured":bool(provider_binding),
      "personal_kv_materialized_root_configured":bool(provider_materialized_root),
      "tvc_provider_session_reference_configured":bool(provider_session_file),
      "provider_session_plaintext_in_config":False,
      "credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE",
      "execution_authority":"NONE",
      "authority_effect":"NONE_CONFIG_ONLY"
    }
    target=(output or Path(values.get("STEGVERSE_UNIVERSAL_INTR_ROUTE_CONFIG","") or DEFAULT_OUTPUT)).expanduser().resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(config,indent=2,sort_keys=True)+"\n"
    if target.exists() and target.read_text(encoding="utf-8")==serialized:
        return {"state":"UNCHANGED","path":str(target),"config":config}
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=target.parent,delete=False) as handle:
        handle.write(serialized);temp=Path(handle.name)
    os.chmod(temp,0o600);temp.replace(target)
    return {"state":"MATERIALIZED","path":str(target),"config":config}

def main()->int:
    try:
        result=materialize()
        print(json.dumps({"schema":"stegverse.universal-intr-route-config-materialization/v1",**result},sort_keys=True));return 0
    except PredicatePending as exc:
        print(json.dumps({"schema":"stegverse.universal-intr-route-config-materialization/v1","state":"PREDICATE_PENDING","reason":str(exc),"authority_effect":"NONE"},sort_keys=True));return 0

if __name__=="__main__":raise SystemExit(main())
