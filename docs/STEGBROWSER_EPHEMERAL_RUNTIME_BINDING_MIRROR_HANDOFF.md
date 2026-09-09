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

```text
canonical Site SV-NODE
-> current-iPhone owner ingress
-> TVC App Store Connect recipient + InTr route
-> SKAP sealed App Store Connect credential custody
-> secret-free TVC identifier/provisioning requests
-> current-iPhone same-device IPA signing executor
-> TVC native Build Upload
-> TestFlight installation
-> canonical same-device resident discovery
-> component evidence receipt
-> ephemeral social execution
-> external object/readback verification
-> StegSocials publication receipt
```

## Merged resident/package baseline

The real `iphoneos` product, host + two extensions, exact bundle identities, App Group entitlement wiring, canonical resident markers, durable local evidence retention, and same-device discovery readback source are validated. The provisional temporary-node route remains retired.

## Apple delivery architecture — current canonical state

The prior GitHub Apple execution path is retired and must not be restored.

### TVC source complete

Merged TVC source provides the exact App Store Connect credential class, SKAP callback-only resolver, provider-operation broker/executor, exact Apple recipient projection, exact Apple InTr route contract, and native Build Upload transaction.

```text
TVC #358 merge: cc5106b381112893893d68f61032e33ab16aab0f
TVC #360 merge: b71f41a131cf5274df7e1a05a23f5758d8667a6b
TVC #361 merge: 963c0037f7f3120a86c9ea657b65124d0ed0eeeb
TVC #363 merge: 15f01fd9e4c472982cc2212c86aecb9ea90e5b49
```

No live Apple/SKAP execution is inferred from source completion.

### StegOS provider/upload convergence

```text
StegOS #297 merge: 790ee065c491822f2c6bf06e77214e99245afd8f
StegOS #298 merge: de38c04accc6196923058db79ccf88db25d85ee6
StegOS #301 merge: ea22296e9bbae7605b241ec86c4e15deac8dc937
```

#297 merged the secret-free signed-IPA -> TVC upload request builder. #298 retired direct `ASC_*`, runner-local App Store Connect `.p8`, and `altool` upload. #301 removed the remaining Apple credential/signing execution from active GitHub workflows and merged secret-free TVC provisioning request surfaces. GitHub Actions is validation/evidence transport only.

### Xcode Cloud candidate disposition

Apple Xcode Cloud was investigated as a provider-native signing executor. It can archive/sign/distribute in Apple's macOS/Xcode environment and App Store Connect/API can manage workflows after onboarding. Apple's current documentation still requires initial Xcode Cloud project/workflow onboarding in Xcode, and the App Store Connect API exposes products only after Xcode Cloud has detected/created them; there is no Xcode Cloud product-creation bootstrap endpoint.

Therefore Xcode Cloud is rejected as the current bootstrap path because it would reintroduce an initial second-machine/Xcode dependency.

### Current-iPhone signing executor — merged source boundary

StegOS #302 replaces the generic macOS/Xcode signer blocker with a current-iPhone same-device browser/WASM signing executor contract and fail-closed orchestrator.

```text
StegOS #302 merge: b241492051e7d98e1b434afd62a030f2bdf54e3d
Current iPhone IPA Signing Executor Validation: 34359361030 SUCCESS
Apple TVC Credential Boundary Validation: 34359360843 SUCCESS
TVC TestFlight Upload Handoff Validation: 34359360807 SUCCESS
StegOS CI: 34359360758 SUCCESS
```

Merged source:

```text
contracts/current-iphone-ipa-signing-executor.v1.json
mobile/web-bootstrap/current-iphone-ipa-signing-executor.js
tests/test_current_iphone_ipa_signing_executor.py
.github/workflows/current-iphone-ipa-signing-executor-validation.yml
```

Exact execution boundary:

```text
execution_surface: CURRENT_USER_IPHONE
executor_class: SAME_DEVICE_BROWSER_WASM_IPA_SIGNER
external_machine_required: false
second_user_operated_machine_allowed: false
github_actions_execution_allowed: false
credential_authority: TV/TVC
app_store_connect_credential_custody: SKAP_SEALED_TV_TVC_OWNED
signing_private_key.origin: CURRENT_IPHONE_EPHEMERAL_SESSION
signing_private_key.persistence_allowed: false
signing_private_key.network_export_allowed: false
signing_private_key.artifact_export_allowed: false
```

The orchestrator binds exact unsigned IPA bytes/SHA-256, source commit, app ID and build number; creates an ephemeral same-device signing key + public CSR; requests certificate/profile material through TVC; requires exact app/control/broadcast bundle IDs and shared App Group in returned profiles; signs nested bundles before the host; verifies codesign structure/entitlements; destroys the key; and emits a signed-IPA commitment and secret-free TVC upload input.

The executor requires real iOS signing semantics: CodeDirectory, SuperBlob, CMS signature, CodeResources, XML + DER entitlements, depth-first nested signing, host signing last, and embedded provisioning profiles for each target.

## Current source blocker — same-device cryptographic engine

The same-device orchestration and contract are merged, but the actual cryptographic transformation engine is not yet implemented. External cross-platform/browser signing implementations were investigated as feasibility references only. A pinned reference audit confirms that pure-Rust WASM-compatible Mach-O/CMS/CodeResources signing is technically feasible, but no unverified external signer is imported into StegOS runtime.

The next implementation target is the StegOS-owned selectively absorbed/vetted WASM cryptographic core beneath the merged #302 interface. It must keep the signing private key local/ephemeral and must not require a Mac, Xcode Cloud bootstrap, GitHub signing, or a second user-operated machine.

## Apple Developer membership observation

Authentic owner-provided iPhone evidence observed on 2026-09-09 confirms Account Holder membership in the Apple Developer Program through Sep 09, 2027. This satisfies membership only; it does not prove App Store Connect API access, App Group/app record materialization, SKAP custody, signed IPA generation, TestFlight processing, or installation.

## Current physical/runtime sequence

```text
App Store Connect API access/key available to owner
-> authentic TVC Apple recipient/liveness/InTr route
-> owner seals .p8 through current-iPhone Site ingress into SKAP
-> TVC identifier/capability requests execute
-> shared App Group registered/assigned to all three App IDs
-> App Store Connect app record exists
-> current-iPhone cryptographic signer engine materialized under #302 contract
-> current-iPhone ephemeral key + CSR
-> TVC certificate/profile operations
-> same-device sign/repack/verify IPA
-> TVC native Build Upload
-> Apple processes build
-> install through TestFlight
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

StegOS `README.md` still contains stale old GitHub Apple-delivery wording. It was reviewed and is noncanonical for execution; the StegOS task handoff and this umbrella handoff supersede it until safe whole-file reconciliation is completed.

## Current state

`CANONICAL_RESIDENT_MERGED_VALIDATED / IPHONEOS_UNSIGNED_PACKAGE_VALIDATED / TVC_APP_STORE_CONNECT_SOURCE_COMPLETE / GITHUB_APPLE_CREDENTIAL_EXECUTION_RETIRED / SECRET_FREE_TVC_PROVISIONING_REQUESTS_MERGED / CURRENT_IPHONE_SIGNING_EXECUTOR_CONTRACT_ORCHESTRATOR_MERGED_VALIDATED / SAME_DEVICE_CRYPTOGRAPHIC_SIGNING_ENGINE_NOT_IMPLEMENTED / XCODE_CLOUD_BOOTSTRAP_REJECTED_REQUIRES_INITIAL_XCODE / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_RUNTIME_AND_APP_RECORD_MATERIALIZATION_PENDING / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING / NATIVE_SOCIAL_PUBLICATION_PROOF_PENDING`
