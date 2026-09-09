# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-09

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`

## Working-instance trajectory

The active objective is one authentic current-iPhone StegBrowser resident instance, followed by the first verified native social publication through the ephemeral browser path.

Merged path:

```text
canonical Site SV-NODE
-> stegverse://resident-rendezvous/activate
-> bounded StegOSMobile resident
-> 127.0.0.1:8000
-> exact same-device discovery readback
-> component evidence receipt
-> ephemeral social execution
-> external object/readback verification
-> StegSocials publication receipt
```

The real `iphoneos` product, host + two extensions, bundle identities, App Group entitlement wiring, canonical resident markers, durable local evidence retention, and same-device discovery readback source are validated. The provisional `stegverse://browser/start`/temporary-node route is retired.

## Site activation handoff observation repair

Site PR #1135 merged at `48006a08c877a3f18ab36e00e934350ec07a1f55` after exact-head success in:

- Site Bootstrap Validate;
- Site Handoff Orchestrator;
- Ecosystem Heartbeat Orchestration;
- Validate StegOS Persistent Card UX.

The deployed public activation surface now distinguishes a custom-scheme request from an actually observed browser-to-app handoff:

```text
APP_OPEN_REQUESTED_NOT_PROVEN
-> APP_HANDOFF_OBSERVED_LISTENER_NOT_PROVEN
   when Safari actually leaves the foreground
or
-> APP_HANDOFF_NOT_OBSERVED
   when Safari remains foreground after the bounded handoff interval
```

Neither state substitutes for the StegOSMobile same-device discovery receipt. The current-iPhone discovery/readback must still be observed inside the installed app.

The implementation claim for this repair was terminalized through Site PR #1147 after merge and deployment evidence were recorded.

Public surface:

`https://stegverse.org/stegos-bootstrap/native-resident-activate.html`

## Preferred Apple delivery path

The preferred path requires only three owner-supplied GitHub Actions secrets after Apple account setup:

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

Apple still requires owner-side account configuration that its public API does not replace: App Store Connect API access/key, registration/assignment of shared App Group `group.org.stegverse.stegosmobile` to all three App IDs, and creation of the App Store Connect app record for `org.stegverse.stegosmobile`.

### Apple Developer membership observation

Authentic owner-provided iPhone evidence observed on 2026-09-09 confirms:

```text
role: Account Holder
program: Apple Developer Program
membership term: 1 year
valid through: Sep 09, 2027
```

Therefore the Apple Developer membership predicate is SATISFIED and must not remain represented as pending. This evidence does not prove App Store Connect API access, shared App Group registration/assignment, App Store Connect app record creation, signed IPA generation, TestFlight processing, or current-iPhone installation.

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

Repository-side working-instance implementation is exhausted up to App Store Connect/TestFlight materialization. The remaining sequence is:

```text
Apple Developer membership active: OBSERVED / VALID THROUGH 2027-09-09
-> App Store Connect API access
-> team App Store Connect API key
-> add the three GitHub Actions secrets
-> run iOS Apple Identifiers Bootstrap
-> register/assign group.org.stegverse.stegosmobile to all three App IDs
-> create App Store Connect app record for org.stegverse.stegosmobile
-> run iOS Ephemeral Provision and TestFlight
-> install processed build from TestFlight on current iPhone
-> open https://stegverse.org/stegos-bootstrap/native-resident-activate.html in the same standalone Safari context that owns the registered canonical Node
-> tap Open StegOS Local Resident
-> require APP_HANDOFF_OBSERVED_LISTENER_NOT_PROVEN on the Site surface
-> require Same-device discovery observed: YES inside StegOSMobile
-> require non-NONE Runtime receipt digest
-> persist authentic component receipt
```

If the public surface reports `APP_HANDOFF_NOT_OBSERVED`, continue the Apple/TestFlight installation path rather than changing resident source. If the handoff is observed but StegOSMobile does not show same-device discovery, continue native loopback/runtime remediation rather than changing the Site projection.

Source/CI/package/signing-workflow evidence does not substitute for those physical observations.

## After working-instance proof

Continue directly into the native StegSocials trajectory:

```text
verified current-iPhone resident
-> short-lived social session
-> Facebook execution
-> platform object ID + canonical URL + exact content commitment + readback
-> StegSocials publication receipt
-> KV / Master Records custody
-> LinkedIn parity
```

Windsor is not required for this path.

## Current state

`CANONICAL_RESIDENT_MERGED_VALIDATED / IPHONEOS_PACKAGE_VALIDATED / COMPLETE_SIGNING_SURFACE_VALIDATED / IDENTIFIERS_BOOTSTRAP_MERGED / THREE_SECRET_EPHEMERAL_TESTFLIGHT_PIPELINE_MERGED_HARDENED / SITE_APP_HANDOFF_OBSERVATION_MERGED_DEPLOYED / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_API_AND_APP_RECORD_MATERIALIZATION_PENDING / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING / NATIVE_SOCIAL_PUBLICATION_PROOF_PENDING`
