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
- evidence references tying the README update to the functional change.

For an explicit **non-material** determination, the no-update path requires both `no_readme_update_reason` and evidence references supporting that determination. Missing materiality, missing required README evidence, or a material change without a README update causes the applicable preflight/admission gate to fail closed.

Legacy/nonfunctional tasks are not retroactively stranded solely because they predate this field. New StegVerse functional mutations are expected to enter through the session-entry/preflight contract with README impact declared, and the worker-admission gate independently preserves the same completeness rule at execution admission.

README completeness is evidence-only. It grants no execution, claim, fence, lease, credential, routing, transition, publication, custody, runtime truth, or other authority.

### Cross-task active-claim projection

The canonical cross-task coordination ledger may mirror an already-existing WorkerCoordinator claim/fence as **coordination-only ownership evidence** when its task, claim, fence, worker identity, and mutation/evidence scope are supported by canonical handoff and control-plane records. These projections are used to prevent another session or autonomous entity from competing with machine-owned work merely because the underlying task is reported as `BLOCKED`.

A projected active claim does **not** mint or transfer authority, prove current runtime execution, renew a lease, or make heartbeat state authoritative. Release of the projected ownership must follow the canonical worker lifecycle; task state alone does not release the claim.

### Cross-task runtime-presence evidence

The canonical cross-task coordination ledger may reuse **fresh resident-runtime presence evidence** for tasks that depend on the same canonical resident substrate. The authoritative producer is the existing runtime-presence projection. Qualifying evidence must identify the canonical `WorkerCoordinator`, remain within its declared freshness window, correlate to the current carrier reference, and retain `NONE_OBSERVATION_ONLY` authority effect.

This prevents separate tasks or sessions from repeatedly inventing their own “is the resident worker alive?” checks. A shared presence predicate is bound to the canonical resident runtime profile and exact worker-runtime identity; it cannot satisfy a differently bound node/runtime subject.

Runtime-presence evidence proves only that a fresh task-capable resident WorkerCoordinator is presently observed. It does **not** prove that a specific request was consumed, that a task executed, that a claim/fence exists, or that any completion predicate passed. HeartBeat remains non-authorizing, and the presence projection grants no execution, admission, transition, credential, custody, publication, or runtime-event authority.

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
