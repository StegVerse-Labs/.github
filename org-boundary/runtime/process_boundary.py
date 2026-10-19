#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
# Processing is selected by the admitted manifest, not by the addressed row.
_SELSPEC=importlib.util.spec_from_file_location(
    "manifest_selection", Path(__file__).resolve().parent/"manifest_selection.py")
selection=importlib.util.module_from_spec(_SELSPEC)
_SELSPEC.loader.exec_module(selection)
# Standing is an ingress precondition. This file is a separately invocable
# ingress surface -- `sdk_manifest_crossing.py` runs it directly as a
# subprocess, never through `kernel.dispatch` -- so a gate that lives only in
# the kernel leaves this lane, the external one, ungated. It is resolved here
# too, before anything is selected or minted.
_NSSPEC=importlib.util.spec_from_file_location(
    "node_standing", Path(__file__).resolve().parent/"node_standing.py")
node_standing=importlib.util.module_from_spec(_NSSPEC)
_NSSPEC.loader.exec_module(node_standing)
KINDS=["INGRESS_ACCEPTED","DISPATCHED","CONSUMED","RESULT_BOUND","EGRESS_EMITTED"]
def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":")).encode()
def hid(prefix,v): return prefix+"-"+hashlib.sha256(canon(v)).hexdigest()[:24]
def load(path): return json.loads(Path(path).read_text())

def resolve_adapter(svc):
    """Resolve only an adapter the capability map explicitly admits.

    Filesystem containment is not admissibility. The registry's disposition is
    the policy; a path is only the materialized module locator after admission.
    """
    disposition=svc.get("endpoint_adapter_disposition")
    if disposition!="ALLOW_DECLARED_ADAPTER":
        raise SystemExit(str(disposition or "FAIL_CLOSED_ENDPOINT_ADAPTER_UNDECLARED"))
    adapter=svc.get("endpoint_adapter")
    if not adapter:
        raise SystemExit("FAIL_CLOSED_ENDPOINT_ADAPTER_NOT_INSTALLED")
    candidate=Path(str(adapter))
    if not candidate.is_absolute():
        candidate=ROOT/candidate
    candidate=candidate.resolve()
    if not candidate.is_file():
        raise SystemExit("FAIL_CLOSED_ENDPOINT_ADAPTER_NOT_MATERIALIZED")
    return candidate

NODE_STATE_WRITE_ONCE="NODE_STATE_WRITE_ONCE"

def endpoint_result(env,svc,envelope_path,node_state_root=None):
    role=svc.get("boundary_role")
    if role=="INTERNAL_ENDPOINT":
        adapter=resolve_adapter(svc)
        command=["python3",str(adapter),"--envelope",str(Path(envelope_path).resolve())]
        # Only an adapter declared to write node state is handed its location.
        # It refuses its write when none was supplied; a pure adapter is given
        # nothing it could write to.
        if svc.get("endpoint_adapter_effect")==NODE_STATE_WRITE_ONCE and node_state_root is not None:
            command+=["--node-state-root",str(node_state_root)]
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"endpoint-response.json"
            completed=subprocess.run(
                command+["--out",str(out)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode!=0 or not out.is_file():
                # Carry the adapter's own reason. Discarding it made every
                # adapter failure read as one opaque message at the boundary.
                detail=(completed.stderr or completed.stdout or "").strip().splitlines()
                raise SystemExit("endpoint-adapter-execution-failed"
                                 + (": "+detail[-1] if detail else ""))
            result=load(out)
            if not isinstance(result,dict):
                raise SystemExit("endpoint-adapter-result-invalid")
            return result
    if role=="BOUNDARY_LOCAL_DIAGNOSTIC":
        return {"echo":env["payload"]}
    raise SystemExit("endpoint-adapter-not-installed")
# Fault semantics aligned to Data-Continuation/.github#10 (Labs#3296 follow-on),
# without changing the processing above. An input that cannot be read or parsed
# is the caller's fault: a TERMINAL six-field record, exit 65 (EX_DATAERR). This
# node's own failure to write --out is NON-terminal: six fields, exit 75
# (EX_TEMPFAIL), and the result is replaced atomically so no partial file stays.
EXIT_INPUT_FAULT=65
EXIT_WRITE_FAULT=75
FAULT_RETRY_ENTRYPOINT="resident-runtime/sdk_manifest_crossing.py::cross (org-boundary/runtime/process_boundary.py)"
FAULT_OWNING_GOAL="INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"

def fault_record(code,predicate,detail,*,terminal,repair,next_attempt):
    return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":predicate,"detail":detail,
            "required_evidence_or_repair":repair,"retry_entrypoint":FAULT_RETRY_ENTRYPOINT,
            "owning_existing_goal":FAULT_OWNING_GOAL,"next_attempt":next_attempt,
            "terminal":terminal,"consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}

def fail(record,code):
    print(json.dumps(record,sort_keys=True)); sys.exit(code)

def read_input(path,argument):
    """One JSON object input, or the terminal PROCESS_BOUNDARY_INPUT_FAULT (exit 65). Writes nothing."""
    try:
        value=json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,UnicodeDecodeError,ValueError) as exc:
        value,detail=None,argument+": "+type(exc).__name__+": "+str(exc)
    else:
        detail=None if isinstance(value,dict) else argument+": top-level "+type(value).__name__+", expected dict"
    if detail is not None:
        fail(fault_record("PROCESS_BOUNDARY_INPUT_FAULT","PROCESS_BOUNDARY_INPUTS_ARE_READABLE_JSON_OBJECTS",detail,
                          terminal=True,repair="supply "+argument+" as a readable UTF-8 JSON object; nothing was written",
                          next_attempt="a corrected "+argument+"; this input is refused as given"),EXIT_INPUT_FAULT)
    return value

def write_result(out,text):
    """Replace --out atomically, or the non-terminal PROCESS_BOUNDARY_WRITE_FAULT (exit 75); no partial file."""
    out=Path(out); tmp=None
    try:
        out.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix="."+out.name+".",suffix=".tmp",dir=str(out.parent))
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            handle.write(text)
        # The permissions a plain write would have given it (mkstemp makes 0600).
        umask=os.umask(0); os.umask(umask)
        os.chmod(tmp,0o666&~umask)
        os.replace(tmp,out); tmp=None
    except OSError as exc:
        if tmp is not None:
            try: os.unlink(tmp)
            except OSError: pass
        fail(fault_record("PROCESS_BOUNDARY_WRITE_FAULT","PROCESS_BOUNDARY_WRITES_ITS_RESULT_ATOMICALLY",
                          "--out: "+type(exc).__name__+": "+str(exc),terminal=False,
                          repair="restore a writable --out location; no partial result was left",
                          next_attempt="run the same crossing again; the processing is deterministic"),EXIT_WRITE_FAULT)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--envelope",required=True); ap.add_argument("--registry",required=True); ap.add_argument("--out",required=True); ap.add_argument("--node-state-root",default=None); a=ap.parse_args()
 env=read_input(a.envelope,"--envelope"); reg=read_input(a.registry,"--registry")
 req=["schema_version","packet_id","direction","origin","destination","carrier","intr_profile","transition","payload","evidence"]; miss=[k for k in req if k not in env]
 if miss: raise SystemExit("missing:"+",".join(miss))
 if env["destination"]["org"]!=reg["organization"]: raise SystemExit("wrong-destination-org")
 svc=next((s for s in reg["services"] if s["service_id"]==env["destination"]["service"]),None)
 if not svc: raise SystemExit("unknown-service")
 # Standing first, then selection. The contract covers ingress, and selection
 # is processing: a crossing that has not established standing must not reach
 # the question of what processing it selected.
 standing=node_standing.require(node_standing.load_contract(ROOT),env)
 # Refuse a declaration this service does not admit before any receipt is
 # minted: a refused crossing must not leave a chain implying it was consumed.
 selected=selection.select_processing(svc,env["payload"])
 base={"packet_id":env["packet_id"],"service_id":svc["service_id"],"payload_hash":hashlib.sha256(canon(env["payload"])).hexdigest()}
 receipts=[]; prev=None
 for kind in KINDS:
  subject={**base,"kind":kind,"previous_receipt_id":prev}; rid=hid(kind.lower(),subject); receipts.append({"kind":kind,"receipt_id":rid,"subject":svc["service_id"],"evidence_hash":hashlib.sha256(canon(subject)).hexdigest(),"previous_receipt_id":prev}); prev=rid
 application_result=endpoint_result(env,svc,a.envelope,a.node_state_root)
 result={"schema_version":reg["organization"].lower().replace(" ","-")+".boundary-execution.v1","packet_id":env["packet_id"],"organization":reg["organization"],"service_id":svc["service_id"],"consumed":True,"application_result":application_result,"authority_effect":env["transition"]["authority_effect"],**selected,**standing,"receipts":receipts,"reconstruction":{"same_execution_required":True,"status":"RECONSTRUCTED","terminal_receipt_id":prev}}
 write_result(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps({"status":"PASS","terminal_receipt_id":prev}))
if __name__=="__main__": main()
