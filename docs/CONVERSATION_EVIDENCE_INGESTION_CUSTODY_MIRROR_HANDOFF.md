# Conversation Evidence Ingestion / Custody Mirror Handoff

Updated: 2026-09-19
Repository: `StegVerse-Labs/.github`
Canonical issue: `#2258`
Goal Task ID: `CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001`
Parent design task: `CONVERSATION-EVIDENCE-SERVICE-PERFORMANCE-REGISTRY-001`
COSV ID: `20011000100000`
Status: `ACTIVE / CANONICAL WORK + WORKERCOORDINATOR RUNTIME PATH STAGED / AUTHENTIC MASTER RECORDS CUSTODY PENDING`

## Contract boundary

Consumes `contracts/conversation-evidence-service-performance-publication-contract.v1.json` unchanged.

This phase implements only immutable evidence ingestion, authenticity-envelope construction, service/transaction/performance binding, required-evidence carriage, and canonical Master Records custody/reconstruction. It does not implement public Site projection, provider-response UI, corroboration UI, enforcement export, or legal/reputational adjudication.

## Implementation

- `workers/conversation_evidence_ingestion.py` builds deterministic ingestion packages, preserves ordered message content/digests and exact attachment bytes/digests, refuses overwrite on persisted record roots, and creates explicit authenticity and transaction bindings.
- `schemas/conversation-evidence-ingestion-package.schema.json` identifies the ingestion-package envelope.
- `tests/test_conversation_evidence_ingestion.py` covers deterministic packaging, write-once behavior, attachment hashing, unchanged v1 contract consumption, exact required-evidence carriage, successful Master Records closure, and fail-closed digest mismatch.
- Existing `workers/canonical_state_transition_custody.py` remains the sole Python custody client. No second Master Records service/store is introduced.

## Master Records transition

Transition: `CONVERSATION_EVIDENCE_INGESTED`.

Required evidence:
1. `CONVERSATION_EVIDENCE_ORIGINAL`
2. `CONVERSATION_AUTHENTICITY_ENVELOPE`
3. `SERVICE_TRANSACTION_BINDING`

Progression requires `RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and exact receipt/reconstruction digest equality.

Source tests may prove the consumer enforces this contract; only an authentic Master Records return can prove runtime custody/reconstruction.

## Privacy / authority

No source conversation is committed by this task. Test fixtures are synthetic.
The ingestion transition records evidence only. It performs no publication and no adjudication.
Interlock/InTr transition authority and Master Records custody/reconstruction authority remain unchanged.

## Source implementation evidence

- Implementation PR: `StegVerse-Labs/.github#2261`
- Exact validated head: `fac9947d5f074ebc07987cfb927644cf0ac79daa`
- Squash merge: `d62823ece61a3fe9613a353c1d91c8d24ce5416e`
- Focused ingestion validation: workflow run `35463861019` — PASS
- Cross-Task Coordination Validation: workflow run `35463860957` — PASS
- DeepSeek resident validation: workflow run `35463860968` — PASS
- Purpose-Bound Worker Derived Lifetime validation: workflow run `35463860945` — PASS
- KV AI Memory Resident Binding validation: workflow run `35463860946` — PASS
- The initial Cross-Task failure on run `35463745877` was traced to the missing mandatory `execution_substrate_resolution` metadata for a runtime-capable task. The task now declares every device/runtime substrate `NOT_APPLICABLE` for this source phase, with `external_device_required=false` and `second_user_operated_device_allowed=false`. No connected-device inventory is queried or used as task state.

These runs prove source/schema/test conformance only. They do not prove an authentic `CONVERSATION_EVIDENCE_INGESTED` transition reached Master Records.

## Next boundary

After exact-head source validation and merge, run an authentic synthetic ingestion through the existing Master Records custody surface. Only after that returns the full progression tuple may this phase claim authentic custody completion or derive a later public-projection implementation task.


## Runtime path staging — 2026-09-19

The existing runtime chain is now bound for this task without adding another scheduler, dispatcher, authority plane, custody store, or device prerequisite:

```text
canonical Task Registry
-> existing generic Canonical Work ingress
-> fresh WorkerCoordinator independent-task-control claim/fence
-> process:conversation-evidence-ingestion-custody-v1
-> workers/conversation_evidence_ingestion_runtime_worker.py
-> synthetic fixture only
-> workers/conversation_evidence_ingestion.py
-> existing canonical_state_transition_custody client
-> authoritative Master Records
```

The runtime worker requires the exact task identity, the admitted `conversation_evidence_synthetic_ingestion_custody` capability, the bounded `receipts/conversation-evidence-ingestion/**` namespace, and a fresh WorkerCoordinator claim/fence. It creates no user-derived conversation content: the fixture is hard-coded synthetic evidence.

A worker response may become `COMPLETED` only when the existing custody client returns `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and exact receipt/reconstruction digest equality. Any other Master Records result is returned as `BLOCKED` with no publication/adjudication promotion.

Source staging does not prove that the Canonical Work ingress, WorkerCoordinator claim/fence, worker invocation, or Master Records custody has occurred.


## Runtime-path merge and authentic evidence check — 2026-09-19

PR `#2291` merged at `e5f40728f92029c8f81fc543c3215e9ad98a0ad5`. Exact-head focused validation run `35468718570` passed together with Cross-Task Coordination, DeepSeek resident, Purpose-Bound Worker, and KV AI Memory repository gates.

After merge, the canonical .github and `master-records/orchestration` evidence surfaces were searched for:
- `CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001`;
- `CONVERSATION_EVIDENCE_INGESTED`;
- a current WorkerCoordinator `claim_id` + `fencing_token`;
- `receipt_sha256` + `reconstructed_receipt_sha256`.

No authentic post-merge runtime receipt was present. Therefore none of the runtime predicates are promoted. In particular:
- WorkerCoordinator claim/fence observed = false;
- Master Records `RECORDED` observed = false;
- reconstruction PASS observed = false;
- required-evidence PASS observed = false;
- exact digest equality observed = false;
- public Site projection successor derived = false.

The remediation path remains the already-merged targeted one-shot:
```text
python scripts/run_worker_runtime.py --task-id CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001
```
through the existing Canonical Work -> WorkerCoordinator -> process adapter -> canonical Master Records path. No device inventory query, second machine prerequisite, alternate runtime, scheduler, dispatcher, or custody plane is introduced.


## State-triggered selector repair — 2026-09-21

Canonical generation 150 exposed a deterministic projection mismatch: the task's runtime-resolution metadata declared the already-admitted state-triggered WorkerCoordinator successor ready, but the canonical row still carried `coordination_state=IN_PROGRESS`, no `checkout_state`, and retained `INGRESS_ADMITTED` in `allowed_next_transitions`. The repaired canonical selector therefore could not classify this task as `WORKERCOORDINATOR_TARGETED_STATE_TRANSITION`.

This repair changes only the canonical coordination projection to the already-established state:
- `coordination_state=ACTIVE`
- `checkout_state=CHECKED_OUT`
- immediate next transition begins at `WORKERCOORDINATOR_CLAIM_FENCE_BOUND`
- `INGRESS_ADMITTED` is removed from the remaining successor list.

No claim/fence is minted by this repair and no runtime, scheduler, dispatcher, custody plane, or device prerequisite is added.


## Existing reusable carrier binding — 2026-09-21

The next concrete reachability defect after selector repair was schedule addressability: the existing `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` reusable task was scheduled for other Goal Tasks but not for `CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001`.

StegVerse-Healer PR `#93` merged at `d77ad6b80c1a9b48eb67de67a2360ac9f3d0d026` after Test Readiness PASS. It adds one task-scoped row to the already-existing neutral scheduler:

```text
RT-REUSABLE-TASK-SCHEDULER-001
-> RT-CANONICAL-WORK-PORTABLE-DISPATCH-001
-> only_consumer=canonical_work_coordination
-> goal_task_id=CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001
-> existing Canonical Work registry cycle
-> existing targeted WorkerCoordinator one-shot
```

No second scheduler, runtime, dispatcher, WorkerCoordinator, custody plane, credential path, request identity, or device prerequisite was added.

Post-merge canonical evidence still contains no authentic fresh WorkerCoordinator claim/fence and no `CONVERSATION_EVIDENCE_INGESTED` Master Records closure. Therefore:
- `worker_claim.claim_ref=null`
- `worker_claim.fence_ref=null`
- Master Records `RECORDED` not observed
- reconstruction PASS not observed
- required-evidence PASS not observed
- exact digest equality not observed
- public Site projection successor not derived.


## Source-refresh ordering closure and current boundary — 2026-09-21

StegVerse-Healer PR `#94` merged at `2e3d41e44c28f0c116b190c6d5a38d094d29a588` after exact-head Test Readiness PASS.

The repair changes only schedule order so the already-existing `RT-SOVEREIGN-SOURCE-REFRESH-001` child executes before this Goal's already-existing `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` child. This removes the deterministic same-cycle `RESIDENT_RUNTIME_ROOT_NOT_MATERIALIZED` ordering failure without adding a scheduler, runtime, dispatcher, WorkerCoordinator, custody plane, credential path, device prerequisite, source transport, or authority.

The next exact unresolved predicate is not another source defect in this Goal. The standing Healer request, dispatcher selector `healer_sovereign_scheduler`, consumer `scripts/consume_healer_sovereign_scheduler_request.py`, local source-refresh bootstrap, and targeted WorkerCoordinator entrypoint are already present. What is not retained is an authentic post-repair `RESIDENT_REQUEST_DISPATCH_VISIT` / Healer scheduler checkpoint proving that the existing standing scheduler consumed the repaired reusable schedule.

Accordingly:
- fresh WorkerCoordinator claim/fence for `CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001`: not observed;
- `WORKERCOORDINATOR_CLAIM_FENCE_BOUND` Master Records closure: not observed;
- `CONVERSATION_EVIDENCE_INGESTED`: not observed;
- public Site projection successor: not derived.


## Native resident initiation trace — 2026-09-21

The post-ordering resident-dispatch initiation path was traced end to end:

```text
scripts/run_heartbeat_runtime.py --continuous
-> carrier-side ensure_worker_presence
-> scripts/run_worker_runtime.py --continuous
-> WorkerCoordinator cycle
-> first iteration local source refresh
-> first iteration dispatch_local_resident_requests
-> scripts/dispatch_resident_execution_requests.py
-> healer_sovereign_scheduler
-> scripts/consume_healer_sovereign_scheduler_request.py
```

The native WorkerCoordinator dispatch cadence is not the blocker: `index` begins at zero, so the worker attempts resident-request dispatch on its first normal non-targeted iteration. Carrier-side supervision is also source-complete: any live continuous carrier checks worker presence from HB/AU sub-signal activity and at least every 100 observed references, and starts/recycles the same canonical `run_worker_runtime.py --continuous` process when absent or stale.

No deterministic source defect remains in this initiation chain. The current retained evidence is instead historical: `control/worker-runtime-state.json` records `last_cycle_at=2026-08-18T19:47:00Z`, `runtime_tick=2`, and `observation_mode=CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION`. No authentic post-repair `runtime-presence.latest.json` proving a fresh task-capable WorkerCoordinator cycle and no authentic `resident-request-dispatch.latest.json` proving a Healer visit are retained in canonical evidence.

Accordingly no code-path substitute is admissible:
- no alternate scheduler;
- no alternate runtime;
- no alternate dispatcher;
- no alternate WorkerCoordinator;
- no alternate carrier;
- no connected-device inventory dependency;
- no device prerequisite.

Fresh claim/fence, Master Records claim/fence custody, synthetic ingestion, and Site-successor derivation remain false.


## Native evidence re-observation — generation 162

Re-observation of canonical native evidence again found no authentic post-repair runtime progression:
- worker runtime state remains historical at `2026-08-18T19:47:00Z`, runtime tick `2`, observation-only;
- runtime-presence receipt absent;
- resident-request-dispatch receipt absent;
- machine-continuation receipt absent;
- Healer scheduler receipt absent;
- Healer registry remains `HANDOFF_READY` with `claim_id=null`.

The first missing authentic transition remains exactly `RESIDENT_REQUEST_DISPATCH_VISIT`. No downstream claim/fence, Master Records closure, synthetic ingestion, completion, or Site successor is promoted. No runtime/source path is modified.
