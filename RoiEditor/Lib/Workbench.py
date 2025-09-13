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
from skimage.io import imread
import numpy as np
import os
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget
from typing import Callable
from Exif import retrieve_tiff_image_info


from LabelToRoiDiff import process_label_image as lbl_process_label_image
from NumpyToRoi import process_label_image as np_process_label_image
from RoiEditor.Lib.PolygonEditor import PolygonEditor
from TinyRoiManager import TinyRoiManager
from TinyRoiFile import TinyRoiFile

from RoiImage import RoiImageWindow
from Context import gvars
from Crumbs import normalize_path

from RoyalKeyInterceptor import RoyalKeyInterceptor
#from .MouseListener import ROIClickListener
from StopWatch import *
from MeasurementWorker import compute_and_plot
from TinyLog import log

from HistogramFrame import HistogramFrame as QHF
from RoiMeasurements import RoiMeasurements

from CellsToNuclei import cells_to_nuclei
from Roi import Roi

from PolygonEditor import PolygonEditor

def get_timestamp_string():
    import datetime
    """Return current time as a string in yyyymmddHHMMSS format."""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

class Workbench(QWidget):
    """class implementing or coordinating all actions
    the idea is to isolate all visualization in the RoiEditorControlPanel,
    RoiImageWindow,RectangleSelectorView, HistogramFrame classes.
    The Workbench is where the real work happens or is coordinated:
    -files are read an processed
    -ROIs end up in the TinyRoiManager
    -the measurements and stats are collected in RoiMeasurements
    -the results are distributed to HistogramFrame and RoiImageWindow/RectangleSelectorView
     for visualization
    -actions are triggered through the incoming calls
    -the effects ripple to the UI and the rest of the system using call backs or 'event-like-calls',typically
     having names starting with 'on_...'
    """

    # Class member type definitions
    parent: QWidget | None
    original_file: str
    base_name: str 
    label_file: str
    cell_roi_file: str
    cell_rm: TinyRoiManager | None
    nuke_rm: TinyRoiManager | None
    rm_collection: list[TinyRoiManager] | None = None
    label_image: np.ndarray | None
    background_image: QImage | None
    background_image_as_rgb: np.ndarray | None
    hist_plot: QHF | None
    measurements: RoiMeasurements | None
    window: RoiImageWindow | None
    #mouse_listener: ROIClickListener | None
    backup_timer: QTimer
    working_dir: str
    msmts_dir: str
    roi_dir: str
    tiff_info: dict | None
    nucleus_label_img: np.ndarray | None
    interceptor: RoyalKeyInterceptor
    on_fail_to_write: Callable[[str], None]
    on_fail_to_build: Callable[[str], None]
    background_image_as_rgb: np.ndarray | None

    @staticmethod
    def dummy_callback_write(msg:str=""):
        log(f"Failed to write: {msg}",type="error")
    @staticmethod
    def dummy_callback_fail2build(msg:str=""):
        log(f"Failed to build: {msg}",)

    def __init__(self, original_file: str,
                 label_file: str,
                 cell_roi_file: str,
                 nuke_roi_file: str,
                 key_to_label_map: dict[str,str],
                 on_fail_to_write: Callable[[str],None]=dummy_callback_write,
                 on_fail_to_build: Callable[[str],None]=dummy_callback_fail2build,
                 parent:QWidget|None=None):
        super().__init__(parent)
        self.parent=parent
        self.original_file: str = original_file
        self.base_name: str = Path(self.original_file).stem
        self.label_file: str = label_file
        self.cell_roi_file: str = cell_roi_file
        self.nuke_roi_file: str = nuke_roi_file
        self.cell_rm: TinyRoiManager | None = None
        self.nuke_rm: TinyRoiManager | None = None
        self.on_fail_to_write=on_fail_to_write
        self.on_fail_to_build=on_fail_to_build
        self.backup_timer= QTimer(self)

        from PyQt6.QtCore import QSettings, QStandardPaths
        settings = QSettings("EditRois")
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
        self.working_dir = normalize_path(settings.value("FileLocation", default_dir))
        log(f"Work folder is {self.working_dir}")
        self.msmts_dir = normalize_path(self.working_dir + "/MsmtsBackup/")
        #log(f"Backups of measurements will be stored in: {self.msmts_dir}")
        os.makedirs(self.msmts_dir, exist_ok=True)
        self.roi_dir = normalize_path(self.working_dir + "/RoiBackup/")
        os.makedirs(self.roi_dir, exist_ok=True)
        log(f"Backups of ROIs will be stored in {self.roi_dir}")
      

        self.window = None
        self.mouse_listener=None

        name_to_code = {    "F2" : Qt.Key.Key_F2,
                            "F3" : Qt.Key.Key_F3,
                            "F4" : Qt.Key.Key_F4,
                            "F5" : Qt.Key.Key_F5,
                            "F6" : Qt.Key.Key_F6,
                            "F7" : Qt.Key.Key_F7,
                            "F8" : Qt.Key.Key_F8,
                            "F9" : Qt.Key.Key_F9,
                            "F10": Qt.Key.Key_F10,
                            "F11": Qt.Key.Key_F11,
                            "F12": Qt.Key.Key_F12                        
        }

        interceptor_key_action = {      Qt.Key.Key_Escape: (self.on_escape_key_pressed,None, True),
                                        Qt.Key.Key_Delete: (self.on_delete_key_pressed,None, True),
                                        Qt.Key.Key_F1: (self.on_f1_key_pressed,None, True)
        }
        for name,label in key_to_label_map.items():
            interceptor_key_action[name_to_code[name]] = (self.on_tagged_delete,label,True)

        self.interceptor = RoyalKeyInterceptor(mapping=interceptor_key_action,parent=self)

    def build(self):
        import cv2
        _, file_extension = os.path.splitext(self.label_file)
        if file_extension== '.npy':
            log("Using cellpose numpy data",type="info")
            data = np.load(self.label_file, allow_pickle=True).item()
            self.label_image = data["masks"]
        else:
            self.label_image= cv2.imread(self.label_file, cv2.IMREAD_UNCHANGED)

    
        lbl_h, lbl_w = self.label_image.shape[:2]
        

        self.background_image_as_rgb = imread(self.original_file)
        h, w, _ = self.background_image_as_rgb.shape
        self.background_image = QImage(self.background_image_as_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        #self.background_image = QImage(self.original_file)
        bkg_w = self.background_image.width()
        bkg_h = self.background_image.height()
        if bkg_w != lbl_w or bkg_h != lbl_h:
            log("image dimensions do not match",type="error")
            self.on_fail_to_build(f"image dimensions do not match: {bkg_w}x{bkg_h} <> {lbl_w}x{lbl_h}")
            return None
        
       
        image_size_str = f"width x height: {bkg_w} x {bkg_h} pixels"
        unit_and_scale=gvars["selected_unit_and_scale"]
        if unit_and_scale["source"] == 'no scaler/unit selected':
            image_size_str = f"width x height: {bkg_w} x {bkg_h} {unit_and_scale['length']['unit']}"
        else:
            physical_size_xy = unit_and_scale["length"]["scaler"] # micron/pixel
            bkg_w_mm = float(bkg_w) * physical_size_xy / 1000.0 # mm
            bkg_h_mm = float(bkg_h) * physical_size_xy / 1000.0 # mm
            image_size_str = f"width x height: {bkg_w_mm:.3f} x {bkg_h_mm:.3f} millimeter, using  xy scaler {unit_and_scale['length']['scaler']} {unit_and_scale['length']['unit']}/pixel, {unit_and_scale['source']}"
        
        _,fn = os.path.split(self.original_file)
        bottom_bar_text_str = f"File: {fn}, {image_size_str}"

        self.cell_rm = TinyRoiManager(parent=self)
        self.rm_collection = [self.cell_rm]

        if self.cell_roi_file and not self.cell_roi_file=="<no name>":
            log("Reading ROIs from zip",type="info")
            cell_roi_array = TinyRoiFile.read_parallel(zip_path=self.cell_roi_file, label_image =self.label_image,num_threads=gvars["read_parallel_num_threads"])
            self.cell_rm.add_from_list_unchecked(cell_roi_array)
        else:
            log("Creating ROIs from label file",type="info")
            StopWatch.start()
            if file_extension == '.npy':
                np_process_label_image(self.cell_rm, data, remove_edges=True, remove_small=True, size_threshold=gvars["roi_minimum_size"])
            else:
                lbl_process_label_image(self.cell_rm, self.label_image, remove_edges=True, remove_small=True, size_threshold=gvars["roi_minimum_size"])
            StopWatch.stop('process label image')

        self.nuke_rm = TinyRoiManager(prefix="N", parent=self)
        if not self.nuke_roi_file or self.nuke_roi_file=="<no name>":
            nuke_roi_array = cells_to_nuclei(self.background_image_as_rgb, self.label_image, self.cell_rm)
            self.nuke_rm.add_from_list_unchecked(nuke_roi_array)
        else:
            nuke_roi_array = TinyRoiFile.read_parallel(zip_path=self.nuke_roi_file, label_image =None,num_threads=gvars["read_parallel_num_threads"])
            self.nuke_rm.add_from_list_unchecked(nuke_roi_array)
            TinyRoiManager.zip(parent_rm=self.cell_rm, child_rm=self.nuke_rm)



        self.rm_collection.append(self.nuke_rm)




        self.cell_rm.force_feret()
        self.measurements=RoiMeasurements(rm=self.cell_rm,delayed_compute=True,unit_and_scale=unit_and_scale,parent=self)

        self.window = RoiImageWindow(qimage=self.background_image,rm=self.cell_rm ,nd=self.nuke_rm,msmts=self.measurements,on_any_change=self.on_any_change, parent=self)
        
        
        self.window.lbl_info.setText(bottom_bar_text_str)

        #self.window.on_set_overlay_visibility(overlay_visible=True)
        self.window.draw_image()

        self.window.showNormal()

        self.hist_plot=QHF(parent=self,on_measurement_selected=self.on_measurement_selected)


        screen = QApplication.primaryScreen().availableGeometry()
        x = max(0,(screen.width() - self.hist_plot.width()))
        y = 0
        self.hist_plot.move(x, y)

        compute_and_plot(self.cell_rm,self.hist_plot,self.measurements)

        self.window.installEventFilter(self.interceptor)

        #self.mouse_listener = ROIClickListener(rm=self.rm, roi_window=self.window, label_array=self.label_image,on_any_change=self.on_any_change,parent=self)
        #self.window.view.viewport().installEventFilter(self.mouse_listener)
        
        self.backup_timer.timeout.connect(self.make_backup)
        self.backup_timer.start(gvars["backup_interval_timer"]) # msec

        #from Context import format_qobject_tree
        #print(format_qobject_tree(self.parent))

        return self.window

    def clean_up(self):
        if self.window:
            self.window.hide()
        if self.backup_timer:
            self.backup_timer.stop()
        log("ROIs will be backed up")
        if self.on_backup_rois(): # and self.on_backup_measurements():
            log("ROIs backed up, safe to close",type="happy")
        else:
            log("No ROIs to be backed up, safe to close",type="happy")
        if self.cell_rm:
            self.cell_rm.deleteLater()
            self.cell_rm=None


    def make_backup(self):
        log("Timed backup triggered")
        #self.on_backup_measurements()
        self.on_backup_rois()        
    
    def on_measurement_selected(self,msmt_name: str):
        self.window.on_select_measurement(msmt_name)
        

    def on_any_change(self,message="",rebuild: bool=False):
        log("Updating: "+ message, type="info",log_level=1000)
        self.window.draw_image(rebuild=rebuild)
        compute_and_plot(self.cell_rm,self.hist_plot,self.measurements)

    def on_toggle_show_deleted(self):
        self.window.draw_image()
    def on_toggle_show_names(self):
        log("Toggling show names",type="info", log_level=1000)
        self.window.draw_image()
    def on_toggle_show_overlay(self):
        self.window.draw_image()
        
    def on_delete_key_pressed(self,argument):
        for trm in self.rm_collection:
            trm.delete_selected()
        self.on_any_change("DELETE key pressed")

    def on_escape_key_pressed(self,argument):
        for trm in self.rm_collection:
            trm.unselect_all()
        self.on_any_change("ESCAPE key pressed")
        
    def on_f1_key_pressed(self,argument):
        log("F1 key pressed: No function: use right-click and drag for rectangle select",type="warning")

    def on_tagged_delete(self,tag):
        for trm in self.rm_collection:
            trm.delete_selected(tag)
        self.on_any_change(f"Function key pressed for tagged delete: {tag}")
    
    def on_add_nucleus_here(self, roi: Roi, position: tuple[int,int]):
        # I clicked an existing nucleus
        if roi and roi.name[0] =='N':
            if roi.state == Roi.ROI_STATE_DELETED:
                log("Restoring a deleted nucleus",type="warning")
            else:
                log("An existing nucleus was clicked",type="info")
            roi.state = Roi.ROI_STATE_ACTIVE
            editor = PolygonEditor(self.background_image,window_width=150, roi=roi)
            roi = editor.run()
            self.on_any_change()
            return
        assert not roi or roi.name[0] == 'L'
        # I clicked a cell or the background
        # we will create a nucleus here
        if not TinyRoiManager.is_valid(self.nuke_rm):
            log("No nucleus ROI manager",type="warning")
            return
        new_nucleus_name = self.nuke_rm.first_free_name()

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
        self.nuke_rm.add(nuke_roi)
        if roi:
            log(f"Creating new nucleus {new_nucleus_name} as child of {roi.name}",type="info")
            roi.children.append(nuke_roi)
        else:
            log(f"Creating new nucleus {new_nucleus_name} on background",type="info")
        self.on_any_change(f"New nucleus {new_nucleus_name} added to parent {roi.name}",rebuild=True)

    def on_select_outliers(self):
        if not self.measurements:
            log("No measurements available", type="warning")
            return
        if not QHF.is_histogram_populated(self.hist_plot): # not 'hist_plot' in gvars:
            log("Histogram/selected measurement not (yet) available", type="warning")
            return

        selected_measurement = self.hist_plot.selected_measurement
        outliers = self.measurements.stats['ACTIVE'][selected_measurement]["outliers"]

        self.cell_rm.select(rois_or_names=outliers,reason_of_selection=selected_measurement+".outlier",additive=True)
        self.on_any_change(f"outliers selected for: {selected_measurement}")

    def on_select_outer(self):
        from .RoiSelect import select_outer_rois_vdb5
        if not TinyRoiManager.is_valid(self.cell_rm) or self.label_image is None:
            log("No ROIs or no label image",type="warning")
        select_outer_rois_vdb5(rm=self.cell_rm, label_image=self.label_image)
        self.on_any_change(f"outer edge selected")

    def on_save_measurements(self):
        if not self.measurements:
            log("No measurements available",type="warning")
            return False
        full_csv_name = normalize_path(f"{self.working_dir}{self.base_name}_msmts.csv")
        full_xlsx_name = normalize_path(f"{self.working_dir}{self.base_name}_msmts.xlsx")
        if Workbench.is_writable(full_csv_name) and Workbench.is_writable(full_xlsx_name):
            log(f"Saving measurements to {full_csv_name}")
            self.measurements.save_measurements_to_csv(full_name=full_csv_name, subset_name="ALL")
            self.measurements.save_measurements_to_xlsx(full_name=full_xlsx_name, subset_name="ALL")
            return True

        log(f"Cannot save measurements to {full_csv_name} or {full_xlsx_name}",type="error")
        self.on_fail_to_write(f"{full_csv_name},{full_xlsx_name}")
        return False


    def on_backup_measurements(self):
        if not self.measurements:
            log("No measurements available",type="warning")
            return False
        now = get_timestamp_string()
        full_name = normalize_path(f"{self.msmts_dir}{now}_{self.base_name}_msmts.csv")
        if Workbench.is_writable(full_name):
            log(f"Backing up measurements to {full_name}")
            self.measurements.save_measurements_to_csv(full_name=full_name, subset_name="ALL")
            return True
        log(f"Cannot backup measurements to {full_name}",type="error")            
        self.on_fail_to_write(full_name)
        return False

    
    def on_backup_rois(self):
        if not TinyRoiManager.is_valid(self.cell_rm):
            log("No ROIs available",type="warning")
            return False
        now = get_timestamp_string()
        cell_roi_list = [None] + [roi for roi in self.cell_rm._name_to_roi.values()]
        cell_roi_file_full_name = normalize_path(f"{self.roi_dir}{now}_{self.base_name}_RoiSet.zip")

        nuke_roi_list = [None] + [roi for roi in self.nuke_rm._name_to_roi.values()]
        nuke_roi_file_full_name = normalize_path(f"{self.roi_dir}{now}_{self.base_name}_NukeRoiSet.zip")


        if Workbench.is_writable(cell_roi_file_full_name) and Workbench.is_writable(nuke_roi_file_full_name):
            log(f"Backing up ROIs to {cell_roi_file_full_name}")
            TinyRoiFile.write_parallel(zip_path=cell_roi_file_full_name, roi_list=cell_roi_list, num_threads=gvars["save_rois_num_threads"])
            TinyRoiFile.write_parallel(zip_path=nuke_roi_file_full_name, roi_list=nuke_roi_list, num_threads=gvars["save_rois_num_threads"])
            return True

        log(f"Cannot backup ROIs to {cell_roi_file_full_name} or {nuke_roi_file_full_name}",type="error")
        self.on_fail_to_write(f"{cell_roi_file_full_name} or {nuke_roi_file_full_name}")
        return False



    def on_save_rois(self):
        if not TinyRoiManager.is_valid(self.cell_rm):
            log("No ROIs available",type="warning")
            return False

        cell_roi_list = [None] + [roi for roi in self.cell_rm._name_to_roi.values()]
        cell_roi_file_full_name = normalize_path(f"{self.working_dir}{self.base_name}_RoiSet.zip")

        nuke_roi_list = [None] + [roi for roi in self.nuke_rm._name_to_roi.values()]
        nuke_roi_file_full_name = normalize_path(f"{self.working_dir}{self.base_name}_NukeRoiSet.zip")

        if Workbench.is_writable(cell_roi_file_full_name) and Workbench.is_writable(nuke_roi_file_full_name):
            log(f"Saving ROIs to {cell_roi_file_full_name} and {nuke_roi_file_full_name}")
            TinyRoiFile.write_parallel(zip_path=cell_roi_file_full_name, roi_list=cell_roi_list, num_threads=gvars["save_rois_num_threads"])
            TinyRoiFile.write_parallel(zip_path=nuke_roi_file_full_name, roi_list=nuke_roi_list, num_threads=gvars["save_rois_num_threads"])
            return True
        
        log(f"Cannot save ROIs to {cell_roi_file_full_name} or {nuke_roi_file_full_name}",type="error")
        self.on_fail_to_write(f"{cell_roi_file_full_name} or {nuke_roi_file_full_name}")
        return False


    @staticmethod
    def is_writable(path):
        try:
            if os.path.exists(path):
                with open(path, 'a'):
                    pass  # Openen in append-modus, niet echt schrijven
            else:
                dir_path = os.path.dirname(path) or '.'
                testfile = os.path.join(dir_path, '.write_test_tmp')
                with open(testfile, 'w'):
                    pass
                os.remove(testfile)
            return True
        except (IOError, PermissionError):
            return False

