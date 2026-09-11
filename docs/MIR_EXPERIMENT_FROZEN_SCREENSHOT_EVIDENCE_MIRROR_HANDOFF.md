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

## Canonical implementation

Task registration was merged through `.github` PR #1450 at merge commit `eb79cf1f700336dbd7d05576e461df46a9093eb1` after exact-head validation succeeded.

The screenshot-continuity implementation was merged through `.github` PR #1453 at squash commit `e0e6a47e479a9bc54ca9ca9647aad8ad54cc0c6f`. Exact implementation head `1b53e9f0c1e4102240ffce0ac9a49331e216c62e` passed all observed required validation lanes before merge:

- organization-control run `34614318562` — PASS;
- deterministic repository suite run `34614318572` — PASS;
- Heartbeat worker validation run `34614318539` — PASS.

Canonical source now includes:

- `schemas/mir-frozen-screenshot-manifest.schema.json`
- `scripts/validate_mir_frozen_screenshot_manifest.py`

The schema fixes the manifest vocabulary. The validator computes a deterministic SHA-256 over canonical JSON and compares a candidate manifest against the frozen baseline. Within one evidence epoch it fails closed if experiment identity changes, evidence epoch changes, the purpose set changes, any purpose maps to a different artifact reference/digest, or the complete manifest digest changes.

These validation failures remain experiment-evidence states. They grant no governance or execution authority.

## Required manifest fields

The manifest binds:

- `schema`
- `experiment_id`
- `evidence_epoch`
- `frozen_at`
- `frozen_by`
- `entries[]`

Each screenshot entry binds at minimum:

- `purpose_id`
- `purpose_description`
- `artifact_ref`
- `artifact_sha256`
- `captured_at` when known

The validator derives the deterministic manifest digest; it is not accepted as an unverified self-asserted field.

## Test-wide continuity rule

Every test stage that consumes screenshot evidence must reference the same frozen manifest digest and the same purpose-to-artifact mappings. A stage may consume only the subset relevant to that stage, but it may not substitute a different artifact for an existing purpose.

A changed screenshot or changed purpose assignment cannot be repaired inside the same evidence epoch. The remediation is to declare a successor evidence epoch and restart the affected experiment run from its pre-execution evidence freeze.

## Failure semantics

- unknown/missing purpose -> `SCREENSHOT_PURPOSE_UNREGISTERED`
- duplicate purpose -> `SCREENSHOT_PURPOSE_DUPLICATE`
- invalid artifact digest -> `SCREENSHOT_ARTIFACT_DIGEST_INVALID`
- purpose remap -> `SCREENSHOT_PURPOSE_BINDING_CHANGED`
- purpose set replacement/removal/addition -> `SCREENSHOT_SET_MUTATED`
- complete canonical manifest drift -> `SCREENSHOT_MANIFEST_DIGEST_CHANGED`
- missing required screenshot -> `SCREENSHOT_EVIDENCE_UNAVAILABLE`
- experiment or epoch identity drift -> `SCREENSHOT_EXPERIMENT_CHANGED` / `SCREENSHOT_EVIDENCE_EPOCH_CHANGED`

These are experiment evidence states, not governance outcomes.

## Separation from Shared Docs

`SHARED-DOCS-MULTIPARTY-FREEZE-001` governs collaborative document revision freeze semantics.

This task governs the MIR experiment's fixed screenshot evidence basis. The two tasks may reuse generic digest/freeze primitives, but neither task subsumes the other.

## Evidence still required

No MIR v0.3 experiment continuity claim is made yet. Completion still requires:

1. the actual pre-execution purpose-indexed screenshot manifest;
2. exact screenshot artifacts whose bytes hash to the bound SHA-256 values;
3. a retained frozen manifest digest before experiment execution;
4. every evidence-consuming stage to reference that same digest;
5. post-run deterministic comparison proving no purpose/artifact binding changed; and
6. retained experiment evidence showing any mutation caused a successor epoch rather than silent substitution.

COSV ID is not yet established. A fresh canonical repository search after PR #1453 found the task record and handoff but no matching task-vector/index entry; a COSV vector must therefore be established through the canonical task-vector coordination path rather than copied from an adjacent task.

## Completion boundary

Completion requires a pre-execution purpose-indexed screenshot manifest, exact artifact digests, deterministic validation, test-stage references to the same manifest digest, and retained evidence that no screenshot or purpose binding changed during the run.

No experiment continuity or screenshot freeze is claimed until those artifacts exist and the validation evidence passes.
