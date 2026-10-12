"""Observed pixels drive targets; independent cameras cannot conceal disagreement."""

import numpy as np
import pytest

from robotops.calibration.agreement import compare_cameras
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import OrderLine, OrderRequest
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_changed_physical_images_change_target_and_conflicting_cameras_never_average(tmp_path):
    settings = Settings.calibration(seed=211)
    runtime = SyntheticRuntime(tmp_path / "runtime.db", settings)
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    service, observer = engine.calibration, engine.measured_observer
    assert service is not None and observer is not None
    for camera in ("camera-west", "camera-east"):
        service.configure(camera, Mutation(request_id="configure", expected_revision=0))
        service.acquire(
            camera, f"{camera}-fit", Mutation(request_id="acquire", expected_revision=1)
        )
        service.fit(
            camera, f"{camera}-fit", camera, Mutation(request_id="fit", expected_revision=2)
        )
        checked = service.validate(
            camera, camera, f"{camera}-unused", Mutation(request_id="validate", expected_revision=3)
        )
        report = service.report(checked.record_ids[0])
        assert report.passed, report.failures
        service.store.approve(
            camera,
            camera,
            report.report_id,
            "Simulated boundary test",
            Mutation(request_id="approve", expected_revision=5),
        )
    service.prepare_tool("camera-west", Mutation(request_id="tool", expected_revision=6))
    order = engine.store.intake(
        OrderRequest(
            order_id="measurement-sensitivity",
            lines=(
                OrderLine(
                    order_line_id="line",
                    product_id="calibration-red-cube",
                    source_id="source",
                    destination_id="destination",
                ),
            ),
        ),
        "measurement-sensitivity",
    )
    job = engine.store.job(order.job_ids[0])
    destination = next(item for item in settings.locations if item.location_id == "destination")
    before = observer.fresh(identity="before-shift")
    first_plan = engine.brain.plan(job, before, destination)
    # Test oracle modifies only the physical simulator. The observer/brain have no
    # access to this shift and must acquire newly rendered RGB and native depth.
    shift = np.array([0.018, 0.012, 0.0])
    with runtime.db.transaction() as db:
        world = runtime._world(db)
        original = world.objects[0]
        shifted = original.model_copy(
            update={
                "pose": original.pose.model_copy(
                    update={
                        "position": tuple(np.array(original.pose.position) + shift),
                    }
                )
            }
        )
        runtime._write_world(db, world.model_copy(update={"objects": (shifted,)}))
    after = observer.fresh(identity="after-shift")
    second_plan = engine.brain.plan(job, after, destination)
    a, b = first_plan.calibrated_plan, second_plan.calibrated_plan
    assert a is not None and b is not None
    actual_shift = (
        np.array(b.target.tcp_target.matrix)[:3, 3] - np.array(a.target.tcp_target.matrix)[:3, 3]
    )
    np.testing.assert_allclose(actual_shift, shift, atol=0.004, rtol=0)
    assert a.observed_object.binding.artifact_id == b.observed_object.binding.artifact_id
    assert (
        a.observed_object.surface_point.selected_rgb_pixel
        != b.observed_object.surface_point.selected_rgb_pixel
    )
    assert a.observed_object.binding.capture_id != b.observed_object.binding.capture_id
    assert runtime.world().step == 0  # Planning is not execution.

    primary = b.observed_object.surface_point
    secondary_id = after.calibrated_observation.bindings[1].capture_id
    from robotops.calibration.contracts import PointMeasurement

    secondary = service.store.record("runtime-point", secondary_id, PointMeasurement)
    first, second = (service.store.active(camera) for camera in ("camera-west", "camera-east"))
    limits = tuple(service.store.state(camera).limits for camera in ("camera-west", "camera-east"))
    agreement = compare_cameras("nominal", primary, secondary, first, second, *limits)
    assert agreement.passed and agreement.shared_mount_identity
    # Independently specified 30 mm disagreement; neither input is replaced by an average.
    conflicting = secondary.model_copy(
        update={"point": (primary.point[0] + 0.03, *primary.point[1:])}
    )
    failed = compare_cameras("conflict", primary, conflicting, first, second, *limits)
    assert not failed.passed and failed.failures == ("CAMERA_POINTS_DISAGREE",)
    assert failed.difference_mm == pytest.approx(30)
    assert failed.primary_point_m == primary.point and failed.secondary_point_m == conflicting.point
    mount = np.array(second.candidate.y.matrix)
    mount[0, 3] += 0.04
    wrong_mount = second.model_copy(
        update={
            "candidate": second.candidate.model_copy(
                update={
                    "y": second.candidate.y.model_copy(update={"matrix": mount.tolist()}),
                }
            )
        }
    )
    assert (
        "UNCHANGED_MOUNT_ESTIMATES_DISAGREE"
        in compare_cameras(
            "mount-conflict",
            primary,
            secondary,
            first,
            wrong_mount,
            *limits,
        ).failures
    )
    distinct_mount = wrong_mount.model_copy(
        update={
            "candidate": wrong_mount.candidate.model_copy(
                update={
                    "board": wrong_mount.candidate.board.model_copy(
                        update={"mounting_id": "separate-board-mount"}
                    ),
                }
            )
        }
    )
    separate = compare_cameras("separate-mount", primary, secondary, first, distinct_mount, *limits)
    assert separate.shared_mount_identity is None and separate.mounting_translation_mm is None
    with pytest.raises(CalibrationError, match="INDEPENDENT_CAMERAS_REQUIRED"):
        compare_cameras("same-camera", primary, primary, first, first, *limits)
    with pytest.raises(CalibrationError, match="CAMERA_AGREEMENT_ARTIFACT_MISMATCH"):
        compare_cameras("wrong-artifact", primary, secondary, second, first, *limits)
    with pytest.raises(CalibrationError, match="CAMERA_AGREEMENT_ARTIFACT_MISMATCH"):
        compare_cameras(
            "wrong-profile",
            primary.model_copy(
                update={
                    "configuration_fingerprint": "different-profile",
                }
            ),
            secondary,
            first,
            second,
            *limits,
        )
    with pytest.raises(CalibrationError, match="MISSING_REFERENCE_LIMIT"):
        compare_cameras(
            "no-limit",
            primary,
            secondary,
            first,
            second,
            limits[0].model_copy(update={"max_reference_error_mm": None}),
            limits[1],
        )
    before_authority = service.store.active("camera-west")
    service.store.invalidate(
        "camera-east",
        "TEST_REFERENCE_CHECK_FAILED",
        Mutation(request_id="block-east", expected_revision=6),
    )
    assert service.store.active("camera-west") == before_authority
    with pytest.raises(CalibrationError, match="ACTIVE_CALIBRATION_SUSPECT"):
        observer.fresh(identity="affected-camera-blocks-observation")
