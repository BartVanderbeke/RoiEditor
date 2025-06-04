"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QSplitter, QApplication, QHeaderView
)
from pyqtgraph import PlotWidget
import pyqtgraph as pg
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

from .Crumbs import format_float

class ColorCycler(object):
    def __init__(self):
        self.colors = [
            QColor(Qt.GlobalColor.blue),
            QColor(Qt.GlobalColor.green),
            QColor(Qt.GlobalColor.red),
            QColor(255, 255, 0),        # yellow
            QColor(Qt.GlobalColor.magenta),
            QColor(255, 165, 0),        # orange
            QColor(255, 192, 203)       # pink
        ]
        self.index = 0

    def next(self):
        color = self.colors[self.index]
        self.index = (self.index + 1) % len(self.colors)
        return color

from typing import Callable
class HistogramFrame(QWidget):
    @classmethod
    def is_histogram_populated(cls,histogram: "HistogramFrame"):
        return histogram is not None and histogram.is_populated

    @property
    def is_populated(self):
        return self._is_populated

    @staticmethod
    def dummy_callback(msmt_name:str):
        print(f"Histogram dummy callback: {msmt_name} selected")


    def __init__(self,on_measurement_selected: Callable[[str], None]=dummy_callback, parent=None):
        self._is_populated=False
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setFixedSize(600, 600)
        self.on_measurement_selected: Callable[[str], None]=on_measurement_selected

    def _on_destroyed(self, obj):
        print("HistogramFrame is being deleted")

    def closeEvent(self, event):
        print("HistogramFrame is being closed")
        event.accept()

    def populate(self, measurement_names, selected_measurement, msmts,parent=None):
        from .Stylesheet import overall
        self.setStyleSheet(overall)

        self.measurement_names = measurement_names
        self.selected_measurement = selected_measurement
        self.msmts = msmts

        self.setWindowTitle(f"Histogram: {self.selected_measurement}")


        pg.setConfigOption('background', '#2b2b2b')
        pg.setConfigOption('foreground', 'w')

        layout = QVBoxLayout() # parent=self
        top_panel = QHBoxLayout() # parent=layout

        self.dropdown = QComboBox() # parent=top_panel
        self.dropdown.addItems(self.measurement_names)
        self.dropdown.setCurrentText(self.selected_measurement)
        self.dropdown.currentIndexChanged.connect(self.on_select_measurement)
        lbl = QLabel(text="Measurement:",parent=self)
        top_panel.addWidget(lbl)
        top_panel.addWidget(self.dropdown)

        layout.addLayout(top_panel)

        self.plot_widget = PlotWidget()
        self.plot_widget.addLegend(offset=(-10, 10), anchor=(1, 0))
        self.plot_widget.setLabel('left', 'Frequency')
        unit = self.msmts.stats["ALL"][self.selected_measurement]["unit"]
        x_axis_label= f"{self.selected_measurement} ({unit})" if unit else f"{self.selected_measurement}"
        self.plot_widget.setLabel('bottom', x_axis_label)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        view_box = self.plot_widget.getViewBox()
        view_box.setMouseEnabled(x=False, y=False)
        view_box.setMenuEnabled(False)
        self.plot_widget.setInteractive(False)


        self.table_widget = QTableWidget(0, 8)
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        from PyQt6.QtWidgets import QAbstractScrollArea
        self.table_widget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table_widget.setHorizontalHeaderLabels([
            "roi set", "N", "average", "stdev", "median", "MAD", "IQR", "Outliers"
        ])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        splitter = QSplitter(parent=self)
        splitter.setChildrenCollapsible(False)
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.addWidget(self.plot_widget)
        splitter.addWidget(self.table_widget)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)
        self.setLayout(layout)

        self.update_plot()
        self._is_populated=True
        self.on_measurement_selected(self.selected_measurement)

    def closeEvent(self, event):
        # minimize iso closing
        event.ignore()
        self.showMinimized()


    def showEvent(self, event):
        self.raise_()
        self.activateWindow()
        super().showEvent(event)

    def on_select_measurement(self, index):
        new_measurement = self.dropdown.currentText()
        if new_measurement != self.selected_measurement:
            self.selected_measurement = new_measurement
            self.setWindowTitle(f"Histogram: {self.selected_measurement}")
            self.update_plot()
            self.on_measurement_selected(new_measurement)

    def update_plot(self):
        self.plot_widget.clear()
        self.table_widget.setRowCount(0)
        colors = ColorCycler()
        for subset_name, _stats in self.msmts.stats.items():
            stats = _stats[self.selected_measurement]
            hist = stats["hist"]
            bin_edges = stats["bin_edges"]
            N = stats["N"]
            unit = stats["unit"]

            x_axis_label= f"{self.selected_measurement} ({unit})" if unit else f"{self.selected_measurement}"
            self.plot_widget.setLabel('bottom', x_axis_label)

            if isinstance(hist, np.ndarray) and len(hist) > 0 and isinstance(bin_edges, np.ndarray) and len(bin_edges) > 1:
                # create staircases
                x = np.repeat(bin_edges, 2)[1:-1]
                y = np.repeat(hist, 2)[:-1]

                color = colors.next()
                legend_label = f"{subset_name}:{self.selected_measurement}"
                self.plot_widget.plot(x, y, pen=pg.mkPen(color=color, width=1.5), stepMode="center", name=legend_label)

            average = stats["mean"]
            stdev = stats["stdev"]
            median = stats["median"]
            mad = stats["mad"]
            q1 = stats["q1"]
            q3 = stats["q3"]
            iqr = q3 - q1
            outliers = stats.get("num_outliers", 0)

            row_data = [
                subset_name,
                str(N),
                f"{format_float(average)}",
                f"{format_float(stdev)}",
                f"{format_float(median)}",
                f"{format_float(mad)}",
                f"{format_float(iqr)}",
                str(outliers)
            ]
            row_idx = self.table_widget.rowCount()
            self.table_widget.insertRow(row_idx)
            for col, val in enumerate(row_data):
                self.table_widget.setItem(row_idx, col, QTableWidgetItem(val))

        self.adjust_table_height()


    def adjust_table_height(self):
        self.table_widget.setMinimumHeight(0)
        self.table_widget.setMaximumHeight(16777215)
        self.table_widget.resizeRowsToContents()
        height = self.table_widget.horizontalHeader().height()
        for row in range(self.table_widget.rowCount()):
            height += self.table_widget.rowHeight(row)
        self.table_widget.setMaximumHeight(height + 4)

if __name__ == "__main__":
    from RoiMeasurements import RoiMeasurements
    from TinyRoiFile import TinyRoiFile
    import StopWatch
    from TinyRoiManager import TinyRoiManager
    from Roi import Roi

    app = QApplication(sys.argv)
    
    base_name="./TestData/A_stitch_RoiSet"
    zip_path = base_name+".zip"
    zip_out_path = base_name+"_OUT.zip"
    num_threads = 12

    rm = TinyRoiManager()
    rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)
    rm.force_feret()
    
    # fills the subset 'ALL'
    msmts = RoiMeasurements(rm)

    subset_name="DELETED"
    deleted_filter = lambda roi: (roi.state==Roi.ROI_STATE_DELETED) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=deleted_filter)
    msmts.compute_stats_subset(subset_name)

    subset_name="ACTIVE"
    active_filter = lambda roi: (roi.state==Roi.ROI_STATE_ACTIVE) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=active_filter)
    msmts.compute_stats_subset(subset_name)
  
    demo = HistogramFrame()
    demo.populate(msmts.measurement_names, "Area", msmts)
    demo.show()
    sys.exit(app.exec())
