"""Compatibility import path for the canonical admitted WorkerCoordinator.

The pre-admission implementation is retained as worker_runtime_legacy.py for
internal inheritance only. All normal imports through heartbeat_runtime.worker_runtime
now receive the mandatory Worker Task Admission Packet gate.
"""
from .admitted_worker_runtime import WorkerCoordinator
from .worker_runtime_legacy import ProcessWorkerAdapter, WorkerResponse

__all__ = ["WorkerCoordinator", "ProcessWorkerAdapter", "WorkerResponse"]
