# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-08

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`

## Working-instance trajectory

Profile/provider expansion is deferred. The active objective is one authentic current-iPhone StegBrowser resident instance.

Merged path:

```text
canonical Site SV-NODE
-> stegverse://resident-rendezvous/activate
-> bounded StegOSMobile resident
-> 127.0.0.1:8000
-> exact same-device discovery readback
-> component evidence receipt
```

The real `iphoneos` product, host + two extensions, bundle identities, App Group entitlement wiring, and canonical resident markers are validated. The provisional `stegverse://browser/start`/temporary-node route is retired.

## Preferred Apple delivery path

The preferred path now requires only three owner-supplied GitHub Actions secrets after Apple account setup:

```text
ASC_KEY_ID
ASC_ISSUER_ID
ASC_PRIVATE_KEY_P8
```

`ASC_PRIVATE_KEY_P8` is the raw multiline `.p8` content; no base64 conversion is required. `APPLE_TEAM_ID`, distribution certificate, and provisioning profiles are not owner secrets.

Stage A — `iOS Apple Identifiers Bootstrap`:

- creates/reuses the three explicit iOS Bundle IDs;
- enables `APP_GROUPS` capability;
- emits bootstrap evidence;
- performs no signing/upload.

Apple still requires owner-side account configuration that its public API does not replace: active Developer Program membership, App Store Connect API access/key, registration/assignment of shared App Group `group.org.stegverse.stegosmobile` to all three App IDs, and creation of the App Store Connect app record for `org.stegverse.stegosmobile`.

Stage B — `iOS Ephemeral Provision and TestFlight`:

- creates an ephemeral RSA signing key/CSR on GitHub macOS;
- creates an ephemeral `IOS_DISTRIBUTION` certificate and three `IOS_APP_STORE` profiles through Apple APIs;
- derives one Team ID from the generated profiles;
- signs the real `iphoneos` archive;
- uses the GitHub workflow run number as the unique app build number;
- exports the TestFlight IPA;
- verifies all three code signatures, exact bundle IDs, shared App Group entitlements, and canonical StegBrowser resident markers;
- uploads to App Store Connect/TestFlight;
- deletes generated profiles, revokes the ephemeral certificate, and destroys runner-local key material.

StegOS PR #272 merged at `22b97c52dda22e5532bc27d598b7d65c7654bf6d` after StegOS CI `34309757923` passed.

No user-operated Mac is required by this path.

## Physical boundary

Repository-side working-instance implementation is exhausted up to Apple account materialization. The remaining sequence is:

```text
Apple Developer membership/API access
-> team App Store Connect API key
-> add the three GitHub Actions secrets
-> run iOS Apple Identifiers Bootstrap
-> register/assign group.org.stegverse.stegosmobile to all three App IDs
-> create App Store Connect app record for org.stegverse.stegosmobile
-> run iOS Ephemeral Provision and TestFlight
-> install processed build from TestFlight on current iPhone
-> activate canonical Site resident-rendezvous projection
-> observe actual 127.0.0.1 discovery
-> persist authentic component receipt
```

Source/CI/package/signing-workflow evidence does not substitute for those physical observations.

## Deferred until working instance

Provider session acquisition, connection-profile expansion, Facebook/LinkedIn live publication, and publication custody remain deferred until signed installation plus same-device resident discovery are authentic.

## Current state

`CANONICAL_RESIDENT_MERGED_VALIDATED / IPHONEOS_PACKAGE_VALIDATED / COMPLETE_SIGNING_SURFACE_VALIDATED / IDENTIFIERS_BOOTSTRAP_MERGED / THREE_SECRET_EPHEMERAL_TESTFLIGHT_PIPELINE_MERGED_HARDENED / APPLE_ACCOUNT_PREREQUISITES_PENDING / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
