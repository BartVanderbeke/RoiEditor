
import os
import sys
import numpy as np
import cv2
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import  QTimer
import random
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from nptyping import NDArray, Shape, Float64

from TinyRoiManager import TinyRoiManager
from TinyRoiFile import TinyRoiFile
from StopWatch import StopWatch


from Roi import Roi
from HistogramFrame import HistogramFrame
from RoiMeasurements import RoiMeasurements
from TinyLog import log
from MeasurementWorker import compute_and_plot



states = [Roi.ROI_STATE_ACTIVE, Roi.ROI_STATE_DELETED, Roi.ROI_STATE_SELECTED]

def test_msmtwrkr():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "./TestData/")
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    base_name = test_path+"6"
    zip_path = base_name + "_rois.zip"
    zip_out_path = base_name + "_RoiSet.zip"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read(zip_path, label_image)
    StopWatch.stop("roi read")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)
            roi.color: NDArray[Shape["1, 3"], Float64] = np.array([0.0, 0.0, 0.0])
            roi.state= random.choice(states)

    hist_plot= HistogramFrame()
    msmts = RoiMeasurements(rm)
    if auto_close_ms > 0:
        msmts.compute_stats_subset("ALL")
        hist_plot.populate(msmts.measurement_names, "Area", msmts)
        hist_plot.show()
        QTimer.singleShot(auto_close_ms, app.quit)
    else:
        compute_and_plot(rm,hist_plot,msmts=msmts)
        log("First round finished, waiting for updates (every 5s)")

        l=[Roi.ROI_STATE_ACTIVE,Roi.ROI_STATE_SELECTED]
        
        def toggle_image():
            log("Triggering update")
            for _,roi in rm:
                roi.state =  random.choice(states)
            compute_and_plot(rm,hist_plot,msmts)


        timer = QTimer()
        timer.timeout.connect(toggle_image)
        timer.start(5000)

    sys.exit(app.exec())


if __name__ == "__main__":
    test_msmtwrkr()
