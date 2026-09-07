# Hosted Provider InTr Runtime Profile Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: `#1121`
Task registry identifier: `LLMA-ANTHROPIC-INTR-TRANSPORT-288`
State: `ADAPTER_SOURCE_MERGED / CANONICAL_REGISTRATION_SOURCE_IN_PROGRESS / AUTHENTIC_RESIDENT_EXECUTION_PENDING`
Authority effect: `NONE_RUNTIME_PROFILE_PROJECTION_ONLY`

## Source of truth

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md`, `docs/CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md`, and `docs/CANONICAL_RUNTIME_PROFILE_MAP_MIRROR_HANDOFF.md`.

Adapter source is merged at:

```text
StegVerse-org/LLM-adapter@cde350e41d16a9932932b96d77c0dbd37b950284
```

Master Records provider-usage custody/reconstruction already exists at `master-records/orchestration:PROVIDER_USAGE_CUSTODY_MIRROR_HANDOFF.md`; no Anthropic-specific custody implementation is required.

## Runtime resolution

No new runtime profile is required.

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
worker runtime: WorkerCoordinator
transition authority: Interlock/InTr
credential authority: TV/TVC
observed reality / custody: Master Records
GitHub token runtime authority: NONE
provider output authority: NONE
```

`INTERNAL` is task-routing direction only. It does not waive the external Anthropic InTr ingress or exact-response egress decisions.

## Existing implementations reused

- Anthropic transport/executor: `StegVerse-org/LLM-adapter` merged source above;
- canonical task identity/coordination: `data/canonical-task-registry.json`;
- resident request dispatch: `scripts/dispatch_resident_execution_requests.py` selector `canonical_work_coordination`;
- registered-task consumer: `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`;
- runtime profile discovery: existing runtime-profile map/matcher;
- execution claim/fence: existing WorkerCoordinator;
- credentials: TV/TVC only;
- ingress/egress: Universal Interlock/InTr;
- provider-usage custody/reconstruction: existing Master Records provider-usage path.

No second runtime, heartbeat, oscillator, scheduler, dispatcher, worker, credential authority, transition authority, or custody path is permitted.

## Canonical request and cross-task projection

Source staging:

```text
control/resident-execution-request.d/canonical-work-anthropic-intr-transport-288.json
control/cross-task-coordination.d/anthropic-intr-transport-288-canonical-work-ingress.json
```

The request is `REQUESTED`, non-authorizing, credential-neutral, and single-device compatible (`second_machine_required=false`). The cross-task fragment records request staging as source evidence and keeps authentic request consumption `UNKNOWN` until the exact resident receipt exists.

Required runtime output:

```text
receipts/sovereign-host/canonical-work-anthropic-intr-transport-288-request-consumption.latest.json
```

## Current runtime boundary

The retained source observation remains historical:

```text
control/worker-runtime-state.json: last_cycle_at 2026-08-18T19:47:00Z
control/worker-runtime-state.json: observation_mode CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
```

Therefore the remaining runtime blocker is authentic current task-executing WorkerCoordinator evidence, not a missing runtime profile.

## Machine preflight / README completeness

Preflight:

```text
data/preflight/llma-anthropic-intr-transport-288-post-merge-reconcile.json
state: PASS
```

README update is not required for this `.github` change set. The change reuses the already-documented generic registered Canonical Work request mechanism and does not alter runtime semantics, interfaces, authority boundaries, custody/evidence semantics, prerequisites, environments, or failure behavior. The LLM-adapter README was updated in the merged adapter source because Anthropic provider semantics were new there.

## Completion predicates

1. Anthropic transport/executor source merged — **COMPLETE** (`cde350e4…`).
2. Exact adapter source/CI gate — **COMPLETE**; source validation only.
3. Existing sovereign runtime selected — **COMPLETE_SOURCE**.
4. Canonical Task Registry task record — **SOURCE MUTATION IN THIS CHANGE SET**.
5. Canonical Work resident request staged — **COMPLETE_SOURCE**.
6. Cross-task request-staging predicate — **SATISFIED_SOURCE**.
7. Authentic resident request consumption / InTr ingress — **NOT OBSERVED**.
8. Authentic current WorkerCoordinator claim/fence — **NOT OBSERVED**.
9. TV/TVC Anthropic credential materialization — **NOT OBSERVED**.
10. Authentic Anthropic provider response — **NOT OBSERVED**.
11. Master Records custody/reconstruction — **NOT OBSERVED**.
12. Exact-response InTr egress ALLOW — **NOT OBSERVED**.
13. Product activation/tag/release — **NOT CLAIMED**.

## Related work safe for the same session

```text
STEGVERSE-CANONICAL-WORK-COORDINATION-001
STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001
```

These may be combined because #288 consumes their existing mechanisms. Their independent runtime predicates and authority boundaries remain intact.
