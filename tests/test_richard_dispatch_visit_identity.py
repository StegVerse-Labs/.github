"""The Richard dispatch visit's transition id keys on the request, not a clock.

`retain_richard_dispatch_visit_in_master_records` names its transition
`task_id:RESIDENT_REQUEST_DISPATCH_VISIT:request_id:request_sha256`. The same
request yields the same id; a different request yields a different one. The
custody writer is replaced by a capture, so nothing is appended anywhere.
"""
import hashlib
import json
import sys
import time
import types

from scripts import dispatch_resident_execution_requests as dispatch

ROOT = dispatch.ROOT
ROW = {"consumer": dispatch.RICHARD_SELECTOR, "consumer_ref": "scripts/consumer.py", "attempted": True,
       "state": "ATTEMPT_RECORDED", "returncode": 0, "result": {"first_failed_cycle": None}}


def sha256_uri(value):
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _runtime(tmp_path, name, request):
    runtime = tmp_path / name
    path = runtime / dispatch.RICHARD_REQUEST_REL
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(request))
    return runtime


def _capture(monkeypatch):
    built = []
    fake = types.ModuleType("canonical_state_transition_custody")
    fake.sha256_uri = sha256_uri
    fake.build_state_receipt = lambda **kwargs: built.append(kwargs) or dict(kwargs)
    fake.submit_state_receipt = lambda receipt: {"state": "RECORDED"}
    fake.organization_receipt_gate = lambda result, **kwargs: {"verified": True, "refusal": None}
    monkeypatch.setitem(sys.modules, "canonical_state_transition_custody", fake)
    return built


def _clock_forbidden(*args, **kwargs):
    raise AssertionError("the visit identity must not read a clock")


def test_the_visit_transition_id_is_deterministic_for_the_same_request(tmp_path, monkeypatch):
    request = json.loads((ROOT / dispatch.RICHARD_REQUEST_REL).read_text(encoding="utf-8"))
    runtime = _runtime(tmp_path, "runtime", request)
    built = _capture(monkeypatch)
    monkeypatch.setattr(time, "time_ns", _clock_forbidden)
    first = dispatch.retain_richard_dispatch_visit_in_master_records(ROOT, runtime, [ROW])
    second = dispatch.retain_richard_dispatch_visit_in_master_records(ROOT, runtime, [ROW])
    assert first["state"] == second["state"] == "RECORDED"
    assert first["transition_id"] == second["transition_id"]
    assert first["transition_id"] == (f"{request['task_id']}:RESIDENT_REQUEST_DISPATCH_VISIT:"
                                      f"{request['request_id']}:{sha256_uri(request)}")
    assert built[0]["transition_id"] == built[1]["transition_id"] == first["transition_id"]


def test_a_different_request_has_a_different_visit_transition_id(tmp_path, monkeypatch):
    request = json.loads((ROOT / dispatch.RICHARD_REQUEST_REL).read_text(encoding="utf-8"))
    changed = {**request, "revision_note": "a different request body"}
    _capture(monkeypatch)
    first = dispatch.retain_richard_dispatch_visit_in_master_records(
        ROOT, _runtime(tmp_path, "a", request), [ROW])
    second = dispatch.retain_richard_dispatch_visit_in_master_records(
        ROOT, _runtime(tmp_path, "b", changed), [ROW])
    assert first["transition_id"] != second["transition_id"]
