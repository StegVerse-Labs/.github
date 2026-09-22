# MIR / StegVerse Reference Architecture Workstream

Canonical Goal Task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
Canonical handoff: `docs/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_MIRROR_HANDOFF.md`
COSV: `50000000100000`

This directory contains the post-v0.3 public reference-architecture work for governable/insurable agents based on explicit separation of powers.

Current artifact:

- `SEPARATION_OF_POWERS_REFERENCE_ARCHITECTURE_DRAFT.md` — draft v0.2 containing the StegVerse actor/authority graph, common receipt envelope, per-corner proof scopes and proof ceilings, prohibited authority collapses, six-corner conformance matrix, minimum fail-closed negative tests, runtime-proof composition rule, evidence-status discipline, and MIR convergence package.
- `AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md` — joint-review evidence reconciliation for AILeash/sebbi.pro, Appendix A R4/R10, and Justin Dobson witness-topology claims. Canonical child task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`; handoff: `docs/MIR_AILEASH_WITNESS_EVIDENCE_RECONCILIATION_MIRROR_HANDOFF.md`.
- `AGENTENVELOPE_DERIVED_AUTHORITY_MAP.md` — independent public-source mapping of AgentEnvelope deterministic derived authority, legitimacy, lifecycle ordering, and re-derived evidence against StegVerse RTG/GTG/TT/AE, InTr, identity, and custody boundaries. Canonical child task: `MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001`; handoff: `docs/MIR_AGENTENVELOPE_DERIVED_AUTHORITY_RECONCILIATION_MIRROR_HANDOFF.md`.

Current discipline:

- seam conformance is not runtime-chain proof;
- evidence custody/reconstruction remains independent of governance, admission, execution, credential/provider authority, and observability;
- counterpart/operator claims remain attributed until independently evidenced;
- the Appendix A R4 exact positive live-tip behavior is independently reproduced for one retained peer/tip;
- sebbi.pro's historical witness vocabulary portability gap is source-inspected;
- historical source recovery now establishes that witness v1.1 vocabulary definitions and its peer legend coexist with chain commitment-scheme source at commit `2d6715868bb2812b98d874ab17890ff89ece30d5`; the later v1.3 witness-specific spec route does not establish absence of earlier publication. The previously unresolved `f824ac83c5843053bdeca7eba53b77afa99465f5` is a retrievable Git blob, not a commit. Exact coverage of disputed historical commitments remains unresolved, so neither blanket R10 failure nor compliance is independently promoted;
- Evidence Custody Seam v0.7 carries explicit `Operator-disclosed`, `Demonstrated`, and `Third-party checkable` evidence classes per Appendix row and narrows A.2 R10 to the artifact/SHOULD condition while keeping the full failure as operator disclosure pending the R6-linked publication answer;
- v0.7 also makes MIRegistry A.1 R2 explicitly operator-disclosed because the earlier recorded run did not complete an end-to-end chain walk;
- user-retained v0.8 review-thread evidence now reports that the submitter-removed rerun exists and exercised a live production export plus an adversarial local case; Richard reports 1,534 events, 50 checkpoints, 48 Bitcoin-anchored checkpoints, 1,406 events under an anchor, offline OTS binding for checkpoint 4714, full leaf/inclusion recomputation, chain continuity, separate-endpoint key pinning, zero socket-family syscalls after correcting two trace-counting mistakes, proof-derived ordering distinct from claimed timestamps, and fail-closed negative controls;
- those v0.8 run results remain `COUNTERPART_REPORTED` until the underlying bundle, OTS proof, inclusion proofs, key-pinning evidence, explorer records, traces, adversarial fixtures, and negative-control outputs are independently retrieved and recomputed;
- `custodian` remains the canonical neutral role term; no specific privacy-regime collision is established in the supplied material;
- OpenTimestamps pending/submission state is not Bitcoin confirmation unless the specific proof and attested block path are independently checked;
- witness count is not control/failure-domain independence;
- AgentEnvelope construction-bound derived authority is recorded as external corroborating architecture, not imported StegVerse authority; deterministic derivation does not by itself prove temporal ordering or governed transition execution;
- AgentEnvelope deterministic re-derivation reconciliation is complete: current Master Records canonical-object/self-hash verification and reconstruction semantics already represent recomputation from canonical inputs, so the disposition is `NO_SOURCE_MUTATION_REQUIRED`; no new evidence authority or schema was added.

The 2026-09-19 targeted acquisition pass identified the MIR transparency locator and authenticated sebbi.pro block/export boundary, but retrieved neither exact disputed blocks nor the authentic v0.8 package. See the [canonical handoff](../MIR_AILEASH_WITNESS_EVIDENCE_RECONCILIATION_MIRROR_HANDOFF.md) for the exact operator export/package inputs and subsequent verification checks. Retrieval limitations do not change evidence classifications.

Generation 70 continuation: complete-tree inspection of AILeash v1.1 source revision `2d6715868bb2812b98d874ab17890ff89ece30d5` did not expose an authentic disputed historical sealed-block/export corpus, and fresh public searches did not expose the reported 1,534-event / 50-checkpoint v0.8 package. R10 therefore remains operator-disclosed, the rerun remains counterpart-reported complete, and the historical 784-record / 30-commitment run remains settled without reinterpretation.

Generation 86 continuation: newly published AILeash `walk.py` and `disclosure.py` source establishes a source-level public walk for the post-2026-09-07 chain and an explicit reset boundary, while leaving the earlier chain's final tip/height unrecorded in the disclosure. This improves current-chain verifiability but does not bridge disputed pre-reset commitments to the recovered v1.1 vocabulary/scheme revision; R10 and v0.8 evidence classifications therefore remain unchanged.
