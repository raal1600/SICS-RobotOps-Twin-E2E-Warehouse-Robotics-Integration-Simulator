from dataclasses import replace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from robotops.calibration.configuration import framed
from robotops.calibration.contracts import Camera, Limits, PointFailure, Stream, Tool
from robotops.calibration.depth import deproject, pixel_to_base, reconstruct
from robotops.calibration.errors import CalibrationError
from robotops.calibration.registration import align_native_depth, validate_alignment
from robotops.calibration.tcp import GraspSpecification, ToolProbe, construct_target, verify_tool


def small_camera():
    stream = Stream(
        width=9,
        height=9,
        k=((5, 0, 4), (0, 5, 4), (0, 0, 1)),
        verification="SIMULATION_ONLY_FACTORY_MODEL",
    )
    baseline = np.eye(4)
    baseline[0, 3] = 0.2
    return Camera(
        camera_id="small",
        profile_id="native-9",
        configuration_revision="1",
        rgb=stream,
        depth=stream,
        depth_scale_m=0.001,
        depth_semantics="optical_z",
        t_c_d=framed(baseline, "d", "c"),
    )


def measured_point():
    camera = small_camera()
    x = np.array([[0, -1, 0, 1], [1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1.0]])
    return reconstruct(
        (5.5, 4),
        np.full((9, 9), 2000, dtype=np.float32),
        camera,
        framed(x, "c", "b"),
        Limits(),
        native_pixel=(5, 4),
    )


def test_native_registration_scale_and_frame_direction_golden():
    point = measured_point()
    assert point.point == (1, 2.6, 5)
    assert point.native_depth_pixel == (5, 4)
    assert point.calculation.outputs["normalized_ray"] == [0.2, 0, 1]
    assert point.calculation.outputs["p_d_m"] == [0.4, 0, 2]
    assert np.allclose(point.calculation.outputs["p_c_m"], [0.6, 0, 2])
    assert point.raw_depth_value == 2000


def test_axial_and_radial_off_axis_are_not_interchangeable():
    camera = small_camera()
    # q=(0.6,0.8,1), ||q||=sqrt(2), axial Z=2 vs radial range=2.
    pixels = np.array([[7, 8.0]])
    axial = deproject(pixels, np.array([2.0]), camera)
    radial = deproject(
        pixels, np.array([2.0]), camera.model_copy(update={"depth_semantics": "radial_range"})
    )
    assert np.allclose(axial, [[1.2, 1.6, 2]])
    assert np.allclose(radial, [[0.848528137423857, 1.131370849898476, 1.414213562373095]])
    assert np.isclose(np.linalg.norm(radial), 2)


@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, 10, 999999])
def test_invalid_native_depth_never_returns_zero_or_fallback(value):
    raw = np.full((9, 9), 2000, dtype=np.float32)
    raw[4, 5] = value
    with pytest.raises(CalibrationError, match="INVALID_SELECTED_DEPTH"):
        reconstruct(
            (5.5, 4),
            raw,
            small_camera(),
            framed(np.eye(4), "c", "b"),
            Limits(),
            native_pixel=(5, 4),
        )


def test_mixed_depth_occlusion_and_sparse_associations_are_rejected():
    raw = np.full((9, 9), 2000, dtype=np.float32)
    raw[:, 6:] = 2500
    with pytest.raises(CalibrationError, match="OCCLUDED_OR_MIXED_DEPTH"):
        reconstruct(
            (5.5, 4),
            raw,
            small_camera(),
            framed(np.eye(4), "c", "b"),
            Limits(),
            native_pixel=(5, 4),
        )
    raw[:] = 0
    raw[4, 5] = 2000
    with pytest.raises(CalibrationError, match="AMBIGUOUS_DEPTH_ASSOCIATION"):
        reconstruct((5.5, 4), raw, small_camera(), framed(np.eye(4), "c", "b"), Limits())


def test_no_approval_returns_typed_error_without_target():
    result = pixel_to_base(
        (5.5, 4),
        np.full((9, 9), 2000, dtype=np.float32),
        small_camera(),
        None,
        Limits(),
        active_valid=True,
    )
    assert isinstance(result, PointFailure)
    assert result.code == "APPROVED_CALIBRATION_REQUIRED"
    assert result.target is None
    assert "point" not in result.model_dump()


def aligned_camera():
    native = small_camera()
    # Physical depth and RGB optical origins differ in x AND z: native Z is not RGB Z.
    transform = np.array(native.t_c_d.matrix)
    transform[2, 3] = 0.5
    return Camera.model_validate(
        {
            **native.model_dump(),
            "t_c_d": framed(transform, "d", "c"),
            "registration": "aligned_documented",
            "aligned_semantics": "native_optical_z",
        }
    )


def test_documented_alignment_preserves_native_semantics_and_explicit_mapping():
    camera = aligned_camera()
    raw = np.full((9, 9), 2000, dtype=np.float32)
    aligned = align_native_depth(raw, camera, "capture-one")
    assert aligned.values[4, 5] == 2000
    assert tuple(aligned.native_pixels[4, 5]) == (5, 4)
    x = framed(np.array([[0, -1, 0, 1], [1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1.0]]), "c", "b")
    result = reconstruct((5, 4), raw, camera, x, Limits(), alignment=aligned)
    assert np.allclose(result.point, (1, 2.6, 5.5))
    assert result.calculation.outputs["p_d_m"] == [0.4, 0, 2]
    assert np.allclose(result.calculation.outputs["p_c_m"], [0.6, 0, 2.5])
    assert result.calculation.inputs["alignment"]["value_semantics"] == "native_optical_z"
    # A string claiming alignment without actual correspondence remains rejected.
    with pytest.raises(CalibrationError, match="ALIGNED_NATIVE_MAPPING_REQUIRED"):
        reconstruct((5, 4), raw, camera, x, Limits())


def test_alignment_rejects_holes_tampering_reused_profile_and_unsupported_semantics():
    camera = aligned_camera()
    raw = np.full((9, 9), 2000, dtype=np.float32)
    aligned = align_native_depth(raw, camera, "capture-one")
    with pytest.raises(CalibrationError, match="ALIGNED_DEPTH_HOLE"):
        reconstruct((0, 0), raw, camera, framed(np.eye(4), "c", "b"), Limits(), alignment=aligned)
    corrupted = aligned.values.copy()
    corrupted[4, 5] = 2500  # Incorrectly reinterpreting native Z as RGB Z is detectable.
    with pytest.raises(CalibrationError, match="ALIGNED_ARRAY_HASH_MISMATCH"):
        validate_alignment((5, 4), raw, camera, replace(aligned, values=corrupted))
    changed = camera.model_copy(update={"profile_id": "new-crop"})
    with pytest.raises(CalibrationError, match="ALIGNED_CONFIGURATION_MISMATCH"):
        validate_alignment((5, 4), raw, changed, aligned)
    wrong = camera.model_copy(update={"aligned_semantics": "rgb_optical_z"})
    with pytest.raises(CalibrationError, match="UNSUPPORTED_ALIGNED_DEPTH_SEMANTICS"):
        align_native_depth(raw, wrong, "capture-one")
    changed_raw = raw.copy()
    changed_raw[4, 5] = 0
    with pytest.raises(CalibrationError, match="ALIGNED_ARRAY_HASH_MISMATCH"):
        validate_alignment((5, 4), changed_raw, camera, aligned)


def test_alignment_does_not_hide_mixed_depth_and_radial_range_stays_radial():
    camera = aligned_camera()
    raw = np.full((9, 9), 2000, dtype=np.float32)
    raw[:, 6:] = 2500
    aligned = align_native_depth(raw, camera, "edge")
    with pytest.raises(CalibrationError, match="OCCLUDED_OR_MIXED_DEPTH"):
        reconstruct((5, 4), raw, camera, framed(np.eye(4), "c", "b"), Limits(), alignment=aligned)
    stream = Stream(
        width=9,
        height=9,
        k=((100, 0, 4), (0, 100, 4), (0, 0, 1)),
        verification="SIMULATION_ONLY_FACTORY_MODEL",
    )
    radial = Camera.model_validate(
        {
            **camera.model_dump(),
            "rgb": stream,
            "depth": stream,
            "depth_semantics": "radial_range",
            "aligned_semantics": "native_radial_range",
            "t_c_d": framed(np.eye(4), "d", "c"),
        }
    )
    raw[:] = 2000
    aligned = align_native_depth(raw, radial, "off-axis-radial")
    result = reconstruct(
        (6, 6), raw, radial, framed(np.eye(4), "c", "b"), Limits(), alignment=aligned
    )
    assert np.isclose(np.linalg.norm(result.point), 2)
    assert np.allclose(result.point, np.array([0.04, 0.04, 2]) / np.sqrt(1.0008))
    assert aligned.values[6, 6] == 2000


def tool_metrology():
    # Independently specified 90-degree tool axes and 200 mm tip; no implementation helper for measurements.
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    offset = np.array([0.0, 0.0, 0.2])
    configured = np.eye(4)
    configured[:3, :3], configured[:3, 3] = rotation, offset
    tool = Tool(
        tool_id="probe", configuration_revision="tool-1", t_f_tcp=framed(configured, "tcp", "f")
    )
    center = np.array([0.1, -0.1, 0.6])
    poses = []
    for angles in (
        [0, 0, 0],
        [0.3, 0, 0],
        [-0.3, 0, 0],
        [0, 0.3, 0],
        [0, -0.3, 0],
        [0.2, 0.2, 0.2],
    ):
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_euler("xyz", angles).as_matrix()
        matrix[:3, 3] = center - matrix[:3, :3] @ offset
        poses.append(framed(matrix, "f", "b"))
    probes = [
        ToolProbe(tcp_reference_point_m=(0, 0, 0), measured_flange_point_m=(0, 0, 0.2)),
        ToolProbe(tcp_reference_point_m=(0.1, 0, 0), measured_flange_point_m=(0, 0.1, 0.2)),
        ToolProbe(tcp_reference_point_m=(0, 0.1, 0), measured_flange_point_m=(-0.1, 0, 0.2)),
        ToolProbe(tcp_reference_point_m=(0, 0, 0.1), measured_flange_point_m=(0, 0, 0.3)),
    ]
    return tool, poses, probes


def test_tcp_pivot_and_independent_orientation_check():
    tool, poses, probes = tool_metrology()
    report = verify_tool(tool, poses, probes, "verified")
    assert report.passed
    assert np.allclose(report.pivot_tip_f_m, [0, 0, 0.2], atol=1e-10)
    assert np.allclose(report.pivot_center_b_m, [0.1, -0.1, 0.6], atol=1e-10)
    changed = np.array(tool.t_f_tcp.matrix)
    changed[2, 3] = 0.21
    wrong = tool.model_copy(update={"t_f_tcp": framed(changed, "tcp", "f")})
    assert verify_tool(wrong, poses, probes, "wrong-offset").failures == (
        "TCP_TRANSLATION_CHECK_FAILED",
    )
    changed[:3, :3] = np.eye(3)
    wrong_axes = tool.model_copy(update={"t_f_tcp": framed(changed, "tcp", "f")})
    assert (
        "TOOL_ORIENTATION_CHECK_FAILED"
        in verify_tool(wrong_axes, poses, probes, "wrong-axes").failures
    )
    with pytest.raises(CalibrationError, match="TCP_PIVOT_UNOBSERVABLE"):
        verify_tool(tool, [poses[0]] * 6, probes, "repeated")


@pytest.mark.parametrize("mode", ["tcp", "flange"])
def test_tcp_and_flange_modes_apply_the_tool_offset_exactly_once(mode):
    tool, poses, probes = tool_metrology()
    verification = verify_tool(tool, poses, probes, "checked")
    grasp = GraspSpecification(
        orientation_b_tcp=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        contact_offset_b_m=(0, 0, 0.01),
        approach_direction_b=(0, 0, -1),
        approach_distance_m=0.1,
        orientation_source="indexed grasp fixture",
        contact_source="10 mm compliant pad",
        approach_source="vertical fixture access",
    )
    target = construct_target(measured_point(), grasp, tool, verification, mode)
    assert np.allclose(np.array(target.tcp_target.matrix)[:3, 3], [1, 2.6, 5.01])
    assert np.allclose(np.array(target.flange_target.matrix)[:3, 3], [1, 2.6, 4.81])
    assert np.allclose(np.array(target.approach_tcp.matrix)[:3, 3], [1, 2.6, 5.11])
    assert target.command_target.source == ("tcp" if mode == "tcp" else "f")
    assert np.allclose(
        np.array(target.flange_target.matrix) @ np.array(tool.t_f_tcp.matrix),
        target.tcp_target.matrix,
    )
    changed = tool.model_copy(update={"configuration_revision": "changed"})
    with pytest.raises(CalibrationError, match="CURRENT_TOOL_VERIFICATION_REQUIRED"):
        construct_target(measured_point(), grasp, changed, verification, mode)
