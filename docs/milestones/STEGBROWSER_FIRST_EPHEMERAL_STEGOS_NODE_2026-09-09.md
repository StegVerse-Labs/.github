# Milestone — First StegBrowser Ephemeral StegOS Node

Date: 2026-09-09

Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
COSV: `40000100100000`

## Milestone statement

StegBrowser reached its first implementation state as a **consistent StegOS node whose browser execution can remain ephemeral while node continuity persists across sessions**.

This milestone is intentionally an implementation/source-build milestone. It does not claim physical current-iPhone runtime completion.

## What changed

The original session-only model was split into two explicit state classes.

### Retained StegBrowser node state

The following now originate in StegBrowser and survive bounded browser-session teardown:

- canonical resident node identity;
- genesis commitment;
- non-secret state commitment;
- continuity generation;
- independently admitted evidence commitments.

### Ephemeral browser execution state

The following remain disposable with the bounded browser/session lease:

- browser profile/context;
- cookies;
- provider sessions;
- credential material;
- navigation history;
- temporary page state.

The result is a persistent StegOS node continuity anchor with disposable browser execution around it.

## Canonical implementation evidence

### StegBrowser

PR #32 — `Retain resident node state in StegBrowser`

Merged commit:

`0de903391f30cb8af50a3f9a8d95cfcd1ea9edf3`

This made StegBrowser, rather than Safari/Site, the canonical origin of browser-resident node state.

### StegOSMobile

PR #309 — `Make StegBrowser the retained iOS resident node origin`

Merged commit:

`cfe1e0b27f085d084c6290d346b6c2ff6be50fcb`

The StegOSMobile app target now:

1. loads or materializes the retained StegBrowser node during controller initialization;
2. binds the local resident rendezvous lifecycle to that retained node;
3. treats Site/Safari activation only as exact-match projection metadata;
4. rejects a projected node mismatch instead of replacing the retained node;
5. preserves the retained node when the bounded browser/session lifecycle stops or expires.

Exact implementation head `03f7531bd747a3c47185eb1efd6c65412e7f05c3` passed:

- StegOS CI — run `34366834530`;
- iOS Device Package Validation — run `34366834574`;
- iOS Apple Toolchain Validation — run `34366834510`.

## Why this is a milestone

Before this change, the browser-resident lifecycle was effectively session-centered and the native path depended on a Site-provided node reference. After this change, StegBrowser has a stable node continuity identity independent of any individual ephemeral browsing lease.

That is the first implementation point at which StegBrowser can be described as a **consistent StegOS node with ephemeral browser execution** rather than merely an ephemeral browser capability.

## Milestone boundary

### Achieved

`FIRST_STEGBROWSER_EPHEMERAL_STEGOS_NODE_IMPLEMENTATION`

Evidence class:

`MERGED_SOURCE + DETERMINISTIC_CI + IPHONEOS_PACKAGE_VALIDATION + APPLE_TOOLCHAIN_BUILD`

### Not yet achieved

The following remain separate runtime milestones and must not be inferred from this implementation milestone:

- authentic current-iPhone retained-node materialization;
- same node reference observed before and after session teardown/restart;
- current-iPhone signed installation;
- live resident-rendezvous discovery from the installed application;
- authentic InTr admission / WorkerCoordinator claim-fence execution;
- live ephemeral provider/browser operation;
- external publication/readback proof.

## Next milestone candidate

`FIRST_AUTHENTIC_CURRENT_IPHONE_STEGBROWSER_NODE_CONTINUITY_PROOF`

Completion should require an installed current-iPhone build to show the same retained StegBrowser node before an ephemeral browser session, after its teardown, and after a subsequent application/session restart, with exact retained-node evidence and no session credential/cookie persistence.