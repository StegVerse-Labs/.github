#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "local-source-generation-executor.json"
TASK_ID = "SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001"
CAPABILITY = "local_source_generation_executor"
CREDENTIAL_AUTHORITY = "TV/TVC"
OWNER_MANIFEST_SCHEMA = "stegverse.owner-implementation-work-manifest/v0.1"
ACTIVATION_SCHEMA = "stegverse.local-source-generation-activation-envelope/v0.1"
REQUEST_SCHEMA = "stegverse.local-source-generation-request/v0.1"
RESPONSE_SCHEMA = "stegverse.local-source-generation-response/v0.1"
RESULT_SCHEMA = "stegverse.local-source-generation-result/v0.1"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def safe_repo_path(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return False
    normalized = posixpath.normpath(value)
    return normalized == value and normalized not in {".", ".."} and not normalized.startswith("../") and not any(ch in value for ch in "*?[]")


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty(item) for item in value)


def sanitized_child_env(runtime_root: Path) -> dict[str, str]:
    path = os.environ.get("PATH", "")
    return {
        "PATH": path,
        "PYTHONPATH": str(runtime_root),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
    }


def child_env_is_secret_free(config: dict[str, Any], env: dict[str, str]) -> bool:
    fragments = [str(x).upper() for x in config.get("secret_name_fragments", []) if isinstance(x, str)]
    for key in env:
        upper = key.upper()
        if any(fragment in upper for fragment in fragments):
            return False
    return True


def formalism_roots() -> dict[str, Path]:
    raw = os.environ.get("STEGVERSE_FORMALISM_ROOTS_JSON", "")
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(value, dict):
        return {}
    return {k: Path(v).expanduser().resolve() for k, v in value.items() if isinstance(k, str) and isinstance(v, str) and v}


def runtime_root(config: dict[str, Any]) -> Path | None:
    candidates: list[Path] = []
    override = os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    for item in config.get("runtime_root_candidates", []):
        if isinstance(item, str):
            candidates.append(Path(item).expanduser() if Path(item).is_absolute() else ROOT / Path(item).expanduser())
    required = [Path(item) for item in config.get("required_runtime_markers", []) if isinstance(item, str)]
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if str(resolved) in seen:
            continue
        seen.add(str(resolved))
        if resolved.is_dir() and all((resolved / marker).is_file() for marker in required):
            return resolved
    return None


def validate_activation(config: dict[str, Any], envelope: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if envelope.get("schema") != ACTIVATION_SCHEMA:
        return None, "ACTIVATION_ENVELOPE_SCHEMA_INVALID"
    if envelope.get("credential_authority") != CREDENTIAL_AUTHORITY:
        return None, "ACTIVATION_CREDENTIAL_AUTHORITY_INVALID"
    if envelope.get("github_token_runtime_authority") is not False or envelope.get("non_tv_tvc_secret_or_token_used") is not False:
        return None, "ACTIVATION_TOKEN_AUTHORITY_FORBIDDEN"
    generation = envelope.get("source_generation") if isinstance(envelope.get("source_generation"), dict) else {}
    model = envelope.get("local_model") if isinstance(envelope.get("local_model"), dict) else {}
    if generation.get("capability_id") != config.get("source_generation_capability_id") or generation.get("phase") != "ACTIVATED":
        return None, "SOURCE_GENERATION_CAPABILITY_NOT_ACTIVATED"
    if model.get("capability_id") != config.get("local_model_capability_id") or model.get("phase") != "ACTIVATED":
        return None, "LOCAL_MODEL_CAPABILITY_NOT_ACTIVATED"
    for prefix, row in (("GENERATOR", generation), ("LOCAL_MODEL", model)):
        if not isinstance(row.get("existence_hash"), str) or len(row["existence_hash"]) != 64:
            return None, f"{prefix}_EXISTENCE_HASH_INVALID"
        if not nonempty(row.get("activation_proof_ref")):
            return None, f"{prefix}_ACTIVATION_PROOF_MISSING"
        if not string_list(row.get("integration_evidence_refs")):
            return None, f"{prefix}_INTEGRATION_EVIDENCE_MISSING"
    if not nonempty(model.get("runtime_proof_ref")):
        return None, "LOCAL_MODEL_RUNTIME_PROOF_MISSING"
    return {"source_generation": generation, "local_model": model, "envelope_sha256": canonical_hash(envelope)}, None


def git_head(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, timeout=5, check=False, env={"PATH": os.environ.get("PATH", "")})
    except Exception:
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and len(value) == 40 else None


def build_request(config: dict[str, Any], manifest: dict[str, Any], owner_root: Path, base_sha: str) -> tuple[dict[str, Any] | None, str | None]:
    proposed = manifest.get("proposed_paths")
    if manifest.get("schema") != OWNER_MANIFEST_SCHEMA or manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
        return None, "OWNER_WORK_NOT_ADMITTED"
    if not isinstance(proposed, list) or not proposed or not all(safe_repo_path(path) for path in proposed):
        return None, "OWNER_PATH_SCOPE_INVALID"
    sources: list[dict[str, Any]] = []
    prompt_bytes = 0
    for path in proposed:
        source_path = (owner_root / str(path)).resolve()
        try:
            source_path.relative_to(owner_root.resolve())
        except ValueError:
            return None, f"OWNER_PATH_ESCAPES_ROOT:{path}"
        if source_path.is_file():
            content = source_path.read_text(encoding="utf-8")
            source_sha = sha_text(content)
        else:
            content = None
            source_sha = None
        prompt_bytes += len((content or "").encode("utf-8"))
        sources.append({"path": path, "exists": content is not None, "source_sha256": source_sha, "content_utf8": content})
    request = {
        "schema": REQUEST_SCHEMA,
        "delta_id": manifest.get("delta_id"),
        "owner_repository": manifest.get("owner_repository"),
        "objective": manifest.get("objective"),
        "kind": manifest.get("kind"),
        "base_ref": "main",
        "expected_base_sha": base_sha,
        "proposed_paths": list(proposed),
        "authority_ceiling": list(manifest.get("authority_ceiling") or []),
        "source_files": sources,
        "requirements": {
            "response_schema": RESPONSE_SCHEMA,
            "json_only": True,
            "only_admitted_paths": True,
            "mirror_handoff_first": True,
            "no_authority_expansion": True,
            "credential_authority": CREDENTIAL_AUTHORITY,
        },
    }
    prompt_bytes += len(json.dumps({k: v for k, v in request.items() if k != "source_files"}, sort_keys=True).encode("utf-8"))
    if prompt_bytes > int(config["maximum_prompt_bytes"]):
        return None, "GENERATION_PROMPT_EXCEEDS_LIMIT"
    return request, None


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def http_json(url: str, payload: dict[str, Any] | None, timeout: float, max_bytes: int) -> tuple[int, dict[str, Any] | None, str | None]:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"} if body is not None else {}, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return int(response.status), None, "MODEL_RESPONSE_EXCEEDS_LIMIT"
            value = json.loads(raw)
            return int(response.status), value if isinstance(value, dict) else None, None
    except urllib.error.HTTPError as exc:
        return int(exc.code), None, f"HTTP_{exc.code}"
    except Exception as exc:
        return 0, None, f"HTTP_ERROR:{type(exc).__name__}"


def start_runtime(config: dict[str, Any], runtime: Path) -> tuple[subprocess.Popen[bytes] | None, str | None, dict[str, Any]]:
    env = sanitized_child_env(runtime)
    if not child_env_is_secret_free(config, env):
        return None, None, {"state": "BLOCKED", "reason": "CHILD_ENVIRONMENT_NOT_SECRET_FREE"}
    port = free_port()
    endpoint = f"http://127.0.0.1:{port}"
    command = [sys.executable, str(runtime / "tools" / "run_sovereign_model.py"), "--host", "127.0.0.1", "--port", str(port)]
    process = subprocess.Popen(command, cwd=runtime, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True, env=env)
    deadline = time.time() + float(config["startup_timeout_seconds"])
    health: dict[str, Any] | None = None
    while time.time() < deadline:
        if process.poll() is not None:
            return process, endpoint, {"state": "FAILED", "reason": "LOCAL_MODEL_PROCESS_EXITED", "returncode": process.returncode}
        status, value, _error = http_json(endpoint + str(config["health_path"]), None, 1.0, 65536)
        if status == 200 and isinstance(value, dict) and value.get("state") == "READY":
            health = value
            break
        time.sleep(0.05)
    if health is None:
        return process, endpoint, {"state": "FAILED", "reason": "LOCAL_MODEL_STARTUP_TIMEOUT"}
    if health.get("private_endpoint_only") is not True or health.get("third_party_inference_required") is not False:
        return process, endpoint, {"state": "FAILED", "reason": "LOCAL_MODEL_HEALTH_AUTHORITY_INVALID", "health": health}
    return process, endpoint, {"state": "READY", "health": health, "child_environment_keys": sorted(env), "consumer_credential_present": False, "non_tv_tvc_secret_or_token_used": False}


def stop_runtime(process: subprocess.Popen[bytes] | None, timeout: float) -> dict[str, Any]:
    if process is None:
        return {"attempted": False, "terminated": True}
    if process.poll() is not None:
        return {"attempted": True, "terminated": True, "returncode": process.returncode}
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except OSError:
        try:
            process.terminate()
        except OSError:
            pass
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            try:
                process.kill()
            except OSError:
                pass
        try:
            process.wait(timeout=1)
        except Exception:
            pass
    return {"attempted": True, "terminated": process.poll() is not None, "returncode": process.returncode}


def extract_response(value: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str | None, dict[str, Any]]:
    if not isinstance(value, dict):
        return None, "MODEL_RESPONSE_NOT_OBJECT", {}
    if value.get("schema") == RESPONSE_SCHEMA:
        return value, None, {"route": "structured"}
    choices = value.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message") if isinstance(choices[0].get("message"), dict) else {}
        text = message.get("content")
        if isinstance(text, str):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return None, "LOCAL_MODEL_STRUCTURED_OUTPUT_INVALID", {"route": "chat", "usage": value.get("usage")}
            if isinstance(parsed, dict):
                return parsed, None, {"route": "chat", "usage": value.get("usage")}
    return None, "LOCAL_MODEL_STRUCTURED_OUTPUT_INVALID", {"usage": value.get("usage")}


def validate_model_response(config: dict[str, Any], manifest: dict[str, Any], request: dict[str, Any], response: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    if response.get("schema") != RESPONSE_SCHEMA:
        return None, "SOURCE_GENERATION_RESPONSE_SCHEMA_INVALID"
    if response.get("delta_id") != manifest.get("delta_id") or response.get("owner_repository") != manifest.get("owner_repository"):
        return None, "SOURCE_GENERATION_RESPONSE_OWNER_MISMATCH"
    files = response.get("files")
    if not isinstance(files, list) or not files or len(files) > int(config["maximum_file_count"]):
        return None, "SOURCE_GENERATION_RESPONSE_FILES_INVALID"
    admitted = list(manifest.get("proposed_paths") or [])
    admitted_set = set(admitted)
    source_rows = {row["path"]: row for row in request["source_files"]}
    normalized: list[dict[str, Any]] = []
    total = 0
    for row in files:
        if not isinstance(row, dict) or not safe_repo_path(row.get("path")) or row.get("path") not in admitted_set or not isinstance(row.get("content_utf8"), str):
            return None, "SOURCE_GENERATION_RESPONSE_PATH_OR_CONTENT_INVALID"
        path = row["path"]
        content = row["content_utf8"]
        total += len(content.encode("utf-8"))
        normalized.append({"path": path, "content_utf8": content, "expected_source_sha256": source_rows[path]["source_sha256"], "replacement_sha256": sha_text(content)})
    if total > int(config["maximum_total_bytes"]):
        return None, "SOURCE_GENERATION_RESPONSE_TOTAL_BYTES_EXCEEDED"
    handoffs = {path for path in admitted if path.endswith("_MIRROR_HANDOFF.md")}
    if not handoffs or normalized[0]["path"] not in handoffs:
        return None, "SOURCE_GENERATION_HANDOFF_NOT_FIRST"
    return normalized, None


def perform_generation(config: dict[str, Any], manifest: dict[str, Any], activation: dict[str, Any]) -> dict[str, Any]:
    owner = manifest.get("owner_repository")
    roots = formalism_roots()
    owner_root = roots.get(owner) if isinstance(owner, str) else None
    if owner_root is None or not owner_root.is_dir():
        return {"state": "BLOCKED", "reason": "OWNER_SOURCE_NOT_MATERIALIZED"}
    base_sha = git_head(owner_root)
    if base_sha is None:
        return {"state": "BLOCKED", "reason": "OWNER_BASE_SHA_NOT_OBSERVABLE"}
    request, error = build_request(config, manifest, owner_root, base_sha)
    if error:
        return {"state": "BLOCKED", "reason": error}
    runtime = runtime_root(config)
    if runtime is None:
        return {"state": "BLOCKED", "reason": "CANONICAL_LOCAL_MODEL_RUNTIME_NOT_MATERIALIZED"}

    process: subprocess.Popen[bytes] | None = None
    endpoint: str | None = None
    started: dict[str, Any] = {}
    response_meta: dict[str, Any] = {}
    teardown: dict[str, Any] = {}
    try:
        process, endpoint, started = start_runtime(config, runtime)
        if started.get("state") != "READY" or endpoint is None:
            return {"state": "BLOCKED", "reason": started.get("reason", "LOCAL_MODEL_NOT_READY"), "runtime": started}
        status, raw, route_error = http_json(endpoint + str(config["structured_endpoint_path"]), request, float(config["request_timeout_seconds"]), int(config["maximum_model_response_bytes"]))
        if status == 404:
            prompt = (
                "Return ONLY a JSON object conforming to schema stegverse.local-source-generation-response/v0.1. "
                "Do not add markdown or prose. Preserve the exact delta_id, owner_repository and only the admitted paths. "
                "The first generated file must be the admitted *_MIRROR_HANDOFF.md. Request follows:\n" + json.dumps(request, sort_keys=True)
            )
            chat_payload = {"model": started.get("health", {}).get("model"), "messages": [{"role": "user", "content": prompt}], "max_tokens": 256, "seed": 0}
            status, raw, route_error = http_json(endpoint + str(config["fallback_chat_endpoint_path"]), chat_payload, float(config["request_timeout_seconds"]), int(config["maximum_model_response_bytes"]))
        if status != 200 or raw is None:
            return {"state": "BLOCKED", "reason": route_error or f"LOCAL_MODEL_HTTP_{status}", "runtime": started}
        parsed, error, response_meta = extract_response(raw)
        if error or parsed is None:
            return {"state": "BLOCKED", "reason": error or "LOCAL_MODEL_STRUCTURED_OUTPUT_INVALID", "runtime": started, "response_meta": response_meta}
        files, error = validate_model_response(config, manifest, request, parsed)
        if error or files is None:
            return {"state": "BLOCKED", "reason": error or "LOCAL_MODEL_OUTPUT_REJECTED", "runtime": started, "response_meta": response_meta}
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        generation = activation["source_generation"]
        model = activation["local_model"]
        result = {
            "schema": RESULT_SCHEMA,
            "delta_id": manifest["delta_id"],
            "owner_repository": owner,
            "base_ref": "main",
            "expected_base_sha": base_sha,
            "new_branch": parsed.get("new_branch") or f"feat/{str(manifest['delta_id']).lower()}",
            "commit_message": parsed.get("commit_message") or f"Implement {manifest['delta_id']}",
            "generator_capability_id": generation["capability_id"],
            "generator_capability_version": generation.get("capability_version", "1.0.0"),
            "generator_existence_hash": generation["existence_hash"],
            "generator_phase": "ACTIVATED",
            "generator_activation_proof_ref": generation["activation_proof_ref"],
            "generator_integration_evidence_refs": list(generation["integration_evidence_refs"]),
            "generator_authority_ref": generation.get("authority_ref", "StegVerse-Labs/StegCore:management/admissible-existence-capability-registry.json"),
            "generator_profile_ref": "StegVerse-Labs/.github:control/local-source-generation-executor.json",
            "local_model_capability_id": model["capability_id"],
            "local_model_phase": "ACTIVATED",
            "local_model_activation_proof_ref": model["activation_proof_ref"],
            "model_runtime_proof_ref": model["runtime_proof_ref"],
            "execution_identity": f"local-source-generation:{manifest['delta_id']}:{base_sha[:12]}:{int(time.time())}",
            "lifetime_class": config["default_lifetime_class"],
            "persistent_execution_used": False,
            "teardown_or_reconstruction_evidence_ref": f"receipts/local-source-generation-executor/teardown/{manifest['delta_id']}.json",
            "credential_authority": CREDENTIAL_AUTHORITY,
            "github_token_runtime_authority": False,
            "non_tv_tvc_secret_or_token_used": False,
            "consumer_credential_present": False,
            "files": files,
            "request_sha256": canonical_hash(request),
            "activation_envelope_sha256": activation["envelope_sha256"],
            "generated_at": now,
            "measured_usage": response_meta.get("usage"),
            "authority_effect": "NONE_LOCAL_SOURCE_PROPOSAL_ONLY"
        }
        return {"state": "COMPLETED", "reason": "LOCAL_SOURCE_GENERATION_RESULT_READY", "result": result, "runtime": started, "response_meta": response_meta}
    finally:
        teardown = stop_runtime(process, float(config["teardown_timeout_seconds"]))
        if endpoint:
            teardown["endpoint"] = endpoint
        teardown["credential_authority"] = CREDENTIAL_AUTHORITY
        teardown["github_token_runtime_authority"] = False
        teardown["non_tv_tvc_secret_or_token_used"] = False
        teardown["authority_effect"] = "NONE_PROCESS_LIFECYCLE_EVIDENCE_ONLY"
        teardown_dir = ROOT / str(config["receipt_directory"]) / "teardown"
        delta = manifest.get("delta_id")
        if isinstance(delta, str) and delta:
            atomic_write(teardown_dir / f"{delta}.json", teardown)


def evaluate(config: dict[str, Any]) -> dict[str, Any]:
    activation_path = ROOT / str(config["activation_envelope"])
    if not activation_path.is_file():
        return {"state": "BLOCKED", "reason": "ACTIVATION_ENVELOPE_MISSING", "results": [], "authority_effect": "NONE_FAIL_CLOSED"}
    activation, error = validate_activation(config, load(activation_path))
    if error or activation is None:
        return {"state": "BLOCKED", "reason": error or "ACTIVATION_INVALID", "results": [], "authority_effect": "NONE_FAIL_CLOSED"}
    owner_dir = ROOT / str(config["owner_work_directory"])
    if not owner_dir.is_dir():
        return {"state": "BLOCKED", "reason": "OWNER_WORK_DIRECTORY_MISSING", "results": [], "authority_effect": "NONE_FAIL_CLOSED"}
    rows: list[dict[str, Any]] = []
    generated = 0
    for path in sorted(owner_dir.glob("*.json")):
        manifest = load(path)
        if manifest.get("schema") != OWNER_MANIFEST_SCHEMA or manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
            continue
        row = perform_generation(config, manifest, activation)
        rows.append({"delta_id": manifest.get("delta_id"), **row})
        if row.get("state") == "COMPLETED" and isinstance(row.get("result"), dict):
            target = ROOT / str(config["generation_result_directory"]) / f"{manifest['delta_id']}.json"
            if target.exists() and canonical_hash(load(target)) != canonical_hash(row["result"]):
                rows[-1] = {"delta_id": manifest.get("delta_id"), "state": "BLOCKED", "reason": "EXISTING_GENERATION_RESULT_DIFFERS"}
                continue
            if not target.exists():
                atomic_write(target, row["result"])
            generated += 1
    if generated:
        return {"state": "COMPLETED", "reason": "LOCAL_GENERATION_RESULTS_EMITTED", "generated": generated, "results": rows, "credential_authority": CREDENTIAL_AUTHORITY, "non_tv_tvc_secret_or_token_used": False, "authority_effect": "NONE_LOCAL_SOURCE_PROPOSAL_ONLY"}
    return {"state": "BLOCKED", "reason": rows[0]["reason"] if len(rows) == 1 else "NO_LOCAL_GENERATION_RESULT", "generated": 0, "results": rows, "credential_authority": CREDENTIAL_AUTHORITY, "non_tv_tvc_secret_or_token_used": False, "authority_effect": "NONE_FAIL_CLOSED"}


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    timing = task.get("heartbeat_timing") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID or not nonempty(task.get("claim_id")) or not isinstance(timing.get("fencing_token"), int):
        return 4
    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 5
    allowed = set(execution.get("allowed_paths") or [])
    for required in ("receipts/local-source-generation-executor/**", "receipts/admissible-source-generation-capability/generation-results/**"):
        if required not in allowed:
            return 6
    config = load(CONFIG_PATH)
    if config.get("schema") != "stegverse.local-source-generation-executor/v0.1" or config.get("credential_authority") != CREDENTIAL_AUTHORITY or config.get("github_token_required") is not False or config.get("consumer_secret_or_token_authority") is not False:
        return 7
    result = evaluate(config)
    receipt = {
        "schema": "stegverse.local-source-generation-executor-receipt/v0.1",
        "goal_id": config["goal_id"],
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": task["claim_id"],
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": timing["fencing_token"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "state": result["state"],
        "result": result,
        "fail_closed": True,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
        "repository_mutation_performed": False,
        "authority_effect": "NONE_LOCAL_SOURCE_PROPOSAL_ONLY"
    }
    receipt_path = ROOT / str(config["receipt_directory"]) / f"{TASK_ID}.json"
    atomic_write(receipt_path, receipt)
    blocked = result["state"] != "COMPLETED"
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": result["state"],
        "transition_id": "LOCAL_SOURCE_GENERATION_RESULT_READY" if not blocked else "LOCAL_SOURCE_GENERATION_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": None if not blocked else "LOCAL_SOURCE_GENERATION_RECHECK",
        "expected_next_earliest_epoch": None if not blocked else epoch + 1,
        "expected_next_latest_epoch": None if not blocked else epoch + 1,
        "checkpoint_ref": f"receipts/local-source-generation-executor/{TASK_ID}.json",
        "evidence_refs": ["control/local-source-generation-executor.json", f"receipts/local-source-generation-executor/{TASK_ID}.json"],
        "blocker": None if not blocked else {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": result["reason"],
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "RECHECK_CANONICAL_ACTIVATION_LOCAL_MODEL_PROFILE_AND_OWNER_SOURCE"
        },
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "local_source_generation_executor"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
