# KV AI WorkerCoordinator Claim/Fence Observer

Goal Task ID: `SV-KV-AI-PERSISTENCE-001`  
COSV task.v1: `20111110110000`  
Owner issue: `StegVerse-Labs/.github#1848`  
Canonical handoff: `docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md`

## Purpose

`scripts/evaluate_kv_ai_workercoordinator_claim_fence_observation.py` records the first missing same-execution predicate for this task as a deterministic observer instead of prose-only inspection:

```text
AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVATION
```

The observer accepts only an already-existing resident runtime claim/fence tuple when the following evidence surfaces agree in the same execution:

```text
receipts/sovereign-host/resident-targeted-execution.latest.json
control/worker-registry.json
events/master-records-worker-assignment.jsonl
```

## Acceptance rule

The observer returns `AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED` only when all of these are true:

```text
task_id == SV-KV-AI-PERSISTENCE-001
cosv_task_vector == 20111110110000
mode == TARGETED_INDEPENDENT_TASK_CONTROL
runtime_execution_attempted == true
same execution event == worker_assignment_bound_from_independent_task_control
claim_id is present
worker_id == kv-ai-memory-resident-worker
fresh fencing_token is present
registry task is ACTIVE
registry worker_instance_id is present
assignment_timer claim/fence/worker_instance tuple matches registry + event
Master Records worker-assignment row matches task_id + claim_id + fencing_token + worker_instance_id
```

If any predicate is absent or mismatched, it returns `AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED` with a machine-readable `missing_predicates` list.

## Authority boundary

This observer does not mint a claim, mint a fence, create a lease, create an assignment timer, authorize execution, authorize InTr admission, prove Personal-KV input, prove ProviderRequest materialization, prove provider/model ingress-response-egress, prove KV writeback/readback, or complete `SV-KV-AI-PERSISTENCE-001`.

Hosted tests validate the observer logic only. A real observed claim/fence still requires owner-custodied resident runtime evidence.
