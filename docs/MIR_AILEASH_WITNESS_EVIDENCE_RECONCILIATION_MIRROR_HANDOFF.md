# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / EXACT PEER TIP ACQUIRED / PLACEHOLDER ATTEST + OTS REQUESTS INVALIDATED`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A R4 claims and Justin Dobson's witness-topology contribution. Preserve a strict distinction between independently observed public behavior, user-provided public responses, source-inspected implementation material, counterpart/self-reported claims, and claims not yet established.

## Current truth

The user supplied the public response from `https://www.flavorflowstrategy.uk/witness.json`:

- chain: `flavorflowstrategy.uk`
- tip: `27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`
- updated_at: `2026-08-13T13:11:06Z`

This provides an exact peer/tip pair for the next witness-attest replay.

The subsequent sebbi.pro request did NOT test that tip. It used the literal placeholder `tip=PASTE_TIP`. sebbi.pro correctly echoed `tip=paste_tip` and returned `witnessed=false`. That response is input-validation/lookup evidence for the literal placeholder only and MUST NOT be treated as a negative finding for the real flavorflow tip.

The exact corrected witness request is:

`https://sebbi.pro/x/witness/attest?peer=flavorflowstrategy.uk&tip=27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`

The user also supplied `/x/ots/list`, containing 50 concrete numeric stamp IDs and proof routes. The subsequent `/x/ots/proof` request used the literal placeholder `ts=STAMP_ID`, producing `bad_stamp_id`. That is not evidence that any listed proof is missing, bad, pending, or unconfirmed.

A valid next OTS retrieval must substitute an actual numeric stamp ID, for example:

`https://sebbi.pro/x/ots/proof?ts=1789455657`

However, `/x/ots/list` itself does not declare whether that proof is confirmed. The returned proof JSON must be inspected first. Only a proof whose `state` is `confirmed` and which exposes raw `ots_base64`/Bitcoin block-height material should proceed to independent OpenTimestamps verification. A service-reported `confirmed` state alone is still not the final independent Bitcoin proof.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`

Latest evidence-map commit: `d7ea68fc0b5c627de4b0711fa5084df7e4620434`.

## Next action

1. Fetch the exact corrected witness-attest URL above and retain the JSON response.
2. If positive, classify only the exact fields returned; do not infer identity/control-domain independence from the result.
3. Fetch one real numeric `/x/ots/proof?ts=<stamp_id>` URL from the supplied list.
4. If that proof is pending, move to an older listed stamp and repeat until a proof reports `state=confirmed`.
5. Retain the complete confirmed proof JSON, decode `ots_base64`, bind it to the returned `tip`/`digest_sha256`, and verify it with a standard OpenTimestamps client against Bitcoin before promoting the Bitcoin-anchor claim.

No architecture or evidence-status promotion is permitted from placeholder responses.
