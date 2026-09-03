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
