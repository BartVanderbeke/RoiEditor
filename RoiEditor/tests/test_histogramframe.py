import os
import sys
import numpy as np
import cv2
from nptyping import NDArray, Shape, Float64
from PyQt6.QtWidgets import QApplication,QWidget
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))
from Exif import read_ome_metadata,dict_to_pretty_json,retrieve_image_info

from RoiMeasurements import RoiMeasurements
from TinyRoiFile import TinyRoiFile
from StopWatch import StopWatch
from TinyRoiManager import TinyRoiManager
from Roi import Roi

from HistogramFrame import HistogramFrame

def test_hist():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'


    base_name=test_path+"B_stitch"
    zip_path = base_name+"_rois.zip"
    zip_out_path = base_name+"_RoiSet.zip"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    rm = TinyRoiManager()
    rois = TinyRoiFile.read(zip_path, label_image)
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)
            roi.color: NDArray[Shape["1, 3"], Float64] = np.array([0.0, 0.0, 0.0])
    rm.force_feret()
    
    
    msmts = RoiMeasurements(rm)
    msmts.compute_stats_subset("ALL")

    subset_name="DELETED"
    deleted_filter = lambda roi: (roi.state==Roi.ROI_STATE_DELETED) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=deleted_filter)
    msmts.compute_stats_subset(subset_name)

    subset_name="ACTIVE"
    active_filter = lambda roi: (roi.state==Roi.ROI_STATE_ACTIVE) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=active_filter)
    msmts.compute_stats_subset(subset_name)
  
    demo = HistogramFrame()
    demo.populate(msmts.measurement_names, "Area", msmts)
    demo.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    test_hist()