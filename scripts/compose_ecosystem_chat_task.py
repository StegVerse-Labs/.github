#!/usr/bin/env python3
"""Build source-only Chat compositions using the existing reusable constructor.

No provider calls, runtime/credential discovery, claims, admissions or receipts.
The resulting dependency graph is a plan for existing owners, not a scheduler.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from . import materialize_reusable_task_construct as constructor
except ImportError:
    import materialize_reusable_task_construct as constructor

ALIASES = {"chatgpt": "openai", "claude": "anthropic", "grok": "xai", "gemini": "google"}
FIRST = "STEGOS-LOCAL-AI-ENTITY-CHATGPT-001"
SECOND = "STEGOS-LOCAL-AI-ENTITY-CLAUDE-CODE-001"
MODES = {"single", "parallel", "fallback"}
INTERACTIONS = {"browser_session", "provider_api", "local_tool"}


def fail(reason):
    raise ValueError(reason)


def nonsecret(value):
    if isinstance(value, dict):
        for key, item in value.items():
            name = key.lower()
            if name in {"token", "api_key", "authorization", "password", "secret", "cookie", "cookies", "private_key"} or name.endswith(("_token", "_secret", "_password", "_api_key")):
                fail("credential material is prohibited in composition parameters")
            nonsecret(item)
    elif isinstance(value, list):
        for item in value:
            nonsecret(item)


def required_text(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{key} must be a nonempty string")
    return value


def compose(spec):
    if not isinstance(spec, dict):
        fail("composition must be an object")
    nonsecret(spec)
    invocation = required_text(spec, "invocation_id")
    task = required_text(spec, "task_id")
    vector = required_text(spec, "cosv_task_vector")
    digest = required_text(spec, "request_hash")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        fail("request_hash must be a SHA-256 digest")
    index = constructor.load_effective_cosv_index()
    constructor.verify_task_pointer(task, vector, index)
    mode = spec.get("routing_mode")
    if mode not in MODES:
        fail("sequential/challenge requires the existing owner's governed derived-input contract; supported: single, parallel, fallback")
    scenario = spec.get("scenario", "answer")
    if scenario not in {"answer", "local_collaboration"}:
        fail("unknown scenario")
    sources = spec.get("sources")
    if not isinstance(sources, list) or not sources or (mode == "single" and len(sources) != 1):
        fail("sources must be nonempty; single requires exactly one source")
    custody = spec.get("custody_mode", "organization_batch")
    if custody not in {"organization_batch", "immediate_master_records"}:
        fail("unknown custody_mode")
    if custody == "immediate_master_records":
        required_text(spec, "immediate_custody_contract_ref")
    normalized = []
    ids = set()
    for source in sources:
        if not isinstance(source, dict):
            fail("each source must be an object")
        source_id = required_text(source, "source_id")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", source_id) or source_id in ids:
            fail("source_id must be unique and use letters, digits, underscore or hyphen")
        ids.add(source_id)
        provider = required_text(source, "provider").lower()
        required_text(source, "model")
        required_text(source, "operation_ref")
        interaction = source.get("interaction_mode")
        if interaction not in INTERACTIONS:
            fail("explicit browser_session, provider_api or local_tool interaction required")
        adapter = source.get("adapter_ref")
        if adapter is not None:
            required_text(source, "adapter_ref")
            required_text(source, "translation_reason")
        if "required" in source and not isinstance(source["required"], bool):
            fail("required must be boolean")
        normalized.append({**source, "canonical_provider": ALIASES.get(provider, provider)})
    if scenario == "local_collaboration":
        if mode != "parallel" or len(normalized) != 2:
            fail("local collaboration requires exactly two separately scoped participants")
        for source, expected, provider in zip(normalized, (FIRST, SECOND), ("openai", "anthropic")):
            if source.get("participant_task_id") != expected or source["canonical_provider"] != provider:
                fail("local order is ChatGPT first, Claude Code second")
            participant_vector = required_text(source, "participant_cosv")
            constructor.verify_task_pointer(expected, participant_vector, index)
        if normalized[1]["interaction_mode"] != "local_tool":
            fail("Claude Code requires genuine local_tool execution; Anthropic Messages is insufficient")

    nodes = []
    common = {"request_hash": digest, "custody_mode": custody}

    def node(node_id, reusable, parameters, dependencies=(), run_condition="AFTER_REQUIRED_EVIDENCE", terminal_paths=False):
        child = constructor.build_manifest(argparse.Namespace(
            reusable_task_id=reusable, invocation_id=f"{invocation}:{node_id}",
            task_id=task, cosv_task_vector=vector,
            parameters_json=json.dumps({**common, **parameters})))
        nodes.append({"node_id": node_id, "depends_on": list(dependencies),
                      "run_condition": run_condition, "all_terminal_paths": terminal_paths,
                      "manifest": child})
        return node_id

    terminal = []
    previous = None
    for source in normalized:
        sid = source["source_id"]
        dependencies = []
        if scenario == "local_collaboration":
            admission = node(f"{sid}-participant", "RT-LOCAL-AI-PARTICIPANT-001", {"source": source},
                             () if previous is None else (previous,),
                             "FIRST_PARTICIPANT_INDEPENDENTLY_RECONSTRUCTED" if previous else "CANONICAL_PARTICIPANT_ADMISSION")
            dependencies.append(admission)
        elif mode == "fallback" and previous:
            dependencies.append(previous)
        lease = node(f"{sid}-lease", "RT-STEGBROWSER-LLM-LEASE-001", {"source": source}, dependencies,
                     "PREVIOUS_SOURCE_UNUSABLE_AND_MANIFEST_FALLBACK_ADMITTED" if mode == "fallback" and previous else "AUTHENTIC_SOURCE_ADMISSION")
        ingress = node(f"{sid}-ingress", "RT-INTR-BOUNDARY-ADMISSION-001", {"source": source}, (lease,))
        operation = node(f"{sid}-operation", "RT-EPHEMERAL-LLM-ROUNDTRIP-001", {"source": source}, (ingress,))
        egress = node(f"{sid}-return", "RT-INTR-ROUNDTRIP-CORRELATION-001", {"source": source}, (operation,))
        close = node(f"{sid}-close", "RT-STEGBROWSER-LLM-CLOSE-001", {"source": source}, (lease, ingress, operation, egress),
                     "ON_ANY_SOURCE_TERMINAL_OUTCOME_INCLUDING_DENY_FAILURE_TIMEOUT_CANCELLATION", True)
        terminal.append(close)
        previous = close
    collected = node("collect", "RT-ECOSYSTEM-CHAT-COLLECT-001", {"source_ids": list(s["source_id"] for s in normalized), "routing_mode": mode}, terminal,
                     "ALL_ATTEMPTED_SOURCES_TERMINAL_AND_UNATTEMPTED_SOURCES_EXPLICITLY_SKIPPED")
    node("custody", "RT-INTR-EVIDENCE-CUSTODY-001", {"contract_ref": spec.get("immediate_custody_contract_ref"), "source_ids": sorted(ids)}, (collected,),
         "DECLARED_ORGANIZATION_BATCH_OR_EXPLICIT_IMMEDIATE_CUSTODY_CONTRACT")
    reusable = "RT-LOCAL-AI-COLLABORATION-001" if scenario == "local_collaboration" else "RT-ECOSYSTEM-CHAT-ANSWER-001"
    return constructor.build_manifest(argparse.Namespace(
        reusable_task_id=reusable, invocation_id=invocation, task_id=task, cosv_task_vector=vector,
        parameters_json=json.dumps({"specification": spec, "nodes": nodes,
            "execution_available": False, "source_only": True,
            "existing_owner_binding_required": True,
            "runtime_boundary": "NO_EXECUTABLE_RUNNER_DECLARED",
            "no_new_runtime_or_authority": True})))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compose(json.loads(Path(args.spec).read_text()))
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
