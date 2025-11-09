import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsPixmapItem,
    QGraphicsEllipseItem,
    QWidget,
    QVBoxLayout,
)
from PyQt6.QtGui import QPixmap, QImage, QPolygonF, QPen, QBrush
from PyQt6.QtCore import QRectF, QPointF, Qt, pyqtSignal, QEventLoop

from Roi import Roi
from TinyLog import log


class TightFitGraphicsView(QGraphicsView):
    def __init__(self, scene, editor, parent):
        super().__init__(scene, parent)
        self.editor = editor

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene():
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class VertexHandle(QGraphicsEllipseItem):
    """A draggable vertex handle that stays the same size on screen."""

    def __init__(self, x, y, radius_px, editor, index):
        r = float(radius_px)
        super().__init__(-r, -r, 2 * r, 2 * r)  # center around (0,0) using the radius
        self.setPos(x, y)

        pen = QPen(Qt.GlobalColor.blue, 1.0)
        pen.setCosmetic(True)  # keep pen 1px on screen
        self.setPen(pen)
        self.setBrush(QBrush(Qt.GlobalColor.transparent))

        # Important: handle remains the same size in screen pixels regardless of zoom
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

        # Interaction
        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        # Performance/visuals
        self.setCacheMode(QGraphicsEllipseItem.CacheMode.DeviceCoordinateCache)

        self.editor = editor
        self.index = index

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        return super().hoverEnterEvent(event)

    def mousePressEvent(self, event):
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        return super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            # Update polygon shape whenever a handle is moved
            self.editor.update_polygon(self.index, value)
        return super().itemChange(change, value)


class PolygonEditor(QWidget):
    finished = pyqtSignal(Roi)

    def __init__(self, qimage, window_width, roi, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle("Polygon Editor")

        if qimage is None:
            raise ValueError("qimage must not be None")
        if roi is None:
            raise ValueError("roi must not be None")

        self.qimage = qimage
        self.window_width = int(window_width)
        self.processed_roi = roi
        self.cx, self.cy = roi.center
        self._close_requested_by_code = False

        self.app = QApplication.instance() or QApplication(sys.argv)

        # Scene + view
        self.scene = QGraphicsScene()
        self.view = TightFitGraphicsView(self.scene, editor=self, parent=self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Background image
        pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(self.qimage))
        pixmap_item.setZValue(10)  # Background
        self.scene.addItem(pixmap_item)

        # Initial frame around (cx, cy)
        half = self.window_width // 2
        initial_rect = QRectF(self.cx - half, self.cy - half, self.window_width, self.window_width)
        self.view.setSceneRect(initial_rect)

        # Polygon initialization
        if len(roi.xpoints) >= 3:
            points = [QPointF(x, y) for x, y in zip(roi.xpoints, roi.ypoints)]
        else:
            points = [QPointF(x, y) for x, y in self._regular_polygon(self.cx, self.cy, self.window_width / 4, 12)]

        self.qpolygon = QPolygonF(points)
        self.polygon_pen = QPen(Qt.GlobalColor.green, 1.0)
        self.polygon_pen.setCosmetic(True)
        self.polygon_item = self.scene.addPolygon(self.qpolygon, self.polygon_pen)
        self.polygon_item.setZValue(500)  # Above image

        # Add handles (fixed screen pixels)
        self.handles = []
        HANDLE_RADIUS_PX = 6  # easy to grab
        for i, pt in enumerate(points):
            h = VertexHandle(pt.x(), pt.y(), HANDLE_RADIUS_PX, self, i)
            h.setZValue(1000)
            self.scene.addItem(h)
            self.handles.append(h)

        # Key handling
        self.view.installEventFilter(self)
        self.show()

        # Zoom slightly wider around the polygon
        bbox = self.qpolygon.boundingRect()
        scale_factor = 1 / 0.8  # adds a ~1.25 safety margin
        expanded = QRectF(
            bbox.center().x() - bbox.width() * scale_factor / 2,
            bbox.center().y() - bbox.height() * scale_factor / 2,
            bbox.width() * scale_factor,
            bbox.height() * scale_factor,
        )
        if expanded.isValid() and expanded.width() > 0 and expanded.height() > 0:
            self.view.setSceneRect(expanded)

        # Force a 1px layout update so fitInView recalculates properly
        w, h = self.view.width(), self.view.height()
        self.view.resize(w + 1, h + 1)

    def update_polygon(self, idx, new_pos):
        """Update polygon when a handle is dragged."""
        self.qpolygon[idx] = new_pos
        self.polygon_item.setPolygon(self.qpolygon)

    def eventFilter(self, a0, a1):
        if a1.type() == a1.Type.KeyPress:
            # --- Zoom shortcuts ---
            if a1.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if a1.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                    self.view.scale(1.25, 1.25)
                    return True
                elif a1.key() == Qt.Key.Key_Minus:
                    self.view.scale(0.8, 0.8)
                    return True
                elif a1.key() == Qt.Key.Key_0:
                    self.view.resetTransform()
                    return True

            # --- ROI accept/cancel ---
            if a1.key() == Qt.Key.Key_Escape:
                log(f"Cancelled editing polygon-> ROI {self.processed_roi.name} unchanged")
                self._close_requested_by_code = True
                self.close()
                return True
            elif a1.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                log(f"Changes to polygon accepted -> ROI {self.processed_roi.name} updated", type="happy")
                xs = [p.x() for p in self.qpolygon]
                ys = [p.y() for p in self.qpolygon]
                self.processed_roi.xpoints, self.processed_roi.ypoints = None, None
                self.processed_roi.xpoints = xs
                self.processed_roi.ypoints = ys
                self._close_requested_by_code = True
                self.close()
                return True
        return super().eventFilter(a0, a1)

    def closeEvent(self, event):
        if not self._close_requested_by_code:
            log(f"Cancelled editing polygon -> ROI {self.processed_roi.name} unchanged", type="warning")
        self.cleanup()
        event.accept()
        super().closeEvent(event)

    def cleanup(self):
        if getattr(self, "_cleaning_up", False):
            return  # Prevent recursive cleanup calls
        self._cleaning_up = True
        self.finished.emit(self.processed_roi)

    def run(self):
        loop = QEventLoop()
        self.finished.connect(lambda _: loop.quit())

        if QApplication.instance():
            loop.exec()
        else:
            self.app.exec()

        return self.processed_roi

    @staticmethod
    def _regular_polygon(cx, cy, radius, n_sides):
        angles = np.linspace(0, 2 * np.pi, n_sides, endpoint=False)
        return [(cx + radius * np.cos(a), cy + radius * np.sin(a)) for a in angles]


# --- Demo usage ---
if __name__ == "__main__":
    # Dummy image
    app = QApplication.instance() or QApplication(sys.argv)
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    img[100:200, 100:200] = [255, 255, 255]
    h, w, ch = img.shape
    qimage = QImage(img.data, w, h, ch * w, QImage.Format.Format_RGB888)

    roi = Roi(xpoints=[150], ypoints=[150], center=(150, 150), bounds=(150, 150, 150, 150))

    demo_parent = QWidget()
    editor = PolygonEditor(qimage, window_width=150, roi=roi, parent=demo_parent)
    result = editor.run()
    print("Result ROI:", result.xpoints, result.ypoints)

    editor = PolygonEditor(qimage, window_width=150, roi=result, parent=demo_parent)
    result2 = editor.run()
    print("Result ROI 2:", result2.xpoints, result2.ypoints)
