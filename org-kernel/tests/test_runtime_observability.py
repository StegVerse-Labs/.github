#!/usr/bin/env python3
import importlib.util, json, tempfile
from pathlib import Path

spec=importlib.util.spec_from_file_location("obs","org-kernel/runtime_observability.py")
obs=importlib.util.module_from_spec(spec); spec.loader.exec_module(obs)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"resident-runtime").mkdir(parents=True)
    (root/"control").mkdir(parents=True)
    (root/"receipts/runtime-observability").mkdir(parents=True)
    (root/"resident-runtime/activation-manifest.json").write_text(json.dumps({
        "organization":"Test-Org","canonical_repository":"Test-Org/.github",
        "state":"SOURCE_INSTALLED_RUNTIME_OBSERVATION_PENDING"
    }))
    (root/"control/heartbeat-carrier-runtime-state.json").write_text(json.dumps({
        "epoch":31,"generation":31,"last_cycle_at":"2026-08-18T19:47:00Z"
    }))
    (root/"control/worker-runtime-state.json").write_text(json.dumps({
        "runtime_tick":2,"last_cycle_at":"2026-08-18T19:47:00Z",
        "observation_mode":"CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
    }))
    (root/"control/worker-control-plane-coordination.json").write_text(json.dumps({
        "worker_coordination":{"state":"ACTIVE","active_leases":[{"task_id":"X"}]}
    }))
    now_ns=obs.K.HB_ANCHOR_UNIX_NS+10_000_000_000
    snap=obs.snapshot(root,now_ns=now_ns)
    assert snap["resident"]["process_observed"] is False
    assert snap["resident"]["current"] is False
    assert snap["runtime_truth"]["governed_request_consumption_proven"] is False
    assert snap["persisted_observers"]["carrier"]["observation_only"] is True
    assert snap["authority"]["hb_grants_authority"] is False

    presence=root/"receipts/runtime-observability/resident-presence.latest.json"
    presence.write_text(json.dumps({
        "schema":"synthetic.test.resident-presence/v1",
        "state":"OBSERVED",
        "runtime_instance_id":"runtime-test-1",
        "node_id":"node-test-1",
        "observed_at":"2026-08-23T19:00:10+00:00"
    }))
    snap2=obs.snapshot(root,now_ns=now_ns,evidence_bindings={
        "resident_presence":"receipts/runtime-observability/resident-presence.latest.json"
    })
    assert snap2["resident"]["process_observed"] is True
    assert snap2["resident"]["current"] is True
    assert snap2["resident"]["identity"]["runtime_instance_id"]=="runtime-test-1"
    # Presence remains non-authorizing and does not promote unrelated runtime truths.
    assert snap2["runtime_truth"]["governed_request_consumption_proven"] is False
    assert snap2["runtime_truth"]["execution_or_state_transition_proven"] is False

    bound=obs.bind_lane(snap2,lane_id="site.personal-form-profile",predicates={
        "profile_write_consumed":"personal_form_profile_write",
        "profile_read_observed":"personal_form_profile_read"
    })
    assert set(bound["missing_evidence_predicates"])=={"profile_write_consumed","profile_read_observed"}
    assert bound["authority_effect"]=="NONE_OBSERVATION_ONLY"

print("HB_RUNTIME_OBSERVABILITY_PASS")
