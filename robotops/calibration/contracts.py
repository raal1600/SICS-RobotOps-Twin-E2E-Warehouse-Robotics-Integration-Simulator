"""Versioned measurement and lifecycle contracts; no hidden simulator transforms."""

import hashlib
import json
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

from robotops.calibration.geometry import rigid

Id = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")]
Vec2 = tuple[float, float]
Vec3 = tuple[float, float, float]
Row4 = tuple[float, float, float, float]
Matrix4 = tuple[Row4, Row4, Row4, Row4]
Matrix3 = tuple[Vec3, Vec3, Vec3]
Frame = Literal["b", "f", "t", "c", "d", "tcp"]


class Record(BaseModel):
    # Wrap serializers deliberately omit a return annotation, as domain.Contract
    # does, so Pydantic retains strict typed wire schemas rather than arbitrary maps.
    model_config = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False, validate_default=True
    )
    schema_version: Literal["calibration-1.0"] = "calibration-1.0"

    def fingerprint(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class Transform(Record):
    source: Frame
    destination: Frame
    matrix: Matrix4
    translation_unit: Literal["m"] = "m"

    @model_validator(mode="after")
    def valid_matrix(self) -> Self:
        rigid(self.matrix)
        return self


class Stream(Record):
    width: int = Field(gt=0, le=4096)
    height: int = Field(gt=0, le=4096)
    k: Matrix3
    distortion_model: Literal["pinhole", "fisheye"] = "pinhole"
    coefficients: tuple[float, ...] = ()
    crop_xy: tuple[int, int] = (0, 0)
    resize_xy: Vec2 = (1, 1)
    verification: Literal["SIMULATION_ONLY_FACTORY_MODEL", "MEASURED_BOARD_MODEL"]

    @model_validator(mode="after")
    def model_consistency(self) -> Self:
        k = np.asarray(self.k)
        if k[0, 0] <= 0 or k[1, 1] <= 0 or not np.allclose(k[2], [0, 0, 1]):
            raise ValueError("INVALID_INTRINSICS")
        if k[0, 1] != 0 or k[1, 0] != 0:
            raise ValueError("UNSUPPORTED_INTRINSIC_SKEW")
        allowed = (4,) if self.distortion_model == "fisheye" else (0, 4, 5, 8)
        if len(self.coefficients) not in allowed:
            raise ValueError("DISTORTION_MODEL_MISMATCH")
        if min(self.crop_xy) < 0 or min(self.resize_xy) <= 0:
            raise ValueError("INVALID_CROP_OR_RESIZE")
        return self


class Camera(Record):
    camera_id: Id
    profile_id: Id
    configuration_revision: Id
    rgb: Stream
    depth: Stream
    depth_scale_m: float = Field(gt=0, le=1)
    depth_semantics: Literal["optical_z", "radial_range"]
    t_c_d: Transform
    registration: Literal["native", "aligned_documented"] = "native"
    aligned_semantics: str | None = None
    min_depth_m: float = Field(default=0.05, gt=0)
    max_depth_m: float = Field(default=4, gt=0)

    @model_validator(mode="after")
    def registration_contract(self) -> Self:
        if (self.t_c_d.source, self.t_c_d.destination) != ("d", "c"):
            raise ValueError("RGB_DEPTH_FRAME_DIRECTION")
        if self.max_depth_m <= self.min_depth_m:
            raise ValueError("INVALID_DEPTH_RANGE")
        if self.registration == "aligned_documented" and not self.aligned_semantics:
            raise ValueError("ALIGNED_DEPTH_SEMANTICS_REQUIRED")
        return self


class Board(Record):
    board_id: Id = "charuco-7x5"
    mounting_id: Id = "flange-mount-1"
    squares_x: int = Field(default=7, ge=3, le=20)
    squares_y: int = Field(default=5, ge=3, le=20)
    square_length_m: float = Field(default=0.045, ge=0.005, le=0.2)
    marker_length_m: float = Field(default=0.0315, gt=0)
    dictionary: Literal["DICT_4X4_100"] = "DICT_4X4_100"
    measured_dimensions_m: Vec2 = (0.315, 0.225)
    corner_ids: tuple[int, ...]
    corners_m: tuple[Vec3, ...]

    @model_validator(mode="after")
    def geometry(self) -> Self:
        count = (self.squares_x - 1) * (self.squares_y - 1)
        if self.marker_length_m >= self.square_length_m:
            raise ValueError("INVALID_MARKER_SIZE")
        if self.corner_ids != tuple(range(count)) or len(self.corners_m) != count:
            raise ValueError("BOARD_POINT_IDENTITIES")
        expected = [
            ((x + 1) * self.square_length_m, (y + 1) * self.square_length_m, 0)
            for y in range(self.squares_y - 1)
            for x in range(self.squares_x - 1)
        ]
        if not np.allclose(self.corners_m, expected, atol=1e-8, rtol=0):
            raise ValueError("BOARD_POINT_ORDER_OR_UNITS")
        if not np.allclose(
            self.measured_dimensions_m,
            [self.squares_x * self.square_length_m, self.squares_y * self.square_length_m],
            atol=1e-8,
            rtol=0,
        ):
            raise ValueError("BOARD_DIMENSIONS_MISMATCH")
        return self


class Tool(Record):
    tool_id: Id
    configuration_revision: Id
    t_f_tcp: Transform
    verification_id: Id | None = None

    @model_validator(mode="after")
    def direction(self) -> Self:
        if (self.t_f_tcp.source, self.t_f_tcp.destination) != ("tcp", "f"):
            raise ValueError("TOOL_FRAME_DIRECTION")
        return self


class ArtifactRef(Record):
    path: str
    sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    media_type: Literal["image/png", "application/x-npy", "application/json"]
    shape: tuple[int, ...] = ()

    @model_validator(mode="after")
    def confined(self) -> Self:
        value = PurePosixPath(self.path)
        if value.is_absolute() or ".." in value.parts or "\\" in self.path or ":" in self.path:
            raise ValueError("UNSAFE_ARTIFACT_PATH")
        return self


class Capture(Record):
    capture_id: Id
    dataset_id: Id
    camera_id: Id
    profile_id: Id
    configuration_fingerprint: str
    board_fingerprint: str
    rgb: ArtifactRef
    depth: ArtifactRef
    rgb_timestamp_s: float
    depth_timestamp_s: float
    robot_timestamp_s: float
    settled: bool
    moving: bool
    t_b_f: Transform
    admitted: bool
    rejection_codes: tuple[str, ...] = ()
    provenance: Literal["SYNTHETIC_IMAGE_SENSOR"] = "SYNTHETIC_IMAGE_SENSOR"
    partition: Literal["fit", "validation", "routine", "runtime"]
    sensor_fault_ids: tuple[Id, ...] = ()

    @model_serializer(mode="wrap")
    def retain_prior_capture(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if not self.sensor_fault_ids:
            result.pop("sensor_fault_ids", None)
        return result

    @model_validator(mode="after")
    def acquisition_status(self) -> Self:
        if (self.t_b_f.source, self.t_b_f.destination) != ("f", "b"):
            raise ValueError("FLANGE_FRAME_DIRECTION")
        if self.admitted == bool(self.rejection_codes):
            raise ValueError("ACQUISITION_STATUS_INCONSISTENT")
        return self


class ReferenceCapture(Record):
    """Independent surveyed fixture coordinate, never reconstructed from the candidate X."""

    reference_id: Id
    base_point_m: Vec3
    capture: Capture
    provenance: Literal["SYNTHETIC_INDEPENDENT_SURVEY_FIXTURE"] = (
        "SYNTHETIC_INDEPENDENT_SURVEY_FIXTURE"
    )


class ReferenceBatch(Record):
    batch_id: Id
    camera_id: Id
    dataset_id: Id
    partition: Literal["validation", "routine"]
    captures: tuple[ReferenceCapture, ...]
    scope: str = "Independent synthetic survey fixtures; reference positions are defined before and without the candidate calibration"

    @model_validator(mode="after")
    def matching_captures(self) -> Self:
        identities = [item.reference_id for item in self.captures]
        if not identities or len(identities) != len(set(identities)):
            raise ValueError("REFERENCE_BATCH_IDENTITIES")
        if any(
            item.reference_id != item.capture.capture_id
            or item.capture.camera_id != self.camera_id
            or item.capture.dataset_id != self.dataset_id
            or item.capture.partition != self.partition
            for item in self.captures
        ):
            raise ValueError("REFERENCE_BATCH_CONTEXT")
        return self


class SurfaceDetection(Record):
    capture_id: Id
    camera_id: Id
    method: Literal["reference_center", "red_cube_top"]
    selected_rgb_pixel: Vec2
    mask: ArtifactRef
    selected_pixel_count: int = Field(gt=0)
    scope: str = "Rule-based detection of one declared synthetic color patch; not a recognition probability or complete grasp pose"


class Limits(Record):
    limits_id: Id = "synthetic-grasp-budget-1"
    scope: Literal["SIMULATION_ONLY"] = "SIMULATION_ONLY"
    justification: str = (
        "10 mm synthetic contact capture radius; reserve 5 mm for depth/robot/tool "
        "and require at most 5 mm independent point error. Pixel and angular limits "
        "are separate quality gates, not production or SICS requirements."
    )
    max_timestamp_skew_s: float = Field(default=0.02, gt=0)
    max_pnp_rms_px: float | None = Field(default=1.5, gt=0)
    max_chain_rms_px: float | None = Field(default=2.0, gt=0)
    max_chain_translation_mm: float | None = Field(default=6, gt=0)
    max_chain_rotation_deg: float | None = Field(default=1, gt=0)
    max_reference_error_mm: float | None = Field(default=5, gt=0)
    min_samples: int = Field(default=10, ge=3)
    min_corners: int = Field(default=8, ge=4)
    min_translation_span_m: Vec3 = (0.12, 0.12, 0.12)
    min_rotation_singular_rad: float = Field(default=0.15, gt=0)
    min_image_coverage: float = Field(default=0.08, gt=0, lt=1)
    outlier_threshold_px: float = Field(default=2.5, gt=0)
    ambiguity_gap_px: float = Field(default=0.08, gt=0)
    minimum_p95_count: int = Field(default=20, ge=20)
    quantile_method: Literal["linear"] = "linear"
    max_depth_surface_spread_m: float = Field(default=0.015, gt=0)
    max_correspondence_error_px: float = Field(default=1.5, gt=0)


class PoseConditioning(Record):
    method: Literal["linearized-pixel-Jacobian-1"] = "linearized-pixel-Jacobian-1"
    pixel_sigma: float
    translation_sigma_mm: float
    rotation_sigma_deg: float
    sigma_multiplier: float = 3
    limitation: str = (
        "Local sensitivity estimate; ignores systematic bias and does not prove physical accuracy"
    )


class PoseSample(Record):
    capture_id: Id
    dataset_id: Id
    camera_id: Id
    configuration_fingerprint: str
    board_fingerprint: str
    t_b_f: Transform
    t_c_t: Transform
    corner_ids: tuple[int, ...]
    object_points_m: tuple[Vec3, ...]
    image_points_px: tuple[Vec2, ...]
    residuals_px: tuple[Vec2, ...]
    pnp_rms_px: float
    excluded_corner_ids: tuple[int, ...] = ()
    excluded_image_points_px: tuple[Vec2, ...] | None = None
    candidate_rms_px: tuple[float, ...]
    partition: Literal["fit", "validation", "routine"]
    conditioning: PoseConditioning | None = None

    @model_serializer(mode="wrap")
    def retain_older_evidence(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        # Pre-conditioning saved samples keep their exact original wire identity.
        result: dict[str, object] = handler(self)
        if self.conditioning is None:
            result.pop("conditioning", None)
        if self.excluded_image_points_px is None:
            result.pop("excluded_image_points_px", None)
        return result

    @model_validator(mode="after")
    def observations(self) -> Self:
        if (self.t_b_f.source, self.t_b_f.destination) != ("f", "b"):
            raise ValueError("FLANGE_FRAME_DIRECTION")
        if (self.t_c_t.source, self.t_c_t.destination) != ("t", "c"):
            raise ValueError("BOARD_POSE_FRAME_DIRECTION")
        count = len(self.corner_ids)
        if count < 4 or len(set(self.corner_ids)) != count:
            raise ValueError("INVALID_SAMPLE_CORNER_IDENTITIES")
        if any(
            len(values) != count
            for values in (
                self.object_points_m,
                self.image_points_px,
                self.residuals_px,
            )
        ):
            raise ValueError("INCONSISTENT_SAMPLE_CORRESPONDENCES")
        expected = float(np.sqrt(np.sum(np.square(self.residuals_px)) / count))
        if self.pnp_rms_px < 0 or not np.isclose(expected, self.pnp_rms_px, atol=1e-8):
            raise ValueError("INCONSISTENT_POINT_RMS")
        if set(self.corner_ids) & set(self.excluded_corner_ids):
            raise ValueError("EXCLUDED_CORNER_USED")
        if self.excluded_image_points_px is not None and len(self.excluded_image_points_px) != len(
            self.excluded_corner_ids
        ):
            raise ValueError("INCONSISTENT_EXCLUDED_CORRESPONDENCES")
        if not self.candidate_rms_px or min(self.candidate_rms_px) < 0:
            raise ValueError("MISSING_PNP_CANDIDATE_DECISION")
        return self


class Coverage(Record):
    sample_count: int
    translation_span_m: Vec3
    rotation_singular_values_rad: Vec3
    image_fraction: float
    failures: tuple[str, ...]


class FitResidual(Record):
    sample_id: Id
    translation_mm: float = Field(ge=0)
    rotation_deg: float = Field(ge=0)
    included: bool
    reason: str


class RobustFitPolicy(Record):
    policy_id: Literal["synthetic-training-consensus-1"] = "synthetic-training-consensus-1"
    scope: Literal["SIMULATION_ONLY"] = "SIMULATION_ONLY"
    hypothesis_count: int = Field(default=64, ge=1, le=256)
    subset_size: int = Field(default=6, ge=3, le=10)
    seed: int = 1147
    max_rejection_fraction: float = Field(default=0.25, ge=0, lt=0.5)
    justification: str = "Training-only consensus uses frozen chain mm/degree limits separately; reject excessive contamination, then require retained pose coverage and unused independent validation."


class FitDiagnostics(Record):
    policy: RobustFitPolicy
    tested_hypotheses: int = Field(ge=1)
    valid_hypotheses: int = Field(ge=1)
    consensus_sample_ids: tuple[Id, ...]
    residuals: tuple[FitResidual, ...]
    selection_rule: str = "Largest training consensus; tie: lowest median max(translation/translation_limit, angle/angle_limit). No holdout data used."


class EstimateLineage(Record):
    artifact_id: Id
    artifact_fingerprint: str
    candidate_fingerprint: str
    created_at_utc: str
    scope: Literal["UNCHANGED_ESTIMATE_NEW_VALIDATION_REQUIRED"] = (
        "UNCHANGED_ESTIMATE_NEW_VALIDATION_REQUIRED"
    )


class Candidate(Record):
    candidate_id: Id
    camera: Camera
    board: Board
    x: Transform
    y: Transform
    mounting_known: bool
    sample_ids: tuple[Id, ...]
    dataset_ids: tuple[Id, ...]
    coverage: Coverage
    weights: tuple[float, ...]
    excluded_sample_ids: tuple[Id, ...] = ()
    status: Literal["CANDIDATE"] = "CANDIDATE"
    active: Literal[False] = False
    solver: Literal["Park-Martin+SO3-chordal", "known-Y+SO3-chordal"]
    software_version: str
    source_fingerprints: dict[str, str]
    limits_fingerprint: str
    fit_diagnostics: FitDiagnostics | None = None
    reused_from: EstimateLineage | None = None

    @model_serializer(mode="wrap")
    def retain_prior_candidate(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if self.fit_diagnostics is None:
            result.pop("fit_diagnostics", None)
        if self.reused_from is None:
            result.pop("reused_from", None)
        return result

    @model_validator(mode="after")
    def consistency(self) -> Self:
        if (self.x.source, self.x.destination) != ("c", "b"):
            raise ValueError("CAMERA_EXTRINSIC_FRAME_DIRECTION")
        if (self.y.source, self.y.destination) != ("t", "f"):
            raise ValueError("BOARD_MOUNT_FRAME_DIRECTION")
        if (
            len(self.sample_ids) != len(set(self.sample_ids))
            or len(self.sample_ids) != len(self.weights)
            or min(self.weights, default=0) <= 0
        ):
            raise ValueError("INVALID_FIT_SAMPLE_WEIGHTS")
        if set(self.sample_ids) & set(self.excluded_sample_ids):
            raise ValueError("EXCLUDED_SAMPLE_USED")
        if self.coverage.failures or self.coverage.sample_count != len(self.sample_ids):
            raise ValueError("CANDIDATE_COVERAGE_INVALID")
        if self.fit_diagnostics is not None:
            included = tuple(
                row.sample_id for row in self.fit_diagnostics.residuals if row.included
            )
            excluded = tuple(
                row.sample_id for row in self.fit_diagnostics.residuals if not row.included
            )
            if included != self.sample_ids or excluded != self.excluded_sample_ids:
                raise ValueError("FIT_EXCLUSION_RECORD_MISMATCH")
        return self


class Calculation(Record):
    function: str
    formula: str
    inputs: dict[str, object]
    outputs: dict[str, object]
    decision: str
    classification: Literal["IN_PROCESS_PYTHON"] = "IN_PROCESS_PYTHON"

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def canonical_json(cls, value: object) -> dict[str, object]:
        # These are saved payloads: tuple/list differences must not change a decision
        # after a JSON/API roundtrip. Scientific arrays stay in referenced artifacts.
        result = json.loads(json.dumps(value, allow_nan=False))
        if not isinstance(result, dict):
            raise ValueError("CALCULATION_PAYLOAD_MUST_BE_OBJECT")
        return result


class PointMeasurement(Record):
    frame: Literal["b"] = "b"
    unit: Literal["m"] = "m"
    point: Vec3
    camera_id: Id
    configuration_fingerprint: str
    transform_fingerprint: str
    selected_rgb_pixel: Vec2
    native_depth_pixel: tuple[int, int]
    raw_depth_value: float
    calculation: Calculation


class PointFailure(Record):
    code: str
    detail: str
    camera_id: Id
    selected_rgb_pixel: Vec2
    target: None = None


class IndependentReference(Record):
    reference_id: Id
    dataset_id: Id
    base_point_m: Vec3
    measurement: PointMeasurement
    provenance: Literal["INDEPENDENT_SYNTHETIC_REFERENCE"] = "INDEPENDENT_SYNTHETIC_REFERENCE"


class ImageValidation(Record):
    capture_id: Id
    point_count: int = Field(gt=0)
    pnp_rms_px: float = Field(ge=0)
    chain_rms_px: float = Field(ge=0)
    chain_translation_mm: float = Field(ge=0)
    chain_rotation_deg: float = Field(ge=0)
    pnp_residuals_px: tuple[Vec2, ...]
    chain_residuals_px: tuple[Vec2, ...]


class ReferenceValidation(Record):
    reference_id: Id
    expected_base_m: Vec3
    predicted_base_m: Vec3
    error_vector_m: Vec3
    error_mm: float = Field(ge=0)


class MeasurementRejection(Record):
    capture_id: Id
    reason: str
    detail: str
    stage: Literal["acquisition", "board_pose", "depth"]
    calculation: Calculation | None = None

    @model_serializer(mode="wrap")
    def retain_prior_rejection(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if self.calculation is None:
            result.pop("calculation", None)
        return result


class ValidationReport(Record):
    report_id: Id
    candidate_id: Id
    candidate_fingerprint: str
    limits_fingerprint: str
    dataset_ids: tuple[Id, ...]
    dataset_fingerprint: str
    passed: bool
    failures: tuple[str, ...]
    images: tuple[ImageValidation, ...]
    references: tuple[ReferenceValidation, ...]
    point_count: int = Field(ge=0)
    pnp_rms_px: float | None
    chain_rms_px: float | None
    reference_count: int = Field(ge=0)
    reference_span_m: Vec3
    reference_median_mm: float | None
    reference_max_mm: float | None
    reference_p95_mm: float | None
    quantile_method: Literal["linear"] = "linear"
    minimum_p95_count: int = Field(ge=20)
    rejected_measurements: tuple[MeasurementRejection, ...] = ()
    limitations: tuple[str, ...] = (
        "Synthetic measurements and simulation-only limits; no real-cell accuracy claim.",
        "Robot kinematics are inputs, not calibrated here; residual flex and robot/depth error remain.",
        "A geometric point does not establish object recognition or a safe grasp.",
    )

    @model_validator(mode="after")
    def status(self) -> Self:
        if self.passed == bool(self.failures):
            raise ValueError("VALIDATION_STATUS_INCONSISTENT")
        if self.point_count != sum(image.point_count for image in self.images):
            raise ValueError("VALIDATION_POINT_COUNT_MISMATCH")
        if self.reference_count != len(self.references):
            raise ValueError("REFERENCE_COUNT_MISMATCH")
        if self.reference_p95_mm is not None and self.reference_count < self.minimum_p95_count:
            raise ValueError("UNSUPPORTED_P95")
        return self


class ApprovalRecord(Record):
    actor: Annotated[str, Field(min_length=1, max_length=100)]
    timestamp_utc: str
    candidate_fingerprint: str
    report_fingerprint: str
    scope: Literal["SIMULATED_OPERATOR_APPROVAL"] = "SIMULATED_OPERATOR_APPROVAL"


class CalibrationArtifact(Record):
    artifact_id: Id
    candidate: Candidate
    validation: ValidationReport
    approval: ApprovalRecord
    status: Literal["APPROVED"] = "APPROVED"
    camera_model_report_id: Id | None = None
    camera_model_report_fingerprint: str | None = None

    @model_serializer(mode="wrap")
    def retain_prior_approval(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if self.camera_model_report_id is None:
            result.pop("camera_model_report_id", None)
            result.pop("camera_model_report_fingerprint", None)
        return result

    @model_validator(mode="after")
    def authorization(self) -> Self:
        if (self.camera_model_report_id is None) != (self.camera_model_report_fingerprint is None):
            raise ValueError("INCOMPLETE_OPTICAL_REPORT_BINDING")
        candidate_hash = self.candidate.fingerprint()
        if not self.validation.passed:
            raise ValueError("PASSING_VALIDATION_REQUIRED")
        if (
            self.validation.candidate_id != self.candidate.candidate_id
            or self.validation.candidate_fingerprint != candidate_hash
            or self.approval.candidate_fingerprint != candidate_hash
            or self.approval.report_fingerprint != self.validation.fingerprint()
            or self.validation.limits_fingerprint != self.candidate.limits_fingerprint
        ):
            raise ValueError("APPROVAL_IDENTITY_MISMATCH")
        return self
