"""Actual RGB readout distortion creates measured corner exclusions and rejections."""

import hashlib
import json
import shutil

import pytest

from robotops.calibration.contracts import Capture, PoseSample
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_rgb_warp_records_real_excluded_pixels_and_reproduces_the_quality_decision(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=113))
    service = Engine(Store(tmp_path / "workflow.db"), runtime).calibration
    camera = "camera-west"

    def request(identity):
        return Mutation(request_id=identity, expected_revision=service.store.state(camera).revision)

    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    service.introduce_fault(camera, "rgb_corner_warp", request("warp"))
    service.acquire(camera, "training-readout-warp", request("measure"))
    with service.store.store.readonly_connect() as db:
        samples = [
            PoseSample.model_validate_json(row[0])
            for row in db.execute("SELECT body FROM calibration_records WHERE kind='sample'")
        ]
        rejections = [
            json.loads(row[0])
            for row in db.execute("SELECT body FROM calibration_records WHERE kind='rejection'")
        ]
    excluded = [sample for sample in samples if sample.excluded_corner_ids]
    assert excluded, "This fixed training scene must expose actual measured outliers"
    assert any(item["reason"] == "PNP_POSE_UNDERCONSTRAINED" for item in rejections)
    for sample in excluded:
        assert len(sample.excluded_image_points_px) == len(sample.excluded_corner_ids)
        assert not set(sample.excluded_corner_ids) & set(sample.corner_ids)
        assert all(
            0 <= point[0] < 960 and 0 <= point[1] < 720 for point in sample.excluded_image_points_px
        )
        capture = service.store.record("capture", sample.capture_id, Capture)
        assert capture.sensor_fault_ids
    with pytest.raises(CalibrationError, match="SUSPECT|APPROVED"):
        service.store.active(camera)
    service.export(tmp_path / "export")
    result = reproduce(tmp_path / "export")
    assert result["passed"], result
    # A copied adversarial bundle cannot replace the saved excluded pixel with a
    # made-up value, even if its record hash is recomputed. Original evidence stays intact.
    shutil.copytree(tmp_path / "export", tmp_path / "tampered-copy")
    manifest_path = tmp_path / "tampered-copy" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    altered = next(
        item
        for item in manifest["records"]
        if item["kind"] == "sample" and item["id"] == excluded[0].capture_id
    )
    altered["body"]["excluded_image_points_px"][0][0] += 8
    altered["sha256"] = hashlib.sha256(
        json.dumps(altered["body"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CalibrationError, match="RECOMPUTED_CORNERS_DIFFER"):
        reproduce(tmp_path / "tampered-copy")
    (tmp_path / "excluded-corners.json").write_text(
        json.dumps([sample.model_dump(mode="json") for sample in excluded], indent=2),
        encoding="utf-8",
    )
