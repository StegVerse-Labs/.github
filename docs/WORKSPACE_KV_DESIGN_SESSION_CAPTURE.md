# WorkSpace / KV Design Session Capture

Date: 2026-09-28
Repository: `StegVerse-Labs/.github`
Related task: `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001` (`PROPOSED` / `UNCLAIMED`)
Status: **CAPTURE ONLY — registry-owner statements recorded verbatim in intent, not yet applied to any record.**

This records decisions and findings from a working session. It changes no record,
resolves no blocker in the registry, and grants no authority. Blocker resolutions
below are stated by the registry owner in discussion; applying them to
`STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001` is a separate, unperformed step.

## 1. BLK1 — canonical WorkSpace surface: RESOLVED by composition

Not a merge of `workspace.html` and `my-kv.html`. Both stay, with different jobs.

- `my-kv.html` — MyKV entry point, standalone page
- an OrgKV page — standalone entry point
- a Company-Employee-KV page — standalone entry point
- `workspace.html` — the **shell**: tabs, where a tab may be a browser page, a
  document writer, or any KV page

This explains the apparent inconsistency that prompted the blocker: a shell should
be thin (43 lines) and a KV page should not (612 lines, 18 modules). Neither links
to the other because they were never alternatives.

**A KV tab is a UI, not an embedded browser page.** It is a rendering of whichever
KV the user is admitted to. The KV's capabilities live within that tab.

**Chrome vs tab.** The shell holds capabilities common to all KVs — StegMusic /
StegDJ, StegOS/Node status, security posture. The tab body holds the KV.

Test for placement: **does it survive switching from MyKV to OrgKV?** Survives →
chrome. Does not → tab. StegMusic must survive without remount, so the chrome
persists while the tab body swaps.

## 2. Isolation is a property of admitted state, not of the browser

MyKV and OrgKV must not share data without explicit user consent. Because a KV tab
is a UI over admitted state rather than an embedded document, isolation is not a
browser concern:

- Page separation would not isolate — same-origin documents share storage and DOM.
- Origin separation or iframe sandboxing would isolate, but would make the boundary
  a **browser-local** guarantee, which WU1 forbids.

Therefore cross-context sharing is itself an admitted transition, and the shell
holds no capability to move data between tabs.

Three state scopes follow: **principal-level** (chrome), **KV-level** (tab body),
**cross-KV** (admitted transition only).

## 3. Capabilities as admitted state — drift-proof by construction

MyKV has two hosts: the standalone entry point and the WorkSpace tab. Two
implementations would drift.

State-dependence of *data* alone does not prevent this — two renderers over
identical data can still disagree on what they show, which record variants they
handle, and which write paths they offer.

What does prevent it: **capability functions bound to admitted operations**, which
the registered goal already requires. If capabilities are admitted state rather
than code, the renderer is generic, MyKV/OrgKV/Company-Employee-KV differ as data,
and there is one interpretation to drift from.

Residual: an unknown record shape must **fail closed and visibly**. Silent omission
is drift that cannot be seen, which is worse than drift that errors.

## 4. Transfer model

**Egress and ingress are two events, not one event recorded twice.** "Released
custody" and "accepted custody" have different predecessors, successors and
authorities. Each endpoint describes its own transition in its own system's terms.

What crosses the seam is a **pointer, not a description**. The sending side records
the capability to trace to the opposite end; after handoff the record belongs to
the receiving system and is described according to that system — StegVerse or
external framework alike.

**Interlock/InTr is a one-way path.** There is no response on the same channel. The
manifest names the next destination, even when that is back to the originating Org.
The acknowledgement is the next leg. A round trip is two one-way transfers.

Consequence: an ephemeral StegOS/Node that dies mid-journey produces a **detectable
incomplete journey** (leg 2 declared, never arrived), not an unresolvable seam.

**Receipts append the manifest, drop off locally for recording, and continue.** The
manifest carries its own running trace while each endpoint keeps a local copy.

**Org to Org:** each Org records the handoff; the packet continues; Master Records
records the same Org-to-Org communication.

**External framework requirement:** ingest the manifest and emit a conforming
return manifest. That is the whole integration surface — smaller than REST, gRPC
or broker integration in *format*, though the behavioural requirement (append a
receipt, record locally, construct the return manifest) is the real cost.

## 5. Manifest vs receipt — where transfer semantics live

The ingress manifest already declares the transfer, in closed schemas:

| Concern | Field |
| --- | --- |
| direction | `completion.direction` |
| counterparty | `source_framework` / `source_instance` / `source_output_id`; `completion.initiator` / `publisher` / `egress` |
| route | `processing.capability` + `processing.route_id` (`additionalProperties: false`) |
| payload identity | `payload_commitment` + `payload_commitment_profile` (`enum: ["sha256"]`) |
| expected return | `return_projection.mode` + `transition_classes` |

The manifest declares the **attempted transfer**; the receipt records **what
happened to it**. `transition_class` already carries the endpoint's own role.

`ECOSYSTEM_STATE_TRANSITION_DISPOSITION_INVARIANT.md` already requires the receipt
to carry the manifest ID/digest.

## 6. Gaps found in source

- **`stegverse.repo-transition-receipt/v1` has no manifest binding and no handoff
  reference.** Required fields are `repository, transition_id, transition_class,
  predecessor_state_sha256, successor_state_sha256, evidence, authority_effect,
  observed_at, previous_receipt_sha256`. Across all three ledger contract files
  there are zero occurrences of counterparty, direction, correlation, peer or
  endpoint. Two endpoints can each record a transition with nothing to match them.
- **`attestation` in `stegverse.ingress-manifest.v1` is `{}`** — an empty schema
  accepting anything, including nothing. **`freshness` is `{"type": "object"}`**,
  unconstrained. These are the fields that would bind the manifest against
  destination rewriting, receipt stripping or forgery, and replay.
- **The receipt ledger records scope (REPOSITORY → ORGANIZATION → master-records),
  not participants.** A KV is not a repository. Endpoint chains for KV, SKAP Vault
  and Node are a different axis and are not built.
- **The KV AI chain explicitly stops short of InTr admission.**
  `SV-KV-AI-PERSISTENCE-001` (IN_PROGRESS) makes KnowledgeVault the governed memory
  substrate for Personal Assistant AI, Organizational AI, StegVerse AI and machine
  agents, via **non-authorizing memory write proposals**.
  `SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001` proceeds *"without claiming
  Interlock/InTr admission, provider/model execution, KV writeback, or Master
  Records reconstruction."* Today the KV AI proposes; it does not transition.
- **Unrecorded dependency.** `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`
  references none of the five `SV-KV-AI-*` records. WorkSpace's write capability is
  gated on that chain reaching InTr admission.

## 7. Root cause named by the registry owner

Most partial implementations are frozen at the same point: **no successful round
trip through Interlock/InTr to an ephemeral StegOS/Node that demonstrates the
transport AND receipt recording by the initiating Org and then Master Records.**

Requirement stated: KV and SKAP Vault each maintain a recorded receipt chain
coinciding with all their events; InTr ingress and egress are each state
transitions recorded at each endpoint's receipt chain recorder.

Acceptance criterion this implies: not "transport happened and both sides
recorded," but **the handoff reference resolved in both directions before the
ephemeral end went away.**

## 8. VA / VACC — health PII methodology

VACC is the veterans' chat assisting with VA claims. Methodology as stated:

1. Documents are stripped of PII; claim docs are completed de-identified.
2. Submission uses the federal system's own identity (Login.gov / ID.me at
   VA.gov); documents are wrapped with the user ID **at that time**.
3. No part of StegVerse retains that PII outside the user's MyKV or preferred
   storage.

`docs/FEDERAL_HEALTH_PII_EXCEEDANCE_HARDENING_MIRROR_HANDOFF.md` already states the
posture precisely: technical enforcement *"intentionally exceeds the current
federal baseline"* while *"not itself assert[ing] HIPAA compliance, FedRAMP
authorization, FISMA authorization, or legal certification."*

### Open concerns

- **Claim narratives resist de-identification.** Unit, deployment window, MOS, the
  incident, a rare condition — any two may uniquely identify. Removing the 18 Safe
  Harbor identifiers is not sufficient, and Safe Harbor is itself a federal
  baseline rather than an exceedance of one.
- **Where the wrap executes decides the posture.** Client-side at submission means
  StegVerse never holds the identified artifact. Server-side means it does,
  transiently, and most of the benefit is lost.
- **MyKV as designated custodian makes WU1–WU3 custody guarantees.** WU1 is
  *Violated* (browser-local IndexedDB trust root). WU2 is *Absent* (no device
  recovery — a lost phone means a veteran cannot reach their own records). WU3 is
  *Absent* (re-registration mints a new Receipt #1, orphaning prior lineage).

### Live page delta

`https://stegverse.org/va-disability-claim-guide.html` instructs veterans to set
**Date range = All time** and **Types = All**, then upload to VA Claims Chat. That
is maximal collection with no de-identification step and no retention statement —
the inverse of the methodology above.

The page does gate correctly: upload only if an *active secure document-upload
control* is present, and it refuses to claim a VA.gov submission path it does not
have. **VA Claims Chat is informational only at time of writing** — no upload
capability, no end-to-end InTr, no dedicated chat — so this is a documentation
delta to close before capability exists, not live exposure.

Note the safety gate speaks to transport, not retention. A secure upload into a
system that retains identified PHI still retains identified PHI.

## 9. Still open

- **BLK2 residual:** do `stegos-apple-credential.html`, `stegfin-trade.html` and
  `generic-login-test.html` lose independent SKAP ingress?
- **Email admission:** is the confirmation link a **carrier** for an SKAP-admitted
  session, or a **verifier**? The goal forbids a second user verifier, so the first
  reading preserves it and the second requires the goal text to change.
- **BLK3, BLK4** — not yet answered.
- **Goal text:** the record says WorkSpace is "the canonical browser representation
  of MyKV and Org KV." Under §1 WorkSpace is the canonical *shell*; the KV pages are
  the canonical representations. Worth correcting when resolutions are applied.
- **Scope:** calendars, email, messaging, VoIP, StegPay, StegWallet, StegID,
  Genealogy Hub, Publisher, StegBrowser, StegOS are named capabilities far beyond
  WU1–WU5. COSV `U = 5` becomes wrong when they are registered.
