from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_mir_process_adapter_uses_transition_probe_wrapper():
    value = json.loads((ROOT / "control/process-worker-adapters.d/mir-roundtrip-egress-authenticity-001.json").read_text(encoding="utf-8"))
    adapter = value["adapters"][0]
    assert adapter["command"] == ["python", "workers/mir_roundtrip_transition_probe_worker.py"]
    assert adapter["enabled"] is True


def test_probe_preserves_existing_worker_and_authorities():
    source = (ROOT / "workers/mir_roundtrip_transition_probe_worker.py").read_text(encoding="utf-8")
    for needle in (
        "from workers import mir_roundtrip_egress_authenticity_worker as base",
        "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
        "MIR_EVENT_INGRESS_INTENT_BOUND",
        "CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED",
        "RTC-STEGVERSE-EGRESS-007",
        "RTC-INTERLOCK-INTR-TRANSPORT-008",
        "RTC-FARSIDE-FINAL-009",
        "EXACT_GOVERNED_RETURN_PACKET_RETAINED",
        "first_non_return_transition_id",
        "master_records_may_grant_transition_authority",
    ):
        assert needle in source


def test_probe_does_not_add_runtime_or_dispatch_plane():
    source = (ROOT / "workers/mir_roundtrip_transition_probe_worker.py").read_text(encoding="utf-8")
    assert "subprocess.Popen" not in source
    assert "Thread(" not in source
    assert "schedule" not in source.lower()
    assert "github actions" not in source.lower()
