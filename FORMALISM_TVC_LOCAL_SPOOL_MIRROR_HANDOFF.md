# Formalism TVC Local Spool Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/formalism-tvc-local-spool-001
goal_id: FORMALISM-TVC-LOCAL-SPOOL-001
parent_goal: FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001
credential_authority: TV/TVC
consumer_secret_or_token_authority: NONE
github_token_required: false
archive_ready: false
```

## Originating requirement

The formalism transport consumer is now merged and can generate bounded non-secret repository-operation request envelopes, but its process adapter deliberately runs inside a temporary repository copy and projects only admitted repository-path deltas. The TVC-governed local runtime therefore has no proven credential-free machine channel through which to receive those requests and return sanitized receipts.

This goal installs a bounded local state-spool capability owned by the heartbeat adapter. The worker never receives the authoritative spool path. It receives a sandbox-local mirror, and the adapter alone validates and atomically projects admitted spool deltas to the configured local continuity root.

## Transport topology

```text
formalism heartbeat worker
  -> sandbox-local bound-state/outbox/*.json
  -> heartbeat adapter validates fenced claim + spool path scope
  -> ~/.stegverse/transport/formalism-tvc-repository/outbox/*.json
  -> TV/TVC local repository-operation intake
  -> ~/.stegverse/transport/formalism-tvc-repository/inbox/*.json
  -> heartbeat adapter mirrors inbox into next worker sandbox
  -> consumer reconciles receipt and advances successor state
```

No GitHub synchronization or GitHub credential is required for this local carrier path.

## Security invariants

The adapter must:

```text
never expose the authoritative external state-root path to the worker
copy external state into a sandbox-local bound-state directory before execution
exclude the sandbox-local bound-state directory from repository mutation accounting
compute a separate before/after state-root delta
permit only explicitly configured relative spool paths
require the same current claim/fencing token as repository mutation
atomically project allowed files only after both repository and spool deltas pass
reject path traversal, symlinks, directories-as-files, and out-of-scope deletion/mutation
persist a mutation-scope receipt identifying repository and external-state decisions
never forward GITHUB_TOKEN, GH_TOKEN, PAT, provider, wallet, or TVC credential values
```

The external state root is continuity state, not repository authority. Spool contents create no mathematical, execution, credential, merge, provider, wallet, signing, broadcast, release, or settlement authority.

## Initial owner

The first consumer is `FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001`. Its allowed external paths are limited to:

```text
outbox/**
inbox/**
processed/**
```

The TVC side may read outbox and write sanitized inbox receipts only under its separate TV/TVC-owned local task. `.github` never receives a credential.

## Required implementation surfaces

```text
heartbeat_runtime/process_adapter.py
scripts/run_heartbeat_runtime.py
control/process-worker-adapters.d/formalism-tvc-repository-transport-consumers-001.json
workers/formalism_tvc_repository_transport_worker.py
tests/test_process_worker_adapter.py or equivalent bounded-state tests
tests/test_formalism_tvc_repository_transport_worker.py
control/session-implementation-claim-2026-08-14-formalism-tvc-local-spool.json
```

## Validation

Required proof:

```text
worker cannot discover authoritative external root
in-scope outbox write persists atomically to external state root
inbox state is available in a subsequent sandbox invocation
out-of-scope external write is denied and not projected
repository out-of-scope mutation still fails closed
claim/fence mismatch still fails closed
no credential environment variable is forwarded
existing process_json_v0.1 workers remain backward-compatible
full repository deterministic suite passes
heartbeat dry-run remains non-persistent
```

## Cross-repository continuation

After this adapter is validated and admitted, `StegVerse-Labs/TVC` must install the complementary local intake task for the same continuity state root. That task remains TV/TVC-owned and is the only component permitted to resolve `TVC_EPHEMERAL_GITHUB_TOKEN` for live repository transport.

## Archive condition

Do not archive the originating session while the bounded spool adapter or TVC intake side is missing/unvalidated, while TVC PR #20 is not validated/canonical, or while an emitted formalism request still requires a chat session to move from `.github` into TVC and back.