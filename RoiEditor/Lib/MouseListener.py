"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtCore import Qt, QObject, QEvent
from typing import Callable

from .Roi import Roi
from .TinyLog import log

def dummy_callback(str) -> None:
    log("MouseListener: no callback connected")

class ROIClickListener(QObject):
    def __init__(self,  rm, roi_window, label_array,on_any_change: Callable[[str], None]=dummy_callback,parent=None):
        super().__init__(parent)
        self.label_array = label_array
        self.roi_window = roi_window
        self.rm = rm
        self.name_digits = len(str(self.rm.num_of_rois))
        self.height, self.width = label_array.shape
        self.on_any_change=on_any_change

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            log("Double Click: no action")
            return True

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.roi_window.view.mapToScene(event.pos())
            x = int(scene_pos.x())
            y = int(scene_pos.y())

            if not (0 <= x < self.width and 0 <= y < self.height):
                log("Click outside image bounds")
                return True

            label_val = int(self.label_array[y, x])
            if label_val <= 0:
                log("Background clicked")
                return True

            roi_name = "L" + str(label_val).zfill(self.name_digits)

            state = self.rm.get_state(roi_name)
            if state == Roi.ROI_STATE_DELETED:
                log(f"ROI {roi_name} already deleted")
                return True

            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.rm.delete(roi_name)
                self.on_any_change(f"Alt + Click → deleting {roi_name}")
                return True
            else:
                self.rm.toggle(roi_name)
                self.on_any_change(f"Click → toggling {roi_name}")
                return True

        return False


# class RoiManager:
#     ROI_STATE_DELETED = -1

#     def __init__(self):
#         self.rois = {"L1": "dummy1", "L2": "dummy2"}
#         self.states = {"L1": 1, "L2": 1}
#         self.num_of_rois = 2

#     def get_roi(self, name):
#         return self.rois.get(name)

#     def get_state(self, name):
#         return self.states.get(name, 0)

#     def toggle(self, name):
#         log(f"[RoiManager] Toggled {name}")

#     def delete(self, name):
#         log(f"[RoiManager] Deleted {name}")
#         self.states[name] = self.ROI_STATE_DELETED


# class DummyRoiImage:
#     def __init__(self, roi_manager, view=None):
#         self.view = view
#         self.roi_manager = roi_manager

#     def draw_image(self):
#         print(f"[RoiImage] draw_image")


# class DummyMeasurements:
#     def data_have_changed(self, reason):
#         print(f"[Measurements] Data changed: {reason}")


# def load_grayscale_image(path):
#     return np.array(Image.open(path).convert("L"))


# def np_to_qimage(np_img):
#     h, w = np_img.shape
#     img8 = np.clip(np_img, 0, 255).astype(np.uint8)
#     return QImage(img8.data, w, h, w, QImage.Format_Grayscale8)

# LABEL_IMAGE_PATH = "A_Stitch_1_cp_masks.png"
# REAL_IMAGE_PATH = "A_Stitch_1.png"

# def main():
#     app = QApplication(sys.argv)

#     # --- Laad labelbeeld (voor ROI lookup)
#     try:
#         label_array = load_grayscale_image(LABEL_IMAGE_PATH)
#     except Exception as e:
#         print(f"Fout bij laden labelbeeld: {e}")
#         sys.exit(1)

#     # --- Laad echt beeld (voor display)
#     try:
#         real_image = load_grayscale_image(REAL_IMAGE_PATH)
#     except Exception as e:
#         print(f"Fout bij laden echt beeld: {e}")
#         sys.exit(1)

#     qimage = np_to_qimage(real_image)
#     pixmap = QPixmap.fromImage(qimage)

#     def on_rect_drawn(rect):
#         print(f"callback triggered {str(rect)}")


#     # --- Setup gvars, roi_manager, roi_image
#     rm = RoiManager()

#     gvars = {
#         "show_names": True,
#         "show_deleted": False,
#     }

#     view = RectangleSelectorView(pixmap,on_rect_drawn)
#     view.setFixedSize(pixmap.size())
#     roi_image = DummyRoiImage(rm, view)

#     def callback(str):
#         log(str)
#         roi_image.draw_image()

#     # --- Installeer muisklik-vanger
#     mouse_listener = ROIClickListener(rm, roi_image, label_array)
#     view.viewport().installEventFilter(mouse_listener)

#     # --- Toon in hoofdvenster
#     window = QMainWindow()
#     window.setWindowTitle("Koninklijk ROI-selectievenster")
#     window.setCentralWidget(view)

#     window.show()

#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()
