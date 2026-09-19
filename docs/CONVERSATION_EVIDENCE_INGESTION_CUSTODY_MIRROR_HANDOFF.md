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
