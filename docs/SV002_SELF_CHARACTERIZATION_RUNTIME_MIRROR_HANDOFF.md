# SV002 Self-Characterization Runtime Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issues: #484, #490
Branch: main

## Source of truth

This file is the current handoff and task source of truth for the resident StegVerse-002 self-characterization execution preflight.

## Canonical experiment owner

```text
experiment: STEGVERSE-002-SELF-CHARACTERIZATION-001
principal contract: StegVerse-002/micro-node-runtime/experiments/self-characterization-001/EXPERIMENT_CONTRACT.v0.1.json
resident task: SHWP-SV002-SELF-CHARACTERIZATION-001
credential authority: TV/TVC
github token runtime authority: NONE
hosted runtime: FORBIDDEN
reference model as principal: FORBIDDEN
model output authority: NONE
```

The experiment may run only against an authentic, locally running, non-reference reasoning subject whose endpoint, model identity, process identity, runtime executable digest, and model digest can be independently verified.

## Current gap

The resident worker already detects:

- locally materialized StegVerse-002 runtime source;
- the exact pinned TT / RTG / GTG / AE commits;
- a configured loopback model endpoint and model ID.

The canonical principal runner additionally requires a `stegverse.self-characterization-runtime-identity/v0.1` descriptor in `STEGVERSE_SELF_CHAR_SUBJECT_IDENTITY_JSON`.

Before issue #484, the worker never constructed or supplied that descriptor. Therefore a qualifying resident model endpoint could be observed but execution would still fail before S0 because subject identity was not bound.

## Merged source closure

```text
subject-identity preflight:
  issue: #484 CLOSED
  PR: #488
  merge: b72af52be222772a57f2f5cfb94578676b68a6bd
  organization validation: SUCCESS
  Heartbeat Worker Project deterministic suite: SUCCESS

resident retry semantics:
  issue: #490 CLOSED
  PR: #491
  merge: e85c9c94ed1af9020bbd55d79216dec8768355f2
  organization validation: SUCCESS
  Heartbeat Worker Project deterministic suite: SUCCESS
```

Scoped source is now complete: a qualifying local Ollama subject can be independently bound to exact model/process/executable evidence, and nonterminal resident attempts remain retryable without permitting duplicate successful principal execution.

## Bounded repair scope

Issue #484 may add only a credential-free local subject-identity preflight for an already-running Ollama-compatible principal runtime.

Required evidence:

```text
loopback/private endpoint
non-reference model ID
/api/tags locally reports exact model digest
local Ollama runtime process observed
process executable path observed
runtime executable SHA-256 observed
process executable matches runtime executable
model digest normalized to SHA-256
identity descriptor bound to exact endpoint/model
```

The worker must fail closed if any required evidence is absent or contradictory.

The repair must not:

- fetch or install a model;
- start a hosted runtime;
- infer a process identity;
- synthesize a model digest;
- accept the StegVerse reference model;
- relax pinned formal-resource commits;
- claim private chain-of-thought;
- grant execution or governance authority to model output.

## Files

- `workers/sv002_self_characterization_worker.py`
- `tests/test_sv002_self_characterization_worker.py`
- `docs/SV002_SELF_CHARACTERIZATION_RUNTIME_MIRROR_HANDOFF.md`


## Resident retry semantics

Issue #490 closes a machine-execution liveness defect in the resident request consumer.

Before this repair, any prior attempt for the same request hash was treated as permanently consumed, even when the worker remained `BLOCKED` because a required local endpoint, pinned formal root, or subject-identity proof was not yet available.

The corrected contract is:

```text
BLOCKED / nonterminal attempt -> ATTEMPT_RECORDED -> retry allowed
COMPLETED principal execution -> terminal_execution_observed=true
same request hash after terminal success -> ALREADY_CONSUMED
duplicate successful principal execution -> prohibited
```

This preserves exactly-once completion while allowing bounded machine retries as dependencies become locally observable.

## Remaining machine-execution gates

After merged source repair:

1. resident source refresh observes the merged worker;
2. the resident request is consumed;
3. exact pinned formal roots are locally present;
4. a qualifying non-reference local reasoning runtime is already running;
5. subject identity preflight passes;
6. principal execution emits `EXPERIMENT_EXECUTION_RECEIPT.json` with `state=COMPLETED`;
7. human-readable, formal, and interaction-receipt artifacts are retained;
8. Master Records reconstruction remains a separate downstream evidence gate.

## Integration destinations

- resident execution/control: StegVerse-Labs/.github
- principal experiment source/artifacts: StegVerse-002/micro-node-runtime
- TT / RTG / GTG / AE evidence: Admissible-Existence repositories
- custody/reconstruction: master-records/orchestration
- public observation projection after authentic evidence: StegVerse-Labs/.github -> StegVerse-org/LLM-adapter -> StegVerse-Labs/Site

Source completion is not experiment completion.


## Current observed state

```text
resident request: REQUESTED
subject-identity preflight source: MERGED / VALIDATED
blocked-attempt retry semantics: MERGED / VALIDATED
known scoped scaffolding/stubs: 0
qualifying non-reference resident reasoning endpoint: NOT OBSERVED
verified resident subject identity: NOT OBSERVED
principal self-characterization execution: NOT OBSERVED
human/formal/interaction artifacts: NOT OBSERVED
Master Records reconstruction: NOT OBSERVED
user action required: false
```

The next lawful transition is machine-owned resident execution. Repository source, validation, or merge cannot satisfy the experiment.
