# MIR Experiment Frozen Screenshot Evidence Mirror Handoff

Updated: 2026-09-11
Goal Task ID: `MIR-EXPERIMENT-FROZEN-SCREENSHOT-EVIDENCE-001`
Adjacent contract task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
Separate Shared Docs task: `SHARED-DOCS-MULTIPARTY-FREEZE-001`
Status: `ACTIVE`

## Goal

Pre-freeze the MIR experiment screenshot evidence set so the exact same screenshot artifacts, bound to the exact same declared purposes, are used throughout the complete test.

## Core invariant

For a single experiment evidence epoch, each screenshot purpose is bound before execution to one exact screenshot artifact and digest. The binding is immutable for that run.

No mid-test screenshot replacement, re-cropping, alternate capture, purpose reassignment, selective substitution, or post-hoc favorable image selection is permitted.

If any screenshot artifact or purpose binding changes, the existing experiment evidence epoch is no longer continuous. A successor evidence epoch / new test run must be declared rather than presenting the changed evidence set as the same test.

## Required manifest fields

Each frozen screenshot entry must bind at minimum:

- `experiment_id`
- `evidence_epoch`
- `purpose_id`
- `purpose_description`
- `artifact_ref`
- `artifact_sha256`
- `captured_at` when known
- `frozen_at`
- `frozen_by`

The manifest itself must have a deterministic digest.

## Test-wide continuity rule

Every test stage that consumes screenshot evidence must reference the same frozen manifest digest and the same purpose-to-artifact mappings. A stage may consume only the subset relevant to that stage, but it may not substitute a different artifact for an existing purpose.

## Failure semantics

- unknown purpose -> `SCREENSHOT_PURPOSE_UNREGISTERED`
- artifact digest mismatch -> `SCREENSHOT_ARTIFACT_MISMATCH`
- purpose remap -> `SCREENSHOT_PURPOSE_BINDING_CHANGED`
- replacement after freeze -> `SCREENSHOT_SET_MUTATED`
- missing required screenshot -> `SCREENSHOT_EVIDENCE_UNAVAILABLE`

These are experiment evidence states, not governance outcomes.

## Separation from Shared Docs

`SHARED-DOCS-MULTIPARTY-FREEZE-001` governs collaborative document revision freeze semantics.

This task governs the MIR experiment's fixed screenshot evidence basis. The two tasks may reuse generic digest/freeze primitives, but neither task subsumes the other.

## Completion boundary

Completion requires a pre-execution purpose-indexed screenshot manifest, exact artifact digests, deterministic validation, test-stage references to the same manifest digest, and retained evidence that no screenshot or purpose binding changed during the run.

No experiment continuity or screenshot freeze is claimed until those artifacts exist.
