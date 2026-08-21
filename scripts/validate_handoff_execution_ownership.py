#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "control" / "handoff-execution-ownership-policy.json"
REQUIRED_SECTION = "## Execution ownership and collision partition"
REQUIRED_BUCKETS = (
    "MANUAL / SESSION-STARTABLE",
    "WORKER-OWNED / DO NOT COMPETE",
    "ESCALATED / AUTHORITY-OWNED",
    "COMPLETED / SUPERSEDED",
)


def main() -> int:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    assert policy["schema"] == "stegverse.handoff-execution-ownership/v1"
    assert policy["legacy_handoff_default"]["manual_execution_allowed"] is False
    assert policy["legacy_handoff_default"]["when_required_section_absent"] == "RECONCILIATION_REQUIRED"
    assert policy["github_token_production_authority"] == "NONE"
    assert policy["credential_authority"] == "TV/TVC"

    paths = sorted(ROOT.glob("docs/**/*_MIRROR_HANDOFF.md"))
    if not paths:
        raise SystemExit("no mirror handoffs discovered")

    failures: list[str] = []
    legacy_reconciliation: list[str] = []
    explicit_partitions = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if REQUIRED_SECTION not in text:
            # The policy explicitly defines this legacy case as fail-closed
            # RECONCILIATION_REQUIRED with manual execution prohibited. Missing
            # prose metadata therefore cannot grant execution authority and must
            # not stop unrelated control-plane validation from progressing.
            legacy_reconciliation.append(str(path.relative_to(ROOT)))
            continue

        explicit_partitions += 1
        section = text.split(REQUIRED_SECTION, 1)[1]
        for bucket in REQUIRED_BUCKETS:
            if bucket not in section:
                failures.append(f"{path.relative_to(ROOT)}: missing bucket {bucket}")
        if "manual_execution_allowed:" not in section:
            failures.append(f"{path.relative_to(ROOT)}: no explicit manual_execution_allowed field")
        if "worker_registry_ref:" not in section:
            failures.append(f"{path.relative_to(ROOT)}: no worker_registry_ref field")
        if "collision_scope:" not in section:
            failures.append(f"{path.relative_to(ROOT)}: no collision_scope field")
        if "release_condition:" not in section:
            failures.append(f"{path.relative_to(ROOT)}: no release_condition field")
        if "next_executable_action:" not in section:
            failures.append(f"{path.relative_to(ROOT)}: no next_executable_action field")

    if failures:
        for failure in failures:
            print("FAIL", failure)
        raise SystemExit(1)

    for path in legacy_reconciliation:
        print(
            "RECONCILIATION_REQUIRED",
            path,
            "manual_execution_allowed=false",
            "authority_effect=NONE",
        )

    print(
        "HANDOFF_EXECUTION_OWNERSHIP_PASS",
        f"handoffs={len(paths)}",
        f"explicit_partitions={explicit_partitions}",
        f"legacy_reconciliation_required={len(legacy_reconciliation)}",
        "legacy_manual_execution_allowed=false",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
