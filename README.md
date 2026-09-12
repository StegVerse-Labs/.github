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

Once an exact machine-owned transition is currently admitted, the resident/entity runtime is expected to execute it, retain the resulting receipt, reconstruct current state, select the next highest-priority admissible nonduplicate task, and submit that next transition for its own contemporaneous governance **without inserting a human approval checkpoint between ordinary machine-owned cycles**.

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

Returned identifiers are orchestration state, not automatically new jobs. The ecosystem first resolves them against canonical active/completed work, verifies Task/COSV binding when present, resolves the applicable handoff, reconciles Master Records evidence, checks WorkerCoordinator claim/fence ownership, classifies continuation versus successor/dependency/adjacency/new work, deduplicates equivalent work, resolves repository/runtime/authority/evidence collisions, and then regroups parallel-capable work.

The default consolidated user-facing report interval is **five orchestration iterations**. Reaching that interval may surface a report but **does not stop admitted machine-owned work**. Reporting and execution continuation are separate semantics. The ecosystem surfaces earlier when the governed goal reaches terminal completion or when an explicit progression condition requires human action, including `HUMAN_ONLY`, `USER_ONLY`, legal-person signature/consent, a no-repair DENY, a genuinely unavailable required runtime with no admitted local materialization, or an unreconstructable current-state invariant.

Intermediate conditions such as an unchanged Task ID, successor Task ID, updated COSV vector, new handoff, validation failure with an admissible repair, newly exposed dependency, adjacent task, or integration candidate do not by themselves create a human checkpoint.

The deterministic non-authorizing evaluator is `scripts/evaluate_goal_resolution_continuation.py`. It does not schedule work or grant authority; it classifies whether the current cycle continues autonomously, reports-and-continues at the bounded cadence, surfaces human review, surfaces terminal completion, or fails closed for a no-repair machine stop. WorkerCoordinator, Interlock/InTr, TV/TVC, and Master Records retain their existing separated authorities.

### COSV task-pointer session continuation

A StegVerse continuation prompt should carry only the canonical task identity and its current COSV `task.v1` vector when those values are available:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

The task ID is the stable identity. The 14-position COSV vector is the compact current-state projection. The receiving session or runtime resolves the task's canonical registry record, source vector, applicable `*_MIRROR_HANDOFF.md` documentation, Master Records evidence, WorkerCoordinator claim/fence state, cross-task relationships, runtime requirements, receipts, and other canonical evidence from those two values rather than repeating that information in prompt prose.

When work on an existing task or goal exposes a distinct necessary piece of work that is not already canonically tracked, the system should first search for equivalent or adjacent work and reuse it when present. If the work is genuinely new, it should create a new adjacent canonical task tied to the same root correlation/goal, give that task its own COSV vector and handoff/evidence relationships, and continue through the ordinary WorkerCoordinator, Interlock/InTr, Master Records, and TV/TVC roles. New task creation is coordination only and grants no execution authority.

The canonical contract is `data/task-coordination-policy.json`, with scoped continuation documentation at `docs/COSV_TASK_POINTER_COORDINATION_MIRROR_HANDOFF.md`. No unique continuation state should remain only in chat prose at session close.

For resident targeted execution, `scripts/refresh_and_execute_resident_task.py` accepts `--cosv-task-vector` alongside an explicit task ID. After the already-local source refresh and before the existing WorkerCoordinator execution command is invoked, the bridge resolves the task ID/vector pair exactly once against the refreshed `control/task-vector-index.json`. Malformed vectors, missing or duplicate task identities, missing provenance, and vector mismatches fail closed before targeted execution. Successful validation is written into `receipts/sovereign-host/resident-targeted-execution.latest.json` as non-authorizing pointer evidence.

The canonical request `control/resident-execution-request.d/cosv-task-pointer-runtime-enforcement-001.json` passes both values through the registered `cosv_task_pointer_runtime_enforcement` resident dispatcher consumer. The local-only WorkerCoordinator source refresh propagates that consumer together with the existing dispatcher and execution bridge. Pointer validation and request consumption grant no execution, claim/fence, credential, Interlock/InTr transition, or Master Records authority; authentic task completion still requires the ordinary downstream execution evidence and canonical progression predicates.

### Terminology invariant

Runtime is an execution substrate/surface, not a boundary.

Authority is a role/property, not a boundary.

Use **boundary** only for an actual limit, interface, containment edge, trust separation, consequence limit, or explicit transition/admission/reconciliation condition that constrains progression. Do not use `runtime boundary` or `authority boundary` as shorthand for the runtime or authority itself.

### Reusable task ephemeral constructs and entropy recovery

Reusable tasks are durable identities, not permanently running task implementations. Each invocation binds invocation-specific parameters and derives the exact RTG -> GTG -> TT construct needed for that invocation from the canonical cross-layer definitions. The resulting manifest binds the reusable identity, parameters, optional tracked task ID + COSV vector, derived construct, runner plan, authority ceiling, dependencies, expected evidence, recording levels, expiry conditions, and entropy-recovery conditions.

The lifecycle is:

```text
durable reusable identity
+ invocation-specific parameters
-> derived RTG / GTG / TT construct
-> manifest-bound bounded runner(s)
-> governed execution + chained receipts
-> runner expiry
-> residual non-executing recording construct when required
-> required scoped recording
-> Master Records custody + reconstruction
-> entropy recovery
```

Runners are ephemeral where possible. Evidence remains durable. A canonical task/COSV identity remains durable when tracking is required. Manifest binding and receipt chaining are mandatory, and recording occurs only at the levels the derived construct and applicable recording policy require.

After runner expiry, any remaining TT/RTG/GTG construct exists solely to preserve invocation identity and manifest binding, carry chained receipts, project required task/COSV state, perform required scoped recording, carry evidence to Master Records, and support reconstruction verification. It has no original execution purpose and may not acquire credentials, mint claims/fences, repeat provider operations, self-extend, or become a persistent service.

**Entropy recovery** is the final displacement of that residual non-executing construct after required recording is complete and Master Records custody/reconstruction confirms that the information-bearing purpose has been satisfied. Entropy recovery does not delete required evidence or Master Records history and does not reactivate the original runner.

The canonical source contract is `data/reusable-task-ephemeral-construct-contract.json`, reusable identities are in `data/reusable-task-registry.json`, invocation manifests use `schemas/reusable-task-invocation-manifest.schema.json`, and deterministic source construction uses `scripts/materialize_reusable_task_construct.py`. Maintenance, Interlock/InTr protocol establishment, external and AI adapters, endpoint monitoring, and social-platform interaction all use this same reusable identity model.

---

## ERL KnowledgeVault evidence custody

Canonical task coordination distinguishes live provider-storage observation from native writer proof. Master Records may preserve and deterministically reconstruct an ERL KV provider observation while its proof class remains `PROVIDER_METADATA_ONLY`; custody does not convert metadata readback into native-adapter execution or byte-for-byte provider readback. Canonical native writer receipts remain separately required before that stronger predicate can be satisfied.

The active task record `data/canonical-task-records/SS-EVIDENCE-COMPARISON-001.json` carries the scoped evidence and dependency state for this lane. StegSocials consumes the stable ERL artifact identity and Master Records custody reference without promoting either into stronger provider-operation or native-writer proof.

---

## ERL KV propagation verification

The completed task `SS-ERL-KV-PROPAGATION-VERIFICATION-001` propagated authenticated ERL-to-MyKV provider-operation proof to its two applicable consumers. Site merged and validated its MyKV ERL/StegSocials projection; Publisher merged and validated its governed KV document-rendering projection. Repository inspection recorded evidence-backed `NOT_APPLICABLE` dispositions for the admissibility and Guardian wikis, and corrected the Guardian target to `StegVerse-002/stegguardian-wiki`.

Canonical closure evidence is retained in `evidence/erl-kv-propagation/2026-09-09-verification-receipt.json` and `docs/SS_ERL_KV_PROPAGATION_VERIFICATION_MIRROR_HANDOFF.md`. The propagation task is retired with no runtime activation, publication, or deployment inference.

---

## Operational Observer Standard

Repositories that generate operational proof artifacts should not be promoted from installed proof infrastructure to observed operational completion until a fresh workflow run, expected artifacts, expected proof files, and receipt validation are confirmed.

The organization-level observer handoff is maintained at:

```text
docs/ORG_OPERATIONAL_OBSERVER_HANDOFF.md
```

This standard keeps operational completion distinct from installed workflow capacity.

---

## Functional Change / README Invariant

Any change that **materially changes repository function** must be reflected in that repository's `README.md` as part of the same functional change.

Material functional change includes changes to externally meaningful behavior such as:

- user-visible capability or workflow;
- runtime behavior or execution semantics;
- interfaces, inputs, outputs, or integration boundaries;
- authority, governance, admission, credential, routing, transition, claim/fence, custody, or evidence semantics;
- operational prerequisites, dependencies, supported environments, or failure behavior;
- capability lifecycle meaning or other behavior a user, operator, integrator, or future autonomous session would reasonably need to understand.

A functional change is not documentation-complete merely because implementation, tests, handoffs, schemas, or receipts were updated. The repository README must either:

1. be updated to describe the material functional effect; or
2. explicitly remain unchanged only when the change is determined not to alter material repository function.

### Machine preflight enforcement

README impact is evaluated at **both** canonical pre-work and worker-admission conditions.

The session/build pre-work entrypoint `scripts/session_build_preflight.py` accepts an explicit README-impact declaration before new functional work may be considered. When `--readme-impact-required` is set, the preflight fails closed with `STOP_AT_README_IMPACT_DEPENDENCY` unless the structured declaration proves either a complete README update for a material change or an evidence-supported non-material determination. This prevents a functional mutation from reaching task creation merely because StegIndex and cross-task coordination otherwise permit new work.

Functional mutation entering the StegVerse worker-task admission path must also declare `readme_impact_required=true` in the task or handoff. The admission packet evaluates a non-authorizing `readme_impact_complete` predicate before the existing WorkerCoordinator may continue toward assignment/claim/fence creation.

For `material_function_change=true`, both gates require:

- `readme_updated_in_change_set=true`;
- the affected `readme_path`;
- evidence references tying that update to the functional change.

For an explicit **non-material** determination, the no-update path requires both `no_readme_update_reason` and evidence references supporting that determination. Missing materiality, missing required README evidence, or a material change without a README update causes the applicable preflight/admission gate to fail closed.

Legacy/nonfunctional tasks are not retroactively stranded solely because they predate this field. New StegVerse functional mutations are expected to enter through the session-entry/preflight contract with README impact declared, and the worker-admission gate independently preserves the same completeness rule at execution admission.

README completeness is evidence-only. It grants no execution, claim, fence, lease, credential, routing, transition, publication, custody, runtime truth, or other authority.

#### Historical machine-preflight supersession

Machine-preflight receipts are retained as historical evidence even when a later canonical correction changes whether their result is currently admissible. Consumers that need **current** preflight meaning must resolve the receipt through `scripts/resolve_machine_preflight_receipt.py` rather than reading a retained `state=PASS` in isolation.

A sibling `<receipt>.supersession.json` is accepted only when it targets that exact receipt, uses `stegverse.preflight-supersession/v1`, retains a `NONE*` authority effect, and explicitly forbids runtime-truth and execution-admission inference. A valid supersession preserves the historical result but makes `current_admissible=false` with the successor disposition. Malformed, mismatched, or authority-escalating supersession state fails closed. Supersession resolution grants no execution, claim, fence, transition, credential, routing, custody, publication, or runtime authority.


### Current-iPhone TVC opaque recipient capability

Canonical dependency `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` now has validated source on both owning sides: the StegOS Mobile target contains the non-exportable P-256 Secure Enclave candidate and TVC-challenge proof-of-possession signer, while TVC verifies the exact ECDSA signature/bindings and alone projects canonical activation/liveness receipts through its Coinbase capability seam. TV/TVC retains credential/capability authority, Interlock/InTr retains transition authority, and GitHub has no runtime authority. Physical current-iPhone execution and the parent Device/KV/SKAP roundtrip remain evidence-gated and are not inferred from merge or CI.

---

## ERL active-research shared Universal InTr submission

The active-research ERL lane reuses the existing resident dispatcher and the existing shared `workers/universal_intr_profiled_ingress.py` listener. It does not create a second resident runtime, listener, scheduler, heartbeat, WorkerCoordinator, credential path, or provider-operation path.

The active ERL resident loopback path uses the ERL-specific transport origin `STEGOS_RESIDENT_LOCAL`. That transport origin describes carriage of an already-materialized resident ERL binding to the existing loopback shared listener; it does **not** replace or rewrite the logical evidence path `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV`. The resident-local hop has credential requirement `NONE`, emits no `X-StegVerse-Authorization-Id`, and rejects any attempt to claim a TVC relay authorization. TV/TVC remains credential authority for transitions that actually require credentials; Interlock/InTr remains transition authority; GitHub runtime authority remains `NONE`.

`TVC_RELAY_EGRESS` is not a generic local-ingress credential. It is reserved for the separate sovereign-relay path whose TVC authorization is exact-scope and single-use against a real admitted relay route, exact opaque payload hash/size, and live execution grant. The legacy ERL relay submitter/materializer remain source history but are no longer selected by the active ERL resident dispatcher.

A retained resident does not depend on generic source refresh knowing every ERL script. Each ERL binding/submission consumer can self-materialize only its exact allow-listed ERL source dependencies from the already-local canonical source root, atomically repair byte drift, verify SHA-256 parity, and then apply and `--check` the idempotent ERL source preparation. Canonical source and runtime roots must be distinct. This convergence performs no clone/fetch/pull/network source transport, creates no authority, and does not itself prove runtime traversal.

When the resident ERL binding already exists but `runtime-state/erl-active-research/intr-submission-input.json` does not, the existing ERL submission consumer materializes the bounded resident-local input from the binding reference plus the explicit `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL`. Missing ingress remains a non-authorizing wait state. The materializer requires loopback HTTP at `/intr/materialization`, binds the exact input hash, and cannot discover or start a listener, create a credential, grant execution authority, or authorize provider replay.

The ERL-only transport validator requires `InTr`, JSON, the exact raw-body SHA-256, `X-StegVerse-Transport-Origin: STEGOS_RESIDENT_LOCAL`, and absence of a relay authorization header. The installed ERL route uses that validator only after identifying an ERL active-research binding; non-ERL profiles retain their existing transport-origin and authorization rules.

A successful authentic shared-listener profile response may preserve the first two verified upstream hop receipts for `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM` and project the terminal `DEVICE_SYSTEM -> KV` request to the existing `SHWP-DEVICE-KV-INTR-OBSERVATION-001` / `StegVerse-Labs/continuity-vault-kit#79` owner. The submitter never fabricates the terminal KV receipt and explicitly forbids provider-operation replay. The complete three-hop chain is proven only after the existing DEVICE_KV owner executes the exact terminal bytes and the resulting receipt preserves prior-receipt continuity.

Source implementation, deterministic tests, GitHub validation, or merge status do not prove authentic resident source materialization, a bound shared loopback ingress, InTr traversal, or terminal KV receipt. Those remain runtime-evidence predicates.

Canonical source for this lane includes:

```text
workers/erl_active_research_intr_profile.py
workers/erl_active_research_transport.py
scripts/materialize_erl_active_research_intr_resident_local_input.py
scripts/submit_erl_active_research_intr_binding_local.py
scripts/install_erl_active_research_universal_intr_route.py
scripts/install_erl_resident_request_wiring.py
control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py
control/resident-execution-request.d/consume-erl-active-research-intr-submission.py
docs/SS_ERL_ACTIVE_RESEARCH_INTR_RUNTIME_BINDING_MIRROR_HANDOFF.md
```

---

## Canonical Policy Context Preflight

StegVerse session/build pre-work must resolve already-canonical architecture and lifecycle policy **before** it interprets task state, derives a blocker, proposes remediation, or creates new work. The machine must not require a human to restate policy that is already canonically resolvable.

The policy-context registry is:

```text
control/canonical-policy-context-registry.json
```

and the canonical pre-work entrypoint remains:

```text
scripts/session_build_preflight.py
```

Every preflight loads the global task-coordination and cross-task policy context. When a canonical task record declares `canonical_policy_refs`, those sources are loaded automatically. Cross-repository refs may resolve through already-materialized repository roots in `STEGVERSE_REPO_ROOTS_JSON`; no network source fetch is introduced.

If a required policy source cannot be resolved, preflight fails closed as `STOP_AT_CANONICAL_POLICY_DEPENDENCY`. Missing policy is an exact source dependency, not permission for a session to invent new lifecycle, authority, device, worker, HeartBeat, custody, or failure semantics. Policy resolution itself grants no execution, claim/fence, Interlock/InTr transition, TV/TVC credential, route, custody, publication, or runtime-truth authority.

This gate consumes existing canonical invariants—including ephemeral runner lifetime, durable accountability, Master Records reconstruction, and prompt-continuation rules—rather than redefining them. Scoped documentation is maintained at `docs/CANONICAL_POLICY_CONTEXT_PREFLIGHT_MIRROR_HANDOFF.md`.
