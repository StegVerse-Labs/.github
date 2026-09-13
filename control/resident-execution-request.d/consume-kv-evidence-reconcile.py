from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "runtime-state/kv-bound-ephemeral-browser-projection/indexed-evidence-reuse-input.json"
OUTPUT = ROOT / "receipts/sovereign-host/kv-bound-ephemeral-browser-projection-evidence-reuse.latest.json"
EVALUATOR = ROOT / "scripts/evaluate_indexed_event_reuse.py"


def main():
    spec = importlib.util.spec_from_file_location("indexed_evidence_reuse", EVALUATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = json.loads(INPUT.read_text(encoding="utf-8")) if INPUT.exists() else {"node_context": {}}
    result = module.evaluate(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
