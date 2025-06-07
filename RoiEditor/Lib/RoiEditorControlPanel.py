"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QButtonGroup
from PyQt6 import uic

from pathlib import Path

from .FileChoosers import find_related_filenames
from .Context import gvars, key_to_label_map

from .Crumbs import normalize_path

from .Workbench import Workbench
from .TinyLog import log
from .Exif import retrieve_tiff_image_info
from .InputValidation import attach_extension_methods
from .Stylesheet import *

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")


class RoiEditorControlPanel(QMainWindow):
    """
    This is the main window of the RoiEditor application.
    Below the class hierarchy of the application is shown
    RoiEditorControlPanel
        log window                      : console window that displays status messages
        redirector                      : class that reroutes all prints to the log window
        Royal key interceptor           : class catching some application specific key presses
        Workbench                       : class implementing or coordinating all actions
            RoyalKeyInterceptor
            TinyRoiManager              : manages the collection of ROIs detected in the image shown in RoiImageWindow
                Roi                     : implements a subset of the functionality of Fiji ROIs
            RoiMeasurements             : manages the measurement-values (area, Feret) and their statistics
            RoiImageWindow              : shows the photograph, ROIs and overlays  
                RectangleSelectorView   : implements rectangle selection on RoiImageWindow
            HistogramFrame              : displays the statistics of RoiMeasurements
            ROIClickListener            : catches the application specific mouse clicks

    """
    ID_PIXEL = 1
    ID_FROM_FILE = 2
    ID_SPECIFIED = 3
    def __init__(self,parent=None):
        super().__init__(parent)
        super().move(-10000, -10000)

        self.setStyleSheet(overall)

        self.setWindowTitle("RoiEditor - Control Panel")
        basepath = os.path.dirname(__file__)
        uifile = os.path.join(basepath, "RoiEditorControlPanel.ui")

        uic.loadUi(uifile, self)
        self.closing=False
        # combined window has no parents

        self.file= { "org" : { "name" : None, "qlabel" : self.txt_original},
            "label" : { "name" : None, "qlabel" : self.txt_label},
            "zip" : { "name" : None, "qlabel" : self.txt_zip}
        }

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.workbench: Workbench = None
        self.label_hint: str = None
        self.bg_unit = QButtonGroup(self)
        self.bg_unit.addButton(self.rb_pixel_is_unit, id=self.ID_PIXEL)
        self.bg_unit.addButton(self.rb_unit_from_file, id=self.ID_FROM_FILE)
        self.bg_unit.addButton(self.rb_unit_specified, id=self.ID_SPECIFIED)
        self.le_custom_scale.setText(str(gvars["custom_scale_range"]["default"]))
        self.scalers= {self.ID_PIXEL: {"length": {"scaler": 1.0, "unit": "px"},"area": {"scaler": 1.0*1.0, "unit": "px"}, "source": "no scaler/unit selected"},
                      self.ID_FROM_FILE: {"length": {"scaler": None, "unit": "µm"},"area": {"scaler": None, "unit": "µm²"}, "source": "read from image"},
                      self.ID_SPECIFIED: {"length": {"scaler": None, "unit": "µm"},"area": {"scaler": None, "unit": "µm²"}, "source": "set by user"},
        }

        self.toggles = {"show_deleted": {"checked": self.cb_show_deleted.isChecked, "setting": "show_deleted", "action": self.wb_on_toggle_show_deleted},
               "show_overlay": {"checked": self.cb_show_overlay.isChecked, "setting": "show_overlay", "action": self.wb_on_toggle_show_overlay},
               "show_names"  : {"checked": self.cb_show_names.isChecked,   "setting": "show_names",   "action": self.wb_on_toggle_show_names},
        }


        attach_extension_methods(self)
                      

    def closeEvent(self, event):
        if self.closing:
            return
        self.closing=True
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        if self.workbench:
            self.clean_up()

        print(f"Closing application: {self.windowTitle()}")
        super().close()
        self.deleteLater()


    def on_previous(self):

        self.reset_names()
        if self.workbench:
            self.clean_up()
            self.close_windows(criterion=lambda x: x is not self and x is not self.log_window)
    
    def on_fail_to_build(self,msg:str=""):
        self.on_previous()
        
    def on_finish(self):

        if self.workbench:
            self.clean_up()
            self.close_windows(criterion=lambda x: x is not self)
        self.closeEvent(None)

    def close_windows(self,criterion):
        print("Closing windows")
        for widget in QApplication.topLevelWidgets():
            if not criterion(self):
                continue
            wpn = widget.parent().windowTitle() if widget.parent() else "orphan "+type(widget).__name__
            name = widget.windowTitle() or widget.objectName() or wpn
            if name:
                print(f"Closing window: {name}")
            super_obj = super(type(widget),widget)
            if hasattr(super_obj,"close"):
                super_obj.close()
            else:
                widget.close()
            widget.deleteLater()


    def clean_up(self):
        assert self.workbench is not None
        self.workbench.clean_up()
        self.workbench.setParent(None)
        self.workbench.deleteLater()
        self.workbench=None


    def handle_toggle(self,toggle_str:str):
        this_toggle=self.toggles[toggle_str]
        is_checked =this_toggle["checked"]()
        gvars[this_toggle["setting"]]=is_checked
        if not self.workbench:
            return
        this_toggle["action"]()        


    def on_toggle_show_deleted(self):
        self.handle_toggle("show_deleted")

    def wb_on_toggle_show_deleted(self):
        self.workbench.on_toggle_show_deleted()

    def on_toggle_show_overlay(self):
        self.handle_toggle("show_overlay")

    def wb_on_toggle_show_overlay(self):
        self.workbench.on_toggle_show_overlay()

    def on_toggle_show_names(self):
        self.handle_toggle("show_names")

    def wb_on_toggle_show_names(self):
        self.workbench.on_toggle_show_names()


    fn_color_dict = {False : "color: white; font-style: normal;",
                     True  : "color: orange; font-style: italic;"}

    def accept_name(self, for_which : str, value : str):
        # "zip" : { "name" : None, "qlabel" : self.txt_zip}
        value = normalize_path(value)
        style= self.fn_color_dict[self.workbench is not None]
        path=Path(value)
        qlbl =self.file[for_which]["qlabel"]
        qlbl.setText(path.stem+path.suffix)
        qlbl.setStyleSheet(style)
        self.file[for_which]["name"]=value
    
    def reset_names(self):
        self.le_scale_from_file.setText('unknown')
        for v in self.file.values():
            v["name"]="<no name>"
            qlbl=v["qlabel"]
            qlbl.setText("<no name>")
            qlbl.setStyleSheet(self.fn_color_dict[False])
    
    def reset_styles(self):
        for v in self.file.values():
            v["qlabel"].setStyleSheet(self.fn_color_dict[False])

    def reset_filename(self,for_which: str):
        v=self.file[for_which]
        v["name"]="<no name>"
        qlbl=v["qlabel"]
        qlbl.setText("<no name>")
        qlbl.setStyleSheet(self.fn_color_dict[False])

    def on_click_clear_original(self):
        log("Clear original filename")
        self.reset_filename(for_which="org")

    def on_click_clear_label(self):
        log("Clear label filename")
        self.reset_filename(for_which="label")
                            
    def on_click_clear_zip(self):
        log("Clear zip filename")
        self.reset_filename(for_which="zip")

    def on_click_browse_original(self):
        self.label_hint = None
        selected_file,hint = self.original_chooser.showDialog()
        if selected_file:
            other_files = find_related_filenames(selected_file)
            self.accept_name(for_which="org",value=selected_file)

            txt = 'unknown'
            if selected_file.endswith(".tiff") or selected_file.endswith(".tif"):
                tiff_info = retrieve_tiff_image_info(selected_file)
                physical_size_x= tiff_info.get("PhysicalSizeX",None)
                if physical_size_x:
                    txt=str(physical_size_x)
            self.le_scale_from_file.setText(txt)

            self.label_hint = hint or other_files[0]
            if self.label_hint:
                self.accept_name(for_which="label",value=self.label_hint)
            self.zip_hint = other_files[1]
            if self.zip_hint:
                self.accept_name(for_which="zip",value=self.zip_hint)
            

    def on_click_browse_label(self):
        selected_file: str = self.label_chooser.showDialog(self.label_hint)
        if selected_file:
            self.accept_name(for_which="label",value=selected_file)

    def on_click_browse_zip(self):
        selected_file: str =self.roi_chooser.showDialog()
        if selected_file:
            self.accept_name(for_which="zip",value=selected_file)

    def on_click_browse_next(self):

        path_str_org = self.file["org"]["name"]
        path_str_lbl = self.file["label"]["name"]
        path_str_zip= self.file["zip"]["name"]

        if not (path_str_org and path_str_lbl) or path_str_org=="<no name>" or path_str_lbl=="<no name>":
            log("Original or label file not selected",type="error")
            return
        if not (Path(path_str_org).exists() and Path(path_str_lbl).exists()):
            log("Original or label file cannot be found",type="error")
            return
        
        if not self.validate_entries_and_continue(): # ... or not
            log("Please enter valid numbers",type="warning")
            return

        if not (path_str_zip and Path(path_str_zip).exists()) or path_str_zip=="<no name>":
            log("Zip file not specified or not found",type="warning")
            self.file["zip"]["name"]="<no name>"
            self.file["zip"]["qlabel"].setText("<no name>")

        if self.workbench:
            log("Cleaning up previous session")
            self.clean_up()



        self.collect_and_report_settings()
        self.reset_styles()

        self.workbench = Workbench(original_file=self.file["org"]["name"],
                                   label_file=self.file["label"]["name"],
                                   roi_file=self.file["zip"]["name"],
                                   on_fail_to_write=self.on_cannot_write_to_file,
                                   on_fail_to_build=self.on_fail_to_build,
                                   key_to_label_map=key_to_label_map,parent=self)
        self.workbench.build()


    def on_save_rois(self):

        if not self.workbench:
            log("No files opened",type="warning")
            return False
        return self.workbench.on_save_rois()

    def on_save_table(self):

        if not self.workbench:
            log("No files opened",type="warning")
            return False
        return self.workbench.on_save_measurements()


    def on_select_outer(self):
        log("Select Outer")
        if not self.workbench:
           log("No files opened",type="warning")
           return
        self.workbench.on_select_outer()
 
    def on_select_outliers(self):
        #log("Select Outliers clicked")
        if not self.workbench:
            log("No files opened",type="warning")
            return
        self.workbench.on_select_outliers()
       
    def on_escape_key_pressed(self,argument):
        if not self.workbench:
            log("No files opened",type="warning")
            return
        self.workbench.on_escape_key_pressed(argument)

    def on_delete_key_pressed(self,argument):
        if not self.workbench:
            log("No files opened",type="warning")
            return
        self.workbench.on_delete_key_pressed(argument)

    def on_f1_key_pressed(self,argument):
        if not self.workbench:
            log("No files opened",type="warning")
            return
        self.workbench.on_f1_key_pressed(argument)

    def on_tagged_delete(self,label):
        if not self.workbench:
            log("No files opened",type="warning")
            return
        self.workbench.on_tagged_delete(label)
    
    def on_cannot_write_to_file(self, filepath):
        QTimer.singleShot(0, lambda: self.show_file_error_msg_box(filepath))

    def show_file_error_msg_box(self,filepath):
        msg = QMessageBox(parent=self)
        screen = msg.screen() or QApplication.primaryScreen()
        center = screen.geometry().center()
        msg.adjustSize()
        msg.move(center - msg.rect().center())
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("File write error")
        msg.setText("The file is already open or is not writable:")
        msg.setInformativeText(f"file: {filepath}")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec() # modal

    def collect_and_report_settings(self):
        log("Original:", self.file["org"]["name"])
        log("Label:", self.file["label"]["name"])
        log("Zip:", self.file["zip"]["name"])
        gvars["remove_at_edge"]=self.cbEdge.isChecked()
        gvars["remove_small"]=self.cbSmall.isChecked()
        log("Remove at edge?", gvars["remove_at_edge"])
        log("Remove small?", gvars["remove_small"])
        log("Min size:", gvars["roi_minimum_size"])
        # {"length": {"scaler": 1.0, "unit": "px"},"area": {"scaler": 1.0*1.0, "unit": "px"}, "source": "no scaler/unit selected"},
        log(gvars["selected_unit_and_scale"])

    def connect_all_handlers(self):
        self.cb_show_names.setChecked(gvars["show_names"])
        self.cb_show_deleted.setChecked(gvars["show_deleted"])
        self.cbEdge.setChecked(gvars["remove_at_edge"])
        self.cbSmall.setChecked(gvars["remove_small"])
        #self.cbPixel.setChecked(gvars["force_pixel_as_unit"])
        self.tbSize.setText(str(gvars["roi_minimum_size"]))
        self.cb_show_overlay.setChecked(gvars["show_overlay"])        
        self.btn_browse_original.clicked.connect(self.on_click_browse_original)
        self.btn_clear_original.clicked.connect(self.on_click_clear_original)
        self.btn_browse_label.clicked.connect(self.on_click_browse_label)
        self.btn_clear_label.clicked.connect(self.on_click_clear_label)
        self.btn_browse_zip.clicked.connect(self.on_click_browse_zip)
        self.btn_clear_zip.clicked.connect(self.on_click_clear_zip)

        self.btn_next.clicked.connect(self.on_click_browse_next)
        self.btn_outer.clicked.connect(self.on_select_outer)
        self.btn_saveRois.clicked.connect(self.on_save_rois)
        self.btn_outliers.clicked.connect(self.on_select_outliers)
        self.btn_saveTable.clicked.connect(self.on_save_table)
        self.cb_show_names.toggled.connect(self.on_toggle_show_names)

        self.cb_show_deleted.toggled.connect(self.on_toggle_show_deleted)

        self.cb_show_overlay.toggled.connect(self.on_toggle_show_overlay)

        self.btn_prev.clicked.connect(self.on_previous)
        self.btn_finish.clicked.connect(self.on_finish)

        #self.bg_unit.idToggled.connect(self.on_bg_unit_toggled)

        self.le_custom_scale.textChanged.connect(self.custom_scale_validate)
        self.tbSize.textChanged.connect(self.remove_small_validate)

    def set_up_key_interceptor(self):
        from .RoyalKeyInterceptor import RoyalKeyInterceptor
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
        self.interceptor.setObjectName("Royal key interceptor")
        self.installEventFilter(self.interceptor)
