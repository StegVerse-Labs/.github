#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
from cosv import transition, validate_vector

SCHEMA = "stegverse.cosv-state-packet/v1"
MODES = {"FULL", "DELTA"}
LEVELS = {"task", "goal", "component", "subsystem", "system", "ecosystem"}


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def record_map(records):
    out = {}
    for record in records:
        identity = record["identity"]
        if identity in out:
            raise ValueError(f"duplicate identity: {identity}")
        if record["level"] not in LEVELS:
            raise ValueError(f"invalid level: {record['level']}")
        if record["profile"] not in ("task.v1", "aggregate.v1"):
            raise ValueError("invalid profile")
        if not validate_vector(record["profile"], record["vector"]):
            raise ValueError(f"invalid vector: {identity}")
        if not record.get("evidence_refs"):
            raise ValueError(f"missing evidence refs: {identity}")
        out[identity] = record
    return out


def state_root(records):
    rows = [
        {"identity": key, "profile": value["profile"], "level": value["level"], "vector": value["vector"]}
        for key, value in sorted(record_map(records).items())
    ]
    return digest(rows)


def unchanged_root(previous_map, changed_ids):
    rows = [
        {"identity": key, "profile": value["profile"], "level": value["level"], "vector": value["vector"]}
        for key, value in sorted(previous_map.items())
        if key not in changed_ids
    ]
    return digest(rows)


def derive_constraints(records):
    critical = conflicts = unassigned = stale = 0
    thread = False
    for record in records:
        digits = list(map(int, record["vector"]))
        exact = record.get("exact_metrics", {})
        if record["profile"] == "aggregate.v1":
            critical += int(exact.get("critical_blockers", digits[9]))
            conflicts += int(exact.get("conflicting_claims", digits[10]))
            unassigned += int(exact.get("unassigned_work", digits[11]))
            stale += int(exact.get("stale_claims", digits[12]))
            thread = thread or digits[13] == 1
        else:
            unassigned += int(exact.get("unassigned_work", digits[2]))
            critical += int(exact.get("blocker_count", digits[10]))
            thread = thread or digits[9] == 1
    return {
        "critical_blockers": critical,
        "conflicting_claims": conflicts,
        "unassigned_work": unassigned,
        "stale_claims": stale,
        "thread_required": thread,
    }


def gradient_inputs(previous_map, current_map, changed_ids):
    result = []
    for identity in sorted(changed_ids):
        current = current_map[identity]
        previous = previous_map.get(identity)
        if previous is None or previous["profile"] != current["profile"]:
            transition_vector = "9" * 14
        else:
            transition_vector = transition(current["profile"], previous["vector"], current["vector"])
        result.append({
            "identity": identity,
            "level": current["level"],
            "profile": current["profile"],
            "previous_vector": None if previous is None else previous["vector"],
            "current_vector": current["vector"],
            "transition_vector": transition_vector,
            "previous_exact_metrics": {} if previous is None else previous.get("exact_metrics", {}),
            "current_exact_metrics": current.get("exact_metrics", {}),
            "admissibility_ref": current.get("admissibility_ref"),
            "coherency_group_ref": current.get("coherency_group_ref"),
            "authority_effect": "NONE",
        })
    return result


def finalize(packet):
    packet = dict(packet)
    packet["packet_sha256"] = digest(packet)
    return packet


def build_full(carrier_ref, records, observed_at, previous_packet_sha256=None):
    current = record_map(records)
    packet = {
        "schema": SCHEMA,
        "mode": "FULL",
        "carrier_ref": carrier_ref,
        "observed_at": observed_at,
        "previous_packet_sha256": previous_packet_sha256,
        "state_root_sha256": state_root(records),
        "unchanged_state_root_sha256": None,
        "records": [current[key] for key in sorted(current)],
        "gradient_inputs": [],
        "constraint_summary": derive_constraints(records),
        "authority": {
            "heartbeat_authority_effect": "NONE",
            "packet_authority_effect": "NONE",
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
            "github_token_runtime_authority": "NONE",
        },
    }
    return finalize(packet)


def build_delta(carrier_ref, previous_packet, current_records, observed_at):
    if previous_packet["mode"] != "FULL":
        raise ValueError("v1 delta build requires a FULL previous packet")
    previous_records = reconstruct(previous_packet, None)
    previous_map = record_map(previous_records)
    current_map = record_map(current_records)
    removed = set(previous_map) - set(current_map)
    if removed:
        raise ValueError("v1 delta does not permit implicit record removal")
    changed = {
        key for key, value in current_map.items()
        if key not in previous_map
        or previous_map[key]["vector"] != value["vector"]
        or previous_map[key].get("exact_metrics", {}) != value.get("exact_metrics", {})
    }
    packet = {
        "schema": SCHEMA,
        "mode": "DELTA",
        "carrier_ref": carrier_ref,
        "observed_at": observed_at,
        "previous_packet_sha256": previous_packet["packet_sha256"],
        "state_root_sha256": state_root(current_records),
        "unchanged_state_root_sha256": unchanged_root(previous_map, changed),
        "records": [current_map[key] for key in sorted(changed)],
        "gradient_inputs": gradient_inputs(previous_map, current_map, changed),
        "constraint_summary": derive_constraints(current_records),
        "authority": {
            "heartbeat_authority_effect": "NONE",
            "packet_authority_effect": "NONE",
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
            "github_token_runtime_authority": "NONE",
        },
    }
    return finalize(packet)


def reconstruct(packet, previous_records):
    if packet["mode"] == "FULL":
        return [dict(record) for record in packet["records"]]
    if previous_records is None:
        raise ValueError("previous records required")
    previous_map = record_map(previous_records)
    changed = record_map(packet["records"])
    if unchanged_root(previous_map, set(changed)) != packet["unchanged_state_root_sha256"]:
        raise ValueError("unchanged root mismatch")
    previous_map.update(changed)
    return [previous_map[key] for key in sorted(previous_map)]


def verify(packet, previous_records=None):
    if packet.get("schema") != SCHEMA or packet.get("mode") not in MODES:
        raise ValueError("invalid packet schema/mode")
    authority = packet.get("authority", {})
    if authority.get("heartbeat_authority_effect") != "NONE" or authority.get("packet_authority_effect") != "NONE":
        raise ValueError("packet/carrier authority must be NONE")
    if authority.get("credential_authority") != "TV/TVC" or authority.get("non_tv_tvc_secret_or_token_used") is not False:
        raise ValueError("credential invariant failed")
    copy = dict(packet)
    claimed = copy.pop("packet_sha256", None)
    if claimed != digest(copy):
        raise ValueError("packet digest mismatch")
    record_map(packet.get("records", []))
    if packet["mode"] == "FULL":
        if state_root(packet["records"]) != packet["state_root_sha256"]:
            raise ValueError("state root mismatch")
    else:
        if previous_records is None:
            raise ValueError("delta verification requires previous reconstructed records")
        reconstructed = reconstruct(packet, previous_records)
        if state_root(reconstructed) != packet["state_root_sha256"]:
            raise ValueError("delta state root mismatch")
    return True


def self_test():
    base = [
        {"identity":"task:a","profile":"task.v1","level":"task","vector":"51000000110100","evidence_refs":["e:a"],"observed_at":"t0","exact_metrics":{}},
        {"identity":"subsystem:x","profile":"aggregate.v1","level":"subsystem","vector":"57665579810010","evidence_refs":["e:x"],"observed_at":"t0","exact_metrics":{"critical_blockers":1}},
    ]
    full = build_full("HB29", base, "2026-08-18T13:00:00Z")
    assert verify(full)
    current = [dict(item) for item in base]
    current[0] = dict(current[0])
    current[0]["vector"] = "71000000100110"
    delta = build_delta("HB30", full, current, "2026-08-18T13:01:00Z")
    assert verify(delta, base)
    rebuilt = reconstruct(delta, base)
    assert state_root(rebuilt) == state_root(current)
    assert delta["gradient_inputs"][0]["transition_vector"] != "0" * 14
    print("COSV_STATE_PACKET_SELF_TEST_PASS")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("packet")
    verify_parser.add_argument("--previous")
    args = parser.parse_args()
    if args.cmd == "self-test":
        return self_test()
    packet = json.loads(Path(args.packet).read_text())
    previous = None if not args.previous else json.loads(Path(args.previous).read_text())
    if isinstance(previous, dict) and "records" in previous:
        previous = reconstruct(previous, None)
    verify(packet, previous)
    print("COSV_STATE_PACKET_VERIFY_PASS")


if __name__ == "__main__":
    main()
