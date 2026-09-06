# Runtime Presence Cross-Task Coordination Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`  
Canonical work parent: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`  
State: `DEFERRED_SUBJECT_BINDING_REQUIRED / AUTHENTIC_RUNTIME_IDENTITY_PENDING`  
Authority effect: `NONE_COORDINATION_STAGING_ONLY`

## Canonical disposition

The parent coordination handoff controls this scope. Runtime-presence evidence MUST NOT be registered as one reusable canonical predicate until authentic evidence establishes the exact resident subject identity required to prevent cross-node/runtime substitution.

The canonical staging record is:

`control/cross-task-coordination-candidates/resident-process-alive-supervised.json`

Required subject identity before admission:

```text
runtime_root identity
+ resident.node_id when available from authentic runtime evidence
+ canonical WorkerCoordinator identity
```

A runtime profile plus WorkerCoordinator class is not sufficient by itself.

## Correction of over-broad registration

PR #1032 / merge `80ea85ef3ed9b00b913f2c5555a3aa7afd8b0598` installed `control/cross-task-coordination.d/runtime-presence-predicates.json` using only:

```text
runtime_profile_id = canonical-resident-substrate-v1
worker_runtime = heartbeat_runtime.worker_runtime.WorkerCoordinator
```

That binding was narrower than a global Boolean but still broader than the parent handoff's required authentic runtime-root/node identity. The canonical parent and pre-existing deferred candidate therefore supersede that registration.

Corrective preflight:

`receipts/preflight/RUNTIME-PRESENCE-SUBJECT-BINDING-CORRECTION-001.json`

Disposition:

- remove the over-broad canonical fragment;
- retain the existing canonical producer;
- retain the existing deferred migration candidate;
- do not create a second presence projector;
- do not group consumers until authentic evidence proves they target the same runtime-root/node subject.

## Existing producer retained

No runtime implementation is removed or duplicated.

```text
producer = heartbeat_runtime/runtime_presence_projection.py
output = receipts/sovereign-host/runtime-presence.latest.json
schema = stegverse.hb-runtime-presence-resident-observability/v1
freshness = worker_cycle_age_seconds <= 60
```

The producer remains the canonical observation source. HeartBeat remains non-authorizing. WorkerCoordinator remains task-control runtime. TV/TVC remains sole credential authority.

## Evidence semantics

Qualifying evidence may establish that one concrete resident runtime is presently observed, including fresh WorkerCoordinator activity. It does not establish that every consumer referring to a canonical resident substrate targets that same runtime instance.

Presence is not request consumption, task execution, claim/fence proof, transition approval, or completion.

## Master Records

Master Records remains authority for authentic retained observed reality. No current authentic runtime-presence event was available during the original or corrective preflight that established a stable shared `runtime_root`/`resident.node_id` binding across the proposed consumers.

## README completeness

The corrective change is material because it narrows evidence-reuse semantics. `README.md` is updated in the same change set to state explicitly that runtime-presence sharing is currently staged/deferred until exact runtime-root/node identity is proven.

## Remaining machine work

1. reuse the existing runtime-presence producer; do not create another probe;
2. when authentic `runtime-presence.latest.json` evidence exists, extract stable `runtime_root` and `resident.node_id` identity;
3. prove which consumers target that exact same subject;
4. only then promote a subject-bound predicate into the canonical composed coordination ledger;
5. continue request-specific execution/consumption predicates independently.

No user action is required.
