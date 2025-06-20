"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import os
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QSettings
from .FileDialog import FileDialog

from .Crumbs import normalize_path
from .Context import gvars
from .TinyLog import log

def find_related_filenames(reference_filepath: str):
    folder = os.path.dirname(reference_filepath)
    base_name, _ = os.path.splitext(os.path.basename(reference_filepath))
    filenames = os.listdir(folder)

    base_name=base_name.lower()
    
    # valid name-endings for label and ROI/zip files
    label_suffixes = ['_seg.npy', '_label.png', '_label.tif', '_label.tiff', '_label.jpg', '_cp_masks.png']
    zip_suffixes = ['_roiset.zip','_rois.zip'] # order indicates the preference

    label_file = None
    zip_file = None

    label_candidates = []
    zip_candidates = []

    for filename in filenames:
        fn =filename.lower()
        if fn.startswith(base_name):
            if any(fn.endswith(suffix) for suffix in label_suffixes):
                label_candidates.append(filename)
            elif any(fn.endswith(suffix) for suffix in zip_suffixes):
                zip_candidates.append(filename)

    # Select shortest valid name from the list of selected files
    label_file = min(label_candidates, key=len) if label_candidates else None

    def preferred_zip_file(candidates, suffixes):
        for suffix in suffixes:
            for f in candidates:
                fn =f.lower()
                if fn.endswith(suffix):
                    return f
        return None

    # Select using the preference as set in 'zip_suffixes'
    zip_file = preferred_zip_file(zip_candidates, zip_suffixes)

    return (
        os.path.join(folder, label_file) if label_file else None,
        os.path.join(folder, zip_file) if zip_file else None
    )

class QOriginalFileChooser:
    # if >2 files are selected the 2 shortest names are kept
    # after trimming to 2 names, the shortest one is chosen for the background image file
    # the longest name is kept as hint for the label file and passed on to the next chooser
    def __init__(self,x=100, y=0,parent=None):
        self.parent = parent
        name_filter = "Original Files (*.jpg *.png *.tif *.tiff)"
        self.dialog = FileDialog(x=x, y=y, title="Select original image", filter=name_filter, parent=self.parent)

    def showDialog(self):
        self.dialog.setDirectoryfromSettings()
        log(f"Label start folder: {self.dialog.getDirectory()}")

        if self.dialog.showDialog() == QFileDialog.DialogCode.Accepted:
            selected_files = self.dialog.selectedFiles()
            if selected_files:
                if len(selected_files) > 2:
                    log("Trimming number of selected files to 2", type="warning")
                selected_files = sorted(selected_files, key=lambda f: len(os.path.basename(f)))[:2]
                self.dialog.writeDirectoryToSettings()
                hint = selected_files[1] if len(selected_files) > 1 else None
                return selected_files[0], hint

        return None, None
    def setParent(self, parent):
        self.dialog.setParent(parent)
    def setWindowFlag(self,flag):
        self.dialog.setWindowFlag(flag)    

class QLabelFileChooser:
    def __init__(self, x=100, y=40,hint=None, parent=None):
        self.parent = parent
        self.hint = hint
        name_filter = "Label Files (*_label.png *_label.tif *_label.tiff *_label.jpg *_cp_masks.png *_seg.npy)"
        self.dialog = FileDialog(x=x, y=y, title="Select label file", filter=name_filter, parent=self.parent)

    def showDialog(self, hint=None):
        _hint=hint or self.hint
        if _hint:
            start_dir= normalize_path(os.path.dirname(_hint)) # dirname strips of trailing (back)slash
            self.dialog.setDirectory(start_dir)
        else:
            self.dialog.setDirectoryfromSettings()
        log(f"Label start folder: {self.dialog.getDirectory()}")

        if self.dialog.showDialog() == QFileDialog.DialogCode.Accepted:
            selected_files = self.dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]

                return selected_file

        return None
    def setParent(self, parent):
        self.dialog.setParent(parent)
    def setWindowFlag(self,flag):
        self.dialog.setWindowFlag(flag) 


import os
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QSettings, QStandardPaths

class QRoiFileChooser:
    def __init__(self,x=100, y=80, parent=None):
        self.parent = parent
        name_filter = "ROI Files (*.zip)"
        self.dialog = FileDialog(x=x, y=y, title="Select ROI ZIP file", filter=name_filter, parent=self.parent)


    def showDialog(self):
        self.dialog.setDirectoryfromSettings()
        log(f"Roi start folder: {self.dialog.getDirectory()}")

        if self.dialog.showDialog() == QFileDialog.DialogCode.Accepted:
            selected_files = self.dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]

                return selected_file

        return None
    
    def setParent(self, parent):
        self.dialog.setParent(parent)
    def setWindowFlag(self,flag):
        self.dialog.setWindowFlag(flag) 
