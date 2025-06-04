"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication
import sys

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

if __name__ == "__main__":
    from TinyRoiFile import TinyRoiFile
    import StopWatch
    from TinyRoiManager import TinyRoiManager
    from Context import gvars
    from Roi import Roi

    app = QApplication(sys.argv)

    base_name = "C_stitch_RoiSet"
    zip_path = base_name + ".zip"
    zip_out_path = base_name + "_OUT.zip"
    num_threads = 12

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
    StopWatch.stop("roi read")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)

    hist_plot= HistogramFrame()
    msmts = RoiMeasurements(rm)
    compute_and_plot(rm,hist_plot,msmts=msmts)
    log("First round finished, waiting for updates (every 5s)")
    import random

    l=[Roi.ROI_STATE_ACTIVE,Roi.ROI_STATE_SELECTED]
    
    def toggle_image():
        log("Triggering update")
        for _,roi in rm:
            roi.state= random.choice(l)
        compute_and_plot(rm,hist_plot,msmts)

    
    from PyQt6.QtCore import  QTimer
    timer = QTimer()
    timer.timeout.connect(toggle_image)
    timer.start(5000)  
        

    sys.exit(app.exec())
