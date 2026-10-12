"""Content-addressed sensor artifacts. Readers verify bytes; writes never replace evidence."""

import hashlib
import io
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from robotops.calibration.contracts import ArtifactRef
from robotops.calibration.errors import CalibrationError


class SensorArtifacts:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _write(
        self, data: bytes, suffix: str, media_type: str, shape: tuple[int, ...]
    ) -> ArtifactRef:
        digest = hashlib.sha256(data).hexdigest()
        relative = f"{digest[:2]}/{digest}.{suffix}"
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, staging_name = tempfile.mkstemp(dir=target.parent, prefix=".capture-")
        staging = Path(staging_name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(staging, target)
            except FileExistsError:
                if target.read_bytes() != data:
                    raise CalibrationError("ARTIFACT_COLLISION") from None
        finally:
            staging.unlink(missing_ok=True)
        return ArtifactRef.model_validate(
            {
                "path": relative,
                "sha256": digest,
                "media_type": media_type,
                "shape": shape,
            }
        )

    def rgb(self, array: NDArray[np.uint8]) -> ArtifactRef:
        if array.ndim != 3 or array.shape[2] != 3 or array.dtype != np.uint8:
            raise CalibrationError("INVALID_RGB_ARRAY")
        success, encoded = cv2.imencode(".png", cv2.cvtColor(array, cv2.COLOR_RGB2BGR))
        if not success:
            raise CalibrationError("IMAGE_ENCODING_FAILED")
        return self._write(encoded.tobytes(), "png", "image/png", array.shape)

    def depth(self, array: NDArray[np.float32]) -> ArtifactRef:
        # Invalid values are deliberately retained: rejecting a measurement must not erase it.
        if array.ndim != 2 or array.dtype != np.float32:
            raise CalibrationError("INVALID_NATIVE_DEPTH_ARRAY")
        buffer = io.BytesIO()
        np.save(buffer, array, allow_pickle=False)
        return self._write(buffer.getvalue(), "npy", "application/x-npy", array.shape)

    def mask(self, array: NDArray[np.bool_]) -> ArtifactRef:
        if array.ndim != 2 or array.dtype != np.bool_:
            raise CalibrationError("INVALID_SURFACE_MASK_ARRAY")
        buffer = io.BytesIO()
        np.save(buffer, array, allow_pickle=False)
        return self._write(buffer.getvalue(), "npy", "application/x-npy", array.shape)

    def read_mask(self, reference: ArtifactRef) -> NDArray[np.bool_]:
        if reference.media_type != "application/x-npy":
            raise CalibrationError("MASK_ARTIFACT_TYPE")
        array = np.load(io.BytesIO(self.read(reference)), allow_pickle=False)
        if tuple(array.shape) != reference.shape or array.dtype != np.bool_:
            raise CalibrationError("MASK_ARTIFACT_SHAPE")
        return np.asarray(array, dtype=np.bool_)

    def read(self, reference: ArtifactRef) -> bytes:
        target = (self.root / reference.path).resolve()
        if not target.is_relative_to(self.root):
            raise CalibrationError("UNSAFE_ARTIFACT_PATH")
        try:
            data = target.read_bytes()
        except FileNotFoundError:
            raise CalibrationError("ARTIFACT_MISSING", reference.path) from None
        if hashlib.sha256(data).hexdigest() != reference.sha256:
            raise CalibrationError("ARTIFACT_HASH_MISMATCH", reference.path)
        return data

    def read_rgb(self, reference: ArtifactRef) -> NDArray[np.uint8]:
        if reference.media_type != "image/png":
            raise CalibrationError("RGB_ARTIFACT_TYPE")
        image = cv2.imdecode(np.frombuffer(self.read(reference), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or tuple(image.shape) != reference.shape:
            raise CalibrationError("RGB_ARTIFACT_SHAPE")
        return np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), dtype=np.uint8)

    def read_depth(self, reference: ArtifactRef) -> NDArray[np.float32]:
        if reference.media_type != "application/x-npy":
            raise CalibrationError("DEPTH_ARTIFACT_TYPE")
        array = np.load(io.BytesIO(self.read(reference)), allow_pickle=False)
        if tuple(array.shape) != reference.shape or array.dtype != np.float32:
            raise CalibrationError("DEPTH_ARTIFACT_SHAPE")
        return np.asarray(array, dtype=np.float32)
