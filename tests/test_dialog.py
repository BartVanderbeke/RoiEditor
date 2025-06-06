import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RoiEditor.Lib.Stylesheet import overall
from RoiEditor.Lib.FileDialog import FileDialog

def test_dialog():
    app = QApplication(sys.argv)
    w = QWidget()
    w.setStyleSheet(overall)
    

    x = 500
    y = 500

    fd = FileDialog(x,y,title="This my title",filter="*.*",parent = w)
    result = fd.showDialog()


if __name__ == "__main__":
    test_dialog()
    sys.exit()