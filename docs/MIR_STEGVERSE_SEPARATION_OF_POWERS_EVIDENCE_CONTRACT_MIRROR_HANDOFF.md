# MIR × StegVerse Separation-of-Powers Evidence Contract Mirror Handoff

Updated: 2026-09-11

## Canonical task

Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`

Frozen contract: `docs/contracts/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_v0.3.md`

Status: ACTIVE — v0.3 is bilaterally frozen. StegVerse and MIR have both accepted v0.3. Implementation and conformance work proceeds against that fixed normative target and does not alter the frozen text.

Freeze evidence: `evidence/mir-stegverse-v0.3-bilateral-freeze-2026-09-10.md`

## Shared Docs reconciliation — 2026-09-11

The Shared Docs text supplied by the user contains the same v0.3 normative contract in two representations: a full long-form copy followed by a condensed copy labeled as verbatim. The GitHub canonical contract stores one Markdown-formatted long-form representation.

Accordingly:

- the Shared Docs paste and GitHub contract are substantively/normatively aligned on v0.3;
- the Shared Docs paste is not byte-for-byte identical to the GitHub Markdown artifact because of duplication and formatting differences;
- bilateral freeze evidence establishes mutual acceptance of the v0.3 normative contract/version and no post-freeze normative amendment;
- do not claim a cross-system byte-identical document hash unless MIR and StegVerse explicitly agree one canonical serialization/hash;
- the GitHub file remains StegVerse's canonical implementation target and must not be silently edited to reflect later implementation notes.

The status line inside the frozen text still reads `Convergence candidate — not frozen until mutual agreement`. That line is part of the mutually reviewed candidate text and is not rewritten after the fact. Current freeze state is carried by this handoff and the freeze-evidence record so the accepted normative text remains unchanged.

## Constitutional invariant

Three powers remain distinct:

1. MIR holds authoritative historical custody.
2. StegVerse determines admissibility/governance now.
3. Provenance proves bounded acts, commitments, observations, and decisions without silently conferring either custody or governance authority.

No participant may combine authoritative historical custody with governance authority over the same subject and decision context. Separation must hold on the wire, at rest, and during reconstruction.

## Frozen interface decisions

- MIR evidence surface: `POST /v1/policy/standing`.
- `POST /v1/policy/evaluate` and recommendation-capable equivalents are outside this contract.
- MIR evidence responses must be verdict-free; governance terms such as ALLOW, DENY, STEP_UP, ADMISSIBLE, INADMISSIBLE, recommendedAction, policyDecision, governanceDecision, and semantic equivalents are out of contract.
- `entityRef` is opaque; StegVerse must not infer identity semantics from the digest.
- StegVerse reads current head for a new decision, verifies evidence, applies predicate-owned freshness, and pins the exact `seq + tip` used.
- Reconstruction uses the pinned checkpoint and never silently substitutes a newer head.
- StegVerse retains only the minimum evidence reference/proof material required to reproduce its decision; it must not accumulate or reconstruct an alternate MIR historical ledger.
- `standing.tier` is only a named deterministic historical classification with reproducible required inputs; it is not governance.
- Claim summary values are `NONE_RECORDED | FLAGGED | CONTESTED`; `NONE_RECORDED` is not exoneration, trust, safety, verification, or admissibility.
- Proof state is explicit: `NOT_REQUESTED | UNAVAILABLE | PROVIDED`; null/empty proof never means verified.
- Unknown proof/leaf scheme is a hard evidence-verification failure with no downgrade.
- Proof failure is an evidence state (`EVIDENCE_UNVERIFIED`), not automatically a governance DENY.
- Witness requirements are StegVerse predicate policy; witness attestations remain independently verifiable evidence and carry no governance authority.

## Shipped versus TO-BUILD boundary

Shipped by MIR, as confirmed at freeze:

- verdict-free `POST /v1/policy/standing` standing surface;
- live standing signals;
- current claim status/summary data;
- committed checkpoint pin.

TO-BUILD / not yet proven shipped:

- `atSeq` / `atTip` historical checkpoint selection;
- explicit `includeProof` and `proofStatus` behavior;
- `claimDetailMode` minimum-necessary detail path;
- inclusion proof with typed audit path and declared leaf scheme;
- signed witness-attestation envelope and key-lifecycle metadata;
- shared `mir.leaf.v3` cross-implementation conformance fixture.

Until inclusion proof and witness surfaces are shipped, `witnesses[]` remains empty and `proofStatus` must report only `NOT_REQUESTED` or `UNAVAILABLE` as appropriate.

## MIR 12.3 implementation note — non-normative

MIR confirmed after freeze that `mir.evidence.v0` is the target response shape. The current live `/policy/standing` response uses live fields including:

- `standing.signals.partnerEventCount`
- `standing.signals.effectivePartnerEventCount`
- `standing.signals.intraOrgTier`
- `claimStatus.activeClaims`
- `claimStatus.riskLevel`

Section 12.3 implementation therefore includes mapping the live response into the frozen `mir.evidence.v0` envelope.

This is an implementation mapping note only. It does not modify the frozen v0.3 contract and must not be treated as permission to silently change the target schema.

## StegVerse implementation and conformance process

The contract defines the interface and normative behavior. Measuring whether StegVerse, MIR, or another implementation conforms to that contract is a StegVerse process concern and does not alter the frozen contract semantics.

Current implementation/conformance work:

1. Materialize schemas for `mir.evidence.v0`, `mir.proof.v0`, `stegverse.mir-reference.v0`, and `stegverse.governance-decision.v0` without importing MIR history custody.
2. Implement an evidence-intake validator that rejects verdict-bearing MIR payloads before governance evaluation.
3. Implement checkpoint selector mismatch handling as a technical evidence state, never a governance verdict.
4. Implement canonical checkpoint-tip serialization and scheme-bound v1/v2/v3 Merkle verification with unknown-scheme hard failure.
5. Implement predicate-owned freshness evaluation and read-head-then-pin semantics.
6. Implement the StegVerse MIR reference record as a decision-dependency reference, with explicit prohibition on historical replication.
7. Keep the StegVerse governance decision record separate from MIR evidence/reference storage.
8. Implement configurable witness requirements separately from MIR.
9. Build negative fixtures for authority collapse, proof overclaim, selector mismatch, stale evidence, unsupported scheme, invalid path, missing witness, and prohibited historical replication.
10. Build the shared `mir.leaf.v3` conformance fixture with MIR and a third implementation once the required canonical event-core fixture is available.

The shared v3 fixture is the next concrete joint step identified by MIR. Failure of an implementation to reproduce the frozen fixture is conformance evidence about that implementation; it does not rewrite the contract.

## External MIR-dependent implementation conditions

These conditions do not alter the frozen contract and do not stop StegVerse-side work:

- confirm MIR canonical checkpoint and `canonicalEventCore` fixtures;
- confirm the StegVerse integration `entityRef` derivation profile/privacy properties;
- MIR ships v0.3 standing extensions;
- MIR ships inclusion-proof response;
- MIR ships signed witness-attestation envelope and applicable OTS reference.

## Collision / adjacent work

`StegVerse-Labs/Standing-Proof-Engine` is adjacent but not authoritative for this contract. Its existing handoff concerns SDK-to-SPE commitment intake and SPE standing receipts. Do not merge MIR historical evidence custody into SPE standing semantics.

`SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003` is adjacent because MIR evidence can enter a generic manifested path, but this contract defines the custody/governance/provenance authority discipline that the adapter must preserve.

## Freeze state

StegVerse acceptance: v0.3 accepted for freeze.

MIR acceptance: explicit acceptance received; MIR stated it was freezing v0.3 on its side as well.

Bilateral contract state: `FROZEN_V0_3`.

The frozen normative target remains `docs/contracts/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_v0.3.md`. No textual amendment is implied by the section 12.3 build note, Shared Docs formatting/duplication, or later conformance work.

Any later normative change requires an explicitly versioned successor contract rather than silently changing v0.3 during implementation or testing.

No claim is made that sections 12.3, 12.5, 12.6, or 12.8 are implemented, validated, deployed, or runtime-proven solely because the contract is frozen.
