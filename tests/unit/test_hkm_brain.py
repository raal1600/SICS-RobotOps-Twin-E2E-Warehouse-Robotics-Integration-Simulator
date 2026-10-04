from datetime import timedelta

import pytest

from robotops.brain.deterministic import DeterministicBrain, parse_structured_output
from robotops.brain.validation import ActionValidator
from robotops.config import Settings
from robotops.domain.models import (
    CellState,
    ObservedMachineState,
    ObservedObject,
    OrderLine,
    OrderRequest,
    WorldObservation,
    utc_now,
)
from robotops.robotics.catalogue import fixture_source_pose, initial_tool_state, load_catalogue
from robotops.workflow.store import Store, metadata


def planning_context(tmp_path, sku="SKU-A"):
    settings = Settings.hkm()
    product = next(item for item in settings.products if item.sku == sku)
    store = Store(tmp_path / "workflow.db")
    order = store.intake(
        OrderRequest(
            order_id="hkm-brain-order",
            lines=(
                OrderLine(
                    order_line_id="line",
                    product_id=product.product_id,
                    source_id=settings.source_for(product.product_id),
                    destination_id=settings.destination_id,
                ),
            ),
        ),
        "hkm-brain-key",
    )
    job = store.job(order.job_ids[0])
    catalogue = load_catalogue()
    sensors = tuple(sensor for sensor in catalogue.cameras if not sensor.presentation_only)
    now = utc_now()
    observation = WorldObservation(
        schema_version="2.0",
        **metadata(job, now=now),
        observation_id="hkm-observation",
        scene_epoch="hkm-epoch",
        step=0,
        captured_at=now,
        model_version="synthetic-observer-2",
        calibration_version=settings.calibration_version,
        cell_generation=0,
        robot_profile_version=catalogue.profile_version,
        frame_tree_version=catalogue.frame_tree_version,
        sensors=sensors,
        machine_telemetry=ObservedMachineState(
            tool_state=initial_tool_state(),
            tcp_pose=catalogue.layout.home_tcp_pose,
            captured_at=now,
            cell_generation=0,
        ),
        objects=tuple(
            ObservedObject(
                schema_version="2.0",
                product_id=item.product_id,
                location_id=settings.source_for(item.product_id),
                pose=fixture_source_pose(item.sku),
                confidence=0.99,
                sensor_id=sensors[0].sensor_id,
                evidence_source="SYNTHETIC_OBSERVATION_MODEL",
            )
            for item in settings.products
        ),
        covered_locations=tuple(location.location_id for location in settings.locations),
    )
    destination = next(
        location
        for location in settings.locations
        if location.location_id == settings.destination_id
    )
    cell = CellState(**metadata(job, now=now))
    return settings, job, observation, destination, cell


@pytest.mark.parametrize(
    "sku,tool",
    [
        ("SKU-A", "EE_VAC_SINGLE"),
        ("SKU-B", "EE_VAC_ARRAY"),
        ("SKU-C", "EE_ADAPTIVE_SOFT"),
        ("SKU-D", "EE_PINCH_NARROW"),
        ("SKU-E", "EE_PINCH_WIDE"),
        ("SKU-F", "EE_SUPPORT_FORK"),
    ],
)
def test_hkm_brain_builds_valid_explainable_observation_only_plan(tmp_path, sku, tool):
    settings, job, observation, destination, cell = planning_context(tmp_path, sku)
    brain = DeterministicBrain(settings)
    first = brain.plan(job, observation, destination)
    assert first == brain.plan(job, observation, destination)
    assert first.schema_version == "2.0" and first.brain_version == "deterministic-hkm-1"
    assert first.selected_tool_id == tool
    assert first.tool_selection.product_id == job.line.product_id
    assert first.tool_selection.sku == sku
    assert first.target_pose == settings.target_pose(job.line.product_id, destination)
    assert first.grasp_pose == first.trajectory.grasp_pose
    assert parse_structured_output(first.model_dump_json()) == first
    assert ActionValidator(settings).validate(first, job, observation, cell, destination) == first


def test_hkm_brain_refuses_missing_other_product_evidence_for_collision(tmp_path):
    settings, job, observation, destination, _ = planning_context(tmp_path)
    missing_other = observation.model_copy(update={"objects": observation.objects[:-1]})
    with pytest.raises(ValueError, match="MISSING_OBSERVATION"):
        DeterministicBrain(settings).plan(job, missing_other, destination)
    unknown = observation.objects[-1].model_copy(update={"product_id": "unconfigured-object"})
    with pytest.raises(ValueError, match="UNKNOWN_OBSERVED_PRODUCT"):
        DeterministicBrain(settings).plan(
            job,
            observation.model_copy(update={"objects": observation.objects[:-1] + (unknown,)}),
            destination,
        )
    uncovered = observation.model_copy(
        update={"covered_locations": observation.covered_locations[1:]}
    )
    with pytest.raises(ValueError, match="COVERAGE_INSUFFICIENT"):
        DeterministicBrain(settings).plan(job, uncovered, destination)


def test_hkm_brain_refuses_contradictory_observations_even_if_product_would_fit(tmp_path):
    settings, job, observation, destination, _ = planning_context(tmp_path)
    contradiction = observation.objects[0].model_copy(
        update={
            "location_id": settings.destination_id,
            "sensor_id": observation.sensors[1].sensor_id,
        }
    )
    changed = observation.model_copy(update={"objects": observation.objects + (contradiction,)})
    with pytest.raises(ValueError, match="CONTRADICTORY_OBSERVATION"):
        DeterministicBrain(settings).plan(job, changed, destination)


def test_hkm_validator_rejects_stale_or_foreign_machine_telemetry(tmp_path):
    settings, job, observation, destination, cell = planning_context(tmp_path)
    plan = DeterministicBrain(settings).plan(job, observation, destination)
    validator = ActionValidator(settings)
    for delta in (-10, 10):
        telemetry = observation.machine_telemetry.model_copy(
            update={"captured_at": observation.captured_at + timedelta(seconds=delta)}
        )
        # The wire contract rejects capture skew before planning can use telemetry.
        with pytest.raises(ValueError, match="TELEMETRY_CAPTURE_MISMATCH"):
            validator.validate(
                plan,
                job,
                observation.model_copy(update={"machine_telemetry": telemetry}),
                cell,
                destination,
            )
    telemetry = observation.machine_telemetry.model_copy(
        update={
            "tcp_pose": observation.machine_telemetry.tcp_pose.model_copy(
                update={"frame_id": "foreign"}
            )
        }
    )
    with pytest.raises(ValueError, match="TELEMETRY_SPATIAL_METADATA_MISMATCH"):
        validator.validate(
            plan,
            job,
            observation.model_copy(update={"machine_telemetry": telemetry}),
            cell,
            destination,
        )


def test_hkm_validator_recomputes_selection_explanation_and_trajectory(tmp_path):
    settings, job, observation, destination, cell = planning_context(tmp_path)
    plan = DeterministicBrain(settings).plan(job, observation, destination)
    validator = ActionValidator(settings)
    candidates = plan.tool_selection.candidate_tools
    altered_candidate = candidates[0].model_copy(update={"score": candidates[0].score + 1})
    selection = plan.tool_selection.model_copy(
        update={"candidate_tools": (altered_candidate,) + candidates[1:]}
    )
    with pytest.raises(ValueError, match="TOOL_SELECTION_EVIDENCE_MISMATCH"):
        validator.validate(
            plan.model_copy(update={"tool_selection": selection}),
            job,
            observation,
            cell,
            destination,
        )
    with pytest.raises(ValueError, match="HKM_BRAIN_VERSION_MISMATCH"):
        validator.validate(
            plan.model_copy(update={"brain_version": "deterministic-1"}),
            job,
            observation,
            cell,
            destination,
        )
    shifted_home = plan.trajectory.waypoints[0].model_copy(
        update={
            "pose": plan.trajectory.waypoints[0].pose.model_copy(
                update={"position": (0.05, -0.6, 1.02)}
            )
        }
    )
    trajectory = plan.trajectory.model_copy(
        update={"waypoints": (shifted_home,) + plan.trajectory.waypoints[1:]}
    )
    with pytest.raises(ValueError, match="TRAJECTORY_INTENT_MISMATCH"):
        validator.validate(
            plan.model_copy(update={"trajectory": trajectory}), job, observation, cell, destination
        )


def test_hkm_validator_rejects_legacy_plan_and_injected_code(tmp_path):
    settings, job, observation, destination, cell = planning_context(tmp_path)
    legacy_plan = DeterministicBrain().plan(job, observation, destination)
    # Give the legacy proposal the expected target; schema version still cannot bypass validation.
    legacy_plan = legacy_plan.model_copy(
        update={"target_pose": settings.target_pose(job.line.product_id, destination)}
    )
    with pytest.raises(ValueError, match="HKM_PROFILE_REQUIRES_VERSION_2"):
        ActionValidator(settings).validate(legacy_plan, job, observation, cell, destination)
    with pytest.raises(ValueError):
        parse_structured_output('{"schema_version":"2.0","python":"arbitrary_robot_code()"}')
