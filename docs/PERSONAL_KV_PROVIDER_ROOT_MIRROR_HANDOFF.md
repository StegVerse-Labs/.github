# Personal KV Provider-Root Resolver Mirror Handoff

Updated: 2026-09-02
Repository: StegVerse-Labs/.github
State: SOURCE_INTEGRATED_VALIDATED_RUNTIME_SESSION_BLOCKED
Authority effect: NONE
Credential authority: TV/TVC

## Goal

Resolve a Personal KnowledgeVault runtime root for DEVICE_KV without treating the browser-local cache, Site, or a storage provider as authority.

## Existing source path

```text
DEVICE_KV request
 -> consume_device_kv_intr_materialization_request.py
 -> materialize_personal_kv_provider_root.py
 -> existing local STEGVERSE_KV_ROOT if present
    OR
 -> CVK runtime/personal_provider_binding.py
 -> TVC-owned ephemeral provider session
 -> read-only exact-byte provider materialization
 -> temporary STEGVERSE_KV_ROOT
 -> existing DEVICE_KV record-class handler
 -> HB-derived response
```

## Regression coverage

- `tests/test_personal_kv_provider_root_resolution.py`
- `.github/workflows/workspace-device-kv-validation.yml`

The regression suite proves:
- an existing local KV root wins without provider-session use;
- absent TVC provider session fails closed;
- no raw Google token environment variable is part of the resolver contract;
- the provider session reference remains `STEGVERSE_TVC_PROVIDER_SESSION_FILE`.

## Runtime blocker

The owner-connected KnowledgeVault and its installation receipt exist, and provider-root materialization source is installed. Automatic DEVICE_KV remains blocked until a legitimate TVC-owned provider session is active.

The current TVC credential-consistency handoff freezes new credential semantics. This lane may not invent a Google OAuth broker, accept a token through Site, or reinterpret a provider binding as credential authority.

## Remaining evidence gates

1. exact-head validation PASS;
2. resident source refresh containing the current resolver + CVK source;
3. active TVC provider session admitted by the authoritative TVC credential lane;
4. exact provider materialization receipt;
5. authentic `MY_KV_INSTALLATION_STATUS` consumption;
6. HB-derived exact response recovery on the registered device;
7. Site marks Personal KV sync observed only from that authentic chain.


## Validation evidence

```text
workflow: Workspace DEVICE_KV Validation Only
run: 33633878485
head: 0c36d92c525531a31ffd96ae8d58df23553d9f60
conclusion: SUCCESS
provider-root regression: PASS
runtime activation inferred: false
```
