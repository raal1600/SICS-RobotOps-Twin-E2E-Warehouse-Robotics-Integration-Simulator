import subprocess

import pytest

from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import CommunicationTimeout


@pytest.mark.parametrize("record_existing", [False, True])
@pytest.mark.parametrize(
    ("stdout", "stderr", "expected"),
    [
        (
            "Saved scene.blend",
            "Cycles render initializing",
            ("Saved scene.blend", "Cycles render initializing"),
        ),
        (
            b"Frame 133 complete\xff",
            b"CPU render stalled",
            ("Frame 133 complete\ufffd", "CPU render stalled"),
        ),
        (None, None, ()),
    ],
)
def test_blender_timeout_retains_partial_diagnostics_without_claiming_effect(
    tmp_path, monkeypatch, record_existing, stdout, stderr, expected
):
    monkeypatch.setattr("robotops.blender.adapter.executable", lambda: "blender-not-invoked")
    runtime = BlenderRuntime(tmp_path / "runtime.db")
    original_world = runtime.world()
    directory = tmp_path / "exchange"
    directory.mkdir()
    invocations = []

    def timeout(args, **kwargs):
        invocations.append((args, kwargs))
        raise subprocess.TimeoutExpired(args, kwargs["timeout"], output=stdout, stderr=stderr)

    monkeypatch.setattr("robotops.blender.adapter.subprocess.run", timeout)
    with pytest.raises(CommunicationTimeout, match="BLENDER_PROCESS_TIMEOUT") as failure:
        runtime._invoke(directory, record_existing=record_existing)
    assert isinstance(failure.value.__cause__, subprocess.TimeoutExpired)
    assert len(invocations) == 1
    args, options = invocations[0]
    assert options["timeout"] == runtime.settings.runtime_timeout_seconds == 60
    assert ("--record-existing" in args) is record_existing
    log_name = "replay.log" if record_existing else "runtime.log"
    log = (directory / log_name).read_text(encoding="utf-8")
    assert "timed out after" in log
    for message in expected:
        assert message in log
    assert not (directory / ("runtime.log" if record_existing else "replay.log")).exists()
    assert runtime.world() == original_world
    assert runtime.events() == []
    assert not (directory / "response.json").exists()
