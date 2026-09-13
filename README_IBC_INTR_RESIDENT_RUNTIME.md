# IBC InTr Resident Runtime Consumer

Updated: 2026-09-12

Goal Task ID: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Handoff: `docs/IBC_INTR_RESIDENT_RUNTIME_MIRROR_HANDOFF.md`
COSV ID: `10100000100000`

This repository slice carries the already-verified Cosmos Hub → Osmosis ACK evidence into the canonical StegVerse resident execution trajectory without creating a second scheduler, credential authority, runtime authority, or custody path.

## Canonical source

```text
control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json
scripts/consume_ibc_intr_resident_request.py
scripts/dispatch_resident_execution_requests.py
tests/test_ibc_intr_resident_consumer.py
```

The historical sovereign-host consumer remains valid as a bounded resident transport implementation, but it is no longer the only practical execution path for this task. The current canonical delivery trajectory is the already-merged current-iPhone StegOSMobile/TestFlight path.

## Current-iPhone source binding

StegOS PR #299 merged the native IBC launch coordinator into the real `StegOSMobile` application launch path. The current TestFlight successor's unsigned IPA is built from a descendant source commit, so no separate IBC-specific IPA rebuild is required.

Exact current product identity:

```text
unsigned IPA sha256: 557d559082bdefca5fcc69c86f342d8cc035c2d803d154de5ed45b5677f80c35
unsigned IPA bytes: 389564
WASM signer sha256: 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
execution surface: CURRENT_USER_IPHONE
signer class: SAME_DEVICE_BROWSER_WASM_IPA_SIGNER
credential authority: TV/TVC
App Store Connect credential custody: SKAP_SEALED_TV_TVC_OWNED
```

## Allocator lineage

`TASK-2026-0010` generation 6 / fence 6 is retained predecessor provenance. The authentic same-device recovery page proved that receipt was already present and performed no allocator mutation.

The current product owner trajectory has advanced to:

```text
canonical allocator task: TASK-2026-0011
claim_registry_generation: 7
fencing_token: 7
claim state: CLAIM_GRANT_OBSERVED
allocation state: ALLOCATION_COMPLETE
journal replay: PASS
```

Site has already merged and publicly published the exact frozen TASK-2026-0011 TestFlight product. The same-device KV recovery wrapper is also merged on Site main through PR #1237 at merge commit `b847d4e408571efb9ff511f1facbc3f38128846d`.

The wrapper derives the exact `CURRENT_IPHONE_TESTFLIGHT_SIGNING` projection in memory from the established current-iPhone Device→KV/InTr path, requires `KV_INSTALLATION_VERIFIED`, and passes that projection directly into the frozen TestFlight bootstrap. It does not synthesize projection commitments or require a saved projection JSON for the normal path.

## Current unresolved runtime boundary

Repository/source publication is no longer the first unresolved predicate. The next authentic evidence is same-device execution from the established current iPhone:

```text
current-iPhone Device→KV projection materialization
-> KV installation verification
-> exact frozen TASK-2026-0011 bootstrap
-> TVC RESOLVE_APP_RESOURCE_ID
-> TVC provisioning material
-> same-device WASM IPA signing
-> exact signed-IPA verification
-> TVC native Build Upload
-> TestFlight processing/install
-> native StegOSMobile launch
-> Documents/ibc-verified-intr-ack-request-consumption.latest.json
```

Source, CI, merge, allocator recovery, publication, signing setup, or TestFlight upload alone do not prove IBC resident execution. Only authentic physical-iPhone launch and the resulting app-local receipt can advance the IBC resident-consumption predicate.

## Authority boundary

```text
Interlock/InTr: transition/admission authority
WorkerCoordinator / canonical allocator: claim/fence authority
KV: private continuity boundary
TV/TVC: credential/provider/signing authority
SKAP: sealed credential custody
Site: public projection/rendezvous only
GitHub Actions: validation/evidence transport only
HB: carrier/observability only
current iPhone: physical execution surface
```

No second user-operated machine is required or admitted as the completion path.
