# SDK Generic Manifest Task Registry Registration Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Canonical controlling handoff: `StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md`
Status: `ACTIVE / TASK REGISTRY REGISTRATION VALIDATION PENDING`

## Purpose

Register the already-existing ACTIVE SDK downstream-propagation goal in the canonical Task Registry introduced by `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001` before any further mutation of the resident refresh/dispatch bridge.

Fresh check-in against `data/canonical-task-records/` found this Goal Task ID absent. Under `scripts/evaluate_task_registry_collision_checkin.py`, absence deterministically returns `STOP_NOT_REGISTERED / END_OR_REGISTER_BEFORE_MUTATION`. Therefore this registration is the prerequisite reconciliation, not new runtime work.

## Registration contract

`data/canonical-task-records/SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003.json` binds:

- canonical Goal Task ID and parent `SDK-PROCESSOR-GENERIC-MANIFEST-002`;
- COSV vector `71000000100110`;
- the existing SDK root and Shared Docs WorkSpace handoffs;
- current repository/component mutation scope;
- remaining authentic resident/custody/callback/provider/lifecycle/publication predicates;
- `coordination_state=ACTIVE`;
- `checkout_state=UNCLAIMED` because this registration does not invent a WorkerCoordinator claim;
- TV/TVC credential authority, Interlock/InTr transition authority, Master Records reality authority, HB observability-only posture, GitHub runtime authority NONE, no hosted fallback, and no second user-operated device requirement.

## Collision boundary

This registration does not authorize the next source change. After merge, the canonical collision evaluator must be run again with the intended mutation context for `StegVerse-Labs/.github`, `resident-refresh-dispatch`, and the two SDK WorkSpace external-collaboration resident selectors. `CONTINUE` permits the current task to proceed. `COORDINATE_CONVERGENCE` requires reconciliation before mutation. `STOP_COLLISION`, `STOP_SUPERSEDED`, or `STOP_INACTIVE` ends this session's mutation lane in favor of the returned canonical owner.

## Discovered next source gap

The generic resident dispatcher already registers:

- `sdk_workspace_external_collab_client_secret_reseal`
- `sdk_workspace_external_collab_consent_listener`

and the sovereign source refresh carries `control/resident-execution-request.d/` wholesale. However, `scripts/refresh_and_dispatch_resident_requests.py` does not yet admit either selector in `ALLOWED_TARGET_CONSUMERS`, and its `NONSECRET_FORWARD` does not yet carry the listener's three required non-secret inputs. Therefore the portable current-device `refresh -> exact targeted dispatch` bridge cannot presently select these two merged consumers even though the lower-level dispatcher can.

No repair to that bridge is made in this registration PR. It must wait for the post-registration collision disposition.

## Validation

`tests/test_sdk_generic_manifest_task_registry_registration.py` validates canonical identity, lifecycle, COSV, authority separation, handoff linkage, resident-refresh-dispatch target declaration, unresolved runtime predicate retention, and absence of completion claims.

## README review

Root README already documents Task Registry resolution/deduplication/collision ordering and authority separation. This registration adds no public capability, runtime, credential path, or execution authority, so no README text change is required.

## Next sequence

1. validate and merge this registration;
2. execute/reconstruct the canonical collision check-in for the exact intended resident-refresh-dispatch mutation context;
3. obey the returned disposition before source mutation;
4. only on an admitted continuation, add the two selectors and exact non-secret forwarding to the existing portable bridge with regression coverage;
5. then observe authentic resident receipts without treating source/CI as runtime evidence.

## Human action

None.
