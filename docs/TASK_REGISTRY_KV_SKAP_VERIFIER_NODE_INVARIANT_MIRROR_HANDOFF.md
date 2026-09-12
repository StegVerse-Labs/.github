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
credential authority: TV/TVC
transition authority: Interlock/InTr
```

A StegOS node may enforce exact local operation integrity and may invoke locally available capabilities after applicable KV/SKAP-backed verification state and Interlock/InTr admission are bound to that operation. This does not turn the node into the verifier.

Replacing one eligible device/node with another must not alter the user's verifier. Node identity may be used for routing, capability continuity, freshness, replay protection, and evidence correlation, but not as a user-verification trust root.

## Enforcement

- `data/task-registry-global-invariants.json` is the machine-readable invariant contract.
- `scripts/evaluate_task_registry_collision_checkin.py` projects the contract into every check-in disposition, including `STOP_NOT_REGISTERED`, so registration work sees the same rule before a new task exists.
- `scripts/validate_task_registry_global_invariants.py` validates the invariant contract and rejects explicit canonical-record contradictions.
- `scripts/validate_org_control_plane.py` runs that validation as part of organization-control validation.
- `tests/test_task_registry_global_verifier_node_invariant.py` verifies global check-in projection and the corrected signer-task posture.

## Correction applied to active signer task

`TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001` no longer treats an iPhone-side independent verifier or a production Ed25519 channel identity as a user-verification prerequisite. Its remaining bridge is KV/SKAP-backed verification + current Interlock/InTr admission -> interchangeable StegOS node -> exact local non-exportable capability invocation.

The already-merged Ed25519 signed InTr envelope may remain as transport-integrity evidence, but it is not a user verifier, does not grant signing/credential/transition authority, and may not make a particular device a required trust root.

## README review

The organization README already preserves separated Task Registry, TV/TVC, Interlock/InTr, Master Records, and device/human authority semantics. This more specific verifier/node invariant is enforced by the machine-readable registry substrate and this handoff; no broad README rewrite is required in this change.

## Manual work

None.
