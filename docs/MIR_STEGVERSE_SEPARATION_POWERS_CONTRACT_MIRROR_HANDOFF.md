# MIR × StegVerse Separation-of-Powers Contract Mirror Handoff

Status: ACTIVE

Goal Task ID: `MIR-STEGVERSE-SEPARATION-POWERS-CONTRACT-001`
Repository: `StegVerse-Labs/.github`

## Goal
Converge, freeze, and implement the MIR × StegVerse Separation-of-Powers Evidence Contract so MIR remains authoritative historical custodian, StegVerse remains governor of admissibility, and provenance proves bounded acts/commitments/observations without transferring either authority.

## Current truth
- Richard Whitney/MIR accepted the constitutional invariant and Sections 1–4 in the supplied v0.2 draft.
- MIR requested convergence around the existing verdict-free `POST /v1/policy/standing` surface, opaque body-carried `entityRef`, complete raw standing inputs, `NONE_RECORDED | FLAGGED | CONTESTED`, `mir.leaf.v3`, scheme-bound interior-node folding, and honest SHIPPED versus TO-BUILD proof status.
- The proof surface remains TO-BUILD until MIR ships an inclusion-proof response and signed witness-attestation envelope.
- StegVerse-side finalization additionally requires explicit checkpoint-selector conflict semantics, proof-availability semantics, claim-detail minimum-necessary disclosure, witness-key lifecycle semantics, canonical byte serialization, and the invariant that a MIR-derived classification never gains governance authority merely because StegVerse reaches the same result.

## Current artifact
`docs/contracts/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_v0.3-rc1.md`

## Completion conditions
1. Mutual agreement to freeze the contract text.
2. Canonical contract artifact merged with README reference.
3. MIR inclusion-proof endpoint and witness-attestation envelope implemented with evidence.
4. StegVerse verifier consumes the contract without historical-custody replication.
5. Shared `mir.leaf.v3` conformance fixture reproduces the same tree/checkpoint independently in MIR, StegVerse, and a third implementation.

## Nonclaims
- Contract convergence is not proof-surface deployment.
- A checkpoint pin is not an inclusion proof.
- Empty `witnesses[]` is not witness verification.
- MIR evidence classifications do not become StegVerse governance decisions.
