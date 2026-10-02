import pytest

from robotops.brain.deterministic import DeterministicBrain
from robotops.brain.validation import ActionValidator
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Fault, Pose
from robotops.observation.model import ObservationModel
from robotops.workflow.store import Store


@pytest.mark.parametrize(
    "updates",
    [
        {"job_id": "other"},
        {"product_id": "product-blue"},
        {"source_id": "wrong"},
        {"destination_id": "wrong"},
        {"order_line_id": "other"},
        {"run_id": "other"},
        {"scene_epoch": "old"},
        {"observation_id": "old"},
        {"cell_generation": 100},
        {"target_pose": Pose(position=(10, 0, 1))},
    ],
)
def test_validator_rejects_semantically_invalid_brain_output(tmp_path, order_request, updates):
    store = Store(tmp_path / "s.db")
    runtime = SyntheticRuntime(tmp_path / "r.db")
    job = store.job(store.intake(order_request, "key").job_ids[0])
    world = runtime.world()
    observation = ObservationModel().observe(world)
    destination = world.locations[1]
    plan = DeterministicBrain().plan(job, observation, destination)
    with pytest.raises(ValueError):
        ActionValidator().validate(
            plan.model_copy(update=updates), job, observation, world.cell, destination
        )


@pytest.mark.parametrize(
    "fault",
    [
        Fault.LOW_CONFIDENCE_OBSERVATION,
        Fault.STALE_OBSERVATION,
        Fault.MISSING_OBSERVATION,
        Fault.CONTRADICTORY_OBSERVATION,
        Fault.POSE_UNCERTAINTY,
    ],
)
def test_validator_requires_usable_pre_execution_observation(tmp_path, order_request, fault):
    store = Store(tmp_path / "s.db")
    runtime = SyntheticRuntime(tmp_path / "r.db")
    job = store.job(store.intake(order_request, "key").job_ids[0])
    world = runtime.world()
    observation = ObservationModel().observe(world, fault)
    destination = world.locations[1]
    plan = DeterministicBrain().plan(job, observation, destination)
    with pytest.raises(ValueError):
        ActionValidator().validate(plan, job, observation, world.cell, destination)


def test_pose_noise_is_configured_and_reproducible(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "r.db")
    observer = ObservationModel(Settings(seed=42, pose_noise_m=0.01))
    a = observer.observe(runtime.world())
    b = observer.observe(runtime.world())
    assert a.objects == b.objects
    assert a.objects[0].uncertainty_m == 0.01
    assert a.objects[0].pose.position != runtime.world().objects[0].pose.position
