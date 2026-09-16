# Separation-of-Powers Reference Architecture for Governable / Insurable Agents

Status: DRAFT v0.2 — not frozen
Goal Task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

## 1. Purpose

Define a vendor- and model-neutral architecture in which governance, transition admission, execution, credential/provider authority, evidence custody/reconstruction, and observability remain separately attributable. The architecture is defined by authority boundaries and proof obligations rather than by any specific AI model, vendor, cloud, ledger, or runtime.

The frozen v0.3 MIR/StegVerse contract is not modified by this draft. This document is the post-freeze reference-architecture layer.

## 2. Actor / authority graph

```text
                         Human / Organization Intent
                                    |
                                    v
                         +-------------------------+
                         | A. Governance / Policy  |
                         +-------------------------+
                                    |
                       governance decision receipt
                                    v
                         +-------------------------+
                         | B. Admission / State    |
                         | Transition Authority    |
                         +-------------------------+
                                    |
                    exact admission/denial receipt
                                    v
                         +-------------------------+
                         | C. Execution            |
                         +-------------------------+
                           ^                 |
                           |                 | execution result /
 bounded provider/session  |                 | transition record
 authority                 |                 v
+--------------------------+----+      +-------------------------+
| D. Credential / Provider     |      | E. Evidence Custody /  |
| Authority                    |----->| Reconstruction          |
+-------------------------------+      +-------------------------+
        |                                      ^
        | credential/session receipts          |
        +--------------------------------------+
                                               |
                                      custody/reconstruction
                                               |
                                               v
                                      +-------------------------+
                                      | F. Observability        |
                                      +-------------------------+
```

This graph is not a temporal workflow and its arrows do not transfer authority. It shows the principal evidence and bounded-authority relationships. An implementation may physically co-locate components, but it must preserve separately attributable authority semantics, proof ceilings, and receipts.

Evidence custody may ingest authentic records from every corner. That does not make custody an authority over those corners. Observability may inspect/correlate the resulting state but remains non-authorizing.

## 3. Common receipt envelope

Every seam-specific receipt should bind, at minimum, the following common envelope before seam-specific fields are added:

- `receipt_schema` and version;
- `receipt_id`;
- `authority_class` or `observer_class`;
- `subject_id` / request or transition correlation identity;
- `issued_at` or observation time;
- `issuer_id` / source identity;
- exact parent or predecessor reference when applicable;
- payload hash or canonical content hash;
- integrity/signature material appropriate to the implementation;
- explicit `proof_scope` describing exactly what the receipt proves;
- explicit `proof_ceiling` describing what the receipt does **not** prove.

A receipt without a bounded proof scope must not be interpreted as granting broader authority or proving downstream effects.

## 4. Authority contracts and proof ceilings

### A. Governance / policy authority

May determine which policy applies and emit an attributable policy decision.

Minimum seam fields:

- policy identity/version/hash;
- subject/request identity;
- decision (`ALLOW`, `DENY`, or bounded equivalent);
- decision time;
- decision authority identity;
- exact downstream binding target where applicable.

Proof scope: which policy was applied and what decision was made for the bound subject.

Proof ceiling: does not prove admission, execution, credential use, provider success, custody, publication, or any downstream state transition.

### B. Admission / state-transition authority

May admit or deny one exact proposed state transition under a contemporaneous governance decision.

Minimum seam fields:

- exact proposed transition identity/hash;
- previous state/root binding;
- governance decision reference;
- admission result;
- admission time;
- transition authority identity;
- lease/nonce/fence when applicable.

Proof scope: whether one exact transition was admitted or denied against one exact predecessor state and governance reference.

Proof ceiling: admission is permission, not proof that execution or state mutation occurred.

### C. Execution

May perform only the operation admitted by the transition authority.

Minimum seam fields:

- admitted transition reference;
- executable identity/version/hash;
- runtime identity;
- start/end or bounded event time;
- result status;
- output/result hash where applicable;
- exact state-change reference.

Proof scope: what executable ran, under which admitted transition, and what result it reported.

Proof ceiling: an executor self-report alone is not historical custody/reconstruction proof where independent custody is required.

### D. Credential / provider authority

May issue or authorize provider/session/credential use for one bounded purpose.

Minimum seam fields:

- provider/credential class;
- bounded purpose/scope;
- requesting transition/execution reference;
- issued/authorized time and expiry where applicable;
- credential/provider authority identity;
- secret-free credential/session reference.

Proof scope: that a specific bounded provider/credential use was authorized or materialized.

Proof ceiling: credential availability or provider-session success does not itself admit the governed transition, prove the intended execution result, or prove downstream state mutation.

### E. Evidence custody / reconstruction

Preserves authentic transition records and supports deterministic reconstruction of what happened. It must remain semantically independent of the authorities whose actions it records.

Minimum seam fields (StegVerse proposal pending MIR first-pass refinement):

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

Proof scope: that specific evidence entered custody and can be reconstructed under the declared method and evidence chain.

Proof ceiling: custody does not retroactively authorize the recorded event and grants no governance, transition, execution, credential, or publication authority.

### F. Observability

May report health, liveness, timing, freshness, metrics, correlation, and externally visible state.

Minimum seam fields:

- observed subject identity;
- observer identity;
- observation type;
- observation time/window;
- observed value/status;
- correlation reference;
- integrity/signature material where required.

Proof scope: what a named observer actually observed over the declared interval.

Proof ceiling: liveness, reachability, metrics, timing, or interface success do not prove an unobserved transition and grant no operational authority.

## 5. Prohibited authority collapses

Physical co-location is not automatically a failure. Semantic self-authorization or self-proving across authority boundaries is.

1. **Governance -> execution authority/proof**: a policy decision may not be treated as execution authority beyond the exact admission contract and never as proof that execution occurred.
2. **Governance -> evidence custody control**: a party defining a decision may not rewrite or manufacture the historical record of its own decision or downstream consequences.
3. **Admission -> execution proof**: admission proves permission for one exact transition, not execution.
4. **Credential/provider -> transition authority**: credential availability does not admit a governed state change.
5. **Credential/provider -> execution proof**: a successful session/token/provider call does not prove the intended governed state transition.
6. **Execution -> independent custody proof**: an executor's self-report cannot substitute for independent custody/reconstruction where the contract requires it.
7. **Evidence custody -> governance/admission authority**: holding or reconstructing the record grants no authority to govern or admit new work.
8. **Observability -> any operational authority**: liveness, timing, health, metrics, reachability, or correlation grant no governance, admission, credential, execution, custody, publication, or completion authority.
9. **Seam conformance -> downstream runtime proof**: passing an interface/conformance fixture proves only the tested seam and fixture behavior.
10. **Historical receipt -> present authority**: a prior valid receipt proves the prior event only; it does not authorize a later transition.
11. **Evidence status -> authority promotion**: changing evidence from `PENDING` or `COUNTERPART_REPORTED` to `VERIFIED` cannot itself promote any actor's authority.
12. **Reconstruction -> causation inference beyond retained records**: deterministic reconstruction may only assert events supported by retained authentic records; gaps remain gaps.

## 6. Core proof invariant

`SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF`

A seam is conformant when its independently reproducible contract and receipts satisfy the agreed fixture. A runtime chain is proven only when the authentic records of the relevant transitions are in custody and can be reconstructed with the required contemporaneous evidence.

No upstream actor may infer missing downstream events from its own success. No downstream custodian may infer missing upstream authorization merely because an event record exists.

## 7. Conformance matrix

| Corner | May assert | Must not assert from its own receipt alone | Minimum negative test |
|---|---|---|---|
| Governance / policy | applicable policy + bounded decision | execution, credential use, state mutation | ALLOW receipt presented as execution proof must fail |
| Admission / transition | exact transition admitted/denied | execution occurred | admitted transition with no execution record must remain unexecuted/unproven |
| Execution | admitted executable ran + bounded result | independent custody/reconstruction | self-report with absent custody record must not become reconstructed history |
| Credential / provider | bounded credential/session authorization/use | governance admission or state mutation | valid provider session with no admission must not authorize transition |
| Evidence custody / reconstruction | exact retained evidence + reconstruction result | new governance/admission authority | valid custody receipt presented as authorization must fail |
| Observability | actual observation over declared interval | unobserved transition or any authority grant | healthy/reachable service with no transition record must not become execution proof |

A conforming implementation must fail closed on every minimum negative test above.

## 8. Runtime-chain proof composition

A stronger runtime-chain claim must be composed from authentic, mutually consistent records rather than inferred from one authority's success. At minimum, where each corner applies, reconstruction should be able to correlate:

1. governance decision receipt;
2. exact transition admission receipt;
3. bounded credential/provider receipt when external provider authority is required;
4. execution result / state-transition record;
5. independent custody entry plus chain/checkpoint material;
6. reconstruction output identifying the exact retained evidence used;
7. contemporaneous witness/anchor material only if actually present;
8. observability records only for the facts they directly observed.

Missing elements do not necessarily mean the underlying event did not occur. They mean the stronger proof claim is not established by the available evidence.

## 9. Evidence status discipline

Proof and witness fields must distinguish at least:

- `VERIFIED`: concrete artifact has been validated against the contract;
- `COUNTERPART_REPORTED`: asserted by another participant but not independently verified;
- `NOT_REQUESTED`: proof/anchor was not requested;
- `UNAVAILABLE`: expected proof surface is not currently available;
- `PENDING`: work to obtain/construct the proof surface is explicitly outstanding.

An empty witness set is preferable to fabricated or inferred witness evidence. A status transition to `VERIFIED` requires a concrete artifact and validation record; chat assertion alone is insufficient.

## 10. Current MIR / StegVerse application

The frozen v0.3 contract remains unchanged. This draft is the next-layer reference architecture requested after the clean round-trip seam validation.

The existing child `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` demonstrates the intended seam discipline: StegVerse and a neutral reproducer independently match the frozen fixture, but MIR's independent reproduction remains required. That seam result cannot be promoted into proof of downstream runtime activity.

Richard/MIR has reported that MIR's tamper-evident hash-chained checkpoints are now anchored to Bitcoin, with an inclusion-proof endpoint next. That statement remains `COUNTERPART_REPORTED` until a concrete independently checkable anchor artifact is supplied. Earlier collaboration established that OpenTimestamps had not yet been implemented, so the newer Bitcoin-anchor statement must be evidenced rather than inferred from the old `otsStatus` stub.

## 11. Insurability / governability interpretation

This architecture does not assert that any implementation is insurable. It defines evidence and authority properties that an insurer, auditor, buyer, regulator, or counterparty could evaluate without relying on a model vendor's self-description.

A conforming implementation should make it possible to answer, with bounded receipts rather than inference:

- who decided the rule;
- who admitted the exact transition;
- what executable performed the operation;
- who authorized any provider/credential use;
- what authentic record was retained;
- how that record can be reconstructed;
- what an independent observer actually saw;
- which facts remain unverified or unavailable.

## 12. Next convergence package

StegVerse sends MIR:

- this actor/authority graph;
- the common receipt envelope and proof-ceiling rule;
- governance and governed-transition seam contracts;
- the prohibited-collapse list;
- minimum receipt fields per seam;
- the six-corner conformance matrix and negative tests.

MIR returns:

- its evidence-custody/reconstruction seam first pass;
- concrete minimum evidence receipts;
- proposed changes to the prohibited-collapse list;
- one actual Bitcoin-anchor/inclusion artifact or precise checkable reference if the new anchor claim is to enter conformance evidence.

The combined artifact is then reviewed for contradictions with frozen v0.3 and the existing `mir.leaf.v3` fixture before any next freeze. No architecture freeze or conformance completion is implied by this draft.