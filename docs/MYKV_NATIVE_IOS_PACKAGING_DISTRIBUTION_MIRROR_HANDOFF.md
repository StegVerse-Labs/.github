# Native MyKV iOS Packaging and Distribution — Canonical Work Handoff

Goal Task ID: `MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001`  
Registry source generation: 222; this source delta proposes generation 223 and must be rebased if main advances.  
Central issue: https://github.com/StegVerse-Labs/.github/issues/2638  
Canonical source registration: .github PR #2640 merged as `32bc737f5496b6bf995c8a650546227b4b7e56b5`.  
Native implementation: StegOS PR #409 merged as `664a0ba3a519823e5f3d92f7902c7051f8c060d5`. Seven exact-head GitHub workflows passed at PR head `f1dd78b3cc69ade2dcf0bff1cb84cce2a20e1dab`; unsigned iPhoneOS artifact ID `10839457097`.

## Nonblocking canonical work identity

The primary and unique work-correlation key is the existing Registry `task_id` / `correlation_id`, `MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001`. The prior established StegBrowser COSV `40000100100000` is **reused solely as a nonunique lineage coordinate**, not presented as an independently derived new COSV or an execution warrant. Source work is explicitly approved by this owner's request, and must no longer wait for an inaccessible `AI_SESSION_GATE` event.

`scripts/resolve_task_work_correlation.py --task-id MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001` deterministically reads the existing canonical Registry, rejects absent/duplicate identities and inconsistent lineage, and returns a stable work-identity digest. It does not create a ledger, credential plane, scheduler, runtime admission, claim/fence, or Master Records closure. The existing AI_SESSION_GATE remains applicable only when actual resident/governed runtime action requests one, and an absent event cannot be turned into a fabricated PERMIT. GitHub source checks are independent of authentic runtime proof.

Existing owner boundaries are explicit: StegOS owns the existing native host and source implementation (`StegVerse-Labs/StegOS#409`), TVC owns Apple credential custody and provider operations (`StegVerse-Labs/TVC#355`), Site owns the existing MyKV origin, and canonical Task Registry owns cross-repository work correlation. No duplicate native Node, KV authority, WorkerCoordinator or device is introduced.

## Source implementation and evidence

The existing native app now includes a MyKV WKWebView entry gated on retained native Node discovery. The WebKit origin must independently prove identical Node identity or fail closed; its storage is not presumed identical to Safari or the native app. All four real signing targets are enumerated: StegOSMobile, StegOSCaptureControl, StegOSCaptureBroadcast and DeviceContinuityPacketTunnel. The native host and packet tunnel require `packet-tunnel-provider` entitlement, and all four targets require proper App Group and provisioning-profile verification. The historical three-target static IPA fails closed.

Seven exact-head PR #409 workflows passed, including native compilation, unsigned iPhoneOS device packaging, signing-source checks and other boundaries. This validates source and unsigned packaging only. Neither the GitHub handoff workflow nor source contracts prove a signed IPA, a live authenticated TV/TVC provider transaction, TestFlight upload, or current-iPhone installation.

## Runtime boundary remains separate

At a **real transition**, inspect the existing resident WorkerCoordinator, Interlock/InTr, TV/TVC and applicable Master Records receipts. A nonexistent or inaccessible transition remains NOT_OBSERVED, never reclassified as FAILED or successfully admitted. If TVC provisioning is required, independently confirm actual Apple Team/certificate/profiles for the four-target bundle family and genuine Apple provider receipts, then sign and upload via existing TV/TVC path. If Apple account access or SKAP custody is genuinely unavailable, retain that as an exact provider prerequisite, **not a Task Registry source-work admission blocker**. Do not create any alternative credential manager.

Current-iPhone installation remains **FALSE / NOT_INSTALLED_NEVER_INSTALLED** until authentic physical-device installation and first-launch identity continuity evidence exists. The PWA remains optional and is not installation evidence.

## Next exact execution boundary

Consume current existing TVC #355 provider readiness and the retained exact-head unsigned artifact via the existing TV/TVC request path. Require four-profile and entitlement equality, signed IPA digest, provider upload/processing receipt, then first-install and independent native/WebKit same-Node adoption evidence. Continue other authorized source fixes even if provider operations are not available; do not reset this goal into a twenty-prompt admission loop.
