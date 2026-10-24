# sv-push-receipt.v1: branch-writer evidence from the push itself

Authoring-Session: grok-lane-c

## Why

TVC#519 `BRANCH_WRITER_IS_BRANCH_OWNER` needs to know who wrote every commit between base and head.
The P4 path rebuilds that from the local reflog. A lost reflog entry (P4's f108ed0a range) leaves the
range FAIL_CLOSED `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`. **That ruling is final.** This component does not
reconstruct that range or any other past range. It only adds evidence for pushes made from now on.

## Pieces

| Piece | Path |
|---|---|
| Schema (closed, `additionalProperties: false`) | `schemas/sv-push-receipt.v1.schema.json` (`$id` `stegverse.sv_push_receipt.v1`) |
| Push-time producer | `resident-runtime/sv_push_receipt.py` |
| Tests | `tests/test_sv_push_receipt.py` |

The schema is modelled on P1's `sv-check-receipt.v1` (blob 070f13f4). It uses the same `hb_epoch` pattern
(ASCII digits, value >= 32), 40-hex shas, `sha256:` seals and a closed object.
Its fields are `schema, repository, ref, old_sha, new_sha, pusher_session, change_id (optional), pushed_commits[], hb_epoch, result_sha256`.

## Producer contract

1. **Before the push:** `sv_push_receipt.py read-ref --repository . --ref refs/remotes/origin/<branch>` gives `old_sha`.
   For a new branch, the pushing session names the fork base instead. It must be an ancestor of the pushed head.
2. **The push:** the session's own normal push. The producer never pushes.
3. **After the push:** `sv_push_receipt.py emit --repository . --repository-name OWNER/NAME --ref refs/heads/<branch> --after-ref refs/remotes/origin/<branch> --old-sha <old> --pusher-session <session> --hb-epoch <N> [--change-id svc:...] --out receipt.json`
   - reads `new_sha` from `--after-ref`;
   - requires `old_sha` to be an ancestor of `new_sha`. A non-fast-forward (force) push is refused, not receipted;
   - sets `pushed_commits` = `git rev-list --reverse --topo-order old_sha..new_sha`, which must end at `new_sha`;
   - seals `result_sha256` (sha256 over canonical JSON: sorted keys, `,`/`:` separators, UTF-8, with the seal field removed).

The producer has these guarantees:

- **Not reflog-based:** the tests run with `core.logAllRefUpdates=false`.
- **No clock:** `hb_epoch` is supplied, else FAIL_CLOSED `HB_EPOCH_NOT_SUPPLIED`.
- **No network.**
- **Read-only:** its only git verbs are `rev-parse`, `cat-file`, `merge-base` and `rev-list`. The only write is the `--out` receipt file.

A refusal is a sealed six-field FAIL_CLOSED result (`stegverse.sv-push-receipt-refusal/v1`, owning goal `StegVerse-org/.github#164`) and writes no file. The refusal codes are:

- `HB_EPOCH_NOT_SUPPLIED` / `HB_EPOCH_INVALID`
- `PUSH_RECEIPT_INPUT_INVALID`
- `PUSH_NOT_OBSERVED` (ref did not move, ref unreadable, old sha absent, commits not listable)
- `PUSH_NOT_FAST_FORWARD`

## Appending is not this component's job

A receipt becomes a ledger receipt only when the **org-ledger writer transition (StegVerse-Labs/.github#3255)**
appends it to `refs/stegverse/organization-ledger` under the shared lock. The producer never appends, never
dispatches the writer, and never touches that ref. The tests assert this.

## Consumer (TVC#519)

`BRANCH_WRITER_IS_BRANCH_OWNER` accepts a contiguous, sealed chain of these receipts:

- `receipts[0].old_sha == base`;
- each `new_sha` equals the next `old_sha`;
- the last `new_sha == head`;
- same repository and ref throughout.

Every `pusher_session` must be the declared session or hold a co-author grant.

- A gap or a broken chain gives FAIL_CLOSED `WRITER_EVIDENCE_GAP`.
- A foreign pusher gives FAIL_CLOSED `BRANCH_HAS_FOREIGN_WRITER`.

Push receipts are an additional, preferred source. The P4 writer-evidence path stays. TVC pins this schema by git blob and sha256 at this PR's head.

## Open

- No reusable-evidence component contract entry yet: RTC-014 is still on draft #3266, and the next id is unassigned.
- No live receipts exist yet. The first ones come from the first pushes made with this producer after it lands.
