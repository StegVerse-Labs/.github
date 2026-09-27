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
4. an interpretation-candidate set that may preserve multiple plausible trajectories during resolution;
5. progressive elimination of materially plausible alternatives with retained reasons;
6. a resolution state of either `SINGLE_SURVIVING_INTERPRETATION` or `UNRESOLVED_INTERPRETATION_SET`;
7. consequence comparison across surviving candidates as diagnostic evidence, without allowing consequence equivalence to substitute for semantic resolution;
8. `READY_FOR_INTR_ADMISSION` only after exactly one materially plausible interpretation survives;
9. receipts sufficient for replay and reconstruction of bridge processing.

## Architectural invariant

Semantic resolution should come from eliminating alternatives, not merely preferring one among them.

Neither model interpretation nor human interpretation becomes truth solely by assertion. Human clarification is additional evidence that may eliminate alternatives; it does not automatically terminate the resolution process.

Multiple surviving interpretations remain unresolved even when their currently projected consequences are equivalent. Consequence equivalence is diagnostic evidence, not semantic resolution.

## Bridge layers

`ELAN source material -> transport envelope -> fact/assertion extraction -> interpretation candidate manifold -> elimination and consequence analysis -> resolution state -> Interlock/InTr admission -> governance -> receipt/return`

The transport envelope MUST NOT itself grant governance, execution, publication, custody, or transition authority.

## Independence from Run 3

Run 3 is independent of machine-to-machine interoperability and is not gated by, dependent on, or defined by this bridge task.

`ELAN-INTR-BRIDGE-001` may proceed in parallel with Run 3 formulation and execution, but neither establishes completion of the other. Run 3 may remain human-mediated or use any separately agreed experimental exchange method. Conversely, completion of the bridge does not imply any Run 3 result.

If a future Run 3 or later experiment happens to use this bridge, its evidence must record the transport class actually observed, but use of the bridge is optional rather than a prerequisite.

No higher interoperability class may be claimed from evidence belonging to a lower class.

## Completion predicates

- `BRIDGE_CONTRACT_CANONICAL`
- `TRANSPORT_ENVELOPE_SCHEMA_VALIDATED`
- `FACT_ASSERTION_INFERENCE_BOUNDARIES_EXPLICIT`
- `MULTI_INTERPRETATION_STATE_SUPPORTED`
- `SINGLE_SURVIVING_INTERPRETATION_REQUIRED_FOR_ADMISSION`
- `CONSEQUENCE_RELATION_RETAINED_AS_DIAGNOSTIC_EVIDENCE`
- `INTR_ADMISSION_BOUNDARY_EXPLICIT`
- `REPLAY_RECONSTRUCTION_RECEIPTS_DEFINED`
- `SDK_REFERENCE_IMPLEMENTATION_VALIDATED`
- `README_AND_HANDOFF_CURRENT`

## Current state

Canonical coordination work is open in `StegVerse-Labs/.github#1729` on branch `elan-intr-bridge-contract-001`.

Reference implementation work is open in `StegVerse-org/StegVerse-SDK#232` on branch `elan-intr-bridge-001`.

The SDK PR adds:

- `docs/ELAN_INTR_BRIDGE_CONTRACT.md`;
- `schemas/elan-intr-bridge-envelope.schema.json`;
- `stegverse_sdk/elan_intr_bridge.py`;
- `tests/test_elan_intr_bridge.py`.

The semantic-resolution rule has been tightened from the initial draft. The bridge now returns `READY_FOR_INTR_ADMISSION` only when exactly one candidate survives. Two or more surviving candidates return `RESOLUTION_REQUIRED` even when all surviving candidates currently map to the same consequence class. The receipt separately records consequence equivalence or divergence so consequence analysis remains available without becoming a shortcut around semantic resolution. The reference evaluator never grants InTr transition authority.

SDK implementation updates were committed through `3dc3671511530390f56419ae93b9d7bcd4fa5a6e` after code, test, and contract changes. GitHub Actions validation for that exact head has not yet been observed, so validation and merge are not claimed.

README projection remains to be updated before task completion.

No live ELAN runtime connection is claimed. Existing Run 2 evidence proves StegVerse-side ELAN-shaped SDK processing only.

## Non-claims

This task does not claim:

- a live ELAN endpoint;
- ELAN credentials or authentication;
- a bidirectional ELAN runtime session;
- direct machine-to-machine interoperability until independently observed;
- dependency, gating, or completion authority over Run 3;
- that Run 3 experimental semantics are finalized.
