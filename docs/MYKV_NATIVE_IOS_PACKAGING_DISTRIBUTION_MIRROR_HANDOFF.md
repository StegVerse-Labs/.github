# Native MyKV iOS Packaging and Distribution — Admission Mirror Handoff

Goal Task ID: `MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001` (requested; not canonically admitted)
Central admission: https://github.com/StegVerse-Labs/.github/issues/2638
Last inspected main monolithic Task Registry: generation 214 (task absent). This draft PR now stages a PROPOSED / UNCLAIMED source row and matching shard at **candidate generation 215**; neither is canonical until the PR is merged against then-current main and re-read.
Recovery COSV: `40000100100000` (not yet independently canonically derived).
Coordination status: SOURCE_PREREGISTRATION_PROPOSED (draft branch only); no canonical ACTIVE or CHECKED_OUT claim. Candidate record: `data/canonical-task-records/MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001.json`.
Predecessor: `KV-ICLOUD-AUTOMATED-UPGRADE-001` / `docs/KV_ICLOUD_AUTOMATED_UPGRADE_MIRROR_HANDOFF.md`.
Implementation owner candidate: `StegVerse-Labs/StegOS/mobile/ios/StegOSMobile.xcodeproj`; collision/admission must confirm.
Apple provider custody: existing StegVerse-Labs/TVC TV/TVC + SKAP boundaries.
Current iPhone MyKV install truth: `NOT_INSTALLED_NEVER_INSTALLED` (last owner-reported; no new install evidence).

## Canonical-admission boundary
This handoff documents exact discovered source and an admission request; its creation cannot itself register a Goal Task, derive COSV, issue WorkerCoordinator claims/fences, admit Interlock/InTr transitions, or establish Master Records closure. After candidate source registration is validated and merged, submit issue #2638 via the authentic current AI_SESSION_GATE; bind disposition to the exact latest Registry generation and converge with any existing overlapping owner before updating the monolithic registry, task record, task vector/index and canonical task state. Do not manually bypass deterministic admission.

## Reusable source
- StegOS native host project: `mobile/ios/StegOSMobile.xcodeproj`, native app entry, native retained StegBrowser Node, existing local rendezvous and on-device continuity. Never create a second native identity or KV.
- Site MyKV runtime: `https://stegverse.org/my-kv.html`; PWA `my-kv-install.html` remains optional fallback and explicitly is not native installation evidence.
- Existing native unsigned build: `.github/workflows/ios-device-package-validation.yml` builds iPhoneOS device app and uploads an unsigned IPA plus SHA-256 manifest.
- Existing signing handoff: `.github/workflows/ios-signed-testflight-build.yml` derives a zero-input credential-free signing request for TV/TVC; workflow does not hold Apple secrets, does not execute native Apple signing and does not prove signed artifact.
- Existing TVC provider flow and same-device browser/WASM signed-IPA byte ingress: reuse exact existing owners; reconcile actual capabilities and authentic provider receipts.
- Current signing-requirements contract lists host plus two embedded capture extensions; actual native project additionally includes DeviceContinuityPacketTunnel. Reconcile *all actual embedded targets* and approved entitlements against TV/TVC provisioning before declaring signability.

## Implementation gate
Place a MyKV owner-facing native navigation surface inside the existing StegOS Mobile host; retain existing native resident Node/continuity and do not silently equate its Node with separate WKWebView-origin state. Bind identity by independently verifiable existing contract before KV storage operations; do not forge a HEALTHY web diagnostic. Load only HTTPS admitted MyKV origin and preserve current Site JS/governance rather than cloning a second runtime. Native UI may report separate native and web health, not a falsely unified success. Keep PWA an optional fallback.

## Evidence/status
- Canonical task admission: NOT OBSERVED. Candidate PROPOSED/UNCLAIMED source row staged at generation 215 in draft `.github` PR; source registration itself grants no execution authority.
- Native MyKV code integration: PENDING.
- Exact-head source tests and iPhoneOS package for new integration: NOT OBSERVED.
- TV/TVC signed IPA, provisioning entitlement verification, TestFlight acceptance: NOT OBSERVED.
- Current-iPhone native installation and first-launch Node/KV identity continuity: NOT OBSERVED.
- CURRENT_IPHONE_MYKV_INSTALLED: FALSE.

## Authorized next steps
1. Validate the candidate source registration against exact current main, merge only after required checks, re-read its new generation, then consume authentic collision/admission outcome for issue #2638 and reconcile COSV and actual canonical owner.
2. Integrate native MyKV in existing StegOS app; perform source tests and exact-head Apple iPhoneOS build without exposing secrets.
3. Exercise existing TV/TVC signing and TestFlight path only after credentials/entitlements are authentically available in that authority boundary, retain actual signed byte/hash receipt.
4. Preserve current-iPhone installation false until independent physical-iPhone installation and first-launch receipts prove otherwise.

No second user-operated device, duplicate scheduler/runtime/authority plane, GitHub-held credential, or fabricated build, signing or installation evidence.
