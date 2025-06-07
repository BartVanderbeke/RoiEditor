import os
import sys
import random
from PyQt6.QtWidgets import QApplication,QWidget
from PyQt6.QtCore import QTimer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from RoiEditor.Lib.Roi import Roi
from RoiEditor.Lib.Context import key_to_label_map
from RoiEditor.Lib.Stylesheet import overall
from RoiEditor.Lib.Workbench import Workbench

def test_workbench():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'
    original_file = test_path+"A_Stitch.tiff"
    label_file = test_path+"A_Stitch_cp_masks.png"
    roi_file = None
    title = "set the scene"
    
    from PyQt6.QtWidgets import QGraphicsTextItem

    _ = QGraphicsTextItem("init")  

    
    dummy = QWidget()
    dummy.setStyleSheet(overall)


    bench = Workbench(original_file, label_file, roi_file, key_to_label_map,parent = dummy)
    window=bench.build()
    rm = bench.rm


    l= [Roi.ROI_STATE_DELETED, Roi.ROI_STATE_SELECTED, Roi.ROI_STATE_DELETED,Roi.ROI_STATE_ACTIVE, Roi.ROI_STATE_SELECTED,Roi.ROI_STATE_DELETED,Roi.ROI_STATE_ACTIVE]

    def toggle_image():
        for _,roi in rm.iter_all():
            roi.state= random.choice(l)
        bench.on_any_change()

    timer = QTimer()
    timer.timeout.connect(toggle_image)
    timer.start(1000)  
    sys.exit(app.exec())


if __name__ == "__main__":
    test_workbench()