"""Input data for registration receipts sealed against generation 326.

The archive comes from git archive of 9bd59fd676345a9833d2266216a70dd76e1610e4.
It contains the aggregate, records, task vectors, index shards, goal seals, allocation
requests, global invariants and check-in caller policy. Candidate code and schemas
remain under test, and the live-base/successor verification never uses this helper.
"""
import atexit
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory


@lru_cache(maxsize=1)
def registration_predecessor_326():
    root = Path(__file__).resolve().parents[1]
    archive = root / "tests/fixtures/canonical_task_registration/predecessor-326.tar.gz"
    if sha256(archive.read_bytes()).hexdigest() != "3cd4d137fe0cc98779f7ba41b4cf3305b3994d87552ae87cfbab7d4eb05a5af5":
        raise ValueError("generation 326 fixture digest mismatch")
    temp = TemporaryDirectory(prefix="registration-predecessor-326-")
    atexit.register(temp.cleanup)
    predecessor = Path(temp.name)
    with tarfile.open(archive, "r:gz") as inputs:
        inputs.extractall(predecessor, filter="data")
    for directory in ("schemas", "scripts"):
        (predecessor / directory).symlink_to(root / directory, target_is_directory=True)
    return predecessor

# Reproduce the committed input archive from the repository root:
# git archive --format=tar.gz --output=/tmp/predecessor-326.tar.gz \
#   9bd59fd676345a9833d2266216a70dd76e1610e4 data/canonical-task-registry.json \
#   data/canonical-task-records data/task-registry-general-checkin-caller-policy.json \
#   data/task-registry-global-invariants.json control/task-vectors \
#   control/task-vector-index.d control/goal-scope-seals control/goal-task-allocation-requests
