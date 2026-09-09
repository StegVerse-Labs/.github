# StegVerse-001 TestFlight Materialization Mirror Handoff

Updated: 2026-09-08
Repository: `StegVerse-Labs/.github`
Goal task: `SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001`
Continuation task: `STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001`
Predecessor handoff: `docs/STEGVERSE_001_EVIDENCE_CHAIN_MIRROR_HANDOFF.md`
Custody task: `MR-STEGVERSE001-BOUNDED-AUTONOMY-001`
Observer successor: `SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001`
State: `HANDOFF_READY_EPHEMERAL_TESTFLIGHT_MATERIALIZATION_OWNER_APPLE_CONFIGURATION_PENDING`

## Canonical retained source

```text
SV001 terminal execution: COMPLETE / do not rerun
canonical terminal source: G23 / fence 23
cycle receipt: sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35
device-local reconstruction: PASS / same_execution=true
Site native activation projection: MERGED
native StegOSMobile loopback resident: MERGED / APPLE-TOOLCHAIN VALIDATED
durable app-local resident evidence store: MERGED / APPLE-TOOLCHAIN VALIDATED
same-device local discovery readback: MERGED / VALIDATED
unsigned iphoneos carrier: BUILT / HASH-VERIFIED
```

The predecessor evidence chain remains valid. This successor handoff changes only the next materialization path after the signing implementation advanced.

## Canonical Site activation

```text
StegVerse-Labs/Site PR #1130
merge: b40e5f2c59bed820dfcfdf684de40fde555ef910
public origin: https://stegverse.org/
activation page: /stegos-bootstrap/native-resident-activate.html
scheme: stegverse://resident-rendezvous/activate
authority effect: NONE_BINDING_ONLY / NONE_PROJECTION_ONLY
```

The Site path recomputes canonical Node Receipt #1, requires exact `SV-NODE-[0-9a-f]{24}`, and does not infer listener readiness, custody, continuation completion, or SV002 disposition.

## Native resident and durable mailbox

Canonical StegOS native progression:

```text
PR #245 -> 419cdfde4e2a9fe68b74c5083aefd1c6c92c1a37
  native canonical-node activation + bounded 127.0.0.1:8000 lifecycle
  StegOS CI 34305004634: SUCCESS
  iOS Apple Toolchain Validation 34305004648: SUCCESS

PR #248 -> bfa580942ee834799f87fdff3a9f1ea8d78067d4
  durable atomic app-local governed-custody evidence retention
  reconstruction reload/revalidation
  same-proof idempotence / conflict and corruption fail closed
  persistence authority NONE_EVIDENCE_ONLY
  StegOS CI 34306233655: SUCCESS
  iOS Apple Toolchain Validation 34306233903: SUCCESS

PR #253 -> merged source 9d069503671d8c5f2a19856c0adece3e2eba962e
  same-device GET /api/resident-rendezvous/v1/discovery readback
  exact schema/node/TV-TVC/NONE validation before component receipt
  StegOS CI 34306875310: SUCCESS
  iOS Apple Toolchain Validation 34306875357: SUCCESS
  iOS Device Package Validation 34306875317: SUCCESS
```

The former process-memory mailbox gap is resolved in source. Authentic current-iPhone retention remains unobserved until the signed app runs there and receives a valid governed custody proof.

## Signing surface and package contract

Full signing-surface validation merged through StegOS PR #259:

```text
merge: b9325bb69c721420218ba622297f95ef80c36cda
app: org.stegverse.stegosmobile
capture extension: org.stegverse.stegosmobile.capture
broadcast extension: org.stegverse.stegosmobile.capture.broadcast
shared app group: group.org.stegverse.stegosmobile
```

Current signing requirements and README reconciliation merged through StegOS PR #273:

```text
merge: 90535b284f8eb25fa4877fdbe4a6305db9e15f16
requirements schema: stegos.mobile-apple-signing-requirements/v1
code validation head: e4142dca91e955560a297da6e19a84981dfa9e94
StegOS CI 34309764529: SUCCESS
iOS Device Package Validation 34309764400: SUCCESS
iOS Apple Toolchain Validation 34309764367: SUCCESS
README maintenance: INCLUDED
```

The contract contains no Apple team identity, certificate private key, provisioning secret, Apple-account password, or App Store Connect private key.

## Preferred one-device TestFlight materialization

The preferred distribution path is now the existing StegOS workflow:

```text
.github/workflows/ios-ephemeral-testflight.yml
```

It requires only the existing App Store Connect API credential triplet as repository secrets:

```text
ASC_KEY_ID
ASC_ISSUER_ID
ASC_PRIVATE_KEY_P8
```

When those owner credentials are present, the workflow:

```text
-> reconciles the fixed bundle identifiers through App Store Connect API
-> requires App Groups capability
-> creates an ephemeral iOS distribution key/CSR/certificate
-> creates three ephemeral App Store provisioning profiles
-> derives one Apple Team ID from those profiles
-> verifies all profiles share the exact app group
-> archives and signs the existing StegOSMobile target family
-> verifies codesigning, bundle IDs, entitlements, and canonical resident markers
-> uploads the signed IPA to App Store Connect/TestFlight
-> deletes generated profiles and revokes the ephemeral distribution certificate
-> deletes runner-local signing material
```

The helper is `StegVerse-Labs/StegOS:tools/apple_ephemeral_provisioning.py`.

The identifier-only preparation workflow is:

```text
.github/workflows/ios-apple-identifiers-bootstrap.yml
```

It can create/reconcile the three bundle IDs and enable the App Groups capability using the same App Store Connect API credential. Source currently records one remaining owner-account configuration condition when absent: create the App Store Connect app record for `org.stegverse.stegosmobile` and ensure `group.org.stegverse.stegosmobile` is assigned to the application family.

The connected GitHub tooling available to this continuation can inspect and modify workflow source but does not expose `workflow_dispatch`; therefore it cannot truthfully manufacture the owner credential state or start these manually dispatched Apple workflows from this execution context.

## Current evidence state

```text
SV001 source/control: COMPLETE
canonical G23 receipt: OBSERVED
device-local same-execution reconstruction: PASS
Site native activation source: MERGED / VALIDATED
StegOSMobile native listener/lifecycle: MERGED / APPLE-TOOLCHAIN VALIDATED
durable native evidence retention: MERGED / APPLE-TOOLCHAIN VALIDATED
same-device discovery readback source: MERGED / VALIDATED
full app + two-extension + app-group signing surface: MERGED / VALIDATED
machine-readable Apple signing requirements: MERGED / VALIDATED
preferred ephemeral TestFlight workflow source: MERGED / SOURCE-VALIDATED
Apple identifier bootstrap workflow source: MERGED / SOURCE-VALIDATED
App Store Connect API credential configuration: NOT OBSERVED
required app-record/shared-app-group owner configuration: NOT OBSERVED
TestFlight signing workflow execution: NOT OBSERVED
signed TestFlight IPA: NOT OBSERVED
TestFlight upload: NOT OBSERVED
signed StegOSMobile installation on authentic current iPhone: NOT OBSERVED
current-iPhone native listener start: NOT OBSERVED
current-iPhone local discovery AVAILABLE: NOT OBSERVED
current-iPhone component observation receipt: NOT OBSERVED
current-device Site activation consumption: NOT OBSERVED
fresh root-InTr custody ALLOW: NOT OBSERVED
Master Records custody PASS: NOT OBSERVED
Master Records reconstruction PASS: NOT OBSERVED
local governed custody proof RETAINED: NOT OBSERVED
continuation proof materialized under observed/**: NOT OBSERVED
retained downstream same-execution chain: NOT OBSERVED
SV002 authentic disposition: NOT OBSERVED
```

## Fail-closed rules

```text
SV001 terminal -> never rerun for downstream evidence
credential configuration not observed -> do not claim TestFlight materialization
Apple identifier/app-group state not observed -> do not claim provisioning readiness
workflow source present -> does not prove workflow execution
signed IPA absent -> do not claim installation
TestFlight upload absent -> do not claim device availability
installation absent -> do not claim listener start
local discovery absent/invalid -> do not emit component runtime proof
fresh root-InTr absent/DENY/mismatch/timeout -> stop before custody
Master Records reconstruction PASS absent -> SV002 remains pending
```

## Next admissible transition

```text
owner confirms/configures ASC_KEY_ID + ASC_ISSUER_ID + raw ASC_PRIVATE_KEY_P8 in StegOS Actions secrets
-> run iOS Apple Identifiers Bootstrap when identifier state has not already been established
-> owner creates App Store Connect app record and assigns group.org.stegverse.stegosmobile if not already configured
-> run iOS Ephemeral Provision and TestFlight
-> observe signed/codesign-verified package + successful TestFlight upload
-> install that existing StegOSMobile build on the authentic current iPhone
-> open https://stegverse.org/stegos-bootstrap/native-resident-activate.html
-> obtain authentic loopback discovery AVAILABLE + component receipt
-> executeMasterRecordsSv001Custody() with exact retained G23
-> fresh root-InTr ALLOW or fail closed
-> Master Records custody/reconstruction PASS
-> exact proof POST to sovereign-local resident
-> durable local mailbox RETAINED
-> WorkerCoordinator continuation validates/materializes under observed/**
-> retained same-execution downstream reconstruction
-> SV002 observation/disposition
```

No new runtime, scheduler, heartbeat, oscillator, WorkerCoordinator, hosted primary, or custody implementation is required by this handoff.
