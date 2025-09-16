import os
import sys
import numpy as np
import cv2

from PyQt6.QtCore import  QTimer
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication, QWidget

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from Context import gvars
from TinyRoiFile import TinyRoiFile
from StopWatch import StopWatch
from TinyRoiManager import TinyRoiManager
from RoiMeasurements import RoiMeasurements
from RoiImage import RoiImageWindow
from Stylesheet import overall
from TinyLog import log
from Roi import Roi

def test_roiimage():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'

    base_name = test_path+"C_stitch"
    zip_path = base_name + "_rois.zip"
    image_path= base_name + ".tiff"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    background_img = QImage(image_path)

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read_parallel(zip_path, label_image, num_threads=num_threads)
    StopWatch.stop("roi read")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)

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
    
    import random
    def toggle_image():
        msmt= random.choice(msmts)
        win.on_select_measurement(msmt_name=msmt)
        log(f"Triggering update: {msmt}")
    
    

    timer = QTimer()
    timer.timeout.connect(toggle_image)
    timer.start(5000) 

    sys.exit(app.exec())

if __name__ == "__main__":
    test_roiimage()