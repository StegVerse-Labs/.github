from workers import manifest_state_transition_intr_ingress as mod

def test_stegbrowser_does_not_fall_through_to_purpose_worker_receipt(tmp_path):
    request={"processing_capability":"stegbrowser","route_id":"stegverse.route.stegbrowser.v1","state_graph":{"profile":"llm.v1"},"graph_id":"stegbrowser:test5-a","canonical_task_id":"EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001","wire_manifest_sha256":"0"*64,"canonical_manifest_sha256":"1"*64,"request_sha256":"3"*64}
    result=mod._capability_dispatch_fail_closed(tmp_path,request)
    assert result["disposition"]=="FAIL_CLOSED"
    assert result["evaluation_boundary"]=="UNIVERSAL_INTR_MANIFEST_CAPABILITY_DISPATCH"
    assert result["processing_capability"]=="stegbrowser" and result["profile"]=="llm.v1"
    assert result["transition_id"]=="INGRESS_ADMITTED"
    assert result["failed_predicate"]=="MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND"
    assert result["organization_master_records_organization_record_observed"] is False


def test_stegbrowser_owner_failure_custody_moved_with_the_execution():
    """Those predicates belonged to the fan execution, which is no longer here.

    Keeping them would assert custody for a path this worker cannot take. The
    SDK owns the fan now and carries the per-branch failure evidence; what this
    worker owes is a verdict that names where the owner went.
    """
    source=(mod.Path(__file__).resolve().parents[1]/"workers/manifest_state_transition_intr_ingress.py").read_text()
    assert 'failed_predicate": "MANIFEST_SELECTED_STEGBROWSER_BROWSER_OPERATION_COMPLETED"' not in source
    assert "REPAIR_EXISTING_STEGBROWSER_OWNER_OR_MANIFEST_DATA_THEN_RETRY_SAME_MANIFEST" not in source
    assert mod.RELOCATED_CAPABILITY_OWNERS["stegbrowser"] == "stegverse.governed_llm_fan.run_governed_llm_fan"
    # The generic adapter's own custody ordering is unaffected.
    assert "organization_records_before_master_records" in source
