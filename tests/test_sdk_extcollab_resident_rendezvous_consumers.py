import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/consume_resident_rendezvous.py"
RESEAL_REQUEST = ROOT / "control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json"
LISTENER_REQUEST = ROOT / "control/resident-execution-request.d/sdk-workspace-external-collab-consent-listener-001.json"


def load_module():
    spec = importlib.util.spec_from_file_location("resident_rendezvous", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_external_collab_consumers_are_exact_registered_profiles():
    module = load_module()
    assert module.RESEAL_CONSUMER in module.CONSUMER_PROFILES
    assert module.LISTENER_CONSUMER in module.CONSUMER_PROFILES

    reseal = json.loads(RESEAL_REQUEST.read_text(encoding="utf-8"))
    listener = json.loads(LISTENER_REQUEST.read_text(encoding="utf-8"))
    assert module.validate_resident_request(reseal, consumer=module.RESEAL_CONSUMER) == reseal
    assert module.validate_resident_request(listener, consumer=module.LISTENER_CONSUMER) == listener

    reseal_bad = dict(reseal)
    reseal_bad["request_granted_authority"] = True
    try:
        module.validate_resident_request(reseal_bad, consumer=module.RESEAL_CONSUMER)
    except module.ResidentRendezvousConsumerError:
        pass
    else:
        raise AssertionError("mutated reseal request must fail closed")

    listener_bad = dict(listener)
    listener_bad["provider_contact_allowed"] = True
    try:
        module.validate_resident_request(listener_bad, consumer=module.LISTENER_CONSUMER)
    except module.ResidentRendezvousConsumerError:
        pass
    else:
        raise AssertionError("mutated listener request must fail closed")


def test_external_collab_outcome_mapping_preserves_existing_consumer_terminals():
    module = load_module()
    assert module._consumer_outcome(module.RESEAL_CONSUMER, {"state": "COMPLETED"}) == ("COMPLETED", True)
    assert module._consumer_outcome(module.RESEAL_CONSUMER, {"state": "TARGET_ALREADY_PRESENT"}) == ("COMPLETED", True)
    assert module._consumer_outcome(module.RESEAL_CONSUMER, {"state": "BLOCKED"}) == ("BLOCKED", False)
    assert module._consumer_outcome(module.LISTENER_CONSUMER, {"state": "SERVICE_ALREADY_HEALTHY"}) == ("COMPLETED", True)
    assert module._consumer_outcome(module.LISTENER_CONSUMER, {"state": "COMPLETED"}) == ("COMPLETED", True)
    assert module._consumer_outcome(module.LISTENER_CONSUMER, {"state": "BLOCKED"}) == ("BLOCKED", False)


def test_listener_nonsecret_environment_survives_transport_sanitization():
    module = load_module()
    env = module.safe_env({
        "PATH": "/usr/bin",
        "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID": "client-id",
        "STEGVERSE_OWNER_BINDING_DIGEST": "sha256:" + "a" * 64,
        "STEGVERSE_STEGFIN_SOURCE_ROOT": "/srv/stegfin",
        "STEGVERSE_TVC_ROOT": "/srv/tvc",
    })
    assert env["STEGVERSE_GOOGLE_DRIVE_CLIENT_ID"] == "client-id"
    assert env["STEGVERSE_OWNER_BINDING_DIGEST"].startswith("sha256:")
    assert env["STEGVERSE_STEGFIN_SOURCE_ROOT"] == "/srv/stegfin"
    assert env["STEGVERSE_TVC_ROOT"] == "/srv/tvc"
    assert env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] == "TV/TVC"
