# StegNutrition Machine Continuation Mirror Handoff

## Authority and scope

This scoped handoff is authoritative only for `SHWP-STEGNUTRITION-CONTINUATION-001` and is subordinate to `docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md` and `docs/ORG_MIRROR_HANDOFF.md`. It does not supersede another lane's heartbeat-hardening authority.

```text
goal_id: STEGNUTRITION-PHOTO-DIET-001
heartbeat_task: SHWP-STEGNUTRITION-CONTINUATION-001
repository: StegVerse-Labs/.github
branch: main
canonical_target: StegVerse-Labs/StegNutrition/STEGNUTRITION_MIRROR_HANDOFF.md
canonical_target_inventory: StegVerse-Labs/StegNutrition/tasks/STEGNUTRITION-SESSION-20260811.json
canonical_inventory_schema: stegnutrition.session-execution-inventory.v4
credential_authority: TV/TVC
route_authority: StegVerse-Labs/TVC
github_token_runtime_authority: NONE
source_state: INSTALLED_VALIDATED_V4_ALIGNED_RECEIPT_GATED
resident_activation_state: PENDING_DIRECT_OBSERVATION
last_directly_observed_resident_epoch: 29
```

## Originating requirement

Archiving a chat must not reduce StegNutrition continuation to a dormant JSON reminder. Eligible machine work must be repeatedly rechecked and executed by the existing single sovereign heartbeat when repository-native execution is possible. Human-authority evidence acquisition and model-quality boundaries remain explicit and may not be fabricated as autonomous success.

## Installed source

```text
handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json
control/worker-registry.d/stegnutrition-continuation-001.json
workers/stegnutrition_continuation_entrypoint.py
workers/stegnutrition_continuation_worker.py
workers/stegnutrition_receipt_contract.py
schemas/stegnutrition-continuation-receipt.schema.json
tools/validate_stegnutrition_continuation_receipt.py
control/process-worker-adapters.json#process:stegnutrition-machine-continuation-v1
control/worker-capability-profiles.json#sovereign-runtime-worker-v1
cost-basis/worker-runtime/stegnutrition-machine-continuation.json
tests/test_stegnutrition_machine_continuation.py
tests/test_stegnutrition_continuation_receipt.py
```

The worker uses only `STEGVERSE_STEGNUTRITION_ROOT` from the process environment. It never receives `GITHUB_TOKEN`, `GH_TOKEN`, provider credentials or a remote repository URL. It does not fetch source. It writes only `receipts/stegnutrition-continuation/**` under a current heartbeat claim/fence.

The process adapter invokes `workers/stegnutrition_continuation_entrypoint.py`, not the raw worker directly. The entrypoint runs the worker, resolves the emitted checkpoint only inside `receipts/stegnutrition-continuation/**`, independently validates the receipt contract, and returns nonzero if the receipt is malformed or violates the no-token/authority invariants. A syntactically written JSON file is therefore not sufficient for successful continuation.

## Current machine behavior

Each admitted heartbeat while unfinished:

1. requires an already locally materialized StegNutrition root containing the canonical handoff and inventory;
2. normalizes either legacy inventory rows or the canonical v4 inventory sections;
3. requires the canonical continuation tasks `012` through `019` that remain relevant to release;
4. runs fixed local `python -m pytest -q` with `PIP_NO_INDEX=1` and no credential environment; StegNutrition now carries a repository-owned zero-network pytest compatibility runner for its audited test surface;
5. separately projects whether semantic training/evaluation source exists and whether a qualified real-data semantic artifact exists;
6. observes automatic scale/portion source, production photo-to-ledger pipeline source and benchmark-ingestion source;
7. counts real photographed/weighed benchmark records without counting synthetic mechanics fixtures as real accuracy;
8. observes the resident heartbeat epoch and requires an exact declared live visual-route activation receipt after HB29;
9. constructs a fenced continuation receipt;
10. independently validates receipt schema, task/claim/fence fields, local validation state, credential authority, explicit `github_token_required=false`, explicit `github_repository_fetch_performed=false`, and completed/blocker consistency;
11. persists only the admitted continuation receipt;
12. returns `COMPLETED` only when all release-candidate predicates are directly supported; otherwise returns `BLOCKED`, `RETRY` or `FAILED` with an exact next solution action.

No general code-writing, GitHub repository-write, release or publication authority is granted.

## Important v4 correction

The original worker expected a historical `execution_inventory` list and old semantic source names (`src/stegnutrition/vision/semantic.py`, `tests/test_semantic_vision.py`). StegNutrition evolved to the v4 inventory and the actual local semantic implementation is now:

```text
src/stegnutrition/semantic_food.py
src/stegnutrition/semantic_eval.py
scripts/train_semantic_food_local.py
tests/test_semantic_food.py
tests/test_semantic_eval.py
```

The worker was corrected in commit `a9cdd727124591f7f54b7e76122e6b0fa5b5be9f`; its contract tests were updated in `850f2836d7a5cfdb27e0f8b46918d8467ac38190`.

It now also observes:

```text
src/stegnutrition/vision/scale.py
src/stegnutrition/vision/auto_portion.py
src/stegnutrition/benchmark_ingest.py
scripts/ingest_weighed_photo_case.py
src/stegnutrition/pipeline.py
tasks/STEGNUTRITION-PRODUCTION-PIPELINE-019.json
```

This correction prevents the first resident execution from failing simply because the machine continuation source lagged behind the repository it was meant to continue.

## Receipt validation gate

The continuation receipt type is now independently specified and validated:

```text
schema: schemas/stegnutrition-continuation-receipt.schema.json
contract: workers/stegnutrition_receipt_contract.py
validator CLI: tools/validate_stegnutrition_continuation_receipt.py
adapter entrypoint: workers/stegnutrition_continuation_entrypoint.py
adapter generation: 15
```

The contract rejects a receipt if it asks for GitHub-token authority, claims a repository fetch, changes credential authority away from TV/TVC, escapes the admitted receipt namespace, uses an unexpected task/schema, or marks itself completed while retaining a blocker or non-COMPLETE local validation state.

## Validation evidence

Current validation head: `6de8e62bc08c7bb6752e86d5fc94fc745ca44570`.

```text
heartbeat worker validation: run 31598640622 / SUCCESS
organization no-token validation: run 31598640713 / SUCCESS
heartbeat job: 94120233607 / SUCCESS
validated heartbeat steps:
  Anonymous public checkout without GitHub token — SUCCESS
  Prove validation environment has no GitHub credential token — SUCCESS
  Compile runtime, workers, and scripts — SUCCESS
  Parse canonical JSON surfaces — SUCCESS
  Validate executable handoffs — SUCCESS
  Run complete deterministic repository test suite — SUCCESS
  Prove heartbeat dry-run cannot persist registry or epoch state — SUCCESS
  Rebuild projections ephemerally without repository persistence — SUCCESS
  Prove workflow itself is non-authorizing — SUCCESS
```

The deterministic repository suite includes the StegNutrition continuation adapter/receipt tests. These are source/control-plane validation proofs only. They do not prove a resident claim/fence or StegNutrition execution.

## Canonical StegNutrition predicates now observed by the worker

```text
semantic_model_source_present
semantic_model_qualified_artifact_present
automatic_portion_surfaces_present
production_pipeline_surfaces_present
benchmark_ingestion_surfaces_present
real_weighed_benchmark_case_count
resident_heartbeat_epoch
live_visual_route_receipt_declared
local_validation.state
```

A qualified semantic artifact requires real-data model/evaluation artifacts under `models/semantic-food/`; source presence alone cannot satisfy it.

## Machine-observable activation blocker

```text
blocker: STEGNUTRITION_CONTINUATION_RESIDENT_CLAIM_NOT_YET_OBSERVED
owner: single resident StegVerse heartbeat
current direct evidence: control/heartbeat-state.json epoch 29 / generation 29 / no StegNutrition issued claim
release_condition:
  resident heartbeat advances beyond HB29;
  registry fragment SHWP-STEGNUTRITION-CONTINUATION-001 is consumed;
  stegnutrition-machine-continuation adapter receives a current fenced claim;
  worker executes against a locally materialized StegNutrition tree;
  receipt receipts/stegnutrition-continuation/SHWP-STEGNUTRITION-CONTINUATION-001.json is produced and independently validates;
  receipt proves github_token_required=false and github_repository_fetch_performed=false.
```

The resident heartbeat must use a locally materialized StegNutrition tree. If absent, the worker remains `BLOCKED` with a local-materialization action and may not substitute a GitHub fetch.

## Collision boundaries

- do not create a second heartbeat or registry;
- do not fabricate HB30 or a claim/fence through repository writes;
- do not use GitHub tokens or GitHub Actions as production execution authority;
- do not treat workflow success as resident activation;
- do not bypass the receipt-validation entrypoint by invoking the raw worker as the registered adapter;
- do not treat semantic source presence as a qualified real-data model artifact;
- do not treat low-level visual evidence as semantic food recognition;
- do not treat synthetic benchmark fixtures as real accuracy data;
- do not grant release/publication authority to this worker.

## Cross-repository continuation

```text
StegVerse-Labs/StegNutrition/tasks/STEGNUTRITION-MACHINE-CONTINUATION-018.json
-> StegVerse-Labs/.github/handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json
-> resident heartbeat claim/fence
-> workers/stegnutrition_continuation_entrypoint.py
-> workers/stegnutrition_continuation_worker.py
-> workers/stegnutrition_receipt_contract.py
-> receipts/stegnutrition-continuation/SHWP-STEGNUTRITION-CONTINUATION-001.json
-> existing TV/TVC visual-route lane when applicable
-> StegNutrition release lane only after release-candidate predicates pass
```

## Archive condition

This session remains distinct support until a resident continuation claim/receipt is directly observed or equivalent canonical sovereign activation evidence supersedes this task. Once that happens, this chat is not required merely to keep machine-executable StegNutrition work checking itself. Product completion and human-authority data acquisition remain separate predicates.
