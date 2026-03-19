"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import sys

from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QSettings, QStandardPaths
from PyQt6.QtCore import QTimer, QPoint

from crumbs import normalize_path

IS_WINDOWS = sys.platform.startswith("win")

class FileDialog(QFileDialog):
    def __init__(self, x=100, y=100,title: str= "",filter: str ="*.*", parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.setViewMode(QFileDialog.ViewMode.Detail)
        self.setNameFilter(filter)

        self.target_pos = QPoint(x, y)

        if IS_WINDOWS:
            self.move(-5000, -5000)
            self.setWindowOpacity(0)  # Optioneel: helemaal onzichtbaar
            self.show()
            self.repaint()

        self.settings = QSettings("RoiEditor", "RoiEditor")

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
        if IS_WINDOWS:
            QTimer.singleShot(100, self._reveal)
        else:
            self.move(self.target_pos)
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
