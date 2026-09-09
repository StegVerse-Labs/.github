# StegBrowser Ephemeral Runtime Binding Mirror Handoff

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV profile: `task.v1`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Canonical vector: `control/task-vectors/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Browser implementation handoff: `StegVerse-Labs/StegBrowser/docs/STEGBROWSER_ECOSYSTEM_EPHEMERAL_MIRROR_HANDOFF.md`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`

## Current source chain

StegBrowser native Facebook publication source and the StegSocials native caller remain merged and validated. The iOS resident path has now advanced through four distinct source boundaries without converting source evidence into runtime authority:

1. standalone loopback listener/bounded lifecycle: `StegVerse-Labs/StegBrowser@86cb4c42bbde1366ca03088a01983273f73de400`;
2. compiled `StegOSMobile` app-target binding: `StegVerse-Labs/StegOS@eb99b9222eba056478aa8d7ed3bc3bafb54fc194`;
3. durable app-local Site custody retention: `StegVerse-Labs/StegOS@bfa580942ee834799f87fdff3a9f1ea8d78067d4`;
4. same-device loopback discovery self-readback and component receipt source: `StegVerse-Labs/StegOS@9d069503671d8c5f2a19856c0adece3e2eba962e`.

## Same-device discovery/readback source

The merged source extends the existing canonical Site-node-bound `SV001ResidentActivationController`; no second activation, node-identity, WorkerCoordinator, or InTr plane is introduced.

After a bounded canonical-node-bound local session starts, StegOSMobile now connects to `127.0.0.1:8000`, requests `GET /api/resident-rendezvous/v1/discovery`, and requires the exact discovery contract:

```text
schema=stegverse.resident-rendezvous.discovery/v1
state=AVAILABLE
target_node_ref=<exact bound canonical SV-NODE>
gateway_execution_authority=NONE
credential_authority=TV/TVC
discovery_grants_authority=false
authority_effect=NONE_DISCOVERY_ONLY
```

Only after exact local readback may the app append `stegos-stegbrowser-current-iphone-rendezvous-receipts.jsonl`. The component receipt explicitly records these predicates as false until separately observed:

```text
intr_admission_observed=false
workercoordinator_claim_observed=false
canonical_request_consumption_observed=false
provider_session_observed=false
publication_observed=false
authority_effect=NONE_COMPONENT_EVIDENCE_ONLY
```

If the listener cannot be reached or the discovery object violates the exact contract after bounded retries, the local session fails closed.

Exact-head validation for the merged source passed:

- StegOS CI `34306875310`: SUCCESS;
- iOS Apple Toolchain Validation `34306875357`: SUCCESS;
- iOS Device Package Validation `34306875317`: SUCCESS, including unsigned iphoneos product construction and verification that the StegBrowser working-instance host is present in the device binary.

These runs prove installed/package capability only. They do not prove that the current participant iPhone executed the listener or emitted the component receipt.

## Durable local custody

The prior in-memory retention gap remains closed. Validated Site custody evidence is persisted atomically in app-local storage keyed by canonical node identity, reconstructed/revalidated after app process reconstruction, idempotent for the same proof, and conflicting-proof fail-closed. Persistence authority remains `NONE_EVIDENCE_ONLY`.

## Canonical resident / InTr state

The canonical resident request remains separate from component evidence. Required authentic continuation evidence still includes:

- task-specific resident request consumption;
- task-specific shared InTr `INGRESS_ADMITTED` evidence;
- authentic WorkerCoordinator claim/fence;
- admitted TV/TVC + SKAP provider session;
- actual Facebook publication/readback proof;
- publication custody/reconstruction.

A same-device discovery receipt must not be promoted into any of those predicates by interpretation.

## Active continuation

1. Materialize the existing canonical Site node binding on the current iPhone using its real `SV-NODE` identity and Node Receipt #1 digest.
2. Allow the merged StegOSMobile source to start one bounded local session and obtain an authentic exact discovery readback/component receipt.
3. Bind that authentic component evidence into the canonical `.github` resident-request continuation without converting it into execution authority.
4. Observe authentic resident request consumption and shared InTr `INGRESS_ADMITTED` evidence.
5. Reconcile through canonical WorkerCoordinator/Master Records and obtain the authentic claim/fence.
6. Resolve one admitted Facebook provider session through TV/TVC + SKAP callback-only custody.
7. Execute one already-approved StegSocials Facebook release through the merged StegBrowser native path.
8. Verify Facebook object ID, canonical URL, exact content commitment, visibility, terminal destruction, and publication custody/reconstruction.
9. Implement LinkedIn company-page parity.
10. Verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## Installation / integration remainder

- Authentic current-iPhone listener/discovery component receipt -> `StegVerse-Labs/StegOS` + `StegVerse-Labs/.github`
- Resident request consumption / InTr evidence -> `StegVerse-Labs/.github`
- WorkerCoordinator + custody reconciliation -> `StegVerse-Labs/.github` + `master-records/orchestration`
- Admitted Facebook provider session -> `StegVerse-Labs/TVC` + `StegVerse-Labs/StegBrowser`
- Live Facebook publication/readback -> `StegVerse-Labs/StegBrowser` + `StegVerse-Labs/StegSocials`
- Publication custody -> `master-records/orchestration`
- LinkedIn parity -> `StegVerse-Labs/StegBrowser` + `StegVerse-Labs/StegSocials`
- Release propagation/status -> `StegVerse-Labs/Site`
- Publication provenance -> `GCAT-BCAT-Engine/Publisher`
- Governance/admissibility docs -> `StegVerse-Labs/admissibility-wiki`
- Guardian/security docs -> `StegVerse-Labs/stegguardian-wiki`

## Current state

`NATIVE_FACEBOOK_SOURCE_PATH_MERGED_VALIDATED / STEGSOCIALS_NATIVE_CALLER_MERGED_VALIDATED / STEGOSMOBILE_DURABLE_CUSTODY_MERGED_VALIDATED / SAME_DEVICE_DISCOVERY_READBACK_MERGED_CI_APPLE_DEVICE_PACKAGE_VALIDATED / CANONICAL_TASK_COSV_INSTALLED / AUTHENTIC_CURRENT_IPHONE_WORKER_INTR_SESSION_PUBLICATION_READBACK_CUSTODY_PENDING`
