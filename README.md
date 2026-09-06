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

### Resident WorkerCoordinator self-heal binding parity

The canonical HeartBeat carrier may supervise the **existing** resident WorkerCoordinator process when that process disappears, but this supervision does not create a second worker or grant task authority. A self-healed WorkerCoordinator must receive the same approved, non-secret local repository/runtime bindings as the canonical worker service so restored process presence does not silently degrade into a worker that is alive but unable to resolve already-local StegVerse dependencies.

Self-heal propagation therefore preserves the canonical worker service's local bindings for StegIndex, TV/TVC, Master Records, StegCore, StegOS, KV, Site, TT/RTG/GTG/AE, resident source manifests, and other explicitly allowlisted local roots. Hosted runtime variables and token/secret/password/API-key/private-key/credential variables remain excluded. TV/TVC remains the credential authority; the carrier remains non-authorizing; WorkerCoordinator and InTr continue to perform their existing independent admission and transition checks.

The self-heal module is also part of the existing **local-only WorkerCoordinator source-refresh set**. An already-materialized resident runtime can therefore receive the corrected supervision implementation from an already-local canonical checkout without network fetch, credential acquisition, mutable-state replacement, or creation of another carrier/worker/scheduler. Refreshing source does not itself prove the long-running carrier has loaded new code or that any task was executed; those remain authentic runtime observations.

Fresh native runtime materialization also copies and explicitly requires the self-heal module alongside `run_heartbeat_runtime.py`. A new resident runtime therefore cannot successfully materialize a carrier entrypoint whose local supervision dependency is absent. The sovereign bootstrap eligibility precheck requires the same module, so `canonical_source_complete` cannot become true before installer execution when that dependency is missing. This is dependency completeness only; successful eligibility/materialization still does not prove carrier/worker presence, request dispatch, consumption, or task completion.

This parity requirement is a runtime continuity and failure-behavior guarantee. It does not imply that source, validation, heartbeat progression, or process restoration proves any task was dispatched, consumed, or completed.

### Portable WorkerCoordinator sequential task lineage

The `CURRENT_USER_IPHONE` portable WorkerCoordinator remains one expression of the canonical `StegVerse-Labs/.github` WorkerCoordinator authority, not a second WorkerCoordinator or a StegOS-owned claim/fence plane. Its persisted portable generation is monotonic across admitted tasks and remains distinct from StegOS device-local task generations.

Portable checkout is **single-use per distinct task package**, not single-use for the entire authority lineage. The v1 portable state tracks `checked_out_task_ids`; a task ID already present in that history fails closed, while a different clean `HANDOFF_READY` task may receive the next WorkerCoordinator generation/fencing token through the same atomic compare-and-set state. Legacy v1 state without that list is interpreted from its retained `last_task_id` without resetting generation.

Terminal packages remain non-checkoutable because portable admission still requires clean `HANDOFF_READY` state. Parallel WorkerCoordinator claim issuance remains prohibited, governed transfer remains required before another execution surface may issue claims, TV/TVC remains credential authority, HeartBeat grants no execution authority, and GitHub retains no runtime authority.

This sequential-lineage behavior allows downstream same-device consumers to reuse the existing portable WorkerCoordinator instead of requiring another machine or creating another runtime authority plane. It does not by itself package, admit, dispatch, execute, or complete any downstream task, and it does not establish current iPhone runtime presence or authentic resident execution evidence.

#### HB32 runtime-surface selection

HB32 progression is derived from the independent 10 ms / 100 Hz phase oscillator with `OSCILLATOR_ONLY` progression. A continuously running resident sampler, carrier process, or native WorkerCoordinator process is **not** a prerequisite for HeartBeat progression and must not be used as a universal prerequisite for task execution on every supported surface.

The runtime-presence projector therefore keeps native process presence and portable task-control observation distinct. `resident.present_worker_runtime_observed` remains the fail-closed native process/supervision predicate. `resident.task_control_runtime_observed` may also become true from an exact **task-scoped** `stegverse.workercoordinator-portable-checkout-receipt/v1` produced by the already-existing portable WorkerCoordinator on `CURRENT_USER_IPHONE`. The portable receipt must bind the canonical `.github` WorkerCoordinator authority owner, independent-task-control domain, exact task/worker/claim/fence, TV/TVC credential boundary, no GitHub runtime authority, no external non-StegVerse machine, and no parallel WorkerCoordinator issuance.

This correction does not turn HeartBeat progression, a static portable package, source materialization, merge, CI, or browser availability into runtime evidence. A portable checkout proves only that the canonical WorkerCoordinator claim/fence transaction actually ran on the bound current-iPhone surface; it does **not** prove request consumption, task execution, transition completion, custody, reconstruction, or product activation. Native process presence remains valid evidence for the native surface, but absence of that process may no longer be reported as generic runtime absence when a separately authenticated portable task-control surface is the applicable canonical path.

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