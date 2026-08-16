# HB29 Reconciliation Rebase Requirement

PR #199 diverged from current `main` while active development added coherent-signal-space carrier and formal-candidate worker support. Do not merge or force-update #199 over those changes.

Required continuation:

1. create a fresh current-main reconciliation branch;
2. replay the bounded #197 changes while preserving current `heartbeat_runtime/signal_space.py`, coherent-signal-space worker/registry/adapter/cost-basis/handoff artifacts, and current adapter validation;
3. validate the complete repository suite on the fresh branch;
4. supersede #199 and #198 only after the replacement validates and merges.

Authority remains unchanged: TV/TVC only for credentials; no NON-TV/TVC secrets/tokens; no Render or GitHub production runtime authority; live HB29 and claims/fences/leases remain resident-owner state.
