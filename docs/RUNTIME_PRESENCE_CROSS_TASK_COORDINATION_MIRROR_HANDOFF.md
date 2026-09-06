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

A bounded local custody path now reuses the existing presence producer and an already-local `master-records/orchestration` checkout. After the carrier-owned supervision path emits `runtime-presence.latest.json`, `scripts/repair_resident_worker_presence.py` may invoke `master-records/orchestration/scripts/intake_resident_runtime_presence.py` only when `STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT` is already declared and the importer exists locally.

The custody handoff:

- performs no network fetch or repository writeback;
- propagates no GitHub token, API key, password, private key, or credential value;
- preserves TV/TVC as credential authority;
- records its local result at `receipts/sovereign-host/runtime-presence-master-records-intake.latest.json`;
- retains the exact source observation, `runtime_root`, and `resident.node_id` when present;
- explicitly sets `cross_task_reuse_authorized=false`;
- creates no task/correlation identity or task effect;
- does not make custody a prerequisite for emitting or retaining the original presence receipt.

This local custody path supplies reconstructable subject-identity evidence for later review. It does not itself satisfy the deferred cross-task binding requirement. Remote repository visibility is also a separate persistence concern; local custody is not repository writeback.

## README completeness

The original corrective change was material because it narrowed evidence-reuse semantics. The local Master Records custody addition is also material because it adds an evidence-retention integration boundary. `README.md` is updated in the same change set and continues to state that custody does not authorize shared reuse.

## Remaining machine work

1. reuse the existing runtime-presence producer; do not create another probe;
2. observe an authentic `runtime-presence.latest.json` and, when the already-local Master Records root is available, retain it through the bounded custody importer;
3. extract stable `runtime_root` and `resident.node_id` identity from authentic retained evidence;
4. prove which consumers target that exact same subject;
5. only then promote a subject-bound predicate into the canonical composed coordination ledger;
6. continue request-specific execution/consumption predicates independently.

No user action is required.
