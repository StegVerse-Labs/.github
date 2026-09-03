# STEGINDEX_PREFLIGHT_MIRROR_HANDOFF.md

Status: ACTIVE
Updated: 2026-09-02
Organization: StegVerse-Labs
Repository: StegVerse-Labs/.github
Goal: STEGINDEX-MANDATORY-PREFLIGHT-CONSUMER

## Source of truth

StegIndex:
- repository: `StegVerse-Labs/StegIndex`
- handoff: `STEGINDEX_MIRROR_HANDOFF.md`
- purpose-aware preflight merge: `4d47439956341ea535e3e937d97c492b193daa51`

Organization consumer:
- `scripts/stegindex_preflight_gate.py`
- `management/stegindex-preflight-consumer-contract.json`

## Purpose

Bind organization/session/build entry logic to StegIndex resolution without turning StegIndex into an authority plane.

The adapter consumes an already-materialized StegIndex checkout and performs no network fetch. It invokes StegIndex's canonical `scripts/preflight.py`, verifies that the result remains resolution-only, and reduces the output to a bounded organization decision.

## Lawful decisions

- `CONTINUE_MACHINE_EXECUTION`
- `REUSE_OR_EXTEND_EXISTING`
- `NO_EXISTING_CAPABILITY_MATCH`
- `EXACT_BLOCKER_ONLY`

## Anti-stall invariant

If StegIndex returns `machine_continuation_required=true`, the organization adapter must return `CONTINUE_MACHINE_EXECUTION`.

A generic `runtime evidence missing` blocker is not permitted in that state.

If StegIndex is not locally materialized, the adapter does not fabricate a resolution and does not fetch it over the network. It emits the exact missing local dependency.

## Authority

This consumer grants NO:
- execution authority;
- admission authority;
- credential authority;
- routing authority;
- claim/fence authority;
- transition authority;
- publication authority;
- custody authority;
- consequence authority.

Actual execution remains owned by the canonical satisfier/worker/runtime identified by repository-local truth.

## Current continuation

source_adapter: IMPLEMENTED
StegIndex purpose-aware resolver: MERGED
organization preflight consumption: SOURCE_BOUND
runtime execution claim: NONE
next_action: validate adapter behavior and integrate the adapter into concrete session/worker entry paths as they are materially touched
manual_execution_allowed: true
user_action_required: false
thread_archive_ready: false

## Merge receipt — 2026-09-02

Organization consumer:
- PR #877
- merge: `63a3aa8e81c3d16fe8c7dfbc6e77d80d1bff8d27`

StegIndex resolver:
- PR #2
- merge: `4d47439956341ea535e3e937d97c492b193daa51`

Source-bound preflight consumption is now present on `main`. This is not evidence that every existing worker invokes the adapter, and it is not runtime activation evidence.

## Truth reconciliation consumer binding — 2026-09-02

StegIndex truth reconciliation source:
- StegVerse-Labs/StegIndex PR #3
- merge: `637b33c99adf08505b485c504512b4b1ba708141`

The organization adapter now treats `indexed_truth_usable=false` as `EXACT_BLOCKER_ONLY` with exact dependency `indexed_truth_reconciled`.

It MUST NOT return `REUSE_OR_EXTEND_EXISTING` or `CONTINUE_MACHINE_EXECUTION` from stale/contradictory indexed truth.

This preserves two independent fail-closed rules:
1. usable existing truth prevents duplicate implementation;
2. unusable indexed truth requires reconciliation before either reuse or new work.
