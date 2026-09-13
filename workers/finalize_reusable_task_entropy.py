#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
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
    entropy = lifecycle.build_entropy_recovery(
        manifest=lifecycle.load_json(Path(args.manifest)),
        runner_expiry=lifecycle.load_json(Path(args.runner_expiry)),
        residual_recording=lifecycle.load_json(Path(args.residual_recording)),
        custody_request=lifecycle.load_json(Path(args.custody_request)),
        custody_record=lifecycle.load_json(Path(args.custody_record)),
    )
    write(Path(args.output), entropy)
    print(json.dumps(entropy, sort_keys=True))


if __name__ == "__main__":
    main()
