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
from FileDialog import FileDialog

from Crumbs import normalize_path
from TinyLog import log

import os

def find_related_filenames(reference_filepath: str):
    folder = os.path.dirname(reference_filepath)
    base_name, _ = os.path.splitext(os.path.basename(reference_filepath))

    # geldige suffixen
    label_suffixes = ['_seg.npy', '_label.png', '_label.tif', '_label.tiff',
                      '_label.jpg', '_cp_masks.png']
    zip_suffixes = ['_roiset.zip', '_rois.zip']  # volgorde = voorkeur

    label_file = None
    zip_file = None

    # labels: pak de eerste bestaande exact-matchende kandidaat
    for suffix in label_suffixes:
        candidate = base_name + suffix
        if os.path.exists(os.path.join(folder, candidate)):
            label_file = os.path.join(folder, candidate)
            break

    # zip: idem, maar in voorkeurvolgorde
    for suffix in zip_suffixes:
        candidate = base_name + suffix
        if os.path.exists(os.path.join(folder, candidate)):
            zip_file = os.path.join(folder, candidate)
            break

    return label_file, zip_file


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
        log(f"Label start folder: {self.dialog.getDirectory()}", type="info")

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
        log(f"Label start folder: {self.dialog.getDirectory()}", type="info")

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
        log(f"Roi start folder: {self.dialog.getDirectory()}", type="info")

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
