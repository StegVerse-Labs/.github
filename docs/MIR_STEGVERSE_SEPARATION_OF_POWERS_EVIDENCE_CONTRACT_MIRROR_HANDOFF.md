# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / GOAL PROMPT 20 DECOMPOSED / CANONICAL MASTER RECORDS STATE-TRANSITION CUSTODY SUCCESSOR REGISTERED / AILEASH WITNESS EVIDENCE CHILD REGISTERED`

## Canonical state

The Goal Task remains active. Frozen v0.3 remains separate from post-freeze reference-architecture work. The architecture continues to enforce separation of governance, admission/state transition, execution, credential/provider authority, evidence custody/reconstruction, and observability. `SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF` remains unchanged.

The historically successful StegVerse-002 route remains the reusable execution pattern:

```text
EVENT
-> Universal InTr intent/materialization request
-> governed Node/outbox/ingress
-> Interlock/InTr admission
-> EVENT_EPHEMERAL runtime materialization
-> execution-time identity
-> governed transition consequence
-> state receipts
-> Master Records custody/reconstruction
```

The MIR lane must duplicate that event-triggered order before adding MIR-specific Goal/COSV, destination-profile, RTC-007/008/009, and governed-return requirements. WorkerCoordinator task control must not become a new event-creation prerequisite merely because MIR is registered as a canonical task.

## Canonical Master Records correction

Master Records recording of state change is not a test-only or MIR-specific diagnostic mechanism. The canonical progression contract already requires every governed state change to retain current decision/execution state evidence and reconstruct current state before autonomous progression continues.

This is now made explicit in:

- `control/canonical-master-records-state-transition-custody-contract.json`;
- `data/canonical-task-records/CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001.json`;
- `docs/CANONICAL_MASTER_RECORDS_STATE_TRANSITION_CUSTODY_MIRROR_HANDOFF.md`.

Canonical invariant:

```text
observe current state
-> propose exact next transition
-> Interlock/InTr governance now
-> TV/TVC now if required
-> retain ALLOW/DENY receipt
-> submit decision receipt to Master Records
-> if ALLOW execute/consume
-> retain execution/failure state receipt
-> submit exact state receipt to Master Records
-> reconstruct current state
-> continue to next governed transition
```

Master Records remains custody/reconstruction only. It may not grant transition, execution, credential, route, or governance authority and may not infer missing authorization from downstream evidence.

## MIR diagnostic reclassification

The recently added `workers/mir_roundtrip_transition_probe_worker.py` is temporary conformance/break-localization instrumentation only. Its packet fanout is not the canonical architecture for recording state.

MIR must consume the same canonical state-transition custody mechanism as every other StegVerse workload. The MIR probe may remain temporarily to compare expected transition order against canonical receipts while adoption is validated, then cease being required for correctness.

The Site MIR transport handoff was reconciled to this model at commit `758d19794f552486d2a466d742ad863cf9fcad27`.

## Goal-prompt-20 decomposition

Remaining implementation work is decomposed to canonical successor:

`CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`

That successor owns:

1. inventory of existing canonical state-receipt emitters and Master Records adapters;
2. one reusable canonical transition-custody API/contract;
3. binding Interlock/InTr decisions, execution states, and fail-closed states to that API;
4. MIR adoption without task-specific probe fanout as the primary custody path;
5. validation against the successful StegVerse-002 event-driven semantics;
6. propagation to other governed StegVerse transition consumers;
7. authentic runtime proof that each observed governed transition reaches Master Records custody/reconstruction.

The original separation-of-powers goal remains the parent architecture/evidence-contract lane; implementation adoption proceeds under the successor rather than extending this goal beyond Prompt 20.

A genuinely separable evidence-reconciliation child is also registered:

`MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`

That child owns AILeash/sebbi.pro/Justin Dobson public-evidence reconciliation for Appendix A R4 and witness-topology claims, with canonical map `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md` and handoff `docs/MIR_AILEASH_WITNESS_EVIDENCE_RECONCILIATION_MIRROR_HANDOFF.md`. It must not promote operator-controlled declarations, roster counts, pending OpenTimestamps states, or profile claims into stronger independent evidence.

A second genuinely separable external-architecture reconciliation child is now registered:

`MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001`

That child owns independent inspection of Matthew McPhillips's public AgentEnvelope derived-authority implementation and its bounded mapping to StegVerse RTG/GTG/TT/AE, Interlock/InTr, identity, and evidence-reconstruction semantics. It must not import AgentEnvelope authority, infer technical equivalence, or create duplicate StegVerse governance/custody machinery. Canonical map: `docs/mir-reference-architecture/AGENTENVELOPE_DERIVED_AUTHORITY_MAP.md`; handoff: `docs/MIR_AGENTENVELOPE_DERIVED_AUTHORITY_RECONCILIATION_MIRROR_HANDOFF.md`.

## Counterpart evidence still required

Separately from canonical custody adoption, independently checkable Bitcoin anchor/inclusion evidence and authentic MIR `mir.leaf.v3` independent reproduction remain pending. The AILeash/sebbi.pro reconciliation independently observed public witness/status surfaces and their bounded disclaimers, but the exact positive live-tip Appendix A attestation and the 784-record/30-commitment clean-room run remain counterpart evidence until independently retained or reproduced.

## Authority boundaries

- Interlock/InTr: current transition admission/state-transition authority.
- TV/TVC: credential authority where required.
- WorkerCoordinator: task control/ownership where required; not universal event-creation authority.
- execution runtime: performs only admitted consequences.
- Master Records: canonical observed-reality custody/reconstruction only.
- GitHub/GitHub Actions: source validation/evidence transport only; runtime authority `NONE`.

## Next action

Implementation continues under `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`.

Evidence reconciliation continues under `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`: obtain one exact positive witness-attest artifact for a known peer/tip if independently reachable, and independently verify a specific confirmed OpenTimestamps/Bitcoin proof before promoting either claim. Preserve current bounded public observations otherwise.

External derived-authority reconciliation continues under `MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001`: check whether deterministic re-derivation is already representable in current StegVerse evidence/verification and Master Records reconstruction schemas before any source mutation.
