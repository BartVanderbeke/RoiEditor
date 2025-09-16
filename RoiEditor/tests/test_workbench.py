import os
import sys
import random
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtWidgets import QApplication,QWidget
from PyQt6.QtCore import QTimer


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))


from Roi import Roi
from Stylesheet import overall
from Workbench import Workbench
import Context as Context #import key_to_label_map,gvars

def test_workbench():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'
    original_file = test_path+"B_Stitch.tiff"
    label_file = test_path+"B_Stitch_cp_masks.png"
    roi_file = None
    nuke_roi_file= None
    title = "set the scene"
    

    ID_PIXEL = 1
    ID_FROM_FILE = 2
    ID_SPECIFIED = 3
    scalers= {ID_PIXEL: {"length": {"scaler": 1.0, "unit": "px"},"area": {"scaler": 1.0*1.0, "unit": "px"}, "source": "no scaler/unit selected"},
                    ID_FROM_FILE: {"length": {"scaler": None, "unit": "µm"},"area": {"scaler": None, "unit": "µm²"}, "source": "read from image"},
                    ID_SPECIFIED: {"length": {"scaler": None, "unit": "µm"},"area": {"scaler": None, "unit": "µm²"}, "source": "set by user"},
    }


    Context.gvars["selected_unit_and_scale"] = scalers[ID_PIXEL]




    _ = QGraphicsTextItem("init")  

    
    dummy = QWidget()
    dummy.setStyleSheet(overall)

    bench = Workbench(original_file = original_file,
                 label_file= label_file,
                 cell_roi_file= roi_file,
                 nuke_roi_file = nuke_roi_file,
                 key_to_label_map = Context.key_to_label_map,
                 parent = dummy)

    window=bench.build()
    rm = bench.cell_rm


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