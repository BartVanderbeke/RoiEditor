"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtWidgets import (
    QMainWindow, QSizePolicy,
    QGraphicsPolygonItem, QGraphicsTextItem
)
from PyQt6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PyQt6.QtGui import (
    QImage, QPixmap, QPolygonF, QPen,QBrush
)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QRect
from PyQt6.QtCore import Qt, QPointF, QTimer

from typing import Callable
from typing import Dict
import numpy as np

from .Roi import Roi
from .StopWatch import *
from .RectangleSelectorView import RectangleSelectorView
from .TinyLog import log

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")


def array2d_to_qpolygonf(_xdata, _ydata):
    # https://github.com/PlotPyStack/PythonQwt/blob/master/qwt/plot_curve.py#L63
    xdata=np.array(_xdata)
    ydata=np.array(_ydata)
    size = xdata.size
    polyline = QPolygonF([QPointF(0, 0)] * size)
    buffer = polyline.data()
    buffer.setsize(16 * size)  # 16 bytes per point: 8 bytes per X,Y value (float64)
    memory = np.frombuffer(buffer, np.float64)
    memory[: (size - 1) * 2 + 1 : 2] = np.asarray(xdata, dtype=np.float64)
    memory[1 : (size - 1) * 2 + 2 : 2] = np.asarray(ydata, dtype=np.float64)
    return polyline


from .Context import gvars
class RoiImageWindow(QMainWindow):
    """
        converts the xpoints and ypoints of the ROIs into polygons and shows them on the background image
        The polygons are cached for faster redrawing
    """
    @staticmethod
    def dummy_callback(self,str):
        log(f"RoiImageWindow: No callback connected: {str}")

    def zoom_to_str(self) -> str:
        return f"{int(self._zoom*100.0)}%"

    def __init__(self, image_array, rm, msmts, on_any_change: Callable[[str], None]=dummy_callback, parent=None):
        self.parent=parent
        self.initialized = False
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.Window)
        super().move(-5000,-5000)

        self.view=None

        black_bg = QWidget(parent=self)
        palette = black_bg.palette()
        palette.setColor(black_bg.backgroundRole(), Qt.GlobalColor.black)
        black_bg.setPalette(palette)
        black_bg.setAutoFillBackground(True)

        self.setCentralWidget(black_bg)

        self.base_title="ROI Editor - Image Window"
        self.setWindowTitle(self.base_title)

        self.image = image_array
        self.pixmap= QPixmap.fromImage(self.image)
        self.rm = rm
        self.msmts = msmts
        self.on_any_change=on_any_change
        self.transparent = QBrush(Qt.BrushStyle.NoBrush)

        # Statusbar and content
        status_bar = QStatusBar()
        status_container = QWidget()
        status_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._zoom=1.0
        self.lbl_zoom = QLabel(self.zoom_to_str())
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_zoom.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.lbl_info = QLabel("text")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout.addWidget(self.lbl_info)
        layout.addStretch(1)
        layout.addWidget(self.lbl_zoom)

        status_container.setLayout(layout)

        status_bar.addPermanentWidget(status_container, 1)
        self.setStatusBar(status_bar)

        self.view = RectangleSelectorView(pixmap=self.pixmap,on_rect_drawn=self._on_rect_drawn,on_change_zoom=self._on_change_zoom,parent=self)
        self.scene = self.view.scene
        self.view.setFrameStyle(0)

        self.state_style_map: Dict[int, Dict] = {
            Roi.ROI_STATE_ACTIVE:   {"pen": QPen(Qt.GlobalColor.yellow,0.5,Qt.PenStyle.SolidLine), "z": 2},
            Roi.ROI_STATE_DELETED:  {"pen": QPen(Qt.GlobalColor.red,0.2,Qt.PenStyle.SolidLine), "z": 1},
            Roi.ROI_STATE_SELECTED: {"pen": QPen(Qt.GlobalColor.blue,1.0,Qt.PenStyle.SolidLine), "z": 3}
        }

        self.z_on_top: int = 4 # on top of everything

        self._roi_polygon_cache: Dict[Roi, QGraphicsPolygonItem] = {}
        self._roi_text_cache: Dict[Roi,QGraphicsTextItem] = {}
        self.selected_measurement=None


    def show(self):
        super().show()

    def set_initial_pos_and_size(self):
        screen_geometry: QRect = QGuiApplication.primaryScreen().availableGeometry()

        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        target_size = int(screen_height * 0.75)
        target_width = min(target_size,screen_width)
        target_height = target_size

        x = screen_geometry.x() + (screen_width - target_width) // 2
        y = screen_geometry.y() + (screen_height - target_height) // 2

        self.setGeometry(x, y, target_width, target_height)


    def _on_change_zoom(self,zoom: float):
        self._zoom=zoom
        self.lbl_zoom.setText(f"{int(zoom*100.0)}%")



    def _on_rect_drawn(self,rect):
        self.rm.select_within(rect, additive=True)
        self.draw_image()
        self.on_any_change("Rectangle select")

    def on_select_measurement(self,msmt_name :str):
        if self.selected_measurement != msmt_name:
            self.selected_measurement = msmt_name
            if self.initialized:
                self.draw_image()


    def _build_and_add_items(self):

        self._roi_polygon_cache.clear()
        self._roi_text_cache.clear()

        #text = QGraphicsTextItem("L0001")
        roi_sample = self.rm.get_sample()
        name=roi_sample.name
        text = QGraphicsTextItem(name)

        bounding = text.boundingRect()

        bw2 = bounding.width() / 2
        bh2= bounding.height() / 2


        for roi_name,roi in self.rm.iter_all():
            qpoly=array2d_to_qpolygonf(roi.xpoints, roi.ypoints)
            item = QGraphicsPolygonItem(qpoly)
            self._roi_polygon_cache[roi] = item

            (cx,cy)=roi.center
            text = QGraphicsTextItem(roi_name)
            text.setDefaultTextColor(Qt.GlobalColor.white)
            text.setZValue(self.z_on_top)
            text.setPos(cx - bw2, cy - bh2)
            self._roi_text_cache[roi]=text


        for item in self._roi_polygon_cache.values():
            self.scene.addItem(item)
        for text in self._roi_text_cache.values():
            self.scene.addItem(text)



    def _update_scene(self):
        dict_roi_visibility_fn={True : (lambda roi: True),
                           False: (lambda roi: roi.state != Roi.ROI_STATE_DELETED)}
        deleted_visible = gvars.get("show_deleted", True)
        roi_visibility_fn=dict_roi_visibility_fn[deleted_visible]
        text_visible = gvars.get("show_names", True)
        show_overlay = self.selected_measurement and gvars.get("show_overlay", True)
        for roi, text in self._roi_text_cache.items():
             text.setVisible(text_visible and roi_visibility_fn(roi))
        if show_overlay:
            for roi, item  in self._roi_polygon_cache.items():
                style = self.state_style_map[roi.state]
                item.setPen(style["pen"])
                item.setZValue(style["z"])
                item.setVisible(roi_visibility_fn(roi))
                item.setBrush(self.msmts.qbrush["ALL"][self.selected_measurement][self.msmts.idx["ALL"][roi]])
        else:
            for roi, item  in self._roi_polygon_cache.items():
                style = self.state_style_map[roi.state]
                item.setPen(style["pen"])
                item.setZValue(style["z"])
                item.setVisible(roi_visibility_fn(roi))
                item.setBrush(self.transparent)


    def draw_image(self):

        if not self._roi_polygon_cache and self.rm:
            self._build_and_add_items()

        self._update_scene()

        from PyQt6.QtCore import QTimer
        if not self.initialized:
            QTimer.singleShot(0, lambda: self.wrap_up())


    def wrap_up(self):
        self.setCentralWidget(self.view)
        QTimer.singleShot(100, lambda: self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))
        QTimer.singleShot(200, lambda: self.set_initial_pos_and_size())
        self.initialized = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.view:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def closeEvent(self, event):
        # minimize iso closing
        event.ignore()
        self.showMinimized()

