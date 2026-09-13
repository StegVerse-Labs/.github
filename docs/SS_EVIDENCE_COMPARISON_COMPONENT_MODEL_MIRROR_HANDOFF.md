# StegSocials Evidence Comparison Component Model Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Canonical runtime/task handoff: `StegVerse-Labs/StegSocials/docs/STEGSOCIALS_ERL_ASSISTED_DRAFTING_MIRROR_HANDOFF.md`
Status: `ACTIVE / REUSABLE COMPONENT RECONCILIATION APPLIED / AUTHENTIC STANDARD-KV RUNTIME EVIDENCE PENDING`

## Scope

This handoff records the source-architecture decomposition required by the canonical Reusable Task Component Model. It does not replace the StegSocials runtime/evidence handoff and does not change the Goal Task identity, COSV, authentic runtime state, or completion predicates.

Canonical model sources:

```text
data/reusable-task-component-model.json
data/reusable-task-component-decomposition-policy.json
scripts/evaluate_reusable_task_componentization.py
docs/REUSABLE_TASK_COMPONENT_MODEL_MIRROR_HANDOFF.md
data/reusable-transport-component-contract.json
```

Goal-specific transport profile:

```text
data/goal-task-transport-profiles/SS-EVIDENCE-COMPARISON-001.json
```

## Decomposition decision

The task exceeds the `13+` decomposition threshold because it has repeated evidence/readback subflows, multiple canonical authority owners, multiple independently evidenced cycles, cross-repository orchestration, a growing handoff sequence, optional premium publication, independently reusable verification/custody stages, and independently provable evidence predicates.

Disposition:

```text
STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION
```

This stops additional bespoke orchestration, not the Goal Task. The same Goal Task continues through reusable components and existing canonical owners.

## Goal Task -> reusable component composition

Only the components required by the current standard/manual lane are selected.

| Component | Existing | Canonical owner / implementation | Inputs | Outputs | Preconditions | Evidence | Cardinality | Failure/reentry | Applicability |
|---|---|---|---|---|---|---|---|---|---|
| `RTC-ROUNDTRIP-003` Governed Round Trip | Yes | Reusable transport contract + existing KV path | preparation bundle, canonical KV path, exact draft bytes | admitted KV write + exact stored-byte readback | valid preparation; KV/SKAP verification/authority available | exact path/hash/size agreement; fail-closed readback | one required standard save/readback cycle; retries only after classified failure | failure does not upgrade evidence; retry must create fresh exact transition evidence where required | REQUIRED |
| `RTC-INTERLOCK-INTR-TRANSPORT-008` Interlock/InTr Transport | Yes | Interlock/InTr | exact bounded KV transition candidate | governed admission/transport receipt | applicable claim/fence when machine-owned; exact subject/payload binding | authentic admission for the exact transition | repeated only for distinct governed transitions | prior receipt never authorizes the next transition | REQUIRED |
| `RTC-EVIDENCE-CUSTODY-004` Evidence Custody and Reconstruction | Yes | Master Records | verified standard-flow evidence plus existing ERL/provider receipt references | custody/readback/reconstruction references | exact evidence class preserved; no evidence upgrading | custody and reconstruction receipts | once per independently custodial evidence object; historical custody reused | malformed/missing evidence fails closed; no synthetic reconstruction | REQUIRED where Goal Task predicate calls for custody/reconstruction |
| Standard-flow evidence validation | Existing canonical implementation | `StegVerse-Labs/StegSocials` merged PR #48 verifier / `scripts/validate_standard_flow_evidence_export.py` | exported standard-flow JSON | PASS/fail-closed validation result | canonical KV admission/readback bindings present | verifier PASS with no device identity/attestation predicate | once per evidence object; repeatable for new objects | invalid/missing bindings fail closed | REQUIRED |
| KV/SKAP user verification | Existing authority | KV/SKAP Vault | user verification/authority state | user-authority result | KV/SKAP available | authority evidence from KV/SKAP only | as required by the exact user-authority transition | never inferred from device/runtime/node/transport identity | REQUIRED when user verification is needed |
| Runtime observation | Existing owner | current canonical runtime/transport observation owners | exact task/runtime subject | observation only | authentic runtime surface | resident/transport observation if actually executed | per authentic runtime event | absence remains absence | CONDITIONAL |
| Credential/session handling | Existing authority | TV/TVC | provider/release request | bounded credential/session | separate provider/release task and exact authorization | authentic issuance/use/destruction receipts | per exact provider operation | fail closed; no credential inference | NOT APPLICABLE to current standard/manual lane; belongs to `SS-KV-SKAP-SOCIAL-RELEASE-001` |
| Publisher projection | Existing reusable component `RTC-PUBLISHER-005` | Publisher + TV/TVC release authority | authorized publication payload | publication/distribution projection | separate provider/release authority | provider publication receipt | provider-operation specific | not selected here | NOT APPLICABLE to current standard/manual lane |
| SDK return assembly | Existing reusable component `RTC-SDK-RETURN-006` | SDK | normalized execution result | SDK return artifact | SDK consumer | return artifact | per SDK request | not selected here | NOT APPLICABLE |
| StegVerse final egress / far-side final | Existing reusable components | Interlock/InTr / far-side owner | exact outbound candidate | final transition receipts | separate outbound/far-side transition required | authentic egress/far-side receipt | per transition | not selected here | NOT APPLICABLE to standard/manual lane |

## Existing work reclassified

- Merged StegSocials PR #48 is **reusable evidence-validation implementation**, not a device verifier and not a new Goal Task.
- Site standard-flow evidence export is **Goal Task-specific configuration/output construction** consumed by the existing evidence validator.
- Existing ERL provider-resource and provider-operation readback logic is **reusable evidence/readback implementation already owned by ERL/StegSocials**, not a reason to create another adapter.
- Existing Master Records ERL receipt custody/reconstruction is **reusable custody/reconstruction implementation**; historical evidence remains preserved and is not replayed.
- The old `SS-EVIDENCE-STANDARD-IPHONE-FLOW-001` formulation is **obsolete/superseded architecture** because device verification/identity is prohibited; its provenance remains historical.
- `SS-EVIDENCE-STANDARD-KV-FLOW-001` remains an adjacent implementation/continuation projection for the same standard-KV objective, not a replacement for the root Goal Task.
- `SS-KV-SKAP-SOCIAL-RELEASE-001` remains a genuinely separate Goal Task because provider publication has independent entitlement, credential/session, provider-execution, publication-receipt, destruction, KV publication-record, and Master Records completion semantics.

## Authority separation

```text
Task Registry       = coordination only
WorkerCoordinator   = claim/fence authority
KV/SKAP Vault       = sole user-verification authority
StegOS device       = interchangeable transport/execution node only
Interlock/InTr      = governed transition/admission authority
TV/TVC              = credential/provider/release authority
Master Records      = observed-reality custody/reconstruction
HeartBeat           = timing/freshness/liveness/correlation/observability only
GitHub              = source/evidence coordination only; runtime authority NONE
```

There is no device verification, device attestation, Secure Enclave user identity, node user identity, runtime-subject user verification, or transport-identity user authority in this composition.

## Remaining Goal Task-specific predicates

Component reuse does not satisfy these by itself. Remaining evidence must stay authentic:

1. authentic standard KV preparation/save/admission on an eligible StegOS transport node;
2. exact stored-byte readback bound to canonical path/hash/size;
3. exported standard-flow evidence object validated by the merged no-device-verification verifier;
4. retained observation/custody evidence at the exact evidence class actually observed;
5. broader publication-record/Master Records predicate remains unsatisfied wherever the canonical root Goal Task still requires a real publication-to-KV reconstruction event;
6. separate premium automated/scheduled publication predicates remain owned by `SS-KV-SKAP-SOCIAL-RELEASE-001` and are not inferred here.

Source/CI/component selection does not prove resident execution, InTr admission, WorkerCoordinator claim/fence, provider credential/session issuance, provider execution, callbacks, publication, custody/readback, reconstruction, far-side transition, or cleanup.

## Next admissible work

1. Preserve the current Goal Task identity and use `data/goal-task-transport-profiles/SS-EVIDENCE-COMPARISON-001.json` for the standard-KV transport composition.
2. Stop adding task-specific transport, readback, custody, credential, callback, or publication orchestration when the selected reusable component or existing owner already supplies it.
3. Reconcile repository README/handoff projections before merging source changes that materially alter architecture.
4. After source reconciliation is merged, pursue only authentic standard-KV admission -> exact readback -> evidence validation through the existing owners; do not synthesize runtime evidence and do not require any specific physical device.

## Human action

None for this source reconciliation. Authentic user-authority interactions, when actually required by a future transition, remain KV/SKAP-driven and are not device verification.