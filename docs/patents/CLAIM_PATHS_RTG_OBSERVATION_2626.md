# Patent provenance claim-path mapping and RTG observation reconciliation

Parent: StegVerse-Labs/.github#2626. Research draft; not legal advice, proof, patent filing, or independent certification.

## RTG observation distinction
Existing RTG `docs/invariants.md` uses `observation_invariant = source_known and scope_known and frame_known`. For physical-emission evidence, **source** must mean authenticated acquisition source (recorder/custody/evidence locator), not the unknown physical emitter. Preserve explicit three-valued emitter attribution (KNOWN / UNKNOWN / DISPUTED) separately. Proposed interface predicate: `acquisition_source_bound AND observation_scope_bounded AND time_basis_bounded AND interpretation_frame_bounded`; emitter attribution is a separately evaluated assertion. Do not silently change RTG canonical invariant without RTG owner validation. An absent acquisition source is distinct from an unknown emitter. An unknown emitter must not prevent original capture, but must prevent unsupported attribution ALLOW.

## Three independently claimable technical mechanisms

### A. Acquisition and attestation
Input: sensor-neutral physical emission observations, source acquisition identity, bounded capture scope, device/system/HB timing coordinates, start/finish commitments. Operation: canonicalize finite observation records; commit each adjacent pair (N observations -> N-1 transitions); create receipt-bound hash chain with evidence locators and uncertainty. Output: verifiable evidence package independent of governance decisions. Novelty investigation: bounded multi-clock evidence commitment and cross-sensor transition preservation. Negative conditions: unknown emitter permitted; altered observation, missing required receipt or missing acquisition binding fails integrity. No claim that a hash establishes physical truth.

### B. Independent replay and reconstruction
Input: previously committed evidence and receipts; no new live sensor needed. Operation: verify original commitments; reconstruct only supported observations/intervals; when incomplete, issue separately identified derived projection with gaps, method, uncertainty, and source references. Output: independently verifiable reconstruction or explicit degraded status. Negative conditions: missing receipt never silently repaired; derived projection cannot claim original identity or completeness. No external device/machine prerequisite.

### C. Comparative reconstruction
Input: two or more independently identified evidence packages or derived projections. Operation: verify each lineage and provenance, compare bounded frequency/time features with uncertainty; identify common ancestry and incompatible time bases before claiming independence or causal attribution. Output: comparison receipt with agreement, divergence, unknowns, and dependence qualifiers. Negative conditions: distinct artifact IDs alone do not prove independent acquisition; common ancestor disallows independent-source claim.

## Governance and formalism boundaries
RTG geometry/AE resolution may characterize transitions and admissible granularity; GTG -> TT determines optional governed use and allocation; STCM governs closure of governed transitions, not every capture; IICT remains unproven. A DENY publication/attribution result cannot mutate original capture. An ALLOW governance result alone cannot execute a transition. All attempted governed transitions require ALLOW, DENY or FAIL_CLOSED in ecosystem runtime mapping; research contract DEFER/TRANSFORM/TERMINATE must be explicitly translated at the governed execution boundary without implicit ALLOW.

## Evidence and validation limits
The PE-01..08 tests are synthetic integrity and policy-separation fixtures, not instrument calibration, real physical capture, production SDK execution, cross-repo contract certification or legal novelty search. Further work: source-bound RTG proposal in its owning registry, golden vectors for canonical serialization, physical recordings across heterogeneous sensors, temporal drift bounds, independent replay implementation, prior-art review, and claim drafting by patent counsel.
