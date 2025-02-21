import time

import pytest

from owa.registry import RUNNABLES, activate_module


@pytest.fixture(scope="module")
def screen_capture():
    activate_module("owa_env_gst")
    capture = RUNNABLES["screen_capture"]()
    capture.start()
    capture.configure(fps=60)
    yield capture
    capture.stop()
    capture.join()


def test_screen_capture_warmup(screen_capture):
    """Test that the screen capture produces RGBA frames during warm-up."""
    for _ in range(15):
        frame_msg = screen_capture.grab()

    assert frame_msg.frame_arr.shape[2] == 4 and frame_msg.frame_arr.ndim == 3, (
        f"Expected RGBA frame but got {frame_msg.frame_arr.shape}"
    )
    print(f"timestamp_ns: {frame_msg.timestamp_ns}, frame_arr.shape: {frame_msg.frame_arr.shape}")


def test_screen_capture_timing(screen_capture):
    """Test the elapsed time for capturing 30 frames."""
    now = time.time()
    for _ in range(30):
        frame_msg = screen_capture.grab()  # noqa: F841
    elapsed_time = time.time() - now
    print(f"Elapsed time to capture 30 frames: {elapsed_time:.3f}s")
    assert elapsed_time < 1.0, "Capturing 30 frames took longer than expected."
