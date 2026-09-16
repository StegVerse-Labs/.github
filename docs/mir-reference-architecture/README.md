# MIR / StegVerse Reference Architecture Workstream

Canonical Goal Task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
Canonical handoff: `docs/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_MIRROR_HANDOFF.md`
COSV: `50000000100000`

This directory contains the post-v0.3 public reference-architecture work for governable/insurable agents based on explicit separation of powers.

Current artifact:

- `SEPARATION_OF_POWERS_REFERENCE_ARCHITECTURE_DRAFT.md` — draft v0.2 containing the StegVerse actor/authority graph, common receipt envelope, per-corner proof scopes and proof ceilings, prohibited authority collapses, six-corner conformance matrix, minimum fail-closed negative tests, runtime-proof composition rule, evidence-status discipline, and MIR convergence package.

Current discipline:

- frozen v0.3 text is not changed by this draft;
- seam conformance is not runtime-chain proof;
- every receipt has a bounded proof scope and proof ceiling;
- evidence custody/reconstruction remains independent of governance, admission, execution, credential/provider authority, and observability;
- physical co-location is allowed only when semantic authority separation and attribution remain intact;
- counterpart claims remain `COUNTERPART_REPORTED` until concrete artifacts are verified;
- the newer MIR Bitcoin-anchor statement is not promoted to verified evidence until an authentic anchor/inclusion artifact is supplied;
- the child `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` remains incomplete until authentic MIR independent reproduction is observed;
- the historically successful StegVerse-002 Node -> Interlock -> InTr -> bounded event-ephemeral runtime -> Master Records reconstruction route is reusable engineering evidence and must be duplicated before adding MIR-specific requirements rather than being re-proved as a generic gate;
- historical SV002 receipts prove that prior route only and grant no present transition authority, so fresh evidence remains required for the current MIR-bound invocation and new transitions.

The active transport successor now binds that duplicate-first order through `StegVerse-Labs/Site/data/mir-roundtrip-egress-sv002-route-binding.v1.json`. One-way MIR transport evidence is scoped to the current Goal/COSV binding, MIR destination-profile binding, final StegVerse-side egress, authentic Interlock/InTr egress, MIR MIRROR far-side transition, destination evidence, and Master Records reconstruction of the current final exit transition. Governed-return and full round-trip predicates are evaluated only after that duplication succeeds.

Draft v0.2 adds a concrete negative-test baseline: governance ALLOW must not become execution proof; admission without an execution record stays unexecuted/unproven; executor self-report cannot substitute for independent custody when required; provider-session success cannot admit a state transition; custody cannot authorize new work; and observability cannot promote liveness into execution proof.
