from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("run_worker_runtime_machine_continuation",ROOT/"scripts/run_worker_runtime.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

def test_due_machine_continuation_dispatches_without_unsupported_env_argument():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        trigger={
          "continuation_due":True,
          "window":{"window_id":42},
          "authority_effect":"NONE_TRIGGER_ONLY"
        }
        dispatch={
          "state":"DISPATCH_COMPLETE",
          "runtime_execution_attempted":True,
          "authority_effect":"NONE_NATIVE_REQUEST_VISIT_ONLY"
        }
        with (
            mock.patch.object(MOD,"current_reference",return_value={"epoch":4200,"heartbeat_id":"HB-4200"}),
            mock.patch.object(MOD,"build_continuation_trigger",return_value=trigger),
            mock.patch.object(MOD,"dispatch_local_resident_requests",return_value=dispatch) as visit,
        ):
            out=MOD.maybe_dispatch_machine_continuation(
                root,
                env={"STEGVERSE_TVC_ROOT":"/local/tvc","GITHUB_TOKEN":"must-not-be-forwarded-here"},
            )
        visit.assert_called_once_with(root)
        assert out["dispatch_attempted"] is True
        assert out["dispatch_result"]["state"]=="DISPATCH_COMPLETE"
        state=json.loads((root/MOD.MACHINE_CONTINUATION_STATE_REL).read_text())
        assert state["last_consumed_window_id"]==42
        assert state["last_dispatch_state"]=="DISPATCH_COMPLETE"

def test_not_due_machine_continuation_does_not_dispatch():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        with (
            mock.patch.object(MOD,"current_reference",return_value={"epoch":4201,"heartbeat_id":"HB-4201"}),
            mock.patch.object(MOD,"build_continuation_trigger",return_value={"continuation_due":False,"window":{"window_id":42}}),
            mock.patch.object(MOD,"dispatch_local_resident_requests") as visit,
        ):
            out=MOD.maybe_dispatch_machine_continuation(root)
        visit.assert_not_called()
        assert out["dispatch_attempted"] is False
