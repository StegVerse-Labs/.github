from scripts.validate_universal_data_transport_invariant import validate

def base():
    return {
      "schema":"stegverse.universal-data-transport-invariant/v1",
      "state":"CANONICAL_POLICY_ADOPTED_RUNTIME_ROLLOUT_ACTIVE",
      "canonical_boundary_stack":["SKAP_VAULT","KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM","EXTERNAL_SYSTEM"],
      "directionality":"BIDIRECTIONAL",
      "adjacent_hops_only":True,
      "transport_protocol":"InTr",
      "interlock_required_per_hop":True,
      "receipt_required_per_completed_hop":True,
      "receipt_hash_chain_required":True,
      "payload_plaintext_in_receipts":False,
      "authority_transfer_by_transport":False,
      "credential_authority":"TV/TVC",
      "event_triggered_transport":True,
      "always_on_application_receiver_required":False,
      "second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,
      "blind_consequence_retry_allowed":False,
      "direct_non_adjacent_transport":False,
      "direct_cross_boundary_state_mutation":False,
      "transport_availability_grants_execution_authority":False,
      "runtime_activation_claimed":False,
      "implementation_ref":"stegos/universal_intr_transport.py"
    }

def test_policy_accepts_canonical_transport_model():
    assert validate(base())==[]

def test_policy_rejects_always_on_receiver_requirement():
    p=base(); p["always_on_application_receiver_required"]=True
    assert "always_on_application_receiver_required" in validate(p)

def test_policy_rejects_direct_boundary_bypass():
    p=base(); p["adjacent_hops_only"]=False
    assert "adjacent_hops_only" in validate(p)

def test_policy_rejects_blind_consequence_retry():
    p=base(); p["blind_consequence_retry_allowed"]=True
    assert "blind_consequence_retry_allowed" in validate(p)
