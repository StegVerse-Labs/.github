#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-ai-ingress-policy.json"
CANONICAL_CHECKIN = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"


def emit(task_id: str, disposition: str, action: str, actor_kind: str | None, reason: str) -> None:
    print(json.dumps({
        "schema": "stegverse.task-registry-ai-session-ingress-disposition/v1",
        "task_id": task_id,
        "actor_kind": actor_kind,
        "disposition": disposition,
        "session_action": action,
        "reason": reason,
        "authority_effect": "NONE",
        "source_policy": "data/task-registry-ai-ingress-policy.json",
        "runtime_identity_attestation_proven": False,
    }, sort_keys=True))


def main() -> None:
    request = json.load(sys.stdin)
    task_id = str(request.get("task_id") or "").strip()
    context = request.get("checkin_context") or {}
    if not isinstance(context, dict):
        emit(task_id, "STOP_INVALID_CONTEXT", "END_SESSION", None, "checkin_context_must_be_object")
        return

    session_id = str(context.get("session_id") or "").strip()
    if not session_id:
        emit(task_id, "STOP_SESSION_ID_REQUIRED", "END_SESSION", None, "ai_session_ingress_requires_session_id")
        return

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    actor_kind = str(context.get("actor_kind") or "").strip().upper()
    if not actor_kind:
        emit(task_id, "STOP_ACTOR_IDENTITY_REQUIRED", "END_SESSION", None, "session_actor_kind_missing")
        return

    denied = set(policy.get("denied_ai_actor_kinds") or [])
    allowed = set(policy.get("allowed_actor_kinds") or [])
    if actor_kind in denied:
        emit(task_id, "STOP_AI_BOUNDARY_DENIED", "END_SESSION", actor_kind, "non_chatgpt_ai_task_registry_ingress_forbidden")
        return
    if actor_kind not in allowed:
        emit(task_id, "STOP_ACTOR_KIND_UNRECOGNIZED", "END_SESSION", actor_kind, "actor_kind_not_admitted_by_source_policy")
        return

    request = dict(request)
    request["checkin_context"] = dict(context)
    request["checkin_context"]["actor_kind"] = actor_kind
    result = subprocess.run(
        [sys.executable, str(CANONICAL_CHECKIN)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        emit(task_id, "STOP_CANONICAL_CHECKIN_ERROR", "END_SESSION", actor_kind, result.stderr.strip() or "canonical_checkin_failed")
        return

    payload = json.loads(result.stdout)
    payload["ai_session_ingress"] = {
        "actor_kind": actor_kind,
        "source_policy": "data/task-registry-ai-ingress-policy.json",
        "chatgpt_is_only_permitted_ai_kind": True,
        "runtime_identity_attestation_proven": False,
        "authority_effect": "NONE"
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
