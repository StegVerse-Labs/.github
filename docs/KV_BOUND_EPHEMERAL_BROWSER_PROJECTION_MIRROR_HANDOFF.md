# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-09

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Active consumer PR: `StegVerse-Labs/StegOS#314`
Merged KV producer PR: `StegVerse-Labs/continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`
Status: `ACTIVE / KV PRODUCER MERGED / CURRENT-IPHONE FILES BRIDGE VALIDATING`

## Canonical architecture

KV is the private governed state-transition continuity boundary. A physical device is an interchangeable interoperability node after proof of control/reconstruction of the existing KV. StegOS is the runtime node, StegBrowser is the browser-capability node, and Safari/Chrome/webviews/comparable browser containers are ephemeral presentation carriers rather than identity or continuity roots.

The first-install seam is:

```text
minimal rendezvous
-> KV/device continuity confirmation
-> KV entry transition/admission
-> browser/container capability observation
-> KV produces opaque purpose-bound projection context
-> iPhone Files supplies that projection artifact to the minimal page
-> page validates it in memory
-> exact IPA/WASM signer materializes only after the gate passes
-> TV/TVC signing/upload boundary
-> TestFlight install
-> authentic retained runtime observation
```

No browser-local IndexedDB, cookies, localStorage, sessionStorage, browser profile, user-agent identity, device fingerprint, or public bootstrap is the continuity/privacy root for this path.

## KV producer — merged

`StegVerse-Labs/continuity-vault-kit#206` merged as `47c363611210b7501cbb50abce768cfe0911057f` after Security Baseline, Repository validation diagnostics, KV Guardrails, KV Historical Provenance, and KV Historical Corpus Import all passed.

Merged source:

```text
scripts/materialize_ephemeral_browser_projection_context.py
schemas/kv-ephemeral-browser-projection-context.schema.json
tests/test_materialize_ephemeral_browser_projection_context.py
docs/KV_EPHEMERAL_BROWSER_PROJECTION_MIRROR_HANDOFF.md
README.md
```

The producer does not decide admission or observe a browser. It accepts only:

```text
stegverse.kv.entry-transition-admission/v1
  purpose=CURRENT_IPHONE_TESTFLIGHT_SIGNING
  state=ADMITTED
  continuity_boundary=KV
  authority_effect=NONE

stegverse.kv.browser-capability-observation/v1
  purpose=CURRENT_IPHONE_TESTFLIGHT_SIGNING
  state=OBSERVED_COMPATIBLE
  continuity_boundary=KV
  browser_identity_authority=false
  authority_effect=NONE
```

Both inputs must carry the same non-empty KV lineage ID. Cross-lineage mixing fails closed. The raw lineage ID is not exported.

Output is only:

```text
stegos.kv-bound-ephemeral-projection-context/v1
purpose=CURRENT_IPHONE_TESTFLIGHT_SIGNING
entry_state=ADMITTED
kv_transition_commitment=sha256:...
admission_commitment=sha256:...
browser_capability_state=OBSERVED_COMPATIBLE
browser_capability_commitment=sha256:...
persistence_effect=NONE_EPHEMERAL_CONTEXT_ONLY
authority_effect=NONE_PROJECTION_GATE_ONLY
```

## StegOS consumer — current branch

Branch: `feat/current-iphone-wasm-static-bootstrap-001`
PR: `StegVerse-Labs/StegOS#314`

The branch was reconciled with current `main` using an explicit merge commit `d84a779b05c4fc60ae52d00e2ef57e2661b03408`; current compare state is `behind_by=0`.

Current source additions/refinements:

```text
mobile/web-bootstrap/kv-bound-ephemeral-projection-context.js
mobile/web-bootstrap/kv-projection-file-loader.js
mobile/web-bootstrap/current-iphone-testflight-bootstrap.js
mobile/web-bootstrap/current-iphone-testflight.html
tests/test_kv_bound_ephemeral_projection_gate.py
```

The consumer now requires the exact projection schema, exact SHA-256 commitment syntax, exact non-authority/non-persistence effects, ADMITTED entry state, and OBSERVED_COMPATIBLE capability state. The minimal TestFlight page accepts a JSON file through the iPhone Files picker, reads it only in memory, and only then calls the bootstrap. It does not use browser-local durable state for this projection.

The validated signer artifacts remain unchanged:

```text
artifact: stegos-current-iphone-wasm-web
artifact digest: sha256:cef2ef22a42195dced25bca2f9c99fab9f6a32f21062f1576386ee69a25d48ee
wasm sha256: 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
wasm bytes: 2277815
glue sha256: 17fe61cfdae43cbe5a1d211beb39838f58e982efdba90c7156fc36402f3adb
```

## Current validation

At head `9c14f4c1bcffff43cfe741a49d2c2c15dfd542b7`:

```text
StegOS CI: PASS
Current iPhone IPA Signing Executor Validation: PASS
Current iPhone WASM Codesign Core Validation: IN_PROGRESS at last observation
```

Do not promote PR #314 until exact-head validation is fully green.

## Remaining execution sequence

1. Finish exact-head StegOS validation and remediate any failure.
2. Maintain StegOS README and PR #314 handoff text for the merged KV producer + Files projection bridge.
3. Merge PR #314 once source validation is green.
4. Materialize authentic KV entry-transition admission and browser-capability observation receipts for `CURRENT_IPHONE_TESTFLIGHT_SIGNING`; source contracts alone are not those receipts.
5. Produce the authentic KV projection JSON and present it through iPhone Files to the minimal TestFlight bootstrap page.
6. Execute TV/TVC Apple provisioning/signing and native Build Upload.
7. Install via TestFlight on the current iPhone and capture authentic retained StegOS/StegBrowser runtime evidence.
8. Return to exactly one frozen measurement-only global convergence pass after the current-iPhone runtime predicates are satisfied.

## Runtime truth

No authentic purpose-bound KV projection file, TestFlight installation, current-iPhone retained-node materialization, or global convergence receipt is claimed by the source work above.

## Manual work

None yet. Source validation and merge work remain machine-executable. User interaction becomes necessary only when an authentic current-iPhone Files selection/TestFlight installation step is actually ready.
