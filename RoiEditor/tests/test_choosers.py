import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from RoiEditor.Lib.Stylesheet import overall
from RoiEditor.Lib.FileChoosers import QOriginalFileChooser,QLabelFileChooser,QRoiFileChooser

def test_choosers():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
   

    w = QWidget()
    w.setStyleSheet(overall)


    print("--- QOriginalFileChooser ---")
    original_chooser = QOriginalFileChooser(parent = w)
    selected, hint = original_chooser.showDialog()
    print("Selected, hint:", selected,hint)

    print("--- QLabelFileChooser ---")
    label_chooser = QLabelFileChooser(hint=hint,parent=w)
    print("Selected:", label_chooser.showDialog(hint))

    print("--- QRoiFileChooser ---")
    roi_chooser = QRoiFileChooser(parent=w)
    print("Selected:", roi_chooser.showDialog())


    #sys.exit(app.exec())

if __name__ == "__main__":
    test_choosers()
    sys.exit()