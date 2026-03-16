"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from collections.abc import Callable
from typing import Any
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject


from tiny_log import log
from tiny_roi_manager import TinyRoiManager

from average_color import average_color_and_grayness

class WorkbenchWorkerSignals(QObject):
    finished = pyqtSignal()

class WorkbenchWorker(QRunnable):
    def __init__(self, images: dict[str, Any], rm: dict[str, TinyRoiManager], on_finished: Callable):
        super().__init__()
        self.signals = WorkbenchWorkerSignals()
        self.images = images
        self.rm = rm
        self.on_finished = on_finished
        self.signals.finished.connect(on_finished)

    def run(self):
        self.do()

    def do(self):
            average_per_roi, grayness_per_roi = average_color_and_grayness(
                self.images["background"],
                self.images["cell_label"],
            )
            for roi_name,roi in self.rm["cell"].iter_all():
                if roi.color is not None and roi.grayness is not None:
                    continue
                idx= int(roi_name[1:]) # skip prefix
                if idx >= len(average_per_roi):
                    log(f"Color missing for {roi_name}",type="error")
                    continue
                roi.color = average_per_roi[idx]
                roi.grayness = float(grayness_per_roi[idx])

            
            self.rm["cell"].force_feret()

            self.signals.finished.emit()

def start_workbench_worker(images: dict[str, Any], rm: dict[str, TinyRoiManager], on_worker_done: Callable):
    worker = WorkbenchWorker(images, rm, on_finished=on_worker_done)
    QThreadPool.globalInstance().start(worker)
    #worker.do()
