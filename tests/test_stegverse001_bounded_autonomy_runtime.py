from __future__ import annotations
import importlib.util, json, os, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv001",ROOT/"workers/stegverse001_bounded_autonomy_runtime_worker.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

def lease():
    return {
      "schema":"stegverse.stegverse001.bounded-autonomy-lease/v1",
      "lease_id":"TEST-LEASE-1","entity_id":"StegVerse-001","entity_alias":"Beta_Orionis",
      "request_id":"TV-REQUEST-STEGVERSE001-BOUNDED-AUTONOMY-001","request_hash":"sha256:c4b3e35d5ecf2246e0e082a591e3144bd61b32cb02133d12a89226cf362f4def",
      "lease_state":"ACTIVE","issuer":"TV/TVC","credential_authority":"TV/TVC",
      "expires_at":(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
      "allowed_transition_classes":["AUTONOMOUS_TASK_DISCOVERY","LOCAL_STATE_OBSERVATION","RECEIPT_EMISSION"],
      "forbidden_transition_classes":["SELF_ACCREDITATION","SOVEREIGN_AUTHORITY_CHANGE","FINANCIAL_BINDING"],
      "receipt_required":True,"denial_reachable_required":True,"denial_reachable":True,
      "self_accreditation_allowed":False,"sovereign_authority_granted":False,
      "lease_consumption":"SINGLE_AUTONOMY_CYCLE",
      "authority_effect":"BOUNDED_PREAUTHORIZED_TRANSITION_CLASSES_ONLY"
    }
    v["lease_hash"]=MOD.sha(v)
    return v

def test_missing_lease_is_pending():
    with tempfile.TemporaryDirectory() as td:
        try: MOD.validate_lease(Path(td)/"missing.json")
        except MOD.LeasePending: pass
        else: raise AssertionError("missing lease must not authorize")

def test_expired_lease_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"lease.json"; v=lease(); v["expires_at"]=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(); p.write_text(json.dumps(v))
        try: MOD.validate_lease(p)
        except RuntimeError as e: assert "expired" in str(e)
        else: raise AssertionError("expired lease accepted")

def test_autonomous_cycle_is_bounded_and_receipted():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); rr=base/"runtime"; (rr/"control").mkdir(parents=True)
        (rr/"control/heartbeat-carrier-runtime-state.json").write_text(json.dumps({"epoch":44}))
        (rr/"control/worker-runtime-state.json").write_text(json.dumps({"observation_mode":"TASK_CAPABLE_EXECUTION"}))
        lp=base/"lease.json"; lp.write_text(json.dumps(lease()))
        task={"claim_id":"claim-1","heartbeat_timing":{"fencing_token":77}}
        with mock.patch.object(MOD,"STATE_ROOT",base/"state"), mock.patch.object(MOD,"runtime_root",return_value=rr):
            rec=MOD.run_cycle(task,MOD.validate_lease(lp),lp)
        assert rec["transition_id"]=="SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED"
        assert rec["self_directed_task_discovery"] is True
        assert rec["autonomous_plan_selection"] is True
        assert rec["network_access_performed"] is False
        assert rec["repository_writeback_performed"] is False
        assert rec["financial_binding_performed"] is False
        assert rec["self_accreditation"] is False
        assert rec["sovereign_authority_claimed"] is False
        assert rec["master_records_custody"]=="PENDING"
        assert (base/"state/receipts/latest.json").is_file()


def test_consumed_lease_is_rejected():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); lp=base/"lease.json"; v=lease(); v["lease_consumption"]="SINGLE_AUTONOMY_CYCLE"; lp.write_text(json.dumps(v))
        used=base/"state/lease-consumption"; used.mkdir(parents=True)
        (used/(v["lease_id"]+".json")).write_text(json.dumps({"state":"CONSUMED"}))
        with mock.patch.object(MOD,"STATE_ROOT",base/"state"):
            try: MOD.validate_lease(lp)
            except RuntimeError as e: assert "already consumed" in str(e)
            else: raise AssertionError("consumed lease accepted")

def test_tvc_default_lease_discovery():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"lease.active.json"; p.write_text("{}")
        with mock.patch.dict(os.environ,{},clear=True), mock.patch.object(MOD,"TVC_DEFAULT_LEASE",p):
            assert MOD.resolve_lease_path()==p
