# TVC Recipient Admission Opaque Signer Component Model Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001`
Runtime handoff: `docs/TVC_RECIPIENT_ADMISSION_OPAQUE_SIGNER_BACKEND_MIRROR_HANDOFF.md`
COSV: `50000000102000`
Parent model: `data/reusable-task-component-model.json`
Decomposition policy: `data/reusable-task-component-decomposition-policy.json`
Transport profile: `data/goal-task-transport-profiles/TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001.json`
Status: `ACTIVE / COMPONENTIZATION REQUIRED / GOAL IDENTITY PRESERVED`

## Reconciliation result

The existing Goal Task remains valid and retains its existing Goal Task ID, COSV, parent/root relationships, completion predicates, and runtime-evidence boundary. Componentization changes composition only; it does not create a successor Goal Task, reset counters, mint authority, or upgrade source evidence into runtime proof.

The deterministic decomposition signals are:

```text
repeated_subflow = true
multiple_authority_crossings = true
multiple_round_trips = true
cross_repository_or_org_spread = true
task_specific_adapter_duplicates_generic_work = true
handoff_sequence_growth = true
failure_path_branching = true
independent_reusability = true
optional_subflow_present = false
independent_evidence_predicate = true
score = 27
decision = STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION
```

Task-specific orchestration growth must therefore stop. Existing canonical reusable components and existing owners are reused instead.

## Required component composition

### 1. Manifest Intake and Binding — `RTC-MANIFEST-001`

- Exists: yes.
- Canonical owner: reusable transport component family / Task Registry coordination only.
- Inputs: exact platform recipient-admission sign request, Goal Task ID, COSV, declared evidence requirements.
- Outputs: bound exact request/manifest identity for downstream composition.
- Preconditions: complete request shape; task/COSV resolved; no private-key material request; no recipient-key reuse; no public invocation.
- Authority owner: none; coordination only.
- Expected evidence: exact request hash/task/COSV/evidence declaration.
- Cardinality: one per signing operation.
- Failure: fail closed on incomplete/mismatched request.
- Required: yes.

### 2. Governed Processing — `RTC-GOVERNED-PROCESSING-002`

- Exists: yes.
- Canonical execution owners: KV/SKAP Vault for user verification, Interlock/InTr for admission, WorkerCoordinator for claim/fence, StegOS canonical runtime for interchangeable node execution, TV/TVC for signing.
- Inputs: bound exact request plus current verification/admission/runtime state.
- Outputs: bounded recipient-admission signing result candidate.
- Preconditions: every authority-specific prerequisite independently satisfied.
- Expected evidence: authority-specific receipts; no receipt authorizes the following component by itself.
- Cardinality: one composition per operation.
- Failure: return exact authority/evidence boundary; do not synthesize continuation.
- Required: yes.

### 3. Governed Round Trip — `RTC-ROUNDTRIP-003`

- Exists: yes.
- Parameter: `recipient_admission_signature_round_trip`.
- Inputs: admitted exact sign operation.
- Outputs: signature response or bounded failure.
- Preconditions: current KV/SKAP provenance, current InTr admission, current claim/fence/runtime eligibility, eligible TV/TVC authority capability.
- Authority: none in the component; underlying state changes remain with their canonical owners.
- Evidence: request/response correlation and receipt-chain extension.
- Cardinality: exactly one declared round trip for this Goal Task; do not force unrelated callback/provider/publication round trips.
- Required: yes.

### 4. Evidence Custody and Reconstruction — `RTC-EVIDENCE-CUSTODY-004`

- Exists: yes.
- Canonical owner: Master Records.
- Inputs: authentic observed receipts for current KV/SKAP provenance, InTr admission, WorkerCoordinator claim/fence, canonical runtime execution, public JWK/key ID projection, and signed-admission result.
- Outputs: custody/readback/reconstruction evidence.
- Preconditions: authentic observed evidence only.
- Evidence: Master Records acceptance and reconstruction.
- Cardinality: as required by evidence policy; not inferred from source merge or CI.
- Required: yes for Goal Task completion evidence.

### 5. Interlock/InTr Transport — `RTC-INTERLOCK-INTR-TRANSPORT-008`

- Exists: yes.
- Parameter: `recipient_admission_sign_request_ingress`.
- Inputs: exact manifest-bound sign request/payload.
- Outputs: governed packet movement plus authentic `INGRESS_ADMITTED` evidence.
- Preconditions: existing Universal InTr route/listener; exact request/payload hashes and authority invariants.
- Authority owner: Interlock/InTr.
- Evidence: authentic resident write-once InTr admission receipt.
- Cardinality: one required InTr transport transition in this Goal Task profile. Do not invent an additional far-side/public egress merely because the maximal transport chain contains one.
- Required: yes.

### 6. Execution materialization / bounded canonical runtime

- Exists: yes, through `data/reusable-task-ephemeral-construct-contract.json` plus existing canonical `EVENT_EPHEMERAL` runtime and `NodeEventExecutionBroker` surfaces.
- Inputs: current materialization, retained interchangeable Node, exact WorkerCoordinator invocation, open canonical runtime lease, registered recipient-admission capability.
- Outputs: bounded capability execution receipt/result.
- Preconditions: existing lease and claim/fence must already be authentic; the component cannot mint either.
- Authority owner: WorkerCoordinator owns claim/fence; Interlock/InTr owns governed transition; component authority effect is none.
- Evidence: canonical broker/runtime receipt.
- Cardinality: one ephemeral operation.
- Failure: stop at missing claim/fence/lease/node evidence; no duplicate scheduler/runtime plane.
- Required: yes.

### 7. Current KV/SKAP verification provenance projection

- Exists: source exists and is reused: `StegVerse-Labs/TVC/tools/project_kv_skap_user_verification_provenance.py` plus the `KVSKAPVerificationProvenanceProvider` consumer contract.
- Family: credential/session + evidence validation existing canonical owner.
- Inputs: applicable current owner-authorization object and exact admitted receipt.
- Outputs: non-secret `VERIFIED` provenance projection.
- Preconditions: already-verified owner authorization exact-bound to an admitted TV/TVC receipt.
- Authority owner: KV/SKAP Vault remains sole user-verification authority; TV/TVC only projects admitted evidence.
- Evidence: exact owner/receipt digests and provenance hash.
- Failure: reject historical/arbitrary custody records, digest drift, unverified owner state, or authority transfer.
- Required: yes.
- Unresolved dependency: canonical selection of the applicable **current** verification record remains unimplemented; do not interpret “latest” as authoritative without a canonical selector.

### 8. Current InTr admission projection

- Exists: source exists and is reused: `UniversalInTrCurrentAdmissionProvider` and the existing recipient-admission signing Universal InTr ingress route.
- Family: governed ingress + evidence validation existing canonical owner.
- Inputs: exact current request/payload/write-once `INGRESS_ADMITTED` receipt.
- Outputs: read-only current admission projection.
- Preconditions: authentic resident route installation and exact current evidence source.
- Authority owner: Interlock/InTr.
- Evidence: exact current receipt/request/payload binding and freshness.
- Failure: reject TVC capability admission substituted for InTr evidence; reject stale or synthetic evidence.
- Required: yes.

### 9. TV/TVC opaque P-256 authority signing capability

- Existing task-specific implementation to retain as capability implementation, not as orchestration owner: `PlatformOpaqueRecipientAdmissionSigner`, `TVCRecipientAdmissionNodeCapability`, and native `TVCRecipientAdmissionBoundOperationSigner`.
- Inputs: exact admitted bound message, authority key ID/public-JWK digest, nonce/freshness bindings.
- Outputs: ECDSA P-256/SHA-256 DER signature plus non-secret response evidence.
- Preconditions: current reusable components above satisfied; distinct role-separated non-exportable authority key.
- Authority owner: TV/TVC.
- Evidence: exact key/JWK/message binding, non-export, no recipient-key reuse, fresh signature.
- Failure: fail closed; no public deep-link/loopback signing oracle and no second signer daemon.
- Required: yes.
- Remaining implementation dependency: generic opaque capability to native signer binding inside an eligible StegOS execution context.

## Components not selected

The Goal Task does **not** require `RTC-PUBLISHER-005`, `RTC-SDK-RETURN-006`, `RTC-STEGVERSE-EGRESS-007`, or `RTC-FARSIDE-FINAL-009`. Publication, SDK assembly, and a far-side final transition are not signer completion predicates and must not be forced into this task merely because they exist in the maximal reusable transport composition.

## Existing session work classification

```text
PlatformOpaqueRecipientAdmissionSigner                 -> task-specific TV/TVC capability adapter; retained
KVSKAPAdmittedNodePlatformTransport                    -> task-specific composition adapter over reusable transport/evidence components; no further bespoke expansion
Universal InTr signing route/current-admission provider -> reusable InTr transport/governed-ingress owner; reused
KV/SKAP provenance projector                           -> reusable evidence/provenance function under existing owner; reused
kv_skap_verified_local_operation                       -> reusable evidence/binding validation behavior; reused
NodeEventExecutionBroker / canonical node carrier      -> reusable execution materialization/runtime owner; reused
TVCRecipientAdmissionNodeCapability                    -> task-specific capability registration over reusable runtime; retained
native bound Secure Enclave signer                     -> task-specific TV/TVC signing capability; retained
public deep-link/loopback signing-service idea         -> rejected/obsolete; must not be introduced
new task-specific scheduler/listener/runtime plane      -> duplicate orchestration; prohibited
```

No historical evidence or merged provenance is deleted. Existing bespoke adapters are retained only where they express task-specific parameter/configuration or TV/TVC signing semantics; generic transport/runtime/evidence responsibilities are rebound to canonical reusable owners.

## Remaining Goal Task-specific predicates

Componentization does not mark these complete:

```text
CURRENT_KV_SKAP_VERIFICATION_RECORD_SELECTION_AND_RUNTIME_PROVIDER_BINDING
AUTHENTIC_CURRENT_INTR_ROUTE_INSTALLATION_AND_EXACT_RECEIPT_EVIDENCE
GENERIC_OPAQUE_P256_TO_NATIVE_SIGNER_BINDING_INSIDE_ELIGIBLE_STEGOS_EXECUTION_CONTEXT
PLATFORM_SIGNER_BACKEND_INJECTED_IN_EXISTING_VAULT_AGENT_LIFECYCLE
PRODUCTION_AUTHORITY_KEY_MATERIALIZATION_OBSERVED
MATCHING_PUBLIC_JWK_TRUST_ANCHOR_BOUND
FRESH_WORKERCOORDINATOR_BOUND_PRODUCTION_SIGNATURE_OBSERVED
MASTER_RECORDS_CUSTODY_AND_RECONSTRUCTION_CONFIRMED
```

Source construction, CI, merge, and component compatibility do not satisfy these runtime predicates.

## Next admissible work

1. Reuse the canonical KV/SKAP provenance component and locate/establish only the missing **current-record selector/provider binding**; do not build another verification mechanism.
2. Reuse the existing Universal InTr component and bind its current evidence source to authentic resident request/payload/receipt state; do not create another listener.
3. Reuse the existing canonical ephemeral runtime/broker component for eligible-node execution; do not create another runtime plane.
4. Bind the task-specific opaque P-256 capability to the existing native signer within that eligible execution context.
5. Inject the finished composition into the existing vault-agent lifecycle only after the required current providers fail closed correctly.
6. Observe authentic production key/JWK/signature evidence and route it to Master Records reconstruction before claiming completion.

## Runtime truth boundary

The canonical runtime handoff remains `docs/TVC_RECIPIENT_ADMISSION_OPAQUE_SIGNER_BACKEND_MIRROR_HANDOFF.md`. This component-model handoff describes source architecture/composition only and must not replace authentic runtime evidence.

## Manual work

None. No second user-operated device is required. No device-local user verification is authorized.
