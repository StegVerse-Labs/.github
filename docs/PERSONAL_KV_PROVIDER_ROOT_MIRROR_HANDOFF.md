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


## Secret-free TVC resident-result integration — 2026-09-03

The provider-root resolver no longer accepts `STEGVERSE_TVC_PROVIDER_SESSION_FILE`.
That environment variable is explicitly rejected as a retired credential-bearing consumer input.

Canonical source chain:

```text
TVC owner-session lifecycle core:
  4c42636b346a9ea0fafbdf8f6696239ba339b819

TVC exact lease/broker contract:
  2c0a758852b5c28190e507bdc8a8b5e2ac0141c5

existing non-exportable Google Drive broker:
  StegVerse-Labs/stegfin-governance
  17930b3b22584248992f5f53d35199bef043b1d4

TVC resident secret-free result producer:
  1a1ee9626d7d2a1afe22454dc9d693c830a17a76

CVK secret-free broker materialization verifier:
  0abda122db5c963b9cbb07a41878eb3bf9304c95
```

The shared resolver now consumes only:

`STEGVERSE_TVC_PROVIDER_MATERIALIZATION_RESULT_FILE`

Expected artifact:
`stegverse.tvc.personal-kv-google-drive-materialization-result/v1`.

The resolver validates outer provider/binding/credential-authority/non-export posture, then
passes only the embedded secret-free `broker_response` to CVK for exact path/hash/size
verification and temporary KV-root materialization.

Existing local `STEGVERSE_KV_ROOT` continues to win without provider materialization.

No .github provider credential, OAuth, lease, broker, or runtime authority is created.
