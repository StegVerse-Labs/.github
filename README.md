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

Once an exact machine-owned transition is currently admitted, the resident/entity runtime is expected to execute it, retain the resulting receipt, reconstruct current state, select the next highest-priority unblocked nonduplicate task, and submit that next transition for its own contemporaneous governance **without inserting a human approval checkpoint between ordinary machine-owned cycles**.

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

### Cross-task active-claim projection

The canonical cross-task coordination ledger may mirror an already-existing WorkerCoordinator claim/fence as **coordination-only ownership evidence** when its task, claim, fence, worker identity, and mutation/evidence scope are supported by canonical handoff and control-plane records. These projections are used to prevent another session or autonomous entity from competing with machine-owned work merely because the underlying task is reported as `BLOCKED` or otherwise nonterminal.

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
