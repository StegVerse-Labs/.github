#!/usr/bin/env python3
"""Idempotently project the Reusable Task Component Model into README.md.

This source utility changes documentation only. It grants no runtime or task authority.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "### Reusable task ephemeral constructs and entropy recovery"
HEADING = "## Reusable Task Component Model"
SECTION = """## Reusable Task Component Model

StegVerse Goal Tasks declare required capabilities and consume reusable task components instead of embedding long task-specific orchestration chains. The canonical model is `data/reusable-task-component-model.json`, the decomposition policy is `data/reusable-task-component-decomposition-policy.json`, and deterministic evaluation is performed by `scripts/evaluate_reusable_task_componentization.py`.

The decomposition process is evaluated at Goal Task creation and as scope grows. Repeated subflows, repeated round trips, multiple authority crossings, cross-repository spread, duplicated generic adapter work, growing handoff sequences, branching remediation, independently reusable sub-processes, optional subflows, and independently provable evidence are explicit signals. When the canonical thresholds are reached, existing reusable components are searched first and decomposition occurs before additional task-specific orchestration is added.

Componentization preserves Goal Task identity, COSV continuity, evidence predicates, and existing authority ownership. Components are capabilities rather than new Goal Tasks by default, and omitted optional components are not forced into unrelated work.

Transport is the first materialized component family under this model and is defined by `data/reusable-transport-component-contract.json`. The complete manifest -> governed processing -> governed round trip(s) -> evidence/custody/reconstruction -> Publisher -> SDK return -> StegVerse egress -> Interlock/InTr -> far-side transition sequence is the maximal transport composition, not a universal pipeline.

Scoped documentation:

```text
docs/REUSABLE_TASK_COMPONENT_MODEL_MIRROR_HANDOFF.md
docs/REUSABLE_GOAL_TASK_TRANSPORT_COMPONENTS_MIRROR_HANDOFF.md
```

"""


def project(text: str) -> str:
    if HEADING in text:
        return text
    if MARKER not in text:
        raise ValueError(f"README projection marker missing: {MARKER}")
    return text.replace(MARKER, SECTION + MARKER, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="README.md")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(args.path)
    original = path.read_text(encoding="utf-8")
    projected = project(original)
    if args.check:
        return 0 if original == projected else 1
    path.write_text(projected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
