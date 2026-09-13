# MIR × StegVerse Separation-of-Powers Evidence Contract v0.3 Convergence Candidate

Authors: Richard Whitney (MIR), Rigel Randolph (StegVerse)

Status: Convergence candidate — not frozen until mutual agreement

Saved: 2026-09-10

This is the v0.3 convergence candidate incorporating MIR's redline and the OTS-anchoring honesty correction.

## Objective

Define the enforceable interface between historical custody, governance, and provenance. This contract defines what each system may emit, consume, retain, and prove. It is not merely an architectural description.

## 1. Constitutional invariant: three powers, no combined authority

The system recognizes three distinct powers:

- **History** — the authoritative record of what an entity did over time.
- **Governance** — the authority to determine what is admissible for a particular decision now.
- **Provenance** — cryptographic evidence that a particular act, observation, or decision occurred as represented.

The separation-of-powers invariant is:

> No participant may combine authoritative historical custody with governance authority over the same subject and decision context. No provenance mechanism may silently confer either historical-custody authority or governance authority.

### MIR

MIR is the custodian of history.

MIR MAY:

- retain historical events;
- derive deterministic evidence summaries from those events;
- produce cryptographic proofs over the retained record;
- publish checkpoints;
- expose claims recorded against an entity;
- produce or expose receipts concerning acts involving MIR.

MIR MUST NOT:

- return `ALLOW`, `DENY`, `STEP_UP`, `ADMISSIBLE`, `INADMISSIBLE`, or semantic equivalents from the evidence interface;
- determine whether evidence satisfies a StegVerse governance predicate;
- alter evidence presentation according to a requested governance outcome.

### StegVerse

StegVerse is the governor of admissibility.

StegVerse MAY:

- request evidence from MIR;
- cryptographically verify that evidence;
- apply StegVerse predicates to verified evidence;
- make and retain governance decisions;
- retain references and proofs necessary to reproduce a decision.

StegVerse MUST NOT:

- ingest MIR’s historical event stream into a StegVerse historical store;
- become an alternate authoritative custodian of MIR history;
- rewrite MIR history;
- represent a cached evidence response as a historical record owned by StegVerse.

### Independent record principle

The historical record is controlled by neither the governed actor nor the governor.

The governor consumes independently held evidence.

The governed actor may generate events and receipts but cannot make those events historically authoritative merely by asserting them.

A system in which the governor also becomes historical custodian has collapsed the separation, regardless of whether the two functions are implemented as separate modules.

## 2. Surface 1 — MIR Evidence Interface

### Principle

MIR returns evidence, never a governance verdict.

The evidence interface MUST be wire-level separate from any endpoint that produces recommendations, policy outcomes, risk assessments, or admissibility conclusions.

The existing:

`POST /v1/policy/evaluate?debug=true`

is outside the StegVerse/MIR evidence contract even where `debug.mirSignals` contains useful evidence.

### SHIPPED — standing evidence surface

The StegVerse/MIR evidence surface is:

`POST /v1/policy/standing`

The shipped standing surface returns a verdict-free standing classification, the raw standing signals used to derive that classification, a claim summary, and a committed checkpoint pin.

The entity reference MUST be supplied in the POST body, not in a URL path.

### entityRef semantics

`entityRef` is an opaque hashed reference. MIR MUST NOT expose the raw external identifier through this interface.

StegVerse MUST treat `entityRef` as an opaque identifier and MUST NOT infer identity semantics from its digest value.

For new identifier-derivation profiles, the derivation scheme SHOULD be versioned and SHOULD use domain separation or a keyed construction where practical to reduce cross-context correlation and offline guessing of low-entropy identifiers. The evidence interface does not require disclosure of the derivation preimage.

### TO-BUILD — v0.3 standing extensions

The same `POST /v1/policy/standing` surface is extended rather than creating a second evidence endpoint.

The request MAY include:

- `atSeq`
- `atTip`
- `includeProof=true|false`
- `claimDetailMode=SUMMARY_ONLY|MINIMUM_NECESSARY`

If neither `atSeq` nor `atTip` is supplied, MIR returns evidence at its current committed head.

If `atSeq` and `atTip` are both supplied, they MUST identify the same committed checkpoint. If they do not, MIR returns the technical evidence state:

`CHECKPOINT_SELECTOR_MISMATCH`

MIR MUST NOT silently prefer either selector and MUST NOT translate the mismatch into a governance verdict.

`claimDetailMode` defaults to `SUMMARY_ONLY`.

### EvidenceResponse v0

```json
{
  "schema": "mir.evidence.v0",
  "entityRef": "opaque-hashed-reference",
  "observedAt": "RFC3339 timestamp",
  "checkpoint": {
    "seq": 0,
    "tip": "sha256:<hex>"
  },
  "standing": {
    "scheme": "mir.standing.v1",
    "tier": "string",
    "signals": {
      "eventCount": 0,
      "effectiveEventCount": 0,
      "firstEventDaysAgo": 0,
      "lastEventDaysAgo": 0,
      "distinctPartners": 0,
      "tierQualifiedPartnerCount": 0
    }
  },
  "claims": {
    "summary": "NONE_RECORDED | FLAGGED | CONTESTED",
    "recordedCount": 0,
    "detailMode": "SUMMARY_ONLY | MINIMUM_NECESSARY"
  },
  "proofStatus": "NOT_REQUESTED | UNAVAILABLE | PROVIDED",
  "proof": null
}
```

The names and numeric representation of raw `mir.standing.v1` inputs MUST match the MIR scheme definition. If the scheme uses additional inputs, those inputs MUST either accompany the tier in `standing.signals` or be normatively enumerated by the named scheme. A tier MUST NOT be presented as independently reproducible unless every input required by that scheme is available to the verifier.

### Proof availability semantics

`NOT_REQUESTED` means `includeProof` was false or absent and no proof conclusion may be inferred.

`UNAVAILABLE` means proof was requested but the required proof material is not available from the current MIR implementation or at the requested checkpoint.

`PROVIDED` means a `ProofBundle` conforming to the negotiated proof schema accompanies the response.

An absent, null, or empty proof object MUST NOT be interpreted as successful verification.

Until the inclusion-proof surface is implemented, `proofStatus` MUST NOT be `PROVIDED` merely because a checkpoint pin is present.

### Standing semantics

`standing.signals` are historical observations.

`standing.tier` is permitted only as a deterministically derived historical classification, not as a policy judgment.

Therefore:

- its derivation scheme MUST be named;
- the raw inputs MUST accompany it or be completely enumerated by the named scheme;
- identical inputs under the same scheme MUST produce the same tier;
- the scheme MUST NOT contain a StegVerse governance outcome;
- StegVerse MUST remain free to ignore the tier and evaluate raw signals directly.

Agreement between a MIR-derived classification and a StegVerse governance result does not transform the MIR classification into governance authority.

The word standing does not imply admissibility.

### Claims semantics

MIR records claims; MIR does not adjudicate them for StegVerse.

`NONE_RECORDED` means only that MIR has no applicable recorded claim at the referenced checkpoint.

It MUST NOT mean:

- trustworthy;
- safe;
- verified;
- exonerated;
- admissible.

`FLAGGED` means one or more relevant claims are recorded.

`CONTESTED` means the historical record contains a dispute or contest concerning an applicable claim.

StegVerse determines the governance consequence, if any.

### Claim-detail disclosure

`SUMMARY_ONLY` is the default and returns only the summary and count required by this contract.

`MINIMUM_NECESSARY` MAY disclose additional claim evidence only when explicitly requested for an identified governance predicate or verification purpose.

Detailed claim disclosure MUST be limited to evidence relevant to that purpose and MUST NOT expose unrelated MIR historical events merely for convenience.

Detailed claim evidence remains MIR-held historical evidence. StegVerse MAY retain the minimum reference and proof material needed to reproduce its decision but MUST NOT convert claim-detail retrieval into an accumulating MIR history replica.

A claim-detail request and response MUST NOT contain a requested governance outcome.

### Explicitly prohibited fields

The evidence response MUST NOT contain:

`allow`, `deny`, `admissible`, `inadmissible`, `stepUp`, `recommendedAction`, `policyDecision`, `governanceDecision`, `riskDisposition`, or semantically equivalent fields intended to tell the governor what decision to make.

Presence of such a field makes the payload out of contract.

## 3. Surface 2 — StegVerse Reference/Custody Boundary

### Principle

StegVerse consumes history by reference, not by custody.

The evidence necessary to justify a governance decision may be retained.

The underlying MIR event history may not.

### StegVerse MIR Evidence Reference v0

```json
{
  "schema": "stegverse.mir-reference.v0",
  "entityRef": "string",
  "checkpoint": {
    "seq": 0,
    "tip": "sha256:<hex>"
  },
  "evidenceClass": "string",
  "proofRef": "string",
  "readAt": "RFC3339 timestamp",
  "evidenceObservedAt": "RFC3339 timestamp",
  "freshnessPolicy": {
    "policyId": "string",
    "maxAgeSeconds": 0
  },
  "verification": {
    "status": "VERIFIED",
    "verifiedAt": "RFC3339 timestamp",
    "verifier": "string"
  }
}
```

This record is a decision dependency reference, not MIR history.

StegVerse MAY additionally retain the minimum proof material required to reproduce verification when external proof retrieval is not guaranteed. That retained proof does not convert StegVerse into historical custodian because it proves a referenced historical state rather than constituting the underlying event stream.

### Prohibited StegVerse custody

StegVerse MUST NOT persist, as part of this interface:

- MIR’s full event stream;
- an accumulating replica of entity history;
- private historical events unrelated to the decision;
- an alternate canonical MIR ledger;
- a mutable reconstruction of MIR history under StegVerse authority.

### Governance decision record

The StegVerse decision is separately retained as StegVerse provenance.

```json
{
  "schema": "stegverse.governance-decision.v0",
  "decisionId": "string",
  "subjectRef": "string",
  "predicateId": "string",
  "predicateVersion": "string",
  "evidenceRefs": ["string"],
  "decision": "ALLOW | DENY | STEP_UP | OTHER_DEFINED_RESULT",
  "decidedAt": "RFC3339 timestamp",
  "decisionReceipt": {}
}
```

The presence of `ALLOW` or `DENY` here is correct because this is a StegVerse governance record, not a MIR historical-evidence response.

## 4. Freshness and checkpoint semantics

Freshness is a StegVerse governance concern, not a MIR decision.

MIR supplies timestamps and committed checkpoints.

StegVerse determines how recent evidence must be for a particular predicate.

### Recommended rule: read-head-then-pin

For a new governance decision:

1. StegVerse requests the current committed MIR head.
2. MIR returns evidence bound to a specific checkpoint `seq + tip`.
3. StegVerse verifies the response.
4. StegVerse evaluates freshness according to its predicate.
5. StegVerse evaluates admissibility.
6. StegVerse records the exact pinned checkpoint used.

For replay, audit, or reconstruction, StegVerse uses the pinned tip rather than silently substituting a newer head.

A newer decision may read a newer head.

### Caching

Caching is permitted only when:

`currentTime - evidenceObservedAt <= predicate.maxEvidenceAge`

and the cached proof still verifies.

Expiration does not mean the historical evidence became false.

It means that evidence is too old to satisfy the current StegVerse governance predicate.

## 5. Surface 3 — Proof Format

Status: TO-BUILD for joint v0.3 conformance. No claim that MIR currently emits an inclusion audit path or signed witness attestation is made by this section.

### Principle

The trust model is not:

> Trust MIR because MIR says this is the history.

It is:

> Read evidence from MIR and verify cryptographically that the referenced committed history has not been rewritten relative to the proof and independently witnessed checkpoint.

### ProofBundle v0

```json
{
  "schema": "mir.proof.v0",
  "checkpoint": {
    "seq": 0,
    "rangeStart": "RFC3339 timestamp",
    "rangeEnd": "RFC3339 timestamp",
    "eventCount": 0,
    "merkleRoot": "sha256:<hex>",
    "prevTip": "sha256:<hex> | null",
    "tip": "sha256:<hex>"
  },
  "leaf": {
    "scheme": "mir.leaf.v1 | mir.leaf.v2 | mir.leaf.v3",
    "hash": "sha256:<hex>",
    "salt": "base64 | null"
  },
  "auditPath": [
    {
      "side": "LEFT | RIGHT",
      "hash": "sha256:<hex>"
    }
  ],
  "witnesses": [
    {
      "witnessId": "string",
      "keyId": "string",
      "keyVersion": "string",
      "attestationRef": "string",
      "observedTip": "sha256:<hex>",
      "observedAt": "RFC3339 timestamp",
      "signatureScheme": "string",
      "signature": "string"
    }
  ]
}
```

### Checkpoint tip construction

Canonical tip construction:

```text
tip = sha256(
  seq
  + ":"
  + rangeStart.ISO
  + ":"
  + rangeEnd.ISO
  + ":"
  + eventCount
  + ":"
  + merkleRoot
  + ":"
  + prevTip
)
```

### Canonical byte serialization

The checkpoint-tip preimage is the UTF-8 encoding of:

`seq + ":" + rangeStart + ":" + rangeEnd + ":" + eventCount + ":" + merkleRoot + ":" + prevTip`

with exactly one ASCII colon (`0x3A`) between fields and no leading or trailing whitespace.

Canonical field rules:

- `seq` and `eventCount`: unsigned base-10 integers with no leading zeroes except the value `0`.
- `rangeStart` and `rangeEnd`: RFC3339 timestamps normalized to UTC with the `Z` designator. Fractional seconds MUST be omitted when zero and otherwise MUST have trailing zeroes removed.
- `merkleRoot` and non-null `prevTip`: lowercase ASCII in the exact form `sha256:<64 lowercase hexadecimal characters>`.
- null `prevTip`: exact lowercase ASCII string `null`.
- No implementation-language object serialization, locale formatting, whitespace insertion, alternate hexadecimal case, or alternate timestamp representation is permitted in the preimage.

The `canonicalEventCore` used by leaf schemes MUST be defined by the applicable leaf-scheme specification as an ordered canonical byte sequence. A leaf scheme is not interoperable until that event-core serialization is fully specified.

### Leaf schemes

#### mir.leaf.v1

Versioned deterministic leaf over the defined event core.

#### mir.leaf.v2

Privacy-preserving salted leaf:

```text
sha256(
  "mir.leaf.v2"
  + ":"
  + salt
  + ":"
  + canonicalEventCore
)
```

Salt is per event.

#### mir.leaf.v3

The forward leaf scheme uses RFC 6962-style domain separation and a per-event salt.

Leaf:

```text
sha256(
  0x00
  + salt
  + canonicalEventCore
)
```

Interior node:

```text
sha256(
  0x01
  + leftHashBytes
  + rightHashBytes
)
```

For `mir.leaf.v1` and `mir.leaf.v2`, interior nodes retain the legacy rule:

`sha256(leftHex + rightHex)`

where `leftHex` and `rightHex` are the canonical lowercase hexadecimal encodings defined by those schemes.

The audit-path fold MUST use the node rule associated with the declared leaf scheme. A verifier MUST NOT apply one universal interior-node rule across v1, v2, and v3.

Unknown leaf scheme: **HARD VERIFICATION FAILURE**. There is no best-effort downgrade.

## 6. Predicate verification procedure

Status: TO-BUILD for the proof-dependent steps until the inclusion-proof endpoint is shipped.

Before any MIR-derived fact may influence a StegVerse governance predicate, the verifier performs:

1. Validate schema.
2. Validate the supported leaf scheme.
3. Recompute the event leaf where the underlying event is available to the verifier.
4. Fold `auditPath` in its declared left/right order using the node rule bound to the declared leaf scheme.
5. Require the result to equal `checkpoint.merkleRoot`.
6. Recompute the checkpoint tip from its canonical fields.
7. Require the recomputed value to equal `checkpoint.tip`.
8. Validate `prevTip` continuity when chain continuity is required.
9. Validate at least the witness requirement defined by the StegVerse predicate.
10. Confirm that witness `observedTip` equals the checkpoint tip.
11. Verify witness signature(s).
12. Apply StegVerse freshness policy.
13. Only then expose the evidence fields to the governance predicate.

Failure of cryptographic verification produces:

`EVIDENCE_UNVERIFIED`

It MUST NOT automatically mean `DENY` unless the applicable StegVerse predicate explicitly defines unverifiable evidence as grounds for denial.

Proof failure is an evidence state; governance determines the consequence.

## 7. Independent witnesses

Status: TO-BUILD until MIR captures and exposes a signed witness-attestation envelope.

A MIR checkpoint becomes independently corroboratable when an external witness attests that it possessed or observed a particular tip at a particular time.

Witnesses MUST NOT gain MIR governance authority.

Witnesses MUST NOT gain StegVerse governance authority.

Their role is limited to statements of the form:

> Witness W observed checkpoint tip T at time X.

### Witness-key lifecycle

Each signed witness attestation MUST identify the witness key with `keyId` and `keyVersion`.

Witness key metadata MUST support reconstruction of whether that key was valid for the witness at `observedAt`, including activation time and, where applicable, rotation, expiration, revocation, or compromise-effective time.

Historical verification MUST evaluate the key state applicable to `observedAt`. A later key rotation does not by itself invalidate an otherwise valid historical attestation.

If a key is later determined to have been compromised during the attested observation interval, the attestation MUST NOT satisfy a witness requirement unless the consuming StegVerse predicate explicitly accepts that evidence state.

A witness network may consist of multiple independent implementations or organizations conforming to the same witness standard.

The contract SHOULD define a minimum witness policy separately from MIR itself so that StegVerse may require:

- one valid independent witness;
- M-of-N witnesses;
- particular witness classes;
- no witness for low-consequence predicates;
- stronger witness requirements for high-consequence predicates.

The witness requirement is therefore governed by StegVerse.

The contents and signature validity of a witness attestation remain independently verifiable evidence.

## 8. Provenance remains distinct from history

A receipt attests one act.

A history proof attests that a referenced act or historical state participates in an accumulated committed record.

These are different claims.

Examples:

- receipt: `Actor A performed act X.`
- inclusion proof: `The committed MIR record represented by checkpoint T contains the leaf corresponding to act X.`
- checkpoint chain: `Checkpoint T follows the previously committed historical state.`
- witness attestation: `Independent witness W possessed/observed T at time Y.`
- StegVerse governance decision: `Given verified evidence E and predicate P, result R was admissible at time Z.`

None substitutes for another.

## 9. Failure semantics

The interface fails closed with respect to evidence validity, not necessarily with respect to the ultimate governance result.

Required evidence states include:

- `VERIFIED`
- `UNVERIFIED`
- `STALE`
- `UNAVAILABLE`
- `UNSUPPORTED_SCHEME`
- `CHECKPOINT_MISMATCH`
- `AUDIT_PATH_INVALID`
- `WITNESS_REQUIREMENT_UNSATISFIED`
- `CHECKPOINT_SELECTOR_MISMATCH`
- `PROOF_NOT_REQUESTED`
- `PROOF_UNAVAILABLE`

MIR may report technical failure states.

MIR may not translate them into governance outcomes.

StegVerse maps evidence states to governance outcomes through its own predicate.

## 10. Contract invariant

The following clause is normative:

> MIR SHALL provide historical evidence without governance verdict. StegVerse SHALL consume MIR history by verifiable reference without assuming historical custody. Provenance SHALL establish bounded claims about acts, commitments, or observations without silently transferring historical or governance authority. Any interface, storage behavior, recommendation, replication mechanism, or fallback that gives MIR governance authority or gives StegVerse authoritative custody of MIR history is outside this contract.

This invariant takes precedence over convenience, implementation topology, caching strategy, recommendation APIs, and internal module boundaries.

Separation must hold on the wire, at rest, and during reconstruction.

## 11. v0.3 convergence decisions

- **Verdict-free endpoint:** YES. Use `POST /v1/policy/standing` as the StegVerse/MIR evidence surface. Do not create a second evidence endpoint and do not filter a governance-capable endpoint downstream.
- **Freshness owner:** StegVerse. MIR reports observation/checkpoint time; StegVerse decides whether it is sufficiently current.
- **Caching:** Allowed, subject to the consuming predicate’s explicit maximum age and successful proof re-verification where proof is required.
- **Pin vs. head:** Read current committed head for each new decision and pin the exact `seq + tip` actually used. Reconstruction always uses the pinned checkpoint.
- **standing.tier:** Retained in v0.3 as a named deterministic historical classification with all required raw inputs available to StegVerse. StegVerse remains free to ignore the tier.
- **Claims summary:** `NONE_RECORDED | FLAGGED | CONTESTED`. `NONE_RECORDED` is not an exoneration or trust conclusion.
- **Proof wire format:** Explicit typed audit-path entries with `LEFT | RIGHT`, named leaf schemes, scheme-bound node rules, canonical checkpoint fields, explicit proof availability state, and independently verifiable witness attestations.
- **Unknown proof scheme:** Hard evidence-verification failure.
- **MIR recommendation endpoint:** `/v1/policy/evaluate` and any recommendation-capable equivalent may continue to exist for other MIR uses, but they are explicitly outside this separation-of-powers evidence contract.
- **Shipped versus to-build:** The standing evidence surface is shipped. The inclusion-proof and signed witness-attestation surfaces remain TO-BUILD until implementation evidence exists.

## 12. Remaining joint implementation and freeze conditions

The architectural contract is converged subject to mutual agreement on this candidate.

The remaining implementation work does not transfer authority between the parties and MUST NOT be represented as shipped before evidence exists:

12.1 Confirm the canonical checkpoint and `canonicalEventCore` serialization rules against MIR implementation fixtures.

12.2 Confirm the `entityRef` derivation profile and its privacy properties for StegVerse integration.

12.3 Ship the v0.3 extensions on `POST /v1/policy/standing`, including historical checkpoint selection and explicit proof availability semantics.

12.4 Finalize and ship minimum-necessary claim-detail disclosure if claim details are required by a StegVerse predicate.

12.5 Ship the MIR inclusion-proof response containing `auditPath`, declared leaf scheme, and checkpoint fields.

12.6 Ship the witness-attestation envelope, including witness key identity/lifecycle metadata, a signed observation of the checkpoint tip, and any applicable OTS reference.

12.7 Establish initial StegVerse freshness classes and witness requirements as StegVerse governance policy, separate from MIR.

12.8 Create a shared `mir.leaf.v3` conformance fixture in which the same tree and checkpoint are independently reproduced by MIR, StegVerse, and a third implementation.

Until 12.5 and 12.6 are shipped, `witnesses[]` MUST remain empty and `proofStatus` MUST accurately report `NOT_REQUESTED` or `UNAVAILABLE` rather than imply proof completion.

Successful completion of the shared v3 conformance fixture demonstrates interoperable proof implementation. It does not alter the constitutional separation of historical custody, governance authority, and provenance defined by this contract.
