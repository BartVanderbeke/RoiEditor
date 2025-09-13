from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPolygonF
from PyQt6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsPolygonItem

from typing import Callable, Any

from TinyLog import log
from TinyRoiManager import TinyRoiManager
from Roi import Roi

def dummy_callback(str) -> None:
    log("ClickableItems: no on_change callback connected",type="error")
def dummy_hover_callback(roi: Roi | None) -> None:
    log("ClickableItems: no hover callback connected",type="error")

class RoiClickablePolygonItem(QGraphicsPolygonItem):
    def __init__(self, polygon: QPolygonF, *,
                 roi: Roi,
                 rm: TinyRoiManager,
                 on_any_change: Callable[[str,bool], None]=dummy_callback,
                 on_hover: Callable[[Roi | None], None]=dummy_hover_callback,
                 on_alt_ctrl_click: Callable[[Roi, tuple[int,int]], None]=None,
                 parent=None):
        super().__init__(polygon, parent)
        self.on_any_change = on_any_change
        self.roi: Roi = roi
        self.rm: TinyRoiManager = rm
        self.on_hover: Callable[[Roi | None], None] = on_hover
        self.setAcceptHoverEvents(True)
        self.on_alt_ctrl_click = on_alt_ctrl_click


    def mouseDoubleClickEvent(self, event):
        # Double Click: no action
        log("Double Click: no action",type="info")
        event.accept()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            log(f"ROI Actions only connected to Left Click",type="info")
            event.accept()
            return

        roi_name = self.roi.name
        roi_state = self.rm.get_state(roi_name)

        mods = event.modifiers()
        if mods == Qt.KeyboardModifier.NoModifier:
            self.rm.toggle_selection(roi_name)
            self.on_any_change(f"ROI Left Click → toggling {roi_name}")
            event.accept()
            return
        
        if mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
            # Get position in scene coordinates for adding a nucleus
            scene_pos = event.scenePos()  # Position in scene coordinates
            image_x = int(scene_pos.x())  # Convert to image coordinates
            image_y = int(scene_pos.y())
            position = (image_x, image_y)

            self.on_alt_ctrl_click(self.roi, position)  
            log(f"ROI Ctrl & Alt Click on {roi_name}",type="info",log_level=1000)
            event.accept()
            return

        if mods & Qt.KeyboardModifier.AltModifier:
            if roi_state == self.roi.ROI_STATE_DELETED:
                log(f"ROI {roi_name} already deleted",type="info")
                event.accept()
                return
            self.rm.delete(roi_name)
            self.on_any_change(f"ROI Alt + Left Click → deleting {roi_name}")
            event.accept()
            return

        if mods & Qt.KeyboardModifier.ControlModifier:
            log("ROI Ctrl+Click: no action",type="info")
            event.accept()
            return

        event.accept()

    def hoverEnterEvent(self, event):
        self.on_hover(self.roi)
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.on_hover(None)
        super().hoverLeaveEvent(event)



