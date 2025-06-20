"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtWidgets import QFileDialog, QApplication,QWidget
from PyQt6.QtWidgets import QTreeView
from PyQt6.QtCore import QSettings, QStandardPaths
from PyQt6.QtCore import QTimer, QPoint

import sys

from .Crumbs import normalize_path
from .TinyLog import log

class FileDialog(QFileDialog):
    def __init__(self, x=100, y=100,title: str= "",filter: str ="*.*", parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.setViewMode(QFileDialog.ViewMode.Detail)
        self.setNameFilter(filter)

        self.target_pos = QPoint(x, y)

        self.move(-5000, -5000)
        self.setWindowOpacity(0)  # Optioneel: helemaal onzichtbaar

        self.show()
        self.repaint()

        self.settings = QSettings("EditRois")

        #self.fileSelected.connect(self._highlight_filename)

    def setParent(self,parent):
        super().setParent(parent)
    def setWindowFlag(self,flag):
        super().setWindowFlag(flag)

    def setDirectoryfromSettings(self):
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
        start_dir = self.settings.value("FileLocation", default_dir)
        start_dir=normalize_path(start_dir)
        self.setDirectory(start_dir)

    def writeDirectoryToSettings(self):
        current_dir=normalize_path(self.directory().absolutePath())
        self.settings.setValue("FileLocation", current_dir)
    
    def getDirectory(self):
        return normalize_path(self.directory().absolutePath())


    def showDialog(self):
        QTimer.singleShot(100, self._reveal)
        return self.exec()

    def _reveal(self):
        self.move(self.target_pos)
        self.setWindowOpacity(1)
        self.raise_()
        self.activateWindow()
        
    # def _highlight_filename(self, *_):
    #     for w in self.findChildren(QTreeView):
    #         if w.isVisible() and w.isEnabled():
    #             w.setFocus()
    #             w.selectAll()
    #             break

