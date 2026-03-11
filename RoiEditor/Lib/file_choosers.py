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

from file_dialog import FileDialog

from crumbs import normalize_path
from tiny_log import log

import os


suffixes: dict[str, list[str]] = {}
suffixes["org"] = ['.tif', '.tiff', '.png', '.jpg', '.png']
suffixes["cell_label"] = ['_cp_masks.png', '_seg.npy', '_label.png', '_label.tif', '_label.tiff', '_label.jpg']
suffixes["cell_zip"] = ['_roiset.zip', '_rois.zip']
suffixes["nuke_label"] = ['_nuke_cp_masks.png', '_nuke_seg.npy', '_nuke_label.png', '_nuke_label.tif', '_nuke_label.tiff', '_nuke_label.jpg']
suffixes["nuke_zip"] = ['_nuke_roiset.zip', '_nuke_rois.zip']


def find_related_filenames(reference_filepath: str) -> dict[str, str | None]:
    folder = os.path.dirname(reference_filepath)
    base_name, _ = os.path.splitext(os.path.basename(reference_filepath))

    files: dict[str, str | None] = {"org": None, "cell_label": None, "cell_zip": None, "nuke_label": None, "nuke_zip": None}

    for key, suffix_list in suffixes.items():
        for suffix in suffix_list:
            candidate = base_name + suffix
            candidate_path = os.path.join(folder, candidate)
            if os.path.exists(candidate_path):
                files[key] = candidate_path
                break
    return files


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
        log(f"Label start folder: {self.dialog.getDirectory()}", type="info", log_level=1000)

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
        log(f"Label start folder: {self.dialog.getDirectory()}", type="info", log_level=1000)

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
