# HB29 Reconciliation Validation Contract

Task: `HEARTBEAT-HB29-CURRENT-MAIN-RECONCILE-197`

This file records the exact source-level validation obligations for the current-main reconciliation branch. It does not claim live runtime activation.

Required deterministic checks:

- `python -m unittest tests.test_heartbeat_engine_v12_cutover`
- `python -m unittest tests.test_worker_runtime_separation`
- `python -m unittest tests.test_sovereign_heartbeat_service`
- `python -m unittest tests.test_sovereign_runtime_activation_v12`
- `python -m unittest tests.test_heartbeat_carrier_non_authority`

Required invariants:

- retained `control/heartbeat-state.json` remains immutable HB29 provenance;
- the separated carrier starts its first persistent successor at HB30;
- the carrier grants no claim, lease, fence, activation or execution authority;
- worker/control-plane state consumes carrier references without advancing them;
- worker assignment timers advance on worker-runtime ticks, not carrier epochs or carrier presence;
- the carried assignment packet transitions into the Master Records bound assignment record when an independently authorized worker assignment occurs;
- the sovereign installer materializes carrier v12 and the worker coordinator as distinct locally supervised StegVerse processes;
- the node-local activation verifier reads separated carrier/control-plane state and retains all nine activation predicates;
- credential authority remains TV/TVC, credential requirement is NONE, no NON-TV/TVC secret/token path is introduced;
- GitHub Actions may validate source but is never production runtime authority;
- Render and other third-party process hosts are prohibited as production authority.

Live activation remains owned by `.github#122/#12` and requires node-local evidence. CI success alone is not activation evidence.
