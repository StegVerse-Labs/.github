# Crypto Live Auto Canonical Work Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Task Registry ID: `CRYPTO-LIVE-AUTO-001`
COSV task vector: `50000000106000`
Source task owner: `StegVerse-Labs/crypto-bot`
Related goals: `CRYPTO-MONEY-MANAGER-001`, `CRYPTO-LIVE-AUTO-001`
Adjacent governed owners: `StegVerse-Labs/TVC#119`, `StegVerse-Labs/stegfin-governance#84`
Status: `RESIDENT_INGRESS_SELF_MATERIALIZATION_REPAIR_MERGED / PORTABLE_DISPATCH_SELECTOR_REPAIR_STAGED / AUTHENTIC_INGRESS_PENDING`

## Purpose

Advance the existing machine-owned CryptoBot live-trading task through the canonical StegVerse Task Registry and generalized Canonical Work resident ingress path without creating a second runtime, scheduler, credential path, Coinbase provider path, or trading implementation.

## Current canonical identity

- task id: `CRYPTO-LIVE-AUTO-001`
- profile: `task.v1`
- COSV vector: `50000000106000`
- lifecycle: `MACHINE_OWNED`
- source coordination state: `PROPOSED`
- allowed next transition: `INGRESS_ADMITTED`
- authentic resident consumption: not yet observed

## Completed source repairs

PR #1263 merged at `8efdad0ac689dbd3692b6dac8e014f4c87bd5c9c` after all three exact-head validation workflows passed:

- Validate organization control plane — SUCCESS;
- Heartbeat Worker Project validation — SUCCESS;
- Deterministic Repository Suite diagnostics — SUCCESS.

That merge repaired two stale-resident ingress failure modes:

1. explicit Canonical Work requests are now exact-byte self-materialized from already-local canonical source before resident request validation, eliminating the prior permanent `NO_REQUEST` path;
2. if an intentionally preserved resident monolithic registry predates the requested task, the consumer can materialize the exact task-specific canonical shard without overwriting the resident registry.

Focused regression coverage remains in `tests/test_crypto_live_auto_resident_ingress_repair.py`.

## Portable refresh/dispatch remediation — 2026-09-09

Post-merge addressability inspection found a third concrete gap. The generic resident dispatcher already registers:

`canonical_work_coordination -> control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`

but `scripts/refresh_and_dispatch_resident_requests.py` did not include `canonical_work_coordination` in its exact-selector allowlist. That meant the portable already-local `refresh -> exact targeted dispatch` bridge could not select the very Canonical Work consumer required to produce the CryptoBot ingress receipt.

The follow-up branch `fix/crypto-live-auto-preserve-resident-task-shard-20260909` now:

- adds `canonical_work_coordination` to `ALLOWED_TARGET_CONSUMERS` in `scripts/refresh_and_dispatch_resident_requests.py`;
- preserves the historical default selector;
- continues exact one-consumer selection with unrelated consumers excluded;
- keeps network source fetch, credential acquisition, claim/fence creation, second-machine requirement, and hosted-runtime execution disabled;
- adds `tests/test_crypto_live_auto_portable_dispatch_selector.py` to prove the portable bridge and generic dispatcher agree on the exact selector.

README was reviewed. It already documents generalized Canonical Work task ingress, resident request dispatch, portable local source refresh/dispatch, and source-vs-runtime evidence separation. No duplicate CryptoBot-specific README section is required for this selector addition.

## Canonical source and runtime chain

`canonical task ingress -> Master Records reconciliation -> WorkerCoordinator admission/claim/fence if independently admitted -> TVC current-iPhone/SKAP/provider evidence -> StegFin #84 bounded decision -> first max-$10 ETH-USD LIMIT/GTC post_only proof -> reconciliation -> next authenticated snapshot -> second bounded cycle -> repeat-loop proof`

The staged request remains:

`control/resident-execution-request.d/canonical-work-crypto-live-auto-001.json`

Expected authentic consumption evidence remains exactly:

`receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json`

No merge, CI result, staged request, COSV pointer, or hosted test may substitute for that receipt.

## Exact next evidence action

After the portable selector repair validates and merges, an already-running sovereign resident must refresh already-local source and dispatch exactly `canonical_work_coordination`. The required resulting artifact is:

`receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json`

Only after that authentic receipt exists may Master Records reconciliation and WorkerCoordinator admission advance. Coinbase interaction remains downstream under TVC #119 and StegFin #84.

## Current completion boundary

Source registration, COSV binding, request staging, structural preflight, and the stale-resident self-materialization repair are complete and merged. The portable targeted-dispatch selector repair is staged for validation. Authentic resident ingress, Master Records reconciliation, WorkerCoordinator admission, current-iPhone TVC/SKAP provider evidence, StegFin bounded approval, first bounded live order, reconciliation, and second-cycle proof remain outstanding.
