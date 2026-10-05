"""Transactional outbox, publisher confirms and durable edge inbox using real services."""

import json
import time
from collections.abc import Callable
from typing import Any

import httpx
import pika  # type: ignore[import-untyped]
import psycopg
from psycopg.rows import dict_row

from robotops.domain.models import RobotCommand
from robotops.domain.ports import Runtime
from robotops.lab.config import LabConfig
from robotops.lab.edge_rpc import EdgeRPC
from robotops.workflow.store import Conflict, digest


class DeliveryStore:
    def __init__(self, config: LabConfig):
        self.config = config
        with self.connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(74829304)")
            db.execute("""
                CREATE TABLE IF NOT EXISTS lab_outbox (
                    command_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, payload TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
                    confirmed_at TIMESTAMPTZ);
                CREATE TABLE IF NOT EXISTS lab_inbox (
                    command_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, payload TEXT NOT NULL,
                    deliveries INTEGER NOT NULL DEFAULT 1, redelivered BOOLEAN NOT NULL DEFAULT FALSE,
                    ack_sent BOOLEAN NOT NULL DEFAULT FALSE, received_at TIMESTAMPTZ DEFAULT now());
                CREATE TABLE IF NOT EXISTS lab_edge_health (
                    queue TEXT PRIMARY KEY, heartbeat TIMESTAMPTZ NOT NULL);
                CREATE TABLE IF NOT EXISTS lab_protocol_events (
                    sequence BIGSERIAL PRIMARY KEY, command_id TEXT NOT NULL,
                    body TEXT NOT NULL);
            """)

    def connect(self) -> psycopg.Connection[dict[str, Any]]:
        return psycopg.connect(self.config.postgres_dsn, row_factory=dict_row, connect_timeout=10)

    def enqueue(self, payload: dict[str, Any]) -> dict[str, Any]:
        command = RobotCommand.model_validate(payload)
        hashed = digest(command)
        with self.connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(74829301)")
            previous = db.execute(
                "SELECT * FROM lab_outbox WHERE command_id=%s", (command.command_id,)
            ).fetchone()
            if previous and previous["payload_hash"] != hashed:
                raise Conflict("COMMAND_ID_PAYLOAD_CONFLICT")
            # Intent and immutable dispatch payload commit atomically before AMQP.
            db.execute(
                "INSERT INTO lab_outbox(command_id,payload_hash,payload) VALUES (%s,%s,%s) "
                "ON CONFLICT DO NOTHING",
                (command.command_id, hashed, command.model_dump_json()),
            )
        return {
            "command_id": command.command_id,
            "payload_hash": hashed,
            "state": previous["state"] if previous else "PENDING",
            "protocol": "SQL",
            "classification": "REAL PROTOCOL",
            "persistence": "PostgreSQL transactional outbox committed",
            "network_effect": False,
        }

    def outbox(self, command_id: str) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM lab_outbox WHERE command_id=%s", (command_id,)
            ).fetchone()
        if row is None:
            raise Conflict("OUTBOX_INTENT_MISSING")
        return row

    def inbox(self, command_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM lab_inbox WHERE command_id=%s", (command_id,)
            ).fetchone()

    def protocol_event(self, command_id: str, event: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO lab_protocol_events(command_id,body) VALUES (%s,%s)",
                (command_id, json.dumps(event)),
            )

    def protocol_events(self, command_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [
                {"sequence": row["sequence"], **json.loads(row["body"])}
                for row in db.execute(
                    "SELECT sequence,body FROM lab_protocol_events WHERE command_id=%s "
                    "ORDER BY sequence",
                    (command_id,),
                ).fetchall()
            ]


def broker(config: LabConfig) -> Any:
    parameters = pika.URLParameters(config.amqp_url)
    parameters.socket_timeout = config.timeout
    parameters.stack_timeout = config.timeout * 2
    parameters.blocked_connection_timeout = config.timeout
    return pika.BlockingConnection(parameters)


def topology(channel: Any, config: LabConfig) -> None:
    channel.exchange_declare(exchange=config.exchange, exchange_type="direct", durable=True)
    channel.queue_declare(queue=config.queue, durable=True)
    channel.queue_bind(queue=config.queue, exchange=config.exchange, routing_key=config.routing_key)


class EdgeAdapter:
    """Consumption only retains intent; SubmitJob is a later explicit trust gate."""

    def __init__(self, config: LabConfig):
        self.config = config
        self.store = DeliveryStore(config)

    def consume_one(self, *, lose_ack: bool = False) -> dict[str, Any] | None:
        try:
            connection = broker(self.config)
        except pika.exceptions.AMQPError:
            raise OSError("BROKER_UNAVAILABLE_INBOX_RETAINED") from None
        try:
            channel = connection.channel()
            topology(channel, self.config)
            channel.basic_qos(prefetch_count=1)
            delivery, properties, body = channel.basic_get(queue=self.config.queue, auto_ack=False)
            with self.store.connect() as db:
                db.execute(
                    "INSERT INTO lab_edge_health VALUES (%s,now()) "
                    "ON CONFLICT(queue) DO UPDATE SET heartbeat=excluded.heartbeat",
                    (self.config.queue,),
                )
            if delivery is None:
                return None
            try:
                command = RobotCommand.model_validate_json(body)
                if properties.message_id != command.command_id:
                    raise Conflict("AMQP_MESSAGE_IDENTITY_MISMATCH")
                hashed = digest(command)
                with self.store.connect() as db:
                    db.execute("SELECT pg_advisory_xact_lock(74829302)")
                    existing = db.execute(
                        "SELECT * FROM lab_inbox WHERE command_id=%s", (command.command_id,)
                    ).fetchone()
                    if existing and existing["payload_hash"] != hashed:
                        raise Conflict("COMMAND_ID_PAYLOAD_CONFLICT")
                    db.execute(
                        "INSERT INTO lab_inbox(command_id,payload_hash,payload,redelivered) "
                        "VALUES (%s,%s,%s,%s) ON CONFLICT(command_id) DO UPDATE SET "
                        "deliveries=lab_inbox.deliveries+1,redelivered=excluded.redelivered,"
                        "ack_sent=FALSE",
                        (
                            command.command_id,
                            hashed,
                            command.model_dump_json(),
                            delivery.redelivered,
                        ),
                    )
            except (ValueError, Conflict):
                channel.basic_nack(delivery_tag=delivery.delivery_tag, requeue=False)
                raise
            if lose_ack:
                return {
                    "command_id": command.command_id,
                    "consumer_ack_sent": False,
                    "reason": "FAULT_CONNECTION_CLOSED_AFTER_INBOX_COMMIT",
                }
            channel.basic_ack(delivery_tag=delivery.delivery_tag)
            with self.store.connect() as db:
                db.execute(
                    "UPDATE lab_inbox SET ack_sent=TRUE WHERE command_id=%s", (command.command_id,)
                )
            return {
                "command_id": command.command_id,
                "consumer_ack_sent": True,
                "redelivered": delivery.redelivered,
                "durable_inbox_committed": True,
            }
        except pika.exceptions.AMQPError:
            raise OSError("BROKER_UNAVAILABLE_INBOX_RETAINED") from None
        finally:
            if connection.is_open:
                connection.close()


class LabBridge:
    def __init__(self, config: LabConfig, runtime: Runtime | None = None):
        self.config = config
        self.runtime = runtime
        self.store = DeliveryStore(config)
        self.opc = EdgeRPC(config)

    def enqueue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.store.enqueue(payload)

    def publish(self, command_id: str) -> dict[str, Any]:
        row = self.store.outbox(command_id)
        try:
            connection = broker(self.config)
        except pika.exceptions.AMQPError:
            raise OSError("BROKER_UNAVAILABLE_OUTBOX_RETAINED") from None
        try:
            channel = connection.channel()
            topology(channel, self.config)
            channel.confirm_delivery()
            with self.store.connect() as db:
                db.execute(
                    "UPDATE lab_outbox SET attempts=attempts+1 WHERE command_id=%s", (command_id,)
                )
            channel.basic_publish(
                exchange=self.config.exchange,
                routing_key=self.config.routing_key,
                body=row["payload"].encode(),
                mandatory=True,
                properties=pika.BasicProperties(
                    message_id=command_id, delivery_mode=2, content_type="application/json"
                ),
            )
            with self.store.connect() as db:
                db.execute(
                    "UPDATE lab_outbox SET state='CONFIRMED',confirmed_at=now() "
                    "WHERE command_id=%s",
                    (command_id,),
                )
        except pika.exceptions.AMQPError:
            raise OSError("BROKER_UNAVAILABLE_OUTBOX_RETAINED") from None
        finally:
            if connection.is_open:
                connection.close()
        return {
            "command_id": command_id,
            "message_id": command_id,
            "exchange": self.config.exchange,
            "routing_key": self.config.routing_key,
            "publisher_confirm": True,
            "consumer_ack": "separate edge stage",
            "protocol": "AMQP 0-9-1",
            "classification": "REAL PROTOCOL",
            "delivery_mode": 2,
            "mandatory": True,
        }

    def edge_deliver(self, command_id: str, minimum_deliveries: int = 1) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.timeout
        while time.monotonic() < deadline:
            row = self.store.inbox(command_id)
            if row and row["ack_sent"] and row["deliveries"] >= minimum_deliveries:
                return {
                    "command_id": command_id,
                    "payload_hash": row["payload_hash"],
                    "deliveries": row["deliveries"],
                    "redelivered": row["redelivered"],
                    "consumer_ack_sent": row["ack_sent"],
                    "durable_inbox_committed": True,
                    "ack_policy": "manual ACK after PostgreSQL inbox commit",
                    "protocol": "AMQP 0-9-1",
                    "classification": "REAL PROTOCOL",
                }
            time.sleep(0.05)
        raise TimeoutError("EDGE_NOT_ACKNOWLEDGED_INTENT_RETAINED")

    def redeliver(self, command_id: str) -> dict[str, Any]:
        previous = self.store.inbox(command_id)
        count = previous["deliveries"] if previous else 0
        confirm = self.publish(command_id)
        return {**self.edge_deliver(command_id, count + 1), "duplicate_publish": confirm}

    def opc_connect(self) -> dict[str, Any]:
        return self.opc.call()

    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        command = RobotCommand.model_validate(payload)
        inbox = self.store.inbox(command.command_id)
        if inbox is None or inbox["payload_hash"] != digest(command):
            raise Conflict("DURABLE_EDGE_IDENTITY_REQUIRED")
        return self.opc.call("SubmitJob", command.model_dump_json())

    def preconditions(self, command_id: str) -> dict[str, Any]:
        if self.runtime is None:
            raise Conflict("LAB_RUNTIME_REQUIRED_FOR_OPERATIONAL_PRECONDITIONS")
        return self.opc.call(
            "CheckPreconditions", command_id, self.runtime.world().model_dump_json()
        )

    def authorize_execute(
        self, command_id: str, callback: Callable[[], dict[str, Any]]
    ) -> dict[str, Any]:
        return self.opc.execute(command_id, callback)

    def live_status(self, command_id: str) -> dict[str, Any]:
        return {
            "command_id": command_id,
            "events": self.store.protocol_events(command_id),
            "read_only": True,
            "protocol": "OPC UA",
            "classification": "REAL PROTOCOL",
            "interface": "simulated controller interface",
        }

    def record_result(self, command_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
        return self.opc.call("ReportResult", command_id, json.dumps(receipt))

    def status(self, command_id: str) -> dict[str, Any]:
        return self.opc.call("GetJobStatus", command_id)

    def acknowledge_result(self, command_id: str, sequence: int) -> dict[str, Any]:
        return self.opc.call("AcknowledgeResult", command_id, sequence)

    def restart(self) -> dict[str, Any]:
        return self.opc.call("RestartController")

    def reconcile_business(
        self, payload: dict[str, Any], fail_once: bool = False
    ) -> dict[str, Any]:
        try:
            response = httpx.post(
                self.config.wms_url + "/v1/wms/acknowledgements",
                json={"outcome": payload, "fail_once": fail_once},
                timeout=self.config.timeout,
            )
        except httpx.TransportError:
            raise OSError("WMS_REST_UNAVAILABLE_RETRY_BUSINESS_ACK_ONLY") from None
        if response.status_code == 503:
            raise OSError("WMS_HTTP_503_RETRY_BUSINESS_ACK_ONLY")
        if response.status_code == 409:
            raise Conflict("WMS_COMMAND_PAYLOAD_CONFLICT")
        response.raise_for_status()
        return dict(response.json())
