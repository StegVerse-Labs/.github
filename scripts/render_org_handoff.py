#!/usr/bin/env python3
"""Render the machine-state section of the Organization HANDOFF deterministically."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "control" / "org-state.json"
CLAIMS = ROOT / "control" / "claims-active.json"
QUEUE = ROOT / "control" / "queue.json"
OUTPUT = ROOT / "docs" / "ORG_CONTROL_PLANE_STATE.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    state, claims, queue = load(STATE), load(CLAIMS), load(QUEUE)
    ordered_task_ids = queue.get("ordered_task_ids", [])
    lines = [
        "# Organization Control Plane State",
        "",
        "> Generated from validated machine-readable state. Do not edit manually.",
        "",
        f"- Schema: `{state.get('schema')}`",
        f"- Organization generation: `{state.get('generation')}`",
        f"- Claim generation: `{claims.get('generation')}`",
        f"- Queue generation: `{queue.get('generation')}`",
        f"- Active claims: `{len(claims.get('claims', []))}`",
        f"- Queued tasks: `{len(ordered_task_ids)}`",
        "",
        "## Active Claims",
        "",
    ]
    if not claims.get("claims"):
        lines.append("No active claims.")
    else:
        lines.extend(["| Task | Repository | Mode | Token |", "|---|---|---|---:|"])
        for claim in sorted(claims["claims"], key=lambda value: (value["repository"]["full_name"], value["task_id"])):
            lines.append(f"| {claim['task_id']} | {claim['repository']['full_name']} | {claim['mode']} | {claim['fencing_token']} |")
    lines.extend(["", "## Queue", ""])
    if not ordered_task_ids:
        lines.append("No queued tasks.")
    else:
        lines.extend(["| Rank | Task |", "|---:|---|"])
        for index, task_id in enumerate(ordered_task_ids, 1):
            lines.append(f"| {index} | {task_id} |")
    rendered = "\n".join(lines).rstrip() + "\n"
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
