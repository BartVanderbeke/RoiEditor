"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage
import cv2
#from skimage.io import imread
import numpy as np
from numpy.typing import NDArray
import os
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget
from typing import Any, Callable
from Exif import retrieve_tiff_image_info

from functools import partial


from LabelToRoiDiff import process_label_image as lbl_process_label_image
from NumpyToRoi import process_label_image as np_process_label_image
from RoiEditor.Lib import Parents
from TinyRoiManager import TinyRoiManager
from TinyRoiFile import TinyRoiFile

from RoiImage import RoiImageWindow
from Context import gvars
import Context
from Crumbs import normalize_path

from RoyalKeyInterceptor import RoyalKeyInterceptor
#from MouseListener import ROIClickListener

from MeasurementWorker import compute_and_plot
from TinyLog import log

from RoiSelect import select_outer_rois_vdb5

from HistogramFrame import HistogramFrame as QHF
from RoiMeasurements import RoiMeasurements

from CellsToNuclei import cells_to_nuclei
from Roi import Roi

from PolygonEditor import PolygonEditor

from AverageColor import distance_array, average_color

from WorkbenchWorker import start_workbench_worker

def get_timestamp_string():
    import datetime
    """Return current time as a string in yymmddHHMMSS format."""
    return datetime.datetime.now().strftime("%y%m%d%H%M%S")

class Workbench(QWidget):
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
    def dummy_callback_write(msg:str=""):
        log(f"Failed to write: {msg}",type="error")
    @staticmethod
    def dummy_callback_fail2build(msg:str=""):
        log(f"Failed to build: {msg}",type="error")

    def __init__(self, selected_files: dict[str, str | None],
                 event_filter: RoyalKeyInterceptor | None = None,
                 on_fail_to_write: Callable[[str],None]=dummy_callback_write,
                 on_fail_to_build: Callable[[str],None]=dummy_callback_fail2build,
                 parent:QWidget|None=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.rm: dict[str,TinyRoiManager] = {}
        self.on_fail_to_write=on_fail_to_write
        self.on_fail_to_build=on_fail_to_build
        self.backup_timer= QTimer(self)
        self.original_file: str
        self.base_name: str 
        self.label_file: str
        self.cell_roi_file: str
        self.rm: dict[str, TinyRoiManager]  = {}
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
        self.files: dict[str, Callable[[], Path]] = {}  
        self.interceptor= event_filter      

        self.files = {
            k: (lambda v=v: Path() if v is None else Path(v))
            for k, v in selected_files.items()
        }

        orgpath = Path(self.files["org"]())
        self.base_name = orgpath.stem
        self.working_dir = normalize_path(str(orgpath.parent))
        # "org" "label" "zip" "nukelabel" "nuke_zip" "zip_out" "nukezip_out" "zip_backup" "nukezip_backup"
        self.files["zip_out"]=lambda:  Path(f"{self.working_dir}{self.base_name}_roiset.zip")
        self.files["nukezip_out"]=lambda:  Path(f"{self.working_dir}{self.base_name}_nuke_roiset.zip")
        self.files["zip_backup"]=lambda:  Path(f"{self.working_dir}/RoiBackup/{get_timestamp_string()}_{self.base_name}_roiset.zip")
        self.files["nukezip_backup"]=lambda:  Path(f"{self.working_dir}/RoiBackup/{get_timestamp_string()}_{self.base_name}_nuke_roiset.zip")
        self.files["msmts_csv_out"]=lambda:  Path(f"{self.working_dir}{self.base_name}_msmts.csv")
        self.files["msmts_xlsx_out"]=lambda:  Path(f"{self.working_dir}{self.base_name}_msmts.xlsx")


        roi_dir = self.files["zip_backup"]().parent
        os.makedirs(roi_dir, exist_ok=True)
        log(f"ROI Backup folder: {roi_dir}",type="info")




    def collect_or_build(self,what : str) -> str:

        used_what = "no file read"
        numpy_data = dict()
        self.images[f"{what}_label"]=None

        np_process = partial(
            np_process_label_image,
            remove_edges=Context.gvars["remove_at_edge"],
            remove_small=Context.gvars["remove_small"],
            size_threshold=Context.gvars["roi_minimum_size"]
        )
        lbl_process = partial(
            lbl_process_label_image,
            remove_edges=Context.gvars["remove_at_edge"],
            remove_small=Context.gvars["remove_small"],
            size_threshold=Context.gvars["roi_minimum_size"]
        )
        fn = self.files[f"{what}_label"]()
        if fn.is_file():
            if fn.suffix.lower() == '.npy':
                numpy_data = np.load(str(fn), allow_pickle=True).item()
                img_label = numpy_data.get("masks", None)
            else:
                img_label = cv2.imread(str(fn), cv2.IMREAD_UNCHANGED)
            img_label = np.ascontiguousarray(img_label)
            self.images[f"{what}_label"] = img_label

        fn = self.files[f"{what}_zip"]()
        if fn.is_file():
            log(f"{what} ROIs ← {fn.name}",type="happy")
            roi_array = TinyRoiFile.read(zip_path=str(fn), label_image =self.images[f"{what}_label"])
            self.rm[what].add_from_list_unchecked(roi_array)
            used_what = "zip"
        else:

            if not self.files[f"{what}_label"]().is_file():
                log(f"{what} ROIs ← No {what} label file selected or found",type="warning")
                return ""
        
            fn = self.files[f"{what}_label"]().name
            log(f"{what} ROIs ← {fn}",type="happy")

            if numpy_data:
                log("-Using cellpose numpy data",type="happy",log_level=1000)
                np_process(self.rm[what], numpy_data)
                used_what = "numpy"
            else:
                log("-Using cellpose label data",type="happy",log_level=1000)
                lbl_process(self.rm[what], self.images[f"{what}_label"])
                used_what = "label"

        return used_what

    def build(self):
        self.parentWidget().eatAllEvents()

        self.rm = dict()


        img_bgr = cv2.imread(str(self.files["org"]())) #cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_bgr = np.ascontiguousarray(img_bgr)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_rgb = np.ascontiguousarray(img_rgb)
        self.images["background"] = img_rgb
        h, w, _ = self.images["background"].shape
        self.background_qimage = QImage(self.images["background"].data, w, h, 3 * w, QImage.Format.Format_RGB888)



        self.rm["cell"] = TinyRoiManager(prefix="L",parent=self)
        self.rm["nuke"] = TinyRoiManager(prefix="N", parent=self)

        image_size_str = f"width x height: {w} x {h} pixels"
        unit_and_scale=Context.gvars["selected_unit_and_scale"]
        if unit_and_scale["source"] == 'no scaler/unit selected':
            image_size_str = f"width x height: {w} x {h} {unit_and_scale['length']['unit']}"
        else:
            physical_size_xy = unit_and_scale["length"]["scaler"] # micron/pixel
            w_mm = float(w) * physical_size_xy / 1000.0 # mm
            h_mm = float(h) * physical_size_xy / 1000.0 # mm
            image_size_str = f"width x height: {w_mm:.3f} x {h_mm:.3f} millimeter, using  xy scaler {unit_and_scale['length']['scaler']} {unit_and_scale['length']['unit']}/px, {unit_and_scale['source']}"

        self.measurements=RoiMeasurements(cell_rm=self.rm["cell"],nuke_rm=self.rm["nuke"],unit_and_scale=unit_and_scale,parent=self)


        self.roi_window = RoiImageWindow(qimage=self.background_qimage,
                                     rm=self.rm["cell"] ,nd=self.rm["nuke"],msmts=self.measurements,
                                     on_any_change=self.on_any_change,
                                     on_add_nucleus_here=self.on_add_nucleus_here,
                                     parent=self)


        fn = self.files["org"]().name
        bottom_bar_text_str = f"File: {fn}, {image_size_str}"        
        self.roi_window.lbl_info.setText(bottom_bar_text_str)
        self.roi_window.draw_image()
        self.roi_window.showNormal()

       
        self.roi_window.installEventFilter(self.interceptor)


        used_what_cell = self.collect_or_build(what="cell")


        if not TinyRoiManager.has_rois(self.rm["cell"]) or used_what_cell == "no file read":
            txt = "No valid cell ROIs detected in image or read from file"
            log(txt,type="error")
            self.on_fail_to_build(txt)
            return None

        force_detect_nuclei = gvars["detect_nuclei"]
        if force_detect_nuclei:
            nuke_roi_array = cells_to_nuclei(self.images["background"], self.images["cell_label"], self.rm["cell"])
            self.rm["nuke"].add_from_list_unchecked(nuke_roi_array)
            if not TinyRoiManager.has_rois(self.rm["nuke"]):
                log(f"nuke ROIs ← No valid nucleus ROIs detected in image or read from file",type="warning")
            else:
                log(f"nuke ROIs ← {len(nuke_roi_array)} nukes from background image",type="happy")
            used_what_nuke = "forced detection"
        else:
            used_what_nuke = self.collect_or_build(what="nuke")
            if used_what_nuke == "zip":
                log("Reuniting nuke children with their cell parents using nuke zip",type="happy",log_level=1000)
                Parents.zip(parent_rm=self.rm["cell"], child_rm=self.rm["nuke"])
            elif used_what_nuke == "label" or used_what_nuke == "numpy":
                log("Finding cell parents for nuke children using label or numpy",type="happy")
                Parents.find_parent(parent_rm=self.rm["cell"], child_rm=self.rm["nuke"],parent_label_image=self.images["cell_label"])
            else:
                log("No nuke ROIs read from file",type="warning")


        lbl_h, lbl_w = self.images["cell_label"].shape[:2]
        if w != lbl_w or h != lbl_h:
            log("image dimensions do not match",type="error")
            self.on_fail_to_build(f"image dimensions do not match: {w}x{h} <> {lbl_w}x{lbl_h}")
            return None 



        self.hist_plot=QHF(parent=self,on_measurement_selected=self.on_measurement_selected)

        screen = QApplication.primaryScreen().availableGeometry()
        x = max(0,(screen.width() - self.hist_plot.width()))
        y = 0
        self.hist_plot.move(x, y)

        wb_on_finished = lambda :  self.on_any_change()
        start_workbench_worker(self.images, self.rm, on_worker_done=wb_on_finished)

        self.backup_timer.timeout.connect(self.make_backup)
        self.backup_timer.start(Context.gvars["backup_interval_timer"]) # msec

        log(f"All is in readiness for the commencement of the cleansing ceremony", type="happy")
        self.parentWidget().allowAllEvents()

        return self.roi_window

    def clean_up(self):
        if self.roi_window:
            self.roi_window.hide()
        if self.hist_plot:
            self.hist_plot.hide()
        if self.backup_timer:
            self.backup_timer.stop()
        log("ROIs will be backed up")
        if self.on_backup_rois():
            log("ROIs backed up, safe to close",type="happy")
        else:
            log("No ROIs to be backed up, safe to close",type="happy")
        for k in self.rm.keys():
            self.rm[k].deleteLater()
            # self.rm[k]=None
        self.rm.clear()

    def make_backup(self):
        log("Timed backup triggered")
        #self.on_backup_measurements()
        self.on_backup_rois()        
    
    def on_measurement_selected(self,msmt_name: str):
        self.roi_window.on_select_measurement(msmt_name)

    def on_any_change_callback(self,rebuild: bool | None = False):
        self.roi_window.draw_image(rebuild=rebuild if rebuild is not None else False)
        assert all(roi.color is not None for roi in self.rm["cell"].list_rois())

    def on_any_change(self, message: str = "", rebuild: bool | None = False):
        log("Updating: "+ message, type="info",log_level=1000)
        on_finished = lambda: self.on_any_change_callback(rebuild=rebuild)
        compute_and_plot(self.rm["cell"],self.hist_plot,self.measurements,on_finished_callback=on_finished)




    def on_toggle_show_deleted(self):
        self.roi_window.draw_image()
    def on_toggle_show_names(self):
        log("Toggling show names",type="info", log_level=1000)
        self.roi_window.draw_image()
    def on_toggle_show_overlay(self):
        self.roi_window.draw_image()
        
    def on_delete_key_pressed(self,argument):
        for trm in self.rm.values():
            trm.delete_selected()
        self.on_any_change("DELETE key pressed")

    def on_escape_key_pressed(self,argument):
        for trm in self.rm.values():
            trm.unselect_all()
        self.on_any_change("ESCAPE key pressed")
        
    def on_f1_key_pressed(self,argument):
        log("F1 key pressed: No function: use right-click and drag for rectangle select",type="warning")

    def on_tagged_delete(self,tag):
        for trm in self.rm.values():
            trm.delete_selected(tag)
        self.on_any_change(f"Function key pressed for tagged delete: {tag}")
    
    def on_add_nucleus_here(self, roi: Roi, position: tuple[int,int]):
        # I clicked an existing nucleus
        if roi and roi.name[0] =='N':
            if roi.state == Roi.ROI_STATE_DELETED:
                log(f"Restoring a deleted nucleus {roi.name}",type="warning")
            else:
                log(f"An existing nucleus {roi.name} was clicked",type="info")
            roi.state = Roi.ROI_STATE_ACTIVE
            roi.tags= {x for x in roi.tags if not x.startswith("DELETED")}
            editor = PolygonEditor(self.background_qimage,window_width=150, roi=roi,parent=self.roi_window)
            roi = editor.run()
            self.on_any_change()
            return
        assert not roi or roi.name[0] == 'L'
        # I clicked a cell or the background
        # we will create a nucleus here
        if self.rm["nuke"] is None:
            log("No nucleus ROI manager",type="error")
            return
        new_nucleus_name = self.rm["nuke"].first_free_name()

        nuke_roi: Roi = Roi(
            xpoints=np.array([position[0]], dtype=float),
            ypoints=np.array([position[1]], dtype=float),
            name=new_nucleus_name,
            bounds=(position[1],position[0], position[1], position[0]),
            center=position,
            n=1,
            area=0,
            state=Roi.ROI_STATE_ACTIVE,
            tags=set(),
            parent=roi # parent may be None
            )
        self.rm["nuke"].add(nuke_roi)
        if roi:
            log(f"Creating new nucleus {new_nucleus_name} as child of {roi.name}",type="info")
            roi.children.append(nuke_roi)
            if roi.state==Roi.ROI_STATE_DELETED:
                nuke_roi.state=Roi.ROI_STATE_DELETED
                nuke_roi.tags.add("DELETED.WITH_PARENT")
        else:
            log(f"Creating new nucleus {new_nucleus_name} on background",type="info")
        self.on_any_change(f"New nucleus {new_nucleus_name} added to parent {roi.name}",rebuild=True)

    def on_select_outliers(self):
        if not self.measurements:
            log("No measurements available (yet)", type="warning")
            return
        if not QHF.is_histogram_populated(self.hist_plot): # not 'hist_plot' in Context.gvars:
            log("Histogram/selected measurement not (yet) available", type="warning")
            return

        selected_measurement = self.hist_plot.selected_measurement
        outliers = self.measurements.stats['ACTIVE'][selected_measurement]["outliers"]

        self.rm["cell"].select(rois_or_names=outliers,reason_of_selection=selected_measurement+".outlier",additive=True)
        self.on_any_change(f"outliers selected for: {selected_measurement}")

    def on_select_outer(self):

        if not TinyRoiManager.has_rois(self.rm["cell"]) or self.images["cell_label"] is None:
            log("No ROIs or no label image",type="warning")
        select_outer_rois_vdb5(rm=self.rm["cell"], label_image=self.images["cell_label"])
        self.on_any_change(f"outer edge selected")

    def on_save_measurements(self):
        if not self.measurements:
            log("No measurements available",type="warning")
            return False

        full_csv_name = str(self.files["msmts_csv_out"]())
        full_xlsx_name = str(self.files["msmts_xlsx_out"]())
        pc = self.files["msmts_csv_out"]()
        px = self.files["msmts_xlsx_out"]()
        if Workbench.__is_writable(full_csv_name) and Workbench.__is_writable(full_xlsx_name):

            log(f"Saving measurements to {pc.name}")
            log(f"Saving measurements to {px.name}")
            self.measurements.save_measurements_to_csv(full_name=full_csv_name, subset_name="ALL")
            self.measurements.save_measurements_to_xlsx(full_name=full_xlsx_name, subset_name="ALL")
            return True

        log(f"Cannot save measurements to {pc} or {px} in folder {px.parent}",type="error")
        self.on_fail_to_write(f"{pc},{px}")
        return False


    def __write_rois(self,cell_roi_path : Path, nuke_roi_path : Path):

        nuke_roi_full_name = str(nuke_roi_path)
        nukes_writable = Workbench.__is_writable(nuke_roi_full_name)
        if TinyRoiManager.has_rois(self.rm["nuke"]):
            nuke_roi_list = [None] + list(self.rm["nuke"]._name_to_roi.values())
            if nukes_writable:
                log(f"Saving Nuke ROIs to {nuke_roi_path.name}")
                TinyRoiFile.write_parallel(zip_path=nuke_roi_full_name, roi_list=nuke_roi_list, num_threads=Context.gvars["save_rois_num_threads"])
        else:
            log("No Nuke ROIs available to be saved",type="warning")

        cell_roi_full_name = str(cell_roi_path)
        cells_writable = Workbench.__is_writable(cell_roi_full_name)
        if cells_writable:
            log(f"Saving Cell ROIs to {cell_roi_path.name}")
            cell_roi_list = [None] + list(self.rm["cell"]._name_to_roi.values())
            TinyRoiFile.write_parallel(zip_path=cell_roi_full_name, roi_list=cell_roi_list, num_threads=Context.gvars["save_rois_num_threads"])

        ret_value = cells_writable and nukes_writable
        if not ret_value:
            log(f"Cannot save ROIs to {nuke_roi_path.name} or {cell_roi_path.name} in folder {cell_roi_path.parent}",type="error")
            self.on_fail_to_write(f"{nuke_roi_path.name} or {cell_roi_path.name}")

        return ret_value

    
    def on_backup_rois(self):
        if not TinyRoiManager.has_rois(self.rm["cell"]):
            log("No Cell ROIs available",type="warning")
            return False
        return self.__write_rois(self.files["zip_backup"](), self.files["nukezip_backup"]())



    def on_save_rois(self):
        if not TinyRoiManager.has_rois(self.rm["cell"]):
            log("No Cell ROIs available",type="warning")
            return False
        return self.__write_rois(self.files["zip_out"](), self.files["nukezip_out"]())


    @staticmethod
    def __is_writable(path):
        try:
            if os.path.exists(path):
                with open(path, 'a'):
                    pass  # Open in append mode, not writing anything
            else:
                dir_path = os.path.dirname(path) or '.'
                testfile = os.path.join(dir_path, '.write_test_tmp')
                with open(testfile, 'w'):
                    pass
                os.remove(testfile)
            return True
        except (IOError, PermissionError):
            return False

