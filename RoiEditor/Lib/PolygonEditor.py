import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsEllipseItem
)
from PyQt6.QtGui import QPixmap, QImage, QPolygonF, QPen, QBrush
from PyQt6.QtCore import QRectF, QPointF, Qt, QObject, pyqtSignal, QEventLoop

from Roi import Roi
from TinyLog import log


class TightFitGraphicsView(QGraphicsView):
    close_using_key = False

    def __init__(self, scene, editor=None):
        super().__init__(scene)
        self.editor = editor

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene():
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def closeEvent(self, event):
        # Treat window close (X button) the same as Escape key
        if not self.close_using_key:
            log("Cancelled editing polygon -> ROI unchanged", type="warning")
        if self.editor:
            self.editor.cleanup()
        event.accept()


class VertexHandle(QGraphicsEllipseItem):
    """A draggable vertex handle that stays the same size on screen."""

    def __init__(self, x, y, radius_px, editor, index):
        r = float(radius_px)
        super().__init__(-r, -r, 2 * r, 2 * r)  # centreer rond (0,0), gebruik radius
        self.setPos(x, y)

        pen = QPen(Qt.GlobalColor.blue, 1.0)
        pen.setCosmetic(True)  # 1px op scherm
        self.setPen(pen)
        self.setBrush(QBrush(Qt.GlobalColor.transparent))

        # Belangrijk: handle blijft even groot in schermpixels, onafhankelijk van zoom
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

        # Interactie
        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        # Performance/visueel
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


class PolygonEditor(QObject):
    finished = pyqtSignal(Roi)

    def __init__(self, qimage, window_width, roi):
        super().__init__()

        if qimage is None:
            raise ValueError("qimage must not be None")
        if roi is None:
            raise ValueError("roi must not be None")

        self.user_closes = False

        self.qimage = qimage
        self.window_width = int(window_width)
        self.processed_roi = roi
        self.cx, self.cy = roi.center

        self.app = QApplication.instance() or QApplication(sys.argv)

        # Scene + view
        self.scene = QGraphicsScene()
        self.view = TightFitGraphicsView(self.scene, editor=self)
        self.view.setWindowTitle("Polygon Editor")

        # Background image
        pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(self.qimage))
        pixmap_item.setZValue(10)  # Background
        self.scene.addItem(pixmap_item)

        # Startkader rond (cx, cy)
        half = self.window_width // 2
        initial_rect = QRectF(self.cx - half, self.cy - half, self.window_width, self.window_width)
        self.view.setSceneRect(initial_rect)

        # Polygon initialisatie
        if len(roi.xpoints) >= 3:
            points = [QPointF(x, y) for x, y in zip(roi.xpoints, roi.ypoints)]
        else:
            points = [QPointF(x, y) for x, y in self._regular_polygon(self.cx, self.cy, self.window_width / 4, 12)]

        self.qpolygon = QPolygonF(points)
        self.polygon_pen = QPen(Qt.GlobalColor.green, 1.0)
        self.polygon_pen.setCosmetic(True)
        self.polygon_item = self.scene.addPolygon(self.qpolygon, self.polygon_pen)
        self.polygon_item.setZValue(500)  # Above image

        # Handles toevoegen (vaste schermpixels)
        self.handles = []
        HANDLE_RADIUS_PX = 6  # prettig vast te pakken
        for i, pt in enumerate(points):
            h = VertexHandle(pt.x(), pt.y(), HANDLE_RADIUS_PX, self, i)
            h.setZValue(1000)
            self.scene.addItem(h)
            self.handles.append(h)

        # Key handling
        self.view.installEventFilter(self)
        self.view.show()

        # Zoom iets ruimer rond de polygon
        bbox = self.qpolygon.boundingRect()
        scale_factor = 1 / 0.8  # = 1.25 marges
        expanded = QRectF(
            bbox.center().x() - bbox.width() * scale_factor / 2,
            bbox.center().y() - bbox.height() * scale_factor / 2,
            bbox.width() * scale_factor,
            bbox.height() * scale_factor,
        )
        if expanded.isValid() and expanded.width() > 0 and expanded.height() > 0:
            self.view.setSceneRect(expanded)

        # Forceer 1px layout update zodat fitInView correct werkt
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
                self.view.close_using_key = True
                self.cleanup()
                return True
            elif a1.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                log(f"Changes to polygon accepted -> ROI {self.processed_roi.name} updated", type="happy")
                xs = [p.x() for p in self.qpolygon]
                ys = [p.y() for p in self.qpolygon]
                self.processed_roi.xpoints, self.processed_roi.ypoints = None, None
                self.processed_roi.xpoints = xs
                self.processed_roi.ypoints = ys
                self.view.close_using_key = True
                self.cleanup()
                return True
        return super().eventFilter(a0, a1)

    def cleanup(self):
        if hasattr(self, "_cleaning_up") and self._cleaning_up:
            return  # Prevent recursive cleanup calls
        self._cleaning_up = True
        self.view.close()
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
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    img[100:200, 100:200] = [255, 255, 255]
    h, w, ch = img.shape
    qimage = QImage(img.data, w, h, ch * w, QImage.Format.Format_RGB888)

    roi = Roi(xpoints=[150], ypoints=[150], center=(150, 150), bounds=(150, 150, 150, 150))

    editor = PolygonEditor(qimage, window_width=150, roi=roi)
    result = editor.run()
    print("Result ROI:", result.xpoints, result.ypoints)

    editor = PolygonEditor(qimage, window_width=150, roi=result)
    result2 = editor.run()
    print("Result ROI 2:", result2.xpoints, result2.ypoints)
