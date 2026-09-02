# Personal Profile DEVICE_KV Mirror Handoff

Updated: 2026-08-31
Repository: StegVerse-Labs/.github
State: SOURCE_INTEGRATED_RUNTIME_OBSERVATION_PENDING
Authority effect: NONE
Credential authority: TV/TVC

## Goal

Permit the owner-facing My KV Personal Information surface to read and update the canonical Personal Contact Profile through the existing registered-Node DEVICE_KV / InTr boundary without granting Site direct file authority.

## Canonical record

- record class: `PERSONAL_CONTACT_PROFILE`
- destination: `_Entities/Self/Personal_Contact_Profile.json`
- source schema/runtime: `StegVerse-Labs/continuity-vault-kit`
- read operation: `REQUEST`
- write proposal: `COMMIT_CANDIDATE`
- write candidate: `PERSONAL_CONTACT_PROFILE_REPLACE`

The resident receiver performs the actual schema validation, atomic persistence, and exact readback. Site receives a persisted response only after exact canonical readback succeeds.

## Implemented source

- `scripts/personal_profile_device_kv_extension.py`
- integration in `scripts/consume_device_kv_intr_materialization_request.py`
- propagation through `scripts/refresh_sovereign_worker_runtime_source.py`
- requirement in `scripts/bootstrap_sovereign_runtime.py`
- installation through `scripts/install_sovereign_heartbeat_service.py`
- validation through `.github/workflows/workspace-device-kv-validation.yml`

## Safety boundaries

- request must be from registered Node origin and bound to `stegos-node://<node_id>`;
- personal profile payload is bounded to 256 KiB;
- secret-like fields are rejected recursively;
- exact canonical destination is fixed and cannot be supplied arbitrarily;
- Personal KV profile updates grant no identity, credential, provider, routing, execution, or transition authority;
- profile read/write does not substitute for Org-KV or Org-Emp-KV;
- HB-derived return is transport/evidence only.

## Remaining evidence gate

Authentic resident source refresh, current-device profile read, owner edit, canonical persistence, exact readback, HB-derived return, and Site consumption must still be observed before runtime activation is claimed.


## 2026-09-02 reusable Personal Form Profile integration

The existing canonical Personal Profile DEVICE_KV extension now also admits the bounded reusable form record rather than introducing a second DEVICE_KV runtime.

Added record contract:

- record class: `PERSONAL_FORM_PROFILE`
- destination: `_Entities/Self/Personal_Form_Profile.json`
- source validator: `StegVerse-Labs/continuity-vault-kit/runtime/personal_form_profile.py`
- requester: `Site / MyKVPersonalFormProfile`
- read scope: `personal_form_profile`
- write scope: `personal_form_profile_update`
- write candidate: `PERSONAL_FORM_PROFILE_REPLACE`
- read response: `stegverse.device-kv.personal-form-profile-response/v1`
- write response: `stegverse.device-kv.personal-form-profile-update-response/v1`

The implementation remains in the existing `scripts/personal_profile_device_kv_extension.py` and existing DEVICE_KV consumer wrapper. No new runtime owner, scheduler, HB signal, transport, claim/fence authority, or credential authority was added.

Reusable e-signature material remains prohibited from ordinary KV. A form profile may carry only a non-secret `skap://signing/<profile-id>` reference with `auto_apply=false`; the extension rejects automatic signature application.

The shared runtime-observability contract for this consumer is `docs/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_MIRROR_HANDOFF.md`. Authentic current-device/resident write consumption, exact canonical readback, HB-derived return recovery, and subsequent read remain required runtime evidence.

The connected Google Drive KnowledgeVault now contains an exact template `_Entities/Self/Personal_Form_Profile.json`; that file-presence fact is not DEVICE_KV consumption proof.
