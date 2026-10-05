"""Lab service addresses. Credentials are never part of presentation evidence."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LabConfig:
    postgres_dsn: str = field(repr=False)
    amqp_url: str = field(repr=False)
    opcua_url: str = "opc.tcp://127.0.0.1:4840/robotops/"
    wms_url: str = "http://127.0.0.1:8081"
    edge_url: str = "http://127.0.0.1:8082"
    journal_path: Path = Path("runs/lab/plc.db")
    exchange: str = "robotops.commands"
    queue: str = "robotops.edge.cell-1"
    routing_key: str = "cell-1.submit"
    timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "LabConfig":
        return cls(
            postgres_dsn=os.environ["ROBOTOPS_POSTGRES_DSN"],
            amqp_url=os.environ["ROBOTOPS_AMQP_URL"],
            opcua_url=os.getenv("ROBOTOPS_OPCUA_URL", "opc.tcp://127.0.0.1:4840/robotops/"),
            wms_url=os.getenv("ROBOTOPS_WMS_URL", "http://127.0.0.1:8081"),
            edge_url=os.getenv("ROBOTOPS_EDGE_URL", "http://127.0.0.1:8082"),
            journal_path=Path(os.getenv("ROBOTOPS_PLC_JOURNAL", "runs/lab/plc.db")),
            queue=os.getenv("ROBOTOPS_AMQP_QUEUE", "robotops.edge.cell-1"),
            exchange=os.getenv("ROBOTOPS_AMQP_EXCHANGE", "robotops.commands"),
            routing_key=os.getenv("ROBOTOPS_AMQP_ROUTING_KEY", "cell-1.submit"),
        )
