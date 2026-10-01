# Organization Role runtime-reality deployment

Organization: `StegVerse-Labs`
Declaration: `ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001`
Date: 2026-10-01
Evidence class: `SOURCE_IMPLEMENTED` (completion contract v1). No runtime observation, no Master Records closure, no canonical task-record mutation and no goal closure is claimed.
Deployment scope: this organization. The Organization Role is deployed per organization, in each organization's own `.github`. This declaration deploys it here and does not deploy it elsewhere.

## The change

```text
runtime_reality_authority:  Master Records  ->  Organization
```

Reality locus: the **organization ledger root**, held under the **organization ledger lock**, written by **manifest-directed append**.

The organization already emits a receipt for every state transition that occurs within it (`.stegverse/transition-ledger/org-contract.json`, `stegverse.organization-transition-receipt/v1`, scope rule `EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT`). That append-only hash-linked chain, at its own ledger root, under its own lock, is where runtime reality for this organization now lives. The authority follows the receipts rather than being assigned to a destination the receipts are later shipped to.

Unchanged by this declaration: Interlock/InTr remains transition authority, WorkerCoordinator remains claim/fence authority, TV/TVC remains credential authority, KV/SKAP Vault remains sole user-verification authority, Task Registry remains work-intent/coordination truth, HeartBeat and GitHub remain non-authorizing.

## master-records restated

`master-records` is the **recorder of released organization batch receipts**.

- It records organization batches that the organization has independently verified and released, for durable cross-organization custody and complex reconstruction (`propagation_target: master-records/.github`).
- Its release predecessor is a verified organization receipt-chain segment. It cannot create, admit, authorize, infer or repair a transition, and it never held transition authority.
- It is **not** the runtime-reality authority of this organization and is **not** a gate on this organization's runtime reality. An organization transition is real when it is appended under the organization ledger lock, not when a batch carrying it is recorded downstream.
- Nothing in this organization awaits it. A batch that has not been released or recorded is a value in the attempted transition's evidence state, not a blocker and not proof of non-occurrence.

Master Records retains custody, reconstruction and cross-organization history. Every existing statement that Master Records is *custody/reconstruction only and holds no transition authority* remains correct and is strengthened, not superseded, by this declaration.

## Conformance standard

Standing standard, restated as the condition every surface in this organization must meet:

> There are no and will be no external machines awaiting anything. This ecosystem is state-transition dependent for all ACTIONS BY MANIFEST. Any place that is not built this way must be updated to this standard or request an exemption.

Operationally:

1. Every action is a manifest-bound attempted state transition with an explicit predecessor, proposed successor, manifested capability and route, governing constraints, evidence and disposition.
2. The manifest determines the destination. So long as the destination exists, the state transition succeeds at ingress into the Interlock and at egress. Destination existence is sufficient; destination liveness is not a predicate.
3. An unavailable receiver is answered by the protocol's own disposition — `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`, with `always_on_receiver_required: false`. No surface waits on a receiver, polls for one, or reports its absence as a blocker.
4. No surface requires an external machine, a second user-operated device, or a remote computer, and none may be introduced as a completion predicate, machine dependency or substrate-unsuitability finding.
5. No separate post-transition "authentic observer" gate exists after verified canonical closure. A non-ALLOW result carries `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`; a bare `BLOCKED`, `UNKNOWN` or `NOT_OBSERVED` is not a finding.

A surface that does not meet this standard is non-conforming with `failure_code: ORGANIZATION_ROLE_CONFORMANCE_NOT_DECLARED`, and must either be updated or hold a registered exemption.

## Exemption path

Register: `data/organization-role-exemption-register.json` (`stegverse.organization-role-exemption-register/v1`).

An exemption is an actionable non-ALLOW disposition for a named surface, not permission to be non-conforming: it carries `surface`, `owning_existing_goal`, `failure_code`, `failed_predicate`, `why_manifest_bound_state_transition_is_not_yet_possible`, `required_evidence_or_repair`, `retry_entrypoint`, `next_attempt` and `expires_or_review_on`. It grants no authority and may not satisfy a terminal predicate.

The register refuses the justifications the standard already forbids — an external machine must be running, a second device is required, a remote computer is unavailable, evidence reachability is pending, a receiver is not always on, an authentic observer has not yet looked. The register opens empty: no surface in this organization has claimed an exemption.

## Superseded prose

28 statements across 23 files in this repository assign *observed-reality* or *runtime-reality* authority to Master Records. Each is superseded by this declaration at its owning surface; each is enumerated with exact path, line and text in `data/organization-role-runtime-reality-deployment.json` under `superseded_prose_statements`, so the residual is explicit and auditable rather than silent.

They are not edited here. Those paragraphs belong to other goals' handoff surfaces, and bounded validation at each owner's source without cross-owner edits is the standing rule. The machine-readable authority block — `data/task-registry-global-invariants.json`, `applies_to: ALL_CANONICAL_TASKS_EXISTING_AND_NEW` — is changed, enforced in `scripts/validate_task_registry_global_invariants.py`, and is what every task check-in receives.

## Record-side work this declaration does not perform

Deferred, gated behind `canonical-task-record.schema.json` reconciliation and registration-before-mutation (spec: `.github` PR #2799):

- `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` — stale `failed_predicate` naming `MASTER_RECORDS_CUSTODY_CONFIGURATION`, and `completion.terminal_model: DECLARED_STATE_TRANSITIONS_WITH_MASTER_RECORDS_CLOSURE`.
- `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`, `data/canonical-task-registry.json`, `data/task-registry-health-monitor-contract.json` — `master_records_role` values predating this declaration.

The completion evidence class `MASTER_RECORDS_RECONSTRUCTED` is **unchanged**. Renaming a completion evidence class is a registry-wide vocabulary migration requiring its own registration; it is not folded into this declaration.

## Validation

`scripts/validate_task_registry_global_invariants.py` now requires the deployed values and the new prohibitions. `tests/test_organization_role_runtime_reality_deployment.py` asserts the declaration, the register, the invariant block and the measured supersession inventory agree. Source validation and merge grant no runtime authority.
