from __future__ import annotations

from typing import Any

from .engine_v5 import HeartbeatRuntime as HeartbeatRuntimeV5, WorkerResponse


class HeartbeatRuntime(HeartbeatRuntimeV5):
    """Single-heartbeat runtime with persistent bounded resource authority."""

    def _ensure_resource_budget(self, task: dict[str, Any], handoff: dict[str, Any]) -> dict[str, Any]:
        existing = task.get("resource_budget")
        if isinstance(existing, dict):
            return existing
        execution = handoff.get("execution") or {}
        # Historical synthetic fixtures exercise lower layers and predate #21.
        synthetic = self._synthetic_fixture_compat(handoff)
        budget = {
            "max_actions": int(execution.get("max_actions", 100 if synthetic else 1)),
            "max_retries": int(execution.get("max_retries", 10 if synthetic else 0)),
            "external_cost_ceiling_usd": float(execution.get("external_cost_ceiling_usd", 0)),
            "runtime_window_beats": int(execution.get("runtime_window_beats", 100 if synthetic else 1)),
            "rate_class": str(execution.get("rate_class", "synthetic_fixture" if synthetic else "unspecified")),
            "allowed_services": list(execution.get("allowed_services") or []),
            "actions_used": 0,
            "retries_used": 0,
            "external_cost_usd": 0.0,
            "renewal_count": 0,
        }
        task["resource_budget"] = budget
        return budget

    def _expiry_budget(self, task: dict[str, Any]) -> tuple[int | None, str]:
        budget, basis = super()._expiry_budget(task)
        if budget is None:
            return None, basis
        handoff = self._handoff(task)
        execution = handoff.get("execution") or {}
        window = execution.get("runtime_window_beats")
        if isinstance(window, int) and window > 0:
            return min(int(budget), window), basis
        return budget, basis

    def _apply_admitted_renewal(self, task: dict[str, Any], handoff: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> bool:
        renewal_ref = task.get("renewal_ref")
        record = None
        if isinstance(renewal_ref, str) and renewal_ref:
            path = self.root / renewal_ref
            if path.exists():
                try:
                    record = self._load(path)
                except Exception:
                    record = None
        applied = super()._apply_admitted_renewal(task, handoff, epoch, events)
        if not applied or not isinstance(record, dict):
            return applied
        budget = self._ensure_resource_budget(task, handoff)
        budget["max_actions"] += int(record.get("additional_actions", 0) or 0)
        budget["max_retries"] += int(record.get("additional_retries", 0) or 0)
        budget["external_cost_ceiling_usd"] += float(record.get("additional_external_cost_usd", 0) or 0)
        budget["runtime_window_beats"] += int(record.get("additional_beats", 0) or 0)
        budget["renewal_count"] = int(budget.get("renewal_count", 0)) + 1
        task["resource_budget"] = budget
        task["archive_reason_codes"] = [
            code for code in task.get("archive_reason_codes", [])
            if not code.startswith("RESOURCE_")
        ]
        if task.get("state") == "EXPIRING":
            task["state"] = "ACTIVE"
        self._event(
            events,
            epoch,
            "resource_authority_renewed",
            task_id=task.get("task_id"),
            renewal_ref=renewal_ref,
            max_actions=budget["max_actions"],
            max_retries=budget["max_retries"],
            external_cost_ceiling_usd=budget["external_cost_ceiling_usd"],
            heartbeat_granted_renewal=False,
        )
        return True

    def _resource_exhaustion_reason(self, budget: dict[str, Any]) -> str | None:
        if int(budget.get("actions_used", 0)) >= int(budget.get("max_actions", 0)):
            return "RESOURCE_ACTION_LIMIT_REACHED"
        if int(budget.get("retries_used", 0)) > int(budget.get("max_retries", 0)):
            return "RESOURCE_RETRY_LIMIT_EXCEEDED"
        if float(budget.get("external_cost_usd", 0)) > float(budget.get("external_cost_ceiling_usd", 0)):
            return "RESOURCE_EXTERNAL_COST_CEILING_EXCEEDED"
        return None

    def _hold_for_resource_renewal(self, task: dict[str, Any], epoch: int, events: list[dict[str, Any]], reason: str) -> None:
        task["state"] = "EXPIRING"
        task["archive_eligible"] = False
        task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + [reason, "RESOURCE_AUTHORIZATION_RENEWAL_REQUIRED"]))
        self._event(
            events,
            epoch,
            "resource_authority_exhausted",
            task_id=task.get("task_id"),
            claim_id=task.get("claim_id"),
            fencing_token=(task.get("heartbeat_timing") or {}).get("fencing_token"),
            reason=reason,
            heartbeat_grants_renewal=False,
        )

    def _quarantine_resource_violation(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, events: list[dict[str, Any]], reason: str, **details: Any) -> None:
        old_claim = task.get("claim_id")
        old_fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
        self._release_worker(registry, task)
        task["state"] = "QUARANTINED"
        task["archive_eligible"] = False
        task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + [reason]))
        self._event(events, epoch, "resource_authority_violation", task_id=task.get("task_id"), released_claim_id=old_claim, fencing_token=old_fence, reason=reason, **details)

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        handoff = self._handoff(task)
        budget = self._ensure_resource_budget(task, handoff)
        self._apply_admitted_renewal(task, handoff, epoch, events)
        budget = self._ensure_resource_budget(task, handoff)

        timing = task.get("heartbeat_timing") or {}
        expiry_epoch = timing.get("expiry_epoch")
        if isinstance(expiry_epoch, int) and epoch >= expiry_epoch:
            super()._invoke(registry, task, epoch, cost_log, events)
            return

        exhausted = self._resource_exhaustion_reason(budget)
        if exhausted:
            self._hold_for_resource_renewal(task, epoch, events, exhausted)
            return

        worker = next((item for item in registry.get("workers", []) if item.get("worker_id") == task.get("worker_id")), None)
        adapter_ref = worker.get("adapter_ref") if worker else None
        adapter_present = bool(adapter_ref and adapter_ref in self.adapters)
        before_cost_records = len(cost_log.get("records", []))
        if adapter_present:
            budget["actions_used"] = int(budget.get("actions_used", 0)) + 1
            task["resource_budget"] = budget

        super()._invoke(registry, task, epoch, cost_log, events)

        # Only successful worker responses can declare retry/cost/service observations.
        responded = (task.get("heartbeat_timing") or {}).get("last_response_epoch") == epoch
        if responded and task.get("state") == "FAILED_RETRYABLE":
            budget["retries_used"] = int(budget.get("retries_used", 0)) + 1

        new_records = cost_log.get("records", [])[before_cost_records:]
        for record in new_records:
            if record.get("task_id") != task.get("task_id") or record.get("heartbeat_epoch") != epoch:
                continue
            cost = record.get("cost") or {}
            external = cost.get("external_cost_usd", 0)
            if isinstance(external, (int, float)):
                budget["external_cost_usd"] = float(budget.get("external_cost_usd", 0)) + float(external)
            services = cost.get("services_used") or []
            if isinstance(services, list):
                unadmitted = sorted(set(str(service) for service in services) - set(budget.get("allowed_services") or []))
                if unadmitted:
                    task["resource_budget"] = budget
                    self._quarantine_resource_violation(registry, task, epoch, events, "RESOURCE_SERVICE_SCOPE_VIOLATION", unadmitted_services=unadmitted)
                    return

        task["resource_budget"] = budget
        if float(budget.get("external_cost_usd", 0)) > float(budget.get("external_cost_ceiling_usd", 0)):
            self._quarantine_resource_violation(registry, task, epoch, events, "RESOURCE_EXTERNAL_COST_CEILING_EXCEEDED", observed_external_cost_usd=budget["external_cost_usd"], ceiling_usd=budget["external_cost_ceiling_usd"])
            return

        exhausted_after = self._resource_exhaustion_reason(budget)
        if exhausted_after and task.get("state") not in {"COMPLETED", "HANDOFF_READY", "FAILED_TERMINAL", "QUARANTINED"}:
            self._hold_for_resource_renewal(task, epoch, events, exhausted_after)

    def _activate_one(self, registry: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        activated = super()._activate_one(registry, epoch, cost_log, events)
        for task in registry.get("tasks", []):
            timing = task.get("heartbeat_timing") or {}
            if timing.get("start_epoch") == epoch:
                self._ensure_resource_budget(task, self._handoff(task))
        return activated


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
