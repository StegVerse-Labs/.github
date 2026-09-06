# HB32 Runtime Issue Handling Rule

For any StegVerse resident-runtime issue whose symptom involves heartbeat progression, oscillator/carrier presence, WorkerCoordinator presence/freshness, resident request dispatch, or task-runtime absence:

1. resolve the canonical HB/oscillator and resident self-heal handoffs first;
2. query `data/runtime-solution-registry.d/hb32-existing-runtime-solutions.json` and reuse a matching existing solution before proposing implementation;
3. distinguish carrier presence, WorkerCoordinator presence, request consumption, task execution, claim/fence, and task completion as separate predicates;
4. do not create another heartbeat, oscillator, scheduler, WorkerCoordinator, resident runtime, hosted observer, or claim/fence plane merely because authentic runtime evidence is missing;
5. only create a successor repair when the existing solution has a specific evidenced gap, with README impact resolved by machine preflight before functional mutation.

This rule is coordination/discovery guidance. It grants no runtime or governance authority.
