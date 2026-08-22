# StegVerse Test Lanes Autolaunch Mirror Handoff

Updated: 2026-08-22T07:03:00-05:00

## Current role

```text
goal_id: STEGVERSE-TEST-LANES-AUTOLAUNCH-001
repository: StegVerse-Labs/.github
role: OPTIONAL_AUTOMATION_ONLY
canonical_direct_execution: docs/STEGVERSE_TEST_LANES_DIRECT_RUN_MIRROR_HANDOFF.md
canonical_direct_runner: scripts/run_test_lanes_direct.py
primary_provider: stegverse_local
third_party_role: CONTROL_OR_FALLBACK_ONLY
credential_authority: TV/TVC
heartbeat_grants_execution_authority: false
heartbeat_required_for_test_execution: false
g18_required_for_test_execution: false
worker_coordinator_required_for_test_execution: false
```

The previous architecture incorrectly made the named canonical 9/9 experiment wait for heartbeat/G18/WorkerCoordinator product-activation predicates. That dependency is superseded for **test execution**.

The heartbeat-owned task remains installed as an optional automation path: if the carrier and WorkerCoordinator are available they may wake and run the same test. Their absence may not block a direct otherwise-admissible run.

## Canonical direct path

See `docs/STEGVERSE_TEST_LANES_DIRECT_RUN_MIRROR_HANDOFF.md`.

Direct execution requires only the experiment's own boundaries:

- current Test Lanes and TVC source trees;
- TVC vault-agent and vault-broker sockets;
- all four external provider credentials live READY through TV/TVC;
- exact canonical external models;
- a private StegVerse PRIMARY endpoint, either already live or launched as a bounded canonical test process;
- exact READY nine-lane plan;
- no credential material exported;
- five candidate executions -> nine sanitized lane records -> comparator PASS.

It does **not** require heartbeat state, G18, WorkerCoordinator state, same-execution product activation, or Master Records product-release proof before the experiment may run.

## Existing optional autolaunch surfaces

```text
handoffs/STEGVERSE-TEST-LANES-AUTOLAUNCH-001.json
control/worker-registry.d/test-lanes-autolaunch.json
control/process-worker-adapters.d/test-lanes-autolaunch.json
control/test-lanes-autolaunch-matrix.v1.json
workers/test_lanes_autolaunch_entrypoint.py
workers/test_lanes_autolaunch_worker.py
```

Those surfaces are retained for automation/backward compatibility. Their heartbeat-specific matrix does not define the direct-run release condition.

## Direct-run source

```text
25dd4c9b9babf51e41659cd1b30c91a6004b7811  initial direct runner
16a3ef8f8319f41a53d945f7c946a8773527908e  no-heartbeat regression tests
a72efb8ad45c2855792611db27dafe8a31129094  bounded canonical StegVerse PRIMARY bootstrap
6af983b789b4046a7d6727f60cbb131eaf11eafb  bounded-primary tests
0618ac96143324268f95e19a578ad769f10192b1  canonical direct-run handoff
```

## Canonical external model selection

Owned by TVC:

```text
OpenAI    gpt-5.6-sol
Anthropic claude-opus-5
DeepSeek  deepseek-v4-pro
Kimi      kimi-k3
```

## Current live boundary

```text
direct-run source: INSTALLED
bounded StegVerse test-primary bootstrap: INSTALLED
canonical model selection: INSTALLED
live TVC four-provider readiness: NOT DIRECTLY OBSERVED
live five-candidate execution: NOT OBSERVED
nine lane evidence records: NOT OBSERVED
comparison PASS: NOT OBSERVED
```

Therefore heartbeat/G18 remediation may continue independently, but the Test Lanes goal should now be advanced by invoking `scripts/run_test_lanes_direct.py` on a StegVerse-controlled runtime and acting only on its direct concrete blockers.

No source, task, handoff, READY status, optional autolaunch assignment, workflow pass, or heartbeat state satisfies the required runtime outcome.
