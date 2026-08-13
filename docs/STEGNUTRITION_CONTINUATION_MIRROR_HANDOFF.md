# StegNutrition Machine Continuation Mirror Handoff

Status: **ACTIVE — SESSION VALIDATION UNTIL RESIDENT CLAIM OR COMPLETION**  
Updated: 2026-08-12 23:50 -05:00

## Authority and scope

This is the canonical scoped handoff for `SHWP-STEGNUTRITION-CONTINUATION-001`, subordinate to the organization heartbeat handoffs and to `StegVerse-Labs/StegNutrition/STEGNUTRITION_MIRROR_HANDOFF.md`.

```text
goal_id: STEGNUTRITION-PHOTO-DIET-001
repository: StegVerse-Labs/.github
branch: main
canonical_product: StegVerse-Labs/StegNutrition/STEGNUTRITION_MIRROR_HANDOFF.md
credential_authority: TV/TVC
route_authority: StegVerse-Labs/TVC
github_token_runtime_authority: NONE
resident_activation_state: PENDING_DIRECT_OBSERVATION
last_directly_observed_resident_epoch: 29
resident_claim_observed: false
continuation_receipt_observed: false
```

The originating requirement is to remove descriptive/manual local-runtime selection, formally develop and use the local model/runtime, prohibit non-TV/TVC secret/token authority, and keep unfinished StegNutrition work executable through the single sovereign heartbeat rather than chat-only instructions.

## Installed resident continuation

The sovereign model/runtime itself is released in `StegVerse-002/micro-node-runtime`. This handoff owns only StegNutrition continuation into the governed TV/TVC route.

The registered task remains `SHWP-STEGNUTRITION-CONTINUATION-001`; no second scheduler or duplicate task exists. Current worker selection is `process:stegnutrition-machine-continuation-v2`.

V2 preserves deterministic local-root discovery and custody/scenario preflights, then executes `scripts/run_full_validation_no_network.py`. The exact `stegnutrition.zero-network-validation.v1` result is retained under `local_validation.validation_proof` in the admitted fenced continuation receipt.

The v2 preflight now also requires the release-projection surfaces before worker execution:
- `src/stegnutrition/release.py`;
- `src/stegnutrition/release_projection.py`;
- `scripts/run_full_validation_no_network.py`;
- `tests/test_release.py`;
- `tests/test_release_projection.py`;
- `tests/test_full_validation_orchestrator.py`;
- `tasks/STEGNUTRITION-RELEASE-PROPAGATION-017.json`.

The unified proof contains a non-authorizing `release_projection`. It remains `BLOCKED` until all five task-017 immutable evidence predicates pass and becomes `READY_FOR_PROPAGATION` only when all five qualify. It cannot tag, publish, mutate downstream repositories or acquire credentials.

Relevant commits:
- `d3062a3b87f6e0f0853d49cb4adfee7d52433917` — unified validator;
- `1a42edd46719241bb94c7f4c38397cc9be4dabb7` — continuation worker v2;
- `0e739a1aa7b676892e3dcf75185fcf258d68d191` / `ea0e6e1b32b3e3b2a12d0d5db7a38e507e8f32c0` — adapter v2 registration/selection;
- `23316121bfddd298ff78373f7fe89e8edd1c1f15` — release projector;
- `b4e664a2f270c3f2b9f72e6b9ebdcae5f2a00121` — release projection bound into unified proof;
- `07af397aba4a64bff2ba0eb39a626b3d510e883b` — v2 stale-tree preflight hardening;
- `caca272f95d2153c5062c763e6b5a5377892bb87` — preflight regression test;
- `f5bd73fcb2dd61ae2e6831725230dd53705899bd` — executable handoff release-projection binding.

No GitHub token, provider key, wallet secret, cloud secret, hosted model provider, source checkout, deployment authority or publication authority is admitted. The adapter allowlist remains only `STEGVERSE_STEGNUTRITION_ROOT`, an optional non-secret local path override.

## Validation chain

A lawful resident execution must:

1. allocate a current fenced claim under the existing heartbeat;
2. discover exactly one already-local canonical StegNutrition tree or accept one valid optional override;
3. fail closed on invalid/ambiguous roots or stale/missing v2/release-projection surfaces;
4. execute runtime-custody preflight and require `ROUTE_ADMITTED`, `credential_requirement=NONE`, replay binding, token-binding rejection and proof-tamper rejection;
5. execute scenario-provider preflight and require `LOCAL_ONLY`, no hosted inference, USDA/photo-portion/evidence binding, and no real-semantic overstatement;
6. execute `StegVerse-Labs/StegNutrition/scripts/run_full_validation_no_network.py`;
7. require custody PASS, scenario PASS and full-suite PASS;
8. project task-017 release readiness from immutable local evidence and local Git commit;
9. persist that exact proof, including `release_projection`, inside the fenced continuation receipt;
10. continue semantic, portion, real-benchmark, live-TVC and live-pipeline predicates without converting absent evidence to success.

## Validation evidence

- `31653573574`: organization control plane SUCCESS for unified-proof v2 integration.
- `31668296347`, job `94347547992`: organization control plane SUCCESS for release-projection preflight head `caca272f95d2153c5062c763e6b5a5377892bb87`.
- In run `31668296347`: control-plane invariants PASS; active-worker ownership PASS; handoff ownership PASS; cross-repository collision enforcement PASS; allocator PASS; reconciliation PASS; JSON/JSONL PASS; no GitHub authority-bearing constructs PASS.

Resident/private StegNutrition full-suite and release-projection tests remain unexecuted on the resident local tree. HB29 remains the last directly observed worker epoch; `HANDOFF_READY/AVAILABLE` is readiness, not activation.

## Current unresolved work

- resident fenced StegNutrition claim/receipt under the existing single heartbeat;
- exact resident unified zero-network validation including release-projection tests;
- real labeled-photo semantic artifact triplet qualification under task `021`;
- real photographed/weighed portion qualification under task `021`;
- live post-HB29 TVC visual route with immutable activation receipt ref/SHA;
- exact proof-bound photo-to-ledger execution with immutable activation receipt ref/SHA;
- `release_projection.state=READY_FOR_PROPAGATION`, then separately authorized release/tag/downstream propagation.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: STEGNUTRITION-FULL-VALIDATION-016
  execution_owner: current active StegNutrition session until resident fenced claim/progress or completion
  claim_state: CLAIMED_FOR_VALIDATION
  worker_registry_ref: StegVerse-Labs/StegNutrition/claims/STEGNUTRITION-FULL-VALIDATION-016.claim.json
  manual_execution_allowed: true
  collision_scope: nonconflicting validation, release-readiness projection integration and resident-HANDOFF integration only; excludes heartbeat claim/fence, TV/TVC route/credential authority, real-evidence fabrication and release publication
  release_condition: unified resident/local zero-network validation PASS is durably retained, or SHWP-STEGNUTRITION-CONTINUATION-001 is actually fenced/claimed and demonstrably progresses the task
  next_executable_action: keep source/task/claim/handoffs synchronized and consume the first lawful resident v2 proof including release_projection
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: SHWP-STEGNUTRITION-CONTINUATION-001
  execution_owner: single resident StegVerse heartbeat plus stegnutrition-machine-continuation-worker
  claim_state: HANDOFF_READY_AVAILABLE_NOT_CLAIMED
  worker_registry_ref: control/worker-registry.d/stegnutrition-continuation-001.json
  manual_execution_allowed: false
  collision_scope: resident claim/fence allocation, automatic local-root/preflight execution, v2 worker execution and continuation-receipt mutation
  release_condition: canonical resident worker completes, supersedes or releases this task under a live current claim/fence
  next_executable_action: resident heartbeat allocates a fenced claim and executes process:stegnutrition-machine-continuation-v2
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: STEGNUTRITION-CONTINUATION-AUTHORITY-BOUNDARIES
  execution_owner: TV/TVC plus StegNutrition evidence and downstream publication authorities
  claim_state: ACTIVE_AUTHORITY_BOUNDARIES
  worker_registry_ref: handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json
  manual_execution_allowed: false
  collision_scope: TV/TVC route/credential authority, real semantic/portion/benchmark evidence acceptance, physical measurements and downstream release/publication authority
  release_condition: each authority-owned predicate is supported by canonical evidence or explicitly superseded
  next_executable_action: existing authority resolves each predicate; never substitute GitHub tokens, hosted inference, fabricated evidence or a second scheduler
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: STEGNUTRITION-LOCAL-RUNTIME-SELECTION-DESCRIPTIVE-STEP
  execution_owner: SUPERSEDED
  claim_state: COMPLETE_SUPERSEDED
  worker_registry_ref: workers/stegnutrition_continuation_entrypoint_v2.py + StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
  manual_execution_allowed: false
  collision_scope: obsolete descriptive/manual local model/root selection
  release_condition: satisfied by automatic local discovery plus released sovereign model/runtime
  next_executable_action: none; continue resident validation/live evidence predicates
```

## Archive condition

This scoped lane is archive-safe only when a documented resident StegNutrition worker is actually claimed and demonstrably progressing under a current fence, or all remaining continuation work is complete/superseded. Registration, source completion, a BLOCKED release projection or hosted control-plane PASS alone is insufficient.
