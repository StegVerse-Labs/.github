# StegVerse-001 Evidence Chain Continuation Mirror Handoff

Updated: 2026-09-08
Repository: `StegVerse-Labs/.github`
Goal task: `SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001`
Continuation task: `STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001`
Custody task: `MR-STEGVERSE001-BOUNDED-AUTONOMY-001`
Observer successor: `SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001`
State: `HANDOFF_READY_NATIVE_RESIDENT_SOURCE_AND_UNSIGNED_IPHONE_PACKAGE_VALIDATED_SIGNED_CURRENT_IPHONE_RUNTIME_EVIDENCE_PENDING`

## Canonical terminal source

```text
execution surface: CURRENT_USER_IPHONE
claim/fence: G23 / 23
transition: SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED
cycle receipt: sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35
device-local reconstruction: PASS / same_execution=true
TVC lease: CONSUMED
G24: duplicate terminal evidence / NON-CUSTODIAL
SV001 rerun: PROHIBITED
```

The G23 hash is a verification predicate. It is not replacement source material and does not authorize any downstream transition.

## Authority separation

```text
WorkerCoordinator: continuation claim/fence only
TV/TVC: credential/bounded-lease authority
Interlock/InTr: fresh governed transition admission
Master Records: custody/reconstruction authority
SV002: observation/disposition only
HB32: timing/freshness/correlation only; authority NONE
Site: same-device materialization/carrier only; authority NONE
StegOS/StegBrowser native resident: local evidence transport/lifecycle only; authority NONE
resident mailbox retention: evidence only; authority NONE
hosted rendezvous: FALLBACK evidence transport only; authority NONE
```

No merge, CI run, Apple compilation, unsigned IPA, deployment, cache refresh, heartbeat progression, prior receipt, recovered hash, Site proof, resident discovery response, or retained mailbox record authorizes custody or SV002.

## Canonical continuation chain

```text
exact retained/recovered canonical G23
-> StegOSWebBootstrap.executeMasterRecordsSv001Custody()
-> fresh root Universal InTr MasterRecords:SV001Custody ALLOW
-> canonical Master Records custody/reconstruction PASS
-> Site governed custody proof
-> sovereign-local resident rendezvous first
-> StegOSMobile/StegBrowser loopback resident on current iPhone
-> local mailbox RETAINED
-> WorkerCoordinator continuation fetch/materialization under observed/**
-> independent continuation proof validation without Master Records mutation
-> retained downstream same-execution reconstruction
-> SV002 observation/disposition
```

Hosted rendezvous is eligible only when the sovereign-local path is unavailable; it never becomes custody/execution authority.

Canonical Site custody proof schema:

```text
stegos.master-records.portable-sv001-custody-proof/v1
```

## Existing continuation controls

Independent continuation WorkerCoordinator binding:

```text
StegVerse-Labs/.github@0dc0ca78e72573e0d129c8a4d0e70955b673b851
```

Governance-bypass repair:

```text
StegVerse-Labs/.github@fb26425243c05bc155972019beae474cd6b29d8f
```

Canonical proof materialization path:

```text
observed/site-master-records-custody.latest.json
```

Sovereign-primary continuation transport hardening:

```text
b8459ceddd5d13aeadd9fc83e686e2859b20cfed
b1ea15c47eb481dc014b07df347aa61886e80a73
3694f635bd5799e489274f2366633cda1aa39bcc
organization-control validation 34301353083: SUCCESS
```

The continuation recomputes proof digest, validates exact lowercase canonical node identity, keeps reachable local `NO_EVIDENCE` local/pending, fails closed on malformed/authority-invalid local responses, and consults hosted transport only when all sovereign-local candidates are unavailable.

## Resident evidence mailbox

`StegVerse-org/LLM-adapter` evidence mailbox source:

```text
3d35b4afef55474881c5a73d6879775b3159a343
40b177d0b929d8c2182d69574948ae551882d952
a7ae5935c5a9d542176c7437905eb38c814bbe8b
```

Endpoint:

```text
/api/resident-rendezvous/v1/evidence/site-governed-custody
```

The mailbox remains non-authorizing.

## Site sovereign-local projection

The Site transport hierarchy is sovereign-local primary with hosted fallback only. The current canonical native-activation projection merged through Site PR #1130:

```text
merge: b40e5f2c59bed820dfcfdf684de40fde555ef910
public source domain: https://stegverse.org/
activation page: /stegos-bootstrap/native-resident-activate.html
activation source: /stegos-bootstrap/sv001-native-resident-activation.js
```

The projection:

- reads the existing canonical `stegos-node-v1` registration and Receipt #1;
- recomputes and verifies Receipt #1 SHA-256;
- accepts only canonical `SV-NODE-[0-9a-f]{24}` identity;
- accepts only `https://stegverse.org` / `https://www.stegverse.org` source origin;
- creates only `stegverse://resident-rendezvous/activate` with `NONE_BINDING_ONLY` semantics;
- records projection authority `NONE_PROJECTION_ONLY`;
- does not claim that app-open proves listener readiness, custody, runtime continuity, or SV002;
- preserves the exact released v13 runtime predecessor;
- preserves the current HIL stale-worker refresh (`RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`, `skipWaiting()`, `clients.claim()`).

Exact reconciled PR validations:

```text
Ecosystem Heartbeat Orchestration 34306880636: SUCCESS
Site Handoff Orchestrator 34306880670: SUCCESS
Site Bootstrap Validate 34306880681: SUCCESS
Validate StegOS Persistent Card UX 34306880682: SUCCESS
```

Post-merge validation:

```text
Validate StegOS Persistent Card UX 34306941374: SUCCESS
Site Bootstrap Validate 34306941352: SUCCESS
```

Direct public observation of the two newly merged activation assets is still pending; source/CI success is not substituted for public propagation evidence.

## Native StegOSMobile resident capability

The prior handoff state that described the iPhone listener as unimplemented is obsolete.

### Canonical activation/lifecycle binding

StegOS PR #245 merged at:

```text
419cdfde4e2a9fe68b74c5083aefd1c6c92c1a37
StegOS CI 34305004634: SUCCESS
iOS Apple Toolchain Validation 34305004648: SUCCESS
```

The real `StegOSMobile` app target consumes the canonical Site-provided `SV-NODE-*` + Receipt #1 binding and starts the existing bounded local listener lifecycle. Local hardware labels are never converted into canonical node identity.

### Durable local evidence retention

StegOS PR #248 merged at:

```text
bfa580942ee834799f87fdff3a9f1ea8d78067d4
StegOS CI 34306233655: SUCCESS
iOS Apple Toolchain Validation 34306233903: SUCCESS
```

Validated governed-custody evidence is atomically persisted in app-local storage, restored/revalidated after app/process reconstruction, idempotent for the same proof, and conflicting/corrupt replacement fails closed. Persistence authority remains `NONE_EVIDENCE_ONLY`.

### Same-device discovery self-readback

StegOS PR #253 source head:

```text
4d46ee10f8032e2e2eeaad10867d95ad0fab4fee
```

Merged source:

```text
9d069503671d8c5f2a19856c0adece3e2eba962e
```

After a canonical node-bound local session starts, the app connects to `127.0.0.1:8000`, requests `GET /api/resident-rendezvous/v1/discovery`, validates exact discovery schema/state/node/TV-TVC/NONE-authority semantics, and only then emits a non-authorizing component observation receipt.

Exact PR #253 validation:

```text
StegOS CI 34306875310: SUCCESS
iOS Apple Toolchain Validation 34306875357: SUCCESS
iOS Device Package Validation 34306875317: SUCCESS
```

The component receipt source explicitly keeps adjacent predicates false until separately observed:

```text
intr_admission_observed=false
workercoordinator_claim_observed=false
canonical_request_consumption_observed=false
provider_session_observed=false
publication_observed=false
authority_effect=NONE_COMPONENT_EVIDENCE_ONLY
```

## Unsigned iPhone package evidence

PR #253 produced a real `iphoneos` Release package artifact:

```text
workflow run: 34306875317
artifact id: 10086970431
artifact: stegos-mobile-unsigned-device-34306875317
artifact archive digest: sha256:db0b995860d5305dd9c3111fc55c06d46199f860072ef75e966bdebdbf014b44
source commit: 4d46ee10f8032e2e2eeaad10867d95ad0fab4fee
bundle id: org.stegverse.stegosmobile
IPA SHA-256: sha256:49913d18e37158fa431525ff766c7162c44719c975b12e55d82d820bd1e339da
iphoneos build: true
StegBrowser host embedded: true
signed: false
installable_on_physical_device: false
next_required_boundary: TV_TVC_APPLE_SIGNING_AND_PROVISIONING
```

The IPA SHA-256 was independently recomputed from the downloaded artifact and matched its manifest exactly.

This is package evidence only. It does not prove installation or execution on the authentic current iPhone.

## Apple signing/provisioning boundary

Current Xcode source uses automatic signing but contains no team identity, signing certificate, provisioning profile, Apple-account credential, or App Store Connect secret.

Existing target identities that must be provisioned consistently are:

```text
app: org.stegverse.stegosmobile
capture extension: org.stegverse.stegosmobile.capture
broadcast extension: org.stegverse.stegosmobile.capture.broadcast
shared app group: group.org.stegverse.stegosmobile
```

All three targets share the app-group entitlement. No new runtime plane is required to cross this boundary; the existing compiled package needs governed Apple signing/provisioning material.

## Current evidence state

```text
SV001 source/control: COMPLETE
canonical terminal G23 receipt: OBSERVED
WorkerCoordinator claim/fence G23/23: OBSERVED
TVC lease lineage: OBSERVED / CONSUMED
device-local same-execution reconstruction: PASS
canonical retained G23 recovery: MERGED / VALIDATED
Site automatic governed custody executor: MERGED / RELEASED
independent continuation WorkerCoordinator binding: MERGED / MACHINE-SELECTABLE
governance-bypass repair: VALIDATED
resident evidence mailbox source: VALIDATED
sovereign-local Site transport hierarchy: VALIDATED
sovereign-local continuation transport hierarchy: VALIDATED
StegBrowser resident semantics: VALIDATED
StegOSMobile native listener/lifecycle: MERGED / APPLE-TOOLCHAIN VALIDATED
canonical Site -> native activation binding: MERGED / VALIDATED
durable native evidence retention: MERGED / APPLE-TOOLCHAIN VALIDATED
same-device discovery readback source: MERGED / VALIDATED
unsigned current-source iphoneos IPA: BUILT / HASH-VERIFIED
signed/installable current-iPhone package: NOT OBSERVED
current-iPhone native listener start: NOT OBSERVED
current-iPhone discovery response: NOT OBSERVED
current-iPhone component observation receipt: NOT OBSERVED
current-device consumption of current Site activation projection: NOT OBSERVED
fresh root-InTr ALLOW for custody: NOT OBSERVED
Master Records custody PASS: NOT OBSERVED
Master Records reconstruction PASS: NOT OBSERVED
Site governed custody proof local RETAINED: NOT OBSERVED
Site proof materialized to continuation observed/**: NOT OBSERVED
retained same-execution downstream chain: NOT OBSERVED
SV002 authentic disposition: NOT OBSERVED
```

## Fail-closed rules

```text
terminal SV001 -> never rerun for downstream evidence
G23 missing/ambiguous -> fail closed; no G24 substitution
signed/installable app absent -> do not claim native runtime
app-open absent -> do not claim listener start
loopback discovery absent/invalid -> no component runtime receipt
fresh root-InTr absent/DENY/mismatch/timeout -> fail closed before custody
partial/historical admission or custody -> no retroactive authorization
sovereign local reachable + NO_EVIDENCE -> remain pending locally; do not fall through to hosted
sovereign local reachable + malformed/authority-invalid -> fail closed; do not fall through to hosted
all sovereign local candidates unavailable -> hosted fallback may be attempted
hosted fallback proof -> evidence only; independently revalidate
proof digest mismatch -> fail closed
proof outside observed/** -> adapter rejects mutation
Master Records reconstruction PASS absent -> SV002 pending
SV002 nonterminal/failure -> retry SV002 independently; never reopen SV001
```

## Next admissible transition

```text
resolve TV_TVC_APPLE_SIGNING_AND_PROVISIONING for the existing validated StegOSMobile package
-> materialize the signed existing app on the authentic current iPhone
-> open the canonical Site activation projection using the existing registered Node Receipt #1
-> obtain authentic local discovery AVAILABLE + component observation receipt
-> consume exact canonical G23 through executeMasterRecordsSv001Custody()
-> fresh root-InTr ALLOW or fail closed
-> Master Records custody/reconstruction PASS
-> exact governed proof POST to local resident
-> local mailbox RETAINED
-> WorkerCoordinator continuation validates/materializes proof under observed/**
-> retained downstream same-execution reconstruction
-> SV002 observation/disposition
```

No new scheduler, heartbeat, oscillator, WorkerCoordinator, proxy, hosted primary, or authority plane is required or permitted by this handoff.
