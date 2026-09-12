# Task Registry KV/SKAP Verifier and Interchangeable Node Invariant Mirror Handoff

Updated: 2026-09-12

## Scope

This is a global Task Registry invariant. It applies to every canonical task already registered and every task registered later.

## Canonical rule

```text
user verifier: KV/SKAP Vault only
StegOS device role: interchangeable transport node
device/node user-verifier authority: NONE
transport-channel user-verifier authority: NONE
local-key / Secure-Enclave user-verifier authority: NONE
Remote Computer role: transport/discovery only
Remote Computer inventory: EVIDENCE_REACHABILITY only
ephemeral compute class: ADMITTED-EPHEMERAL-STEGOS-NODE
execution substrate selection authority effect: NONE
second user-operated device allowed: false
credential authority: TV/TVC
transition/admission authority: Interlock/InTr
claim/fence authority: WorkerCoordinator
runtime-reality/provenance authority: Master Records
```

A StegOS node may enforce exact local operation integrity and may invoke locally available capabilities after applicable KV/SKAP-backed verification state and Interlock/InTr admission are bound to that operation. This does not turn the node into the verifier.

Replacing one eligible device/node with another must not alter the user's verifier. Node identity may be used for routing, capability continuity, freshness, replay protection, and evidence correlation, but not as a user-verification trust root.

## Canonical execution-substrate and Remote Computer rule

Every runtime-capable task must review execution capacity in this order:

```text
1. STEG-BROWSER-RETAINED-RESIDENT-NODE
2. STEGOS-CURRENT-DEVICE-NODE
3. STEG-BROWSER-EPHEMERAL-LEASE
4. SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER
5. ADMITTED-EPHEMERAL-STEGOS-NODE
6. REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT
```

Remote Computer is not a distinct runtime class, execution authority, scheduler, durable machine dependency, or completion predicate. It is a transport/discovery surface. Capacity found through that transport may participate only after it materializes as the canonical StegBrowser/StegOS node class and is admitted as `ADMITTED-EPHEMERAL-STEGOS-NODE` through Interlock/InTr.

An empty Remote Computer inventory, unavailable connector, missing receipt, temporarily unreachable listener, or similar observation is `EVIDENCE_REACHABILITY` only. It may remain pending evidence; it may not establish substrate `UNSUITABLE`, authorize an external-device requirement, or create a second user-operated-machine dependency.

Presence or connectivity grants no execution, transition, claim/fence, credential, custody, publication, verification, or completion authority.

## Existing and new task enforcement

- All check-in dispositions carry `data/task-registry-global-invariants.json`, including `STOP_NOT_REGISTERED`; therefore a task sees this rule before registration and at every later check-in.
- New runtime-capable task records must include a valid `execution_substrate_resolution` and are rejected at registration if they omit or contradict the canonical review order.
- Existing/legacy runtime-capable tasks are no longer grandfathered through check-in. If their structured substrate review is absent or invalid, check-in returns `STOP_SUBSTRATE_REVIEW_REQUIRED` with `authority_effect=NONE` before mutation.
- `scripts/validate_task_registry_global_invariants.py` scans all canonical task records for explicit contradictions, including attempts to turn Remote Computer into a required machine or authority-bearing execution substrate.
- A substrate review does not mint execution authority. Interlock/InTr and WorkerCoordinator retain their existing roles.

## Enforcement

- `data/task-registry-global-invariants.json` is the machine-readable invariant contract.
- `scripts/evaluate_task_registry_collision_checkin.py` projects the contract into every check-in disposition and fail-closes runtime-capable legacy tasks missing substrate resolution.
- `scripts/validate_task_registration_substrate_resolution.py` enforces structured resolution on newly registered runtime-capable tasks.
- `scripts/validate_task_registry_global_invariants.py` validates the invariant contract and rejects explicit canonical-record contradictions across the registry.
- `scripts/validate_org_control_plane.py` runs the invariant validations as part of organization-control validation.
- `tests/test_task_registry_global_verifier_node_invariant.py` verifies projection to existing and not-yet-registered tasks.
- `tests/test_task_registry_collision_checkin.py` verifies legacy runtime tasks cannot bypass substrate reconciliation.

## Correction applied to active signer task

`TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001` no longer treats an iPhone-side independent verifier or a production Ed25519 channel identity as a user-verification prerequisite. Its remaining bridge is KV/SKAP-backed verification + current Interlock/InTr admission -> interchangeable StegOS node -> exact local non-exportable capability invocation.

The already-merged Ed25519 signed InTr envelope may remain as transport-integrity evidence, but it is not a user verifier, does not grant signing/credential/transition authority, and may not make a particular device a required trust root.

## README review

The organization README already preserves separated Task Registry, TV/TVC, Interlock/InTr, Master Records, and device/human authority semantics. This more specific verifier/node/substrate invariant is enforced by the machine-readable registry substrate and this handoff; no broad README rewrite is required in this change.

## Manual work

None.
