"""`stegverse-labs.remediation`: StegHealer classifies a remediation lane that crossed in over InTr.

The lane's route is calculated by the SDK (StegVerse-SDK stegverse/remediation_fork.py)
from where remediation was recognized, the manifested path and the direct route to
StegHealer; every organization crossing is InTr egress then InTr ingress, ending at
this service. The classifier is StegVerse-Healer's, loaded only from the checkout of
the commit org-runtime/remediation-classifier.json pins. Classification grants
nothing. Temporary repositories only; nothing is fetched.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


endpoint = _load("remediation_endpoint_under_test", "resident-runtime/remediation_endpoint.py")


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _route():
    route = {"schema": "stegverse.remediation-route/v1",
             "entry_organization": "StegVerse-org",
             "direct_route_to_steghealer": [
                 {"from": "SDK", "to": "StegVerse-org", "crossing": "INTERLOCK_INTR_INGRESS"},
                 {"from": "StegVerse-org", "to": "StegVerse-Labs", "crossing": "INTERLOCK_INTR_EGRESS"},
                 {"from": "StegVerse-org", "to": "StegVerse-Labs", "crossing": "INTERLOCK_INTR_INGRESS"},
                 {"from": "StegVerse-Labs", "to": "stegverse-labs.remediation", "crossing": "INTERNAL_ENDPOINT"}],
             "route_sha256": "r" * 64}
    return route


def _packet(request=None, **body_overrides):
    request = request or {"remediation_route": _route(),
                          "non_allow": {"disposition": "DENY", "failed_predicate": "P"},
                          "original_request": {"request_sha256": "a" * 64}}
    body = {"schema": endpoint.REQUEST_SCHEMA, "sdk_request_sha256": "b" * 64,
            "remediation_request": request,
            "remediation_request_sha256": hashlib.sha256(_canon(request)).hexdigest(),
            "remediation_route_sha256": request["remediation_route"]["route_sha256"]}
    body.update(body_overrides)
    return {"packet_id": "pkt-remediation-test", "origin": {"org": "StegVerse-org"},
            "destination": {"org": "StegVerse-Labs", "service": endpoint.SERVICE_ID},
            "payload": {"body": body}}


def _healer(action="RESUBMIT", granted=False):
    def classify(non_allow, original_request):
        return {"schema": "stegverse.healer.sdk-deny-classification/v1", "state": "DETECTED",
                "suggested_action": action, "execution_authority_granted": granted,
                "original_request_sha256": original_request["request_sha256"]}
    return lambda: (classify, None)


def test_a_lane_that_crossed_in_over_intr_is_classified_and_grants_nothing():
    out = endpoint.classify(_packet(), loader=_healer())
    assert out["disposition"] == "ALLOW"
    assert out["state"] == "REMEDIATION_CLASSIFIED"
    assert out["suggested_action"] == "RESUBMIT"
    assert out["classification_grants_authority"] is False
    assert out["governance_disposition"] == "NOT_EVALUATED"
    assert out["classifier_repository"] == "StegVerse-Labs/StegVerse-Healer"


@pytest.mark.parametrize("mutate, reason", [
    (lambda p: p["payload"]["body"].update(schema="other"), "REMEDIATION_REQUEST_SCHEMA_NOT_RECEIVED:other"),
    (lambda p: p["payload"]["body"].update(remediation_request_sha256="0" * 64), "REMEDIATION_REQUEST_DIGEST_MISMATCH"),
    (lambda p: p["payload"]["body"].update(remediation_route_sha256="x"), "REMEDIATION_ROUTE_DIGEST_MISMATCH"),
])
def test_an_unbound_lane_is_recorded_fail_closed(mutate, reason):
    packet = _packet()
    mutate(packet)
    out = endpoint.classify(packet, loader=_healer())
    assert (out["disposition"], out["reason"], out["classification"]) == ("FAIL_CLOSED", reason, None)


def test_a_route_that_bypasses_intr_or_ends_elsewhere_is_refused():
    bypass = _route()
    bypass["direct_route_to_steghealer"] = [h for h in bypass["direct_route_to_steghealer"]
                                            if h["crossing"] != "INTERLOCK_INTR_INGRESS" or h["from"] == "SDK"]
    out = endpoint.classify(_packet({"remediation_route": bypass, "non_allow": {}, "original_request": {}}),
                            loader=_healer())
    assert out["reason"] == "REMEDIATION_ROUTE_CROSSING_FROM_ORIGIN_IS_NOT_INTERLOCK_INTR"
    elsewhere = _route()
    elsewhere["direct_route_to_steghealer"][-1]["to"] = "stegverse-labs.other"
    out = endpoint.classify(_packet({"remediation_route": elsewhere, "non_allow": {}, "original_request": {}}),
                            loader=_healer())
    assert out["reason"] == "REMEDIATION_ROUTE_DOES_NOT_END_AT_THIS_SERVICE"


def test_without_the_pinned_classifier_nothing_is_guessed():
    out = endpoint.classify(_packet(), loader=lambda: (None, "REMEDIATION_CLASSIFIER_NOT_MATERIALIZED"))
    assert (out["disposition"], out["reason"]) == ("FAIL_CLOSED", "REMEDIATION_CLASSIFIER_NOT_MATERIALIZED")


def test_a_classification_claiming_authority_is_refused():
    out = endpoint.classify(_packet(), loader=_healer(granted=True))
    assert (out["disposition"], out["reason"]) == ("FAIL_CLOSED", "REMEDIATION_CLASSIFICATION_AUTHORITY_ESCALATION")


def test_the_classifier_loads_only_from_the_pinned_commit(tmp_path):
    checkout = tmp_path / ".stegverse/remediation-classifier/StegVerse-Healer"
    (checkout / "app").mkdir(parents=True)
    (checkout / "app/manifest_remediation_intake.py").write_text(
        "def classify_sdk_deny(result, request):\n    return {'execution_authority_granted': False}\n")
    git = ["git", "-C", str(checkout)]
    subprocess.run(git[:1] + ["init", "-q", str(checkout)], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c"], check=True)
    head = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    pin = {**endpoint.classifier_pin(), "commit": head}
    classify, refusal = endpoint.load_classifier(pin, root=tmp_path)
    assert refusal is None and classify({}, {}) == {"execution_authority_granted": False}
    _, refusal = endpoint.load_classifier({**pin, "commit": "f" * 40}, root=tmp_path)
    assert refusal == "REMEDIATION_CLASSIFIER_NOT_AT_PINNED_COMMIT"
    _, refusal = endpoint.load_classifier(pin, root=tmp_path / "absent")
    assert refusal == "REMEDIATION_CLASSIFIER_NOT_MATERIALIZED"


def test_the_pin_is_anonymous_and_the_registry_serves_remediation_once():
    pin = endpoint.classifier_pin()
    assert pin["repository"] == "StegVerse-Labs/StegVerse-Healer"
    assert len(pin["commit"]) == 40
    assert pin["read_credential"]["fetch"] == "ANONYMOUS_PINNED_COMMIT"
    assert pin["classification_grants_authority"] is False
    registry = json.loads((ROOT / "org-boundary/registry/services.json").read_text())
    served = [s["service_id"] for s in registry["services"]
              if {"capability": "remediation", "route_id": "stegverse.route.governed-remediation.v1"}
              in (s.get("admits_processing") or [])]
    assert served == ["stegverse-labs.remediation"]
