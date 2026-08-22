from copy import deepcopy

from state_language import (
    build_alignment_packet,
    canonical_hash,
    derive_delta,
    normalize_vector,
    preclaim_revalidate,
    reconcile_tasks,
)


def vector(**values):
    dimensions = {
        name: {"type": "enum" if isinstance(value, str) else "boolean", "value": value, "criticality": "HIGH"}
        for name, value in values.items()
    }
    return {
        "schema": "stegverse.semantic-state-vector/v1",
        "subject": "module:test",
        "resolution": "execution",
        "revision": 1,
        "source_ref": "docs/TEST_MIRROR_HANDOFF.md",
        "dimensions": dimensions,
        "evidence_refs": ["receipt:test"],
        "authority": {"effect": "NONE", "domain": "TEST"},
    }


def test_canonical_hash_is_order_independent():
    a = vector(runtime="ACTIVE", aligned=True)
    b = deepcopy(a)
    b["dimensions"] = {"aligned": b["dimensions"]["aligned"], "runtime": b["dimensions"]["runtime"]}
    assert canonical_hash(normalize_vector(a)) == canonical_hash(normalize_vector(b))


def test_metadata_only_change_does_not_create_semantic_delta():
    before = vector(runtime="ACTIVE")
    after = deepcopy(before)
    after["revision"] = 2
    after["source_ref"] = "docs/RENAMED_EXPLANATION.md"
    delta = derive_delta(before, after, affected_scopes=["module:test"])
    assert delta["changes"] == {}


def test_dimension_change_is_explicit_delta():
    before = vector(runtime="BLOCKED")
    after = vector(runtime="ACTIVE")
    delta = derive_delta(before, after, affected_scopes=["module:test"])
    assert delta["changes"]["runtime"]["before"]["value"] == "BLOCKED"
    assert delta["changes"]["runtime"]["after"]["value"] == "ACTIVE"


def test_reconciliation_creates_amends_and_supersedes_without_deletion():
    state = vector(runtime="ACTIVE")
    state_hash = canonical_hash(normalize_vector(state))
    registry = {
        "tasks": [
            {"task_id": "old", "state": "HANDOFF_READY", "goal": "obsolete", "authority": {"domain": "TEST", "ceiling_ref": "A"}},
            {"task_id": "keep", "state": "HANDOFF_READY", "goal": "old wording", "authority": {"domain": "TEST", "ceiling_ref": "A"}},
        ]
    }
    desired = [
        {"task_id": "keep", "state": "HANDOFF_READY", "goal": "new wording", "authority": {"domain": "TEST", "ceiling_ref": "A"}},
        {"task_id": "new", "state": "HANDOFF_READY", "goal": "new work", "authority": {"domain": "TEST", "ceiling_ref": "A"}},
    ]
    reconciled, effects = reconcile_tasks(
        registry,
        desired,
        source_state_hash=state_hash,
        source_handoff_ref="docs/TEST_MIRROR_HANDOFF.md",
    )
    by_id = {task["task_id"]: task for task in reconciled["tasks"]}
    assert by_id["old"]["state"] == "SUPERSEDED"
    assert by_id["keep"]["goal"] == "new wording"
    assert by_id["keep"]["reconciliation_disposition"] == "AMENDED"
    assert by_id["keep"]["history"][-1]["task_semantics"]["goal"] == "old wording"
    assert by_id["new"]["state"] == "HANDOFF_READY"
    assert {effect["disposition"] for effect in effects} == {"SUPERSEDED", "AMENDED", "CREATED"}


def test_reapplying_same_projection_does_not_advance_generation():
    state = vector(runtime="ACTIVE")
    state_hash = canonical_hash(normalize_vector(state))
    desired = [{"task_id": "t", "state": "HANDOFF_READY", "goal": "same", "authority": {"domain": "TEST", "ceiling_ref": "A"}}]
    first, first_effects = reconcile_tasks({"tasks": []}, desired, source_state_hash=state_hash, source_handoff_ref="docs/TEST_MIRROR_HANDOFF.md")
    second, second_effects = reconcile_tasks(first, desired, source_state_hash=state_hash, source_handoff_ref="docs/TEST_MIRROR_HANDOFF.md")
    assert first["reconciliation_generation"] == 1
    assert second["reconciliation_generation"] == 1
    assert first_effects[0]["disposition"] == "CREATED"
    assert second_effects[0]["disposition"] == "UNCHANGED"


def test_active_task_is_not_silently_rewritten():
    state = vector(runtime="ACTIVE")
    state_hash = canonical_hash(normalize_vector(state))
    registry = {"tasks": [{"task_id": "t", "state": "ACTIVE", "claim_id": "c", "goal": "old", "authority": {"domain": "TEST", "ceiling_ref": "A"}}]}
    desired = [{"task_id": "t", "state": "HANDOFF_READY", "goal": "new", "authority": {"domain": "TEST", "ceiling_ref": "A"}}]
    reconciled, effects = reconcile_tasks(registry, desired, source_state_hash=state_hash, source_handoff_ref="docs/TEST_MIRROR_HANDOFF.md")
    assert reconciled["tasks"][0]["goal"] == "old"
    assert reconciled["tasks"][0]["reconciliation_disposition"] == "ESCALATION_REQUIRED"
    assert effects[0]["reason"] == "ACTIVE_CLAIM_REQUIRES_PRECLAIM_OR_SUCCESSOR_RECONCILIATION"


def test_preclaim_fails_closed_on_stale_state():
    current = vector(runtime="ACTIVE")
    old = vector(runtime="BLOCKED")
    task = {"task_id": "t", "source_state_hash": canonical_hash(normalize_vector(old)), "reconciliation_disposition": "UNCHANGED"}
    ok, reason = preclaim_revalidate(task, current)
    assert ok is False
    assert reason == "TASK_SOURCE_STATE_STALE"


def test_alignment_packet_binds_transition_and_master_records_destination():
    before = vector(runtime="BLOCKED")
    after = vector(runtime="ACTIVE")
    delta = derive_delta(before, after, affected_scopes=["module:test"])
    packet = build_alignment_packet(
        transition_id="T-1",
        source_handoff_ref="docs/TEST_MIRROR_HANDOFF.md",
        before_state=before,
        after_state=after,
        semantic_delta=delta,
        module_id="module:test",
        endpoint_id="task-registry",
        projection_before={"tasks": ["old"]},
        projection_after={"tasks": ["new"]},
        task_effects=[{"task_id": "old", "disposition": "SUPERSEDED"}],
        alignment_disposition="ALIGNED",
    )
    assert packet["custody_destination"] == "master-records/orchestration"
    assert packet["source_state_hash"] == delta["source_state_hash"]
    assert packet["target_state_hash"] == delta["target_state_hash"]
    assert packet["reconstruction_state"] == "PASS"
