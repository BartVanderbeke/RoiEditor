
import os
import sys
import numpy as np
import cv2
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import  QTimer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.TinyRoiFile import TinyRoiFile
from RoiEditor.Lib.StopWatch import StopWatch

from RoiEditor.Lib.Context import gvars
from RoiEditor.Lib.Roi import Roi
from RoiEditor.Lib.HistogramFrame import HistogramFrame
from RoiEditor.Lib.RoiMeasurements import RoiMeasurements
from RoiEditor.Lib.TinyLog import log
from RoiEditor.Lib.MeasurementWorker import compute_and_plot


def test_msmtwrkr():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "./TestData/")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    base_name = test_path+"C_stitch"
    zip_path = base_name + "_rois.zip"
    zip_out_path = base_name + "_RoiSet.zip"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read_parallel(zip_path, label_image, num_threads=num_threads)
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


    timer = QTimer()
    timer.timeout.connect(toggle_image)
    timer.start(5000)  
        

    sys.exit(app.exec())


if __name__ == "__main__":
    test_msmtwrkr()