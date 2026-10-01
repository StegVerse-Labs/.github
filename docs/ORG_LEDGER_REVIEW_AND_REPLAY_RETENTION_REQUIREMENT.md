# Organization ledger review and tiered replay/reconstruction retention requirement

Source review and requirement capture. Written 2026-10-01 for near-term resolution.

## Claims boundary

This document mints no authority. It registers no canonical task, derives no COSV,
observes no runtime, and claims no adoption, conformance or deployment. No
`worker_claim` is asserted here: where no authentic WorkerCoordinator claim or
fence has been observed, the canonical projection remains
`authority: WORKERCOORDINATOR`, `claim_ref: null`, `fence_ref: null`,
`projection_only: true`.

Coordination state: **PROPOSED / UNCLAIMED**. COSV: **pending canonical derivation**;
this source document does not mint one.

Part A reviews source in `StegVerse-org/.github`, which cannot be written from a
session scoped to `StegVerse-Labs`. It is recorded here because this repository is
the ecosystem coordination surface. **It should be mirrored into
`StegVerse-org/.github` by an owner who can write there.**

---

## Part A — `StegVerse-org/.github` organization ledger review

Reviewed at `ef34106` (last commit 2026-09-27, PR #12
`fix/org-ledger-serialized-atomic-append-20260927`; only `main` exists, no
in-flight branches). Subject:
`resident-runtime/aggregate_repo_transition.py`, 176 lines, 9 functions.

Gated in CI by `.github/workflows/org-runtime-boundary.yml`, which path-filters on
both the implementation and `tests/test_org_ledger_atomic_append.py` and runs it on
`push` and `pull_request` via `unittest discover`. Its 3 tests pass.

### What is sound

- The chain is cryptographically linked: `previous_receipt_sha256` sits inside the
  hashed body, so the chain is tamper-evident.
- Durability is correct: same-directory `mkstemp` → `fsync` → `os.replace` →
  directory `fsync`. This is **more careful than the StegVerse-Labs counterpart**,
  which has no `_sync_directory`.
- `flock(LOCK_EX)` brackets the HEAD read, receipt creation and HEAD publication;
  the concurrency test demonstrates serialization.
- The recovery predicates take the right posture — `ORG_LEDGER_HEAD_MISSING_WITH_EXISTING_RECEIPTS`,
  `ORG_LEDGER_UNPUBLISHED_OR_ORPHAN_RECEIPTS_RECOVERY_REQUIRED`,
  `ORG_LEDGER_PREDECESSOR_CYCLE` — refusing to silently fork or reset the chain.
- Receipt schema is `stegverse.organization-transition-receipt/v1`, matching
  StegVerse-Labs. This is the interop-critical property and it holds.

### A1 — Malformed repo receipts bypass the structured fail-closed path

`append()` constructs `body` using `repo_receipt["repository"]` (line 133) and
`repo_receipt["transition_id"]` (line 135), but calls `verify_repo(repo_receipt)`
at line 134 — inside the same dict literal. Literals evaluate in order, so line 133
runs before the verifier.

Observed: a receipt missing `repository` raises `KeyError: 'repository'` instead of
`SystemExit("repo outside organization")`.

Not a corruption defect — it occurs before any write, and `flock` releases on
context exit. It is a contract defect: a module built on named fail-closed
predicates emits a traceback for malformed input.

**Repair:** call `verify_repo` before constructing `body`.

### A2 — `boundary_evidence` is recorded but never verified

StegVerse-Labs' `verify_required_evidence` requires a `required_evidence_manifest`
list and, per entry, `evidence_id`, `evidence_type`, `origin_transition_id`,
`encoding`, `sha256`, `content`; enforces unique `evidence_id`; binds
`origin_transition_id` to the receipt's `transition_id`; decodes `canonical-json`,
`utf-8` or `base64`; and verifies the SHA-256 of the decoded bytes.

StegVerse-org has none of this. `boundary_evidence` is an arbitrary dict stored
verbatim into the hashed body, CLI-defaulted to `{}`. The repository's own test
appends with `{}` / `"NONE"` and passes.

Consequence: a receipt is tamper-evident **after** the fact, but nothing establishes
the evidence was authentic **at** append time. This is the property that
`organization_receipt_observed` flipping true is meant to carry, so A2 — not the
append mechanics — is the gap that gates the SDK dependency.

**This is the highest-priority item in this document.** See C5.

### A3 — `_sha256` state fields accept non-digests

`predecessor_org_state_sha256` and `successor_org_state_sha256` pass straight
through (lines 137–138) with no format validation; `main()` accepts them as bare
required strings. The repository's own test writes `"state-before"` /
`"state-after"` into them. Chain validation does not catch this, because it
validates only `previous_receipt_sha256`.

**Repair:** require `sha256:` + 64 hex, the shape `_validate_existing_head`
already enforces for the head at line 85.

### A4 — Append cost grows linearly with ledger length

`_validate_existing_head` walks the whole chain to genesis on every append
(lines 97–111), re-loading and re-hashing every receipt, then globs the receipt
directory and set-compares (lines 112–114).

Measured, 300 sequential appends into a fresh ledger:

| appends | mean per append |
| --- | --- |
| #1–25 | 3.19 ms |
| #126–150 | 7.05 ms |
| #276–300 | 12.87 ms |

4.0x over 300 appends; slope ≈ 0.035 ms per existing receipt. Projected ≈ 355 ms
per append at 10,000 receipts and ≈ 3.5 s at 100,000. Total ledger cost is
quadratic.

This reads as deliberate — it is a strong integrity check and it is what catches
the orphan case the test covers. It is recorded as a decision, not a defect. It
becomes blocking under Part B; see C1.

---

## Part B — Requirement: tiered replay and reconstruction retention

Captured from the owner, 2026-10-01, in their terms:

> Replay and Reconstruction need to be determined by account or tier. The higher the
> account or tier status (and more costly) the longer the records remain replayable
> and reconstructable.

> Otherwise, replay and reconstruction incur per use fees once they're archived or
> merkled.

So the model is **not deletion**. Records pass from a tier-length included window
into an archived or Merkle-committed state in which they remain replayable and
reconstructable on a per-use fee basis. Nothing is destroyed; the cost basis
changes.

### Existing vocabulary: what to reuse, and what must not be reused

**Retention must not reuse the existing expiry vocabulary.** In this repository
`expiry` is exclusively worker and credential lease/fence lifetime:

- `expiry_basis` is a **required field of `heartbeat_timing`** in
  `schemas/worker-registry.schema.json`, sitting beside `fencing_token`,
  `expiry_epoch`, `transition_sequence` and `max_missing_response_beats`. Its enum
  is `STATIC_BOOTSTRAP`, `TASK_CLASS_COST_BASIS`, `OBSERVED_TRANSITION_COST_BASIS`,
  `HUMAN_AUTHORITY`, `NONE`.
- `lease` carries `issued_at`, `expires_at`, `heartbeat_due_at`,
  `handoff_grace_expires_at`, `fencing_token`, `renewal_allowed`, `max_renewals`.
- `claim_expires_at` and `block_expires_at` are claim/fence fields.
- Every occurrence of `expiry_basis` sits in worker, heartbeat, lease or
  credential source: `control/worker-registry.json`, `control/heartbeat-*.json`,
  `heartbeat_runtime/engine_v9.py`, `cost-basis/worker-runtime/`, and their tests.
- **`wall_clock_expiry_authority` is `false` in all 16 occurrences.** Wall clock is
  explicitly not the authority for expiry here.

These are two different mechanisms and must not share a field family:

| | lease expiry | records retention |
| --- | --- | --- |
| purpose | liveness — a hold lapses so another worker can take over | durability and cost basis |
| measured in | heartbeat epochs and beats | wall clock |
| wall-clock authority | explicitly `false` | inherently wall clock |
| on elapse | the hold is released | nothing is released; cost basis changes |

`TASK_CLASS_COST_BASIS` is the cost basis for a **worker lease duration**, not
evidence that record retention is already cost-derived. Retention needs its own
basis.

**Recommendation:** name retention fields so they cannot be confused with lease
expiry — e.g. `retention_class`, `replayable_until`, `reconstructable_until`,
`retention_basis` — and avoid the `expiry_*` family entirely.

**Safe to reuse:** `run` / `replay` / `reconstruct` already exist as distinct
operations — the SDK CLI exposes them as `--fallback-operation` choices.
- **No tier, account, subscription, billing or metering vocabulary exists in this
  repository today.** `cost-basis/` contains only `worker-runtime`. This is new
  vocabulary and should be named deliberately.
- Nearest existing owner, for collision review rather than assumption:
  `GOVERNANCE-METERED-POLICY-RECOVERY-001`, COSV `10100000124000`,
  `PROPOSED / UNCLAIMED`, 4 blockers. Its scope is provider-neutral policy/cost
  contract recovery; it does **not** mention replay, reconstruction, tier or
  archive. Whether this requirement is a child of it or a sibling is an owner
  decision — see the open questions.

---

## Part C — Design consequences that must be resolved

### C1 — The current validator forbids archiving or merkling

`_validate_existing_head` requires every receipt **body** to be present on disk
forever. It loads each one while walking to genesis (lines 103–110) and then asserts
`stored == reachable` against a directory glob (lines 112–114). Any archival or
Merkle compaction that removes bodies from `receipts/` makes those sets differ and
raises `ORG_LEDGER_UNPUBLISHED_OR_ORPHAN_RECEIPTS_RECOVERY_REQUIRED` — permanently,
fail-closed.

Merkling is precisely what this function currently forbids. It cannot be added
without changing it.

The same code is the A4 cost. **One change resolves both:** validate back to the
nearest Merkle anchor, and treat an anchored prefix as reachable-by-commitment
rather than requiring its files. The full walk then belongs behind an explicit
`--verify-full` or recovery entrypoint.

### C2 — Two clocks, not one

- The **included window** should be bound at write time, into the receipt, and be
  immutable thereafter. Otherwise a tier downgrade retroactively shortens evidence
  already paid for, which makes downgrade an evidence-deletion lever.
- The **per-use fee** is assessed at use time against the account's then-current
  tier.

These are different fields under different authorities and should not be collapsed.

### C3 — Replay and reconstruction need separate horizons

Reconstruction needs the chain and state commitments. Replay additionally needs
inputs and evidence, so it is heavier and should leave the included window first.
Tier buys the length of each horizon independently.

### C4 — A metered replay is a disclosure and must be receipted

The governance chain already models disclosure as a receipted stage —
`disclosure_projection` with receipt class `projection-decision`. A paid replay or
reconstruction is a disclosure event and should emit its own receipt binding
requester, tier, fee basis, and exactly what was served. Without this, the exposure
record is incomplete precisely where money changes hands.

### C5 — A2 must be fixed before merkling ships

A Merkle root attests that bytes are what was written. It does not attest that they
were authentic. Merkle-committing an unverified `boundary_evidence` blob
permanently commits unverifiable evidence — and then charges per use for access to
it. **Sequence A2 before any archival or Merkle work.** This is the strongest
ordering constraint in this document.

### C6 — Chain anchors should be permanent at every tier

Anchors are small, and the chain's verifiability is an ecosystem invariant rather
than a paid feature. Tier should buy the bodies' included window and waive the
per-use fee. It should never buy the chain's integrity.

### C7 — Tier must not become a device or platform gate

The governing ecosystem invariant is that anyone on any device can use every part
of StegVerse. A lower tier must remain fully usable from any device, with a shorter
included window — never with a narrower set of supported devices, platforms or
surfaces.

---

## Open questions for the owner

1. Is this requirement a child of `GOVERNANCE-METERED-POLICY-RECOVERY-001`, or a
   sibling with its own canonical task? That vector is `UNCLAIMED` with 4 blockers
   and does not cover replay or retention.
2. Is retention keyed to **account** identity or **subscription tier**, and what
   happens to an already-written receipt's included window on downgrade? C2
   recommends write-time binding; the decision is the owner's.
3. Is there a minimum retention floor at every tier for governance or regulatory
   reasons, independent of what tier is purchased?
4. What is the retention basis field called, and what are its values? It must be
   separate from `expiry_basis`, which is worker/credential lease lifetime under
   heartbeat authority with `wall_clock_expiry_authority: false` — see Part B.

## Suggested sequence

1. **A1 and A3** — small, local repairs to `aggregate_repo_transition.py`.
2. **A2** — evidence verification parity with StegVerse-Labs. Gates both the SDK
   `organization_receipt_observed` dependency and, per C5, all archival work.
3. **C1** — anchor-bounded validation, which also resolves A4.
4. **Part B** — tiered retention and per-use metering, once 1–3 hold.
