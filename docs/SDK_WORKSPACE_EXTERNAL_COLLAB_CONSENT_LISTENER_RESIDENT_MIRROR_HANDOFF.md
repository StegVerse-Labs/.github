# SDK WorkSpace External-Collaboration Consent Listener Resident Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Parent handoff: `StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md`
Status: `ACTIVE / RESIDENT CONSENT-LISTENER REQUEST MERGED / AUTHENTIC RESIDENT CONSUMPTION NEXT`

## Purpose

Carry the already-merged TVC external-collaboration Google Drive consent listener installer into the existing sovereign resident request dispatcher without creating a second scheduler, listener implementation, Gateway owner, credential path, hosted executor, or user-operated machine.

This lane is independent of whether the client-secret reseal request has already completed. It may install and prove the loopback listener source/runtime boundary, but it must not initiate Google consent until exact external-collaboration client-secret custody and public callback reachability are separately proven.

## Canonical TVC source

```text
StegVerse-Labs/TVC
scripts/install_external_collab_google_drive_consent_service.py
Git blob: dae00dbec1a79d611a3184e185e04e6f29110348
resident unit: deploy/systemd/stegtvc-external-collab-google-drive-consent.service
loopback health: http://127.0.0.1:8786/tvc/external-collaboration/google-drive/consent/health
```

The request pins the installer by Git blob identity. A newer local TVC checkout is eligible only when the exact installer file remains byte-identical to this validated source.

## Resident request

```text
request: control/resident-execution-request.d/sdk-workspace-external-collab-consent-listener-001.json
consumer: control/resident-execution-request.d/consume-sdk-workspace-external-collab-consent-listener.py
selector: sdk_workspace_external_collab_consent_listener
request_id: RESIDENT-EXEC-SDK-WORKSPACE-EXTCOLLAB-CONSENT-LISTENER-001
receipt: receipts/sovereign-host/sdk-workspace-external-collab-consent-listener.latest.json
```

The request carries no credential material. It grants no provider operation, Google consent, public route, Gateway, GitHub-token, HeartBeat, signing, broadcast, or final readiness authority.

## Non-secret runtime inputs

The installer requires three non-secret runtime values already belonging to the resident configuration boundary:

```text
STEGVERSE_GOOGLE_DRIVE_CLIENT_ID
STEGVERSE_OWNER_BINDING_DIGEST
STEGVERSE_STEGFIN_SOURCE_ROOT
```

The dispatcher carries only those named non-secret values. The consumer fails closed when any are absent or malformed. It does not infer them from credential plaintext, GitHub secrets, browser input, or Personal-KV consent authority.

## Consumer behavior

The consumer:

1. refuses hosted CI/Render/Vercel/Cloudflare execution;
2. validates the exact non-authorizing request;
3. resolves an already-local TVC checkout and verifies the installer Git blob;
4. validates the three non-secret inputs without logging credential material;
5. checks the exact loopback health endpoint first and returns `SERVICE_ALREADY_HEALTHY` when the exact listener is already healthy;
6. otherwise requires resident root authority and invokes only the pinned TVC installer;
7. re-reads the exact loopback health endpoint after installation;
8. accepts completion only when health reports `state=HEALTHY`, `client_secret_purpose=google_drive.external_collaboration.client_secret`, `credential_material_present=false`, `provider_contact_performed=false`, and `runtime_activation_claimed=false`;
9. retains only a secret-free resident consumption receipt;
10. never claims public `stegverse.org` routing, client-secret custody, owner consent, provider probe, or WorkSpace readiness.

## Dispatcher integration

`scripts/dispatch_resident_execution_requests.py` registers the exact selector and passes only the three additional non-secret values through the existing dispatcher allowlist. `SERVICE_ALREADY_HEALTHY` is accepted as a terminal non-authorizing state. No secret-bearing environment name was added.

## Validation and merge evidence

PR: `StegVerse-Labs/.github#1382`
Merge: `f791bf2fa3eacfcdf7e9459916eec991293eb2c1`
Exact validated final source head: `fa560f09e7003b3a9d16e73c1390335c9dc726a1`

Initial source head `5107d92945d0f6f069b12f24312b3bde8988cd96` passed the focused consent-listener gate but exposed one valid repository-hygiene failure: organization-control run `34557838308` stopped at workflow-surface hygiene because the new source-validation workflow had not yet been classified. No runtime or consumer semantic step failed.

Repair head `7a654b6cad2827c6b24b9847b04bf0bb346395b2` registered the workflow in `control/workflow-surface-registry.json` as validation-only `KEEP_STANDALONE_EXCEPTION`, preserving the fail-closed workflow-proliferation invariant without granting runtime authority.

Final head `fa560f09e7003b3a9d16e73c1390335c9dc726a1` passed all observed affected gates:

- `SDK WorkSpace External Collaboration Consent Listener Resident Validation` `34558002459` — PASS;
- `Validate organization control plane - No GitHub Token Authority` `34558002391` — PASS;
- `Heartbeat Worker Project - Validation Only / No GitHub Token Authority` `34558002427` — PASS;
- `SDK WorkSpace External Collaboration Reseal Resident Validation` `34558002497` — PASS;
- `Deterministic Repository Suite - Diagnostic Evidence Only` `34558002382` — PASS;
- `Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing)` `34558002425` — PASS;
- `validate-deepseek-resident` `34558002480` — PASS.

Hosted workflow PASS is source validation only. It is not authentic systemd installation, loopback health, resident request consumption, public route binding, Google consent, or provider execution evidence.

## Collision boundary

- Existing Service Gateway owner remains `StegVerse-org/LLM-adapter#72`; this lane installs only the loopback TVC service.
- Existing client-secret reseal owner remains `sdk_workspace_external_collab_client_secret_reseal`; this lane does not modify custody.
- CMC-029 remains the sovereign TLS path and is not owned here.
- No Render, Vercel, Cloudflare tunnel, rotating tunnel, or competing HTTPS surface may be introduced.

## Completion boundary

Source/CI completion is now merged. Authentic runtime completion still requires a resident-produced secret-free receipt with either:

```text
state=SERVICE_ALREADY_HEALTHY
```

or:

```text
state=COMPLETED
loopback_health_verified=true
listener_bind=127.0.0.1:8786
```

Neither state implies public callback reachability or Google consent.

## README review

Root README semantics already cover machine-owned continuation, TV/TVC credential authority, InTr transition separation, and no hosted runtime authority. No public capability or user-facing route is introduced by this internal request, so no README text change is required. The README should be revisited only when an authentic externally observable workflow is activated.

## Next sequence

1. Observe the existing sovereign resident dispatcher consume `sdk_workspace_external_collab_consent_listener`; do not create a hosted substitute.
2. If the secret-free receipt is `BLOCKED`, remediate only the exact missing non-secret/source/root prerequisite through its existing owner.
3. Retain authentic loopback health evidence from `127.0.0.1:8786`.
4. Independently observe the already-merged client-secret reseal request and keep custody false until its authentic receipt proves otherwise.
5. Let machine-owned Service Gateway #72 bind the exact three public consent routes and CMC-029 TLS; independently verify public reachability.
6. Only after client-secret custody and public callback reachability are both proven, perform owner-present Google consent on the current iPhone.

## Human action

None. Owner interaction is not required for resident listener installation.