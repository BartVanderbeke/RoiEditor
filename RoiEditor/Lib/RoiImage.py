"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtWidgets import (
    QMainWindow, QSizePolicy,
    QGraphicsPolygonItem, QGraphicsTextItem, QGraphicsSimpleTextItem
)
from PyQt6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PyQt6.QtGui import (
    QImage, QPixmap, QPolygonF, QPen,QBrush,QPolygon
)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QRect
from PyQt6.QtCore import Qt, QPointF, QTimer,QPoint
from PyQt6.QtGui import QColor

from typing import Callable
from typing import Dict
import numpy as np

from Roi import Roi
from StopWatch import *
from RectangleSelectorView import RectangleSelectorView
from TinyLog import log
from ClickableItems import RoiClickablePolygonItem
from RoiMeasurements import RoiMeasurements
from TinyRoiManager import TinyRoiManager


import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")


def array2d_to_qpolygonf(_xdata, _ydata):
    # trimmed down version of Pierre Raybaut's array2d_to_qpolygonf
    # https://github.com/PlotPyStack/PythonQwt/blob/master/qwt/plot_curve.py#L63
    xdata=np.array(_xdata)
    ydata=np.array(_ydata)
    size = xdata.size
    polyline = QPolygonF([QPointF(0, 0)] * size)
    buffer = polyline.data()
    buffer.setsize(16 * size)  # 16 bytes per point: 8 bytes per X,Y value (float64)
    memory = np.frombuffer(buffer, dtype=np.float64)
    memory[: (size - 1) * 2 + 1 : 2] = np.asarray(xdata, dtype=np.float64)
    memory[1 : (size - 1) * 2 + 2 : 2] = np.asarray(ydata, dtype=np.float64)
    return polyline


from Context import gvars
class RoiImageWindow(QMainWindow):
    """
        converts the xpoints and ypoints of the ROIs into polygons and shows them on the background image
        The polygons are cached for faster redrawing
    """
    WIDGET_SIZE = 3
    @staticmethod
    def __x_polygon() -> QPolygonF:
        return QPolygonF([QPointF(-RoiImageWindow.WIDGET_SIZE, RoiImageWindow.WIDGET_SIZE),
                          QPointF(RoiImageWindow.WIDGET_SIZE, -RoiImageWindow.WIDGET_SIZE),
                          QPointF(0.0, 0.0),
                          QPointF(RoiImageWindow.WIDGET_SIZE, RoiImageWindow.WIDGET_SIZE),
                          QPointF(-RoiImageWindow.WIDGET_SIZE, -RoiImageWindow.WIDGET_SIZE),
                          QPointF(0.0, 0.0)])
    
    @staticmethod
    def __x_polygon_at(cx:int,cy:int) -> QPolygon:
        poly = QPolygonF(RoiImageWindow.__x_polygon())
        poly.translate(cx,cy)
        return QPolygonF(poly)  

    @staticmethod
    def dummy_callback(str):
        log(f"RoiImageWindow: No callback connected: {str}")

    def zoom_to_str(self) -> str:
        return f"{int(self._zoom*100.0)}%"

    def __init__(self,
                 qimage: QImage,
                 rm: TinyRoiManager,nd: TinyRoiManager,
                 msmts: RoiMeasurements,
                 on_any_change: Callable[[str], None]=dummy_callback,
                 parent: QWidget | None = None):
        self.parent =parent
        self.nuke_rm = nd
        self.initialized = False
        self.root_item = None
        self.dummy_polygon = None
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

        self.qimage = qimage
        self.pixmap= QPixmap.fromImage(self.qimage)
        self.cell_rm = rm
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
        self.view.setMouseTracking(True)
        self.scene = self.view.scene
        self.view.setFrameStyle(0)

        dummy_item = QGraphicsTextItem("Hello")
        self.font_family = dummy_item.font().family()
        self.font_size = int(dummy_item.font().pointSizeF())
        self.font_string = dummy_item.font().toString

        selected_color = QColor("#00F0FF")
        base_color = QColor("#CFFF04")
        deleted_color  = QColor("#C88D94")

        self.cell_state_style_map: Dict[int, Dict] = {
            Roi.ROI_STATE_ACTIVE:   {"pen": QPen(base_color,0.75,Qt.PenStyle.SolidLine), "z": 2},
            Roi.ROI_STATE_DELETED:  {"pen": QPen(deleted_color,0.5,Qt.PenStyle.SolidLine), "z": 1},
            Roi.ROI_STATE_SELECTED: {"pen": QPen(selected_color,1.5,Qt.PenStyle.SolidLine), "z": 3}
        }
        #self.roi_hover_style = {"pen": QPen(QColor("#FF10F0"),2,Qt.PenStyle.SolidLine), "z": 3}


        self.roi_hover_state_style_map: Dict[int, Dict] = {
            Roi.ROI_STATE_ACTIVE:   {"pen": QPen(base_color,2.0,Qt.PenStyle.SolidLine), "z": 2},
            Roi.ROI_STATE_DELETED:  {"pen": QPen(deleted_color,1.0,Qt.PenStyle.SolidLine), "z": 1},
            Roi.ROI_STATE_SELECTED: {"pen": QPen(selected_color,2.0,Qt.PenStyle.SolidLine), "z": 3}
        }


        self.z_on_top: int = 10 # on top of everything

        self._roi_polygon_cache: Dict[Roi, RoiClickablePolygonItem] = {}
        self._roi_text_cache: Dict[Roi,QGraphicsSimpleTextItem] = {}
        self._nukes_polygon_cache: Dict[Roi,RoiClickablePolygonItem] = {}
        self.selected_measurement=None
        self.hover_nuke=None
        self.hover_roi=None

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
        self.cell_rm.select_within(rect, additive=True)
        self.draw_image()
        self.on_any_change("Rectangle select")

    def on_select_measurement(self,msmt_name :str):
        if self.selected_measurement != msmt_name:
            self.selected_measurement = msmt_name
            if self.initialized:
                self.draw_image()

    def on_hover_nucleus(self,nk: Roi):
        self.hover_nuke=nk
        self._update_scene()
    
    def on_hover_roi(self,roi : Roi):
        self.hover_roi=roi
        self._update_scene()

    def _build_and_add_items(self):
        #self.scene.clear()
        if self.root_item:
            self.scene.removeItem(self.root_item)

        self._roi_polygon_cache.clear()
        self._roi_text_cache.clear()
        self._nukes_polygon_cache.clear()

        self.root_item = QGraphicsTextItem("")
        self.root_item.setVisible(True)


        self.dummy_polygon = QGraphicsPolygonItem(QPolygonF(),parent=self.root_item,)
        dummy_roi = Roi(name="dummy",xpoints=np.empty((0,)).astype(int),ypoints=np.empty((0,)).astype(int))
        self.dummy_polygon  = RoiClickablePolygonItem(QPolygonF(),roi=dummy_roi,
                                                      rm=self.cell_rm,
                                                      on_any_change=self.on_any_change,
                                                      on_hover=self.on_hover_roi,
                                                      on_alt_ctrl_click=self.parent.on_add_nucleus_here,
                                                      parent=self.dummy_polygon)

        # get a dummy to determine the size of the text bounding box
        roi_sample = self.cell_rm.get_sample()
        name=roi_sample.name
        dummy_text = QGraphicsSimpleTextItem(name)
        dummy_text.setPen(QPen(Qt.PenStyle.NoPen))
        bounding = dummy_text.boundingRect()
        bw2 = bounding.width() / 2
        bh2= bounding.height() / 2


        for roi_name,roi in self.cell_rm.iter_all():
            (cx,cy)=roi.center
            x,y =cx - bw2, cy - bh2
            z = self.z_on_top-1
            qpoly=array2d_to_qpolygonf(roi.xpoints, roi.ypoints)
            item  = RoiClickablePolygonItem(qpoly,roi=roi,rm=self.cell_rm,
                                            on_any_change=self.on_any_change,
                                            on_hover=self.on_hover_roi,
                                            on_alt_ctrl_click=self.parent.on_add_nucleus_here,
                                            parent=self.root_item)
            self._roi_polygon_cache[roi] = item


            text = QGraphicsSimpleTextItem(roi_name)
            text.setBrush(QColor("white"))   
            text.setPen(QPen(QColor("white"))) # QPen(Qt.PenStyle.NoPen)
            text.setZValue(z)
            text.setPos(x, y)
            text.setParentItem(item)
            self._roi_text_cache[roi]=text



        for nuke_name,nk in self.nuke_rm.iter_all():

            (cx,cy)=nk.center
            qpoly =RoiImageWindow.__x_polygon_at(cx,cy)
            # parent (item) must be root (item) otherwise the nuclei (items) inside cells cannot be selected 
            item  = RoiClickablePolygonItem(qpoly,roi=nk,rm=self.nuke_rm,
                                            on_any_change=self.on_any_change,
                                            on_hover=self.on_hover_nucleus,
                                            on_alt_ctrl_click=self.parent.on_add_nucleus_here,
                                            parent= self.root_item)
            item.setZValue(self.z_on_top)
            self._nukes_polygon_cache[nk] = item


        self.scene.addItem(self.root_item)


    def _update_scene(self):
        dict_brush_overlay = {
            # self.msmts.qbrush contains the coloring based on the 'distance' to the median
            True: {self.cell_rm: lambda roi: self.msmts.qbrush["ALL"][self.selected_measurement][self.msmts.idx["ALL"][roi]],
                   self.nuke_rm: lambda roi: self.transparent
                   },
            False: {
                self.cell_rm: lambda roi: self.transparent,
                self.nuke_rm: lambda roi: self.transparent
            }
        }
        dict_roi_visibility_fn={True : (lambda roi: True),
                           False: (lambda roi: roi.state != Roi.ROI_STATE_DELETED)}
        deleted_visible = gvars.get("show_deleted", True)
        roi_visibility_fn=dict_roi_visibility_fn[deleted_visible]
        text_visible = gvars.get("show_names", True)
        show_overlay = gvars.get("show_overlay", True)
        show_overlay &= self.selected_measurement is not None

        for roi, text in self._roi_text_cache.items():
             text.setVisible(text_visible and roi_visibility_fn(roi))

        for rm, item_cache, hovered_obj in [(self.cell_rm,self._roi_polygon_cache,self.hover_roi),
                                            (self.nuke_rm,self._nukes_polygon_cache,self.hover_nuke)]:
            dict_brush = dict_brush_overlay[show_overlay]
            for roi, item  in item_cache.items():
                style = self.cell_state_style_map[roi.state]
                item.setPen(style["pen"])
                item.setVisible(roi_visibility_fn(roi))
                brush = dict_brush[rm](roi)
                item.setBrush(brush)
            if hovered_obj:
                hover_item = item_cache.get(hovered_obj,None)
                if hover_item: 
                    style = self.roi_hover_state_style_map[hovered_obj.state]
                    hover_item.setPen(style["pen"])



    def draw_image(self,rebuild: bool = False):
        if rebuild or (not self._roi_polygon_cache and self.cell_rm):
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
        self.showMinimized()
        event.accept()

