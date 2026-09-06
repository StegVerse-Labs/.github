# HIL Resident Session Cohort Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Primary canonical task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Parent handoff: `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`
Machine preflight: `receipts/preflight/HIL-RESIDENT-SESSION-COHORT-20260906.json`

## Purpose

This handoff records the exact existing task identifiers that may be worked in one StegVerse resident-runtime session without merging their authority, claims, fences, completion predicates, or lifecycle semantics.

It does not create a new task, runtime, heartbeat, oscillator, WorkerCoordinator, scheduler, dispatcher, claim/fence plane, credential route, or transition authority.

## Canonical HIL state

```text
task_id: SHWP-HIL-SOVEREIGN-RECEIVER-001
resident_request: RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
worker_state: HANDOFF_READY
cross_task_predicate: PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002
cross_task_predicate_state: UNKNOWN
authentic_runtime_execution_observed: false
Master_Record_release_ready: false
credential_authority: TV/TVC
GitHub_token_runtime_authority: NONE
same_device_execution_required: true
requires_other_machine: false
```

The acceptance-evidence repair merged in `.github` PR #1112 requires authentic dispatcher + HIL resident-consumption evidence before the first resident activation segment may report `PASS`. Source, merge, CI, heartbeat progression, materialization alone, or receiver source readiness cannot substitute for request consumption.

## Task registry identifiers

### Primary task

```text
SHWP-HIL-SOVEREIGN-RECEIVER-001
```

Registry surfaces:

```text
handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
control/worker-registry.d/hil-sovereign-receiver-001.json
control/task-vectors/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
control/task-vector-index.json
```

### Related work that can be combined into one resident-runtime session

The following existing identifiers share the same sovereign resident execution substrate or are explicitly listed in the canonical targetable machine-task cohort. Combining them into one session means resolving and visiting them together where their existing dispatcher/executor supports it; each task still requires its own admission, claim/fence or dedicated execution semantics, evidence, and terminal predicates.

```text
SHWP-HIL-SOVEREIGN-RECEIVER-001
COSV-LIVE-PACKET-AUTOMATION-006
SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
SHWP-TV-TVC-RESIDENT-PROOF-001
SHWP-DURABLE-RUNTIME-ACTIVATION
SHWP-ECOSYSTEM-CHAT-INFERENCE-001
```

Relationship notes:

- `SHWP-HIL-SOVEREIGN-RECEIVER-001` is the primary HIL task and uses the existing resident HIL consumer/targeted executor.
- `COSV-LIVE-PACKET-AUTOMATION-006`, `SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001`, `SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001`, and `SHWP-TV-TVC-RESIDENT-PROOF-001` are explicitly listed with HIL in the canonical generic targeted one-shot cohort in `docs/COSV_SESSION_CONSOLIDATION_MIRROR_HANDOFF.md`.
- `SHWP-DURABLE-RUNTIME-ACTIVATION` is cross-task related through the same resident substrate and its own canonical request-consumption predicate, but HIL does not depend on G18 completion and must not consume G18's claim/fence.
- `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` is cross-task related through the same resident runtime session, but retains its dedicated parent executor and its own request-consumption predicate; it is not converted into HIL's generic targeted path.

## Cross-task predicates to preserve separately

```text
PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002
PRED-RESIDENT-REQUEST-CONSUMED-G18-RESUME-FENCE18-001
PRED-RESIDENT-REQUEST-CONSUMED-ECOSYSTEM-CHAT-PARENT-002
```

These predicates are coordination/evidence relationships only. One becoming satisfied does not satisfy either of the others.

## Session-combination invariant

```text
one resident session
!= one shared task authority
!= one shared claim/fence
!= one shared completion predicate
```

The resident dispatcher may visit independent consumers in one session. A failure or wait-state in one independent task must not fabricate success or authority for another task. HIL remains independently admitted under its own task identity and evidence chain.

## Current highest-priority HIL transition

The first missing HIL predicate remains authentic consumption of `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` on the existing same-device resident path, followed by authentic ESRL `LEASE_OPEN`, a real WorkerCoordinator claim/fresh fence, HIL receiver READY, receiver/custody evidence, controlled browser receipt, restart exact-byte reconstruction, TVC lifecycle receiving/admission, and eventually Master Records release eligibility.

No additional source implementation is required to manufacture that evidence. The existing HB32/WorkerCoordinator/dispatcher/HIL-consumer/targeted-execution path must produce it authentically.

## Master Records boundary

`StegVerse-Labs/Site/docs/HIL_FIRST_MASTER_RECORD_RELEASE_PREPARATION.md` remains fail-closed. Session grouping does not authorize custody, reconstruction, release, orchestration submission, private review, publication, or public acquisition.

## README completeness

This file is coordination/documentation reconciliation only. It records already-existing identifiers and relationships and changes no repository behavior, runtime semantics, interface, governance/authority boundary, evidence semantics, prerequisite, dependency, failure behavior, or capability meaning. `README.md` therefore requires no additional change for this handoff; the material resident HIL acceptance-evidence behavior is already documented there from PR #1112.

## Copy/paste task registry block

```text
<task registry identifier and related identifiers>
PRIMARY_TASK_REGISTRY_IDENTIFIER=SHWP-HIL-SOVEREIGN-RECEIVER-001
RELATED_TASK_REGISTRY_IDENTIFIERS=COSV-LIVE-PACKET-AUTOMATION-006,SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001,SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001,SHWP-TV-TVC-RESIDENT-PROOF-001,SHWP-DURABLE-RUNTIME-ACTIVATION,SHWP-ECOSYSTEM-CHAT-INFERENCE-001
PRIMARY_RUNTIME_PREDICATE=PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002
RELATED_RUNTIME_PREDICATES=PRED-RESIDENT-REQUEST-CONSUMED-G18-RESUME-FENCE18-001,PRED-RESIDENT-REQUEST-CONSUMED-ECOSYSTEM-CHAT-PARENT-002
SESSION_COMBINATION_AUTHORITY_EFFECT=NONE_COORDINATION_ONLY
</task registry identifier and related identifiers>
```
