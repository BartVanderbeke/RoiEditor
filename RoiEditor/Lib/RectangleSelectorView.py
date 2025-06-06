"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtGui import QPixmap, QPen
from PyQt6.QtCore import Qt,QRectF, QPointF
from typing import Optional, Callable
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem,QWidget

class RectangleSelectorView(QGraphicsView):
    def dummy_callback_zoom(self, f : float) -> None:
        print(f"RectangleSelectorView: no callback assigned {f}")
    def dummy_callback_rect(self, r : QRectF) -> None:
        print(f"RectangleSelectorView: no callback assigned")


    def __init__(self,
                 pixmap: QPixmap,
                 on_rect_drawn: Optional[Callable[[QRectF], None]] = None,
                 on_change_zoom: Optional[Callable[[float], None]] = None,
                 parent: Optional[QWidget] = None
                 ) -> None:
        super().__init__(parent)
        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.viewport().setStyleSheet("background-color: black;")
        self._zoom=1.0
        self.setFrameStyle(0)
        self.setMouseTracking(True)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))

        self.origin = QPointF()
        self.rubber_band = QGraphicsRectItem()
        self.rubber_band.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
        self.rubber_band.setZValue(10)
        self.rubber_band.setVisible(False)
        self.scene.addItem(self.rubber_band)
        self.on_rect_drawn=on_rect_drawn if on_rect_drawn else self.dummy_callback_rect
        self.on_change_zoom=on_change_zoom if on_change_zoom else self.dummy_callback_zoom
        self.on_change_zoom(self._zoom)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.origin = self.mapToScene(event.pos())
            self.rubber_band.setRect(QRectF(self.origin, self.origin))
            self.rubber_band.setVisible(True)

    def mouseMoveEvent(self, event):
        if self.rubber_band.isVisible():
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self.origin, current_pos).normalized()
            self.rubber_band.setRect(rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self.rubber_band.isVisible():
            rect = self.rubber_band.rect()
            self.rubber_band.setVisible(False)
            self.on_rect_drawn(rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)


    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus:
                self.zoom(1.25)
            elif event.key() == Qt.Key.Key_Minus:
                self.zoom(0.8)
            elif event.key() == Qt.Key.Key_0:
                self.reset_zoom()
        else:
            super().keyPressEvent(event)

    def reset_zoom(self):
        self.resetTransform()
        self._zoom=1.0
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.on_change_zoom(self._zoom)

    def zoom(self, factor):
        self._zoom *= factor
        self.scale(factor, factor)
        self.on_change_zoom(self._zoom)


