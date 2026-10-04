"""Capture unmodified v1 compatibility evidence without touching tracked source."""

import hashlib
import importlib.metadata
import json
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from robotops.brain.deterministic import DeterministicBrain
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import ActionPlan, Fault, JobState, OrderLine, OrderRequest, RobotCommand, Verdict, utc_now
from robotops.observation.model import ObservationModel
from robotops.scene_geometry import cell_meshes
from robotops.verification.verifier import Verifier
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store, digest

EXPECTED_HEAD = "eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98"
OUT = ROOT / "artifacts/hkm-baseline-eaf35b4/legacy-golden"
if OUT.exists():
    raise RuntimeError("Refusing to overwrite historical compatibility evidence")
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
assert head == EXPECTED_HEAD, head
source_files = [
    "robotops/domain/models.py", "robotops/config.py", "robotops/cell/runtime.py",
    "robotops/workflow/store.py", "robotops/workflow/engine.py", "robotops/workflow/states.py",
    "robotops/brain/deterministic.py", "robotops/brain/validation.py", "robotops/observation/model.py",
    "robotops/observation/quality.py", "robotops/verification/verifier.py", "robotops/scene_geometry.py",
    "robotops/robot_gateway/gateway.py", "robotops/blender/visualization.py", "uv.lock",
]
subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *source_files], cwd=ROOT, check=True)
OUT.mkdir(parents=True)


def save(name, value):
    content = value.model_dump_json(indent=2) if hasattr(value, "model_dump_json") else json.dumps(value, indent=2)
    (OUT / name).write_text(content + "\n", encoding="utf-8")


runtime = SyntheticRuntime(OUT / "execution/runtime.db")
store = Store(OUT / "execution/workflow.db")
engine = Engine(store, runtime)
before = runtime.world()
save("world-before.json", before)
save("scene-before.json", cell_meshes(before.model_dump(mode="json")))
save("settings.json", runtime.settings)
request = OrderRequest(
    order_id="legacy-golden-order",
    lines=(OrderLine(order_line_id="legacy-golden-line", product_id="product-red", source_id="source", destination_id="destination"),),
)
save("order-request.json", request)
order = store.intake(request, "legacy-golden-idempotency-key")
job = engine.run(order.job_ids[0], Fault.DROP_ACK_AFTER_EFFECT)
assert job.state == JobState.UNKNOWN_OUTCOME
assert job.command_id is not None and job.action_plan_id is not None
command = store.load(RobotCommand, job.command_id)
plan = store.load(ActionPlan, job.action_plan_id)
receipt = runtime.recorded_journal(command.command_id)
assert receipt is not None
after = runtime.world()
assert after.objects[0].location_id == "destination"
assert after.step == before.step + 1
assert receipt.effect_count == 1
assert receipt.payload_hash == digest(command)
assert sum(event.event_type == "PICK_EFFECT" for event in runtime.events()) == 1
save("world-after.json", after)
save("action-plan.json", plan)
save("robot-command.json", command)
(OUT / "robot-command-original-wire.json").write_text(command.model_dump_json(), encoding="utf-8")
save("receipt.json", receipt)
save("job-unknown.json", job)
save("order-unknown.json", store.order(order.order_id))
save("workflow-events.json", [event.model_dump(mode="json") for event in store.timeline()])
save("runtime-events.json", [event.model_dump(mode="json") for event in runtime.events()])

observer = ObservationModel(runtime.settings)
verifier = Verifier(runtime.settings)
for name, fault, expected in [
    ("normal", None, Verdict.VERIFIED_SUCCESS),
    ("contradictory", Fault.CONTRADICTORY_OBSERVATION, Verdict.INCONCLUSIVE),
]:
    observation = observer.observe(after, fault).model_copy(update={
        "run_id": job.run_id, "correlation_id": job.correlation_id, "causation_id": command.command_id,
    })
    verdict = verifier.verify(command, observation, receipt)
    assert verdict.verdict == expected, verdict
    save(f"observation-{name}.json", observation)
    save(f"verification-{name}.json", verdict)

# Neither offline assessment resolves the workflow. These snapshots must remain
# unknown so a later implementation can reconcile the ORIGINAL persisted command.
assert store.job(job.job_id).state == JobState.UNKNOWN_OUTCOME
snapshot = OUT / "restart-snapshot"
snapshot.mkdir()
for source in (runtime.db.path, store.path):
    with sqlite3.connect(source) as source_db, sqlite3.connect(snapshot / source.name) as destination_db:
        source_db.backup(destination_db)

with sqlite3.connect(snapshot / "runtime.db") as db:
    journal = db.execute("SELECT payload_hash,command,receipt FROM controller_journal WHERE id=?", (command.command_id,)).fetchone()
    assert journal is not None and journal[0] == digest(command)
    assert journal[1] == command.model_dump_json()
    save("controller-row.json", {"payload_hash": journal[0], "command_wire": journal[1], "receipt_wire": journal[2]})
with sqlite3.connect(snapshot / "workflow.db") as db:
    assert db.execute("SELECT state FROM jobs WHERE id=?", (job.job_id,)).fetchone()[0] == "UNKNOWN_OUTCOME"

files = {
    path.relative_to(OUT).as_posix(): {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    for path in sorted(OUT.rglob("*")) if path.is_file() and not path.name.endswith(("-wal", "-shm"))
}
manifest = {
    "purpose": "PRE-UPGRADE v1 golden compatibility evidence; isolated synthetic runtime; no user data",
    "captured_at_utc": utc_now().isoformat(),
    "source_commit": head,
    "execution_sources_clean": True,
    "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files},
    "python": sys.version,
    "platform": platform.platform(),
    "pydantic": importlib.metadata.version("pydantic"),
    "runtime": "SyntheticRuntime",
    "schema_version": "1.0",
    "command_id": command.command_id,
    "command_digest": digest(command),
    "job_id": job.job_id,
    "order_id": order.order_id,
    "scene_epoch": after.scene_epoch,
    "workflow_state": job.state,
    "pick_effect_count": 1,
    "normal_verdict": "VERIFIED_SUCCESS",
    "contradictory_verdict": "INCONCLUSIVE",
    "restart_snapshot": "restart-snapshot",
    "notes": "Offline verifier checks did not mutate workflow. Copy restart-snapshot before exercising upgraded recovery; never modify these originals. Observation freshness expires; upgraded recovery must collect new evidence.",
    "files": files,
}
save("manifest.json", manifest)
print(json.dumps({key: manifest[key] for key in ["source_commit", "command_id", "command_digest", "job_id", "workflow_state", "pick_effect_count", "normal_verdict", "contradictory_verdict"]}, indent=2))
print(str(OUT / "manifest.json"))
