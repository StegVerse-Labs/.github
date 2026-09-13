from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_REL = Path("runtime-state/kv-bound-ephemeral-browser-projection/indexed-evidence-reuse-input.json")
OUTPUT_REL = Path("receipts/sovereign-host/kv-bound-ephemeral-browser-projection-evidence-reuse.latest.json")
EVALUATOR_REL = Path("scripts/evaluate_indexed_event_reuse.py")
BUILDER_REL = Path("scripts/build_kv_evidence_reuse_input.py")


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def consume(source_root: Path, runtime_root: Path):
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    evaluator_path = runtime / EVALUATOR_REL
    if not evaluator_path.is_file():
        evaluator_path = source / EVALUATOR_REL
    evaluator = _load_module(evaluator_path, "indexed_evidence_reuse")

    input_path = runtime / INPUT_REL
    if input_path.is_file():
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        input_source = "RUNTIME_PREMATERIALIZED"
    else:
        builder_path = runtime / BUILDER_REL
        if not builder_path.is_file():
            builder_path = source / BUILDER_REL
        builder = _load_module(builder_path, "kv_evidence_reuse_input")
        payload = builder.build_payload(source, runtime)
        input_source = "AUTOMATIC_CANONICAL_AND_RESIDENT_EVIDENCE"

    decision = dict(evaluator.evaluate(payload))
    decision_state = decision.get("state")
    result = dict(decision)
    result.setdefault("schema", "stegverse.indexed-evidence-reuse-decision/v1")
    result["reuse_decision_state"] = decision_state
    if decision_state == "FAIL_CLOSED":
        result["state"] = "EVIDENCE_REUSE_FAIL_CLOSED"
    result["task_id"] = "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001"
    result["input_source"] = input_source
    result["input_derived_automatically"] = input_source == "AUTOMATIC_CANONICAL_AND_RESIDENT_EVIDENCE"
    result["credential_authority"] = "TV/TVC"
    result["github_token_runtime_authority"] = "NONE"
    result["request_granted_authority"] = False
    result["second_machine_required"] = False
    result["user_interaction_required"] = False
    output = runtime / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile indexed evidence against current verification requirements.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") != "EVIDENCE_REUSE_FAIL_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
