# Portable Organization Claim Allocator TASK-2026-0012 Successor Mirror Handoff

Updated: 2026-09-13
Parent Goal Task: `STEGOS-DEVICE-CONTINUITY-PACKET-TUNNEL-RUNTIME-001`
Delivery owner Goal Task: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Canonical allocator issue: `StegVerse-Labs/.github#884`
Predecessor allocator task: `TASK-2026-0011`
Successor allocator task: `TASK-2026-0012`
Status: `ACTIVE / RETAINED-STATE SUCCESSOR SOURCE IN VALIDATION / NO CLAIM YET`

## Purpose

Allow the existing portable organization allocator on the established current iPhone to select one fresh Site projection successor for a carrier-capable StegOS TestFlight package, without widening, rewriting, or reactivating the authentic TASK-2026-0011 generation-7/fence-7 claim.

This handoff does not create another allocator, WorkerCoordinator, signing pipeline, TVC path, KV/SKAP verifier, runtime observer, or device authority.

## Why a successor is required

TASK-2026-0011 is frozen provenance. Its Site package transports source from the earlier KV-gate baseline and the actual unsigned IPA served by Site is independently hard-bound to:

```text
source_commit = 32115e32d701e783af2c2659a900e4bc90460fd2
ipa_sha256 = 557d559082bdefca5fcc69c86f342d8cc035c2d803d154de5ed45b5677f80c35
```

Direct StegOS comparison shows that source lineage is diverged from the carrier-capable host-activation source floor:

```text
67dc40e8b78ed8566d598a2aa87b52536a534878
```

The packet-tunnel runtime Goal therefore cannot use the frozen TASK-0011 IPA bytes as execution evidence. Metadata-only substitution is prohibited.

## Successor task

`tasks/TASK-2026-0012.json` preserves the existing Site/TestFlight architecture but narrows its mutation scope to the package surfaces that must be regenerated or rebound for the carrier-capable build:

- unsigned IPA bytes;
- unsigned IPA manifest;
- unsigned IPA materializer;
- existing KV-bound TestFlight entry/bootstrap;
- existing Site task/handoff projection;
- exact successor source-transport request.

The successor requires the actual regenerated StegOS source commit to equal `67dc40e8b78ed8566d598a2aa87b52536a534878` or be a descendant of it. That requirement is source identity, not a scheduler dependency and not runtime proof.

## Portable retained-state package

`control/portable-org-allocator/current-iphone-package-task0012.json` uses the same authority epoch:

```text
ORG-ALLOCATOR-PORTABLE-IPHONE-20260902
```

and the same canonical allocator/CAS/claim machinery. The package carries only TASK-2026-0012 because prior tasks and authentic claim history are retained in the current allocator state.

The package is exact-source-bound to the TASK-0012 task blob and canonical claims/queue provenance. It does not grant a claim merely by existing.

## Allocator validation extension

`org_allocator/portable_allocator.js` gains one exact TASK-0012 package form. Existing TASK-0011 and historical TASK-0007..0010 validation is preserved unchanged.

The TASK-0012 validator requires:

- organization `StegVerse-Labs`;
- `queued` / `release` task floor;
- exact requested timestamp;
- exactly one scoped Site requirement on the existing `site:current-iphone-kv-testflight-static-bootstrap` dependency surface;
- no scheduler task dependencies;
- predecessor `TASK-2026-0011`, generation 7, fence 7;
- `reactivation_or_scope_widening_allowed=false`;
- source floor exactly `67dc40e8b78ed8566d598a2aa87b52536a534878`;
- actual source commit unset until materialization;
- actual source must later equal or descend from the floor;
- frozen TASK-0011 unsigned IPA source recorded as `32115e32...` and explicitly non-substitutable;
- metadata-only refresh prohibited.

## Deterministic state-transition tests

`tests/test_portable_org_claim_allocator_task0012.py` proves:

1. package/task exact equality and source-floor invariants;
2. when a retained TASK-0011 G7/F7 claim still holds the same dependency surface, TASK-0012 is not selected and claim generation remains 7;
3. when authentic G7 lineage is retained but the predecessor claim has been released and TASK-0011 is completed, TASK-0012 is selected at generation 8 and receives fence 8.

These tests prove allocator source semantics only. They do not assert an authentic G8/F8 current-iPhone claim has occurred.

## Authority invariants

- organization allocator / WorkerCoordinator: claim and fencing authority;
- Task Registry: coordination only;
- Interlock/InTr: actual governed StegVerse transition authority;
- TV/TVC: credentials/provider/release authority;
- KV/SKAP Vault: sole user-verification authority;
- StegOS Nodes: interchangeable transport/execution surfaces, user-verification authority `NONE`;
- Master Records: observed-reality custody/reconstruction;
- HeartBeat: timing/freshness/correlation/observability only;
- GitHub/CI: source validation only, runtime authority `NONE`;
- second user-operated device: prohibited and unnecessary.

## Next admissible sequence

1. Validate and merge the TASK-0012 task, allocator validation extension, retained-state package, tests, and packet-tunnel dependency projection.
2. Project the TASK-0012 package through the existing immutable current-iPhone allocator carrier; do not reset allocator state.
3. If TASK-0011 still owns the conflicting Site surface, fail closed without generation advance.
4. Once that claim is authentically released/completed, permit the canonical allocator to select TASK-0012 at the next generation/fence.
5. Only after authentic TASK-0012 claim/fence evidence exists may the Site package be regenerated from carrier-capable StegOS source.
6. Package projection/build evidence still does not satisfy packet-tunnel runtime predicates; authentic installed execution and exact `127.0.0.1:8766` observation remain downstream.

## Manual work

None at this source-validation stage.
