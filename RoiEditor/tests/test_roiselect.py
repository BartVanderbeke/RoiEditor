import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QGraphicsTextItem
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from TinyRoiManager import TinyRoiManager
from StopWatch import StopWatch
from Context import key_to_label_map
from Workbench import Workbench
from StopWatch import StopWatch
import Context

from RoiSelect import select_outer_rois_vdb5,select_outer_rois_vdb,select_outer_rois_vdb3,select_outer_rois_vdb4

def test_roiselect():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    Context.gvars["show_names"] = True
    Context.gvars["show_deleted"] = True

    ID_PIXEL = 1
    ID_FROM_FILE = 2
    ID_SPECIFIED = 3
    scalers= {ID_PIXEL: {"length": {"scaler": 1.0, "unit": "px"},"area": {"scaler": 1.0*1.0, "unit": "px"}, "source": "no scaler/unit selected"},
                    ID_FROM_FILE: {"length": {"scaler": None, "unit": "µm"},"area": {"scaler": None, "unit": "µm²"}, "source": "read from image"},
                    ID_SPECIFIED: {"length": {"scaler": None, "unit": "µm"},"area": {"scaler": None, "unit": "µm²"}, "source": "set by user"},
    }

    key_to_label_map = Context.key_to_label_map

    Context.gvars["selected_unit_and_scale"] = scalers[ID_PIXEL]    

    original_file = test_path+"B_stitch.tiff"
    label_file = test_path+"B_stitch_cp_masks.png"
    roi_file = None
    nuke_roi_file= None
  
    _ = QGraphicsTextItem("init")  

        # def __init__(self, original_file: str,
        #          label_file: str,
        #          cell_roi_file: str,
        #          nuke_roi_file: str,
        #          key_to_label_map: dict[str,str],
        #          on_fail_to_write: Callable[[str],None]=dummy_callback_write,
        #          on_fail_to_build: Callable[[str],None]=dummy_callback_fail2build,
        #          parent:QWidget|None=None):

    files= {"org" : original_file,
            "cell_label" : label_file,
            "cell_zip" : roi_file,
            "nuke_label" : None,
            "nuke_zip" : nuke_roi_file
        }


    bench = Workbench(files,
                      key_to_label_map)
    window=bench.build()
    select_outer_rois_vdb(bench.rm["cell"], step =1)
    window.draw_image()

    bench2 = Workbench(files, key_to_label_map)
    window2=bench2.build()
    select_outer_rois_vdb3(bench2.rm["cell"], step = 1)
    window2.draw_image()

    bench3 = Workbench(files, key_to_label_map)
    window3=bench3.build()
    select_outer_rois_vdb4(bench3.rm["cell"], step = 1)
    window3.draw_image()

    bench5 = Workbench(files, key_to_label_map)
    window5=bench5.build()
    label_image = cv2.imread(label_file,cv2.IMREAD_UNCHANGED)
    StopWatch.start("detect edge")
    select_outer_rois_vdb5(bench5.rm["cell"], label_image)
    StopWatch.stop("detect edge")
    window5.draw_image()

    sys.exit(app.exec())


if __name__ == "__main__":
        test_roiselect()