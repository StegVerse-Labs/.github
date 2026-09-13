# ELAN Interlock/InTr Bridge Mirror Handoff

Updated: 2026-09-13
Goal Task ID: `ELAN-INTR-BRIDGE-001`
COSV ID: `71000000100110`
Status: `ACTIVE`

## Goal

Build and validate a provider-neutral Interlock/InTr bridge contract for ELAN-originated evidence while preserving a strict separation between transport, semantic resolution, governance admission, and downstream authority.

This task is intentionally separate from completed `ELAN-CUMULATIVE-PUBLICATION-001`. It does not reopen or rewrite Run 1 or Run 2 evidence.

## Scope

The bridge must support:

1. intake of ELAN-originated or ELAN-shaped evidence through a deterministic transport envelope;
2. explicit source identity and provenance without claiming a live ELAN runtime unless observed;
3. separation of observable facts, human assertions, inferred interpretations, and unresolved ambiguities;
4. an interpretation-candidate set that may preserve multiple plausible trajectories;
5. consequence comparison before any ambiguous semantic interpretation is admitted as governed state;
6. a resolution state of either `SINGLE_SURVIVING_INTERPRETATION` or `UNRESOLVED_INTERPRETATION_SET`;
7. escalation for additional evidence or human clarification when materially divergent consequences remain;
8. InTr handoff only after the contract's admission conditions are satisfied;
9. receipts sufficient for replay, reconstruction, and Run 3.x experiment analysis.

## Architectural invariant

Semantic resolution should come from eliminating alternatives, not merely preferring one among them.

Neither model interpretation nor human interpretation becomes truth solely by assertion. Human clarification is additional evidence that may eliminate alternatives; it does not automatically terminate the resolution process.

## Bridge layers

`ELAN source material -> transport envelope -> fact/assertion extraction -> interpretation candidate manifold -> elimination and consequence analysis -> resolution state -> Interlock/InTr admission -> governance -> receipt/return`

The transport envelope MUST NOT itself grant governance, execution, publication, custody, or transition authority.

## Run 3.x relation

Run 3.x formulation is being developed in parallel. The bridge contract is intended to provide the stable implementation boundary required before Run 3.x claims direct interoperability.

Run 3.x must distinguish at least:

- human-mediated evidence exchange;
- ELAN-shaped SDK submission;
- authentic ELAN runtime submission, if later observed;
- direct bidirectional runtime interoperability, if later observed.

No higher interoperability class may be claimed from evidence belonging to a lower class.

## Completion predicates

- `BRIDGE_CONTRACT_CANONICAL`
- `TRANSPORT_ENVELOPE_SCHEMA_VALIDATED`
- `FACT_ASSERTION_INFERENCE_BOUNDARIES_EXPLICIT`
- `MULTI_INTERPRETATION_STATE_SUPPORTED`
- `CONSEQUENCE_DIVERGENCE_ESCALATES_BEFORE_ADMISSION`
- `INTR_ADMISSION_BOUNDARY_EXPLICIT`
- `REPLAY_RECONSTRUCTION_RECEIPTS_DEFINED`
- `SDK_REFERENCE_IMPLEMENTATION_VALIDATED`
- `README_AND_HANDOFF_CURRENT`

## Current state

Canonical task registration and bridge implementation are being created. No live ELAN runtime connection is claimed. Existing Run 2 evidence proves StegVerse-side ELAN-shaped SDK processing only.

## Non-claims

This task does not claim:

- a live ELAN endpoint;
- ELAN credentials or authentication;
- a bidirectional ELAN runtime session;
- direct machine-to-machine interoperability until independently observed;
- that Run 3.x experimental semantics are finalized.
