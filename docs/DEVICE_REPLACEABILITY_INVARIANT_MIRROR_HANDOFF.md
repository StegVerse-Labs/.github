# Device Replaceability Invariant Mirror Handoff

Status: `ACTIVE / CANONICAL / GLOBAL`
Canonical owner: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Authority effect: `NONE_POLICY_ONLY`

## Canonical invariant

Every user-operated device is an interchangeable access/transport endpoint. No specific phone, tablet, computer, browser, operating system, service worker, IndexedDB instance, or browser-local session may become the sole continuity root, execution identity, runtime-completion prerequisite, credential authority, or reconstruction authority for a StegVerse task.

Provider-backed KnowledgeVault/MyKV continuity is provider-neutral. Google Drive, iCloud, or any other configured storage provider is reached through the canonical KV provider-neutral contract; the client device is not the KV root.

A replacement device must be able to continue from canonical KV state plus retained task/claim/transition/receipt evidence without replaying already-authentic transitions merely because the device changed.

## Required interpretation

```text
ANY AUTHORIZED USER DEVICE
-> resolve configured provider-neutral MyKV/KV continuity
-> reconstruct canonical task/node/receipt state
-> WorkerCoordinator claim/fence where required
-> Interlock/InTr governed admission/transition
-> bounded execution
-> TV/TVC provider/credential operation where required
-> exact receipts
-> Master Records reconstruction
```

Device-local cryptographic or presentation work is permitted only when it is ephemeral, bounded, and reconstructible. Losing or replacing the device must not lose canonical continuity.

## Explicitly prohibited interpretations

The following are invalid architectural requirements:

- `ESTABLISHED_CURRENT_IPHONE` as a required execution substrate or continuity identity.
- `CURRENT_IPHONE_*` as a required runtime identity rather than a legacy implementation/evidence label.
- `same-device` as a required completion predicate.
- `do not switch devices` as an architectural continuity rule.
- preservation of Safari, IndexedDB, service-worker state, or a browser-local node journal as the sole canonical continuity source.
- iOS-specific access semantics as a requirement for Google Drive, iCloud, or other provider-backed KV continuity.
- creating a new task, runtime owner, scheduler, dispatcher, credential route, or authority plane merely because the user changes devices.

## Legacy labels

Historical evidence, file names, symbols, releases, and immutable receipts may still contain strings such as `CURRENT_IPHONE_*`, `current-iphone-*`, `same-device-*`, or `ESTABLISHED_CURRENT_IPHONE`. Those strings are `NON_NORMATIVE_LEGACY_LABELS_ONLY`.

They may identify what happened historically or name an implementation artifact. They must never be interpreted as current architecture, a device prerequisite, an instruction to preserve one device, or permission to bind continuity to one device.

When legacy wording conflicts with this invariant, this invariant wins and the local wording must be treated as stale or historical.

## MyKV/provider rule

MyKV/KV storage-provider identity and user-device identity are independent dimensions. A KV instance hosted in Google Drive remains the same continuity source whether accessed from iOS, Android, macOS, Windows, Linux, or another authorized client surface. The provider adapter and Interlock/InTr path own the normalized access semantics; the device must not be injected between continuity identity and provider identity.

## Preflight rule

This handoff and `control/device-replaceability-invariant.json` are mandatory canonical policy context before:

- task interpretation;
- blocker derivation;
- remediation proposals;
- runtime/substrate selection;
- KV/MyKV architecture reasoning;
- source mutation;
- creation of device-specific implementation tasks.

Any interpretation that makes a particular device, OS, browser, or browser-local state necessary for continuity must fail closed as `DEVICE_BOUND_INTERPRETATION_INVALID` and be rebound to provider-neutral KV plus retained canonical evidence.

## Runtime evidence rule

Authentic evidence from one device remains authentic evidence after that device is replaced. Device replacement does not invalidate WorkerCoordinator claims/fences, Interlock/InTr receipts, TV/TVC receipts, Master Records custody, or other canonical retained evidence unless the evidence itself explicitly and legitimately binds a security property to hardware and the canonical policy allows that binding.

A device-specific observation can prove what occurred on that device; it cannot elevate that device into the architectural owner of continuity.
