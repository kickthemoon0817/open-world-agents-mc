# ruff: noqa: E402
# To suppress the warning for E402, waiting for https://github.com/astral-sh/ruff/issues/3711
import inspect

import gi

gi.require_version("Gst", "1.0")


from gi.repository import Gst
from loguru import logger

from owa.registry import LISTENERS

from ..gst_factory import screen_capture_pipeline
from ..gst_runner import GstPipelineRunner
from ..utils import sample_to_ndarray
from .msg import FrameStamped

if not Gst.is_initialized():
    Gst.init(None)


class MetricManager:
    def __init__(self):
        """Initialize the metric manager with empty history."""
        self._timestamps = []
        self._latencies = []
        # Keep a reasonable history length to avoid memory issues
        self._max_history = 100

    def append(self, timestamp_ns: int, latency: float):
        """
        Add a new frame timestamp and latency measurement.

        Args:
            timestamp_ns: Frame timestamp in nanoseconds
            latency: Processing latency in milliseconds
        """
        self._timestamps.append(timestamp_ns)
        self._latencies.append(latency)

        # Maintain history size limit
        if len(self._timestamps) > self._max_history:
            self._timestamps.pop(0)
            self._latencies.pop(0)

    @property
    def latency(self):
        """
        Returns the average latency in seconds.

        Returns:
            float: Average latency or 0.0 if no data
        """
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies) / Gst.SECOND

    @property
    def fps(self):
        """
        Calculate frames per second based on recorded timestamps.

        Returns:
            float: Calculated FPS or 0.0 if insufficient data
        """
        if len(self._timestamps) < 2:
            return 0.0

        # Calculate time difference between first and last frame in seconds
        # Convert from nanoseconds to seconds
        time_diff_sec = (self._timestamps[-1] - self._timestamps[0]) / 1e9

        if time_diff_sec <= 0:
            return 0.0

        # Calculate frames per second
        return (len(self._timestamps) - 1) / time_diff_sec


def build_screen_callback(callback):
    metric_manager = MetricManager()

    def screen_callback(sample: Gst.Sample, pipeline: Gst.Pipeline, metadata: dict):
        frame_arr = sample_to_ndarray(sample)
        latency = metadata["latency"]
        timestamp_ns = metadata["frame_time_ns"]
        metric_manager.append(timestamp_ns, latency)

        message = FrameStamped(timestamp_ns=timestamp_ns, frame_arr=frame_arr)
        params = inspect.signature(callback).parameters
        if len(params) == 1:
            callback(message)
        else:
            callback(message, metric_manager)

    return screen_callback


@LISTENERS.register("screen")
class ScreenListener(GstPipelineRunner):
    """
    GStreamer-based screen capture listener.

    Captures screen content and delivers frames to a callback function.
    Can capture specific windows, monitors, or the entire screen.

    Example:
    ```python
    from owa.registry import LISTENERS, activate_module
    import cv2
    import numpy as np

    # Activate the GStreamer module
    activate_module("owa_env_gst")

    # Define a callback to process frames
    def process_frame(frame):
        # Display the frame
        cv2.imshow("Screen Capture", frame.frame_arr)
        cv2.waitKey(1)

    # Create and configure the listener
    screen = LISTENERS["screen"]().configure(
        callback=process_frame,
        fps=30,
        show_cursor=True
    )

    # Run the screen capture
    with screen.session:
        input("Press Enter to stop")
    ```

    For performance metrics:
    ```python
    def process_with_metrics(frame, metrics):
        print(f"FPS: {metrics.fps:.2f}, Latency: {metrics.latency*1000:.2f} ms")
        cv2.imshow("Screen", frame.frame_arr)
        cv2.waitKey(1)

    screen.configure(callback=process_with_metrics)
    ```
    """

    def on_configure(
        self,
        *,
        callback,
        show_cursor: bool = True,
        fps: float = 60,
        window_name: str | None = None,
        monitor_idx: int | None = None,
        additional_args: str | None = None,
    ) -> bool:
        """
        Configure the GStreamer pipeline for screen capture.

        Keyword Arguments:
            callback: Function to call with each captured frame
            show_cursor (bool): Whether to show the cursor in the capture.
            fps (float): Frames per second.
            window_name (str | None): (Optional) specific window to capture.
            monitor_idx (int | None): (Optional) specific monitor index.
            additional_args (str | None): (Optional) additional arguments to pass to the pipeline.
        """
        # Construct the pipeline description
        pipeline_description = screen_capture_pipeline(
            show_cursor=show_cursor,
            fps=fps,
            window_name=window_name,
            monitor_idx=monitor_idx,
            additional_args=additional_args,
        )
        logger.debug(f"Constructed pipeline: {pipeline_description}")
        super().on_configure(pipeline_description)

        wrapped_callback = build_screen_callback(callback)
        self.register_appsink_callback(wrapped_callback)
