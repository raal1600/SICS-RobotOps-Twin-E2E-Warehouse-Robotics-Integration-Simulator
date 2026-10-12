import cv2
import numpy as np
import pytest

from robotops.calibration.inspection import depth_display, depth_preview


def test_preview_declares_raw_quantiles_clipping_and_missing_pixels_without_changing_depth():
    raw = np.array([[0, -1, np.nan, np.inf, 100, 200, 300, 400, 500]], dtype=np.float32)
    saved = raw.copy()
    info = depth_display(raw)
    assert info.low_raw == pytest.approx(104)
    assert info.high_raw == pytest.approx(496)
    assert info.valid_pixels == 5 and info.invalid_pixels == 4
    colored = depth_preview(raw)
    np.testing.assert_array_equal(colored[0, :4], np.tile([255, 0, 255], (4, 1)))
    expected = cv2.applyColorMap(np.array([[0, 255]], np.uint8), cv2.COLORMAP_TURBO)
    np.testing.assert_array_equal(colored[0, 4], expected[0, 0])
    np.testing.assert_array_equal(colored[0, -1], expected[0, -1])
    np.testing.assert_array_equal(raw, saved)


def test_all_missing_depth_has_no_invented_numeric_range():
    raw = np.array([[0, np.nan]], dtype=np.float32)
    assert depth_display(raw).low_raw is None
    assert depth_display(raw).high_raw is None
    assert depth_display(raw).valid_pixels == 0
    np.testing.assert_array_equal(depth_preview(raw)[0], [[255, 0, 255], [255, 0, 255]])
