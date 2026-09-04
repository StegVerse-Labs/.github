#!/usr/bin/env python3
"""Normalize GitHub failure/problem email observations into canonical incident proposals.

Input rows are explicit email-monitor observations. This utility clusters noisy
messages by normalized repository/workflow/error signature and emits incident
proposals only. It does not mark work failed, create execution authority, or
admit a task transition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        result = value
    elif isinstance(value, dict) and isinstance(value.get("messages"), list):
        result = value["messages"]
    elif isinstance(value, dict) and isinstance(value.get("events"), list):
        result = value["events"]
    else:
        raise SystemExit("FAIL_CLOSED: input must be list or object with messages/events")
    if not all(isinstance(item, dict) for item in result):
        raise SystemExit("FAIL_CLOSED: every input row must be an object")
    return result


def norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\b[0-9a-f]{7,64}\b", "<sha>", text)
    text = re.sub(r"\b\d{5,}\b", "<id>", text)
    text = re.sub(r"\s+", " ", text)
    return text


def signature(row: dict[str, Any]) -> tuple[str, str, str]:
    repo = norm(row.get("repository") or row.get("repo") or row.get("repository_full_name"))
    workflow = norm(row.get("workflow") or row.get("workflow_name") or row.get("subject"))
    error = norm(row.get("error_signature") or row.get("error") or row.get("failure") or row.get("snippet") or row.get("subject"))
    return repo or "unknown-repo", workflow or "unknown-workflow", error or "unknown-error"


def incident_id(parts: tuple[str, str, str]) -> str:
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:24]
    return "INC-GITHUB-" + digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for source in args.inputs:
        for row in rows(load(Path(source))):
            groups.setdefault(signature(row), []).append({**row, "source_file": source})

    incidents = []
    for sig, observations in sorted(groups.items()):
        refs = sorted({str(r.get("message_id") or r.get("id") or r.get("thread_id") or r.get("source_file")) for r in observations})
        incidents.append({
            "incident_id": incident_id(sig),
            "kind": "GITHUB_FAILURE_EMAIL_CLUSTER",
            "normalized_repository": sig[0],
            "normalized_workflow": sig[1],
            "normalized_error_signature": sig[2],
            "observation_count": len(observations),
            "observation_refs": refs,
            "state": "INCIDENT_PROPOSED_NOT_ADMITTED",
            "task_ingress_required": True,
            "email_observation_is_execution_evidence": False,
            "incident_proposal_mints_execution_authority": False,
        })

    result = {
        "schema": "stegverse.github-failure-email-incident-proposals/v1",
        "incident_count": len(incidents),
        "incidents": incidents,
        "authority_effect": "NONE_PROPOSAL_ONLY",
        "nonclaims": [
            "EMAIL_COUNT_IS_NOT_FAILURE_COUNT",
            "EMAIL_OBSERVATION_DOES_NOT_PROVE_RUNTIME_FAILURE",
            "INCIDENT_PROPOSAL_REQUIRES_CANONICAL_TASK_INGRESS_BEFORE_WORK",
        ],
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
