# Legacy Continuity Validation Worker Source Test Note

This branch adds public control-plane regression coverage for `workers/legacy_continuity_validation_worker.py` only.

The test validates fail-closed behavior for missing source, wrong exact HEAD, dirty worktree, focused-test failure, credential stripping, four-test coverage including the frozen simulation, and explicit non-authority fields.

It does not access the private Continuity repository, execute the private-source validation worker against a real checkout, determine a death, notify a recipient, arm an authentic capsule, create authentic TVC authorization, or move StegCoin/StegToken.

Hosted CI for this branch is validation-only and grants no runtime, credential, release, or consequence authority.
