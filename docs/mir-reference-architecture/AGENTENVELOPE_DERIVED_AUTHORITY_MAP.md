# AgentEnvelope / StegVerse derived-authority evidence map

Updated: 2026-09-18
Goal Task: `MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

## Evidence boundary

This map records independent inspection of public AgentEnvelope sources. It does not certify AgentEnvelope, import its authority into StegVerse, or claim shared authorship, derivation, or technical equivalence.

Public source commit inspected: `BlackBoxEngineering/agent-envelope-sdk@39a332c7c649747a68d1d86866a55511e10a47e9`.
Public protocol draft inspected: `draft-mcphillips-agentenvelope-derived-authority-01` (2026-08-31).

## AgentEnvelope mechanics observed

| Surface | Public source behavior | Bounded conclusion |
| --- | --- | --- |
| Authority derivation | `identityRoot -> domainSeed -> actionEnvelope -> actionSeed -> agentAddress` | Action identity is deterministically derived from root/domain plus complete canonical action scope. |
| Scope | Action envelope binds agent ID, domain, action index, operation, resources, time window, decay, and use limit | Changing derivation input changes capability/address. |
| Public record | Stores domain projection, action envelope/hash, address, status and metadata; no action seed | Verifier-safe record is distinct from signing material. |
| Offline verification | Checks canonical record/envelope/hash, domain, time decay and recovered signature address | Proves record/signature consistency; does not prove all current governance state. |
| Usage/replay | Max-use consumption requires external/verifier-controlled or hosted state | Derivation alone is not replay/use-state proof. |
| Legitimacy | Additive versioned governance state evaluated from policy, evidence and time | Cryptographic authority and current admissibility are separate. |
| Legitimacy events | Signed/attributable events update legitimacy state; producer should be distinct from executor for renewal/suspension/restoration | External design also resists executor self-governance. |
| Temporal ordering | Timestamps/state versions exist; `createdAt` is metadata outside derivation; no predecessor chain is defined by the open v1 action-record derivation itself | Descent/authority derivation does not by itself prove event sequence. |
| Hosted governance | May store ledgers/events/reports while remaining outside root/action-seed custody | Hosted observation/governance does not create derived authority. |

## StegVerse crosswalk

| AgentEnvelope property | Nearest StegVerse surface | Disposition |
| --- | --- | --- |
| deterministic root/domain/action derivation | identity/capability evidence input | structural correspondence only; no authority transfer |
| action envelope scope | SDK manifested operation/resources + governance inputs | compatible evidence form; no duplicate schema required absent gap proof |
| derived action address/signature | TV/TVC/KV-SKAP-adjacent identity/credential evidence boundary | technique is informative; existing StegVerse authority owners remain unchanged |
| legitimacy state/evaluator | GTG / StegCore governance evaluation | conceptual overlap; AgentEnvelope does not replace GTG/StegCore |
| current legitimacy vs valid signature | GTG + InTr commit-time admission | supports the same separation principle; InTr remains transition authority |
| public record and verifier report | TT evidence_refs / receipt_refs | can be referenced as evidence; TT remains ordered transition representation |
| event/record relation without intrinsic sequence proof | RTG causal continuity + TT temporal attribution | derivation may establish relation but not realized ordering |
| retrieved record/event evidence | Master Records custody/reconstruction | existing custody role |
| deterministic re-derivation | verification/reconstruction method | investigate whether existing schemas already encode this; do not add duplicate engine |

## Key distinctions

```text
DERIVED_ACTION_IDENTITY != CURRENT_LEGITIMACY
CURRENT_LEGITIMACY != STEGVERSE_INTR_ALLOW
SIGNATURE_VALID != TRANSITION_EXECUTED
DERIVATION_RELATION != TEMPORAL_ORDER
RE-DERIVATION_PROOF != RETAINED_EVENT_RECEIPT
```

## Current result

AgentEnvelope independently implements construction-bound authority lineage and explicitly separates cryptographic authority from present-tense legitimacy. This supports the architectural principle raised in the MIR discussion.

The open v1 material also preserves the limitation Richard Whitney identified: deterministic derivation establishes an authority/descent relation but is not itself a cryptographically linked lifecycle sequence proving when a record/actor came into existence relative to an arbitrary action.

StegVerse already has distinct formalisms and authority owners for causal relation, governance disposition, ordered transition representation, transition admission, credential/user verification, and custody/reconstruction. No new governance engine, transition engine, credential owner, or custody owner is justified by this comparison.

## Schema reconciliation result

Current Master Records at `master-records/core-lite@be0d08d73c96f50308991793327522dc01304657` already supports deterministic recomputation as a verification/reconstruction operation:

- `record_self_hash` plus declared `hash_convention` gives a canonical recomputation recipe;
- `canonical_object_digest` represents canonical derived-object identity;
- `tools/verify_record_hash.py` recomputes from canonical inputs and compares declared versus computed values fail-closed;
- reconstruction profiles retain immutable evidence references, provenance, predecessor/successor linkage, algorithm/configuration versions, achieved reconstruction fidelity, and authority posture.

Therefore the conceptual distinction:

```text
RETRIEVED_ARTIFACT
DETERMINISTIC_REDERIVATION
```

does not require a new enum, schema, engine, or authority owner. A deterministic verifier result may be retained as evidence while the underlying proposition is recomputed from canonical inputs.

Disposition: `NO_SOURCE_MUTATION_REQUIRED`.
