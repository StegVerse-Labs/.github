# KV-SKAP-VAULT-FUNCTIONAL-001 mirror handoff (PROPOSED identity, registration request only)

This file projects a **request**. It is not the Task Registry, it mints no authority and it bumps no registry generation. The identity `KV-SKAP-VAULT-FUNCTIONAL-001` is a proposal (`NONE_PROPOSAL_ONLY`). It becomes canonical only when `scripts/canonical_task_registration_transition.py` applies it, after its collision check-in reaches CONTINUE.

- Request: `tests/fixtures/canonical_task_registration/i1-goal-manifests/KV-SKAP-VAULT-FUNCTIONAL-001.request.json` (NEW_IDENTITY)
- Allocation request: `control/goal-task-allocation-requests/lane-d-kv-skap-vault-2026-10-23.json` (cosv_task_vector null; the transition derives the vector from the declared exact metrics)
- Source: the owner's priority for after the operating-mode ladder, a functional KV with a SKAP Vault inside KV, relayed by Coordination on 2026-10-23 under StegVerse-org/.github#160
- Sealed scope (GOAL_SCOPE_SEALED): `sha256:d68e239bd1eeabe6558b52928632e9e1df35656e55b3f899755924e66b862ada`. Changing the goal, the targets, the predicates or the finish point needs a new digest and a `control/goal-scope-supersede-requests/` entry.

## Finish point (test-verifiable)

- Acceptance test: `StegVerse-Labs/continuity-vault-kit:tests/test_kv_skap_vault_finish_point.py::KvSkapVaultFinishPoint::test_finish_point_verdict`
- Predicate `KV_SKAP_VAULT_FINISH_POINT`: `python -m runtime.kv_skap_vault finish-point` returns `ALLOW`, which means every expected evidence predicate is ALLOW over one receipt-hash lineage. Until then it returns a six-field FAIL_CLOSED that names each unmet predicate.
- Lowest supported mode: E0 (ecosystem only, no LLM, Python stdlib)

## Authority (unchanged, not duplicated)

- KV/SKAP Vault is the only user verifier.
- TV/TVC is the credential authority and the sole writer of SKAP ciphertext custody. The vault holds custody-key references only.
- Interlock/InTr is the transition authority.
- WorkerCoordinator owns claims and fences.

## Adjacent, not equivalent

- STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 is the shell that consumes this goal.
- STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001 is the single-device lane. This goal depends on it.
- TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001
- SS-KV-SKAP-SOCIAL-RELEASE-001

The collision check-in currently returns COORDINATE_CONVERGENCE with three of these (see MANIFEST.json `expected_plan`). The owners or Coordination need to confirm adjacency-not-equivalence before the identity can apply.
