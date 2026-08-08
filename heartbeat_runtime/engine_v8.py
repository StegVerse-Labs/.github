from __future__ import annotations

from typing import Any

from .engine_v7_1 import HeartbeatRuntime as HeartbeatRuntimeV7, WorkerResponse


class HeartbeatRuntime(HeartbeatRuntimeV7):
    """Single-heartbeat runtime with canonical worker capability profiles."""

    def _capability_profile(self, worker: dict[str, Any]) -> dict[str, Any] | None:
        ref = worker.get("capability_profile_ref")
        if not isinstance(ref, str) or "#" not in ref:
            return None
        path_ref, profile_id = ref.split("#", 1)
        path = self.root / path_ref
        if not path.exists() or not profile_id:
            return None
        try:
            registry = self._load(path)
        except Exception:
            return None
        if registry.get("schema") != "stegverse.worker-capability-profiles/v0.1":
            return None
        return next((item for item in registry.get("profiles", []) if item.get("profile_id") == profile_id), None)

    def _worker_profile_valid(self, worker: dict[str, Any], required: set[str]) -> bool:
        profile = self._capability_profile(worker)
        if profile is None:
            return False
        worker_caps = set(worker.get("capabilities") or [])
        allowed = set(profile.get("allowed_capabilities") or [])
        if profile.get("executor_type") != worker.get("executor_type"):
            return False
        if profile.get("availability_grants_authority") is not False:
            return False
        if profile.get("capability_match_grants_authority") is not False:
            return False
        if not worker_caps.issubset(allowed):
            return False
        if not required.issubset(worker_caps):
            return False
        if any(cap.startswith("deployment_") for cap in required) and profile.get("deployment_allowed") is not True:
            return False
        mutation_markers = {"github_repository_write", "code_and_schema_implementation", "bounded_repository_mutation", "deployment_update", "deployment_release"}
        if required.intersection(mutation_markers) and profile.get("mutation_allowed") is not True:
            return False
        return True

    def _worker_for(self, task: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any] | None:
        handoff = self._handoff(task)
        if self._synthetic_fixture_compat(handoff):
            return super()._worker_for(task, registry)
        required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
        matches: list[dict[str, Any]] = []
        for worker in sorted(registry.get("workers", []), key=lambda item: item["worker_id"]):
            adapter_ref = worker.get("adapter_ref")
            if worker.get("status") != "AVAILABLE" or not adapter_ref or adapter_ref not in self.adapters:
                continue
            if self._worker_profile_valid(worker, required):
                matches.append(worker)
        # Capability/profile matching establishes eligibility only. Ambiguity still
        # fails closed and execution authorization is checked separately upstream.
        if len(matches) != 1:
            return None
        return matches[0]


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
