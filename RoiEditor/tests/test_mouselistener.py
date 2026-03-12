from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QImage, QPixmap
import cv2

import numpy as np
from mouse_listener import ROIClickListener
from rectangle_selector_view import RectangleSelectorView

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
        self.states[name] = self.ROI_STATE_DELETED


class DummyRoiImage:
    def __init__(self, roi_manager, view=None):
        self.view = view
        self.roi_manager = roi_manager

    def draw_image(self):
        print(f"[RoiImage] draw_image")


class DummyMeasurements:
    def data_have_changed(self, reason):
        pass


def load_grayscale_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    return np.array(img)


def np_to_qimage(np_img):
    h, w = np_img.shape
    img8 = np.clip(np_img, 0, 255).astype(np.uint8)
    return QImage(img8.data, w, h, w, QImage.Format.Format_Grayscale8)

from RoiEditor.tests._helpers import data_path, fail, run_qt_loop


def test_mouselistener(qapp):
    try:
        label_array = load_grayscale_image(str(data_path("A_stitch_cp_masks.png")))
        real_image = load_grayscale_image(str(data_path("A_stitch.tiff")))
        pixmap = QPixmap.fromImage(np_to_qimage(real_image))
        view = RectangleSelectorView(pixmap, lambda rect: None)
        view.setFixedSize(pixmap.size())
        roi_image = DummyRoiImage(RoiManager(), view)
        mouse_listener = ROIClickListener(roi_image.roi_manager, roi_image, label_array)
        view.viewport().installEventFilter(mouse_listener)
        window = QMainWindow()
        window.setCentralWidget(view)
        window.show()
        run_qt_loop(qapp, cleanup=window.close)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
