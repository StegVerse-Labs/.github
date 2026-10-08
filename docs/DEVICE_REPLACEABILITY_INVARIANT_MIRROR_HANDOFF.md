# Device Replaceability Invariant Mirror Handoff

Updated: 2026-10-08

## Scope

Organization-wide invariant for every StegVerse-Labs surface that authenticates a user, holds custody, recovers custody or executes on a client device. Machine-readable contract: `control/device-replaceability-invariant.json`.

This file and its contract are the canonical targets cited by `StegVerse-Labs/TVC/docs/CURRENT_IPHONE_PROVIDER_CORS_MIRROR_HANDOFF.md`. Neither existed before this change; repository history holds no earlier or renamed copy, so they are created here rather than restored.

## Canonical rule

```text
authorized client device:            interchangeable
admitted execution surface:          interchangeable
mandatory root prerequisite:         no device, OS, browser, Secure Enclave or ThisDeviceOnly key
mandatory recovery prerequisite:     no device, OS, browser, Secure Enclave or ThisDeviceOnly key
recovery source:                     portable sealed custody (KV/_Vault/SKAP) + owner-held recovery material
user verification authority:         KV/SKAP Vault
device identity is user verification: false
second device required:              false
```

Replacing one authorized device or admitted execution surface with another must not change the user's verifier, custody or recovery path. Device-bound keys and hardware enclaves may protect a local operation, but loss of the device never loses custody: recovery is reconstructed from portable sealed custody plus material the owner holds.

Device identity may be used for routing, capability continuity, freshness, replay protection and evidence correlation. It is never a user-verification trust root.

## Relationship to existing invariants

- `data/task-registry-global-invariants.json` and `docs/TASK_REGISTRY_KV_SKAP_VERIFIER_NODE_INVARIANT_MIRROR_HANDOFF.md` already hold that the user verifier is KV/SKAP Vault only, that StegOS nodes are interchangeable transport nodes, and that no second user-operated device is allowed. This invariant states the same position for client devices and recovery, and adds the explicit recovery-source rule.
- Credential authority stays with TV/TVC; transition/admission with Interlock/InTr; claim/fence with WorkerCoordinator; runtime-reality/provenance with Master Records.

## Authority effect

`NONE_INVARIANT_DECLARATION_ONLY`. This declaration grants no execution, credential, custody, verification or completion authority, and observes no runtime.

## Manual work

None.
