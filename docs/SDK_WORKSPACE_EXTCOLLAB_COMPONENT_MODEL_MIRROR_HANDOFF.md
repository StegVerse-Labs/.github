# SDK WorkSpace External-Collaboration Component Model Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Canonical runtime handoff: `docs/SDK_WORKSPACE_EXTCOLLAB_AUTHENTIC_RUNTIME_004_MIRROR_HANDOFF.md`
COSV: `71000000100110`
Model merge: `StegVerse-Labs/.github#1652` -> `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`
Status: `ACTIVE / REUSABLE COMPONENT MODEL RECONCILED / CURRENT RUNTIME PRESENCE ABSENT`

## Identity and decomposition decision

The existing Goal Task remains valid. Componentization does not rename, replace, close, or reset it. The parent remains `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`; no new successor or child Goal Task is required by this reconciliation.

Applying `data/reusable-task-component-decomposition-policy.json` activates all ten signals for this task and yields score `30`, requiring task-specific orchestration growth to stop. Continuation must compose existing reusable components and canonical owners.

## Component composition

The canonical goal profile is `data/goal-task-transport-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json`. It records inputs, outputs, preconditions, authority owner, evidence, cardinality, failure semantics, and applicability for each bound component.

Current-stage required/reusable composition:

1. **Runtime observation** — existing `heartbeat_runtime/runtime_presence_projection.py`; input is the existing resident subject binding; output is authentic current runtime presence; HeartBeat remains observability-only; absence fails closed.
2. **RTC-MANIFEST-001** — complete manifest and task/COSV binding; Task Registry remains coordination-only.
3. **Execution materialization** — reuse `data/reusable-task-ephemeral-construct-contract.json`; WorkerCoordinator owns claim/fence and Interlock/InTr owns governed transitions; only after authentic current resident presence.
4. **RTC-INTERLOCK-INTR-TRANSPORT-008** — repeatable governed movement; Interlock/InTr owns admission/transition; no bypass on denial/block.
5. **RTC-ROUNDTRIP-003** — five declared task-bound instances: resident client-secret reseal, resident consent listener, sovereign callback, owner-present provider consent, authoritative provider-file probe. Each round trip produces independent evidence and never authorizes the next.
6. **Credential/session path** — reuse TV/TVC provider/session handling when reached; KV/SKAP Vault is the sole user-verification authority. StegOS/device/node/transport identity cannot verify the user.
7. **Evidence validation** — reuse canonical validators; source, CI, merge state, and static compatibility cannot upgrade runtime evidence.
8. **RTC-EVIDENCE-CUSTODY-004** — Master Records owns custody/readback/reconstruction.

Stage-conditional components for this same Goal Task:

- **RTC-SDK-RETURN-006** only when a validated SDK return is required.
- **RTC-PUBLISHER-005** only when the public-distribution stage is reached and authentic TV/TVC release authority exists.
- **RTC-STEGVERSE-EGRESS-007** only when distribution egress is reached; Interlock/InTr remains transition authority.
- **RTC-FARSIDE-FINAL-009** only when far-side distribution completion is actually required.

These conditional components remain part of the Goal Task capability envelope because its completion predicates include downstream/public distribution, but they are not premature prerequisites for resident observation or resident reseal/listener execution.

## Reuse / duplicate-orchestration disposition

No new reusable component is required at this time. Existing reusable/canonical owners cover runtime observation, manifest binding, bounded execution materialization, governed transport, governed round trips, credential/session handling, evidence validation, custody/reconstruction, SDK return, publication, egress, and far-side completion.

Retire/supersede task-local duplication of:

- runtime-presence probing;
- generic Interlock/InTr adapters or transport loops;
- generic request/response correlation loops;
- generic evidence validation;
- Master Records reconstruction paths;
- generic provider/session orchestration;
- manual release/publication substitution;
- device-local user verification.

Historical source/evidence remains provenance. PR #1493 was closed as an obsolete parallel reconciliation path; later canonical merges already preserve its relevant evidence.

Model-level callback-correlation, release-propagation, and failure-remediation component candidates remain candidates only. This Goal Task does not need to create task-local versions of them.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed state-transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes, never user verifiers or user-identity authorities.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: synchronization, timing, freshness, liveness, state correlation, observability only.
- GitHub: source/evidence coordination only, never runtime authority.

Runtime subject binding and resident node identity are evidence-correlation subjects only.

## Goal-specific predicates preserved

Componentization changes none of these:

- `RESIDENT_RESEAL_CONSUMPTION_RECEIPT_OBSERVED`
- `RESIDENT_CONSENT_LISTENER_CONSUMPTION_RECEIPT_OBSERVED`
- `EXTERNAL_COLLAB_CLIENT_SECRET_CUSTODY_PROVEN`
- `SOVEREIGN_CALLBACK_REACHABILITY_PROVEN`
- `OWNER_PRESENT_GOOGLE_CONSENT_PROVEN`
- `AUTHORITATIVE_PROVIDER_FILE_PROBE_PROVEN`
- `SDK_ACTIVE_PROBE_COMPLETE_PREDICATE_REEVALUATION_PROVEN`
- `MIR_TRANSITION_REPORTING_PROVEN`
- `MASTER_RECORDS_CUSTODY_RECONSTRUCTION_PROVEN`
- `ONE_CURRENT_DEVICE_END_TO_END_PROVEN`
- `DOWNSTREAM_PROPAGATION_COMPLETE`
- `PUBLIC_DISTRIBUTIONS_COMPLETE`

## Runtime/evidence truth

Static source compatibility remains proven for `canonical-resident-substrate-v1`; the unresolved runtime boundary remains `CURRENT_OBSERVATION_REQUIRED:DECLARED_ONLY` / `UNRESOLVED_NO_CURRENT_AUTHORIZED_DEVICE`.

Fresh reconciliation observation on 2026-09-12:

- authorized resident connector: zero devices;
- retained Drive reseal receipt matches: zero;
- retained Drive listener receipt matches: zero.

Therefore resident execution, InTr admission, WorkerCoordinator claim/fence, provider/session issuance, callback, custody/readback, Master Records reconstruction, publication, far-side transition, cleanup, and end-to-end completion remain unproven.

## Validation/source state

Reusable Task Component Model PR #1652 merged at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`; exact head `075b1e71d0ebe3591899db03d570da79eed5e916` passed Organization Control `34730323940`, Deterministic Repository Suite `34730323942`, and Heartbeat Worker Project `34730323876`.

This reconciliation adds explicit component applicability/cardinality bindings and regression coverage on branch `reconcile/sdk-extcollab-component-profile-004`. Source validation for this branch must pass before merge; no runtime claim is made by that validation.

## Next admissible work

1. Validate and merge the component-profile reconciliation only if exact-head CI is green.
2. Re-invoke only the existing runtime-observation component.
3. If authentic current resident presence appears, compose the existing execution-materialization + Interlock/InTr transport + round-trip components for the reseal and consent-listener operations.
4. Accept only authentic completion/already-satisfied/exact-blocked receipts and preserve each evidence boundary independently.
5. Do not enter provider consent, publication, egress, or far-side stages until their declared upstream applicability predicates are authentic.

README review: the root README already contains the canonical Reusable Task Component Model projection; this change refines one Goal Task profile and does not require another product-facing README change.

## Human action

None.
