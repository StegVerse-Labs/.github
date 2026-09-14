# StegVerse

StegVerse is an open framework for rethinking how humans interact online as artificial intelligence becomes part of everyday life.

It focuses on **expectations, identity, boundaries, continuity, and replaceability** —  
**not** authority, control, or permanence.

StegVerse is **not** a platform, company, or governing body.  
It is a public collection of ideas, documentation, standards, and tools that anyone can read, fork, or ignore.

---

## What StegVerse Is

- A way to think about human–AI interaction without assuming AI is infallible
- A set of open standards and reference implementations
- A continuity-aware approach to identity, memory, and intent
- A framework designed to evolve, fork, or be replaced when better systems emerge

---

## What StegVerse Is Not

- ❌ Not a product  
- ❌ Not a social network  
- ❌ Not a governing authority  
- ❌ Not an AI platform  
- ❌ Not a final or permanent solution  
- ❌ Not a belief system  

Nothing here enforces behavior or claims moral authority.

---

## Core Principles

### Transparency over control
All work is public and inspectable. Nothing relies on secrecy or privileged access.

### Replaceability over permanence
Systems should be able to step aside when they no longer serve people well.

### Boundaries over assumptions
Clear limits and expectations matter more than raw capability.

### Continuity without gatekeeping
Identity, memory, and intent should survive change without locking the future into the past.

### Forking is a feature
Disagreement, reinterpretation, and improvement are expected and encouraged.

---

## Structure

StegVerse is organized into repositories that cover:

- Foundational principles and admissibility (`StegSeed`, `StegCore`)
- Identity and lineage (`StegID`, genealogy and continuity tooling)
- Documentation and archival continuity (`continuity-vault-kit`)
- AI agents and operational experiments
- Research, narrative, and long-form analysis
- Tooling for transparency, review, and survivability

Not all repositories are production software.  
Many are conceptual, documentary, or exploratory by design.

---

## Autonomous Governed Entity Progression

StegVerse distinguishes **governance** from **manual orchestration**.

For machine-owned entity work, authority is never inferred and never reused from a prior event. Every exact state change still requires the current applicable Interlock/InTr governance decision, with TV/TVC consulted when credential authority is required. A prior receipt proves a prior transition; it does not authorize the next one.

Once an exact machine-owned transition is currently admitted, the resident/entity runtime is expected to execute it, retain the resulting receipt, and reconstruct current state. **Before selecting another task, it must first check the current root Goal Task.** If that Goal Task has both `completion.claimed=true` and `completion.validated=true`, the current autonomous goal chain stops: no successor or adjacent work is selected in that cycle, and a TV/TVC-bound GitHub completion-notification request is emitted. Only when the Goal Task is not complete does the runtime select the next highest-priority admissible nonduplicate task scoped to that same goal and submit that transition for contemporaneous governance without inserting a human approval checkpoint between ordinary machine-owned cycles.

Within an incomplete Goal Task, StegVerse selects ecosystem **repair, remediation, canonicalization, reconciliation, correction, and regression-fix work first** when such work is admissible. That priority is applied before ordinary checkout-state ordering, so an unclaimed repair/canonicalization task may outrank an already-checked-out feature or expansion task. This is selection order only: collision checks, WorkerCoordinator claim/fence authority, current Interlock/InTr governance, TV/TVC credential authority, and Master Records reconstruction remain unchanged.

The completion notification is a GitHub-originated event, not a Gmail substitute and not a GitHub Actions authority path. Its issue body contains exactly six task-block header lines—`Goal Task ID`, `Handoff Task ID`, `COSV ID`, `Session Prompt Count`, `Goal Prompt Count`, and `STATUS`—and excludes `Summary of work` and `Manual Work`. Provider credential/mutation authority remains TV/TVC; GitHub Actions remains validation/evidence transport only. GitHub email delivery remains subject to the account's GitHub notification settings.

Human interaction is required only when the exact transition declares a human authority class such as `HUMAN_ONLY`, `USER_ONLY`, `LEGAL_PERSON_SIGNATURE`, or `OWNER_EXPLICIT_CONSENT`. Running on a user's iPhone does not by itself make a transition human-owned.

The canonical progression contract is:

```text
control/entity-autonomous-governed-progression-contract.json
```

with the scoped handoff:

```text
docs/ENTITY_AUTONOMOUS_GOVERNED_PROGRESSION_MIRROR_HANDOFF.md
```

The current-user iOS interaction queue serializes true human/device mutations only. It is not a scheduler, approval queue, WorkerCoordinator replacement, or authority source for machine-owned entity transitions.

SV001 Master Records custody/reconstruction is explicitly classified as a `MACHINE_GOVERNED` current-iPhone transition. Its former `IPHONE-MR-SV001-CUSTODY-001` human-action admission is superseded; the retained G23 receipt is evidence input, not authority. Custody still requires the exact contemporaneous Interlock/InTr governance transition and canonical Master Records processing, so removing it from the human interaction queue neither authorizes nor proves custody.

HeartBeat and HB-derived carriers remain timing/reference/freshness/correlation/carriage mechanisms only and grant no execution, admission, credential, routing, transition, claim/fence, custody, publication, receiving, or consequence authority.

### Canonical Work task ingress

Canonical Work task ingress applies to tasks that already exist in the canonical Task Registry. The existing resident Canonical Work consumer may visit multiple explicit task request specifications without creating a second dispatcher, WorkerCoordinator, scheduler, heartbeat, or oscillator. Each request binds the existing `task_id + task.v1 vector` to its registered source state before execution eligibility is evaluated.

The ingress mechanism does not create task identity, mint a WorkerCoordinator claim or fence, grant credentials, authorize an Interlock/InTr transition, or prove runtime execution. The Task Registry remains work-intent/coordination truth, WorkerCoordinator remains claim/fence authority, TV/TVC remains credential authority, Interlock/InTr remains governed transition authority, and Master Records remains observed-reality/reconstruction authority. Multiple explicit task request specifications therefore reuse the same resident ingress mechanism while preserving each task's exact identity and evidence predicates.

A newly registered canonical task may be present as an exact `data/canonical-task-records/<task_id>.json` shard before a preserved sovereign resident's monolithic `data/canonical-task-registry.json` has been refreshed. The generic Canonical Work resident consumer may self-materialize that exact source shard into the resident task-shard directory while preserving the existing monolithic registry. This is stale-registry recovery only: the shard must resolve the requested task identity exactly, and materialization does not create task identity or grant execution authority.

The dedicated `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` request uses this same Canonical Work consumer and shared Interlock/InTr ingress. Once its ordinary `PROPOSED -> INGRESS_ADMITTED` bootstrap succeeds, the existing bootstrap wrapper invokes the already-implemented global runtime-node-profile convergence visitor in measurement-only mode. That measurement path freezes one run identity and forbids same-run remediation or automatic retry after a lane's first failure; it does not create a second dispatcher, listener, runtime, scheduler, WorkerCoordinator, heartbeat, or authority source.

### KV AI WorkerCoordinator admission status

The adjacent task `SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001` records the non-authorizing admission-readiness path for `SV-KV-AI-PERSISTENCE-001`. Its canonical task record and admission status sidecar persist the runtime-resolution projection against `control/runtime-profile-map.json` generation 2 and record `WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED` when repository-visible WorkerCoordinator registry state has no fresh claim, worker instance, lease, or fence.

This clears only the source-visible admission-status predicate for the adjacent task. It does not complete `SV-KV-AI-PERSISTENCE-001`, does not mint a WorkerCoordinator claim or fence, and does not prove Interlock/InTr admission, provider/model execution, KV writeback/readback, or Master Records reconstruction.

Canonical source for the adjacent admission lane:

```text
data/canonical-task-records/SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001.json
data/workercoordinator-admission/SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001.json
docs/KV_AI_MEMORY_WORKERCOORDINATOR_ADMISSION_MIRROR_HANDOFF.md
```

### Fenced Personal-KV AI memory resident execution

Canonical Goal Task `SV-KV-AI-PERSISTENCE-001` reuses the existing resident dispatcher and WorkerCoordinator rather than creating a memory-specific scheduler or runtime owner. Its selector is `kv_ai_memory`; the resident request carries no private memory, prompt, credential, token, or provider-secret content.

Private working state lives under a fenced bound-state root:

```text
~/.stegverse/state/kv-ai-memory-resident/
  inputs/context-packet.json
  inputs/memory-packet-admission.json
  inputs/provider-request-input.json
  materialized/provider-request.json
  receipts/provider-request-materialization.json
```

The request consumer checks only whether the required private input paths exist. If they do not, it returns `BOUND_STATE_INPUT_NOT_READY` without consuming the request or attempting WorkerCoordinator execution. When they do exist, the existing WorkerCoordinator must still mint the current claim/fence before `ProcessWorkerAdapter` exposes a sandbox mirror of that state to `workers/kv_ai_memory_resident_worker.py`.

The worker delegates exact provider-request construction to the already-local `StegVerse-org/LLM-adapter` materializer and stops at `HANDOFF_READY / KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED`. That state proves no provider ingress, TV/TVC provider operation, model execution, provider egress, KV writeback, activation, or model authority. Those remain separate governed transitions and evidence predicates.

Canonical source for the resident lane:

```text
docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md
handoffs/SV-KV-AI-PERSISTENCE-001.json
control/worker-registry.d/kv-ai-memory-resident-001.json
control/process-worker-adapters.d/kv-ai-memory-resident-001.json
control/resident-execution-request.d/kv-ai-memory-resident-001.json
scripts/consume_kv_ai_memory_resident_request.py
workers/kv_ai_memory_resident_worker.py
```

### Bounded StegSocials Universal InTr ingress

Bounded StegSocials social publication reuses the same organization-owned, event-triggered Universal InTr listener rather than creating a separate social runtime or admission service. StegSocials first emits a secret-free `stegverse.universal-work-interlock/v1` `INGRESS/RECEIVED` record for one already-authorized bounded use. The `.github` organization owner binds that exact record into the existing `stegverse.universal-intr-materialization-request/v1` transport shape and routes it through the shared `workers/universal_intr_profiled_ingress.py` listener under the `StegSocials:BoundedSocialIngress` profile.

The source-side RECEIVED record is not an admission receipt. Only invocation by the authentic shared sovereign listener may emit the write-once `stegverse.stegsocials-bounded-intr-materialization-ingress/v1` `INGRESS_ADMITTED` receipt. That receipt proves the exact bounded work/group/use/content/platform/account request crossed the governed ingress transition; it does **not** grant publication/provider authority, resolve credentials, mint a WorkerCoordinator claim/fence, or prove provider execution. TV/TVC remains credential authority, and the admitted event proceeds next to task-scoped SKAP session materialization and the existing event-ephemeral StegBrowser path.

The route is installed idempotently into the existing shared listener, starts no second listener/scheduler/heartbeat/WorkerCoordinator, requires no persistent transport runtime or always-on application receiver, and permits durable queue or event-ephemeral materialization when the receiver is unavailable. Raw credentials are prohibited. Node-outbox wrappers are rejected unless their exact wrapper hash/identity contract is separately validated; no node/interlock identity may be inferred from an unverified wrapper.

Canonical source for this lane:

```text
scripts/build_stegsocials_bounded_intr_materialization.py
workers/stegsocials_bounded_intr_ingress.py
scripts/install_stegsocials_bounded_universal_intr_route.py
docs/STEGSOCIALS_BOUNDED_INTR_ADMISSION_ROUTE_MIRROR_HANDOFF.md
```

### Cross-task runtime-presence evidence

Cross-task runtime-presence evidence is subject-bound observation, not generic proof that arbitrary work executed. shared cross-task reuse is currently deferred until authentic subject binding identifies the relevant `runtime_root`, `resident.node_id` when available from authentic runtime evidence, and the canonical worker runtime identity.

A process-alive or runtime-presence receipt does **not** prove that a specific request was consumed, that a task executed, or that its completion predicate was satisfied. HeartBeat remains non-authorizing: heartbeat/oscillator evidence can support timing, freshness, correlation, and observation, but cannot grant execution, admission, claim/fence, credential, routing, transition, custody, publication, or completion authority.

### Independent post-terminal SV001 evidence continuation

The registered continuation task `STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001` is independently selectable by the existing WorkerCoordinator after the canonical SV001 execution is already terminal. This prevents downstream Master Records/SV002 evidence progression from being coupled only to retries of the parent SV001 consumer.

The dedicated binding reuses the existing HB32/self-heal/local-source-refresh runtime and `scripts/continue_stegverse001_evidence_chain.py`. It does **not** rerun terminal SV001, create another heartbeat, oscillator, scheduler, WorkerCoordinator, custody authority, or human approval loop. A WorkerCoordinator claim/fence only admits the continuation worker to execute its bounded task; every new custody state change still requires its own current Interlock/InTr decision, TV/TVC remains credential authority, and Master Records remains custody/reconstruction authority.

If the continuation returns a retryable evidence state, the worker returns `HANDOFF_READY` so the existing machine runtime can retry later. It reports `COMPLETED` only when the canonical continuation itself returns `PASS`. Source registration, worker selection, HB32 progression, or a prior SV001 receipt cannot substitute for the required downstream runtime evidence.

### Active task problem/solution semantics

Problems and constraints are metadata, not an operational stopping state. A canonical unresolved task remains active or machine-owned while the current owner attempts a solution within its authority ceiling, derives a successor task, or transfers/escalates through the existing governed mechanism. `BLOCKED` is therefore not a canonical Task Registry `coordination_state`; dependency, problem/constraint, incident, and evidence metadata carry the reason a particular transition cannot yet proceed. Historical receipts or domain-specific schemas may retain older labels as provenance, but those labels do not create a current operational stopping state.

### Human-originated intent and autonomous goal resolution

The human originates an **idea, query, or goal**. After that intent is admitted, the ecosystem owns machine-executable continuation: task decomposition, Task/COSV continuity, handoff resolution, evidence reconciliation, dependency and collision resolution, parallel regrouping, and next-admissible-work selection continue without requiring the human to copy intermediate Task IDs, COSV vectors, or `*_MIRROR_HANDOFF.md` identifiers back into another prompt.

Returned identifiers are orchestration state, not automatically new jobs. The ecosystem first resolves them against canonical active/completed work, verifies Task/COSV binding when present, resolves the applicable handoff, reconciles Master Records evidence, and checks the current root Goal Task completion state. A Goal Task whose completion is both claimed and validated is terminal for that autonomous goal cycle: continuation stops, no successor/adjacent task is selected before the completion notification request, and retirement may occur later as archival lifecycle work. If the Goal Task is not complete, the ecosystem checks WorkerCoordinator claim/fence ownership, classifies continuation versus successor/dependency/adjacency/new work, deduplicates equivalent work, resolves repository/runtime/authority/evidence collisions, regroups parallel-capable work, prioritizes admissible ecosystem repair/remediation/canonicalization work, and then selects the next admissible nonduplicate task scoped to the same goal.

The default consolidated user-facing report interval is **five orchestration iterations**. Reaching that interval may surface a report but **does not stop admitted machine-owned work**. Reporting and execution continuation are separate semantics. The ecosystem surfaces earlier when the governed Goal Task reaches validated completion or when an explicit progression condition requires human action, including `HUMAN_ONLY`, `USER_ONLY`, legal-person signature/consent, a no-repair DENY, a genuinely unavailable required runtime with no admitted local materialization, or an unreconstructable current-state invariant.

Intermediate conditions such as an unchanged Task ID, successor Task ID, updated COSV vector, new handoff, validation failure with an admissible repair, newly exposed dependency, adjacent task, or integration candidate do not by themselves create a human checkpoint.

The deterministic non-authorizing evaluator is `scripts/evaluate_goal_resolution_continuation.py`. It does not schedule work or grant authority; it classifies whether the current cycle continues autonomously, reports-and-continues at the bounded cadence, surfaces human review, surfaces terminal completion, or fails closed for a no-repair machine stop. The resident registry cycle additionally enforces the completion-first stop and repair/remediation/canonicalization-first ordering before selecting more work. WorkerCoordinator, Interlock/InTr, TV/TVC, and Master Records retain their existing separated authorities.

### COSV task-pointer session continuation

A StegVerse continuation prompt should carry only the canonical task identity and its current COSV `task.v1` vector when those values are available:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

The task ID is the stable identity. The 14-position COSV vector is the compact current-state projection. The receiving session or runtime resolves the task's canonical registry record, source vector, applicable `*_MIRROR_HANDOFF.md` documentation, Master Records evidence, WorkerCoordinator claim/fence state, cross-task relationships, runtime requirements, receipts, and other canonical evidence from those two values rather than repeating that information in prompt prose.
