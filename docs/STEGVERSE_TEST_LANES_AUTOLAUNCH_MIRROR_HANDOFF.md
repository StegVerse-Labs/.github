# StegVerse Test Lanes Autolaunch Mirror Handoff

Updated: 2026-08-18T15:00:00-05:00

## Active goal and claim

```text
goal_id: STEGVERSE-TEST-LANES-AUTOLAUNCH-001
originating_goal: Automatically run the canonical nine-lane StegVerse test when all required runtime, authority, credential, plan, duplicate-execution, and evidence boundaries are actually satisfied.
repository: StegVerse-Labs/.github
branch: main
canonical_task_owner: StegVerse-Labs/.github worker control plane
claim_state: CLAIMED_FOR_IMPLEMENTATION
claimant: current integration session
claim_created_at: 2026-08-18T15:00:00-05:00
claim_release_condition: matrix evaluator, worker registration, tests, downstream trigger contract, task-state propagation, and strongest available validation are installed and transferred
primary_provider: stegverse_local
third_party_role: CONTROL_OR_FALLBACK_ONLY
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
heartbeat_grants_execution_authority: false
```

## Canonical dependencies

- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json` — machine-owned G18 heartbeat/WorkerCoordinator activation.
- `StegVerse-Labs/.github#60` — sovereign local inference activation worker.
- `StegVerse-Labs/TVC/docs/PROVIDER_CAPSULE_MIRROR_HANDOFF.md` — TVC-local provider readiness/capsule/lease execution authority.
- `GCAT-BCAT-Engine/workflows/experiments/stegverse-test-lanes/TEST_LANES_MIRROR_HANDOFF.md` — portable nine-lane manifest/planner/evidence/comparator.

## Collision boundaries

1. Do not mutate or duplicate G18 heartbeat activation implementation or fencing token.
2. Heartbeat/carrier events only wake/re-evaluate this matrix; they never authorize test execution.
3. Do not create a second TV/TVC vault, provider broker, lease authority, or credential ingress.
4. Do not make external providers primary or required for sovereign progress.
5. Do not accept `READY`, task assignment, workflow success, source completeness, or handoff state as runtime proof.
6. Test execution requires a fresh bounded execution claim/fence and exact immutable input identities.

## Intended state machine

```text
heartbeat/worker transition or relevant durable-state change
-> evaluate authoritative condition matrix
-> persist matrix receipt
-> if hard requirements unmet: BLOCKED/WAITING with exact predicates
-> if all required predicates pass: acquire fresh bounded test-run claim
-> freeze manifest/task/plan hashes
-> invoke StegVerse PRIMARY execution through sovereign path
-> invoke READY external control groups through TVC only
-> persist sanitized evidence
-> deterministic comparison
-> terminal completion receipt
```

## Required matrix classes

- REQUIRED: sovereign runtime, StegVerse primary, TVC route, manifest/task/plan identity, evidence sink, validation predicates.
- OPTIONAL: external provider capsules unless the manifest explicitly marks a lane required.
- PROHIBITIVE: NON-TV/TVC secret authority, third-party PRIMARY promotion, duplicate execution claim/fence, stale/mismatched hashes.
- MACHINE_OWNED: G18 HB30+/WorkerCoordinator and sovereign same-execution activation evidence.
- HUMAN_AUTHORITY: provider secret-value entry only through `TVC-PROVIDER-CREDENTIAL-BINDING-011`.

## Completion criteria

This scope is not complete merely because the matrix source exists. Completion requires installed evaluator + tests + worker/task integration + durable outputs and direct evidence that the evaluator can distinguish blocked from executable state. Full goal activation additionally requires the actual canonical nine-lane run, sanitized evidence, deterministic comparison, and downstream runtime proof.

## Validation commands

```text
python -m pytest -q tests/test_test_lanes_autolaunch_matrix.py
python scripts/evaluate_test_lanes_autolaunch_matrix.py --help
```

## Integration and propagation obligations

- Register a non-authorizing worker/task in `.github` control-plane state.
- Point executable transition to TVC/Test Lanes canonical runners; do not duplicate them.
- Update `StegVerse-Labs/TVC` Provider Capsule task/handoff with the autolaunch consumer.
- Update `GCAT-BCAT-Engine/workflows` Test Lanes task/handoff with the autolaunch producer.
- Attach the integration state to `.github#60` without changing its G18 authority.

## Current accounting

```text
required developed surfaces: 0/6
validation: 0/3
integration: 0/4
goal activation: 0%
session consolidation: 0/1
archive_state: PROHIBITED_WHILE_REQUIRED_EXECUTION_REMAINS
```

## Exact next task

Install the deterministic condition matrix schema/config and evaluator in this repository, then tests, worker/task registration, and downstream trigger contract.