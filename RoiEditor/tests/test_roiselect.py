import os
import sys
from PyQt6.QtCore import QTimer, QThreadPool
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtWidgets import QGraphicsTextItem
import cv2
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from StopWatch import StopWatch
from workbench import Workbench
import Context

from RoiSelect import select_outer_rois_vdb5,select_outer_rois_vdb,select_outer_rois_vdb3,select_outer_rois_vdb4

def test_roiselect():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")

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

    Context.gvars["selected_unit_and_scale"] = scalers[ID_PIXEL]    

    original_file = test_path+"6.tif"
    label_file = test_path+"6_cp_masks.png"
    roi_file = test_path+"6_rois.zip"
    nuke_roi_file= None
  
    _ = QGraphicsTextItem("init")  

    class DummyParent(QWidget):
        def eatAllEvents(self):
            pass
        def allowAllEvents(self):
            pass

    dummy_parent = DummyParent()

    files= {"org" : original_file,
            "cell_label" : label_file,
            "cell_zip" : roi_file,
            "nuke_label" : None,
            "nuke_zip" : nuke_roi_file
        }


    if auto_close_ms > 0:
        bench = Workbench(files, parent=dummy_parent)
        window = bench.build()
        label_image = cv2.imread(label_file, cv2.IMREAD_UNCHANGED)
        StopWatch.start("detect edge")
        select_outer_rois_vdb5(bench.rm["cell"], label_image)
        StopWatch.stop("detect edge")
        window.draw_image()

        def shutdown():
            bench.clean_up()
            QThreadPool.globalInstance().clear()
            QThreadPool.globalInstance().waitForDone(2000)
            app.quit()
        QTimer.singleShot(auto_close_ms, shutdown)
    else:
        bench = Workbench(files, parent=dummy_parent)
        window = bench.build()
        select_outer_rois_vdb(bench.rm["cell"], step=1)
        window.draw_image()

        bench2 = Workbench(files, parent=dummy_parent)
        window2 = bench2.build()
        select_outer_rois_vdb3(bench2.rm["cell"], step=1)
        window2.draw_image()

        bench3 = Workbench(files, parent=dummy_parent)
        window3 = bench3.build()
        select_outer_rois_vdb4(bench3.rm["cell"], step=1)
        window3.draw_image()

        bench5 = Workbench(files, parent=dummy_parent)
        window5 = bench5.build()
        label_image = cv2.imread(label_file, cv2.IMREAD_UNCHANGED)
        StopWatch.start("detect edge")
        select_outer_rois_vdb5(bench5.rm["cell"], label_image)
        StopWatch.stop("detect edge")
        window5.draw_image()

    sys.exit(app.exec())


if __name__ == "__main__":
        test_roiselect()
