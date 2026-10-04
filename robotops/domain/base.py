"""Strict shared wire primitives and explicit, hash-preserving schema revisions."""

from datetime import UTC, datetime
from math import isclose
from typing import Annotated, Any, ClassVar, Literal, Self
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    SerializerFunctionWrapHandler,
    StringConstraints,
    field_validator,
    model_serializer,
    model_validator,
)

Identifier = Annotated[str, StringConstraints(min_length=1, max_length=160, pattern=r"^[\w.:-]+$")]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


def stable_id(namespace: str, value: str) -> str:
    return str(uuid5(NAMESPACE_URL, namespace + ":" + value))


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        allow_inf_nan=False,
    )
    # The str annotation permits immutable subclasses to declare a different literal
    # version. The base wire contract still accepts exactly 1.0, including defaults.
    schema_version: str = Field(
        default="1.0", pattern=r"^1\.0$", json_schema_extra={"const": "1.0"}
    )
    extension_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def legacy_has_no_extensions(self) -> Self:
        self._check_extensions()
        return self

    def _check_extensions(self) -> None:
        if self.schema_version == "1.0" and any(
            getattr(self, name) is not None for name in self.extension_fields
        ):
            raise ValueError("VERSION_2_FIELDS_REQUIRE_VERSION_2")

    @model_serializer(mode="wrap")
    def preserve_original_wire_shape(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        # Pydantic infers the serialized JSON schema from a return annotation.
        # Omit it specifically on this wrapper so the original typed model schema
        # survives (dict[str, Any] would incorrectly publish an unrestricted map).
        # Archived command digests include defaults. Never add new null fields to
        # their canonical JSON or silently remove an invalid non-null extension.
        self._check_extensions()
        data: dict[str, Any] = handler(self)
        if self.schema_version == "1.0":
            for name in self.extension_fields:
                data.pop(name, None)
        return data


class V2Contract(Contract):
    schema_version: Literal["2.0"] = "2.0"


class VersionedContract(Contract):
    schema_version: Literal["1.0", "2.0"] = "1.0"


class Record(Contract):
    run_id: Identifier
    correlation_id: Identifier
    causation_id: Identifier
    timestamp: AwareDatetime

    @field_validator("timestamp")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class VersionedRecord(Record):
    schema_version: Literal["1.0", "2.0"] = "1.0"


class Pose(Contract):
    position: tuple[FiniteFloat, FiniteFloat, FiniteFloat]
    quaternion_xyzw: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat] = (0, 0, 0, 1)
    unit: Literal["m"] = "m"
    frame_id: Identifier = "cell_world"
    calibration_version: Identifier = "cal-1"

    @model_validator(mode="after")
    def normalized(self) -> Self:
        if not isclose(sum(x * x for x in self.quaternion_xyzw), 1.0, abs_tol=1e-6):
            raise ValueError("quaternion must have unit norm within 1e-6")
        return self
