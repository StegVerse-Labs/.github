# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / EVIDENCE RECONCILIATION / CURRENT WITNESS + OTS ATTEMPT RECORDED`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A R4 claims and Justin Dobson's witness-topology contribution. Preserve a strict distinction between independently observed public behavior, source-inspected implementation material, counterpart/self-reported claims, and claims not yet established.

## Current truth

The public sebbi.pro surfaces presently expose unauthenticated verification/witness routes including `/api/verify-chain`, `/x/witness/tip`, `/x/witness/peers`, and a published ordering-test document. Public responses explicitly bound their own claims: `self-consistent` is not third-party verification; witness roster membership is not endorsement or identity proof; OpenTimestamps submission is not Bitcoin confirmation; pending proofs remain pending.

On the current 2026-09-17 observation, `/x/witness/peers` returned six peers rather than the five seen previously. `flavorflowstrategy.uk` was the strongest current peer candidate in that response: current/live/reached/bound, 394 observations, 142 distinct tips, and bound to `https://www.flavorflowstrategy.uk/witness.json`. The peer's exact current tip was not independently retained in this run, so no peer/tip pair was invented and no positive `/x/witness/attest` result was promoted.

The public AILeash source repository declares and implements a witness-attestation route `/x/witness/attest?peer=&tip=` and public witness topology modules. Source inspection establishes the route and intended semantics, not an authentic positive runtime attestation for the exact Appendix A live tip.

The Evidence Custody Seam Appendix A R4 positive-live claim therefore remains `COUNTERPART_REPORTED` unless an exact live tip is independently queried through the acceptor read route and its positive response is retained.

The current public `/x/ots/status` response reported 1,801 proof files, 1,803 attempts, 1,801 stamped and 2 failed. Its latest proof (`stamp_id=1789632190`, tip `ca9eb461fd2af52b92feca6661f4e0cad6501c7438141d5a6c6e573f5f84af6e`) was explicitly `pending` with no Bitcoin block height. The auto-upgrade summary reported older proofs as confirmed, but that is still service-side status rather than independent Bitcoin verification.

Public source inspection of `modules/ots.py` confirms that `/x/ots/list` enumerates proofs and `/x/ots/proof?ts=<stamp_id>` returns the raw `.ots` bytes as base64 plus the recorded tip, proof hash, state, Bitcoin block heights, and standard-client verification steps. This establishes an independent-verification path in principle. A specific confirmed raw proof was not independently obtained through the currently available external fetch surface in this run, so no Bitcoin claim was promoted.

Red Flag AI Pro independently publishes an open witness standard and publicly names sebbi.pro/AILeash as a witness-network peer. That provides external corroboration of a separately operated witness relationship, but does not itself supply the exact current peer tip or prove all historical exchanges/control-domain independence.

Justin Dobson/AILeash/sebbi.pro linkage is strongly supported by public self-description and user-provided profile context, but identity/ownership claims from operator-controlled sources remain source-declared rather than independent identity verification.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`

Latest evidence-map commit: `f9f29dd35073b9f5af89c86e0e88f7ee240460e4`.

## Next action

Preferred path: independently fetch the exact current tip from one currently reached/bound peer (starting with `flavorflowstrategy.uk`), query `https://sebbi.pro/x/witness/attest?peer=<peer>&tip=<tip>`, and retain the response if positive. Separately obtain a specific confirmed proof from `/x/ots/list` + `/x/ots/proof`, decode it, and verify it with the standard OpenTimestamps client against Bitcoin. Promote only the exact claims those artifacts establish.

If the available automated fetch surface still cannot retrieve the peer tip or raw proof bytes, use the public endpoints directly in a browser as the minimum manual acquisition path; no architecture or evidence status changes are permitted merely because the retrieval path is inconvenient.
