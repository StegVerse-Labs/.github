# Canonical Task Registration: Discovery and Authority Boundary

Owner issue: https://github.com/StegVerse-Labs/.github/issues/3195
Status: DOCUMENTATION / DISCOVERY ONLY — NOT AN ADMISSION RECEIPT.

## Start here
The ecosystem canonical task coordination source is `StegVerse-Labs/.github:data/canonical-task-registry.json`. Individual task records are under `data/canonical-task-records/`; shards are not a replacement for the aggregate Registry. Organization-specific work intent may also be disclosed from `StegVerse-org/.github:orchestration/task-registry.json` through the manifest-admitted `resident-runtime/task_registry_disclosure_endpoint.py`. **Do not conflate these two registries.** A disclosure digest proves the disclosed content, not task admission.

1. Inspect the current canonical aggregate Registry and `scripts/query_canonical_tasks.py` (read-only topic query). If aggregate retrieval is unavailable, inspect relevant shards to diagnose, but do not claim a complete collision check.
2. Identify an existing owner Goal Task, issue, handoff, and COSV. Use `scripts/evaluate_task_registry_collision_checkin.py` to evaluate candidate collisions against current canonical data. Do not infer a unique identity from a search result.
3. For a genuinely new Goal Task, submit a scoped proposal to the canonical Registry owner with requested goal, owning repository/issue, targets, existing-task collision analysis, proposed handoff, required evidence, dependencies and next admissible transition. The owner must establish any new canonical ID/COSV and amend the canonical Registry and matching task record through the existing governed process. A proposal or GitHub issue is not admission.
4. Re-read the committed Registry and exact task shard, record generation, source commit, identity/COSV, owner issue, and admission/transition evidence. If these do not agree, return an actionable non-ALLOW disposition.
5. Only an already-registered HANDOFF_READY task proceeds to `heartbeat_runtime/worker_task_admission.py` for fresh `ADMIT | UPDATE | RETIRE | BLOCK` review. `ADMIT` permits existing WorkerCoordinator assignment checks; it does not mint a claim/fence or authorize execution. Actual state transitions independently return `ALLOW | DENY | FAIL_CLOSED` under applicable manifest, InTr and Master Records authority.

## Capability discovery
The organization service declaration lives at `StegVerse-org/.github:org-boundary/registry/services.json`. `resident-runtime/capability_demonstration_projection.py` derives observed capability evidence and does not declare or authorize new capabilities. The organization `task_registry_disclosure_endpoint.py` is an existing read-only diagnostic path, not a write or registration endpoint. Any future registration capability declaration must be added by its actual capability owner using the existing service/profile mechanism and validated bindings; never invent a route or bypass the SDK.

## Failure and retry
If the complete Registry cannot be read or collision checked, return `FAIL_CLOSED` with predicate `CANONICAL_REGISTRY_READBACK_OR_COLLISION_CHECK_UNVERIFIED`, the attempted source reference, owner issue, repair requirement (restore complete current readback or authorized collision check), and retry entrypoint `scripts/query_canonical_tasks.py` / `scripts/evaluate_task_registry_collision_checkin.py`. Do not allocate an ID/COSV, start a claim, or convert the defect into an indefinite external-machine wait.

This guide is a navigation aid; current canonical contracts and owner-approved transitions supersede it.
