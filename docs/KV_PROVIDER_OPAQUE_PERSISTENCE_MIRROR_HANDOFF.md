# KV Provider-Opaque Persistence Mirror Handoff

Updated: 2026-09-13

```text
goal_id: KV-PROVIDER-OPAQUE-PERSISTENCE-001
parent_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/continuity-vault-kit
adjacent_runtime_owner: StegVerse-Labs/StegOS
skap_credential_authority: TV/TVC
transition_authority: Interlock/InTr
github_runtime_authority: NONE
second_user_operated_device_required: false
hosted_runtime_fallback: NONE
```

## Reconciliation finding

The parent Device <-> KV <-> SKAP goal already requires provider-independent protection and fail-closed custody. This child does not introduce a new architectural requirement. It isolates the implementation/evidence gap discovered during source reconciliation.

SKAP persisted-object protection is already materially enforced in TVC source: persisted envelopes are cryptographically sealed, plaintext persistence and KV decryption authority are rejected, decryption requires a separate protected recipient key operation, and persisted execution authority is forbidden.

The canonical KV privacy/state-transition contract establishes that storage providers are materialization/custody rather than identity or authority roots, but current repository evidence does not yet demonstrate an equivalent provider-opaque cryptographic persisted-object layer for ordinary KnowledgeVault materialization.

## Required invariant

For every provider-backed KV #1/#2/#n object:

```text
provider possesses persisted bytes
!= plaintext access
!= decryption capability
!= use authority
!= transition authority
```

Persisted provider objects must therefore be ciphertext/authenticated envelope material whose decryption requires a separately held admitted protected-key operation. The provider object itself must contain no reusable plaintext key material, private key, decryption capability, transition grant, or authority-bearing secret.

## Completion predicates

```text
KV_PERSISTED_OBJECTS_ARE_PROVIDER_OPAQUE_BY_CRYPTOGRAPHIC_CONSTRUCTION
STORAGE_PROVIDER_POSSESSION_DOES_NOT_CONFER_PLAINTEXT_ACCESS
STORAGE_PROVIDER_POSSESSION_DOES_NOT_CONFER_DECRYPTION_CAPABILITY
STORAGE_PROVIDER_POSSESSION_DOES_NOT_CONFER_USE_OR_TRANSITION_AUTHORITY
KV_DECRYPTION_REQUIRES_ADMITTED_NON_EXPORTABLE_OR_EQUIVALENT_PROTECTED_KEY_OPERATION
KV_OBJECT_BINDINGS_ARE_AUTHENTICATED_AND_TAMPER_EVIDENT
PLAINTEXT_IS_NOT_PERSISTED_IN_PROVIDER_MATERIALIZATION
KEY_MATERIAL_IS_NOT_PERSISTED_WITH_PROVIDER_OBJECTS
EXACT_READBACK_FAILS_CLOSED_ON_KEY_BINDING_OR_OBJECT_TAMPER
SKAP_TV_TVC_CREDENTIAL_AUTHORITY_REMAINS_UNCHANGED
```

## Implementation direction

Reuse the existing protected-key/ciphertext-envelope principles rather than creating another credential system. The KV envelope must be provider-neutral and bind at minimum the KV instance/set, object identity/version, purpose/classification, prior-transition or state commitment where applicable, recipient/protected-key capability identifier, and ciphertext integrity commitment.

The resolver must fail closed before plaintext materialization when object bindings, recipient capability, authorization/admission context, integrity, or transition prerequisites do not match. Provider storage access alone must never be sufficient to invoke decryption.

Interlock/InTr remains the governed transition-admission authority. TV/TVC remains credential authority for SKAP/provider credentials. KV protected-object encryption does not mint either authority.

## Negative validation requirements

Tests must prove at least:

- copied provider object without the protected-key capability cannot decrypt;
- provider locator/account identity does not satisfy decryption admission;
- modified ciphertext, AAD/bindings, recipient capability, KV instance/object identity, or transition commitment fails closed;
- ordinary provider materialization contains no plaintext secret/key field;
- decrypted bytes are not persisted as a side effect of readback;
- exact readback succeeds only through the admitted capability path;
- the same contract works independently of iCloud Drive, Google Drive, OneDrive, Dropbox, local/provider storage, or future admitted storage media.

## Parent return contract

Return this component to `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` only after source implementation and deterministic negative/positive validation establish the provider-opaque KV persisted-object boundary. Authentic runtime proof remains separately required by the parent before it can claim roundtrip completion.

## Manual work

None.
