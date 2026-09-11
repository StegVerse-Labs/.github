# SDK WorkSpace External-Collaboration Client-Secret Reseal Resident Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Parent handoff: `StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md`
Status: `ACTIVE / RESIDENT BINDING MERGED + VALIDATED / AUTHENTIC CONSUMPTION NEXT`

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

## Merge and validation evidence

StegVerse-Labs/.github PR #1370 merged at:

```text
de09dcb3f74c19e3f891704f4db33db915ee61c6
```

Final exact-head source commit before merge:

```text
a3d8002180c5ea8dddc51d735c6541da6dd272f3
```

Observed exact-head validations all completed successfully:

```text
34555121264 Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing) PASS
34555121049 SDK WorkSpace External Collaboration Reseal Resident Validation PASS
34555121010 Validate organization control plane - No GitHub Token Authority PASS
34555120999 validate-deepseek-resident PASS
34555121000 Deterministic Repository Suite - Diagnostic Evidence Only PASS
34555121027 Heartbeat Worker Project - Validation Only / No GitHub Token Authority PASS
```

The previously reported repository-wide integration failures are therefore repaired on the merged implementation. No further CI repair is pending for PR #1370.

## Authentic runtime observation

As of this reconciliation, repository-tracked `main` does not contain:

```text
receipts/sovereign-host/sdk-workspace-external-collab-client-secret-reseal.latest.json
```

Therefore no authentic resident consumption state is claimed yet. In particular, source merge and green CI do not prove any of:

```text
TARGET_ALREADY_PRESENT
BLOCKED with an authentic local prerequisite observation
COMPLETED resident reseal
external-collaboration target custody readback
resident-seal liveness
provider authorization or provider contact
```

The next evidence must come from the existing authorized resident dispatcher/runtime, not from a hosted substitute.

## README review

Root `README.md` was re-reviewed against the merged binding. Its existing Autonomous Governed Entity Progression and Canonical Work semantics already require machine-owned continuation without a human approval checkpoint while preserving WorkerCoordinator, Interlock/InTr, TV/TVC, and Master Records authority separation. No public README capability change is warranted because authentic runtime consumption has not yet been proven.

## Validation boundary

Hosted tests prove request shape, dispatcher registration, source-refresh carriage, hosted-environment refusal, target-no-overwrite behavior, and secret-free completion acceptance using synthetic paths/results. Hosted CI may not execute the real reseal because real resident key/ciphertext custody is TV/TVC-only.

Authentic completion remains:

```text
resident request source merged
-> resident source refresh materializes request + consumer
-> existing dispatcher visits exact selector
-> authentic local TVC script blob matches
-> authentic source custody + current resident-seal liveness exist
-> root resident executes TVC reseal exactly once OR validates existing target custody
-> target custody exact readback exists
-> non-secret consumption receipt records the authentic observed state
```

## Next sequence

1. Observe the existing resident consume the merged selector; do not create a hosted substitute or competing resident runtime.
2. If the authentic receipt is `TARGET_ALREADY_PRESENT`, validate the existing external-collaboration target custody and bounded use path without overwrite.
3. If the authentic receipt is `BLOCKED`, remediate the exact observed local prerequisite through its existing owner, then re-dispatch the same request.
4. If the authentic receipt is `COMPLETED`, retain exact target custody readback/use evidence and reconcile the Task Registry/runtime proof fields.
5. After authentic target custody is proven, validate bounded `GoogleDriveExternalCollaborationClientSecretUse` resolution.
6. Continue resident consent-listener installation, machine-owned Service Gateway #72 callback binding, CMC-029 `stegverse.org` HTTPS, owner-present consent, and the exact provider-file probe.
7. Feed the provider result through the SDK bridge/active-probe path, then continue Shared Docs lifecycle transitions, MIR reporting, Master Records custody/reconstruction, and one-current-device proof.

## Human action

None. Do not ask the user to re-enter the Google OAuth client secret while the merged resident request is still intended to reuse admissible existing Personal-KV ciphertext custody when present.
