#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cosv  # noqa: E402

SCHEMA_ID = "stegverse.repository-operational-state/v1"
STATE_KEYS = [
    "source_complete",
    "validated",
    "integrated",
    "released",
    "propagated",
    "activated",
    "runtime_proven",
]
EVIDENCE_KEYS = [
    "receipts",
    "manifests",
    "validation_runs",
    "issues",
    "pull_requests",
    "release_refs",
    "runtime_refs",
]

def _require(condition, message):
    if not condition:
        raise ValueError(message)

def implementation_completion(implementation):
    developed = int(implementation.get("developed_files", 0))
    scaffolding = int(implementation.get("scaffolding_files", 0))
    stubs = int(implementation.get("stub_files", 0))
    unknown = int(implementation.get("unknown_files", 0))
    _require(min(developed, scaffolding, stubs, unknown) >= 0, "implementation counts must be non-negative")
    total = developed + scaffolding + stubs + unknown
    return None if total == 0 else round((developed / total) * 100, 2)

def validate_cosv_binding(payload):
    repo_record = payload["cosv"]["repository"]
    _require(repo_record["profile"] == "aggregate.v1", "repository COSV must use aggregate.v1")
    _require(cosv.validate_record(repo_record), "repository COSV record invalid")
    for task in payload["cosv"]["tasks"]:
        _require(task["profile"] == "task.v1", "task COSV must use task.v1")
        _require(cosv.validate_record(task), f"task COSV invalid: {task.get('identity', '<unknown>')}")
    transition = payload["cosv"].get("transition")
    if transition is not None:
        _require(transition["profile"] == "transition.v1", "transition COSV must use transition.v1")
        _require(cosv.validate_record(transition), "transition COSV record invalid")
        _require(
            cosv.transition(repo_record["profile"], transition["from_vector"], transition["to_vector"]) == transition["vector"],
            "transition vector does not match COSV semantics",
        )

def validate_semantics(payload):
    _require(payload.get("schema") == SCHEMA_ID, "unsupported repository operational-state schema")
    repository = payload["repository"]
    for key in ("org", "name", "commit", "default_branch"):
        _require(bool(repository.get(key)), f"repository.{key} required")

    authority = payload["authority"]
    _require(authority.get("credential_authority") == "TV/TVC", "credential authority must remain TV/TVC")
    _require(authority.get("github_token_runtime_authority") == "NONE", "GitHub token runtime authority must remain NONE")
    _require(str(authority.get("repository_handoff", "")).endswith("MIRROR_HANDOFF.md"), "repository handoff must be a MIRROR_HANDOFF.md")

    validate_cosv_binding(payload)

    implementation = payload["implementation"]
    expected_completion = implementation_completion(implementation)
    declared_completion = implementation.get("completion_percent")
    if expected_completion is None:
        _require(declared_completion is None, "completion_percent must be null when no files are classified")
    else:
        _require(
            declared_completion is not None and abs(float(declared_completion) - expected_completion) < 0.01,
            f"completion_percent must equal developed/total = {expected_completion}",
        )

    state = payload["operational_state"]
    for key in STATE_KEYS:
        _require(key in state and state[key] in (True, False, None), f"operational_state.{key} must be true/false/null")

    evidence = payload["evidence"]
    for key in EVIDENCE_KEYS:
        _require(isinstance(evidence.get(key), list), f"evidence.{key} must be an array")

    # Fail closed: source completeness cannot manufacture stronger states.
    if state["activated"] is True:
        _require(bool(evidence["runtime_refs"] or evidence["receipts"]), "activation requires runtime or receipt evidence")
    if state["runtime_proven"] is True:
        _require(bool(evidence["runtime_refs"]), "runtime_proven requires runtime_refs")
    if state["released"] is True:
        _require(bool(evidence["release_refs"]), "released requires release_refs")
    if state["validated"] is True:
        _require(bool(evidence["validation_runs"] or evidence["receipts"]), "validated requires validation evidence")

    next_transition = payload["next_transition"]
    _require(next_transition.get("admissible") in (True, False, None), "next_transition.admissible must be true/false/null")
    _require(isinstance(next_transition.get("requirements"), list), "next_transition.requirements must be an array")
    _require(isinstance(next_transition.get("target_files"), list), "next_transition.target_files must be an array")

    projections = payload["projections"]
    for key in ("mirror_handoff", "human_summary", "ai_execution_brief"):
        _require(isinstance(projections.get(key), str), f"projections.{key} must be a string")

    return True

def render_human_summary(payload):
    repo = payload["repository"]
    state = payload["operational_state"]
    impl = payload["implementation"]
    vector = payload["cosv"]["repository"]["vector"]
    active = len(payload["work"]["active"])
    blocked = len(payload["work"]["blocked"])
    return (
        f"{repo['org']}/{repo['name']}@{repo['commit'][:12]} "
        f"COSV={vector} developed={impl['completion_percent']}% "
        f"source_complete={state['source_complete']} validated={state['validated']} "
        f"released={state['released']} activated={state['activated']} "
        f"runtime_proven={state['runtime_proven']} active_work={active} blocked={blocked}"
    )

def render_ai_execution_brief(payload):
    repo = payload["repository"]
    authority = payload["authority"]
    nxt = payload["next_transition"]
    return "\n".join([
        f"Repository: {repo['org']}/{repo['name']} @ {repo['commit']}",
        f"Authority handoff: {authority['repository_handoff']}",
        f"COSV repository vector: {payload['cosv']['repository']['vector']}",
        f"Next transition: {nxt['state']}",
        f"Admissible: {nxt['admissible']}",
        f"Authority required: {nxt['authority_required']}",
        "Requirements: " + (", ".join(nxt["requirements"]) if nxt["requirements"] else "none"),
        "Target files: " + (", ".join(nxt["target_files"]) if nxt["target_files"] else "none"),
        "Do not infer activation/runtime proof from source, merge, CI, or handoff state.",
        "COSV is an index into evidence; inspect referenced evidence before mutation.",
    ])

def hydrate_projections(payload):
    payload = json.loads(json.dumps(payload))
    payload["projections"]["human_summary"] = render_human_summary(payload)
    payload["projections"]["ai_execution_brief"] = render_ai_execution_brief(payload)
    return payload

def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("validate")
    p.add_argument("file")
    p = sp.add_parser("project")
    p.add_argument("file")
    p.add_argument("--output")
    args = ap.parse_args()

    payload = json.loads(Path(args.file).read_text())
    validate_semantics(payload)

    if args.cmd == "validate":
        print("REPOSITORY_OPERATIONAL_STATE_VALIDATION_PASS")
        return

    projected = hydrate_projections(payload)
    rendered = json.dumps(projected, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered)
    else:
        print(rendered, end="")

if __name__ == "__main__":
    main()
