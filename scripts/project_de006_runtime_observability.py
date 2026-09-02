#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.runtime_presence_projection import project  # noqa: E402

PROFILE = ROOT / "control/runtime-observability-consumers/decision-envelope-de006.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Project DE-006 through the canonical shared HB/runtime observability contract.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()

    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    result = project(args.runtime_root, profile["evidence_bindings"])
    output = {
        "schema": "stegverse.decision-envelope.de006-runtime-observability/v1",
        "consumer_id": profile["consumer_id"],
        "consumer_repository": profile["consumer_repository"],
        "shared_contract": profile["shared_contract"],
        "runtime_projection": result,
        "predicate_bindings": profile["predicates"],
        "external_predicates": profile["downstream_external_predicates"],
        "propagation_state": profile["propagation_state"],
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
