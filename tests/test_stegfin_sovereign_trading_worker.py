from __future__ import annotations

import io
import json
import os
import runpy
import sys
from pathlib import Path


WORKER = Path("workers/stegfin_sovereign_trading_worker.py")
TASK_ID = "SHWP-STEGFIN-SOVEREIGN-TRADING-001"


def invocation() -> dict:
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 101,
        "task": {
            "task_id": TASK_ID,
            "claim_id": "claim-stegfin-1",
            "worker_id": "stegfin-sovereign-trading-worker",
            "worker_instance_id": "worker-HB101-G1",
            "heartbeat_timing": {"fencing_token": 1},
        },
        "handoff": {
            "execution": {
                "required_capabilities": [
                    "runtime_observation",
                    "bounded_process_execution",
                    "durable_state_reconstruction",
                ],
                "allowed_paths": ["receipts/stegfin-sovereign-trading/**"],
            }
        },
    }


def test_hosted_github_runner_is_rejected_as_production_worker(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(invocation())))
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    try:
        runpy.run_path(str(Path(__file__).resolve().parents[1] / WORKER), run_name="__main__")
    except SystemExit as exc:
        assert exc.code == 0
    response = json.loads(out.getvalue())
    assert response["state"] == "BLOCKED"
    assert response["transition_id"] == "STEGFIN_SOVEREIGN_WORKER_WAITING_FOR_STEGVERSE_CARRIER"


def test_handoff_has_no_wallet_or_custody_authority():
    handoff = json.loads(Path("handoffs/SHWP-STEGFIN-SOVEREIGN-TRADING-001.json").read_text())
    ceiling = set(handoff["goal"]["authority_ceiling"])
    assert "no_wallet_signing_authority" in ceiling
    assert "no_transaction_broadcast_authority" in ceiling
    assert "no_custody_authority" in ceiling
    assert "no_scale_up_authority" in ceiling
    assert handoff["block"]["third_party_blocker"] is False
    assert handoff["block"]["human_action_required"] is False
