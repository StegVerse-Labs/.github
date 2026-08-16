"""StegVerse heartbeat carrier and worker coordination primitives.

`CarrierHeartbeatRuntime` is the canonical non-authorizing production carrier.
`WorkerCoordinator` is the separated worker/control-plane runtime. The historical
package-level `HeartbeatRuntime` remains the versioned-v11 compatibility API for
existing worker/control-plane consumers; production deployment never uses that
alias and selects engine v12 explicitly.
"""

from .engine_v12 import HeartbeatRuntime as CarrierHeartbeatRuntime
from .engine_v11 import HeartbeatRuntime, WorkerResponse
from .worker_runtime import WorkerCoordinator
from .process_adapter import ProcessWorkerAdapter

__all__ = [
    "HeartbeatRuntime",
    "CarrierHeartbeatRuntime",
    "WorkerCoordinator",
    "WorkerResponse",
    "ProcessWorkerAdapter",
]
