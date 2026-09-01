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
