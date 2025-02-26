# ruff: noqa: E402
# To suppress the warning for E402, waiting for https://github.com/astral-sh/ruff/issues/3711
import gi

gi.require_version("Gst", "1.0")

import inspect

from gi.repository import Gst
from loguru import logger

from ..utils import try_set_state, wait_for_message

# Initialize GStreamer
if not Gst.is_initialized():
    Gst.init(None)


class AppsinkExtension:
    def register_appsink_callback(self, callback):
        """
        Register a callback function to be called when a new sample is available from an appsink.

        Args:
            callback: Callback function to be called
        """
        self.callback = callback
        self.appsinks = self.find_elements_by_name("appsink")
        for appsink in self.appsinks:
            appsink.set_property("emit-signals", True)
            appsink.set_property("wait-on-eos", False)
            appsink.set_property("max-buffers", 1)
            appsink.set_property("drop", True)
            appsink.connect("new-sample", self._on_new_sample)

    def _on_new_sample(self, appsink: Gst.Element) -> Gst.FlowReturn:
        """
        Handle new samples from appsinks.

        Args:
            appsink: Source appsink element

        Returns:
            Gst.FlowReturn: Status of sample processing
        """
        sample = appsink.emit("pull-sample")
        if sample is None:
            logger.error("Failed to get sample")
            return Gst.FlowReturn.ERROR

        kwargs = {}
        parameters = inspect.signature(self.callback).parameters
        if "pipeline" in parameters:
            kwargs["pipeline"] = self.pipeline
        if "appsink" in parameters:
            kwargs["appsink"] = appsink

        self.callback(sample, **kwargs)
        return Gst.FlowReturn.OK


class SeekExtension:
    pipeline: Gst.Pipeline

    # seek to the start time if provided. https://stackoverflow.com/questions/39454407/is-there-a-way-to-play-song-from-the-middle-in-gstreamer
    def seek(self, start_time: float | None = None, end_time: float | None = None):
        """
        Seek to specified time position in the media. Note that not every source(e.g. live source) supports seeking.

        Args:
            time_seconds: Time position to seek to in seconds
        """
        # check whether seeking is supported
        # query = Gst.Query.new_seeking(Gst.Format.TIME)
        # if not self.pipeline.query(query):
        #     logger.error("Seeking not supported by the pipeline.")
        #     return

        try_set_state(self.pipeline, Gst.State.PAUSED)

        # we may consider Gst.SeekFlags.KEY_UNIT flag (go to nearest keyframe) for more efficient seeking
        self.pipeline.seek(
            1.0,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            Gst.SeekType.SET if start_time is not None else Gst.SeekType.NONE,
            int(start_time * Gst.SECOND) if start_time is not None else 0,
            Gst.SeekType.SET if end_time is not None else Gst.SeekType.NONE,
            int(end_time * Gst.SECOND) if end_time is not None else 0,
        )

        # https://gstreamer.freedesktop.org/documentation/application-development/advanced/queryevents.html?gi-language=c
        # > You can wait (blocking) for the seek to complete with gst_element_get_state() or by waiting for the ASYNC_DONE message to appear on the bus.
        wait_for_message(self.pipeline, Gst.MessageType.ASYNC_DONE)

        _, position = self.pipeline.query_position(Gst.Format.TIME)
        _, duration = self.pipeline.query_duration(Gst.Format.TIME)
        logger.info(
            f"Seeked to {position / Gst.SECOND:.2f}/{duration / Gst.SECOND:.2f} seconds. "
            f"Requested time range: "
            f"{start_time:.2f} - {end_time:.2f} seconds. "
            if start_time is not None and end_time is not None
            else f"{'start' if start_time is None else start_time:.2f} - {'end' if end_time is None else end_time:.2f} seconds. "
        )


class FPSDisplayExtension:
    def enable_fps_display(self, callback=None):
        """
        Turn on FPS display on the video sink. Utilize the 'fpsdisplaysink' element.
        """
        fpsdisplaysink = self.find_elements_by_name("fpsdisplaysink")[0]

        def fps_measurement_callback(fpsdisplaysink, fps, droprate, avgfps):
            print(f"FPS: {fps}, Drop Rate: {droprate}, Average FPS: {avgfps}")

        _callback = fps_measurement_callback if callback is None else callback

        fpsdisplaysink.connect("fps-measurements", _callback)
        fpsdisplaysink.set_property("signal-fps-measurements", True)


__all__ = ["AppsinkExtension", "SeekExtension", "FPSDisplayExtension"]
