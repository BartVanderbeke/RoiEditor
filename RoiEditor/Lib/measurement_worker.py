"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject

from roi_measurements import RoiMeasurements
from tiny_log import log
from roi import Roi
from histogram_frame import HistogramFrame
from tiny_roi_manager import TinyRoiManager


def calculate_measurements(msmts: RoiMeasurements):
        #if not msmts.subset_all_calculated:
        #    log("First calculation of measurements started", type="info", log_level=1000)
            #msmts.compute_stats_subset(subset_name="ALL")
        #else:
        msmts.compute_stats_subset(subset_name="ALL")
        log("(Re)calculation of measurements started", type="info", log_level=1000)

        subset_name = "DELETED"
        filter = lambda roi: (roi.state == Roi.ROI_STATE_DELETED) if roi else False
        msmts.define_subset(subset_name=subset_name, filter=filter)
        msmts.compute_stats_subset(subset_name)

        subset_name = "ACTIVE"
        filter = lambda roi: (roi.state == Roi.ROI_STATE_ACTIVE) if roi else False
        msmts.define_subset(subset_name=subset_name, filter=filter)
        msmts.compute_stats_subset(subset_name)

        subset_name = "SELECTED"
        filter = lambda roi: (roi.state == Roi.ROI_STATE_SELECTED) if roi else False
        msmts.define_subset(subset_name=subset_name, filter=filter)
        msmts.compute_stats_subset(subset_name)


class MeasurementWorkerSignals(QObject):
    finished = pyqtSignal(object)

class MeasurementWorker(QRunnable):
    def __init__(self, rm,msmts):
        super().__init__()
        self.rm = rm
        self.msmts =msmts
        self.signals = MeasurementWorkerSignals()

    def run(self):
        calculate_measurements(msmts=self.msmts)
        self.signals.finished.emit(self.msmts)



def compute_and_plot(rm: TinyRoiManager,hist_plot:HistogramFrame, msmts: RoiMeasurements, on_finished_callback=None):
    def on_worker_done(msmts):
        if HistogramFrame.is_histogram_populated(hist_plot):
            hist_plot.update_plot()
        else:
            hist_plot.populate(msmts.measurement_names, "Area", msmts)


            hist_plot.show()

        if on_finished_callback and callable(on_finished_callback):
            on_finished_callback()

        log("Measurements available and plot updated", type="info", log_level=1000)


    worker = MeasurementWorker(rm,msmts)
    worker.signals.finished.connect(on_worker_done)

    QThreadPool.globalInstance().start(worker)
    #calculate_measurements(msmts)
    #on_worker_done(msmts)

