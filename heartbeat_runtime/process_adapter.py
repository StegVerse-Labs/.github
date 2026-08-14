from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from .engine_v2 import WorkerResponse
from .blocker_policy import validate_worker_response_blocker


class ProcessWorkerAdapter:
    """Invoke a pre-admitted worker executable through a sandboxed JSON protocol.

    The configured executable never mutates the authoritative workspace directly.
    It runs in a temporary copy, the adapter computes the candidate filesystem
    delta, validates every changed path against the admitted HANDOFF path scope
    and the current claim/fence, and only then projects accepted mutations back.

    An adapter may additionally bind one local continuity-state root. The worker
    sees only a sandbox-local mirror through ``STEGVERSE_BOUND_STATE_ROOT``; it
    never receives the authoritative path. External-state changes are diffed and
    fenced independently and are projected only when every changed relative path
    is within the adapter's explicit state scope. This creates a bounded local
    request/receipt carrier without forwarding a credential or giving a worker
    arbitrary host-filesystem authority.

    The adapter itself grants no execution authority.

    Runtime invariant: BLOCKED is not a passive waiting state. Every blocked
    response must include a resolution contract. Third-party dependencies may
    never be returned as BLOCKED; they require ACTIVE workaround execution.
    """

    RECEIPT_ROOT = "receipts/worker-mutation-scope"
    BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"

    def __init__(
        self,
        command: list[str],
        *,
        cwd: str | Path,
        timeout_seconds: float = 30.0,
        env_allowlist: tuple[str, ...] = (),
        bound_state_root: str | Path | None = None,
        bound_state_allowed_paths: tuple[str, ...] = (),
    ) -> None:
        if not command or any(not isinstance(part, str) or not part for part in command):
            raise ValueError("command must be a non-empty list of strings")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        self.command = tuple(command)
        self.cwd = Path(cwd).resolve()
        self.timeout_seconds = float(timeout_seconds)
        self.env_allowlist = tuple(env_allowlist)
        self.bound_state_root = (
            Path(bound_state_root).expanduser().resolve() if bound_state_root is not None else None
        )
        self.bound_state_allowed_paths = tuple(bound_state_allowed_paths)
        if self.bound_state_root is None and self.bound_state_allowed_paths:
            raise ValueError("bound_state_allowed_paths require bound_state_root")
        if self.bound_state_root is not None and not self.bound_state_allowed_paths:
            raise ValueError("bound_state_root requires non-empty bound_state_allowed_paths")
        for pattern in self.bound_state_allowed_paths:
            if (
                not isinstance(pattern, str)
                or not pattern
                or pattern.startswith("/")
                or ".." in PurePosixPath(pattern).parts
            ):
                raise ValueError("bound-state path patterns must be safe relative paths")

    def _environment(self, *, sandbox_state_root: Path | None = None) -> dict[str, str]:
        env = {"PATH": os.environ.get("PATH", "")}
        for name in self.env_allowlist:
            if name in os.environ:
                env[name] = os.environ[name]
        if sandbox_state_root is not None:
            env[self.BOUND_STATE_ENV] = str(sandbox_state_root)
        return env

    def _ignored(self, relative: str) -> bool:
        parts = PurePosixPath(relative).parts
        return (
            ".git" in parts
            or "__pycache__" in parts
            or relative.endswith(".pyc")
            or relative.startswith(f"{self.RECEIPT_ROOT}/")
            or ".heartbeat-runtime.lock" in parts
        )

    def _snapshot(self, root: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if self._ignored(relative):
                continue
            values[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return values

    def _validate_state_tree(self, root: Path) -> None:
        if not root.exists():
            return
        if root.is_symlink() or not root.is_dir():
            raise RuntimeError("bound state root must be a real directory")
        for path in root.rglob("*"):
            if path.is_symlink():
                raise RuntimeError("bound state tree may not contain symlinks")
            if path.is_dir():
                continue
            if not path.is_file():
                raise RuntimeError("bound state tree contains unsupported filesystem entry")
            relative = path.relative_to(root).as_posix()
            if relative.startswith("/") or ".." in PurePosixPath(relative).parts:
                raise RuntimeError("bound state tree contains unsafe path")

    def _state_snapshot(self, root: Path) -> dict[str, str]:
        self._validate_state_tree(root)
        values: dict[str, str] = {}
        if not root.exists():
            return values
        for path in sorted(root.rglob("*")):
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                values[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return values

    def _path_allowed(self, relative: str, patterns: list[str] | tuple[str, ...]) -> bool:
        if not relative or relative.startswith("/") or ".." in PurePosixPath(relative).parts:
            return False
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                continue
            normalized = pattern.lstrip("./")
            if fnmatch.fnmatchcase(relative, normalized):
                return True
            if normalized.endswith("/**") and relative.startswith(normalized[:-3].rstrip("/") + "/"):
                return True
        return False

    def _validate_fence(self, task: dict[str, Any]) -> tuple[str, int]:
        claim_id = task.get("claim_id")
        timing = task.get("heartbeat_timing") or {}
        fence = timing.get("fencing_token")
        if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int) or fence < 1:
            raise RuntimeError("mutation-capable process worker requires a current fenced claim")
        if not claim_id.endswith(f"-G{fence}"):
            raise RuntimeError("claim/fencing generation mismatch")
        return claim_id, fence

    def _write_scope_receipt(
        self,
        *,
        task: dict[str, Any],
        epoch: int,
        claim_id: str,
        fence: int,
        changed_paths: list[str],
        allowed_paths: list[str],
        decision: str,
        reason: str,
        bound_state_changed_paths: list[str] | None = None,
        bound_state_allowed_paths: list[str] | None = None,
    ) -> str:
        task_id = str(task.get("task_id"))
        receipt = {
            "schema": "stegverse.worker-mutation-scope-receipt/v0.1",
            "task_id": task_id,
            "claim_id": claim_id,
            "fencing_token": fence,
            "heartbeat_epoch": epoch,
            "decision": decision,
            "reason": reason,
            "changed_paths": changed_paths,
            "allowed_paths": allowed_paths,
            "bound_state_enabled": self.bound_state_root is not None,
            "bound_state_changed_paths": bound_state_changed_paths or [],
            "bound_state_allowed_paths": bound_state_allowed_paths or [],
            "bound_state_authoritative_path_exposed_to_worker": False,
            "authority_effect": "none_adapter_scope_enforcement_only",
        }
        digest = hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]
        relative = f"{self.RECEIPT_ROOT}/{task_id}-HB{epoch}-G{fence}-{digest}.json"
        target = self.cwd / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write("\n")
            temp_name = stream.name
        os.replace(temp_name, target)
        return relative

    def _apply_delta(
        self,
        authoritative_root: Path,
        sandbox_root: Path,
        after: dict[str, str],
        changed_paths: list[str],
    ) -> None:
        root = authoritative_root.resolve()
        for relative in changed_paths:
            target = (root / relative).resolve()
            if root != target and root not in target.parents:
                raise RuntimeError("candidate mutation escaped authoritative root")
            source = sandbox_root / relative
            if relative not in after:
                if target.exists():
                    if target.is_symlink() or not target.is_file():
                        raise RuntimeError("refusing non-file bound mutation target")
                    target.unlink()
                continue
            if source.is_symlink() or not source.is_file():
                raise RuntimeError("candidate mutation source must be a regular file")
            target.parent.mkdir(parents=True, exist_ok=True)
            data = source.read_bytes()
            with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as stream:
                stream.write(data)
                temp_name = stream.name
            os.replace(temp_name, target)

    def __call__(self, task: dict[str, Any], handoff: dict[str, Any], epoch: int) -> WorkerResponse:
        claim_id, fence = self._validate_fence(task)
        execution = handoff.get("execution") or {}
        allowed_paths = list(execution.get("allowed_paths") or [])
        required_capabilities = list(execution.get("required_capabilities") or [])
        if not allowed_paths:
            raise RuntimeError("mutation-capable process worker has no admitted path scope")
        if not required_capabilities:
            raise RuntimeError("mutation-capable process worker has no admitted capability scope")

        with tempfile.TemporaryDirectory(prefix="stegverse-worker-sandbox-") as temp_dir:
            temp_root = Path(temp_dir)
            sandbox = temp_root / "workspace"
            shutil.copytree(
                self.cwd,
                sandbox,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".heartbeat-runtime.lock"),
            )
            before = self._snapshot(sandbox)

            sandbox_state: Path | None = None
            state_before: dict[str, str] = {}
            if self.bound_state_root is not None:
                self._validate_state_tree(self.bound_state_root)
                sandbox_state = temp_root / "bound-state"
                if self.bound_state_root.exists():
                    shutil.copytree(self.bound_state_root, sandbox_state)
                else:
                    sandbox_state.mkdir(parents=True, exist_ok=True)
                state_before = self._state_snapshot(sandbox_state)

            payload = {
                "schema": "stegverse.worker-invocation/v0.1",
                "heartbeat_epoch": epoch,
                "task": task,
                "handoff": handoff,
                "scope": {
                    "allowed_paths": allowed_paths,
                    "required_capabilities": required_capabilities,
                    "allowed_services": list(execution.get("allowed_services") or []),
                    "allowed_contracts": list(execution.get("allowed_contracts") or []),
                    "allowed_release_surfaces": list(execution.get("allowed_release_surfaces") or []),
                    "allowed_workflows": list(execution.get("allowed_workflows") or []),
                    "claim_id": claim_id,
                    "fencing_token": fence,
                    "bound_state_enabled": sandbox_state is not None,
                    "bound_state_allowed_paths": list(self.bound_state_allowed_paths),
                    "bound_state_authoritative_path_exposed": False,
                },
                "blocker_policy_ref": "control/blocker-resolution-policy.json",
                "authority_effect": "none_adapter_only",
            }
            completed = subprocess.run(
                self.command,
                cwd=sandbox,
                input=json.dumps(payload, sort_keys=True) + "\n",
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                env=self._environment(sandbox_state_root=sandbox_state),
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip()[-2000:]
                raise RuntimeError(f"worker process exited {completed.returncode}: {stderr}")
            try:
                response = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError("worker process did not emit one valid JSON response") from exc
            if response.get("schema") != "stegverse.worker-response/v0.1":
                raise RuntimeError("unsupported worker response schema")

            validate_worker_response_blocker(response)

            after = self._snapshot(sandbox)
            changed_paths = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
            denied = [path for path in changed_paths if not self._path_allowed(path, allowed_paths)]

            state_after: dict[str, str] = {}
            state_changed_paths: list[str] = []
            state_denied: list[str] = []
            if sandbox_state is not None:
                state_after = self._state_snapshot(sandbox_state)
                state_changed_paths = sorted(
                    path for path in set(state_before) | set(state_after)
                    if state_before.get(path) != state_after.get(path)
                )
                state_denied = [
                    path for path in state_changed_paths
                    if not self._path_allowed(path, self.bound_state_allowed_paths)
                ]

            if denied or state_denied:
                reason = "OUT_OF_SCOPE_MUTATION" if denied else "OUT_OF_SCOPE_BOUND_STATE_MUTATION"
                receipt_ref = self._write_scope_receipt(
                    task=task,
                    epoch=epoch,
                    claim_id=claim_id,
                    fence=fence,
                    changed_paths=changed_paths,
                    allowed_paths=allowed_paths,
                    decision="DENY",
                    reason=reason,
                    bound_state_changed_paths=state_changed_paths,
                    bound_state_allowed_paths=list(self.bound_state_allowed_paths),
                )
                rejected = denied + [f"BOUND_STATE:{path}" for path in state_denied]
                raise RuntimeError(
                    f"worker mutation denied by claim scope; receipt={receipt_ref}; paths={rejected}"
                )

            self._apply_delta(self.cwd, sandbox, after, changed_paths)
            if sandbox_state is not None and self.bound_state_root is not None:
                self.bound_state_root.mkdir(parents=True, exist_ok=True)
                self._apply_delta(
                    self.bound_state_root,
                    sandbox_state,
                    state_after,
                    state_changed_paths,
                )
            receipt_ref = self._write_scope_receipt(
                task=task,
                epoch=epoch,
                claim_id=claim_id,
                fence=fence,
                changed_paths=changed_paths,
                allowed_paths=allowed_paths,
                decision="ALLOW",
                reason="ALL_MUTATIONS_WITHIN_CURRENT_FENCED_SCOPE",
                bound_state_changed_paths=state_changed_paths,
                bound_state_allowed_paths=list(self.bound_state_allowed_paths),
            )

        state = str(response.get("state", ""))
        transition_id = str(response.get("transition_id", ""))
        transition_sequence = response.get("transition_sequence")
        if not state or not transition_id or not isinstance(transition_sequence, int) or transition_sequence < 0:
            raise RuntimeError("worker response missing state/transition_id/transition_sequence")

        evidence_refs = response.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or any(not isinstance(ref, str) for ref in evidence_refs):
            raise RuntimeError("worker response evidence_refs must be strings")
        if receipt_ref not in evidence_refs:
            evidence_refs.append(receipt_ref)
        cost = response.get("cost_observation")
        if cost is not None and not isinstance(cost, dict):
            raise RuntimeError("worker response cost_observation must be an object")

        return WorkerResponse(
            state=state,
            transition_id=transition_id,
            transition_sequence=transition_sequence,
            expected_next_transition=response.get("expected_next_transition"),
            expected_next_earliest_epoch=response.get("expected_next_earliest_epoch"),
            expected_next_latest_epoch=response.get("expected_next_latest_epoch"),
            checkpoint_ref=response.get("checkpoint_ref"),
            evidence_refs=tuple(evidence_refs),
            cost_observation=cost,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "adapter_type": (
                "process_json_bound_state_v0.1" if self.bound_state_root is not None else "process_json_v0.1"
            ),
            "command": list(self.command),
            "cwd": str(self.cwd),
            "timeout_seconds": self.timeout_seconds,
            "env_allowlist": list(self.env_allowlist),
            "task_controls_command": False,
            "adapter_grants_authority": False,
            "worker_mutates_authoritative_workspace_directly": False,
            "sandbox_delta_scope_enforcement": True,
            "claim_fence_required_before_commit": True,
            "blocked_requires_resolution_contract": True,
            "third_party_dependency_may_block": False,
            "bound_state_enabled": self.bound_state_root is not None,
            "bound_state_allowed_paths": list(self.bound_state_allowed_paths),
            "bound_state_authoritative_path_exposed_to_worker": False,
            "blocker_policy_ref": "control/blocker-resolution-policy.json",
        }
