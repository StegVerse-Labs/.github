# StegBrowser Runtime Connection Ingress Mirror Handoff

Updated: 2026-09-15

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Root lineage: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SINGLE A1-A4 INVOCATION COMPOSITION SOURCE RECONCILED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Scope and terminal boundary

This child owns the A1 observation/projection surface and composes A2 through A4 through the existing canonical StegBrowser reusable invocation. It does not implement a second lease, runtime materializer, WorkerCoordinator path, or A4 ingress worker and stops before Round Trip 1 payload processing.

```text
A1 authentic invocation-bound connection-state observation
-> resolve canonical registered StegVerse Node Receipt #1 input
-> A2 bind validated Node/Interlock to exact manifest invocation
-> A2.1 establish existing bounded invocation lease/state binding
-> A2.2 materialize existing EVENT_EPHEMERAL StegOS runtime
-> A3 existing organization-local WorkerCoordinator claim/fence
-> A4 existing exact manifest Interlock/InTr ingress
-> STOP CHILD / handoff to Round Trip 1 owner
```

## Canonical Node-binding representation

There is one concrete Node Receipt #1 input contract:

```text
parameter: node_genesis_receipt
environment: STEGVERSE_NODE_GENESIS_RECEIPT
schema: stegos.node_handoff_receipt.v1
receipt_number: 1
validator: StegOS stegos.network_manifold.validate_node_genesis_receipt
```

`CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING` is a selector name only. It is not a second receipt schema, path format, Node identity, or authority source. The child resolves that selector to the concrete `node_genesis_receipt` / `STEGVERSE_NODE_GENESIS_RECEIPT` path and fails closed when a valid Receipt #1 is unavailable.

A plain `stegverse.sovereign-node-declaration/v0.4` declaration may not be promoted or inferred into Receipt #1 because it does not itself establish the required registered Node + Interlock continuity receipt.

No external runtime/device/host discovery is permitted or performed.

## A1

The child reuses the existing shared Universal InTr profile and resolver. `callable`, `refreshable`, and `applicable_protocol_resolved` remain invocation-bound transition variables under Interlock/InTr; none are persistent source/runtime properties.

```text
callable=false
-> no execution materialization

callable=true AND refreshable=true
-> RT-SOVEREIGN-SOURCE-REFRESH-001

callable=true AND refreshable=false
-> no refresh task

callable=true AND applicable_protocol_resolved=false
-> RT-INTR-PROTOCOL-ESTABLISH-001

callable=true AND applicable_protocol_resolved=true
-> continue through canonical Node-bound StegBrowser invocation
```

## A2 through A4 — single execution owner

The one execution owner is:

`RT-STEGBROWSER-RUNTIME-CONSUMPTION-001`

through:

`scripts/run_stegbrowser_manifest_bound_runtime.py`

That existing path:

1. validates the declared manifest and binds its exact SHA-256;
2. validates the concrete registered Node Receipt #1;
3. consumes exact `node_id`, `interlock_id`, and registration receipt hash;
4. constructs the existing `LeaseRequest` bound to manifest + Node + Interlock + registration + Goal/COSV + task/registry state;
5. materializes through existing `SovereignLocalEventRuntimeAdapter` as `RuntimeClass.EVENT_EPHEMERAL` with rendezvous not required and no persistent/participant/developer host requirement;
6. retains exact lease/runtime/state-root correlation;
7. invokes the existing organization-local boundary path for authentic WorkerCoordinator claim/fence;
8. uses the existing `workers/stegbrowser_manifest_intr_ingress.py` for exact A4 ingress correlation verification;
9. stops at the A4 boundary before Round Trip 1.

The previous child-local direct call to `workers/stegbrowser_manifest_intr_ingress.py` is removed. A4 can only be reached after the canonical Node/Interlock/lease/runtime identity exists.

## A2.1 and A2.2 explicit predicates

A2.1:

```text
INVOCATION_SCOPED_LEASE_ESTABLISHED
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
INTR_MATERIALIZATION_ADMITTED
```

A2.2:

```text
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
```

A3:

`CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED`

A4:

```text
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
INTR_ADMISSION_OBSERVED
```

## Authentic evidence state

Source reconciliation does not satisfy runtime predicates. Current authentic state remains:

```text
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = false
STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
INTR_ADMISSION_OBSERVED = false
```

Expected retained child observation:

`receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json`

Expected canonical invocation boundary:

`receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json`

Only authentic authority-owned resident evidence may promote these predicates. GitHub/CI cannot.

## Issue #1918

Issue `#1918` is already closed as the bounded source-binding defect resolved by merged+validated PR `#1923`. This reconciliation does not reopen it because the missing materializer hypothesis is false and the source binding remains complete after eliminating the duplicate A1-A4 representation. Runtime evidence remains a separate active evidence predicate, not an unresolved #1918 source defect.

## Authority invariants

- Task Registry: coordination only.
- Native resident dispatcher: discovery/dispatch only; no authority.
- A1 resolver: observation/selection only.
- `RT-SOVEREIGN-SOURCE-REFRESH-001`: local source materialization only when the invocation transition selects it.
- `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001`: non-authorizing composition of existing execution surfaces.
- WorkerCoordinator: A3 claim/fence authority.
- Interlock/InTr: A1 transition-state and A4 transition/ingress authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.

## Current first unresolved predicate

`RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED`

## Manual work

None.
