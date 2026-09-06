#!/usr/bin/env python3
"""Render a portable, non-authorizing coordination projection for session handoffs."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from heartbeat_runtime.coordination_ledger import LEDGER_SCHEMA, load_composed_coordination_ledger


def render(ledger: dict[str, Any]) -> str:
    if ledger.get("schema") != LEDGER_SCHEMA:
        raise ValueError("unsupported coordination ledger schema")
    predicates = {p.get("predicate_id"): p for p in ledger.get("predicates", []) if p.get("predicate_id")}
    active_claims = [c for c in ledger.get("claims", []) if c.get("state") == "ACTIVE"]
    composition = ledger.get("composition") if isinstance(ledger.get("composition"), dict) else {}
    lines = [
        "## Canonical cross-task coordination projection",
        "",
        "> Projection only. Runtime truth remains with each authoritative producer; this section grants no execution, claim, fence, lease, credential, route, transition, custody, publication, or runtime-event authority.",
        "",
        f"Source: `StegVerse-Labs/.github/control/cross-task-coordination.json` + canonical fragments ({ledger.get('schema')})",
        f"Fragments: {', '.join(composition.get('fragment_ids', [])) if composition.get('fragment_ids') else 'none'}",
        "",
        "### Tasks",
        "",
    ]
    for task in sorted(ledger.get("tasks", []), key=lambda x: str(x.get("task_id", ""))):
        required = task.get("required_predicates", [])
        states = [f"{pid}={predicates.get(pid, {}).get('state', 'UNKNOWN')}" for pid in required]
        lines.append(f"- `{task.get('task_id')}` — state `{task.get('state', 'UNKNOWN')}`; predicates: {', '.join(states) if states else 'none'}")
    lines.extend(["", "### Active claims", ""])
    if active_claims:
        for claim in sorted(active_claims, key=lambda x: str(x.get("claim_id", ""))):
            lines.append(f"- `{claim.get('claim_id')}` owns coordination scope for `{claim.get('task_id')}`; do not duplicate that scope.")
    else:
        lines.append("- none")
    lines.extend(["", "### Evidence gaps", ""])
    gaps = ledger.get("gaps", [])
    if gaps:
        for gap in gaps:
            binding = gap.get("subject_binding") if isinstance(gap.get("subject_binding"), dict) else {}
            subject = f"; subject `{binding}`" if binding else ""
            lines.append(f"- `{gap.get('predicate_id')}`{subject}: {gap.get('missing_observation') or 'exact evidence delta recorded'}; producer `{gap.get('required_producer')}`; action: {gap.get('action_without_collision')}")
    else:
        lines.append("- none")
    lines.extend(["", "Before declaring a blocker, resolve adjacent satisfied predicates, active producers/claims, exact subject bindings, and evidence gaps from the composed canonical ledger.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--fragments-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    ledger = load_composed_coordination_ledger(args.ledger, args.fragments_dir)
    text = render(ledger)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
