# StegBrowser Ephemeral Runtime Binding Mirror Handoff

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV profile: `task.v1`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Canonical vector: `control/task-vectors/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Index shard: `control/task-vector-index.d/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Implementation handoff: `StegVerse-Labs/StegBrowser/docs/STEGBROWSER_ECOSYSTEM_EPHEMERAL_MIRROR_HANDOFF.md`

## Observed state

Merged StegBrowser source includes a Playwright/Chromium ephemeral execution substrate that consumes the bounded lease contract, opens a fresh browser context, validates origin/action/navigation scope, retains only admitted commitments and receipts, closes the context/browser, and emits a terminal destruction receipt.

Observed execution evidence:

- `StegVerse-Labs/StegBrowser@d9453e9a2e2dd56ed16a99b2ce2b297dc613de48`
- run `34298624360`: authentic Chromium retrieval of `https://stegverse.org/` + terminal destruction validation
- artifact `10084081467`, digest `sha256:a9612d5be08128a5b7dae59114499921ef66fad1101dc6701ec23839c17499d5`
- `StegVerse-Labs/StegBrowser@dd596c4cb3ccbdcd85758b4d12bc8ad9e2ee539d`
- run `34298752980`: authentic bounded Chromium retrieval of the supplied StegVerse Facebook publication URL + terminal destruction validation
- artifact `10084130220`, digest `sha256:eabb6cfe6e8e1c5a9464d3b684260f458f5adb75e72db1599963fb189f5f8a6c`

These observations prove the ephemeral browser substrate and external public-surface reachability. They do not by themselves prove full ecosystem activation or credentialed-site access.

## Active continuation

1. Validate and merge the StegSocials caller adapter under `SS-EVIDENCE-COMPARISON-001`.
2. Bind caller requests through the existing Interlock/InTr admission path so an admitted lease, rather than a caller proposal, enters StegBrowser.
3. Preserve the terminal destruction evidence path through that admitted execution.
4. Connect the existing TV/TVC + SKAP runtime boundary for one credentialed ephemeral browser session without embedding raw credential/session material in repository state, lease payloads, or retained artifacts.
5. Verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## WorkerCoordinator projection

The canonical task record is installed with `worker_claim.projection_only=true` and no fabricated claim/fence reference. WorkerCoordinator remains the source for an authentic execution claim/fence if/when the resident execution lane consumes this task.

## Current state

`CLAIMED_INTEGRATION / PUBLIC_AND_EXTERNAL_PUBLIC_SURFACE_PROOF_COMPLETE / ECOSYSTEM_ADMISSION_AND_CREDENTIALED_SESSION_PENDING`
