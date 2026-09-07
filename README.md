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

### Active task problem/solution semantics

Problems and constraints are metadata, not an operational stopping state. A canonical unresolved task remains active or machine-owned while the current owner attempts a solution within its authority ceiling, derives a successor task, or transfers/escalates through the existing governed mechanism. `BLOCKED` is therefore not a canonical Task Registry `coordination_state`; dependency, problem/constraint, incident, and evidence metadata carry the reason a particular transition cannot yet proceed. Historical receipts or domain-specific schemas may retain older labels as provenance, but those labels do not create a current operational stopping state.

### COSV task-pointer session continuation

A StegVerse continuation prompt should carry only the canonical task identity and its current COSV `task.v1` vector when those values are available:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

The task ID is the stable identity. The 14-position COSV vector is the compact current-state projection. The receiving session or runtime resolves the task's canonical registry record, source vector, applicable `*_MIRROR_HANDOFF.md` documentation, Master Records evidence, WorkerCoordinator claim/fence state, cross-task relationships, runtime requirements, receipts, and other canonical evidence from those two values rather than repeating that information in prompt prose.

When work on an existing task or goal exposes a distinct necessary piece of work that is not already canonically tracked, the system should first search for equivalent or adjacent work and reuse it when present. If the work is genuinely new, it should create a new adjacent canonical task tied to the same root correlation/goal, give that task its own COSV vector and handoff/evidence relationships, and continue through the ordinary WorkerCoordinator, Interlock/InTr, Master Records, and TV/TVC authority boundaries. New task creation is coordination only and grants no execution authority.

The canonical contract is `data/task-coordination-policy.json`, with scoped continuation documentation at `docs/COSV_TASK_POINTER_COORDINATION_MIRROR_HANDOFF.md`. No unique continuation state should remain only in chat prose at session close.

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

README impact is evaluated at **both** canonical pre-work and worker-admission boundaries.

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

#### Exact cross-task evidence field values

Cross-task evidence predicates may require not only that a receipt field exists, but that the field has an exact terminal value. `required_field_values` maps dotted paths inside `evidence.fields` to the exact JSON values that qualify the evidence. Missing paths and unequal values fail closed with `REQUIRED_FIELD_VALUE_MISMATCH:<path>`.

This distinction is required for evidence such as `terminal=true`, exact WorkerCoordinator claim identity, exact fencing token, or other values where field presence alone is not proof of the predicate. A receipt containing `terminal=false` therefore cannot satisfy a predicate merely because `terminal` exists. Dotted nested paths such as `claim.fence` are resolved deterministically. Exact-value qualification remains evidence-only and grants no execution, admission, claim, fence, transition, credential, custody, publication, runtime truth, or other authority.

### Native heartbeat carrier CLI entrypoint

The optional resident sampler/persistence observer is installed through the
repository-root command documented by the canonical resident-start handoff:

```bash
python scripts/install_sovereign_heartbeat_carrier.py
```

The entrypoint resolves its repository-local `scripts` package without requiring
`PYTHONPATH`, a module-form substitute, a network fetch, or a credential. This
is execution compatibility for the existing carrier-only installer; it does not
make the sampler causal to HeartBeat progression, start WorkerCoordinator, grant
task authority, or change the HB32 `OSCILLATOR_ONLY` protocol semantics.

A successful native-supervisor command is not sufficient for
`carrier_active=true`. The activation receipt requires two valid persisted
oscillator observations with an increasing epoch and the canonical 10 ms /
100 Hz, observation-only, `OSCILLATOR_ONLY` invariants. Registration without
observed progression fails closed and cannot be reported as live runtime.

### SV002 standing-awareness resident dispatch

The existing portable refresh-and-dispatch bridge admits the existing
`astra_class_resilience_awareness` and `quantum_resilience_awareness`
selectors as well as `sv002_org_runtime_activation`. A bounded resident repair
must invoke the same bridge once per selector in that prerequisite order; it
must stop before SV002 activation if either standing-awareness dispatch fails.
This extends no heartbeat, oscillator, scheduler, dispatcher, WorkerCoordinator,
claim, fence, credential, or transition authority.

### Resident WorkerCoordinator self-heal binding parity

The canonical HeartBeat carrier may supervise the **existing** resident WorkerCoordinator process when that process disappears, but this supervision does not create a second worker or grant task authority. A self-healed WorkerCoordinator must receive the same approved, non-secret local repository/runtime bindings as the canonical worker service so restored process presence does not silently degrade into a worker that is alive but unable to resolve already-local StegVerse dependencies.

A live PID is not sufficient evidence that the WorkerCoordinator is healthy. On each existing HB-scale supervision visit, the self-heal path reuses the canonical runtime-presence freshness predicate. If an existing WorkerCoordinator PID is alive but its task-capable cycle is stale or no longer task-capable, the carrier-side supervision reuses the established controlled process-termination helper, recycles only that WorkerCoordinator process, and requires a new task-capable worker tick before reporting repaired presence. The HB32 oscillator and carrier remain running and non-authorizing throughout; this recovery does not create a second worker, scheduler, runtime, claim/fence path, or transition authority.

Self-heal propagation therefore preserves the canonical worker service's local bindings for StegIndex, TV/TVC, Master Records, StegCore, StegOS, KV, Site, TT/RTG/GTG/AE, resident source manifests, and other explicitly allowlisted local roots. Hosted runtime variables and token/secret/password/API-key/private-key/credential variables remain excluded. TV/TVC remains the credential authority; the carrier remains non-authorizing; WorkerCoordinator and InTr continue to perform their existing independent admission and transition checks.

The self-heal module is also part of the existing **local-only WorkerCoordinator source-refresh set**. An already-materialized resident runtime can therefore receive the corrected supervision implementation from an already-local canonical checkout without network fetch, credential acquisition, mutable-state replacement, or creation of another carrier/worker/scheduler. Refreshing source does not itself prove the long-running carrier has loaded new code or that any task was executed; those remain authentic runtime observations.

Fresh native runtime materialization also copies and explicitly requires the self-heal module alongside `run_heartbeat_runtime.py`. A new resident runtime therefore cannot successfully materialize a carrier entrypoint whose local supervision dependency is absent. The sovereign bootstrap eligibility precheck requires the same module, so `canonical_source_complete` cannot become true before installer execution when that dependency is missing. This is dependency completeness only; successful eligibility/materialization still does not prove carrier/worker presence, request dispatch, consumption, or task completion.

### Resident HIL activation acceptance evidence

`scripts/run_hil_resident_activation_test.py` is an execution/evidence harness for the existing HIL runtime path; it is not a receipt generator or a substitute runtime. A `PASS` must bind the same evidence denominator used by the canonical HIL cross-task predicate rather than infer request consumption from downstream receiver state.

The harness therefore requires component-produced evidence for the resident request dispatcher, the exact `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` HIL consumption receipt, the InTr ingress receipt, HIL materialization/`LEASE_OPEN`, targeted execution, and the HIL receiver receipt with a real claim, integer fencing token, and `receiver_ready=true`. The resident-consumption receipt must be `COMPLETED` for task `SHWP-HIL-SOVEREIGN-RECEIVER-001`, mode `TARGETED_INDEPENDENT_TASK_CONTROL`, with `runtime_execution_attempted=true` and `terminal_hil_transition_observed=true`, while retaining TV/TVC credential authority, GitHub runtime authority `NONE`, no HeartBeat execution authority, and no second-machine requirement.

For `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`, `terminal_hil_transition_observed=true` means the bounded resident request has reached its success boundary; it does **not** mean the broader HIL lifecycle is complete. Authentic `HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED` is sufficient to mark that exact request `COMPLETED` and replay-protected because the existing same-device receiver is READY and public observation is downstream of routine local `LEASE_OPEN`. The receipt separately exposes `broader_hil_lifecycle_complete`; it remains false at local READY. Public rendezvous, controlled participant receipt, exact-byte restart/reconstruction, TVC lifecycle, private review, publication, Site projection, and Master Records release remain separately governed predicates. Failures or predicate-pending states before local READY remain retryable.

The dispatcher is intentionally independent across consumers, so unrelated request failures do not invalidate an otherwise exact HIL outcome; the HIL outcome itself must show that the existing HIL consumer was actually attempted and returned the exact terminal consumption evidence. A receiver receipt, materialization receipt, process PID, heartbeat progression, source merge, or CI result cannot substitute for that request-consumption predicate. Hosted validation environments remain inadmissible as authentic HIL runtime evidence, and none of these receipts grants execution, claim/fence, transition, credential, custody, review, publication, or Master Records authority.

A self-healed or stale-worker-recycled WorkerCoordinator now persists its task-capable `runtime.cycle()` before any potentially long resident maintenance on logical tick zero. Rendezvous polling, local source refresh, resident request dispatch, HB-derived machine-continuation dispatch, and transition-release refresh therefore run only after the cycle observed by the existing three-second supervision proof. This prevents a healthy restarted worker from being killed as `WORKER_REPAIR_FAILED` merely because synchronous resident dispatch began before its first cycle and outlived the proof window. Existing maintenance cadence is unchanged: resident dispatch and local source refresh are still visited on tick zero and every 100 logical ticks, after the cycle. No new heartbeat, oscillator, scheduler, WorkerCoordinator, dispatcher, authority, credential path, or second-machine dependency is introduced.

### Resident HIL activation acceptance evidence

`scripts/run_hil_resident_activation_test.py` is an execution/evidence harness for the existing HIL runtime path; it is not a receipt generator or a substitute runtime. A `PASS` must bind the same evidence denominator used by the canonical HIL cross-task predicate rather than infer request consumption from downstream receiver state.

The harness therefore requires component-produced evidence for the resident request dispatcher, the exact `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` HIL consumption receipt, the InTr ingress receipt, HIL materialization/`LEASE_OPEN`, targeted execution, and the HIL receiver receipt with a real claim, integer fencing token, and `receiver_ready=true`. The resident-consumption receipt must be `COMPLETED` for task `SHWP-HIL-SOVEREIGN-RECEIVER-001`, mode `TARGETED_INDEPENDENT_TASK_CONTROL`, with `runtime_execution_attempted=true` and `terminal_hil_transition_observed=true`, while retaining TV/TVC credential authority, GitHub runtime authority `NONE`, no HeartBeat execution authority, and no second-machine requirement.

The dispatcher is intentionally independent across consumers, so unrelated request failures do not invalidate an otherwise exact HIL outcome; the HIL outcome itself must show that the existing HIL consumer was actually attempted and returned the exact terminal consumption evidence. A receiver receipt, materialization receipt, process PID, heartbeat progression, source merge, or CI result cannot substitute for that request-consumption predicate. Hosted validation environments remain inadmissible as authentic HIL runtime evidence, and none of these receipts grants execution, claim/fence, transition, credential, custody, review, publication, or Master Records authority.

This parity requirement is a runtime continuity and failure-behavior guarantee. It does not imply that source, validation, heartbeat progression, or process restoration proves any task was dispatched, consumed, or completed.

### G18 same-host sovereign runtime recovery

The durable-runtime G18 worker must reuse the existing runtime recovery stack before surfacing a sovereign-runtime constraint. It first attempts the canonical native v13 bootstrap. If that bootstrap does not produce a complete deployment-local activation proof on an eligible non-hosted StegVerse host, G18 automatically invokes the already-existing `scripts/run_sovereign_ephemeral_console.py` fallback on the **same physical host**.

The fallback creates isolated logical runtime roots and separate local HeartBeat-carrier and WorkerCoordinator processes, verifies the existing activation and isolation predicates, and retains the primary local runtime only when the console proof is `COMPLETE`, all logical nodes and isolation predicates pass, the canonical activation proof is promoted, and every G18 activation predicate—including a task-capable WorkerCoordinator cycle—is true. A successful native bootstrap skips the fallback entirely.

Because this fallback is part of the canonical G18 recovery contract, resident source completeness and propagation must guarantee the same script. Sovereign bootstrap eligibility requires `scripts/run_sovereign_ephemeral_console.py`; fresh native runtime materialization copies and verifies it; and the existing local-only WorkerCoordinator source refresh carries it into an already-materialized resident runtime. A source tree, fresh materialization, or local refresh that omits this dependency fails closed instead of reporting a complete G18 recovery surface.

When G18 is resumed from an already-materialized resident runtime, that resident runtime remains the mutable state/proof target, but it is **not** promoted into the canonical source tree. The existing local refresh/execution path preserves the already-local canonical source binding and G18 must resolve `bootstrap_sovereign_runtime.py` and `run_sovereign_ephemeral_console.py` from that bound canonical source while targeting `STEGVERSE_HEARTBEAT_ROOT` for resident state. If the canonical local source binding is absent, unreadable, equal to the resident runtime root, or lacks the required recovery entrypoints, G18 fails closed rather than silently treating refreshed runtime state as source. No network source fetch is introduced.

This source/runtime separation is reused by `RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001`: both the parent G18 activation task and its request-consumption resolution task traverse the same already-local canonical-source → resident-refresh → existing fence-18 execution path. The binding repair therefore serves both task-registry identities without minting another claim/fence, request, scheduler, HeartBeat, WorkerCoordinator, or runtime solution.

This recovery path does not require a second user-operated machine, a hosted process provider, a third-party scheduler, GitHub runtime authority, or a new WorkerCoordinator authority plane. TV/TVC remains credential authority. HeartBeat remains a 10 ms / 100 Hz timing/reference/carriage substrate with `OSCILLATOR_ONLY` progression and grants no execution, admission, claim/fence, credential, routing, transition, custody, publication, or consequence authority.

If both native bootstrap and the existing same-host fallback remain incomplete, G18 fails closed with both outcomes recorded. A generic runtime blocker must not be emitted merely because native service proof is incomplete without first evaluating this already-built recovery path.

Source, merge, CI, or the presence of the fallback code is not authentic runtime evidence. Activation still requires deployment-local G18 receipts and the canonical activation proof.

### Portable WorkerCoordinator sequential task lineage

The `CURRENT_USER_IPHONE` portable WorkerCoordinator remains one expression of the canonical `StegVerse-Labs/.github` WorkerCoordinator authority, not a second WorkerCoordinator or a StegOS-owned claim/fence plane. Its persisted portable generation is monotonic across admitted tasks and remains distinct from StegOS device-local task generations.

Portable checkout is **single-use per distinct task package**, not single-use for the entire authority lineage. The v1 portable state tracks `checked_out_task_ids`; a task ID already present in that history fails closed, while a different clean `HANDOFF_READY` task may receive the next WorkerCoordinator generation/fencing token through the same atomic compare-and-set state. Legacy v1 state without that list is interpreted from its retained `last_task_id` without resetting generation.

Terminal packages remain non-checkoutable because portable admission still requires clean `HANDOFF_READY` state. Parallel WorkerCoordinator claim issuance remains prohibited, governed transfer remains required before another execution surface may issue claims, TV/TVC remains credential authority, HeartBeat grants no execution authority, and GitHub retains no runtime authority.

This sequential-lineage behavior allows downstream same-device consumers to reuse the existing portable WorkerCoordinator instead of requiring another machine or creating another runtime authority plane. It does not by itself package, admit, dispatch, execute, or complete any downstream task, and it does not establish current iPhone runtime presence or authentic resident execution evidence.

### Portable organization allocator successor-task continuity

The `CURRENT_USER_IPHONE` portable organization allocator may extend its exact source catalog with a new distinct queued task while preserving the same `ORG-ALLOCATOR-PORTABLE-IPHONE-20260902` authority epoch and the already-persisted claim/fence lineage. A completed predecessor task is never reactivated merely because source later changes.

For the HB31 Ecosystem Chat autostart projection, `TASK-2026-0008` / fence 4 remains historical provenance. The corrected autostart source is represented by distinct `TASK-2026-0009`, with a non-overlapping Site path and dependency surface. The existing atomic allocator CAS may grant only the next monotonic generation/fence when that successor is actually selected; package/catalog presence, source merge, CI, heartbeat progression, or the predecessor receipt does not grant the successor claim.

The portable state is not reset and prior claims are not deleted to make successor work eligible. Existing collision checks remain fail-closed, TV/TVC remains credential authority, HeartBeat grants no claim authority, GitHub has no runtime authority, and no second allocator, scheduler, WorkerCoordinator, or user-operated machine is introduced.

### Ecosystem Chat same-device terminal execution surface

The canonical Ecosystem Chat parent may satisfy its sovereign runtime-surface predicate through either the existing native/private-process path or the exact `CURRENT_USER_IPHONE` service-worker path. The service-worker path is accepted only when the runtime proof binds `SERVICE_WORKER_LOCAL_INTERCEPT`, the canonical `https://stegverse.org/stegos-bootstrap/local-model` endpoint and StegOS service-worker scope, observed device-local interception, observed real inference, and `network_egress_required=false`.

This does **not** rewrite browser execution as a native process. A current-iPhone service-worker receipt continues to report `real_model_process_observed=false` and `private_endpoint_only=false`; the parent instead records `device_local_runtime_observed=true`, `runtime_execution_surface=CURRENT_USER_IPHONE_SERVICE_WORKER`, and the aggregate `sovereign_runtime_execution_surface_observed=true` only when the exact device predicates pass.

All other terminal predicates remain fail-closed: fresh WorkerCoordinator claim/fence, exact TVC route, exact LLM-adapter execution, measured usage, Master Records provider-usage and transition reconstruction, same-execution identity, persistent conversational runtime readiness, TV/TVC credential authority with credential requirement `NONE`, no GitHub runtime authority, and no hosted/third-party production dependency. Source, merge, CI, package presence, or browser capability alone does not prove current-iPhone execution or product activation.

#### Ecosystem Chat resident-request consumption evidence

The Ecosystem Chat parent resident-request **consumption** predicate is intentionally narrower than parent activation. The canonical consumer `scripts/consume_resident_execution_request.py` does not emit a generic `consumed` boolean. Its durable consumption evidence is the exact `stegverse.resident-execution-request-consumption/v1` receipt for request `RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002`, task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`, mode `DEDICATED_ECOSYSTEM_CHAT_PARENT`, state `ATTEMPT_RECORDED`, with `runtime_execution_attempted=true`.

That receipt proves only that the exact bounded request reached its existing dedicated consumer and was attempted under the consumer's exactly-once request-id/content-hash semantics. It does **not** prove that the parent reached terminal `PASS`, that a fresh WorkerCoordinator fence was obtained, that model inference occurred, that TVC route admission passed, that usage or Master Records persistence completed, or that conversational runtime readiness is true. Those remain separate downstream predicates. An `ALREADY_CONSUMED` return on a later invocation is replay protection, not a substitute for the original persisted attempted-execution receipt and grants no authority.

### Canonical Work task ingress

The Canonical Work resident bootstrap is a **shared governed ingress mechanism for tasks that already exist in the canonical Task Registry**. It is no longer limited to the coordination bootstrap task itself. A caller must provide an explicit `task_id`; the bootstrap fails closed unless that identity resolves exactly once, remains `PROPOSED`, explicitly allows `INGRESS_ADMITTED`, has no projected WorkerCoordinator claim/fence, and preserves the canonical authority model.

The bootstrap reuses the existing Universal InTr listener and Canonical Work ingress adapter. It does not create task identity, a second listener, another scheduler, another WorkerCoordinator, or another authority plane. The resident Canonical Work consumer may carry multiple explicit task request specifications and visits them independently so one task-local failure does not prevent another registered request from being attempted.

The resident consumer treats `data/canonical-task-registry.json` as mutable resident coordination state once it exists. Local source materialization may seed that registry only when the resident copy is absent; it must not overwrite an existing resident registry with a static source copy. This preserves later authentic ingress projections, runtime-resolution projections, and other governed task-state evolution while still allowing a fresh runtime to bootstrap from canonical source. Preserving the registry does not grant task authority or validate any existing projection; downstream Canonical Work, WorkerCoordinator, Master Records, and Interlock/InTr checks remain required.

A successful bootstrap receipt proves only the exact bounded `TASK_INGRESS` request, `INGRESS_ADMITTED` receipt, Canonical Work consumption receipt, and proposed registry projection that it actually observed. It does **not** prove WorkerCoordinator claim/fence, governed task execution, Master Records reconciliation, egress, closure, deployment, or product activation. Source presence, request staging, merge, CI, heartbeat progression, or dispatcher visitation likewise do not substitute for those runtime predicates.

`QUANTUM-RESILIENCE-001` is the first additional task staged through this reusable path. Additional registered tasks may use the same path only through explicit fixed request specifications and the same fail-closed identity/authority checks; staging a request remains non-authorizing and requires the same resident Interlock/InTr transition boundary, TV/TVC credential authority, no GitHub-token runtime authority, and no second user-operated machine.

### Native email action monitor

StegVerse includes a native bounded mailbox-maintenance handler at `scripts/run_native_email_action_monitor.py`. It is intended to replace an assistant-mediated mailbox loop using the **existing** HB/oscillator resident continuation path rather than a ChatGPT automation or second scheduler.

The resident path is:

```text
HB32 / canonical 100 Hz oscillator reference
-> existing HB machine-continuation / resident WorkerCoordinator cycle
-> scripts/dispatch_resident_execution_requests.py
-> standing native-email resident request
-> scripts/consume_native_email_action_monitor_request.py
-> scripts/run_native_email_action_monitor.py
-> local StegOps TVC broker
-> exact TVC Gmail provider operation
-> stegverse.native-email-action-monitor-receipt/v1
```

The mailbox pass is restricted to GitHub operational notification senders (`notifications@github.com`, `noreply@github.com`) and `[Task Update]` mail. It resolves the exact bounded message-ID batch before mutation, clusters those operational signals, archives only those exact reviewed operational IDs, measures actionable backlog depth, reads inbox totals, and emits a durable receipt. Unrelated inbox mail is not selected for archive.

Provider credentials are not accepted by this handler. Provider access must arrive through the existing StegOps broker and exact TV/TVC Gmail provider route; responses must retain `TV/TVC` as credential authority, export no credential material, and transfer no provider-operation authority. The handler fails closed if those invariants are absent. No Google/OAuth credential belongs in `.github`, resident receipts, GitHub Actions, or the assistant-mediated path.

The handler reuses `scripts/normalize_github_failure_email_events.py` signature/incident semantics. Email and GitHub notifications are attention/observation signals only: they do not prove source completion, CI truth, deployment, resident execution, runtime failure, governed activation, or task completion. Incident clusters remain `INCIDENT_PROPOSED_NOT_ADMITTED` and require canonical task ingress before technical work is authorized.

The standing request is retryable. A temporary absence of the exact TV/TVC Gmail owner session records an attempted/pending resident outcome rather than silently terminating the capability. HB/oscillator progression remains `OSCILLATOR_ONLY` and grants no execution, task-admission, claim/fence, credential, routing, transition, custody, publication, mailbox, or provider authority. Source, merge, CI, dispatcher registration, or heartbeat progression do not prove live Gmail execution; authentic operation requires the retained native monitor receipt from the resident path.

### Cross-task active-claim projection

The canonical cross-task coordination ledger may mirror an already-existing WorkerCoordinator claim/fence as **coordination-only ownership evidence** when its task, claim, fence, worker identity, and mutation/evidence scope are supported by canonical handoff and control-plane records. These projections are used to prevent another session or autonomous entity from competing with machine-owned work merely because the underlying task has unresolved problem/constraint metadata or is otherwise nonterminal.

Current projections include the all-organization federation G17 claim, durable-runtime G18 claim, and stable StegGate rendezvous G13 claim. Each remains owned by its original canonical worker/task lifecycle; the cross-task ledger only exposes that ownership to collision and adjacency resolution.

Composed-ledger loading now validates **claim coverage parity** against the sibling canonical `control/worker-registry.json` when that registry is present. Every unreleased task with `executor_binding=BOUND` and a claim ID must have an `ACTIVE` coordination mirror with matching task ID, fencing token, worker ID, and worker-instance ID. Conversely, an `ACTIVE` coordination claim carrying WorkerCoordinator identity cannot remain after that claim is released or becomes terminal in the worker registry. Missing mirrors, stale mirrors, identity drift, duplicate bound claims, or an incompatible worker-registry schema fail closed before coordination consumers receive the ledger.

This parity check does not copy claim authority into the coordination ledger and does not infer current execution. `control/worker-registry.json` remains authoritative for WorkerCoordinator claim/fence ownership; the coordination record remains a non-authorizing collision/adjacency projection. The check exists so static projection drift cannot silently cause two sessions to compete for machine-owned work or preserve ownership after canonical release.

A projected active claim does **not** mint or transfer authority, prove current runtime execution, renew a lease, or make heartbeat state authoritative. Release of the projected ownership must follow the canonical worker lifecycle; task state alone does not release the claim.

### Cross-task runtime-presence evidence

StegVerse has one existing resident runtime-presence projector, but **shared cross-task reuse is currently deferred until exact resident subject identity is proven from authentic runtime evidence**.

The canonical producer remains the existing runtime-presence projection. A reusable presence predicate must bind at least the concrete `runtime_root`, `resident.node_id` when available from authentic evidence, and canonical `WorkerCoordinator` identity. A runtime profile name plus worker class is not sufficient to let evidence from one resident instance satisfy another node/runtime consumer.

Until that binding exists, runtime-presence relationships remain staged in `control/cross-task-coordination-candidates/resident-process-alive-supervised.json`; they are not a global Boolean in the canonical composed coordination ledger. No second heartbeat, WorkerCoordinator, scheduler, hosted observer, or runtime-presence probe should be created to bypass this subject-binding requirement.

Once exact subject identity is established, qualifying evidence must remain within its declared freshness window, correlate to the current carrier reference, and retain `NONE_OBSERVATION_ONLY` authority effect.

Runtime-presence evidence proves only that a fresh task-capable resident WorkerCoordinator is presently observed for that exact bound subject. It does **not** prove that a specific request was consumed, that a task executed, that a claim/fence exists, or that any completion predicate passed. HeartBeat remains non-authorizing, and the presence projection grants no execution, admission, transition, credential, custody, publication, or runtime-event authority.

The existing carrier-owned supervision visit may now submit the just-emitted `receipts/sovereign-host/runtime-presence.latest.json` to an **already-local** `master-records/orchestration` checkout when `STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT` is declared and that checkout exposes its canonical runtime-presence importer. This is a custody/reconstruction handoff only: it performs no network fetch or repository writeback, propagates no GitHub token or secret/credential value, and records the local attempt at `receipts/sovereign-host/runtime-presence-master-records-intake.latest.json`.

Fresh sovereign control-plane bundles that vendor `master-records/orchestration` now fail closed unless that local checkout descends from Master Records PR #80 (`8e33b3e95d3d9e34387fe393031f44bebcdb5d57`) and contains the protected runtime-presence importer plus custody schema. A pre-#80 Master Records checkout can no longer pass bundle source proof while silently omitting the custody path. This is a source/prerequisite guarantee only; it does not prove that an already-running resident has refreshed its vendor tree or that authentic runtime presence has been emitted or custodied.

Master Records retains the exact source observation and its concrete `runtime_root` / node identity when available, but intake explicitly sets `cross_task_reuse_authorized=false` and creates no task/correlation identity. Missing Master Records root/importer does not block or delete the original presence receipt; invalid intake authority semantics fail closed only for the custody handoff. Local custody therefore closes the reconstructability gap between “not emitted” and “emitted locally but not retained,” while still requiring a separate governed subject-binding decision before any task may reuse that evidence.

Source merge, validation, importer availability, or a local intake-capability receipt does not prove that authentic runtime presence was observed or custodied, and local custody is not proof of remote repository persistence.

### Resident DeepSeek InTr governed runtime

The resident dispatcher now contains one bounded DeepSeek InTr request/consumer for `SHWP-DEEPSEEK-INTR-RUNTIME-001`. It reuses the existing WorkerCoordinator rather than creating another runtime or scheduler. The task must obtain a fresh WorkerCoordinator claim/fence, then a canonical portable StegGate ingress `ALLOW` before TVC can issue the exact-bound single-use DeepSeek lease.

The provider operation uses the existing TVC non-exportable vault broker. DeepSeek credential material never enters `.github` or LLM-adapter. The resulting provider-usage event is sent through the existing Master Records owner-local Unix-socket custody broker; egress cannot continue unless authentic custody is recorded and reconstruction is `PASS`. A separate canonical StegGate egress `ALLOW`, bound to the exact provider response hash, is then required by LLM-adapter's exact-response egress verifier.

The complete resident path is therefore:

```text
existing resident dispatcher
-> existing WorkerCoordinator claim + fresh fence
-> canonical StegGate ingress ALLOW
-> exact-bound TVC DeepSeek lease
-> existing TVC non-exportable provider operation
-> DeepSeek response
-> Master Records local custody + reconstruction PASS
-> canonical StegGate egress ALLOW
-> LLM-adapter exact-response egress admission
-> same-execution resident receipt
```

HeartBeat remains timing/reference/carriage only and grants none of these decisions. The standing request, dispatcher, source merge, GitHub Actions validation, provider output, and Master Records custody receipt grant no transition or execution authority. No second user-operated machine, hosted execution surface, GitHub runtime token, DeepSeek credential export, or Master Records bearer export is part of this path. Source/CI completion does not prove that a resident cycle has actually run; authentic completion requires the retained same-execution component receipts.

This invariant exists so the README remains the human-facing projection of what the repository actually does, while canonical machine-readable records and receipts remain authoritative for exact state and evidence.

---

## About Permanence

StegVerse is intentionally **not designed to last forever**.

Its purpose is to exist long enough to:

- Help people interact more clearly during a period of rapid AI adoption
- Preserve context and intent during change
- Make it easier for future systems to replace it

Any system that cannot be replaced has failed.

---

## Participation

There is no onboarding process and no central authority.

If something here is useful:

- Read it
- Reuse it
- Fork it
- Adapt it

If something here is wrong:

- Challenge it
- Improve it
- Replace it

StegVerse claims no ownership over the future.

---

## License & Use

Unless otherwise specified, repositories are published under permissive open-source licenses.

Use, modification, and redistribution are encouraged.

---

## Final Note

StegVerse exists because the way we interact online is changing — whether we plan for it or not.

This project is an attempt to participate thoughtfully, openly, and humanely in that change.