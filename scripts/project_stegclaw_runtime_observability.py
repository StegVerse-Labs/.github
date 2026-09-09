#!/usr/bin/env python3
"""Project StegClaw P4 through the canonical shared resident-presence projector."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.runtime_presence_projection import project  # noqa: E402

PROFILE_REL = Path("control/runtime-observability-consumers/data-continuation-stegclaw-p4.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Project StegClaw P4 through the canonical shared runtime-presence contract.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()

    source = args.source_root.expanduser().resolve()
    profile_path = source / PROFILE_REL
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    result = project(args.runtime_root.expanduser().resolve(), profile["evidence_bindings"])
    output = {
        "schema": "stegverse.stegclaw.p4-runtime-observability/v1",
        "state": result.get("state", "OBSERVATION_PROJECTED") if isinstance(result, dict) else "OBSERVATION_PROJECTED",
        "consumer_id": profile["consumer_id"],
        "consumer_repository": profile["consumer_repository"],
        "shared_contract": profile["shared_contract"],
        "runtime_projection": result,
        "predicate_bindings": profile["predicates"],
        "external_predicates": profile.get("downstream_external_predicates", []),
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
