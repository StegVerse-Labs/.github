# MIR × StegVerse Separation-of-Powers Evidence Contract Mirror Handoff

Updated: 2026-09-10

## Canonical task

Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`

Canonical contract candidate: `docs/contracts/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_v0.3.md`

Status: ACTIVE — StegVerse accepts the exact v0.3 convergence candidate for freeze; bilateral freeze remains pending explicit MIR acceptance of the same artifact. StegVerse implementation and conformance measurement continue as process work under the accepted contract and are not prerequisites to StegVerse acceptance.

## Constitutional invariant

Three powers remain distinct:

1. MIR holds authoritative historical custody.
2. StegVerse determines admissibility/governance now.
3. Provenance proves bounded acts, commitments, observations, and decisions without silently conferring either custody or governance authority.

No participant may combine authoritative historical custody with governance authority over the same subject and decision context. Separation must hold on the wire, at rest, and during reconstruction.

## Converged interface decisions

- MIR evidence surface: `POST /v1/policy/standing`.
- `POST /v1/policy/evaluate` and recommendation-capable equivalents are outside this contract.
- MIR evidence responses must be verdict-free; governance terms such as ALLOW, DENY, STEP_UP, ADMISSIBLE, INADMISSIBLE, recommendedAction, policyDecision, governanceDecision, and semantic equivalents are out of contract.
- `entityRef` is opaque; StegVerse must not infer identity semantics from the digest.
- StegVerse reads current head for a new decision, verifies evidence, applies predicate-owned freshness, and pins the exact `seq + tip` used.
- Reconstruction uses the pinned checkpoint and never silently substitutes a newer head.
- StegVerse retains only the minimum evidence reference/proof material required to reproduce its decision; it must not accumulate or reconstruct an alternate MIR historical ledger.
- `standing.tier` is allowed only as a named deterministic historical classification with all required inputs independently reproducible; it is not governance.
- Claim summary values are `NONE_RECORDED | FLAGGED | CONTESTED`; `NONE_RECORDED` is not exoneration, trust, safety, verification, or admissibility.
- Proof state is explicit: `NOT_REQUESTED | UNAVAILABLE | PROVIDED`; null/empty proof never means verified.
- Unknown proof/leaf scheme is a hard evidence-verification failure with no downgrade.
- Proof failure is an evidence state (`EVIDENCE_UNVERIFIED`), not automatically a governance DENY.
- Witness requirements are StegVerse predicate policy; witness attestations remain independently verifiable evidence and carry no governance authority.

## Shipped versus TO-BUILD boundary

Shipped by MIR, per convergence candidate:

- verdict-free `POST /v1/policy/standing` standing surface;
- raw standing signals;
- claims summary;
- committed checkpoint pin.

TO-BUILD / not yet proven shipped:

- `atSeq` / `atTip` historical checkpoint selection;
- explicit `includeProof` and `proofStatus` behavior;
- `claimDetailMode` minimum-necessary detail path;
- inclusion proof with typed audit path and declared leaf scheme;
- signed witness-attestation envelope and key-lifecycle metadata;
- shared `mir.leaf.v3` cross-implementation conformance fixture.

Until inclusion proof and witness surfaces are shipped, `witnesses[]` must remain empty and `proofStatus` must report only `NOT_REQUESTED` or `UNAVAILABLE` as appropriate.

## StegVerse implementation and conformance process

The contract defines the interface and normative behavior. Measuring whether StegVerse, MIR, or another implementation conforms to that contract is a StegVerse process concern and does not alter the accepted contract semantics.

The following work implements and measures conformance to the accepted interface; it is not a prerequisite to StegVerse accepting v0.3 for freeze:

1. Materialize schemas for `mir.evidence.v0`, `mir.proof.v0`, `stegverse.mir-reference.v0`, and `stegverse.governance-decision.v0` without importing MIR history custody.
2. Implement an evidence-intake validator that rejects verdict-bearing MIR payloads before governance evaluation.
3. Implement checkpoint selector mismatch handling as a technical evidence state, never a governance verdict.
4. Implement canonical checkpoint-tip serialization and scheme-bound v1/v2/v3 Merkle verification with unknown-scheme hard failure.
5. Implement predicate-owned freshness evaluation and read-head-then-pin semantics.
6. Implement the StegVerse MIR reference record as a decision-dependency reference, with explicit prohibition on historical replication.
7. Keep the StegVerse governance decision record separate from MIR evidence/reference storage.
8. Implement configurable witness requirements separately from MIR.
9. Build negative fixtures for authority collapse, proof overclaim, selector mismatch, stale evidence, unsupported scheme, invalid path, missing witness, and prohibited historical replication.
10. Establish shared `mir.leaf.v3` fixture reproduction with MIR and a third implementation once MIR provides the required canonical event-core fixtures.

The shared v3 fixture is therefore a conformance measurement of the frozen interface. Failure of a tested implementation to reproduce it indicates implementation nonconformance or an implementation defect to investigate; it does not silently rewrite the frozen contract.

## External MIR-dependent implementation conditions

These conditions do not stop StegVerse acceptance or StegVerse-side implementation:

- confirm MIR canonical checkpoint and `canonicalEventCore` fixtures;
- confirm the StegVerse integration `entityRef` derivation profile/privacy properties;
- MIR ships v0.3 standing extensions;
- MIR ships inclusion-proof response;
- MIR ships signed witness-attestation envelope and applicable OTS reference.

StegVerse can complete validators, schemas, canonicalization, reference/custody enforcement, freshness/witness policy surfaces, negative fixtures, and adapter contracts before those MIR surfaces are live.

## Collision / adjacent work

`StegVerse-Labs/Standing-Proof-Engine` is adjacent but not authoritative for this contract. Its existing handoff concerns SDK-to-SPE commitment intake and SPE standing receipts. Do not merge MIR historical evidence custody into SPE standing semantics.

`SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003` is adjacent because MIR evidence can enter a generic manifested path, but this contract defines the custody/governance/provenance authority discipline that the adapter must preserve.

## Freeze state

StegVerse acceptance: `ACCEPTED_FOR_FREEZE` for the exact v0.3 convergence-candidate artifact currently recorded at `docs/contracts/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_v0.3.md`.

Bilateral contract state: not yet claimed frozen. Freeze occurs when MIR explicitly accepts the same exact artifact/version. No additional StegVerse conformance test, implementation result, runtime evidence, proof availability, witness availability, or deployment result is required to make StegVerse's acceptance effective.

After bilateral freeze, implementation and conformance work continues against the frozen v0.3 target. Any later normative change requires an explicitly versioned successor contract rather than silently changing the v0.3 target during testing.

No MIR acceptance, bilateral freeze, runtime, deployment, proof availability, witness availability, or implementation conformance is claimed without corresponding evidence.
