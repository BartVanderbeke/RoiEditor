import os
import sys
import numpy as np
import cv2

from PyQt6.QtCore import  QTimer
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication, QWidget
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from context import gvars
from tiny_roi_file import TinyRoiFile
from stop_watch import StopWatch
from tiny_roi_manager import TinyRoiManager
from roi_measurements import RoiMeasurements
from roi_image import RoiImageWindow
from stylesheet import overall
from tiny_log import log
from roi import Roi

def test_roiimage():
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'

    base_name = test_path+"6"
    zip_path = base_name + "_rois.zip"
    image_path= base_name + ".tif"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    background_img = QImage(image_path)

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read(zip_path, label_image)
    StopWatch.stop("roi read")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)

    if auto_close_ms <= 0:
        StopWatch.start("Feret")
        rm.force_feret()
        StopWatch.stop("Feret")
    
    StopWatch.start("msmts all")
    msmts = RoiMeasurements(rm)
    StopWatch.stop("msmts all")

    def on_any_change(str):
        log(f"Something changed: {str}")
    
    class DummyParent(QWidget):
        def on_add_nucleus_here(roi: Roi,here):
            log(f"DummyParent.on_add_nucleus_here: {roi.name}, {here}")


    dummy = DummyParent()
    dummy.setStyleSheet(overall)

    win = RoiImageWindow(qimage=background_img,rm=rm,nd=None,msmts=msmts, on_any_change=on_any_change,parent=dummy)


    win.draw_image()
    win.showNormal()

    win.on_select_measurement(msmt_name="Area")
    #win.on_set_overlay_visibility(overlay_visible=True)

    msmts=["Area","Feret", "FeretAngle", "AngleShifted","MinFeret", "FeretX", "FeretY", "FeretRatio"]
    if auto_close_ms > 0:
        msmts = ["Area"]
    
    import random
    def toggle_image():
        msmt= random.choice(msmts)
        win.on_select_measurement(msmt_name=msmt)
        log(f"Triggering update: {msmt}")
    
    

    if auto_close_ms > 0:
        QTimer.singleShot(auto_close_ms, app.quit)
    else:
        timer = QTimer()
        timer.timeout.connect(toggle_image)
        timer.start(5000) 

    sys.exit(app.exec())

if __name__ == "__main__":
    test_roiimage()
