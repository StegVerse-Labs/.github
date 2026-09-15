# StegBrowser Runtime Connection Ingress Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Root lineage: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SOURCE CHILD INSTALLED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Scope

This child exists because the parent Goal reached its prompt-decomposition boundary while the remaining work is a distinct authentic execution subproblem.

The child owns only GC A1 through A4:

1. resolve invocation-bound `callable`, `refreshable`, and applicable protocol state from authentic Interlock/InTr transition evidence;
2. select only reusable capabilities whose registered predicates match that state;
3. materialize the admitted execution surface;
4. obtain the authentic current WorkerCoordinator claim/fence;
5. reach authentic Interlock/InTr ingress on the already-bound manifest route.

It stops before Round Trip 1 payload processing. `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` remains the reusable capability for the later manifest-declared two-round-trip composition after this child reaches A4.

## Manifest invariant

The route is already declared by:

`control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json`

This child does not discover or substitute endpoints or receivers.

## A1 state-transition model

`callable` and `refreshable` are invocation-bound state-transition variables. They are not persistent runtime-source facts.

The child also binds:

`applicable_protocol_resolved`

Selection rules:

```text
callable=false
-> no execution materialization
-> no source refresh
-> no protocol-establishment task selected merely because protocol_resolved=false

callable=true AND refreshable=true
-> select RT-SOVEREIGN-SOURCE-REFRESH-001

callable=true AND refreshable=false
-> do not invent a refresh requirement

callable=true AND applicable_protocol_resolved=false
-> select RT-INTR-PROTOCOL-ESTABLISH-001

callable=true AND applicable_protocol_resolved=true
-> do not create protocol-establishment work
```

The deterministic resolver is:

`scripts/resolve_stegbrowser_runtime_connection_transition.py`

It accepts only an observation identified as:

`stegverse.intr-runtime-connection-transition-observation/v1`

with `authority_owner=Interlock/InTr` and `authority_effect=OBSERVATION_ONLY`.

The resolver selects work only. It grants no execution or transition authority.

## Existing reusable capabilities

No new reusable task is required.

- `RT-SOVEREIGN-SOURCE-REFRESH-001` — state-selected when `callable=true AND refreshable=true`.
- `RT-INTR-PROTOCOL-ESTABLISH-001` — state-selected when `callable=true AND applicable_protocol_resolved=false`.
- `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` — downstream handoff after authentic A4 ingress; not executed by this child before A4.

## Child completion predicates

```text
MANIFEST_BOUND_TO_INVOCATION = true
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = true
CALLABLE_STATE_BOUND_TO_INVOCATION = true
REFRESHABLE_STATE_BOUND_TO_INVOCATION = true
MATCHING_REUSABLE_CAPABILITIES_SELECTED = true
ADMITTED_EXECUTION_SURFACE_MATERIALIZED = true
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true
INTR_ADMISSION_OBSERVED = true
NO_ROUND_TRIP_1_PAYLOAD_PROCESSING_EXECUTED_BY_CHILD = true
NO_SECOND_USER_OPERATED_DEVICE_REQUIRED = true
```

Only authentic authority-owned evidence may satisfy runtime predicates. Source/CI cannot promote them.

## Out-of-scope defect rule

The canonical out-of-scope remediation contract applies unchanged. A foreign observed defect is retained and routed to StegVerse-Healer for independent trigger evaluation without widening this child's scope. A pending predicate alone is not a Healer trigger.

## Authority invariants

- Task Registry / child record: coordination only.
- Resolver: selection only, no authority.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: connection-state and ingress/transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- Healer: independent trigger evaluation and triggered bounded remediation only.
- GitHub/CI: source validation only; runtime authority `NONE`.

## Current first unresolved predicate

`RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED`

## Manual work

None.
