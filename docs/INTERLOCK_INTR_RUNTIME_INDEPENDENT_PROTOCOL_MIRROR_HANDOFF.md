# Interlock/InTr runtime-independent protocol mirror handoff

Updated: 2026-10-01
Goal Task ID: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`
Issue: #2897
COSV ID: `50000000102000`
Status: `ACTIVE / CHECKED OUT / CONFORMANCE VECTOR PREPARATION`

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
- Current canonical documentation traces public `run-manifest` through `stegverse/evaluator_console.py` and `stegverse/manifest_execution.py` to `stegverse.manifest_state_transition_runtime.execute_manifest`.
- That runtime is documented as attaching through `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL` and `STEGVERSE_TVC_RELAY_AUTHORIZATION_ID`; missing attachment returns typed SDK-local FAIL_CLOSED rather than creating a substitute runtime.
- The shared canonical ingress profile is `SDK:ManifestStateTransition` at `/intr/materialization`; repository source includes `workers/manifest_state_transition_intr_ingress.py` and tests for the shared profile.
- Repository evidence also states that GitHub is validation/evidence transport, not authentic Universal InTr runtime authority, and that the active ChatGPT execution surface did not expose a non-caller-editable authenticated Universal InTr/TVC invocation primitive in the cited observations.

These are source-level findings only. An authentic current production invocation boundary has not been established in this task and remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Next action

Reconcile replacement PR #2909 against its current base and exact head without weakening the protocol. Validate the synthetic conformance fixtures with a deterministic verifier, then map each protocol field to the existing SDK ingress-manifest / ManifestStateTransition / Universal InTr / TV-TVC receipt seams. Preserve `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` for authentic runtime execution until a non-caller-editable execution interface is actually available.
