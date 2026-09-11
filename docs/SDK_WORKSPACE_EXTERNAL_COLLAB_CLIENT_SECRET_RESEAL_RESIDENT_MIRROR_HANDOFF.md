# SDK WorkSpace External-Collaboration Client-Secret Reseal Resident Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Parent handoff: `StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md`
Status: `ACTIVE / RESIDENT REQUEST + CONSUMER SOURCE IMPLEMENTED / VALIDATION PENDING`

## Purpose

Carry the already-merged TVC PR #397 one-time client-secret purpose reseal into the existing sovereign resident request dispatcher without creating a second scheduler, WorkerCoordinator, heartbeat, hosted executor, credential path, or user-operated machine.

## Canonical source

TVC reseal source:

```text
StegVerse-Labs/TVC
scripts/reseal_google_drive_external_collaboration_client_secret.py
Git blob: fba3f668e08dba300cd994e85b3c70872fc1f8e6
PR #397 merge: 15f2e1afc9bb65d506241f3c9f0a4ce4bec1f46c
```

The resident request pins the script by Git blob identity rather than requiring TVC `HEAD` to remain frozen. A newer local TVC checkout is therefore eligible only if the exact reseal execution file is byte-identical to the validated source.

## Resident request

```text
control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json
request_id: RESIDENT-EXEC-SDK-WORKSPACE-EXTCOLLAB-CLIENT-SECRET-RESEAL-001
selector: sdk_workspace_external_collab_client_secret_reseal
task_id: SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003
```

The request carries no credential material. It permits no network source fetch, GitHub token runtime authority, provider operation, heartbeat authority, second machine, or authority transfer.

Exact resident paths are taken from the canonical TVC source:

```text
Personal-KV source custody:
  /var/lib/stegverse/skap/resident-sealed/google-drive-client-secret/custody-receipt.json
external-collaboration target custody:
  /var/lib/stegverse/skap/resident-sealed/google-drive-external-collaboration-client-secret/custody-receipt.json
resident-seal activation:
  /var/lib/stegverse/skap/resident-sealed/recipient-key.latest.json
resident-seal private key:
  /run/stegverse/tv-tvc-credentials/SKAP_RESIDENT_SEAL_P256_PRIVATE.pem
```

## Consumer

```text
control/resident-execution-request.d/consume-sdk-workspace-external-collab-client-secret-reseal.py
```

It is placed under `control/resident-execution-request.d/` because that directory is already carried wholesale by `scripts/refresh_sovereign_worker_runtime_source.py`. No new source-refresh mechanism is introduced.

The canonical dispatcher registers:

```text
sdk_workspace_external_collab_client_secret_reseal
-> control/resident-execution-request.d/consume-sdk-workspace-external-collab-client-secret-reseal.py
```

The consumer:
1. fails closed in hosted CI/Render/Vercel/Cloudflare environments;
2. validates the exact non-authorizing request;
3. resolves an already-local TVC checkout;
4. verifies the TVC reseal script by Git blob identity;
5. observes source/target/activation/private-key presence without reading credential values;
6. if target custody already exists, returns `TARGET_ALREADY_PRESENT` and does not overwrite it;
7. if prerequisites are absent, returns a durable `BLOCKED` observation describing the missing condition;
8. requires root for the actual TVC reseal invocation;
9. invokes only the pinned TVC reseal script with no plaintext/client-secret argument;
10. accepts completion only when the TVC result is secret-free, exact-purpose, TV/TVC-bound, non-provider-authorizing, and the target custody receipt exists afterward;
11. persists only a non-secret resident consumption receipt.

`BLOCKED` is an observed condition, not a new canonical Task Registry lifecycle state and does not stop unrelated resident consumers.

## Existing source-refresh and dispatcher reuse

No second runtime is created. Existing source refresh already carries:

```text
control/resident-execution-request.d/
scripts/dispatch_resident_execution_requests.py
```

The dispatcher continues to visit independent consumers even when another request is blocked. HeartBeat remains synchronization/continuation only and grants no execution or credential authority.

## README review

Root `README.md` was reviewed. Its existing Autonomous Governed Entity Progression and Canonical Work semantics already require machine-owned continuation without a human approval checkpoint while preserving WorkerCoordinator, Interlock/InTr, TV/TVC, and Master Records authority separation. No public README capability change is required for this internal resident request.

## Validation boundary

Hosted tests may prove request shape, dispatcher registration, source-refresh carriage, hosted-environment refusal, target-no-overwrite behavior, and secret-free completion acceptance using synthetic paths/results. Hosted CI may not execute the real reseal because real resident key/ciphertext custody is TV/TVC-only.

Authentic completion remains:

```text
resident request source merged
-> resident source refresh materializes request + consumer
-> existing dispatcher visits exact selector
-> authentic local TVC script blob matches
-> authentic source custody + current resident-seal liveness exist
-> root resident executes TVC reseal exactly once
-> target custody exact readback exists
-> non-secret consumption receipt state=COMPLETED
```

## Next sequence

1. Validate and merge this request/consumer/dispatcher binding.
2. Observe the existing resident consume it; do not create a hosted substitute.
3. If `TARGET_ALREADY_PRESENT`, validate the existing target rather than overwrite it.
4. If `BLOCKED`, remediate the exact observed resident condition through its existing owner.
5. After authentic target custody is proven, validate bounded `GoogleDriveExternalCollaborationClientSecretUse` resolution.
6. Continue resident consent-listener installation, machine-owned Service Gateway #72 callback binding, CMC-029 `stegverse.org` HTTPS, owner-present consent, and the exact provider-file probe.

## Human action

None. This resident request is specifically intended to avoid asking the user to re-enter the Google OAuth client secret when the already-sealed Personal-KV source object is authentically available.
