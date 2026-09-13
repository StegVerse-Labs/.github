#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import reusable_task_lifecycle as lifecycle

def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--runner-expiry", required=True)
    parser.add_argument("--residual-recording", required=True)
    parser.add_argument("--custody-request", required=True)
    parser.add_argument("--custody-record", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest = lifecycle.load_json(Path(args.manifest))
    expiry = lifecycle.load_json(Path(args.runner_expiry))
    residual = lifecycle.load_json(Path(args.residual_recording))
    request = lifecycle.load_json(Path(args.custody_request))
    record = lifecycle.load_json(Path(args.custody_record))
    entropy = lifecycle.build_entropy_recovery(manifest=manifest, runner_expiry=expiry, residual_recording=residual, custody_request=request, custody_record=record)
    write(Path(args.output), entropy)
    print(json.dumps(entropy, sort_keys=True))

if __name__ == "__main__":
    main()
