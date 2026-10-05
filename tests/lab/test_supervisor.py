"""Bounded supervisor behavior independent of external service availability."""

import json

import pytest

from robotops.lab.config import LabConfig
from tools.lab_stack import LabStack


def test_monitor_recovers_from_one_transient_health_failure(tmp_path, monkeypatch, capsys):
    stack = LabStack(LabConfig(postgres_dsn="unused", amqp_url="unused"), tmp_path)
    responses = iter([False, True])

    def healthy():
        try:
            return next(responses)
        except StopIteration:
            raise KeyboardInterrupt from None

    stack.health_failures = {"api": "ReadTimeout"}
    monkeypatch.setattr(stack, "healthy", healthy)
    monkeypatch.setattr("tools.lab_stack.time.sleep", lambda _: None)
    with pytest.raises(KeyboardInterrupt):
        stack.monitor()
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert reports[0]["status"] == "degraded"
    assert reports[0]["failures"] == {"api": "ReadTimeout"}
    assert reports[1]["status"] == "health_restored"


def test_monitor_stops_after_bounded_sustained_failure(tmp_path, monkeypatch, capsys):
    stack = LabStack(LabConfig(postgres_dsn="unused", amqp_url="unused"), tmp_path)
    stack.health_failures = {"broker_consumer": "HEARTBEAT_OLDER_THAN_15_SECONDS"}
    clock = iter([0, 10, 31])
    monkeypatch.setattr(stack, "healthy", lambda: False)
    monkeypatch.setattr("tools.lab_stack.time.sleep", lambda _: None)
    monkeypatch.setattr("tools.lab_stack.time.monotonic", lambda: next(clock))
    with pytest.raises(RuntimeError, match="LAB_HEALTH_LOST.*broker_consumer"):
        stack.monitor()
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(reports) == 3
    assert reports[-1]["duration_seconds"] == 31
