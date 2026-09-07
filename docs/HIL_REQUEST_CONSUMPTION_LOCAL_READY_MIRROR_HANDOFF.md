# HIL Request Consumption Local-Ready Mirror Handoff

Updated: 2026-09-06
Task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Resident request: `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`
Cross-task predicate: `PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`
Preflight: `receipts/preflight/HIL-REQUEST-CONSUMPTION-LOCAL-READY-001.json`

## Runtime defect corrected

The resident request consumer historically kept request `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` retryable after the already-existing HIL worker reached `HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED`. That behavior coupled completion of the bounded resident execution request to later public-rendezvous/TVC/reconstruction lifecycle work.

The current same-device contract supersedes that coupling. Routine local HIL `LEASE_OPEN` and receiver READY do not require another machine or a public Gateway prerequisite. Once the exact resident request successfully reaches the existing same-device local receiver READY transition, that request is consumed and must not be reissued merely because downstream public/TVC/Master Records predicates remain incomplete.

## Correct boundary

```text
RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
-> existing route/materialization checks
-> existing WorkerCoordinator targeted execution
-> HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED
-> resident request state = COMPLETED / replay-protected
-> broader HIL lifecycle remains ACTIVE
```

The existing `terminal_hil_transition_observed` receipt field is retained for compatibility with the canonical cross-task evidence contract. For this bounded consumer it means **terminal for the resident request**, not terminal for the broader HIL lifecycle. The receipt additionally carries `broader_hil_lifecycle_complete` so those meanings cannot be conflated.

`broader_hil_lifecycle_complete` remains false at local READY and ordinary public-rendezvous stages. Downstream receiver receipt, exact-byte reconstruction, TVC lifecycle, private review, publication, Site projection, and Master Records release remain independently governed evidence predicates.

## Retry behavior

Retry remains allowed when:

- runtime/node route predicates are pending;
- targeted execution returns no recognized HIL local-ready-or-later transition;
- execution fails closed before the bounded request reaches its success boundary.

Retry is no longer allowed after authentic local READY for the same request id and request hash. A later invocation returns `ALREADY_CONSUMED` and does not launch another targeted execution.

## Authority invariants

```text
HB / oscillator execution authority = NONE
WorkerCoordinator claim/fence authority = unchanged
Interlock/InTr transition authority = unchanged
TV/TVC credential authority = unchanged
GitHub token runtime authority = NONE
request consumption = not HIL lifecycle completion
request consumption = not publication/custody/Master Records authority
second user-operated machine required = false
```

No new heartbeat, oscillator, scheduler, WorkerCoordinator, dispatcher, request, claim/fence plane, runtime host, credential path, or receiver is created.

## README completeness

This is a material runtime/failure/evidence-semantics repair because it changes when the existing resident request stops retrying. `README.md` is updated in the same change set.

## Authentic evidence boundary

Source, merge, tests, or CI do not establish that request `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` has been consumed on a real resident runtime. The canonical cross-task predicate remains unsatisfied until the exact component-produced consumption receipt is observed with the required request/task identity and terminal request-consumption evidence.
