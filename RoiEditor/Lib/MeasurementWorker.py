"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject

from .RoiMeasurements import RoiMeasurements
from .TinyLog import log
from .Context import gvars
from .Roi import Roi
from .HistogramFrame import HistogramFrame
from .TinyRoiManager import TinyRoiManager

class MeasurementWorkerSignals(QObject):
    finished = pyqtSignal(object)

class MeasurementWorker(QRunnable):
    def __init__(self, rm,msmts):
        super().__init__()
        self.rm = rm
        self.msmts =msmts
        self.signals = MeasurementWorkerSignals()

    def run(self):
        if not self.msmts.subset_all_calculated:
            log("First calculation of measurements started")
            self.msmts.compute_stats_subset(subset_name="ALL")
        else:
            log("Re-calculation of measurements started")


        subset_name = "DELETED"
        filter = lambda roi: (roi.state == Roi.ROI_STATE_DELETED) if roi else False
        self.msmts.define_subset(subset_name=subset_name, filter=filter)
        self.msmts.compute_stats_subset(subset_name)

        subset_name = "ACTIVE"
        filter = lambda roi: (roi.state == Roi.ROI_STATE_ACTIVE) if roi else False
        self.msmts.define_subset(subset_name=subset_name, filter=filter)
        self.msmts.compute_stats_subset(subset_name)

        subset_name = "SELECTED"
        filter = lambda roi: (roi.state == Roi.ROI_STATE_SELECTED) if roi else False
        self.msmts.define_subset(subset_name=subset_name, filter=filter)
        self.msmts.compute_stats_subset(subset_name)

        self.signals.finished.emit(self.msmts)



def compute_and_plot(rm: TinyRoiManager,hist_plot:HistogramFrame, msmts: RoiMeasurements):
    def on_worker_done(msmts_param):
        if HistogramFrame.is_histogram_populated(hist_plot):
            hist_plot.update_plot()
        else:
            hist_plot.populate(msmts_param.measurement_names, "Area", msmts_param)
            hist_plot.show()

        log("Measurements available and plot updated")        


    worker = MeasurementWorker(rm,msmts)
    worker.signals.finished.connect(on_worker_done)

    QThreadPool.globalInstance().start(worker)

