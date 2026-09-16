# Separation-of-Powers Reference Architecture for Governable / Insurable Agents

Status: DRAFT v0.1 — not frozen
Goal Task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

## 1. Purpose

Define a vendor- and model-neutral architecture in which governance, transition admission, execution, credential/provider authority, evidence custody/reconstruction, and observability remain separately attributable. The architecture is defined by authority boundaries and proof obligations rather than by any specific AI model, vendor, cloud, ledger, or runtime.

## 2. Actor / authority diagram

```text
Human / Organization Intent
          |
          v
+-----------------------------+
| A. Governance / Policy      |
| decides applicable rules    |
+-----------------------------+
          |
          | governance decision receipt
          v
+-----------------------------+
| B. Admission / State        |
| Transition Authority        |
| admits/denies exact change  |
+-----------------------------+
          |
          | admission receipt + exact binding
          v
+-----------------------------+
| C. Execution                |
| performs admitted operation |
+-----------------------------+
          |
          | execution result / transition record
          v
+-----------------------------+
| D. Credential / Provider    |
| Authority                   |
| authorizes provider/session |
+-----------------------------+
          |
          | credential/session/provider receipt
          v
+-----------------------------+
| E. Evidence Custody /       |
| Reconstruction              |
| preserves what happened     |
+-----------------------------+
          |
          | custody + reconstruction receipts
          v
+-----------------------------+
| F. Observability            |
| timing, health, correlation |
+-----------------------------+
```

The arrows describe expected evidence flow, not a grant of authority from one box to another. Implementations may combine software processes physically, but they must preserve independently attributable authority semantics and receipts.

## 3. Authority contracts

### A. Governance / policy authority

May determine which policy applies and may emit an attributable policy decision. It may not execute the operation, mint credential authority, infer that execution happened, or rewrite historical evidence.

Minimum receipt fields:

- policy identity/version/hash;
- subject/request identity;
- decision (`ALLOW`, `DENY`, or bounded equivalent);
- decision time;
- decision authority identity;
- exact downstream binding target where applicable;
- receipt integrity/signature material.

### B. Admission / state-transition authority

May admit or deny one exact proposed state transition under a contemporaneous governance decision. It may not substitute a prior governance receipt for a new transition or treat an interface success as execution proof.

Minimum receipt fields:

- exact proposed transition identity/hash;
- previous state/root binding;
- governance decision reference;
- admission result;
- admission time;
- transition authority identity;
- lease/nonce/fence when applicable;
- integrity/signature material.

### C. Execution

May perform only the operation admitted by the transition authority. Execution may return a result, but success claims remain provisional until the actual transition record is independently retained/reconstructable where the contract requires that proof.

Minimum receipt fields:

- admitted transition reference;
- executable identity/version/hash;
- runtime identity;
- start/end or bounded event time;
- result status;
- output/result hash where applicable;
- exact state-change reference;
- integrity/signature material.

### D. Credential / provider authority

May issue or authorize provider/session/credential use for a bounded purpose. It does not thereby authorize the governed state transition and cannot self-attest that downstream execution occurred.

Minimum receipt fields:

- provider/credential class;
- bounded purpose/scope;
- requesting transition/execution reference;
- issued/authorized time and expiry where applicable;
- credential/provider authority identity;
- secret-free credential/session reference;
- integrity/signature material.

### E. Evidence custody / reconstruction

Preserves authentic transition records and supports deterministic reconstruction of what happened. It must remain semantically independent of the authorities whose actions it records. It never gains governance or transition authority merely by holding evidence.

Minimum receipt fields (StegVerse proposal pending MIR first-pass refinement):

- evidence object identity/hash;
- subject transition identity;
- source authority/runtime identity;
- acquisition/observation time;
- custody entry/reference;
- predecessor/checkpoint linkage where chained;
- witness/anchor references only when actually present;
- reconstruction method/version;
- integrity/signature material;
- explicit proof status that remains honest when external anchoring/witness evidence is unavailable.

### F. Observability

May report health, liveness, timing, freshness, metrics, correlation, and externally visible state. Observability is non-authorizing and cannot prove an unobserved state transition simply because a service is alive or a seam is reachable.

Minimum receipt fields:

- observed subject identity;
- observer identity;
- observation type;
- observation time/window;
- observed value/status;
- correlation reference;
- integrity/signature material where required.

## 4. Prohibited authority collapses

The following collapses are prohibited unless an implementation proves equivalent independent controls and attribution at the contract level; physical co-location alone is not disqualifying, but semantic self-authorization is:

1. Governance/policy -> execution: a policy decision may not be treated as proof or authority that execution occurred.
2. Governance/policy -> evidence custody: the party defining a decision may not rewrite or manufacture the historical record of its own decision or downstream consequences.
3. Admission/state transition -> execution proof: admission proves permission for one exact transition, not execution.
4. Credential/provider -> transition authority: credential availability does not admit a governed state change.
5. Credential/provider -> execution proof: a successful session/token/provider call does not prove the intended governed state transition.
6. Execution -> evidence custody: an executor's self-report alone is insufficient when the contract requires independent custody/reconstruction.
7. Evidence custody -> governance or transition authority: holding or reconstructing the record grants no authority to govern or admit new work.
8. Observability -> any authority: liveness, timing, health, metrics, or reachability grant no governance, admission, credential, execution, custody, or publication authority.
9. Seam conformance -> downstream runtime proof: passing an interface/conformance fixture proves only the tested seam and fixture behavior.
10. Historical receipt -> present authority: a prior valid receipt proves the prior event only; it does not authorize a later transition.

## 5. Core proof invariant

`SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF`

A seam is conformant when its independently reproducible contract and receipts satisfy the agreed fixture. A runtime chain is proven only when the authentic records of the relevant transitions are in custody and can be reconstructed with the required contemporaneous evidence.

No upstream actor may infer missing downstream events from its own success.

## 6. Evidence status discipline

Proof and witness fields must distinguish at least:

- `VERIFIED`: concrete artifact has been validated against the contract;
- `COUNTERPART_REPORTED`: asserted by another participant but not independently verified;
- `NOT_REQUESTED`: proof/anchor was not requested;
- `UNAVAILABLE`: expected proof surface is not currently available;
- `PENDING`: work to obtain/construct the proof surface is explicitly outstanding.

An empty witness set is preferable to fabricated or inferred witness evidence.

## 7. Current MIR / StegVerse application

The frozen v0.3 contract remains unchanged. This draft is the next-layer reference architecture requested after the clean round-trip seam validation.

Richard/MIR has reported that MIR's tamper-evident hash-chained checkpoints are now anchored to Bitcoin, with an inclusion-proof endpoint next. That statement is recorded here only as `COUNTERPART_REPORTED` until a concrete independently checkable anchor artifact is supplied. Earlier collaboration established that OpenTimestamps had not yet been implemented, so the newer claim must be evidenced rather than inferred from the old `otsStatus` stub.

## 8. Next convergence package

StegVerse should send MIR:

- this actor/authority diagram;
- the governance and governed-transition seam contracts;
- the prohibited-collapse list;
- the minimum receipt fields per seam.

MIR should return:

- its evidence-custody/reconstruction seam first pass;
- concrete minimum evidence receipts;
- one actual Bitcoin-anchor/inclusion artifact or precise checkable reference if the new anchor claim is to enter conformance evidence.

The combined artifact should then be reviewed for contradictions with frozen v0.3 and the existing `mir.leaf.v3` fixture before any next freeze.
