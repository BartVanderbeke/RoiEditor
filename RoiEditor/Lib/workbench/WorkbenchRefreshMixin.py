from MeasurementWorker import compute_and_plot
from TinyLog import log


class WorkbenchRefreshMixin:
    def on_measurement_selected(self, msmt_name: str):
        self.roi_window.on_select_measurement(msmt_name)

    def on_any_change_callback(self, rebuild: bool | None = False):
        self.roi_window.draw_image(rebuild=rebuild if rebuild is not None else False)
        assert all(roi.color is not None for roi in self.rm["cell"].list_rois())

    def on_any_change(self, message: str = "", rebuild: bool | None = False):
        log("Updating: " + message, type="info", log_level=1000)
        on_finished = lambda: self.on_any_change_callback(rebuild=rebuild)
        compute_and_plot(
            self.rm["cell"],
            self.hist_plot,
            self.measurements,
            on_finished_callback=on_finished,
        )

    def on_toggle_show_deleted(self):
        self.roi_window.draw_image()

    def on_toggle_show_names(self):
        log("Toggling show names", type="info", log_level=1000)
        self.roi_window.draw_image()

    def on_toggle_show_overlay(self):
        self.roi_window.draw_image()

