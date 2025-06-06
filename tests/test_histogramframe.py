import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from RoiEditor.Lib.Exif import read_ome_metadata,dict_to_pretty_json,retrieve_image_info

from RoiEditor.Lib.RoiMeasurements import RoiMeasurements
from RoiEditor.Lib.TinyRoiFile import TinyRoiFile
from RoiEditor.Lib.StopWatch import StopWatch
from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.Roi import Roi

from RoiEditor.Lib.HistogramFrame import HistogramFrame

def test_hist():
    app = QApplication(sys.argv)

    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'


    base_name=test_path+"A_stitch_RoiSet"
    zip_path = base_name+".zip"
    zip_out_path = base_name+"_OUT.zip"
    num_threads = 12

    rm = TinyRoiManager()
    rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)
    rm.force_feret()
    
    # fills the subset 'ALL'
    msmts = RoiMeasurements(rm)

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