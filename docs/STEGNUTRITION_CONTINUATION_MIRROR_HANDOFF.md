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

The worker receives no GitHub token/provider credential/remote repository URL, performs no repository fetch, and writes only its admitted receipt namespace under a current heartbeat claim/fence. The registered entrypoint independently validates the emitted receipt contract before success can be returned.

## Current machine behavior

Each admitted heartbeat while unfinished validates the locally materialized StegNutrition tree, canonical v4 task inventory, offline deterministic tests, semantic model/evaluation source and qualified real-data artifact status, portion/pipeline/benchmark surfaces, real weighed benchmark cases, resident heartbeat epoch, and declared live visual-route evidence. It returns completion only when all release predicates are supported; otherwise it emits exact active solution/constraint evidence for continuation or escalation.

No general code-writing, GitHub repository-write, release or publication authority is granted.

## Important v4 correction

The worker is aligned to the current semantic and production surfaces:

```text
src/stegnutrition/semantic_food.py
src/stegnutrition/semantic_eval.py
scripts/train_semantic_food_local.py
tests/test_semantic_food.py
tests/test_semantic_eval.py
src/stegnutrition/vision/scale.py
src/stegnutrition/vision/auto_portion.py
src/stegnutrition/benchmark_ingest.py
scripts/ingest_weighed_photo_case.py
src/stegnutrition/pipeline.py
tasks/STEGNUTRITION-PRODUCTION-PIPELINE-019.json
```

## Receipt validation gate

```text
schema: schemas/stegnutrition-continuation-receipt.schema.json
contract: workers/stegnutrition_receipt_contract.py
validator CLI: tools/validate_stegnutrition_continuation_receipt.py
adapter entrypoint: workers/stegnutrition_continuation_entrypoint.py
adapter generation: 15
```

The contract rejects GitHub-token authority, repository fetches, non-TV/TVC credential authority, receipt path escape, unexpected task/schema identity, or false completion.

## Validation evidence

```text
heartbeat worker validation: run 31598640622 / SUCCESS
organization no-token validation: run 31598640713 / SUCCESS
heartbeat job: 94120233607 / SUCCESS
```

These prove source/control-plane behavior only, not a resident claim/fence or completed StegNutrition execution.

## Machine-observable activation condition

The last direct resident evidence is HB29 with no issued StegNutrition claim. Completion of the machine-continuation activation step requires heartbeat advance beyond HB29, registry fragment consumption, a current fenced claim, execution against a locally materialized StegNutrition tree, and an independently valid continuation receipt proving `github_token_required=false` and `github_repository_fetch_performed=false`.

If local materialization or another required predicate is absent, that condition must remain active solution work or derive/escalate a successor task; it is not a release to arbitrary manual implementation.

## Collision boundaries

- one heartbeat and one worker registry only;
- no fabricated heartbeat/claim/fence by repository writes;
- no GitHub-token or hosted production execution authority;
- workflow success is not resident activation;
- no bypass of receipt validation;
- semantic source is not a qualified real-data artifact;
- synthetic fixtures are not real accuracy data;
- no release/publication authority is granted to this worker.

## Cross-repository continuation

```text
StegVerse-Labs/StegNutrition/tasks/STEGNUTRITION-MACHINE-CONTINUATION-018.json
-> StegVerse-Labs/.github/handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json
-> resident heartbeat claim/fence
-> continuation entrypoint/worker/receipt contract
-> receipts/stegnutrition-continuation/SHWP-STEGNUTRITION-CONTINUATION-001.json
-> existing TV/TVC visual-route lane when applicable
-> StegNutrition release lane only after release-candidate predicates pass
```

## Execution ownership and collision partition

Standard: `StegVerse-Labs/Continuity/docs/REPOSITORY_HANDOFF_STANDARD.md` / `stegverse.handoff-execution-ownership/v1`.

### MANUAL / SESSION-STARTABLE

Human-authority real-data acquisition may occur only when a current StegNutrition task/handoff explicitly assigns that human role; it is not implementation authority over the continuation worker. No worker implementation or resident activation task is manually startable by default.

```yaml
- task_id: STEGNUTRITION-HUMAN-EVIDENCE-ROLE
  execution_owner: explicitly assigned human authority under the StegNutrition repository task state
  claim_state: UNCLAIMED
  worker_registry_ref: StegVerse-Labs/StegNutrition/STEGNUTRITION_MIRROR_HANDOFF.md
  manual_execution_allowed: true
  manual_allowed_role: validation
  collision_scope: acquisition/review of explicitly requested real photographed/weighed evidence only; excludes worker code, heartbeat, registry, TV/TVC route, release, and publication scope
  release_condition: evidence is durably ingested/validated or the StegNutrition task state withdraws the request
  next_executable_action: act only when the current StegNutrition handoff/task explicitly requests the bounded human evidence action
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: SHWP-STEGNUTRITION-CONTINUATION-001
  execution_owner: resident sovereign heartbeat + stegnutrition-machine-continuation worker
  claim_state: MACHINE_OWNED
  worker_registry_ref: control/worker-registry.d/stegnutrition-continuation-001.json
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: continuation worker/entrypoint/receipt execution, resident claim/fence, local validation, visual-route observation, and machine continuation receipt mutation
  release_condition: canonical worker completes/supersedes/releases the task under a live resident claim/fence
  next_executable_action: resident heartbeat executes the registered continuation task and persists a valid receipt
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: STEGNUTRITION-CONTINUATION-CONSTRAINT-RESOLUTION
  execution_owner: engine-v11 authority chain + applicable TV/TVC/StegNutrition authority
  claim_state: ESCALATED
  worker_registry_ref: control/worker-registry.json + docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md + StegVerse-Labs/StegNutrition/STEGNUTRITION_MIRROR_HANDOFF.md
  manual_execution_allowed: false
  manual_allowed_role: NONE
  collision_scope: local materialization, runtime capability, route/admission, model-quality, or evidence constraints not resolvable by the current worker
  release_condition: next capable authority resolves the constraint or explicitly assigns a bounded human-authority action
  next_executable_action: derive/register successor RESOLVE/ESCALATE work; never substitute GitHub fetch/token authority
```

### COMPLETED / SUPERSEDED

- v4 source alignment: complete.
- Receipt contract/validator: complete.
- Hosted no-token/source validation: complete.
- Chat-only continuation ownership: superseded by resident worker/task state.

## Archive condition

Machine continuation is now durably owned by the resident worker/registry path. Product completion and human evidence remain distinct predicates governed by current task state; incomplete machine work does not become manual implementation work.
