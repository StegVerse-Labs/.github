# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-09

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`
- TVC Apple handoff: `StegVerse-Labs/TVC/docs/APP_STORE_CONNECT_TV_TVC_SKAP_MIRROR_HANDOFF.md`

## Working-instance trajectory

The active objective remains one authentic current-iPhone StegBrowser resident instance, followed by the first verified native social publication through the ephemeral browser path.

Merged resident path:

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

The real `iphoneos` product, host + two extensions, exact bundle identities, App Group entitlement wiring, canonical resident markers, durable local evidence retention, and same-device discovery readback source are validated. The provisional temporary-node route remains retired.

## Apple delivery architecture — current canonical state

The prior three-secret GitHub Apple execution path is retired and must not be restored.

Current merged sequence:

```text
current-iPhone owner ingress
-> TVC App Store Connect recipient projection + InTr route
-> SKAP sealed App Store Connect credential custody
-> TVC callback-only provider session
-> secret-free StegOS identifier/provisioning requests
-> admitted macOS/Xcode signing executor
-> executor-local ephemeral signing key + CSR
-> TVC certificate/profile operations
-> local sign/export/verify
-> secret-free signed-IPA -> TVC Build Upload request
-> TVC native Build Upload transaction
-> TestFlight processing/install
-> same-device StegBrowser discovery proof
```

### TVC source complete

Merged TVC source now provides:

```text
exact App Store Connect credential class
SKAP callback-only resolver
provider-operation broker/executor
exact App Store Connect recipient projection
exact App Store Connect InTr route contract
native Build Upload create/reserve/chunk-upload/uploaded=true commit transaction
```

Key evidence:

```text
TVC #358 merge: cc5106b381112893893d68f61032e33ab16aab0f
TVC #360 merge: b71f41a131cf5274df7e1a05a23f5758d8667a6b
TVC #361 merge: 963c0037f7f3120a86c9ea657b65124d0ed0eeeb
TVC #363 merge: 15f01fd9e4c472982cc2212c86aecb9ea90e5b49
```

No live Apple/SKAP execution is inferred from source completion.

### StegOS provider/upload convergence

StegOS #297 merged the secret-free signed-IPA -> TVC upload request builder.

StegOS #298 retired direct `ASC_*`, runner-local App Store Connect `.p8`, and `altool` upload from the signed TestFlight workflow.

StegOS #301 then removed the remaining Apple credential/signing execution from active GitHub workflows and introduced:

```text
scripts/build_tvc_apple_provisioning_request.py
contracts/apple-signing-executor-request.v1.json
.github/workflows/apple-tvc-credential-boundary-validation.yml
```

Exact merge:

```text
StegOS #301 merge: ea22296e9bbae7605b241ec86c4e15deac8dc937
Apple TVC Credential Boundary Validation: 34358157254 SUCCESS
TVC TestFlight Upload Handoff Validation: 34358157189 SUCCESS
StegOS CI: 34358157211 SUCCESS
```

Active Apple workflows now carry no `ASC_*`, App Store Connect `.p8`, Apple distribution-certificate secret, provisioning-profile secret, `security import`, or `altool` execution. GitHub Actions is validation/evidence transport only.

### Secret-free TVC provisioning requests

StegOS can now construct credential-free requests for:

```text
bundle ID lookup/create
APP_GROUPS capability enablement
IOS_DISTRIBUTION certificate issuance from a public CSR
IOS_APP_STORE profile creation
```

Every request declares:

```text
credential_authority: TV/TVC
credential_custody: SKAP_SEALED_TV_TVC_OWNED
github_actions_credential_access: false
consumer_credential_access: false
```

### Signing executor boundary

The remaining signing requirement is now explicit rather than hidden in GitHub Actions:

```text
execution_surface: ADMITTED_MACOS_XCODE_SIGNING_EXECUTOR
external_machine_required: false
github_actions_execution_allowed: false
github_actions_role: VALIDATION_AND_EVIDENCE_TRANSPORT_ONLY
signing_private_key_origin: EXECUTOR_LOCAL_EPHEMERAL
signing_private_key_export_allowed: false
credential_authority: TV/TVC
```

The executor must generate its signing key and CSR locally, submit only the CSR through TVC, consume returned certificate/profile material transiently, sign/export/verify the IPA, call TVC Build Upload, destroy the signing key, and emit evidence commitments.

No second user-operated Mac is an acceptable substitute.

## Apple Developer membership observation

Authentic owner-provided iPhone evidence observed on 2026-09-09 confirms:

```text
role: Account Holder
program: Apple Developer Program
membership term: 1 year
valid through: Sep 09, 2027
```

This satisfies Apple Developer membership only. It does not prove App Store Connect API access, shared App Group registration/assignment, App Store Connect app record creation, SKAP custody, signed IPA generation, TestFlight processing, or current-iPhone installation.

## Site activation handoff

The deployed Site surface still distinguishes requested custom-scheme navigation from an observed browser-to-app foreground handoff. Neither state substitutes for StegOSMobile same-device discovery.

Public surface:

`https://stegverse.org/stegos-bootstrap/native-resident-activate.html`

## Current physical/runtime boundary

The remaining sequence is:

```text
App Store Connect API access/key available to owner
-> authentic TVC Apple recipient/liveness/InTr route
-> owner seals .p8 through current-iPhone Site ingress into SKAP
-> TVC identifier/capability requests execute
-> shared App Group registered/assigned to all three App IDs
-> App Store Connect app record exists
-> admitted macOS/Xcode signing executor materialized
-> executor-local signing key + CSR
-> TVC certificate/profile operations
-> sign/export/verify IPA
-> TVC native Build Upload
-> Apple processes build
-> install through TestFlight on current iPhone
-> activate canonical Site rendezvous
-> observe exact same-device discovery
-> persist component runtime/observation evidence
```

Source/CI/package validation does not substitute for those observations.

## After working-instance proof

Continue directly into native StegSocials:

```text
verified current-iPhone resident
-> short-lived social session
-> approved Facebook/LinkedIn execution
-> platform object ID + canonical URL + exact content commitment + readback
-> StegSocials publication receipt
-> KV / Master Records custody
```

Windsor is not required for this path.

## Documentation note

StegOS `README.md` was reviewed during #301 and still contains an obsolete paragraph describing the old three-secret GitHub TestFlight path. That paragraph is stale and must not be treated as canonical execution guidance; the StegOS task handoff and this umbrella handoff supersede it until README text is reconciled.

## Current state

`CANONICAL_RESIDENT_MERGED_VALIDATED / IPHONEOS_UNSIGNED_PACKAGE_VALIDATED / TVC_APP_STORE_CONNECT_SOURCE_COMPLETE / STEGOS_PROVIDER_AND_UPLOAD_HANDOFF_COMPLETE / GITHUB_APPLE_CREDENTIAL_EXECUTION_RETIRED / SECRET_FREE_TVC_PROVISIONING_REQUESTS_MERGED / ADMITTED_MACOS_XCODE_SIGNING_EXECUTOR_NOT_MATERIALIZED / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_RUNTIME_AND_APP_RECORD_MATERIALIZATION_PENDING / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING / NATIVE_SOCIAL_PUBLICATION_PROOF_PENDING`
