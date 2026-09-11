# Portable Organization Claim Allocator TASK-2026-0011 Successor Mirror Handoff

Updated: 2026-09-10
Parent goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Child goal: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Canonical allocator issue: `StegVerse-Labs/.github#884`
Successor task: `TASK-2026-0011`
Status: `ACTIVE / RETAINED-STATE SUCCESSOR ALLOCATOR SOURCE IN VALIDATION`

## Purpose

Extend the existing canonical portable organization allocator so the retained current-iPhone allocator state can consume the new KV-gated delta successor without resetting or replacing the authentic TASK-2026-0010 generation-6/fence-6 state.

## Authentic predecessor evidence

Current-iPhone immutable journal recovery proved:

```text
TASK-2026-0010 selected
claim_registry_generation 6
fencing_token 6
CLAIM_GRANT_OBSERVED
ALLOCATION_COMPLETE
journal replay PASS
recovery allocator mutation false
```

TASK-0010's G6 claim remains active provenance. It is not widened or reactivated.

## Successor package model

`control/portable-org-allocator/current-iphone-package-task0011.json` is intentionally a retained-state successor package. It carries only `TASK-2026-0011` because predecessor task statuses and claims already live in the retained atomic allocator state.

The package retains the exact authority epoch:

```text
ORG-ALLOCATOR-PORTABLE-IPHONE-20260902
```

and requires the current canonical task blob plus canonical claims/queue source bindings.

TASK-0011 uses a new dependency surface and new Site paths:

```text
site:current-iphone-kv-testflight-static-bootstrap
stegos-bootstrap/current-iphone-kv-testflight.html
stegos-bootstrap/current-iphone-kv-testflight-bootstrap.js
stegos-bootstrap/kv-bound-ephemeral-projection-context.js
stegos-bootstrap/kv-projection-file-loader.js
```

Those paths/surface do not retroactively alter TASK-0010's predecessor scope.

## Allocator implementation

`org_allocator/portable_allocator.js` preserves the existing allocation/CAS/claim-observation logic. Its package validator gains one exact successor-package form:

```text
tasks == [TASK-2026-0011]
task source blob == a9f90414e59e308d66faf7ff2d5c31173b1687ca
requested_at == 2026-09-11T01:51:58Z
priority_class == release
dependency surface == site:current-iphone-kv-testflight-static-bootstrap
```

Historical TASK-0007 through TASK-0010 package validation remains unchanged.

The successor package does not authorize an initial-state execution path in Site. The runtime wrapper must require already-retained allocator state before invoking it.

## Deterministic validation

`tests/test_portable_org_claim_allocator_task0011.py` requires:

1. package/task exact equality and expected KV delta scope;
2. a retained G6 state with an active TASK-0010 claim remains intact;
3. the unchanged allocator transition selects TASK-0011 at generation/fence 7 when scopes do not collide;
4. a held claim on the new dependency surface causes no selection and no generation advance.

## Authority invariants

```text
canonical allocator claim authority: unchanged
WorkerCoordinator claim/fence authority: unchanged
Interlock/InTr transition authority: unchanged
TV/TVC credential authority: unchanged
HB authority: observability only
GitHub Actions runtime authority: NONE
state reset/replacement allowed: false
second user-operated machine required: false
Render fallback: none
```

## Next sequence

1. Validate/merge this source update.
2. Project the updated allocator JS plus TASK-0011 successor package into a new immutable Site `stegos-node` allocator carrier under bootstrap-support scope only.
3. On current iPhone, require retained G6 state and execute exactly one canonical TASK-0011 allocation attempt.
4. Export exact G7 claim/fence evidence if selected.
5. Only then mutate the TASK-0011 Site product branch.

## Manual work

None until the immutable Site TASK-0011 allocator carrier is published.
