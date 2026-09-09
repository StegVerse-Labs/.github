# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-08

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV profile: `task.v1`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Canonical vector: `control/task-vectors/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Browser implementation handoff: `StegVerse-Labs/StegBrowser/docs/STEGBROWSER_ECOSYSTEM_EPHEMERAL_MIRROR_HANDOFF.md`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`

## Current source chain

The working-instance lane is intentionally ahead of profile/social expansion. StegBrowser native browser mechanics remain merged, but current work is constrained to producing an authentic current-iPhone resident instance.

Merged native/device chain:

1. standalone loopback listener/bounded lifecycle: `StegVerse-Labs/StegBrowser@86cb4c42bbde1366ca03088a01983273f73de400`;
2. compiled `StegOSMobile` app-target binding and canonical Site-node activation;
3. durable app-local Site custody retention: `StegVerse-Labs/StegOS@bfa580942ee834799f87fdff3a9f1ea8d78067d4`;
4. same-device loopback discovery self-readback/component receipt: `StegVerse-Labs/StegOS@9d069503671d8c5f2a19856c0adece3e2eba962e`;
5. canonical `iphoneos` device packaging with the provisional duplicate browser host removed;
6. complete Apple signing-surface validation: `StegVerse-Labs/StegOS@b9325bb69c721420218ba622297f95ef80c36cda`;
7. GitHub-macOS signed/TestFlight build pipeline: `StegVerse-Labs/StegOS@91e93a70ed15d21d84cc7b511b6c71b64b9dc19b`.

## Canonical current-iPhone resident path

There is one resident activation path:

```text
stegverse://resident-rendezvous/activate
-> existing canonical Site SV-NODE identity
-> bounded StegOSMobile loopback lifecycle
-> 127.0.0.1:8000
-> GET /api/resident-rendezvous/v1/discovery
-> exact discovery validation
-> NONE_COMPONENT_EVIDENCE_ONLY local receipt
```

The retired provisional `stegverse://browser/start` path and temporary node identity are not part of the physical-runtime path.

After a bounded canonical-node-bound local session starts, StegOSMobile requires:

```text
schema=stegverse.resident-rendezvous.discovery/v1
state=AVAILABLE
target_node_ref=<exact bound canonical SV-NODE>
gateway_execution_authority=NONE
credential_authority=TV/TVC
discovery_grants_authority=false
authority_effect=NONE_DISCOVERY_ONLY
```

The local component receipt keeps downstream predicates false until separately observed, including InTr admission, WorkerCoordinator claim/fence, canonical request consumption, provider session, and publication.

## Physical-device package and signing surface

The unsigned `iphoneos` build path is validated against the real device SDK. The complete signing surface is now checked before credentials are introduced:

```text
host app: org.stegverse.stegosmobile
capture extension: org.stegverse.stegosmobile.capture
broadcast extension: org.stegverse.stegosmobile.capture.broadcast
shared app group: group.org.stegverse.stegosmobile
```

StegOS PR #259 merged at `b9325bb69c721420218ba622297f95ef80c36cda` after:

```text
StegOS CI 34307735221: SUCCESS
iOS Device Package Validation 34307735192: SUCCESS
```

The package gate verifies both embedded extensions, exact bundle identifiers, entitlement files, target entitlement wiring, canonical StegBrowser resident strings, and the shared App Group. This remains unsigned package evidence and does not prove installation.

## Signed/TestFlight pipeline

StegOS PR #260 merged at `91e93a70ed15d21d84cc7b511b6c71b64b9dc19b`; StegOS CI `34307932313` passed.

The workflow-dispatch-only signing lane runs on GitHub macOS so no user-operated Mac is required. It is designed to:

1. consume Apple-issued signing material only from GitHub Actions secrets;
2. create a temporary keychain;
3. install/validate the distribution certificate and the three matching provisioning profiles;
4. require exact bundle IDs and shared App Group;
5. archive the real `iphoneos` application;
6. export an App Store Connect/TestFlight IPA;
7. verify code signatures, entitlements, embedded extensions, and canonical resident markers;
8. emit signed IPA/manifest evidence;
9. optionally upload to App Store Connect/TestFlight with API-key material;
10. destroy transient signing material.

No certificate, profile, Apple-account credential, API private key, or signing private key is committed to source.

## Current external boundary

Repository implementation is no longer the blocker for signed-build construction. The remaining pre-install input is authentic Apple-issued material/account access. No connected evidence currently establishes that the required distribution certificate/provisioning profiles/App Store Connect API material already exist.

Required physical sequence:

```text
Apple-issued signing/account material
-> merged GitHub macOS signing workflow
-> signed IPA / optional TestFlight upload
-> install on current iPhone
-> canonical Site-node activation
-> actual 127.0.0.1 listener start
-> actual same-device discovery response
-> persisted current-iPhone component receipt
```

Source, CI, unsigned IPA evidence, and signing-pipeline existence must not be promoted into current-iPhone runtime evidence.

## Canonical resident / InTr state

The canonical resident request remains separate from component evidence. Required authentic continuation evidence still includes task-specific resident request consumption, shared InTr `INGRESS_ADMITTED`, authentic WorkerCoordinator claim/fence, and later provider/publication evidence. Those later social/provider steps remain deliberately deferred until a working current-iPhone instance exists.

## Active continuation

1. Materialize authentic Apple signing/account inputs for the existing app + two extension identities and shared App Group.
2. Run the merged signed/TestFlight workflow without a user-operated Mac.
3. Install the resulting build on the current iPhone.
4. Activate the existing canonical Site node binding and obtain authentic loopback discovery/component evidence.
5. Bind that component evidence into the canonical resident-request continuation.
6. Observe authentic resident request consumption and shared InTr `INGRESS_ADMITTED`.
7. Reconcile through canonical WorkerCoordinator/Master Records and obtain the authentic claim/fence.
8. Only after the working instance is proven, resume provider-session/profile/publication work.

## Current state

`NATIVE_BROWSER_SOURCE_MERGED_VALIDATED / STEGOSMOBILE_CANONICAL_RESIDENT_MERGED_VALIDATED / SAME_DEVICE_DISCOVERY_READBACK_MERGED_VALIDATED / IPHONEOS_DEVICE_PACKAGE_VALIDATED / COMPLETE_APP_EXTENSION_APPGROUP_SIGNING_SURFACE_VALIDATED / GITHUB_MACOS_SIGNED_TESTFLIGHT_PIPELINE_MERGED / APPLE_ISSUED_SIGNING_MATERIAL_PENDING / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
