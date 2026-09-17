# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / APPENDIX A R4 BEHAVIOR INDEPENDENTLY REPRODUCED / OTS PROOF RETAINED PENDING`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A R4 claims and Justin Dobson's witness-topology contribution. Preserve a strict distinction between independently observed public behavior, user-retained public responses, source-inspected implementation material, counterpart/self-reported claims, and claims not yet established.

## Current truth

The user supplied the public response from `https://www.flavorflowstrategy.uk/witness.json`:

- chain: `flavorflowstrategy.uk`
- tip: `27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`
- updated_at: `2026-08-13T13:11:06Z`

The exact corrected sebbi.pro witness request was then executed:

`https://sebbi.pro/x/witness/attest?peer=flavorflowstrategy.uk&tip=27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`

The retained response returned:

- `witnessed=true`
- `first_observed=2026-08-13T13:11:06.564037+00:00`
- `last_observed=2026-09-17T08:18:40.589471+00:00`
- `times_observed=253`
- `sealed_in_our_chain=c76219e876dacc45aea9884a91dafa68c2e5fa31b4d928474181cbd521ea24f3`
- `block_index=560`

This independently reproduces the core Appendix A R4 public-read behavior for one exact peer/tip. The historical Richard Whitney artifact itself remains separate provenance, but the behavioral existence claim is no longer merely counterpart-reported.

The same response also returned `liveness=self-declared`, `reachability=unrecorded`, `name_status=unbound`, and `submitted_url=null`, and explicitly limits what it proves to the fact that the exact tip was handed to sebbi.pro and sealed into its chain. No identity, current-liveness, control-domain-independence, or Bitcoin claim is promoted from this response.

The user also retrieved a concrete OpenTimestamps proof:

- stamp: `1789455657`
- tip/digest: `510837825c194c303eedfaeb0528d0fc6dfe4e6bbf1e5534ef8bb34edccd0224`
- proof bytes: `721`
- proof SHA-256: `8511ef312479e9fd97d05ecd69d35a8d2ab727aa6e49f20c441657d714f7dd53`
- state: `pending`
- Bitcoin block heights: none
- pending calendars: Alice and Bob OpenTimestamps calendars

The supplied `ots_base64` was decoded locally. It produced exactly 721 bytes; SHA-256 of those bytes exactly matched the returned proof hash, and the artifact begins with the OpenTimestamps proof header. This independently binds the retained bytes to the public response, but the proof is still pending and therefore is not Bitcoin-confirmed evidence.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`

Latest evidence-map commit: `10bae874629a944667f9343d99efdddaa57e3c07`.

## Current promotion state

Promoted narrowly:

- exact unauthenticated witness-attest behavior for one peer/tip;
- positive observed state;
- first/last observation times;
- observation count;
- sealed chain hash and block index;
- internal consistency of the retained raw pending OTS artifact with its reported byte count/hash.

Not promoted:

- peer/operator identity;
- current liveness for the historical witness observation;
- witness control/failure-domain independence;
- complete historical witness topology;
- Bitcoin confirmation for stamp `1789455657`;
- Richard Whitney's exact historical response artifact;
- the 784-record / 30-commitment clean-room run.

## StegBrowser / SV002 invocation reconciliation — 2026-09-17

Field-by-field comparison against the validated StegVerse-002 browser lane identified one concrete pre-A1 divergence in the `.github` observation/composition path. The validated/current Node browser surface reads the registered Node directly from the existing `stegos-node-v1` IndexedDB registration projection and binds the immutable StegBrowser invocation to `indexeddb://stegos-node-v1/meta/registration`. By contrast, `scripts/consume_stegbrowser_runtime_connection_ingress_request.py` still attempts to resolve Receipt #1 from the host environment variable `STEGVERSE_NODE_GENESIS_RECEIPT` and a filesystem path before invoking the manifest-bound runner.

That host-side file-path requirement is not the historically successful SV002 Node binding and must not be treated as evidence that the registered Node itself is unavailable. The later canonical current-iPhone correction explicitly assigns evidence observation to the existing Node/InTr runtime and canonical receipt paths and removes any user-operated page/device prerequisite. Therefore the missing host filesystem projection is an observation/composition defect, not proof that A1 cannot occur.

No second request or nonce mutation was performed while investigating this defect.

A separate immutable-manifest constraint was also confirmed: the existing nonce `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z` is bound to `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001:owned-mirror-route`, whose outbound receiver is `STEGVERSE_OWNED_MIRROR_REFLECTOR` and expected action is `REFLECT_DECLARED_RECORDS_PACKET`. It is not an arbitrary external HTTP GET/navigation manifest. Using that immutable request to fetch a sebbi.pro proof URL would mutate/substitute the declared route/payload semantics and therefore is not permitted under the same-nonce/no-second-request constraint.

Accordingly:

- preserve the existing immutable StegBrowser mirror invocation unchanged;
- do not promote host `STEGVERSE_NODE_GENESIS_RECEIPT` absence into Node absence;
- repair/reconcile only the observer/composition seam so it re-observes authority-owned existing Node/InTr receipts rather than requiring a host-side Receipt #1 file as a gating prerequisite;
- do not repurpose the immutable mirror manifest for sebbi.pro;
- a sebbi.pro StegBrowser GET must use an already-registered compatible GET/navigation invocation if one exists, otherwise it requires a separately authorized manifest-bound invocation rather than mutation of the current nonce.

No existing registered StegBrowser arbitrary-GET/navigation reusable task was found in the current `.github` registry search, so no external sebbi.pro browser execution is claimed from this investigation.

## Next action

Retrieve an older real OTS proof until one returns `state=confirmed` with at least one Bitcoin block height. Retain the complete proof JSON and raw `ots_base64`; independently verify the proof bytes against the returned digest using a standard OpenTimestamps client and an independently obtained Bitcoin chain/header path before promoting the Bitcoin external-time claim.

In parallel, reconcile the StegBrowser A1 observer/composition seam with the already-working SV002/current-Node IndexedDB binding so absence of a host filesystem Receipt #1 projection does not masquerade as registered-Node absence. Do not mutate the immutable owned-mirror nonce to carry sebbi.pro traffic.

Separately, if v0.4 topology scoring is pursued, collect evidence of actual cross-witness edges and independently attributable operator/control/failure domains. Do not derive a resilience number from roster membership or peer count alone.
