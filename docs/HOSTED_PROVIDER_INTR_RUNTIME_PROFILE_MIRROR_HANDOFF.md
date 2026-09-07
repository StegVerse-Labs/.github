# Hosted Provider InTr Runtime Profile Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: `#1121`
Branch: `feat/provider-intr-runtime-profile-1121`
State: `CANONICAL_TASK_REGISTERED / RESIDENT_REQUEST_STAGED / AUTHENTIC_RESIDENT_EXECUTION_PENDING`
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

## Canonical task registration

`LLMA-ANTHROPIC-INTR-TRANSPORT-288` is now present exactly once in `data/canonical-task-registry.json` generation 16 as `PROPOSED`.

Its canonical runtime requirements are:

```text
capabilities: [bounded_process_execution]
environment: SOVEREIGN_RESIDENT
direction: INTERNAL
mutation_required: true
deployment_required: false
current_observation_required: false
runtime_resolution: null until the normal runtime-profile resolution cycle executes
worker_claim: null claim / null fence / WORKERCOORDINATOR authority
allowed_next_transition: INGRESS_ADMITTED
```

The task explicitly records the current live blocker instead of a false profile blocker:

`BLOCK-ANTHROPIC-CURRENT-TASK-EXECUTING-WORKERCOORDINATOR`.

No task admission, claim, fence, credential, provider call, custody receipt, or egress ALLOW is inferred from registration.

## Resident request staging

The existing Canonical Work resident consumer has been extended only by one explicit task specification; its shared execution logic is unchanged.

```text
request: control/resident-execution-request.d/canonical-work-anthropic-intr-transport-288.json
mode: CANONICAL_WORK_EVENT_BOOTSTRAP
entrypoint: scripts/install_and_run_canonical_work_event_bootstrap.py
consumer selector: canonical_work_coordination
consumer implementation: control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py
expected consumption receipt: receipts/sovereign-host/canonical-work-anthropic-intr-transport-288-request-consumption.latest.json
second_machine_required: false
network_source_fetch_allowed: false
credential_authority: TV/TVC
GitHub token runtime authority: NONE
request authority effect: NONE_REQUEST_ONLY
```

No new dispatcher, scheduler, listener, heartbeat, oscillator, WorkerCoordinator, or runtime implementation was created.

## Anthropic #288 adapter binding

`StegVerse-org/LLM-adapter#314` is the current-main source integration PR. It carries explicit runtime binding plus the native Anthropic transport/executor, schemas, tests, reference transaction, source gate, and README semantics. The prior stale branch/PR is provenance only and is not the merge path.

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

## Current observed runtime state

Canonical source currently records:

```text
control/heartbeat-carrier-runtime-state.json: activation_state ACTIVE / epoch 31
control/worker-runtime-state.json: last_cycle_at 2026-08-18T19:47:00Z
control/worker-runtime-state.json: observation_mode CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
```

Therefore the correct remaining runtime predicate is `AUTHENTIC_CURRENT_TASK_EXECUTING_WORKERCOORDINATOR_OBSERVATION`, not `RUNTIME_PROFILE_MISSING`.

## README impact

No new `.github` runtime capability is introduced after reconciliation; the runtime semantics are existing behavior. Root `.github` README change is therefore not required for the profile itself. This scoped handoff plus canonical task/request state records the cross-repository selection. The LLM-adapter README is required because Anthropic transport/interface semantics are new there and has been updated on #314.

## Completion predicates

1. adapter task declares exact existing runtime requirements — COMPLETE;
2. adapter transport/executor/test/source-gate surfaces installed on current-main branch — COMPLETE_SOURCE_PENDING_FINAL_CI;
3. LLM-adapter README reconciliation — COMPLETE;
4. cross-repository canonical Task Registry registration — COMPLETE_SOURCE;
5. #288 Canonical Work resident request staged in existing consumer — COMPLETE_SOURCE;
6. runtime resolution projects `sovereign-runtime-worker-v1` as compatible — PENDING_AUTHENTIC_RUNTIME_PROFILE_CYCLE;
7. authentic Canonical Work ingress/request-consumption receipt — NOT YET OBSERVED;
8. current task-executing WorkerCoordinator observation — NOT YET OBSERVED;
9. live Anthropic provider transaction / Master Records reconstruction / exact egress ALLOW — NOT CLAIMED.

## Downstream boundary

Source merge permits capability documentation only. Site/Publisher availability claims remain gated on an authentic governed transaction whose ingress receipt, exact provider response hash, egress receipt, and Master Records reconstruction all bind the same execution.
