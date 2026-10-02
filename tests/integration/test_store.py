from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest

from robotops.domain.models import JobState, OrderRequest, utc_now
from robotops.workflow.store import Conflict, OwnershipError, Store


def test_duplicate_order_same_payload_and_restart(tmp_path, order_request):
    path = tmp_path / "workflow.db"
    store = Store(path)
    original = store.intake(order_request, "key")
    assert store.intake(order_request, "key") == original
    restarted = Store(path)
    assert restarted.intake(order_request, "key") == original
    assert len(restarted.recoverable()) == 1
    assert len(restarted.timeline(original.order_id)) == 2
    assert restarted.run_id == store.run_id


def test_duplicate_order_conflict(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    store.intake(order_request, "key")
    changed = OrderRequest.model_validate({**order_request.model_dump(), "order_id": "other"})
    with pytest.raises(Conflict, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        store.intake(changed, "key")
    changed = OrderRequest.model_validate(
        {
            **order_request.model_dump(),
            "lines": [{**order_request.lines[0].model_dump(), "product_id": "product-blue"}],
        }
    )
    with pytest.raises(Conflict, match="ORDER_ID_CONFLICT"):
        store.intake(changed, "different-key")


def test_two_worker_claim_race(tmp_path, order_request):
    path = tmp_path / "workflow.db"
    store = Store(path)
    order = store.intake(order_request, "key")
    barrier = Barrier(2)

    def worker(owner):
        repo = Store(path)
        barrier.wait()
        return repo.claim(order.job_ids[0], owner, 30)

    with ThreadPoolExecutor(2) as pool:
        claims = list(pool.map(worker, ["worker-a", "worker-b"]))
    assert sum(c is not None for c in claims) == 1


def test_expired_claim_is_fenced_and_transition_is_atomic(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    job_id = store.intake(order_request, "key").job_ids[0]
    start = utc_now()
    old = store.claim(job_id, "a", 1, now=start)
    fresh = store.claim(job_id, "b", 30, now=start + timedelta(seconds=2))
    assert old and fresh and fresh.fence > old.fence
    with pytest.raises(OwnershipError):
        store.transition(job_id, JobState.VALIDATED, "VALID", claim=old)
    assert store.job(job_id).state == JobState.RECEIVED
    assert len(store.timeline()) == 2
    store.transition(job_id, JobState.VALIDATED, "VALID", claim=fresh)
    assert Store(store.path).job(job_id).state == JobState.VALIDATED
    event = store.timeline()[-1]
    assert event.state_before == "RECEIVED" and event.state_after == "VALIDATED"
    assert event.causation_id == store.timeline()[-2].event_id
    store.release(old)
    assert store.claim(job_id, "c", 30) is None


def test_intake_is_atomic_during_race(tmp_path, order_request):
    path = tmp_path / "workflow.db"
    Store(path)
    barrier = Barrier(2)

    def worker(_):
        repo = Store(path)
        barrier.wait()
        return repo.intake(order_request, "key")

    with ThreadPoolExecutor(2) as pool:
        result = list(pool.map(worker, range(2)))
    assert result[0] == result[1]
    assert len(Store(path).recoverable()) == 1
