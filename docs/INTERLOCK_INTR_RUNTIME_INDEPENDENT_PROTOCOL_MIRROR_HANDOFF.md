# Interlock/InTr runtime-independent protocol mirror handoff

Updated: 2026-10-01
Goal Task ID: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`
Issue: #2897
COSV ID: `50000000102000`
Status: `ACTIVE / VALIDATED DOCUMENTARY PROTOCOL / RUNTIME OBSERVATION UNAVAILABLE`

## Goal

Define a runtime-independent, machine-readable Interlock/InTr interoperability protocol in which registered nodes exchange manifested, payload-bound communications while each receiving framework independently determines the admissible state transition in its own runtime.

## Protocol boundary

The protocol standardizes the observable inter-system boundary, not participating runtimes. A conforming external framework is not required to adopt StegVerse internal runtime code, governance implementation, state representation, database, credential implementation, Master Records, or SDK.

Communication using Interlock/InTr requires registered-node identity and manifested intent. The protocol binds the communication to source, destination, payload commitment, applicable predecessor/state context, requested capability, disposition, receipt, resulting-state commitment where applicable, and evidence references.

The receiving framework remains authoritative for its own state machine. Incoming external data is not presumed to be governed by the originating framework. StegVerse governs its own output automatically; that property does not transfer StegVerse governance authority to the external framework.

## Disposition

Every attempted state-transition-dependent communication MUST terminate with an evidentiary disposition:

- `ALLOW`
- `DENY`
- `FAIL_CLOSED`

A transport success alone MUST NOT be represented as an allowed state transition.

## Initial interoperability profile

`MasterRecordsCheckpoint/v1` is the first bounded profile of this protocol.

Master Records remains sole checkpoint-construction/custody authority. For external checkpoint communication:
1. Master Records establishes canonical checkpoint C.
2. An egress manifest declares intent, checkpoint reference/commitment, registered destination node and requested checkpoint capability.
3. The receiving StegVerse boundary resolves applicable state and governs the permitted output projection.
4. Interlock/InTr transfers the permitted data and retains a transfer receipt.
5. External witness evidence may return through manifested registered-node ingress bound to digest(C).
6. The return is verified and receipted before any applicable resulting state/evidence is retained.

The manifest is provenance for communicating the checkpoint; it is not the checkpoint.

## Adoption/conformance boundary

No external adoption, external conformance, production interoperability, network participation, or runtime execution is claimed by this documentary task. Such claims require independently retained evidence.

## Parent

Decomposed from `MASTER-RECORDS-REPORTABLE-CHECKPOINT-001` / issue #2895.

## Reviewed implementation plan and vectors

The accepted machine-readable implementation plan is `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_IMPLEMENTATION_PLAN_v1.json`. Synthetic non-authorizing conformance fixtures are in `test-vectors/interlock-intr-runtime-independent-protocol-v1.json` and cover ALLOW, DENY, FAIL_CLOSED, node identity, payload, predecessor/state, manifest intent, requested capability, receipt binding, and the first bounded `MasterRecordsCheckpoint/v1` profile.

Exact-head workflow evidence on the prior PR head demonstrated a missing `execution_substrate_resolution` for this documentary task. The task record now declares all runtime substrates NOT_APPLICABLE with no selected substrate. The prior test-suite ratchet also reported an unrelated/new registry-gate failure and one newly passing baseline test; fresh exact-head CI is required before attributing or repairing further defects.

No external adoption, external conformance, production interoperability, runtime execution, deployment, or merge is claimed.

## Replacement PR and exact-head validation

PR #2898 remained unavailable through authoritative connector search. The preserved branch was therefore used to create replacement PR #2909 with explicit replacement evidence. At creation, #2909 targeted `master-records-reportable-checkpoint-2895` from exact head `5ec4bdf4b9244f19051048434df9380375532692`. All five observed workflows for that exact head completed SUCCESS, including Cross-Task Coordination Validation and Test suite ratchet. The branch remains diverged from its base (10 ahead / 2 behind), so mergeability is not inferred from CI success.

## Initial source-level surface trace

Default-branch source evidence identifies these existing seams:

- Public SDK `run-manifest` exists and prior canonical evidence binds successful public results to the exact canonical ingress manifest and deterministic generic execution request.
- Current SDK source at `StegVerse-org/StegVerse-SDK@bafb093797f75e4d1fc94f8b45eb278dda3809f9` traces public `run-manifest` through `stegverse/manifest_execution.py` to route-selected runtime bindings including `stegverse.manifest_state_transition_runtime.execute_manifest`.
- The current manifest-state-transition runtime no longer uses `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL` or `STEGVERSE_TVC_RELAY_AUTHORIZATION_ID`. It resolves the destination only from `completion.egress`, opens no connection, supplies no transport credential, and returns an SDK-bound handoff to the receiving Interlock runtime. That handoff is explicitly not admission and must not be promoted into an authentic far-side disposition.
- The shared canonical ingress profile is `SDK:ManifestStateTransition` at `/intr/materialization`; repository source includes `workers/manifest_state_transition_intr_ingress.py` and tests for the shared profile.
- Repository evidence also states that GitHub is validation/evidence transport, not authentic Universal InTr runtime authority, and that the active ChatGPT execution surface did not expose a non-caller-editable authenticated Universal InTr/TVC invocation primitive in the cited observations.

These are source-level findings only. An authentic current production invocation boundary has not been established in this task and remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Parent reconciliation, verifier and field mapping

The two parent-only changes were reconciled into this branch by carrying forward the current parent versions of the Master Records checkpoint task record and handoff; no successor artifact was discarded. A deterministic verifier now exists at `scripts/verify_interlock_intr_runtime_independent_protocol.py` for the synthetic fixture package. Its fixture semantics were independently exercised during this task and produced the expected ALLOW, DENY, FAIL_CLOSED and negative FAIL_CLOSED classifications; repository exact-head CI remains the required admission evidence for the committed verifier.

Machine-readable source mapping is retained at `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_SOURCE_MAPPING_v1.json`. It maps registered identity, manifest intent, source/destination, payload commitment, state/predecessor context, capability, disposition, transfer receipt, resulting-state commitment and evidence references to current SDK seams and explicitly records partial/profile-dependent gaps.

Authentic Interlock/InTr execution remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Existing-owner seam resolution

Current source makes the smallest ownership boundary explicit rather than requiring another SDK transport path:

1. SDK/Manifest Builder owns canonical manifest validation, route resolution, state-graph derivation, destination binding and handoff commitment.
2. TV/TVC remains credential authority; `derive_execution_request` declares `credential_authority = TV/TVC` without making the SDK a credential issuer.
3. The receiving Interlock/InTr runtime is the existing owner that must authenticate registered-node identity, consume the manifested handoff, evaluate the receiving state/predecessor and produce the terminal ALLOW, DENY or FAIL_CLOSED.
4. That same receiving boundary must produce the authentic transfer/admission receipt and resulting-state commitment where applicable.
5. Master Records remains custody/replay/reconstruction authority for applicable retained closure evidence.

Therefore the smallest unresolved seam is not a new SDK feature: it is exposure/observation of the existing receiving Interlock/InTr admission operation with authenticated node/TVC context and receipt/result return. Until that owner seam is authentically callable, the runtime state remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Exact-head validation

PR #2915 exact head `182972c95ae734b43109580cff8ff391afcc306f` completed all five repository workflows successfully and was 9 commits ahead / 0 behind its parent. The generic deterministic repository suite ran 38 tests successfully, but its workflow did not explicitly execute the newly added standalone protocol verifier. A dedicated non-authorizing workflow has therefore been added to run `scripts/verify_interlock_intr_runtime_independent_protocol.py` and preserve the synthetic/external-conformance-false boundary. Fresh exact-head workflow evidence is required after that addition.

## Next action

Observe the dedicated protocol-vector workflow and all repository-required workflows at the new exact head. Repair only demonstrated failures. If requirements are satisfied, reconcile PR #2915 mergeability and merge only with expected-head protection. After merge, trace the existing receiving Interlock/InTr owner surface for an authenticated node/TVC admission operation; do not add SDK transport/admission authority and preserve `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` unless that operation is actually invoked.


## Verified merge and deterministic conformance reconciliation

Replacement PR #2915 merged from exact head `f00400f2fd35bad2aacff368f8de9db4a5cbbd86` as merge commit `03e043f4680612bcbaf14601bd799b71b662877d`. All six exact-head workflows completed successfully. Dedicated run `36946008125` executed the committed verifier and returned `status=PASS`: ALLOW, DENY, FAIL_CLOSED, every negative binding fixture as FAIL_CLOSED, and the Master Records checkpoint profile as ALLOW_DENY_OR_FAIL_CLOSED. The workflow separately retained `INTERLOCK_INTR_VECTOR_VALIDATION_NON_AUTHORIZING_PASS`. This validates the documentary/synthetic protocol contract; it does not establish external conformance or authentic runtime execution.

## Current receiving operation surface

Current source identifies `workers/universal_intr_profiled_ingress.py` as the shared existing owner for `POST /intr/materialization`. Its transport boundary accepts authenticated `TVC_RELAY_EGRESS` authorization or a bound registered-node outbox identity and dispatches profile-specific admission without transferring credential or execution authority to the SDK. Existing TVC recipient admission source emits a write-once `INGRESS_ADMITTED` receipt with `transition_authority=Interlock/InTr` and `credential_authority=TV/TVC`.

Current operation-surface inspection exposes repository and Actions evidence operations but no authenticated, non-caller-editable registered-node or `TVC_RELAY_EGRESS` invocation primitive for this listener. GitHub cannot substitute for that authority. No request was fabricated and no local listener was started.

Current runtime observation disposition: `AUTHENTIC_REGISTERED_NODE_INTR_ADMISSION_INTERFACE_UNAVAILABLE_IN_CURRENT_EXECUTION_CONTEXT`.
Authentic runtime execution: `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Successor action

Return the validated protocol result to `MASTER-RECORDS-REPORTABLE-CHECKPOINT-001` for bounded `MasterRecordsCheckpoint/v1` integration. Any future authentic runtime observation must use the already-owned receiving listener through an exposed authenticated registered-node or TVC relay operation; do not create another listener, credential route, SDK transport authority or parallel admission plane.
