# Master Records reportable checkpoint mirror handoff

Updated: 2026-10-01
Goal Task ID: `MASTER-RECORDS-REPORTABLE-CHECKPOINT-001`
Issue: #2895
COSV ID: `50000000101000`
Status: `ACTIVE / CHECKED OUT / SPECIFICATION AND TEST VECTOR PREPARATION`

## Goal

Define a witness-neutral, privacy-minimal checkpoint primitive that commits to an authentically closed historical section of Master Records and can later be presented to an independent witness without transferring StegVerse custody, transition, credential, or governance authority.

## Authority boundary

- Master Records remains custody/reconstruction authority.
- Interlock/InTr is the registered-node data-transfer protocol boundary. Node registration is required to communicate using Interlock/InTr; use of the protocol does not itself mean the external framework's input is a governed data set.
- TV/TVC remains credential authority.
- A witness observes/retains a bounded commitment only and obtains no StegVerse authority.
- A checkpoint is not, by itself, independent proof. External observation/anchoring is a separate evidence layer.
- No AILeash/sebbi-specific transport, cadence, Bitcoin requirement, membership semantics, or API is part of v1.
- No external submission is authorized by this task until the counterpart's exact current payload/schema and submission procedure are received and mapped.

## Successor interoperability boundary

The checkpoint primitive MUST remain distinct from Interlock/InTr transport and ecosystem admission semantics:

- one-way external evidence/data can exist without treating the external framework's data as a governed external data set;
- communication **using Interlock/InTr** requires node registration;
- a manifest declares intent to enter the StegVerse ecosystem and is evaluated at the ecosystem boundary;
- StegVerse governs all output automatically, so any response/egress is a StegVerse-governed allowed transfer set;
- that output property does not imply that the originating external framework supplied a governed data set or surrendered its own governance model;
- witness status, node registration, manifest intent, admission, and permitted output are separate states and MUST NOT be collapsed;
- future witness-to-node interoperability should bind a verified witness identity to node registration only through the existing registration/manifest boundary, not through checkpoint semantics.

A useful directional model is:

```text
external data/evidence
        |
        | (not inherently a governed external data set)
        v
node registration + manifest intent
        |
        v
Interlock/InTr ecosystem communication
        |
        v
StegVerse processing
        |
        v
allowed StegVerse-governed output set
```

The successor protocol is now validated as a synthetic/non-authorizing documentary contract by merged PR #2915. `MasterRecordsCheckpoint/v1` therefore binds its communication profile to registered-node identity, manifest intent `REPORT_MASTER_RECORDS_CHECKPOINT`, exact checkpoint-digest payload commitment, receiving-framework `ALLOW`/`DENY`/`FAIL_CLOSED`, and a write-once transfer/admission receipt. These are interoperability-envelope requirements, not participating-runtime implementation requirements and not a transfer of checkpoint authority.

## Required closure predicate

Every admitted leaf MUST derive from an existing Master Records closure satisfying all of:

```text
state = RECORDED
reconstruction_status = PASS
required_evidence_validation_status = PASS
receipt_sha256 == reconstructed_receipt_sha256
```

Missing or mismatched predicates MUST fail closed. Repository artifacts, coordination state, receipts without reconstruction, or external evidence cannot substitute for this closure.

## v1 construction

### Canonical leaf

A leaf commits only to the immutable closure identity required to reconstruct the underlying Master Record:

```text
leaf_preimage =
  "stegverse-master-records-leaf/v1\n" ||
  u64be(sequence) ||
  receipt_sha256_bytes ||
  reconstructed_receipt_sha256_bytes

leaf_hash = SHA256(0x00 || leaf_preimage)
```

The sequence is the canonical Master Records sequence within the selected closed range. The two digests MUST be equal before leaf construction; carrying both makes the equality predicate independently checkable from retained verification material.

### Merkle tree

Internal nodes use domain separation:

```text
node_hash = SHA256(0x01 || left_hash || right_hash)
```

The tree follows RFC 6962-style history-tree splitting: for n > 1, split at the largest power of two strictly less than n. No duplicate-last-leaf padding is permitted.

### Checkpoint

`MasterRecordsCheckpoint/v1` contains:

- `origin`: stable StegVerse Master Records origin identifier;
- `checkpoint_sequence`: monotonic checkpoint number;
- `first_sequence` / `last_sequence`;
- `tree_size`;
- `merkle_root`;
- `predecessor_checkpoint_digest` (null only for genesis checkpoint);
- `closure_receipt_sha256`: exact terminal closure binding the selected range;
- `canonicalization`: `stegverse-master-records-merkle/v1`;
- `hash_algorithm`: `sha256`;
- `signature_profile`;
- `signing_key_id`;
- `signature`.

The checkpoint digest is SHA-256 over canonical JSON of the unsigned fields using UTF-8, sorted keys, no insignificant whitespace, integers as decimal JSON numbers, lowercase hexadecimal digests, and a trailing LF. The signature covers that digest under the declared signature profile.

### Public projection

The privacy-minimal external projection contains only:

`origin, checkpoint_sequence, tree_size, merkle_root, predecessor_checkpoint_digest, checkpoint_digest, canonicalization, hash_algorithm, signature_profile, signing_key_id, signature`.

It MUST NOT expose record payloads, subjects, correlation IDs, manifests, KV material, credentials, private keys, or reconstruction contents.

## Verification material

A retained verification package MUST support:

1. checkpoint digest/signature verification;
2. leaf recomputation from an authorized disclosed closure identity;
3. Merkle inclusion proof for a selected leaf;
4. predecessor continuity;
5. append-only consistency proof between checkpoints where the later checkpoint extends the same origin/history.

External witnessing is separately evidenced by exact checkpoint-digest equality plus the witness's own independently retrievable receipt/commitment/anchor evidence.

## Fail-closed cases

Reject checkpoint construction or verification on: non-RECORDED state; reconstruction not PASS; required evidence validation not PASS; receipt/reconstruction digest mismatch; duplicate/non-monotonic sequence; range gap; root mismatch; invalid inclusion proof; invalid consistency proof; predecessor digest mismatch; unsupported canonicalization/hash/signature profile; signature failure; or public projection containing forbidden private fields.

## Deterministic test vector

The first vector is synthetic and non-authorizing. It MUST use fixed closure identities and fixed sequence numbers, calculate leaves/root/checkpoint digest reproducibly, prove one inclusion, and include negative mutations for digest mismatch, leaf mutation, predecessor mutation and root mutation. It MUST NOT be presented as authentic Master Records runtime evidence or submitted externally.

## Current state

Issue #2895 created. Branch `master-records-reportable-checkpoint-2895` created from canonical main `d2f0db79e2da691597e25c53d6e44c480bb26898`.

No external witness submission, runtime execution, authentic Master Records checkpoint, Bitcoin anchor, deployment, or completion is claimed.

## Successor task

The generalized runtime-independent state-transition data-transfer protocol has been decomposed into `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001` / issue #2897. Its canonical handoff is `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_MIRROR_HANDOFF.md`. `MasterRecordsCheckpoint/v1` remains the first bounded interoperability profile and remains provider-neutral; this parent task does not claim external adoption or conformance.

## Returned validated protocol result

Child `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001` returned `PASS_SYNTHETIC_NON_AUTHORIZING` from PR #2915, merge commit `03e043f4680612bcbaf14601bd799b71b662877d`, dedicated verifier run `36946008125`. The parent now carries that contract in its task record, checkpoint schema and `test-vectors/master-records-checkpoint-interoperability-v1.json`.

The live receiving interface remains unavailable in this execution context: `AUTHENTIC_REGISTERED_NODE_INTR_ADMISSION_INTERFACE_UNAVAILABLE_IN_CURRENT_EXECUTION_CONTEXT`; authentic runtime execution remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`. Those are runtime-observation facts only and are not prerequisites for documentary checkpoint-profile validation.

No additional listener, credential route, SDK transport authority, participating-runtime implementation requirement, external adoption or external conformance is introduced.

## Next action

Add/extend a deterministic checkpoint verifier for the existing Merkle/checkpoint construction plus the new interoperability-envelope vectors, update README, and run repository validation at exact head. Repair only demonstrated failures and merge with expected-head protection only after repository requirements succeed. Map an external witness only after its exact current submission schema/procedure is received.
