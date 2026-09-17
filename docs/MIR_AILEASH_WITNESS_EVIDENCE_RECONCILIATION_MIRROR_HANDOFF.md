# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / EVIDENCE RECONCILIATION`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A R4 claims and Justin Dobson's witness-topology contribution. Preserve a strict distinction between independently observed public behavior, source-inspected implementation material, counterpart/self-reported claims, and claims not yet established.

## Current truth

The public sebbi.pro surfaces presently expose unauthenticated verification/witness routes including `/api/verify-chain`, `/x/witness/tip`, `/x/witness/peers`, and a published ordering-test document. Public responses explicitly bound their own claims: `self-consistent` is not third-party verification; witness roster membership is not endorsement or identity proof; OpenTimestamps submission is not Bitcoin confirmation; pending proofs remain pending.

The public AILeash source repository declares and implements a witness-attestation route `/x/witness/attest?peer=&tip=` and public witness topology modules. Source inspection establishes the route and intended semantics, not an authentic positive runtime attestation for the exact Appendix A live tip.

The Evidence Custody Seam Appendix A R4 positive-live claim remains `COUNTERPART_REPORTED` unless an exact live tip is independently queried through the acceptor read route and its positive response is retained. The public route's existence and unauthenticated design are independently/source-observed; the exact positive live-tip result described by Richard is not yet independently reproduced in this task.

The current public `/x/ots/status` response exposes stored proof attempts and distinguishes `pending` from confirmed. This is evidence that the service publishes bounded anchor status; it is not independent proof that a particular digest is in Bitcoin. No Bitcoin-anchor claim is promoted without independent proof verification.

Justin Dobson/AILeash/sebbi.pro linkage is strongly supported by public self-description and user-provided profile context, but identity/ownership claims from operator-controlled sources remain source-declared rather than independent identity verification.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`

## Next action

Obtain one exact current peer tip from an independently reachable peer or retained Appendix A test artifact; query the unauthenticated sebbi.pro witness-attest route for that exact peer/tip; retain the response and classify only the claims carried on its face. Separately verify any Bitcoin-confirmed proof with independent OpenTimestamps/Bitcoin verification material before promotion. Do not treat AILeash's own conformance JSON, README, profile text, or service status as independent proof of the claims they describe.
