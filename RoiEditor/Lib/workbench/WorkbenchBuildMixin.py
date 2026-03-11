from functools import partial

import cv2
import numpy as np
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

import Context
from Context import gvars
from RoiEditor.Lib import Parents
from CellsToNuclei import cells_to_nuclei
from HistogramFrame import HistogramFrame as QHF
from LabelToRoiDiff import process_label_image as lbl_process_label_image
from NumpyToRoi import process_label_image as np_process_label_image
from RoiImage import RoiImageWindow
from RoiMeasurements import RoiMeasurements
from TinyLog import log
from TinyRoiFile import TinyRoiFile
from TinyRoiManager import TinyRoiManager
from WorkbenchWorker import start_workbench_worker


class WorkbenchBuildMixin:
    def collect_or_build(self, what: str) -> str:
        used_what = "no file read"
        numpy_data = dict()
        self.images[f"{what}_label"] = None

        np_process = partial(
            np_process_label_image,
            remove_edges=Context.gvars["remove_at_edge"],
            remove_small=Context.gvars["remove_small"],
            size_threshold=Context.gvars["roi_minimum_size"],
        )
        lbl_process = partial(
            lbl_process_label_image,
            remove_edges=Context.gvars["remove_at_edge"],
            remove_small=Context.gvars["remove_small"],
            size_threshold=Context.gvars["roi_minimum_size"],
        )
        fn = self.files[f"{what}_label"]()
        if fn.is_file():
            if fn.suffix.lower() == ".npy":
                numpy_data = np.load(str(fn), allow_pickle=True).item()
                img_label = numpy_data.get("masks", None)
            else:
                img_label = cv2.imread(str(fn), cv2.IMREAD_UNCHANGED)
            img_label = np.ascontiguousarray(img_label)
            self.images[f"{what}_label"] = img_label

        fn = self.files[f"{what}_zip"]()
        if fn.is_file():
            log(f"{what} ROIs ← {fn.name}", type="happy")
            roi_array = TinyRoiFile.read(zip_path=str(fn), label_image=self.images[f"{what}_label"])
            self.rm[what].add_from_list_unchecked(roi_array)
            used_what = "zip"
        else:
            if not self.files[f"{what}_label"]().is_file():
                log(f"{what} ROIs ← No {what} label file selected or found", type="warning")
                return ""

            fn = self.files[f"{what}_label"]().name
            log(f"{what} ROIs ← {fn}", type="happy")

            if numpy_data:
                log("-Using cellpose numpy data", type="happy", log_level=1000)
                np_process(self.rm[what], numpy_data)
                used_what = "numpy"
            else:
                log("-Using cellpose label data", type="happy", log_level=1000)
                lbl_process(self.rm[what], self.images[f"{what}_label"])
                used_what = "label"

        return used_what

    def build(self):
        self.parentWidget().eatAllEvents()

        self.rm = dict()

        img_bgr = cv2.imread(str(self.files["org"]()))
        img_bgr = np.ascontiguousarray(img_bgr)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_rgb = np.ascontiguousarray(img_rgb)
        self.images["background"] = img_rgb
        h, w, _ = self.images["background"].shape
        self.background_qimage = QImage(
            self.images["background"].data,
            w,
            h,
            3 * w,
            QImage.Format.Format_RGB888,
        )

        self.rm["cell"] = TinyRoiManager(prefix="L", parent=self)
        self.rm["nuke"] = TinyRoiManager(prefix="N", parent=self)

        image_size_str = f"width x height: {w} x {h} pixels"
        unit_and_scale = Context.gvars["selected_unit_and_scale"]
        if unit_and_scale["source"] == "no scaler/unit selected":
            image_size_str = f"width x height: {w} x {h} {unit_and_scale['length']['unit']}"
        else:
            physical_size_xy = unit_and_scale["length"]["scaler"]
            w_mm = float(w) * physical_size_xy / 1000.0
            h_mm = float(h) * physical_size_xy / 1000.0
            image_size_str = (
                f"width x height: {w_mm:.3f} x {h_mm:.3f} millimeter, using  xy scaler "
                f"{unit_and_scale['length']['scaler']} {unit_and_scale['length']['unit']}/px, "
                f"{unit_and_scale['source']}"
            )

        self.measurements = RoiMeasurements(
            cell_rm=self.rm["cell"],
            nuke_rm=self.rm["nuke"],
            unit_and_scale=unit_and_scale,
            parent=self,
        )

        self.roi_window = RoiImageWindow(
            qimage=self.background_qimage,
            rm=self.rm["cell"],
            nd=self.rm["nuke"],
            msmts=self.measurements,
            on_any_change=self.on_any_change,
            on_add_nucleus_here=self.on_add_nucleus_here,
            parent=self,
        )

        fn = self.files["org"]().name
        bottom_bar_text_str = f"File: {fn}, {image_size_str}"
        self.roi_window.lbl_info.setText(bottom_bar_text_str)
        self.roi_window.draw_image()
        self.roi_window.showNormal()

        self.roi_window.installEventFilter(self.interceptor)

        used_what_cell = self.collect_or_build(what="cell")

        if not TinyRoiManager.has_rois(self.rm["cell"]) or used_what_cell == "no file read":
            txt = "No valid cell ROIs detected in image or read from file"
            log(txt, type="error")
            self.on_fail_to_build(txt)
            return None

        force_detect_nuclei = gvars["detect_nuclei"]
        if force_detect_nuclei:
            nuke_roi_array = cells_to_nuclei(
                self.images["background"],
                self.images["cell_label"],
                self.rm["cell"],
            )
            self.rm["nuke"].add_from_list_unchecked(nuke_roi_array)
            if not TinyRoiManager.has_rois(self.rm["nuke"]):
                log("nuke ROIs ← No valid nucleus ROIs detected in image or read from file", type="warning")
            else:
                log(f"nuke ROIs ← {len(nuke_roi_array)} nukes from background image", type="happy")
            used_what_nuke = "forced detection"
        else:
            used_what_nuke = self.collect_or_build(what="nuke")
            if used_what_nuke == "zip":
                log("Reuniting nuke children with their cell parents using nuke zip", type="happy", log_level=1000)
                Parents.zip(parent_rm=self.rm["cell"], child_rm=self.rm["nuke"])
            elif used_what_nuke == "label" or used_what_nuke == "numpy":
                log("Finding cell parents for nuke children using label or numpy", type="happy")
                Parents.find_parent(
                    parent_rm=self.rm["cell"],
                    child_rm=self.rm["nuke"],
                    parent_label_image=self.images["cell_label"],
                )
            else:
                log("No nuke ROIs read from file", type="warning")

        lbl_h, lbl_w = self.images["cell_label"].shape[:2]
        if w != lbl_w or h != lbl_h:
            log("image dimensions do not match", type="error")
            self.on_fail_to_build(f"image dimensions do not match: {w}x{h} <> {lbl_w}x{lbl_h}")
            return None

        self.hist_plot = QHF(parent=self, on_measurement_selected=self.on_measurement_selected)
        self.roi_window.selected_measurement = "Area"

        screen = QApplication.primaryScreen().availableGeometry()
        x = max(0, (screen.width() - self.hist_plot.width()))
        y = 0
        self.hist_plot.move(x, y)

        wb_on_finished = lambda: self.on_any_change()
        start_workbench_worker(self.images, self.rm, on_worker_done=wb_on_finished)

        self.backup_timer.timeout.connect(self.make_backup)
        self.backup_timer.start(Context.gvars["backup_interval_timer"])

        log("All is in readiness for the commencement of the cleansing ceremony", type="happy")
        self.parentWidget().allowAllEvents()

        return self.roi_window

