# Site Publication Source Refresh Scheduler Materialization Note

Goal Task: `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`
COSV: `50000000102000`

The neutral reusable scheduler is canonical, and Healer is only a consumer/carrier. The source-refresh trajectory exposed one materialization gap: the canonical sovereign source refresh copied the reusable-task trigger and registry shards but did not include `scripts/run_reusable_task_scheduler.py` or `data/reusable-task-scheduler-contract.json` in the resident static source set.

`RT-SOVEREIGN-SOURCE-REFRESH-001` therefore uses `scripts/refresh_sovereign_worker_runtime_source_reusable.py`, a thin adapter that extends the existing proven local-only refresh static set with the neutral scheduler runner/contract and then delegates to the same canonical `refresh()` implementation. It creates no second refresher, scheduler, source transport, credential route, runtime owner, claim/fence authority, or transition authority.

This is source repair only. It does not promote `SOVEREIGN_SOURCE_REFRESH_OBSERVED` or any downstream Site runtime/publication predicate. Authentic evidence still requires the resident reusable invocation receipt.
