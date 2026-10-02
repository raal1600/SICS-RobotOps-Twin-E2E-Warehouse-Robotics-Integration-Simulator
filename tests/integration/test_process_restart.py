import subprocess
import sys
from datetime import timedelta

from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import JobState, utc_now
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_process_dies_after_effect_before_orchestrator_receipt(tmp_path):
    script = """
import os,sys
from pathlib import Path
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import OrderRequest,OrderLine
from robotops.workflow.store import Store
from robotops.workflow.engine import Engine
class CrashRuntime(SyntheticRuntime):
    def apply(self, command, fault=None):
        super().apply(command,fault)
        os._exit(17)
p=Path(sys.argv[1])
s=Store(p/'workflow.db')
e=Engine(s,CrashRuntime(p/'runtime.db'))
o=s.intake(OrderRequest(order_id='crash-order',lines=(OrderLine(order_line_id='line',
    product_id='product-red',source_id='source',destination_id='destination'),)),'key')
e.run(o.job_ids[0])
"""
    child = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)], capture_output=True, text=True
    )
    assert child.returncode == 17, child.stderr
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job = store.recoverable()[0]
    assert job.state == JobState.EXECUTING
    command_id = job.command_id
    assert engine.recover()[0].state == JobState.EXECUTING  # live lease is respected
    assert sum(e.event_type == "PICK_EFFECT" for e in runtime.events()) == 1
    # Deterministically model lease time elapsing after the child is confirmed dead.
    with store.transaction() as db:
        db.execute("UPDATE lease SET expires=?", ((utc_now() - timedelta(seconds=1)).isoformat(),))
    assert engine.recover()[0].state == JobState.COMPLETED
    assert store.job(job.job_id).command_id == command_id
    assert sum(e.event_type == "PICK_EFFECT" for e in runtime.events()) == 1
    assert not any(e.event_type == "DUPLICATE_SUPPRESSED" for e in runtime.events())
