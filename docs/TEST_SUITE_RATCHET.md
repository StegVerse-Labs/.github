# Test suite ratchet

Every other workflow in this repository is path-filtered to an explicit file
list, so a test that no workflow names is never run by CI. When this was added
that was **562 of 662 test files**. The tests existed, passed locally, and
protected nothing.

That is the honest explanation for a cross-repository seam break shipping with
both repositories green: the SDK began emitting a `journey/v2` while the
StegBrowser owner accepted `journey/v1` only, and no CI job on either side ran
the tests that would have noticed.

## What it does

Runs the whole suite on every pull request, with no path filter, and compares
the **set** of failing tests against `data/test-suite-baseline.json`.

A set, not a count. A change that breaks one test while another is fixed leaves
the count unchanged, which is exactly the regression a count would miss.

- a failing test not in the baseline → **red**, named
- a baseline test that now passes → reported as `NEWLY_PASSING`, **not** a
  failure, so the baseline can be tightened deliberately rather than drifting
- an excluded test → ignored in both directions

Failures are also emitted as Healer-intake findings through the existing
`scripts/registry_gate_findings.py`, so a red gate reaches the repair path as
structured input rather than as English in a log.

## The baseline is a ceiling, not an endorsement

It records the failures that already exist on main. Nothing here requires them
to be fixed and nothing stops the ceiling being lowered as they are. What it
forbids is adding to them.

## Exclusions name their reason

One test is excluded today:
`test_canonical_master_records_local_adapter_repair.py::…::test_calls_existing_state_transition_authority_without_schema_relabel`.

It is not flaky. It is **environment-sensitive**: it fails when the suite runs
from a git worktree and passes from a primary checkout — 114 against 113 on the
same commit. Since CI's checkout is neither exactly, the gate is made correct
under both by watching neither direction for this test. The exclusion carries
that reason and the repair: make the test independent of checkout shape, then
remove the exclusion.

An exclusion is never a silent retry. It is recorded where a reviewer sees it.

## Verified before merge

| case | result |
|---|---|
| primary checkout (113 failing) | green, `new=0` |
| git worktree (114 failing) | green, `new=0` — the exclusion holds |
| injected new failure | **red**, exit 1, names the test, one Healer finding |
| baseline entry that now passes | green, reported `NEWLY_PASSING` |

## Regenerating

`python scripts/check_test_suite_ratchet.py --write-baseline` rewrites the
known-failing set and preserves exclusions with their reasons. Do it in the same
change that causes the movement, so the diff shows what moved and why.

## Boundary

Source validation only. It mints no receipt, confers no admission, observes no
runtime and grants no authority.
