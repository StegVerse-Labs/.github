from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "control/process-worker-adapters.d/gadi-resident-execution-001.json"
WORKER_BRIDGE = ROOT / "workers/gadi_resident_execution_worker.py"
DISPATCHER = ROOT / "scripts/dispatch_gadi_resident_execution.py"
PREFLIGHT = ROOT / "scripts/preflight_gadi_resident_execution.py"
RAW_CONSUMER = ROOT / "control/resident-execution-request.d/consume-gadi-resident-execution.py"


def test_worker_adapter_routes_through_worker_bridge_then_preflight_gated_dispatcher():
    payload = json.loads(ADAPTER.read_text(encoding="utf-8"))
    adapter = payload["adapters"][0]
    command = adapter["command"]
    assert adapter["enabled"] is True
    assert adapter["adapter_ref"] == "process:gadi-resident-execution-v2-preflight-gated"
    assert command == ["python", "workers/gadi_resident_execution_worker.py"]
    assert "consume-gadi-resident-execution.py" not in " ".join(command)
    worker_text = WORKER_BRIDGE.read_text(encoding="utf-8")
    assert "from scripts.dispatch_gadi_resident_execution import dispatch" in worker_text
    assert "current_worker_claim=task" in worker_text
    assert WORKER_BRIDGE.is_file()
    assert DISPATCHER.is_file()
    assert PREFLIGHT.is_file()
    assert RAW_CONSUMER.is_file()


def test_dispatcher_preserves_zero_blocker_gate_before_raw_consumer():
    text = DISPATCHER.read_text(encoding="utf-8")
    preflight_pos = text.index("preflight_gadi_resident_execution.py")
    consumer_pos = text.index("consume-gadi-resident-execution.py")
    assert preflight_pos < consumer_pos
    assert '"READY_FOR_RESIDENT_CONSUMPTION"' in text
    assert 'pre_result.get("blocker_count") != 0' in text
    assert '"consumer_attempted":False' in text
