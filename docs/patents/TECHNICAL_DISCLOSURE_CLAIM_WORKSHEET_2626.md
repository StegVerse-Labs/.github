# Patent technical disclosure and claim-development worksheet — physical-emission provenance

Parent: StegVerse-Labs/.github#2626. Research and invention-disclosure draft; **not a patent filing, legal opinion, or assertion of novelty**. Counsel should determine claim scope and filing strategy. Existing related files: `PHYSICAL_EMISSION_FORMALISM_MAPPING_2626.md` and `CLAIM_PATHS_RTG_OBSERVATION_2626.md`.

## Problem and technical distinction
A sensor can observe a physical emission without establishing the emitter's identity. Original acquisition evidence, subsequent reconstruction, and comparison of two evidentiary histories are separate technical operations. Conventional hashes establish consistency of committed bytes, not physical truth; clock readings from different origins cannot silently be collapsed. The proposed system makes these distinctions explicit, machine-checkable, and reconstructable.

## Shared data model (candidate embodiment)
`Observation`: immutable index, modality, bounded measurement payload (e.g., frequency/time-domain characteristics), unit, uncertainty, sensor/acquisition identity, capture scope, calibration reference, device-time coordinate, system-time coordinate, optional heartbeat coordinate and their respective confidence/drift bounds.

`Acquisition`: capture ID, authenticated recorder/source binding, start/finish commitments, ordered observations, canonical encoding version, digest algorithm, adjacent-transition receipts, evidence locator and integrity manifest, attribution status (KNOWN/UNKNOWN/DISPUTED), and attribution evidence if any.

`TransitionReceipt`: capture ID, adjacent indices `i,i+1`, hashes of the two canonical observation records, transition digest, preceding receipt reference, acquisition scope and receipt version. For N>=2 observations, exactly N-1 adjacent transitions; empty or single-snapshot acquisitions must be separately typed rather than claiming a transition.

`Reconstruction`: source capture/receipt identities, verified portions, missing/corrupt intervals, reconstruction method and parameters, uncertainty, derived artifact identity, and a flag that distinguishes source completeness from derived coverage.

`Comparison`: references to two or more source/derived artifacts, ancestry graph, time-basis alignment method, feature comparison with error bounds, independence status (SUPPORTED/NOT_ESTABLISHED/DISPROVED), divergences and an independently committed result receipt.

## Claim path A — acquisition and attestation
1. Bind an acquisition device or recorder and scope without requiring knowledge of the physical emitter.
2. Observe a finite sequence and retain distinct time bases and uncertainty.
3. Canonicalize each observation under a versioned schema.
4. Construct adjacent-pair transition records and integrity-linked receipts.
5. Commit start/finish and evidence manifest, retaining UNKNOWN emitter attribution when necessary.
6. Verify that missing or altered observations/receipts fail original-chain integrity without erasing valid original data.

**Candidate independent method claim structure:** receiving sensor observations of a physical emission; binding an acquisition origin and bounded capture context; producing versioned adjacent-transition commitments from the ordered observations; retaining non-equivalent time coordinates and uncertainty; emitting a verifiable evidence manifest separately from physical-emitter attribution.

**Dependent-claim candidates:** heterogeneous sensors; frequency composition vectors; drift-bounded clock alignment; heartbeat coordinates; content-addressed evidence locators; tamper/missing-receipt detection; privacy-preserving attribution.

## Claim path B — replay and reconstruction
1. Receive a pre-existing acquisition manifest and finite receipt set, without requiring live sensing.
2. Verify original commitments and explicitly identify unavailable or contradictory portions.
3. Reconstruct only supported observations/intervals; optional inference is labeled derived.
4. Bind the method, parameters, gap map, uncertainty and original source references to a new identity.
5. Emit a reconstruction receipt without upgrading the original evidence completeness.

**Candidate independent method claim structure:** verifying an existing receipt-bound physical-emission observation sequence; constructing a bounded replay representation from authenticated portions; producing separately identified derived intervals with explicit uncertainty; committing reconstruction lineage and completeness status without replacing source evidence.

**Dependent-claim candidates:** deterministic replay; selective reconstruction; alternate time bases; gap-aware interpolation; reconstruction reproducibility checks; comparison to raw sensor artifacts.

## Claim path C — comparative reconstruction
1. Receive two or more original or derived evidence packages.
2. Verify each source lineage and identify shared ancestry.
3. Align comparable time/frequency features under bounded error rather than silently treating timestamps as identical.
4. Compute agreement, divergence and unknown regions.
5. Explicitly classify whether independent acquisition is supported, disproved, or not established.
6. Commit the comparison receipt with references, methods, uncertainties and independence qualification.

**Candidate independent method claim structure:** verifying plural provenance-bound physical-emission histories; determining shared derivation ancestry; aligning measurement features with uncertainty bounds; generating a comparison artifact that separately encodes similarity, disagreement and source-independence standing.

**Dependent-claim candidates:** cross-modality comparison; common-ancestor detection; frequency signature alignment; non-synchronized clock intervals; degraded-source comparison; anti-circular corroboration checks.

## Distinct technical boundaries and non-claims
- A, B and C are independently operable. No SV-011, TT capability derivation, GTG disposition, SDK, network, hosted machine, second device, or governance framework is a prerequisite for their underlying mechanisms.
- Optional governed publication, attribution, or downstream execution remains a separate consumer transition; authorization never retroactively changes original evidence.
- UNKNOWN physical emitter does not mean UNKNOWN authenticated recorder. RTG source-known terminology requires source-owner reconciliation before claiming canonical equivalence.
- A digest alone does not establish sensor accuracy, emitter identity, clock truth, or independent acquisition.
- Synthetic PE-01..08 fixtures are bounded model tests, not actual sensor evidence, novelty confirmation, enablement demonstration, or production certification.

## Figure specifications for drafting
- **Fig. 1:** Recorder/sensor -> bounded observation capture -> canonicalizer -> adjacency/receipt builder -> immutable evidence manifest; parallel emitter-attribution UNKNOWN path.
- **Fig. 2:** Three separate device/system/heartbeat clock tracks, each with uncertainty bands; alignment as an explicit derived mapping.
- **Fig. 3:** Original receipt chain -> verification -> missing-region map -> replay engine -> separately identified reconstruction receipt.
- **Fig. 4:** Two evidence ancestry trees converging at a shared ancestor; comparator emits NOT_ESTABLISHED independence despite distinct artifact IDs.
- **Fig. 5:** Independent A/B/C interfaces feeding an optional governed consumer; DENY publication does not alter original capture.

## Evidence needed before filing assertions
- Establish earliest conception and public-disclosure chronology, inventor(s), and exact supporting records.
- Produce a runnable reference implementation and golden canonical-byte vectors for A/B/C; current PE fixtures are illustrative models only.
- Test altered observations, missing receipts, clock conflicts, unknown emitter, partial replay, shared ancestry, and cross-sensor comparison.
- Obtain representative physical recordings or clearly identify prophetic embodiments where permitted; do not present synthetic data as empirical capture.
- Conduct documented prior-art search and counsel review for novelty, nonobviousness, enablement, written description, and claim differentiation.
- Confirm patent application type, jurisdiction, filing owner, deadlines, drawings, and inventor declarations.

## Filing gate
This worksheet advances technical disclosure but does **not** establish filing readiness. Defer SV-011 TT next-capability primitive under parent issue #2626, reference StegVerse-org/.github#68, and do not divert this patent work.
