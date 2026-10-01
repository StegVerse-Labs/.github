# SDK Generic Manifest Ecosystem Invariant — Mirror Handoff

Updated: 2026-10-01
Goal Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
Parent Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `71000000100110`
Issue: `StegVerse-Labs/.github#1615`
Status: `ACTIVE / ARCHITECTURAL VALIDATION + REMEDIATION`

## System-wide invariant under validation

Every StegVerse processing action is manifest-driven. Processing semantics are selected only by an admitted manifest's declared `processing.capability` bound to `processing.route_id` and an installed admissible route.

Source identity, provider identity, framework identity, adapter identity, transport identity, model identity, subsystem identity, response class, file type, or prior result may contribute provenance/policy evidence but MUST NOT independently select processing semantics.

Adapters may translate protocol/framing and preserve source-native artifacts, but MUST delegate processing selection into the canonical SDK manifest ingress/route-resolution machinery. Adapters MUST NOT create parallel processor-selection, governance, custody, credential, or routing authority.

## Why this task exists

A conversational failure mode exposed an architectural validation gap: assertions about ecosystem invariants were accepted and repeated before checking canonical implementation surfaces. This task makes architectural-claim validation explicit and repairs discovered implementation skew.

The predecessor task `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003` retired at prompt ceiling with `DOWNSTREAM_PROPAGATION_COMPLETE` still unresolved. This task continues that unresolved architectural portion; it does not resurrect the retired task.

## Evidence observed at task creation

### PASS — SDK generic manifest contract

`StegVerse-org/StegVerse-SDK/stegverse/manifest_contract.py`
- requires non-empty `processing.capability`;
- requires non-empty `processing.route_id`;
- rejects route-id mismatch.

`StegVerse-org/StegVerse-SDK/stegverse/governance_ingress_runtime.py`
- compares `processing.route_id` with resolved route;
- compares `processing.capability` with resolved route processor capability;
- fails closed on mismatch.

### VIOLATION / architectural skew — LLM Adapter governed ingress

`StegVerse-org/LLM-adapter/llm_adapter/governed_manifest_ingress.py`
- accepts an injected `governance_handler`;
- directly invokes `governance_handler(canonical_manifest)`;
- therefore the adapter surface is governance-hardwired rather than delegating generic processor selection through canonical SDK route resolution.

### VIOLATION / architectural skew — Site MIR return adapter

`StegVerse-Labs/Site/assets/mir-accounting-return-v1.js`
- hardwires `RESPONSE_CLASS = MIR_HISTORICAL_ACCOUNTING`;
- hardwires `PROFILE_NAME = SDK:EvaluatorReviewIngress`;
- hardwires the `evaluator-read-review` route before generic SDK manifest processing;
- therefore MIR source/response class currently predetermines processor destination.

### PARTIAL / requires boundary classification — TVC MIR provider broker

TVC correctly constrains credentials/provider operations, but the MIR provider-specific operation profile must be examined to distinguish credential/transport admission from processing-semantic selection. Provider-operation constraints may remain provider-specific, but they MUST NOT replace canonical manifest-declared processing selection for ecosystem processing.

## Required inventory

Classify representative surfaces as `PASS`, `PARTIAL`, `VIOLATION`, or `NOT_PROVEN`:

1. StegVerse SDK manifest ingress + processor registry/runtime.
2. LLM Adapter manifest ingress/egress.
3. Site external-return adapters including MIR.
4. TVC provider-operation broker and provider profiles.
5. StegCore manifested transaction/governance entry.
6. StegOS/Continuity resident dispatcher and InTr materialization entry.
7. Master Records custody/reconstruction interfaces.
8. Shared-document/external-collaboration ingestion.
9. Provider/framework adapters including Elyria and future integrations.
10. Session-originated execution boundary, documented separately from non-session external ingress.

## Remediation contract

For every VIOLATION:

```text
source-native external/internal artifact
-> canonical stegverse.ingress-manifest.v1 admission/canonicalization
-> processing.capability
-> processing.route_id
-> installed-route resolution/admissibility
-> processor-specific route
-> canonical transitions/custody/receipts
-> return projection
```

No adapter may replace the middle four steps with source/type/provider-specific processor selection.

## Architectural-claim validation gate

Before declaring a StegVerse architectural rule already system-wide, require:

1. canonical contract/task/handoff evidence;
2. implementation evidence from the owning core surface;
3. search of representative downstream adapters/consumers for contradictory routing behavior;
4. explicit counterexample search;
5. runtime evidence when the claim concerns enforcement rather than source construction;
6. classification as `PROVEN`, `PARTIAL`, `CONTRADICTED`, or `NOT_PROVEN`.

A user assertion or conversational correction is an architectural hypothesis until this gate is satisfied. It may guide the investigation but MUST NOT be reported as existing ecosystem fact without evidence.

## Completion predicates

- ecosystem inventory completed across required surfaces;
- all discovered source/type/provider-driven processor-selection violations remediated or explicitly blocked/fail-closed;
- LLM Adapter delegates processing selection to canonical SDK machinery;
- MIR return enters canonical SDK manifest ingress before route selection;
- regression tests detect capability/route mismatch and direct identity-driven routing shortcuts;
- downstream propagation evidence reconciled with predecessor task;
- representative runtime evidence demonstrates canonical manifest-driven route resolution on at least one non-governance and one governance path;
- no claim of system-wide enforcement until all predicates above are satisfied.

## Authority boundaries

- SDK manifest/processor contract: processing declaration + route-resolution contract owner.
- Interlock/InTr: transition transport/admission, not processor-selection authority.
- TV/TVC: credential authority, not processor-selection authority.
- Adapters: protocol/framing only.
- StegCore/other processors: execute only after admitted manifested route selection.
- GitHub Actions: validation/evidence transport only; runtime authority NONE.
- Heartbeat: observability only.

## Next continuation

1. Complete repo-wide evidence inventory.
2. Patch LLM Adapter hardwired governance ingress to delegate to canonical SDK route resolution without breaking governance compatibility.
3. Patch MIR return path so source-native MIR artifact is first represented by canonical SDK ingress manifest; evaluator-read-review becomes a manifest-selected route for the current test, not a source-derived route.
4. Add cross-repository regression evidence and reconcile canonical task record.


## 2026-09-27 existing manifest-invariant owner projection

Current-main source audit at `495832cd27f959925c65f8c69ec4a37ab5edb366`, Registry generation 260, found one ACTIVE/CHECKED_OUT exact owner omitted from the aggregate: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`, COSV `71000000100110`, existing [issue #1615](https://github.com/StegVerse-Labs/.github/issues/1615). The generation-261 source candidate adds that existing exact shard unchanged, preserving its parent/root, checkout, handoffs, evidence and completion=false. This restores aggregate lookup without issuing admission, changing ownership, minting a COSV or claiming runtime enforcement. The exact-owner projection regression covers identity uniqueness and full shard equality. Other legacy/proposed shard omissions are not automatically promoted.

The existing owner continues the manifest-routing inventory and source repairs described in `docs/SDK_GENERIC_MANIFEST_ECOSYSTEM_INVARIANT_MIRROR_HANDOFF.md`; governance and non-governance original route evidence remain required for system-wide enforcement. Central coordination owner remains #1766. Source reconciliation does not establish InTr execution, Master Records closure or autonomous successor selection.


## 2026-10-01 clarified ACTION-BY-MANIFEST audit

Owner clarification was reconciled against current source rather than promoted by assertion. The required actionable chain is:

```text
recognized Node endpoint
-> Interlock/InTr transfer
-> distributed SDK manifest endpoint
-> admitted stegverse.ingress-manifest.v1
-> manifest-declared processing.capability + processing.route_id
-> installed route resolution/admissibility
-> state-dependent ACTION
-> endpoint receipt
-> durable Organization receipt chain
-> bounded/batched Master Records custody + reconstruction
```

Runtime observation remains state-transition dependent. Source, CI, merge, fixtures and documentation do not prove authentic runtime execution. No external machine, named device, hosted service, scheduler or passive waiting endpoint is a prerequisite. An unavailable observation interface is an evidence-reachability condition, not authority and not permission to infer downstream execution.

### Representative surface classification

| Surface | Classification | Exact evidence / remediation |
|---|---|---|
| SDK manifest contract + route resolution | PASS (source contract) | `StegVerse-org/StegVerse-SDK:stegverse/manifest_contract.py`, `route_resolution.py`, `governance_ingress_runtime.py`; capability/route must match installed processor binding. Runtime-wide enforcement remains NOT_PROVEN. |
| LLM Adapter governed ingress | VIOLATION | Current `llm_adapter/governed_manifest_ingress.py` still calls caller-injected `governance_handler(canonical_manifest)` after local validation. Native repair issue: StegVerse-org/LLM-adapter#354. Required topology is recognized Node -> Interlock/InTr -> SDK manifest endpoint; LLM Adapter must not choose governance processing. |
| Site MIR return | VIOLATION | Current `assets/mir-accounting-return-v1.js` correctly uses Node/InTr materialization but preselects `evaluator-read-review` / `SDK:EvaluatorReviewIngress` from MIR-specific source shape. Native repair issue: StegVerse-Labs/Site#1478. MIR identity remains provenance only; SDK manifest route resolution must select processing. |
| TVC provider-operation broker | NOT_PROVEN | Credential/provider authority may remain TV/TVC-specific, but current audit did not establish end-to-end proof that provider identity never selects ecosystem processing. No exemption inferred. |
| StegCore manifested processing entry | NOT_PROVEN | Existing invariant requires admitted manifested route before processor execution; current bounded audit did not establish the full Node->SDK->ACTION->Organization-chain path for representative StegCore execution. |
| Continuity/StegOS InTr materialization | PARTIAL | Existing Node/InTr materialization and receipt contracts exist, but full representative authentic runtime chain under this invariant is not yet established. |
| Organization receipt custody -> Master Records batch | PARTIAL | `resident-runtime/organization_custody_readback.py` and ORGANIZATION-BATCH-CUSTODY-REPLAY-001 establish source contracts and exact-source validation. Its handoff explicitly retains authentic organization/Master Records runtime closure as unobserved; do not promote source/CI to runtime proof. |
| Shared-document/external-collaboration ingestion | NOT_PROVEN | Reusable collaboration definitions exist, but no evidence in this audit proves every actionable path enters through the complete clarified chain. |
| External framework/provider path (including Elyria) | PARTIAL | Existing external-framework work preserves foreign observations and generic SDK ingress concepts, but any translation layer is framing-only. Conformance now requires recognized Node + Interlock/InTr transfer to SDK before processing selection. |
| Session-originated execution | PARTIAL | Universal work/AI preexecution documents reuse manifest + InTr components; authenticated runtime observation remains separate and must not be inferred from session/source/CI state. |

No `EXEMPTION_REQUESTED` surface was found in this bounded audit. Any actionable surface that cannot conform must request an explicit exemption rather than silently bypassing the invariant.

### Remediation rule

For every current or future actionable surface, repair toward the chain above through the existing native owner. Translation/framing code may exist but has authority NONE and may not become a processor selector, governance owner, custody plane, credential authority, runtime, scheduler or dispatcher. Organizations retain their own predecessor-linked receipt chains and send bounded/batched segments to Master Records for custody/reconstruction.

### Runtime completion gate

System-wide enforcement remains **NOT_PROVEN**. Completion requires representative authentic governance and non-governance state-transition observations, endpoint receipts, Organization-chain readback and applicable Master Records reconstruction. GitHub Actions remain validation/evidence transport only.


## 2026-10-01 framework-neutral Node Exchange / interconnected capability custody

Machine-readable source profile: `data/node-exchange/interconnected-capability-custody-v0.1.json`.

The external-framework boundary is generalized from a framework-specific integration into the same Node exchange class used by ephemeral StegOS/Node participation. The ordered evidence model is: reciprocal Node existence exchange -> optional/persistent cryptographic identity binding when attribution is required -> state-dependent capability declaration -> manifest-bound request -> native capability action with ALLOW/DENY/FAIL_CLOSED -> endpoint evidence -> resulting-state commitment -> existing SDK/Organization retention -> applicable bounded Master Records custody/reconstruction.

"Interconnected capability custody" means each independently governed Node retains authority over its own implementation and state while the exchange preserves attributable commitments/receipts sufficient to reconstruct the cross-boundary capability interaction. It does not transfer ownership of a capability, another framework's governance, runtime authority, or truth of that framework's substantive claims.

For externally attributable experiments, `VERIFIED_NODE` is required. `UNVERIFIED_NODE` material may be explored but may not be represented as an authenticated external-framework result; `VERIFICATION_FAILED` fails attribution. Node verification proves participant provenance, not scientific/mathematical/governance claims.

The first bounded falsification case is StegVerse <-> a Richard-operated Sebbi.Pro node. Phase 1 is generic reciprocal Node existence only, using the same semantics expected for an ephemeral Node. Identity/capability binding follows only after existence evidence. A single `MasterRecordsCheckpoint/v1` witness attempt follows only after those phases succeed. No Sebbi-specific runtime, scheduler, dispatcher, credential authority, logging/custody path or governance implementation is introduced.

Multi-hop A->B->C capability composition remains explicitly `UNPROVEN` and MUST NOT be claimed from this profile or the single-hop demonstration. External adoption, Sebbi governance conformance, and system-wide runtime enforcement likewise remain unproven.


## 2026-10-01 healthy-Node credential eligibility + ephemeral meeting-point transport

Credential issuance is downstream of Node admission and MUST NOT become an alternate ingress. The ordered eligibility chain is: authenticated Node existence -> identity binding -> current state-dependent Node health -> manifested request authorization -> request-relative native credential projection -> transport. The credential-request prerequisite is `REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE`; unknown health fails closed. Identity validity, Node health and request authorization are distinct predicates.

The profile supports explicit `health_at_issuance` and `health_at_consumption` requirements. Issuance requires current health. A credential whose declared profile also requires consumption-time health produces authentic non-ALLOW when the requester is degraded or health cannot be established at presentation; possession of a credential does not override current state.

Request-relative credential projection separates `credential_type` (for example API_KEY or SIGNED_TOKEN) from `credential_class` (for example TRANSPORT, WITNESS or EVALUATION). Native credential representation may vary by destination, but projected authority MUST NOT exceed the admitted manifested request. Durable receipts retain credential commitments/type/class/scope/issuance/consumption evidence, not secret material.

`EPHEMERAL_MEETING_POINT_TRANSPORT` is source-specified and runtime-unproven: Framework A -> ephemeral StegOS E -> Framework B is represented as separate manifested A EGRESS -> E INGRESS and E EGRESS -> B INGRESS legs with endpoint receipts and predecessor/state binding. E is an observable transition participant, not a discretionary broker or durable custody authority. Durable custody remains the existing Organization receipt chain and applicable Master Records reconstruction. Transport mediation is explicitly distinct from multi-hop capability composition, which remains UNPROVEN.

Deterministic profile fixtures cover healthy requester eligibility, unknown-health FAIL_CLOSED, degradation after issuance when consumption-time health is required, and attempted alternate-ingress credential bypass. These are source fixtures/specification, not authentic runtime dispositions.

## 2026-10-01 native-repair follow-up and deeper surface evidence

Canonical PR #2900 is merged as `cc579a827e98f5b5dea8670a7b4f81d5df85946f`; its final PR head was `3559a1542bedc9aba750e95360eff692504f5c2a`, not the earlier `ff98d97ab1408eb327b25a75443faa268b071e74`. The earlier head had a failed Cross-Task Coordination Validation check and therefore is not recorded as an admissible merge head. The final head had four observed completed successful checks before the recorded merge. PR review collection was empty; no independent-review claim is made.

Native remediation is now source-candidate work, not runtime proof:

- LLM Adapter #354 -> PR #355: removes the caller-injected governance-specific processing selector, requires a recognized Node plus manifest `processing.capability` / `processing.route_id`, and frames a non-authorizing InTr transfer to the distributed SDK manifest endpoint. Negative regressions cover source-identity selection and unrecognized-Node bypass. Its first head failed the repository work-mutation-safety gate because the required mutation receipt was absent; the demonstrated failure was repaired by adding the repository-native work-safety receipt. Exact-head validation remains pending at the current PR head.
- Site #1478 -> PR #1479: removes MIR preselection of `evaluator-read-review` / `SDK:EvaluatorReviewIngress`; the returned complete manifest must declare capability/route and the Site path targets generic `sdk-manifest-ingress` / `SDK:ManifestIngress`. The first head failed Site orchestration because no active pre-work claim mapped the branch; that demonstrated failure was repaired with a bounded claim under this canonical task. The existing generated InTr profile registry does not yet establish the generic profile, so Site intentionally fails closed rather than falling back. Existing-owner follow-up: StegOS #418.

Deeper representative classification:

- **TVC provider-operation / Test Lanes: PARTIAL.** `scripts/tvc_run_test_lane_external_candidate.py` verifies a READY plan/group, provider/capability equality, a non-authorizing execution group, capsule resolution and a short-lived TV/TVC lease before one vault-broker provider operation. It also carries `manifest_hash`. This is evidence that provider identity is constrained downstream, but the inspected source does not itself prove the complete recognized-Node -> Interlock/InTr -> distributed SDK manifest endpoint chain for the actionable provider call. Do not classify PASS or VIOLATION solely from this bounded file.
- **StegCore customer-local execution: PARTIAL.** `tests/test_sdk_customer_local_prerelease.py` constructs SDK manifests with explicit `processing.capability=governance` and a declared customer-local route, exercises ALLOW/DENY/FAIL_CLOSED mutation semantics, and verifies non-ALLOW cannot mutate. The same fixture explicitly demonstrates that the manifest-only entry point cannot contact remote InTr without host bindings. Thus manifest-driven route/action semantics are source-proven, while the complete recognized-Node/InTr transfer and Organization/Master Records chain are not established by this evidence.
- **Shared-document/external collaboration: PARTIAL.** Existing Ecosystem Chat census states that the data packet carries the manifest selecting processing and that provider identity does not select processing; TVC external-collaboration handoffs preserve read-only provider-operation separation and explicitly deny gateway credential/governance/InTr/Master Records authority. This is stronger than NOT_PROVEN for the source architecture, but authentic end-to-end Node -> InTr -> SDK -> action -> Organization -> Master Records evidence remains unobserved here.

No new `EXEMPTION_REQUESTED` classification is introduced. These PARTIAL classifications are source-evidence statements only and do not establish authentic runtime execution.


## 2026-10-01 issue #2901 — first executable Node Exchange conformance specimen

Issue `#2901` is reconciled as source specimen `data/node-exchange/first-executable-conformance-v0.1.json`. It uses existing owners only and orders the first authentic attempt as authenticated reciprocal Node existence -> identity binding -> current health -> `REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE` -> manifest-bound request authorization. A request-relative TV/TVC credential, `MasterRecordsCheckpoint/v1`, or optional ephemeral StegOS meeting-point transport MUST NOT be attempted before that ordering is authentically satisfied.

The first bounded external target remains a Richard-operated Sebbi.Pro Node, but endpoint, credentials, identity evidence and health evidence remain `UNSPECIFIED`; none may be invented. When an authenticated execution surface is actually available, retain the first authentic `ALLOW`, `DENY` or `FAIL_CLOSED` and applicable custody evidence without retrying for a preferred disposition. Unknown required health fails closed; credential/transport presentation before Node admission is non-ALLOW. Source fixtures, CI and merge are not runtime proof.

## 2026-10-01 Site #1481 verified generic-manifest propagation

Canonical PR #2906 remains closed and unmerged because its earlier evidence correctly became stale while Site #1481 was failing. It is preserved as history and is not reopened or silently treated as merged evidence.

Site PR #1481 was reconstructed on then-current Site main after its original branch became conflict-dirty. Only its bounded deltas were replayed; newer main COSV changes were preserved. Exact-head validation then exposed and repaired three concrete residuals: the KV mirror validator still required `evaluator-read-review`; the MIR return custody binding passed `SDK:ManifestIngress` where the accepted registry key is `sdk-manifest-ingress`; and the downstream return consumer still required `SDK_EVALUATOR_INGRESS_ADMITTED`. The repaired consumer now carries `SDK_MANIFEST_INGRESS_ADMITTED` and `EXECUTE_MANIFEST_SELECTED_SDK_PROCESSING_AFTER_MANIFEST_INGRESS`.

Final Site #1481 head `b9ff7388a85a19d01f8a6af53d6e78ce3e48911a` had eight observed completed successful exact-head checks and was mergeable/clean before expected-head merge. It merged as `aaa8f0da87d36968f80e46918fc9b1cf1c126f92`. This proves repository/source conformance of the generic profile propagation only. Authentic Node -> Interlock/InTr -> distributed SDK endpoint execution, Organization custody/readback and Master Records reconstruction remain `NOT_PROVEN` by this evidence.

### Bounded post-merge selector census

A bounded default-branch source census across `StegVerse-org/LLM-adapter`, `StegVerse-org/StegVerse-SDK`, `StegVerse-Labs/StegOS` and `StegVerse-Labs/Site` found no affirmative `source_identity_selects_processing=true` or `adapter_selects_processing=true` implementation; the LLM-adapter implementation and tests explicitly retain both as false, and the SDK generic processing contract states that source/provider/framework/adapter/transport/model/interface identity cannot select processing semantics.

Historical/direct evaluator-specific ingress surfaces still exist as separately named capabilities: Site service-worker surfaces advertise `SDK:EvaluatorReviewIngress`; StegOS retains `evaluator_intr_roundtrip.py` and evaluator-specific handoffs; and the SDK connector capability overlay retains the `SDK:EvaluatorReviewIngress` / `evaluator-read-review` baseline. Their mere existence is not evidence that source identity selects processing: they remain valid only when explicitly requested as their declared capability/profile. This census does not establish that every possible call path is routed through generic `SDK:ManifestIngress`, so system-wide replacement of direct processor-specific ingress is `NOT_PROVEN`, not inferred.

The repaired Site MIR return path is no longer one of those direct selectors: it requires manifest-declared `processing.capability` / `processing.route_id`, transports via `sdk-manifest-ingress`, binds KV custody to that profile ID, and hands off only after `SDK_MANIFEST_INGRESS_ADMITTED`. Authentic runtime execution remains `NOT_PROVEN` absent authenticated Node -> Interlock/InTr -> distributed SDK endpoint evidence and applicable Organization/Master Records closure.
