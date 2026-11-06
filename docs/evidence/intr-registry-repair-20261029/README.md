# InTr Registry repair diagnostic — 2026-10-29

Goal: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`; COSV `50000000102000`.
Source: Labs main `6b13c3a749b2940d6142644196a8302823c1f45a`, generation 322,
120 aggregate rows, task omitted. Shard blob `a6cd7003ff8088749337d2e2c970c728c6757670`.
Evidence class: local source diagnostic and isolated apply rehearsal. Authority effect NONE.
No canonical Registry, shard, vector, claim, fence, ledger or private-runtime mutation.

## Executed findings

| Case | Exact result | Meaning |
|---|---|---|
| 01 live existing-identity plan | FAIL_CLOSED / CANONICAL_RECORD_SCHEMA_INVALID | Explicit task_registry_mints_execution_authority=false absent. |
| 02 prescribed row_fields repair plan | FAIL_CLOSED / RECORD_DATA_TASK_NOT_IN_AGGREGATE_REGISTRY | The previous repair instruction cannot operate on this omitted shard alone. |
| 03 hypothetical explicit false | FAIL_CLOSED / COSV_NOT_DERIVABLE | Planner reads top-level cosv_task_vector, while this legacy shard records nested cosv.vector. |
| 04 hypothetical false + existing-vector projection | ALLOW, collision check-in ALLOW | Same recorded 50000000102000, no metrics invented. Residual schema, claim and exact-metrics evidence remain. |
| 05 atomic record-data plan | ALLOW, proposed generation 323, files_changed=false | Existing register_from_record plus three exact row_fields edits resolves the bootstrap cycle in one existing transition. |
| 06 isolated atomic apply | ALLOW, files_changed=true in throwaway worktree only | All seven native validators and every-task handoff projection passed (the apply entrypoint returns only after them). |
| 07 isolated re-apply | NO_CHANGE | Idempotent at the same tip reference. |
| 08 independent collision gate | ALLOW / CONTINUE for this task | Native unmodified evaluator over original versus isolated successor; event ledger empty. |

Inputs and raw outputs are retained beside this file. Case 04's ALLOW is a hypothetical
predecessor test; it is not an apply-ready live request. Case 05 is an existing record-data
route **proposal for the Registry owner**, not permission to bypass that owner's choice
of registration transition. Its generation 323 was only rehearsed and is not reserved.
The apply worktree's Registry and shard were restored byte-for-byte afterward.

## Exact proposed data change

`05-atomic-record-data-route.input.json` asks the existing transition to:

1. Project the existing shard into its omitted aggregate row with register_from_record.
2. Replace authority_model with exactly the existing object plus
   task_registry_mints_execution_authority=false.
3. Add cosv_task_vector and source_state_vector_ref copied from the same shard's
   already-recorded nested cosv values. No vector value is allocated or re-derived.

Everything else remains as observed, including ACTIVE, null claim/fence and
completion.claimed=false / validated=false. The native registration diagnostic
continues to report CANONICAL_RECORD_SCHEMA_SUCCESSOR_REQUIRED,
CLAIM_NOT_ISSUED_BY_WORKERCOORDINATOR and COSV_EXACT_METRICS_NOT_OBSERVED.
A test of those residuals is not evidence that they are resolved.

## Reproduction and owner action

On the pinned source in an isolated worktree, run the native entrypoints using
this directory's retained inputs. Cases 01/03/04 use
`python scripts/canonical_task_registration_transition.py plan --request INPUT --base .`.
For cases 03/04 only, the isolated shard must equal INPUT.record before planning;
restore it after the diagnostic. Never apply these hypothetical requests to live state.
Cases 02/05 use
`python scripts/apply_task_record_data.py INPUT --tip-ref 6b13c3a749b2940d6142644196a8302823c1f45a`.
The case 06 rehearsal adds --apply for the case 05 input in an isolated worktree;
case 07 repeats it, then case 08 runs
`python scripts/check_registry_collision_checkin.py --base-root ORIGINAL --head-root REHEARSAL`.

Registry owner: adjudicate this existing atomic record-data route versus an explicit
shard-repair successor followed by native registration. Refresh live generation and
all before values, preserve this exact recorded identity, serialize the authorized
transition, run native validators/collision/readback on its actual committed head,
then record the documentary validation and cumulative-count disposition.
Do not retire the task, invent a successor, or infer private-runtime authority from
this diagnostic. A separate accepted owner ruling is still required.

Fresh session count 1; cumulative recovery lower bound 33/20; exact total unknown.
The lower bound extends #2897 comment 6504413293 (32) by this one qualifying prompt.
No counter reset, exact-total assertion, canonical count disposition or release.
