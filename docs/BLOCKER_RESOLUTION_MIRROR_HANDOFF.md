# Blocker Resolution Runtime Mirror Handoff

## Status

```text
goal_id: WORKER-BLOCKER-REMEDIATION-001
owner: StegVerse-Labs/.github#65
state: IMPLEMENTED_ON_MAIN_VALIDATION_PENDING
archive_ready: false
```

## Canonical invariant

A blocker is not permission to wait. A blocker means the current solution is insufficient and a different solution or workaround is required.

Third-party dependencies are never StegVerse blockers. Provider credentials, SaaS quotas, hosted inference, external schedulers, vendor outages, and similar external conditions may make one candidate path unavailable, but the worker must remain active on solution selection and pursue a StegVerse-owned/federated or otherwise admitted alternate path.

## Runtime enforcement

- `control/blocker-resolution-policy.json` is the machine-readable policy.
- `heartbeat_runtime/blocker_policy.py` validates worker blocker contracts.
- `heartbeat_runtime/process_adapter.py` rejects passive `BLOCKED` responses and rejects any `BLOCKED` response whose dependency class is `THIRD_PARTY`.
- Every legitimate `BLOCKED` response must state the problem, `solution_required=true`, one or more workaround candidates, and the next solution action.
- A third-party condition must be represented as an active workaround-selection/execution transition, not a blocked transition.

## Active worker corrections

- `workers/steggate_rendezvous_deployment_worker.py`: missing/rejected Cloudflare credentials and Cloudflare deployment failure now return `ACTIVE / THIRD_PARTY_WORKAROUND_REQUIRED` and name alternate sovereign/admitted rendezvous paths.
- `workers/sovereign_runtime_activation_worker.py`: missing sovereign runtime evidence now reports `SOVEREIGN_RUNTIME_SOLUTION_REQUIRED` with concrete native-node activation alternatives rather than a bare observation-only blocker.
- `workers/ecosystem_chat_sovereign_inference_worker.py`: missing local inference evidence now reports `SOVEREIGN_INFERENCE_SOLUTION_REQUIRED`, including smaller/alternate local model options rather than hosted-provider fallback.
- `control/organization-task-registry.json`: AaCT-E connector write authority is now `WORKAROUND_REQUIRED`, not `BLOCKED`; internal no-repository conditions retain blockers only with explicit repository/relay construction alternatives.
- `workers/organization_federation_readiness_worker.py`: validates the distinction between `WORKAROUND_REQUIRED` and internal `BLOCKED` conditions.

## Validation

`tests/test_blocker_resolution_policy.py` proves:

1. third-party dependencies cannot be returned as `BLOCKED`;
2. passive `BLOCKED` responses without a resolution contract are rejected;
3. internal blockers are valid only with workaround candidates and a next solution action;
4. third-party `ACTIVE` workaround execution is accepted.

`.github/workflows/heartbeat-worker-project.yml` compiles the policy/runtime/active workers and runs the blocker-resolution tests as a hosted acceptance check.

## Completion condition

This goal is not complete merely because the policy is installed. Hosted validation must pass, current worker projections must adopt the new transitions, and issue #65 must remain open until at least the critical-path sovereign runtime worker moves from repeated observation into measurable solution execution.

No chat history is required to reconstruct this rule, but the originating thread remains NOT ARCHIVE READY while ecosystem goals remain unmet.
