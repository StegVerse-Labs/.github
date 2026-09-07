# Hosted Provider InTr Runtime Profile Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: `#1121`
Branch: `feat/provider-intr-runtime-profile-1121`
State: `EXISTING_PROFILE_IDENTIFIED / CROSS_REPO_TASK_PROJECTION_PENDING`
Authority effect: `NONE_RUNTIME_PROFILE_PROJECTION_ONLY`

## Source of truth

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `docs/CANONICAL_RUNTIME_PROFILE_MAP_MIRROR_HANDOFF.md`.

The goal is to make optional hosted-provider interoperability resolvable by the existing canonical runtime-profile matcher without creating a second runtime or granting provider authority.

## Resolution

No new runtime profile is required.

The canonical `sovereign-runtime-worker-v1` already declares `bounded_process_execution`, permits mutation within an admitted sovereign-runtime scope, runs on the existing resident HB32/WorkerCoordinator substrate, and retains TV/TVC credential authority. The runtime matcher treats `direction` as canonical task-routing direction, not arbitrary network packet direction. Therefore an Anthropic transport task is an `INTERNAL` WorkerCoordinator task whose provider request/response crosses the external boundary only through the separately governed Anthropic InTr transport contract.

Creating a second provider-specific heartbeat/worker/runtime profile would duplicate the existing execution substrate and is rejected.

## Existing runtime reused

```text
runtime profile: sovereign-runtime-worker-v1
resident substrate: canonical-resident-substrate-v1
required capability: bounded_process_execution
environment: SOVEREIGN_RESIDENT
task routing direction: INTERNAL
mutation_required: true
deployment_required: false
current_observation_required_for_candidate_discovery: false
HB protocol: HB32
heartbeat progression: OSCILLATOR_ONLY
oscillator: independent 100 Hz reference / 10 ms reference increment
worker runtime: WorkerCoordinator
transition authority: Interlock/InTr
credential authority: TV/TVC
observed reality / custody: Master Records
GitHub token runtime authority: NONE
provider output authority: NONE
```

Candidate discovery deliberately does not require a current runtime observation. The matcher otherwise removes a valid declared profile and causes the false generic `runtime missing` failure. Live task execution still requires WorkerCoordinator admission/claim/fence and authentic current runtime evidence through the existing runtime/observability path.

## Anthropic #288 binding

`StegVerse-org/LLM-adapter#288` now carries explicit `runtime_binding` and `runtime_requirements` selecting this existing profile. Its source handoff records the same binding.

Required invariants remain:

```text
canonical_sovereign_route_replaced: false
hosted_provider_required: false
credential_authority: TV/TVC
transition_authority: Interlock/InTr
provider_output_authority: NONE
profile_match_grants_execution_authority: false
live_runtime_observation_required_before_provider_call: true
```

The adapter task binding repairs profile discovery only. It does not synthesize an InTr ALLOW, a WorkerCoordinator claim/fence, provider credentials, provider output, Master Records custody, or activation evidence.

## Current observed runtime state

Canonical source currently records:

```text
control/heartbeat-carrier-runtime-state.json: activation_state ACTIVE / epoch 31
control/worker-runtime-state.json: last_cycle_at 2026-08-18T19:47:00Z
control/worker-runtime-state.json: observation_mode CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
```

Therefore the correct remaining runtime predicate is `AUTHENTIC_CURRENT_TASK_EXECUTING_WORKERCOORDINATOR_OBSERVATION`, not `RUNTIME_PROFILE_MISSING`.

## Cross-repository projection

The canonical runtime resolver consumes `runtime_requirements` from `data/canonical-task-registry.json`. The adapter task now has the correct requirements; they still need to enter the canonical Task Registry through the existing Canonical Work coordination/admission path. Do not hand-create execution authority or a parallel registry to bypass this step.

## README impact

No new runtime capability is introduced after reconciliation; the runtime semantics are existing behavior. README change in `.github` is therefore NOT REQUIRED for the profile itself. The scoped handoff is required because it records the cross-repository selection and explains why no second profile is created. The LLM-adapter README remains REQUIRED by #288 because Anthropic transport/interface semantics are new there.

## Completion predicates

1. adapter task declares exact existing runtime requirements — COMPLETE;
2. adapter scoped handoff records existing profile and authority boundary — COMPLETE;
3. cross-repository canonical Task Registry projection — PENDING_CANONICAL_WORK_ADMISSION;
4. runtime resolution projects `sovereign-runtime-worker-v1` as compatible — PENDING_REGISTRY_PROJECTION;
5. WorkerCoordinator current task-executing observation — NOT YET OBSERVED;
6. no live Anthropic/Claude execution is claimed without authentic runtime evidence — PRESERVED.

## Downstream boundary

This runtime-profile reconciliation does not authorize Site, Publisher, StegIndex, protocol wiki, tag, release, or activation propagation. Those remain governed by the #288 release/evidence predicates.
