# MIR / AgentEnvelope derived-authority reconciliation mirror handoff

Updated: 2026-09-18
Goal Task ID: `MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / PUBLIC SPEC + SDK SOURCE INSPECTED / DETERMINISTIC REDERIVATION ALREADY REPRESENTABLE / NO_SOURCE_MUTATION_REQUIRED / RECONCILIATION COMPLETE`

## Goal

Independently inspect Matthew McPhillips's public AgentEnvelope specification and implementation and map its derived-authority, custody, legitimacy, verification, and lifecycle semantics against current StegVerse RTG/GTG/TT/AE, Interlock/InTr, identity, and evidence-reconstruction primitives without importing AgentEnvelope authority or creating duplicate StegVerse machinery.

## Public source evidence inspected

Current public implementation source inspected at:

- `BlackBoxEngineering/agent-envelope-sdk@39a332c7c649747a68d1d86866a55511e10a47e9`;
- `spec/agent-envelope-v1.md`;
- `src/avatar.js`;
- `README.md`;
- `spec/examples/public-action-record.json`;
- IETF Internet-Draft `draft-mcphillips-agentenvelope-derived-authority-01`, published 2026-08-31.

These are external public sources. Their claims are not StegVerse runtime proof, certification, or authority.

## Confirmed AgentEnvelope construction semantics

The public v1 authority tree is:

```text
identityRoot -> domainSeed -> actionEnvelope -> actionSeed -> agentAddress
```

The implementation derives the domain seed from the secret identity root plus canonical `DomainInfo`, then derives the action seed from that domain seed plus the complete canonical action envelope. The agent address is the public address of the derived action seed.

The action envelope binds at least:

- agent identifier;
- domain identifier/hash;
- action index;
- operation;
- resources;
- time window;
- decay policy;
- usage limit.

Changing those canonical derivation inputs changes the derived action seed/address. A worker receives only the scoped action capability, not the root or sibling capabilities.

This independently substantiates Richard Whitney's description that, in AgentEnvelope, construction carries the authority relation rather than requiring a later verifier to accept a child-authored lineage assertion.

## What offline verification actually proves

AgentEnvelope offline verification is record- and signature-based. A verifier checks the public action record, canonical action-envelope hash, domain projection, time decay, signature form, and recovered signer address.

This establishes that the payload was signed by the private material corresponding to the public action address bound to that public action record.

The current SDK explicitly says that offline verification does not establish nonce freshness, delegate revocation, live legitimacy, or whether a max-use slot has already been consumed. Those require governed/stateful surfaces.

Therefore:

```text
DERIVED_AUTHORITY_PROVEN != CURRENT_GOVERNANCE_ADMISSIBILITY_PROVEN
DERIVED_AUTHORITY_PROVEN != HISTORICAL_SEQUENCE_PROVEN
```

## Legitimacy/governance boundary

The -01 draft adds `LegitimacyState`, evidence statements, deterministic legitimacy evaluation, legitimacy events, governance reports, and an explicit Governance Evaluator role.

The draft deliberately separates cryptographic authority from present-tense legitimacy:

- derived authority answers whether the action signer belongs to the defined authority path;
- legitimacy answers whether that otherwise-valid authority is currently admissible under policy, evidence, time, and operating context;
- a valid signature may coexist with denied legitimacy;
- the executor should not be the sole actor renewing/suspending/restoring its own legitimacy.

That separation is structurally compatible with StegVerse's existing prohibition on collapsing identity/capability proof into governance or transition authority. It does not establish technical identity between the systems.

## Temporal / lifecycle ordering result

The inspected v1 SDK contains timestamps and version/hash fields in several objects:

- domain/public-record `createdAt`;
- delegate `issuedAt`;
- mint request `requestedAt`;
- legitimacy state `stateVersion` / `stateHash`;
- legitimacy event `occurredAt` / `effectiveAt`.

However, the core public action record declares `createdAt` metadata and explicitly excludes it from derivation. Offline verification checks the record/action/signature and time-window validity, not a predecessor-linked creation/registration chain.

The -01 draft recommends audit/event continuity as part of full governance verification, but the inspected open SDK/spec does not define a cryptographic predecessor chain establishing that a public record, mint/registration event, or derived actor existed before an arbitrary external action solely from the derivation relation.

Bounded finding:

```text
DERIVATION_PROVES_AUTHORITY RELATION
DERIVATION_ALONE_DOES_NOT_PROVE EVENT ORDER
```

This matches the narrow ordering limitation Richard reported. It must not be broadened into a claim that AgentEnvelope cannot implement stronger ordering in hosted or future profiles.

## Re-derived versus retrieved evidence

AgentEnvelope exposes a real evidence shape that the MIR discussion should distinguish:

1. retained evidence: a record, event, receipt, or state object was emitted/stored and later retrieved;
2. deterministic re-derivation: a verifier recomputes a derived identity/hash/address from canonical inputs and checks equality/signature consistency.

The second can prove a deterministic mathematical relationship without requiring a previously stored assertion of that relationship. It does not eliminate the need for retained event evidence when the proposition being proved is temporal, lifecycle, usage, revocation, execution, or governed state transition.

## StegVerse mapping

### RTG

RTG already distinguishes causal/relational realization from snapshot membership and states that snapshot membership alone does not establish causal continuity. AgentEnvelope derivation can supply a strong relation/identity input, but it does not by itself establish RTG causal ordering or transition realization.

Disposition: compatible evidence input; no RTG primitive replacement.

### GTG

AgentEnvelope legitimacy separates present-tense admissibility from cryptographic derivation and supports policy/evidence evaluation by a distinct evaluator. This is conceptually adjacent to GTG authority/standing/governance disposition.

Disposition: structural overlap only. AgentEnvelope legitimacy is not imported as GTG authority, and GTG remains canonical StegVerse governance formalism.

### TT

TT already requires proposal/commit state distinction, authority/evidence references, commit-time validity, consequence, observer posture, and receipts. TT also preserves unresolved temporal order explicitly.

AgentEnvelope's derived public action record can be referenced as identity/capability evidence, while creation/mint/legitimacy events can be referenced as event evidence. TT remains the place where StegVerse represents ordered governed transition state.

Disposition: no duplicate transition table or lifecycle ledger required.

### AE

AE/StegCore governs admissibility/coherent continuation and distinguishes valid resolution from requested-effect realization. AgentEnvelope's derivation does not supersede AE. Its legitimacy concept is external corroborating architecture for separating valid cryptographic authority from current admissibility.

Disposition: no AE source mutation from conceptual resemblance alone.

### Interlock/InTr

Interlock/InTr remains StegVerse current transition-admission/state-transition authority. A derived AgentEnvelope capability, if ever consumed by StegVerse, would be evidence/input presented to admission; it would not itself authorize a StegVerse state transition.

Disposition:

```text
AGENTENVELOPE_CAPABILITY != INTR_ALLOW
```

### Identity / credential boundary

AgentEnvelope binds a deterministic action identity to a derived signing capability. StegVerse currently keeps credential authority at TV/TVC and user verification at KV/SKAP Vault where applicable.

Disposition: AgentEnvelope demonstrates a useful derived action-identity technique, but no StegVerse credential/verification authority transfer is justified.

### Evidence custody / Master Records

Deterministic re-derivation can be represented as a verification method for a proposition. Master Records remains observed-reality custody/reconstruction and does not become an authority issuer or governance evaluator.

The minimum generic distinction worth retaining is:

```text
evidence_method = RETRIEVED_ARTIFACT | DETERMINISTIC_REDERIVATION
```

but this is a semantic observation only. Under the Canonical Invariant Ingress Lock, no new StegVerse schema or source mutation is admissible until it is proven that existing verification/reconstruction semantics cannot already represent deterministic recomputation.

## Deterministic re-derivation schema reconciliation — 2026-09-18

Current Master Records source was inspected at `master-records/core-lite@be0d08d73c96f50308991793327522dc01304657`, including:

- `MASTER_RECORDS_MIRROR_HANDOFF.md`;
- `README.md`;
- `schemas/typed_custody_evidence.schema.json`;
- `docs/CUSTODY_RECORD_HASH_CONVENTION.md`;
- `tools/verify_record_hash.py`;
- `docs/reconstruction/INFERENCE_WINDOW_RESOLUTION.md`;
- `tools/validate_reconstruction_profile.py`.

The existing model already represents deterministic recomputation without creating a distinct authority class:

1. `canonical_object_digest` represents a digest of a canonical object;
2. `record_self_hash` represents a deterministically recomputable record digest under a declared canonicalization convention;
3. `verify_record_hash.py` re-computes the canonical digest from current record inputs, returns both `declared` and `computed`, and fails closed on mismatch;
4. reconstruction profiles explicitly bind evidence sources, immutable references, provenance, predecessor/successor linkage, algorithm/configuration versions, achieved reconstruction resolution, and an authority posture bounded by reconstructable evidence;
5. Master Records already separates evidence identity/reconstruction from truth, execution, governance, publication, and credential authority.

Therefore AgentEnvelope-style deterministic re-derivation can be represented by retaining the canonical inputs plus their immutable references, the verification algorithm/version, the recomputed proposition/digest/address result, and the resulting verifier receipt as ordinary custody/reconstruction evidence. A new `verification_method` enum is not required for correctness.

The semantic distinction remains useful in explanatory material:

```text
RETRIEVED_ARTIFACT = retained bytes/state later retrieved
DETERMINISTIC_REDERIVATION = verifier recomputes a proposition from canonical inputs
```

but this is a classification of how evidence is established, not a new evidence authority, custody class, or transition role.

Disposition:

```text
NO_SOURCE_MUTATION_REQUIRED
```

No Master Records schema, TT/RTG/GTG/AE formalism, Interlock/InTr contract, TV/TVC credential surface, KV/SKAP user-verification surface, or new evidence engine is needed for this AgentEnvelope reconciliation.

## Current disposition

The investigation confirms meaningful architectural convergence around construction-time authority/lineage and explicit separation of cryptographic authority from current legitimacy.

It does not establish that AgentEnvelope and StegVerse are the same architecture, that either derives from the other, or that StegVerse lacks a needed authority role.

No new authority owner, identity class, governance engine, transition engine, or custody engine is justified.

## Next action

No schema implementation remains for this reconciliation. Preserve AgentEnvelope as external corroborating architecture and reuse existing canonical-object/self-hash verification plus Master Records reconstruction semantics whenever deterministic re-derivation evidence is needed.

Any future AgentEnvelope integration must enter StegVerse as bounded evidence/input to existing governance and transition authority, not as a new authority owner.
