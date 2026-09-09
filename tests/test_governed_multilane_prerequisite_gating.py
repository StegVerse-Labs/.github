from scripts.consume_governed_multilane_manifold_activation_request import (
    dependency_map,
    result_has_qualifying_evidence,
    reuse_is_qualifying,
)


def test_dependency_map_tracks_only_depends_on_edges():
    lineage = {
        "edges": [
            {"kind": "DEPENDS_ON", "from": "CHILD", "to": "PRE"},
            {"kind": "RELATED_TO", "from": "CHILD", "to": "OTHER"},
        ]
    }
    assert dependency_map(lineage) == {"CHILD": ["PRE"]}


def test_worker_success_requires_explicit_qualifying_evidence():
    assert result_has_qualifying_evidence({"returncode": 0}) is False
    assert result_has_qualifying_evidence({"state": "HANDOFF_READY"}) is False
    assert result_has_qualifying_evidence({"state": "COMPLETE"}) is True
    assert result_has_qualifying_evidence({"result": {"receipt_observed": True}}) is True


def test_aggregate_gadi_reuse_is_not_qualifying_for_dependents():
    assert reuse_is_qualifying(
        {"state": "INITIAL_IMPLEMENTATION_COMPLETE"},
        "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS",
    ) is False


def test_completed_reuse_can_qualify_for_dependents():
    assert reuse_is_qualifying(
        {"state": "COMPLETE_RELEASED"},
        "REUSE_COMPLETE_DO_NOT_REEXECUTE",
    ) is True
