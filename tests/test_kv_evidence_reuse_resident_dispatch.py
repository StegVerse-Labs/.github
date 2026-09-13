from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = ROOT / "scripts/dispatch_resident_execution_requests.py"
CONSUMER = ROOT / "control/resident-execution-request.d/consume-kv-evidence-reconcile.py"
EVALUATOR = ROOT / "scripts/evaluate_indexed_event_reuse.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dispatcher_registers_machine_owned_evidence_reconciler():
    dispatcher = load(DISPATCHER, "resident_dispatch_kv_evidence")
    assert (
        "kv_bound_ephemeral_evidence_reconcile",
        "control/resident-execution-request.d/consume-kv-evidence-reconcile.py",
    ) in dispatcher.CONSUMERS
    selected = dispatcher.select_consumers(("kv_bound_ephemeral_evidence_reconcile",))
    assert selected == (("kv_bound_ephemeral_evidence_reconcile", "control/resident-execution-request.d/consume-kv-evidence-reconcile.py"),)


def test_consumer_uses_runtime_input_without_user_interaction(tmp_path: Path):
    runtime = tmp_path / "runtime"
    source = tmp_path / "source"
    (runtime / "scripts").mkdir(parents=True)
    (runtime / "control/resident-execution-request.d").mkdir(parents=True)
    (runtime / "runtime-state/kv-bound-ephemeral-browser-projection").mkdir(parents=True)
    (source / "scripts").mkdir(parents=True)
    (source / "scripts/evaluate_indexed_event_reuse.py").write_text(EVALUATOR.read_text(encoding="utf-8"), encoding="utf-8")
    payload = {
        "node_context": {"connectivity_state": "ESTABLISHED"},
        "current_requirements": {"required_predicates": ["CURRENT_IPHONE_RUNTIME_AUTHENTIC", "TVC_NATIVE_BUILD_UPLOAD_OBSERVED"]},
        "indexed_event": {
            "event_ref": "indexed:test",
            "replay_state": "PASS",
            "reconstruction_state": "PASS",
            "observed_predicates": ["CURRENT_IPHONE_RUNTIME_AUTHENTIC"],
        },
    }
    input_path = runtime / "runtime-state/kv-bound-ephemeral-browser-projection/indexed-evidence-reuse-input.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    consumer = load(CONSUMER, "kv_evidence_consumer")
    result = consumer.consume(source, runtime)
    assert result["state"] == "DELTA_REQUIRED"
    assert result["missing_delta"] == ["TVC_NATIVE_BUILD_UPLOAD_OBSERVED"]
    assert result["user_interaction_required"] is False
    assert result["request_granted_authority"] is False
    assert result["second_machine_required"] is False


def test_missing_node_connectivity_waits_without_user_step(tmp_path: Path):
    runtime = tmp_path / "runtime"
    source = tmp_path / "source"
    (runtime / "runtime-state/kv-bound-ephemeral-browser-projection").mkdir(parents=True)
    (source / "scripts").mkdir(parents=True)
    (source / "scripts/evaluate_indexed_event_reuse.py").write_text(EVALUATOR.read_text(encoding="utf-8"), encoding="utf-8")
    consumer = load(CONSUMER, "kv_evidence_consumer_wait")
    result = consumer.consume(source, runtime)
    assert result["state"] == "WAITING_FOR_ESTABLISHED_NODE_CONNECTIVITY"
    assert result["user_interaction_required"] is False
