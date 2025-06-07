import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QGraphicsTextItem
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.StopWatch import StopWatch
from RoiEditor.Lib.Context import key_to_label_map
from RoiEditor.Lib.Workbench import Workbench
from RoiEditor.Lib.StopWatch import StopWatch

from RoiEditor.Lib.RoiSelect import select_outer_rois_vdb5,select_outer_rois_vdb,select_outer_rois_vdb3,select_outer_rois_vdb4

def test_roiselect():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'

    app = QApplication(sys.argv)
    #rm = TinyRoiManager()


    gvars = {
        "show_names": True,
        "show_deleted": True,
    }

    # Padvariabelen
    # original_file = "A_stitch.tiff"
    # label_file = "A_stitch_label.png"
    # roi_file = None
    original_file = test_path+"A_stitch.tiff"
    label_file = test_path+"A_stitch_cp_masks.png"
    roi_file = None
  
    _ = QGraphicsTextItem("init")  

    bench = Workbench(original_file, label_file, roi_file, key_to_label_map)
    window=bench.build()
    select_outer_rois_vdb(bench.rm, step =1)
    window.draw_image()

    bench2 = Workbench(original_file, label_file, roi_file, key_to_label_map)
    window2=bench2.build()
    select_outer_rois_vdb3(bench2.rm, step = 1)
    window2.draw_image()

    bench3 = Workbench(original_file, label_file, roi_file, key_to_label_map)
    window3=bench3.build()
    select_outer_rois_vdb4(bench3.rm, step = 1)
    window3.draw_image()

    bench5 = Workbench(original_file, label_file, roi_file, key_to_label_map)
    window5=bench5.build()
    label_image = cv2.imread(label_file,cv2.IMREAD_UNCHANGED)
    StopWatch.start("detect edge")
    select_outer_rois_vdb5(bench5.rm,label_image)
    StopWatch.stop("detect edge")
    window5.draw_image()

    sys.exit(app.exec())


if __name__ == "__main__":
        test_roiselect()