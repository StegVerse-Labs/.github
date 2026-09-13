# Reusable Resident Rendezvous Component Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Component: `RTC-RESIDENT-RENDEZVOUS-010`
Consuming Goal Task: `GADI-RUNTIME-CLOSURE-001`
COSV: `10100000100000`
Status: `SOURCE_IMPLEMENTED / VALIDATION_PENDING / RUNTIME_EVIDENCE_PENDING`

## Purpose

`RTC-RESIDENT-RENDEZVOUS-010` generalizes the existing resident rendezvous carrier into a bounded registered-consumer transport without creating another resident runtime, listener, scheduler, WorkerCoordinator, InTr authority, credential route, or user-verification path.

Canonical resident entrypoint remains:

```text
scripts/consume_resident_rendezvous.py
```

The standing runtime continues to invoke that same entrypoint. The implementation selects only an explicitly registered profile and then invokes the already-existing generic resident dispatcher with `--only-consumer <selector>`.

## Registered profiles

```text
stegos_kv_intr_chain
  request: control/resident-execution-request.d/stegos-kv-intr-chain-001.json
  receipt: receipts/sovereign-host/stegos-kv-intr-chain-consumption.latest.json

gadi_runtime_observation
  request: control/resident-execution-request.d/gadi-runtime-observation-001.json
  receipt: receipts/sovereign-host/gadi-runtime-observation-request-consumption.latest.json
```

Existing StegOS/KV behavior remains the default compatibility profile. GADI uses its exact pre-existing request contract; rendezvous cannot add fields, weaken validation, or mint authority.

## Authority contract

The component is transport-only and non-authorizing.

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed admission/transition authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS node reference: routing only, never user verification.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: timing/freshness/liveness/correlation/observability only.
- GitHub: no runtime authority.

The transport environment rejects hosted execution and credential-bearing environment variables. Network source-code fetch remains prohibited. The transport envelope carries only bounded request/correlation material and preserves the inner request digest.

## Delivery semantics

```text
resident advertisement for registered consumer
-> gateway fetch for target node
-> exact outer envelope validation
-> exact consumer-specific inner request validation
-> digest + expiry validation
-> materialize only the consumer-owned canonical request path
-> generic resident dispatcher --only-consumer <selector>
-> consumer-owned receipt
-> correlated rendezvous ACK
```

A GADI rendezvous ACK proves only delivery/consumer observation. It is not GADI completion and does not imply InTr admission, WorkerCoordinator claim/fence, defensive execution, effect, reassessment, termination, or Master Records reconstruction.

## Failure semantics

Fail closed for unregistered consumers, target mismatch, request digest mismatch, expired request, exact inner-contract mismatch, arbitrary local-request overwrite, hosted runtime, credential-bearing environment, or absent dispatcher.

The historical StegOS/KV request `001/002 -> 003` supersession remains narrowly preserved. Other consumers cannot overwrite a differing existing canonical local request.

## Validation

Regression coverage includes the legacy StegOS/KV rendezvous tests plus `tests/test_reusable_resident_rendezvous_gadi.py`, which requires:

- exact GADI contract drift fails closed;
- dispatch uses the canonical registered `gadi_runtime_observation` selector;
- GADI request materializes at its existing canonical path;
- ACK remains `gateway_execution_authority=NONE`;
- node identity role remains `ROUTING_ONLY`;
- KV/SKAP Vault remains the declared user-verification authority;
- network source fetch remains false;
- unregistered consumers fail before dispatch.

Source validation does not establish runtime delivery or round-trip completion.

## Remaining work

After `.github` source validation and merge, the Site/browser request producer must consume this reusable profile rather than its current hard-coded `stegos_kv_intr_chain` constants. That propagation must preserve transport-only node routing and must not treat Node Receipt #1 as user-verification authority.

## Manual work

None.
