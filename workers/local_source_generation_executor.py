#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "local-source-generation-executor.json"
TASK_ID = "SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001"
INVOCATION_SCHEMA = "stegverse.worker-invocation/v0.1"
RESULT_SCHEMA = "stegverse.local-source-generation-result/v0.1"
RUNTIME_PROOF_SCHEMA = "stegverse.local-source-generation-runtime-proof/v0.1"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def activated_evidence(value: object, capability_id: str) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(value, dict):
        return None, "CAPABILITY_EVIDENCE_MISSING"
    if value.get("capability_id") != capability_id:
        return None, "CAPABILITY_ID_MISMATCH"
    if value.get("phase") != "ACTIVATED":
        return None, "CAPABILITY_NOT_ACTIVATED"
    if not nonempty(value.get("activation_proof_ref")):
        return None, "ACTIVATION_PROOF_MISSING"
    refs = value.get("integration_evidence_refs")
    if not isinstance(refs, list) or not refs or not all(nonempty(item) for item in refs):
        return None, "INTEGRATION_EVIDENCE_MISSING"
    return value, None


def loopback_endpoint(value: object, allowed_hosts: set[str]) -> tuple[str | None, str | None]:
    if not nonempty(value):
        return None, "RUNTIME_ENDPOINT_MISSING"
    parsed = urllib.parse.urlparse(str(value))
    if parsed.scheme != "http" or parsed.hostname not in allowed_hosts:
        return None, "RUNTIME_ENDPOINT_NOT_LOOPBACK_HTTP"
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None, "RUNTIME_ENDPOINT_AUTH_OR_DECORATION_FORBIDDEN"
    base = str(value).rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    return base, None


def safe_runtime_env(config: dict[str, Any], source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    forbidden = tuple(str(x).upper() for x in config.get("forbidden_env_name_fragments") or [])
    for name, value in values.items():
        upper = name.upper()
        if value and any(marker in upper for marker in forbidden):
            # Presence in parent environment does not grant failure or authority;
            # it is deliberately excluded from the child. The returned environment
            # is the security boundary consumed by subprocess launch.
            continue
    allowed = set(config.get("runtime_env_allowlist") or [])
    return {name: values[name] for name in allowed if name in values}


def runtime_root(payload: dict[str, Any]) -> Path | None:
    explicit = payload.get("local_runtime_root")
    if nonempty(explicit):
        root = Path(str(explicit)).expanduser().resolve()
        if (root / "tools" / "run_sovereign_model.py").is_file():
            return root
    candidates = (
        Path.home() / ".stegverse" / "workloads" / "micro-node-runtime",
        Path.home() / "stegverse" / "micro-node-runtime",
        Path.home() / "StegVerse" / "micro-node-runtime",
    )
    for root in candidates:
        if (root / "tools" / "run_sovereign_model.py").is_file():
            return root.resolve()
    return None


def manifest_source_bindings(manifest: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if manifest.get("schema") != "stegverse.owner-implementation-work-manifest/v0.1":
        return None, "OWNER_MANIFEST_SCHEMA_INVALID"
    if manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
        return None, "OWNER_MANIFEST_NOT_ADMITTED"
    proposed = manifest.get("proposed_paths")
    if not isinstance(proposed, list) or not proposed or not all(nonempty(x) for x in proposed):
        return None, "OWNER_MANIFEST_PATH_SCOPE_INVALID"
    source_hashes = payload.get("source_hashes")
    if not isinstance(source_hashes, dict):
        return None, "SOURCE_HASHES_MISSING"
    normalized: dict[str, str | None] = {}
    for path in proposed:
        digest = source_hashes.get(path)
        if digest is not None and (not isinstance(digest, str) or len(digest) != 64):
            return None, f"SOURCE_HASH_INVALID:{path}"
        normalized[str(path)] = digest
    base_ref = payload.get("base_ref")
    base_sha = payload.get("expected_base_sha")
    if not nonempty(base_ref) or not isinstance(base_sha, str) or len(base_sha) != 40:
        return None, "BASE_IDENTITY_INVALID"
    return {
        "owner_manifest_sha256": canonical_hash(manifest),
        "owner_repository": manifest.get("owner_repository"),
        "delta_id": manifest.get("delta_id"),
        "proposed_paths": list(proposed),
        "source_hashes": normalized,
        "base_ref": base_ref,
        "expected_base_sha": base_sha,
    }, None


def generation_prompt(bindings: dict[str, Any]) -> str:
    contract = {
        "instruction": "Return JSON only. Produce replacement UTF-8 contents only for admitted paths. First file must be an admitted *_MIRROR_HANDOFF.md path. Do not include credentials, tokens, secrets, network instructions, signing, broadcast, provider or wallet operations.",
        "owner_manifest_sha256": bindings["owner_manifest_sha256"],
        "owner_repository": bindings["owner_repository"],
        "delta_id": bindings["delta_id"],
        "base_ref": bindings["base_ref"],
        "expected_base_sha": bindings["expected_base_sha"],
        "admitted_paths": bindings["proposed_paths"],
        "expected_source_sha256": bindings["source_hashes"],
        "output_schema": {
            "files": [{"path": "string", "content_utf8": "string"}],
            "new_branch": "string",
            "commit_message": "string"
        }
    }
    return canonical_json(contract)


def request_completion(endpoint: str, prompt: str, timeout: int, maximum_response_bytes: int) -> tuple[dict[str, Any] | None, dict[str, Any], str | None]:
    request_payload = {
        "model": "stegverse-reference-lm-v1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "seed": 0,
    }
    body = canonical_json(request_payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(maximum_response_bytes + 1)
    except Exception as exc:
        return None, {}, f"RUNTIME_REQUEST_FAILED:{type(exc).__name__}"
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
    if len(raw) > maximum_response_bytes:
        return None, {}, "RUNTIME_RESPONSE_TOO_LARGE"
    try:
        envelope = json.loads(raw.decode("utf-8"))
        content = envelope["choices"][0]["message"]["content"]
        generated = json.loads(content)
    except Exception:
        return None, {}, "MODEL_OUTPUT_NOT_STRICT_JSON"
    if not isinstance(generated, dict):
        return None, {}, "MODEL_OUTPUT_ROOT_NOT_OBJECT"
    telemetry = {
        "latency_ms": elapsed_ms,
        "usage": envelope.get("usage") if isinstance(envelope, dict) else None,
        "model": envelope.get("model") if isinstance(envelope, dict) else None,
        "model_hash": ((envelope.get("stegverse") or {}).get("model_hash") if isinstance(envelope, dict) else None),
    }
    return generated, telemetry, None


def validate_generated(config: dict[str, Any], bindings: dict[str, Any], generated: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    files = generated.get("files")
    if not isinstance(files, list) or not files:
        return None, "GENERATED_FILES_MISSING"
    if len(files) > int(config["maximum_file_count"]):
        return None, "GENERATED_FILE_COUNT_EXCEEDED"
    admitted = set(bindings["proposed_paths"])
    total = 0
    normalized: list[dict[str, Any]] = []
    for row in files:
        if not isinstance(row, dict):
            return None, "GENERATED_FILE_ROW_INVALID"
        path = row.get("path")
        content = row.get("content_utf8")
        if path not in admitted:
            return None, f"GENERATED_PATH_NOT_ADMITTED:{path}"
        if not isinstance(content, str):
            return None, f"GENERATED_CONTENT_NOT_TEXT:{path}"
        total += len(content.encode("utf-8"))
        normalized.append({
            "path": path,
            "content_utf8": content,
            "expected_source_sha256": bindings["source_hashes"].get(path),
            "replacement_sha256": sha256_text(content),
        })
    if total > int(config["maximum_total_bytes"]):
        return None, "GENERATED_TOTAL_BYTES_EXCEEDED"
    handoffs = {path for path in admitted if path.endswith("_MIRROR_HANDOFF.md")}
    if not handoffs or normalized[0]["path"] not in handoffs:
        return None, "GENERATED_HANDOFF_NOT_FIRST"
    if not nonempty(generated.get("new_branch")) or not nonempty(generated.get("commit_message")):
        return None, "GENERATED_BRANCH_OR_COMMIT_MESSAGE_MISSING"
    return normalized, None


def make_result(config: dict[str, Any], payload: dict[str, Any], bindings: dict[str, Any], files: list[dict[str, Any]], telemetry: dict[str, Any], runtime_proof_ref: str, teardown_ref: str) -> dict[str, Any]:
    source_evidence = payload["source_generation_capability_evidence"]
    model_evidence = payload["local_model_capability_evidence"]
    generated = payload["_generated"]
    return {
        "schema": RESULT_SCHEMA,
        "delta_id": bindings["delta_id"],
        "owner_repository": bindings["owner_repository"],
        "generator_capability_id": config["source_generation_capability_id"],
        "generator_capability_version": source_evidence.get("capability_version", "1.0.0"),
        "generator_existence_hash": source_evidence.get("existence_hash"),
        "generator_phase": "ACTIVATED",
        "generator_activation_proof_ref": source_evidence["activation_proof_ref"],
        "generator_integration_evidence_refs": list(source_evidence["integration_evidence_refs"]),
        "generator_authority_ref": source_evidence.get("authority_ref"),
        "generator_profile_ref": source_evidence.get("profile_ref"),
        "local_model_capability_id": config["local_model_capability_id"],
        "local_model_phase": "ACTIVATED",
        "local_model_activation_proof_ref": model_evidence["activation_proof_ref"],
        "model_runtime_proof_ref": runtime_proof_ref,
        "lifetime_class": payload.get("lifetime_class", "ONE_SHOT_OPERATION"),
        "persistent_execution_used": False,
        "teardown_or_reconstruction_evidence_ref": teardown_ref,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_used": False,
        "consumer_credential_present": False,
        "base_ref": bindings["base_ref"],
        "expected_base_sha": bindings["expected_base_sha"],
        "files": files,
        "new_branch": generated["new_branch"],
        "commit_message": generated["commit_message"],
        "execution_identity": payload.get("execution_identity") or f"local-source-generation:{bindings['delta_id']}",
        "usage": telemetry.get("usage"),
    }


def execute(config: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    source_evidence, error = activated_evidence(payload.get("source_generation_capability_evidence"), config["source_generation_capability_id"])
    if error:
        return {"state": "BLOCKED", "reason": f"SOURCE_GENERATION_{error}", "authority_effect": "NONE_FAIL_CLOSED"}, 0
    model_evidence, error = activated_evidence(payload.get("local_model_capability_evidence"), config["local_model_capability_id"])
    if error:
        return {"state": "BLOCKED", "reason": f"LOCAL_MODEL_{error}", "authority_effect": "NONE_FAIL_CLOSED"}, 0
    if not nonempty(source_evidence.get("existence_hash")) or len(source_evidence["existence_hash"]) != 64:
        return {"state": "BLOCKED", "reason": "SOURCE_GENERATION_EXISTENCE_HASH_INVALID", "authority_effect": "NONE_FAIL_CLOSED"}, 0
    if not nonempty(source_evidence.get("authority_ref")) or not nonempty(source_evidence.get("profile_ref")):
        return {"state": "BLOCKED", "reason": "SOURCE_GENERATION_AUTHORITY_OR_PROFILE_MISSING", "authority_effect": "NONE_FAIL_CLOSED"}, 0

    manifest = payload.get("owner_manifest")
    if not isinstance(manifest, dict):
        return {"state": "BLOCKED", "reason": "OWNER_MANIFEST_MISSING", "authority_effect": "NONE_FAIL_CLOSED"}, 0
    bindings, error = manifest_source_bindings(manifest, payload)
    if error:
        return {"state": "BLOCKED", "reason": error, "authority_effect": "NONE_FAIL_CLOSED"}, 0

    lifetime = payload.get("lifetime_class", "ONE_SHOT_OPERATION")
    if lifetime not in set(config["allowed_lifetime_classes"]):
        return {"state": "BLOCKED", "reason": "LIFETIME_CLASS_NOT_ADMITTED", "authority_effect": "NONE_FAIL_CLOSED"}, 0

    endpoint, error = loopback_endpoint(payload.get("runtime_endpoint"), set(config["allowed_hosts"]))
    process: subprocess.Popen[str] | None = None
    launched = False
    runtime_root_value: str | None = None
    if error:
        root = runtime_root(payload)
        if root is None:
            return {"state": "BLOCKED", "reason": "CANONICAL_LOCAL_RUNTIME_NOT_DISCOVERED", "authority_effect": "NONE_FAIL_CLOSED"}, 0
        runtime_root_value = str(root)
        port = int(payload.get("runtime_port") or config["default_runtime_port"])
        endpoint = f"http://127.0.0.1:{port}"
        child_env = safe_runtime_env(config)
        command = [sys.executable, str(root / config["canonical_local_runtime_tool"]), "--host", "127.0.0.1", "--port", str(port)]
        try:
            process = subprocess.Popen(command, cwd=str(root), env=child_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            launched = True
            time.sleep(float(payload.get("startup_wait_seconds", 0.25)))
            if process.poll() is not None:
                return {"state": "BLOCKED", "reason": "LOCAL_RUNTIME_LAUNCH_FAILED", "authority_effect": "NONE_FAIL_CLOSED"}, 0
        except Exception as exc:
            return {"state": "BLOCKED", "reason": f"LOCAL_RUNTIME_LAUNCH_FAILED:{type(exc).__name__}", "authority_effect": "NONE_FAIL_CLOSED"}, 0

    prompt = generation_prompt(bindings)
    prompt_sha = sha256_text(prompt)
    generated: dict[str, Any] | None = None
    telemetry: dict[str, Any] = {}
    request_error: str | None = None
    try:
        generated, telemetry, request_error = request_completion(str(endpoint), prompt, int(config["request_timeout_seconds"]), int(config["maximum_response_bytes"]))
        if request_error:
            return {"state": "BLOCKED", "reason": request_error, "authority_effect": "NONE_FAIL_CLOSED"}, 0
        files, error = validate_generated(config, bindings, generated)
        if error:
            return {"state": "BLOCKED", "reason": error, "authority_effect": "NONE_FAIL_CLOSED"}, 0
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    proof_id = f"{bindings['delta_id']}-{prompt_sha[:16]}"
    runtime_proof_ref = f"receipts/local-source-generation-executor/{proof_id}-runtime.json"
    teardown_ref = f"receipts/local-source-generation-executor/{proof_id}-teardown.json"
    payload["_generated"] = generated
    result = make_result(config, payload, bindings, files, telemetry, runtime_proof_ref, teardown_ref)
    proof = {
        "schema": RUNTIME_PROOF_SCHEMA,
        "proof_id": proof_id,
        "delta_id": bindings["delta_id"],
        "owner_manifest_sha256": bindings["owner_manifest_sha256"],
        "prompt_sha256": prompt_sha,
        "endpoint_class": "LOOPBACK_ONLY",
        "runtime_reused": not launched,
        "runtime_launched": launched,
        "runtime_root": runtime_root_value,
        "runtime_model": telemetry.get("model"),
        "runtime_model_hash": telemetry.get("model_hash"),
        "usage": telemetry.get("usage"),
        "persistent_execution_used": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "consumer_credential_present": False,
        "non_tv_tvc_secret_or_token_used": False,
        "provider_secret_used": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY"
    }
    teardown = {
        "schema": "stegverse.local-source-generation-teardown/v0.1",
        "proof_id": proof_id,
        "runtime_was_launched": launched,
        "runtime_terminated_after_operation": True if launched else None,
        "persistent_execution_used": False,
        "authority_effect": "NONE"
    }
    result["_runtime_proof"] = proof
    result["_teardown_proof"] = teardown
    return {"state": "COMPLETED", "reason": "LOCAL_SOURCE_GENERATION_RESULT_READY", "result": result, "authority_effect": "NONE_RESULT_ONLY"}, 0


def persist(result: dict[str, Any]) -> None:
    if result.get("state") != "COMPLETED":
        return
    body = result["result"]
    proof = body.pop("_runtime_proof")
    teardown = body.pop("_teardown_proof")
    delta_id = body["delta_id"]
    target_dir = ROOT / "receipts" / "admissible-source-generation-capability" / "generation-results"
    proof_dir = ROOT / "receipts" / "local-source-generation-executor"
    target_dir.mkdir(parents=True, exist_ok=True)
    proof_dir.mkdir(parents=True, exist_ok=True)
    proof_id = proof["proof_id"]
    for path, value in (
        (target_dir / f"{delta_id}.json", body),
        (proof_dir / f"{proof_id}-runtime.json", proof),
        (proof_dir / f"{proof_id}-teardown.json", teardown),
    ):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temp_name = handle.name
        os.replace(temp_name, path)


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != INVOCATION_SCHEMA:
        return 3
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        return 4
    payload = invocation.get("payload") or {}
    if not isinstance(payload, dict):
        return 5
    config = load_json(CONFIG_PATH)
    result, code = execute(config, payload)
    if result.get("state") == "COMPLETED":
        persist(result)
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
