"""RoiEditor

Author: Bart Vanderbeke
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

class FileDialog(QFileDialog):
    def __init__(self, x=100, y=100,title: str= "",filter: str ="*.*", parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.setViewMode(QFileDialog.ViewMode.Detail)
        self.setNameFilter(filter)

        settings = QSettings("EditRois")
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
        self.last_dir = settings.value("FileLocation", default_dir)
        self.last_dir=normalize_path(self.last_dir)
        self.setDirectory(self.last_dir)

        self.target_pos = QPoint(x, y)

        self.move(-5000, -5000)
        self.setWindowOpacity(0)  # Optioneel: helemaal onzichtbaar

        self.show()
        self.repaint()

        #self.fileSelected.connect(self._highlight_filename)

    def setParent(self,parent):
        super().setParent(parent)
    def setWindowFlag(self,flag):
        super().setWindowFlag(flag)


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

if __name__ == "__main__":
    import sys
    from Stylesheet import overall

    app = QApplication(sys.argv)
    w = QWidget()
    w.setStyleSheet(overall)
    

    x = 500
    y = 500

    fd = FileDialog(x,y,title="This my title",filter="*.txt",parent = w)
    result = fd.showDialog()


    sys.exit(app.exec())