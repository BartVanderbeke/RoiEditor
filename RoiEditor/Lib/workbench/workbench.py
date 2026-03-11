"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from typing import Callable

import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QWidget

from histogram_frame import HistogramFrame as QHF
from roi_image import RoiImageWindow
from roi_measurements import RoiMeasurements
from royal_key_interceptor import RoyalKeyInterceptor
from tiny_log import log
from tiny_roi_manager import TinyRoiManager

from .workbench_actions_mixin import WorkbenchActionsMixin
from .workbench_build_mixin import WorkbenchBuildMixin
from .workbench_paths_mixin import WorkbenchPathsMixin
from .workbench_persistence_mixin import WorkbenchPersistenceMixin
from .workbench_refresh_mixin import WorkbenchRefreshMixin


class Workbench(
    QWidget,
    WorkbenchPathsMixin,
    WorkbenchBuildMixin,
    WorkbenchRefreshMixin,
    WorkbenchActionsMixin,
    WorkbenchPersistenceMixin,
):
    """class implementing or coordinating all actions
    the idea is to isolate all visualization in the RoiEditorControlPanel,
    RoiImageWindow,RectangleSelectorView, HistogramFrame classes.
    The Workbench is where the real work happens or is coordinated:
    -files are read and processed
    -ROIs end up in the TinyRoiManager
    -the measurements and stats are collected in RoiMeasurements
    -the results are distributed to HistogramFrame and RoiImageWindow/RectangleSelectorView
     for visualization
    -actions are triggered through the incoming calls
    -the effects ripple to the UI and the rest of the system using call backs or 'event-like-calls',typically
     having names starting with 'on_...'
    """

    @staticmethod
    def dummy_callback_write(msg: str = ""):
        log(f"Failed to write: {msg}", type="error")

    @staticmethod
    def dummy_callback_fail2build(msg: str = ""):
        log(f"Failed to build: {msg}", type="error")

    def __init__(
        self,
        selected_files: dict[str, str | None],
        event_filter: RoyalKeyInterceptor | None = None,
        on_fail_to_write: Callable[[str], None] = dummy_callback_write,
        on_fail_to_build: Callable[[str], None] = dummy_callback_fail2build,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.rm: dict[str, TinyRoiManager] = {}
        self.on_fail_to_write = on_fail_to_write
        self.on_fail_to_build = on_fail_to_build
        self.backup_timer = QTimer(self)
        self.original_file: str
        self.base_name: str
        self.label_file: str
        self.cell_roi_file: str
        self.rm: dict[str, TinyRoiManager] = {}
        self.label_image: np.ndarray | None
        self.background_qimage: QImage | None
        self.background_rgb_image: np.ndarray | None
        self.hist_plot: QHF | None
        self.measurements: RoiMeasurements | None
        self.roi_window: RoiImageWindow | None
        self.backup_timer: QTimer
        self.working_dir: str
        self.tiff_info: dict | None
        self.nucleus_label_img: np.ndarray | None
        self.on_fail_to_write: Callable[[str], None]
        self.on_fail_to_build: Callable[[str], None]
        self.background_rgb_image: np.ndarray | None
        self.images: dict[str, NDArray | None] = {}
        self.files = {}
        self.interceptor = event_filter

        self._init_paths(selected_files)

