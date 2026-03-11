import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QPixmap,QImage
from PyQt6.QtCore import QTimer
import cv2

import numpy as np
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from tiny_log import log
from rectangle_selector_view import RectangleSelectorView
from mouse_listener import ROIClickListener

class RoiManager:
    ROI_STATE_DELETED = -1

    def __init__(self):
        self.rois = {"L1": "dummy1", "L2": "dummy2"}
        self.states = {"L1": 1, "L2": 1}
        self.num_of_rois = 2

    def get_roi(self, name):
        return self.rois.get(name)

    def get_state(self, name):
        return self.states.get(name, 0)

    def toggle_selection(self, name):
        log(f"[RoiManager] Toggled {name}")

    def delete(self, name):
        log(f"[RoiManager] Deleted {name}")
        self.states[name] = self.ROI_STATE_DELETED


class DummyRoiImage:
    def __init__(self, roi_manager, view=None):
        self.view = view
        self.roi_manager = roi_manager

    def draw_image(self):
        print(f"[RoiImage] draw_image")


class DummyMeasurements:
    def data_have_changed(self, reason):
        print(f"[Measurements] Data changed: {reason}")


def load_grayscale_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    return np.array(img)


def np_to_qimage(np_img):
    h, w = np_img.shape
    img8 = np.clip(np_img, 0, 255).astype(np.uint8)
    return QImage(img8.data, w, h, w, QImage.Format.Format_Grayscale8)



def test_mouselistener():
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)


    try:
        label_array = load_grayscale_image(LABEL_IMAGE_PATH)
    except Exception as e:
        print(f"Fout bij laden labelbeeld: {e}")
        sys.exit(1)


    try:
        real_image = load_grayscale_image(REAL_IMAGE_PATH)
    except Exception as e:
        print(f"Fout bij laden echt beeld: {e}")
        sys.exit(1)

    qimage = np_to_qimage(real_image)
    pixmap = QPixmap.fromImage(qimage)

    def on_rect_drawn(rect):
        print(f"callback triggered {str(rect)}")



    rm = RoiManager()

    gvars = {
        "show_names": True,
        "show_deleted": False,
    }

    view = RectangleSelectorView(pixmap,on_rect_drawn)
    view.setFixedSize(pixmap.size())
    roi_image = DummyRoiImage(rm, view)

    def callback(str):
        log(str)
        roi_image.draw_image()


    mouse_listener = ROIClickListener(rm, roi_image, label_array)
    view.viewport().installEventFilter(mouse_listener)


    window = QMainWindow()
    window.setWindowTitle("Koninklijk ROI-selectievenster")
    window.setCentralWidget(view)

    window.show()
    if auto_close_ms > 0:
        QTimer.singleShot(auto_close_ms, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")
    LABEL_IMAGE_PATH = os.path.join(test_path,"6_cp_masks.png")
    REAL_IMAGE_PATH = os.path.join(test_path,"6.tif")

    test_mouselistener()
