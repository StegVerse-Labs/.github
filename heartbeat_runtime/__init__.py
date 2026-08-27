"""StegVerse heartbeat carrier and worker coordination primitives.

`CarrierHeartbeatRuntime` is the canonical non-authorizing production carrier.
`WorkerCoordinator` is the separated worker/control-plane runtime with mandatory
pre-initiation Worker Task Admission Packet review. The historical package-level
`HeartbeatRuntime` remains the versioned-v11 compatibility API for existing
worker/control-plane consumers; production deployment selects the fragment-aware
separated carrier explicitly.
"""

from .engine_v13 import HeartbeatRuntime as CarrierHeartbeatRuntime
from .engine_v11 import HeartbeatRuntime, WorkerResponse
from .admitted_worker_runtime import WorkerCoordinator
from .process_adapter import ProcessWorkerAdapter
from .governed_manifold import GovernedProjectionDimension, governed_manifold_observation

__all__ = [
    "HeartbeatRuntime",
    "CarrierHeartbeatRuntime",
    "WorkerCoordinator",
    "WorkerResponse",
    "ProcessWorkerAdapter",
    "GovernedProjectionDimension",
    "governed_manifold_observation",
]
