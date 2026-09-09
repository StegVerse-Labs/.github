# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-09

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Merged KV producer: `StegVerse-Labs/continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`
Merged StegOS consumer: `StegVerse-Labs/StegOS#314` -> `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`
Status: `ACTIVE / SOURCE PRODUCER+CONSUMER MERGED / AUTHENTIC INTR RECEIPT ADAPTER NEXT`

## Canonical architecture

KV is the private governed state-transition continuity boundary. A physical device is an interchangeable interoperability node after proof of control/reconstruction of the existing KV. StegOS is the runtime node, StegBrowser is the browser-capability node, and Safari/Chrome/webviews/comparable browser containers are ephemeral presentation carriers rather than identity or continuity roots.

The intended first-install seam is:

```text
minimal rendezvous
-> KV/device continuity confirmation
-> authentic KV entry transition/admission
-> actual browser/container capability observation
-> KV produces opaque purpose-bound projection context
-> current iPhone supplies the projection artifact to the minimal page
-> page validates it in memory
-> exact IPA/WASM signer materializes only after the gate passes
-> TV/TVC signing/upload boundary
-> TestFlight install
-> authentic retained runtime observation
```

No browser-local IndexedDB, cookies, localStorage, sessionStorage, browser profile, user-agent identity, device fingerprint, or public bootstrap is the continuity/privacy root for this path.

## KV producer — merged and validated

`StegVerse-Labs/continuity-vault-kit#206` merged as `47c363611210b7501cbb50abce768cfe0911057f` after Security Baseline, Repository validation diagnostics, KV Guardrails, KV Historical Provenance, and KV Historical Corpus Import all passed.

Merged source:

```text
scripts/materialize_ephemeral_browser_projection_context.py
schemas/kv-ephemeral-browser-projection-context.schema.json
tests/test_materialize_ephemeral_browser_projection_context.py
docs/KV_EPHEMERAL_BROWSER_PROJECTION_MIRROR_HANDOFF.md
README.md
```

The producer requires an already-admitted purpose-bound KV entry transition and same-lineage compatible browser-capability observation, rejects cross-lineage mixing and browser identity authority, and emits only the opaque non-authorizing projection fields required by StegOS. Raw KV lineage identity is not exported.

## StegOS consumer — merged and exact-head validated

`StegVerse-Labs/StegOS#314` merged as `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`.

The branch was first reconciled with `main` at `d84a779b05c4fc60ae52d00e2ef57e2661b03408`, leaving `behind_by=0`, and the validated binary signer artifacts were preserved.

Merged consumer source:

```text
mobile/web-bootstrap/kv-bound-ephemeral-projection-context.js
mobile/web-bootstrap/kv-projection-file-loader.js
mobile/web-bootstrap/current-iphone-testflight-bootstrap.js
mobile/web-bootstrap/current-iphone-testflight.html
tests/test_kv_bound_ephemeral_projection_gate.py
docs/KV_BOUND_STEGBROWSER_EPHEMERAL_PROJECTION_MIRROR_HANDOFF.md
```

At exact PR head `753049754fd0adad1a8f96acd41123f8e20e5f9d` all required checks passed:

```text
StegOS CI: PASS — run 34410852666
Current iPhone IPA Signing Executor Validation: PASS — run 34410852617
Current iPhone WASM Codesign Core Validation: PASS — run 34410852705
```

The WASM validation passed the pinned wrapper compile, browser-loadable package build, exact compiler diagnostics/package export, signing source-contract tests, and pinned-reference/bounded-wrapper gate before merge.

## Existing authentic admission primitive discovered

The next runtime-source gap does not require a second InTr implementation. `StegVerse-Labs/Site/stegos-node/device-kv-intr-sync.js` and the root-scoped `intr-service-worker.js` already provide the current-iPhone Device -> KV Universal InTr path.

That path validates and retains authentic `stegverse.device-kv-intr-materialization-ingress/v1` receipts with:

```text
state=INGRESS_ADMITTED
exact_request_validated=true
write_once_persisted=true
node_id=<exact registered node>
interlock_id=<exact registered Interlock>
outbox_entry_hash=<exact local write-once entry>
transport_payload_sha256=<exact payload digest>
runtime_execution_attempted=false
claim_or_fence_minted=false
credential_authority=TV/TVC
github_token_runtime_authority=NONE
authority_effect=NONE_INGRESS_ONLY
```

This is the canonical admission primitive to reuse. The next adapter must not invent a new admission authority or hand-author an `ADMITTED` receipt.

## Next implementation slice

1. Extend the existing Device -> KV InTr request vocabulary with one purpose-bound entry class for `CURRENT_IPHONE_TESTFLIGHT_SIGNING`, reusing the same root-scoped `/intr/materialization` path and current-iPhone service worker.
2. Observe required browser capabilities from actual APIs/features rather than user-agent identity or fingerprinting, bind that observation to the same request/KV lineage, and keep `browser_identity_authority=false`.
3. Adapt the authentic Device-KV `INGRESS_ADMITTED` receipt plus same-lineage capability observation into the two input receipts expected by the merged continuity-vault-kit projection producer.
4. Materialize the authentic projection JSON only after those predicates pass.
5. Project/deploy the merged minimal TestFlight page and exact signer source to Site without turning Site into KV, credential, or transition authority.
6. Perform current-iPhone Files selection only once the authentic projection artifact exists.
7. Continue TV/TVC provisioning/signing, native Build Upload, TestFlight installation, retained StegOS/StegBrowser observation, then exactly one frozen global measurement pass.

## Runtime truth

No authentic purpose-bound TestFlight KV entry receipt, same-lineage browser-capability receipt, projection JSON, TestFlight installation, current-iPhone retained-node execution, or global convergence receipt is claimed yet. Source producer and consumer are merged; authentic receipt production is now the active boundary.

## Manual work

None yet. The purpose-bound Device-KV InTr adapter and capability-observation source remain machine-executable. User interaction becomes necessary only when the authentic projection file/current-iPhone TestFlight step is actually ready.
