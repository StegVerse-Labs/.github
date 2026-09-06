# Runtime Presence Cross-Task Coordination Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`  
Canonical work parent: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`  
State: `SOURCE_IMPLEMENTED / AUTHENTIC_RUNTIME_PRESENCE_PENDING`  
Authority effect: `NONE_COORDINATION_ONLY`

## Purpose

Bind the already-existing canonical resident runtime-presence producer to one subject-bound cross-task predicate so resident tasks reuse the same fresh evidence instead of creating independent liveness probes.

## Preflight

Machine preflight: `receipts/preflight/CROSS-TASK-RUNTIME-PRESENCE-PREDICATE-001.json`.

The preflight passed before functional mutation and established:

- no equivalent canonical coordination predicate was already present;
- no active evidence-production claim or mutation collision was observed;
- the authoritative producer already exists at `heartbeat_runtime/runtime_presence_projection.py`;
- Master Records has no authentic matching current event yet;
- no new heartbeat, WorkerCoordinator, scheduler, or runtime probe is required;
- the change is materially functional because it changes coordination/evidence-reuse semantics, so `README.md` is updated in the same change set.

## Canonical predicate

Fragment: `control/cross-task-coordination.d/runtime-presence-predicates.json`

```text
semantic_predicate_id = resident_worker_runtime_present
subject.runtime_profile_id = canonical-resident-substrate-v1
subject.worker_runtime = heartbeat_runtime.worker_runtime.WorkerCoordinator
producer = heartbeat_runtime/runtime_presence_projection.py
output = receipts/sovereign-host/runtime-presence.latest.json
schema = stegverse.hb-runtime-presence-resident-observability/v1
freshness = worker_cycle_age_seconds <= 60
```

The predicate is shared only when semantic identity **and** subject binding match.

## Consumers

- `SHWP-SV002-ORG-RUNTIME-ACTIVATION-001`
- `SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001`
- `SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001`
- `SHWP-SV011-PHASE5-BOUNDARY-001`

## Evidence semantics

A qualifying presence receipt must establish:

- `resident.present_worker_runtime_observed=true`;
- `resident.worker_cycle_fresh=true`;
- carrier/worker freshness correlation;
- canonical WorkerCoordinator identity;
- observation-only/non-authorizing projection semantics.

Presence is **not** request consumption, task execution, claim/fence proof, transition approval, or task completion. Request-specific `resident_request_consumed` predicates remain distinct and subject-bound.

## Master Records

Master Records remains authoritative for observed reality and reconstructable retained events. No matching authentic current runtime-presence event was observed during preflight, so this predicate remains `UNKNOWN` until the canonical resident producer emits fresh evidence and any applicable custody/reconciliation path retains it.

## Collision rule

Do not create a second runtime-presence probe for these consumers. Reuse the canonical producer/output. If a different runtime/node identity is required, create a differently subject-bound predicate rather than broadening this one.

## README completeness

`README.md` now documents cross-task runtime-presence evidence reuse and explicitly preserves the distinction between runtime presence and execution/completion proof.

## Remaining machine work

1. validate this fragment under canonical composed-ledger validation;
2. allow the existing resident runtime to produce fresh `runtime-presence.latest.json` evidence;
3. when qualifying evidence exists, reevaluate all bound consumers before creating another presence check;
4. continue request-specific execution only through their existing WorkerCoordinator/InTr/TV-TVC paths.

No user action is required.
