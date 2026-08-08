#!/usr/bin/env python3
"""Compatibility diagnostic for organization heartbeat assertions.

This script no longer increments the heartbeat epoch. Epoch ownership belongs
only to heartbeat_runtime.HeartBeatRuntime.cycle(). Use --dry-run to inspect
which claim assertions the current epoch would carry.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.org_assertions import issue_claim_assertions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()
    heartbeat = json.loads((ROOT / "control" / "heartbeat-state.json").read_text(encoding="utf-8"))
    epoch = int(heartbeat.get("epoch", 0))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    issued = issue_claim_assertions(ROOT, epoch, now, write=False)
    print(json.dumps({
        "schema": "stegverse.org-heartbeat-assertion-diagnostic/v1",
        "epoch": epoch,
        "issued": issued,
        "epoch_advanced": False,
        "authority_effect": "none"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
