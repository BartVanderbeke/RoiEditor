"""RoiEditor

Author: Bart Vanderbeke & Elisa
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

    def eventFilter(self, a0: QObject, a1: QEvent):
        if a1.type() == QEvent.Type.MouseButtonDblClick:
            log("Double Click: no action")
            return True

        if a1.type() == QEvent.Type.MouseButtonPress and a1.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.roi_window.view.mapToScene(a1.pos())
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

            if a1.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.rm.delete(roi_name)
                self.on_any_change(f"Alt + Click → deleting {roi_name}")
                return True
            else:
                self.rm.toggle(roi_name)
                self.on_any_change(f"Click → toggling {roi_name}")
                return True

        return False
