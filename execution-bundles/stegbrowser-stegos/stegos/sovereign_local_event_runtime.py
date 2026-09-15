"""Bounded local-only EVENT_EPHEMERAL adapter for the StegBrowser carrier.

Behavior is pinned to StegVerse-Labs/StegOS/stegos/sovereign_local_event_runtime.py
(blob c3b19e85073b8d8cf8df4e953cb0d347da76d4e1). It creates no credential,
task, transition, heartbeat, route, or runtime authority.
"""
from __future__ import annotations
import json, os, re, signal, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from stegos.ephemeral_runtime_lease import LeaseProfile, LeaseRequest, RendezvousRequirement, RuntimeClass

CREDENTIAL_AUTHORITY = "TV/TVC"
AUTHORITY_EFFECT = False
SOVEREIGN_MATERIALIZATION_SCHEMA = "stegverse.sovereign-heartbeat-materialization/v4"
SOVEREIGN_PROCESS_SCHEMAS = {"stegverse.ephemeral-sovereign-process/v3", "stegverse.ephemeral-sovereign-process/v4"}
class SovereignLocalEventRuntimeError(RuntimeError): pass
Runner = Callable[..., subprocess.CompletedProcess[str]]
def _require(condition: bool, reason: str) -> None:
    if not condition: raise SovereignLocalEventRuntimeError(reason)
def _safe_segment(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return clean[:96] or "lease"
def _json_stdout(completed: subprocess.CompletedProcess[str], label: str) -> dict[str, Any]:
    _require(completed.returncode == 0, f"{label}_failed:returncode={completed.returncode}")
    try: value = json.loads(completed.stdout)
    except Exception as exc: raise SovereignLocalEventRuntimeError(f"{label}_invalid_json") from exc
    _require(isinstance(value, dict), f"{label}_object_required")
    return value

def _terminate(pid: object) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0: return True
    try: os.kill(pid, signal.SIGTERM)
    except OSError: return True
    return True

@dataclass
class SovereignLocalEventRuntimeAdapter:
    sovereign_source_root: Path
    runtime_base: Path
    python_executable: str = sys.executable
    runner: Runner = subprocess.run
    authority_effect = False
    def _materialize_script(self) -> Path: return self.sovereign_source_root / "scripts" / "install_sovereign_heartbeat_service.py"
    def _restart_script(self) -> Path: return self.sovereign_source_root / "scripts" / "restart_sovereign_ephemeral_node.py"
    def _validate_source_surface(self) -> None:
        _require(self._materialize_script().is_file(), "sovereign_materializer_missing")
        _require(self._restart_script().is_file(), "sovereign_node_supervisor_missing")
    def provision(self, request: LeaseRequest) -> Mapping[str, Any]:
        request.validate()
        _require(request.profile == LeaseProfile.INTAKE, "local_event_runtime_requires_intake")
        _require(request.runtime_class == RuntimeClass.EVENT_EPHEMERAL, "local_event_runtime_requires_event_ephemeral")
        _require(request.rendezvous == RendezvousRequirement.NOT_REQUIRED, "local_event_runtime_forbids_rendezvous")
        _require(request.persistent_host_required is False, "persistent_host_forbidden")
        _require(request.participant_machine_required is False, "participant_machine_forbidden")
        _require(request.developer_machine_required is False, "developer_machine_forbidden")
        _require(request.authority.credential_authority == CREDENTIAL_AUTHORITY, "credential_authority_must_remain_tv_tvc")
        self._validate_source_surface()
        runtime_root = (self.runtime_base / _safe_segment(request.lease_id)).resolve()
        completed = self.runner([self.python_executable, str(self._materialize_script()), "--source-root", str(self.sovereign_source_root.resolve()), "--runtime-root", str(runtime_root), "--materialize-only"], check=False, capture_output=True, text=True)
        receipt = _json_stdout(completed, "sovereign_materialization")
        _require(receipt.get("schema") == SOVEREIGN_MATERIALIZATION_SCHEMA, "unexpected_sovereign_materialization_schema")
        _require(Path(str(receipt.get("runtime_root", ""))).resolve() == runtime_root, "sovereign_runtime_root_mismatch")
        _require(receipt.get("credential_authority") == CREDENTIAL_AUTHORITY, "sovereign_credential_authority_mismatch")
        _require(receipt.get("credential_requirement") == "NONE", "materialization_credential_requirement_forbidden")
        _require(receipt.get("non_tv_tvc_secret_or_token_used") is False, "non_tv_tvc_secret_forbidden")
        _require(receipt.get("third_party_process_host_required") is False, "third_party_process_host_forbidden")
        _require(receipt.get("third_party_scheduler_required") is False, "third_party_scheduler_forbidden")
        _require(receipt.get("heartbeat_grants_execution_authority") is False, "heartbeat_execution_authority_forbidden")
        return {"lease_id":request.lease_id,"runtime_root":str(runtime_root),"implementation_ref":request.implementation_ref,"state_root_binding":request.state_root_binding,"source_receipt_id":request.source_receipt_id,"consequence_id":request.consequence_id,"generation":request.generation,"rendezvous_required":False,"materialization_receipt":receipt,"credential_authority":CREDENTIAL_AUTHORITY,"credential_material_present":False,"requires_other_machine":False,"authority_effect":AUTHORITY_EFFECT}
    def materialize(self, compute_lease: Mapping[str, Any], implementation_ref: str) -> Mapping[str, Any]:
        runtime_root=Path(str(compute_lease.get("runtime_root", ""))).resolve()
        _require(runtime_root.is_dir(),"materialized_runtime_root_missing")
        _require(compute_lease.get("implementation_ref")==implementation_ref,"implementation_ref_mismatch")
        _require(compute_lease.get("rendezvous_required") is False,"local_event_runtime_rendezvous_drift")
        _require(compute_lease.get("credential_authority")==CREDENTIAL_AUTHORITY,"credential_authority_must_remain_tv_tvc")
        _require(compute_lease.get("credential_material_present") is False,"credential_material_forbidden")
        completed=self.runner([self.python_executable,str(self._restart_script()),"--runtime-root",str(runtime_root)],check=False,capture_output=True,text=True)
        receipt=_json_stdout(completed,"sovereign_node_start")
        _require(receipt.get("schema") in SOVEREIGN_PROCESS_SCHEMAS,"unexpected_sovereign_process_schema")
        _require(receipt.get("active") is True,"sovereign_node_not_active")
        _require(receipt.get("carrier_active") is True,"sovereign_carrier_not_active")
        _require(receipt.get("worker_active") is True,"sovereign_worker_not_active")
        _require(receipt.get("worker_task_capable_cycle_observed") is True,"sovereign_worker_cycle_not_observed")
        _require(receipt.get("separate_carrier_and_worker_processes") is True,"separated_runtime_required")
        _require(receipt.get("credential_authority")==CREDENTIAL_AUTHORITY,"sovereign_process_credential_authority_mismatch")
        _require(receipt.get("non_tv_tvc_secret_or_token_used") is False,"sovereign_process_non_tv_tvc_secret_forbidden")
        runtime_id=receipt.get("runtime_id")
        if not isinstance(runtime_id,str) or not runtime_id: runtime_id=f"LOCAL-EVENT-{compute_lease['lease_id']}"
        return {"runtime_id":runtime_id,"runtime_root":str(runtime_root),"lease_id":compute_lease["lease_id"],"implementation_ref":implementation_ref,"state_root_binding":compute_lease["state_root_binding"],"carrier_pid":receipt.get("carrier_pid",receipt.get("pid")),"worker_pid":receipt.get("worker_pid"),"node_process_receipt":receipt,"local_identity_basis":"SOVEREIGN_PROCESS_RECEIPT","rendezvous_required":False,"route_admitted":False,"outbound_egress_executed":False,"credential_authority":CREDENTIAL_AUTHORITY,"credential_material_present":False,"requires_other_machine":False,"authority_effect":AUTHORITY_EFFECT}
    def verify_local(self, runtime: Mapping[str, Any], implementation_ref: str) -> Mapping[str, Any]:
        _require(runtime.get("implementation_ref")==implementation_ref,"local_implementation_ref_mismatch")
        _require(runtime.get("rendezvous_required") is False,"local_runtime_rendezvous_forbidden")
        _require(runtime.get("route_admitted") is False,"local_runtime_cannot_admit_route")
        _require(runtime.get("outbound_egress_executed") is False,"local_runtime_cannot_execute_egress")
        _require(runtime.get("credential_authority")==CREDENTIAL_AUTHORITY,"credential_authority_must_remain_tv_tvc")
        _require(runtime.get("credential_material_present") is False,"credential_material_forbidden")
        receipt=runtime.get("node_process_receipt"); _require(isinstance(receipt,Mapping),"node_process_receipt_required")
        _require(receipt.get("active") is True,"local_sovereign_process_not_active")
        _require(receipt.get("carrier_active") is True,"local_sovereign_carrier_not_active")
        _require(receipt.get("worker_active") is True,"local_sovereign_worker_not_active")
        _require(receipt.get("worker_task_capable_cycle_observed") is True,"local_worker_task_cycle_not_observed")
        return {"verified":True,"verification_kind":"SOVEREIGN_LOCAL_EVENT_RUNTIME_READY","runtime_id":runtime["runtime_id"],"implementation_ref":implementation_ref,"requires_other_machine":False,"rendezvous_required":False,"authority_effect":AUTHORITY_EFFECT}
    def verify_public(self, rendezvous: Mapping[str, Any], implementation_ref: str) -> Mapping[str, Any]: raise SovereignLocalEventRuntimeError("public_verification_not_part_of_local_event_runtime")
    def open(self, runtime: Mapping[str, Any]) -> Mapping[str, Any]: raise SovereignLocalEventRuntimeError("rendezvous_not_part_of_local_event_runtime")
    def close(self, rendezvous: Mapping[str, Any] | None) -> Mapping[str, Any]: return {"required":False,"closed":True,"authority_effect":"NONE"}
    def release(self, compute_lease: Mapping[str, Any]) -> Mapping[str, Any]:
        runtime_root=Path(str(compute_lease.get("runtime_root", ""))).resolve(); process_path=runtime_root/"receipts"/"sovereign-host"/"ephemeral-process.latest.json"; process_receipt={}
        if process_path.is_file():
            try:
                value=json.loads(process_path.read_text(encoding="utf-8")); process_receipt=value if isinstance(value,dict) else {}
            except Exception: process_receipt={}
        return {"runtime_root":str(runtime_root),"carrier_terminated":_terminate(process_receipt.get("carrier_pid",process_receipt.get("pid"))),"worker_terminated":_terminate(process_receipt.get("worker_pid")),"rendezvous_terminated":True,"credential_authority":CREDENTIAL_AUTHORITY,"credential_material_present":False,"requires_other_machine":False,"authority_effect":AUTHORITY_EFFECT}

SOURCE_PROVENANCE={"repository":"StegVerse-Labs/StegOS","source_path":"stegos/sovereign_local_event_runtime.py","source_blob_sha":"c3b19e85073b8d8cf8df4e953cb0d347da76d4e1","authority_effect":"NONE"}
