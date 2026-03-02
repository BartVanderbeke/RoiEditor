import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from Stylesheet import overall
from FileChoosers import QOriginalFileChooser,QLabelFileChooser,QRoiFileChooser

def test_choosers():
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
   

    w = QWidget()
    w.setStyleSheet(overall)


    if auto_close_ms > 0:
        base_path = os.path.dirname(__file__)
        test_path = os.path.join(base_path, "TestData")
        selected = os.path.join(test_path, "6.tif")
        hint = test_path
        print("--- QOriginalFileChooser ---")
        print("Selected, hint:", selected, hint)
        print("--- QLabelFileChooser ---")
        print("Selected:", os.path.join(test_path, "6_cp_masks.png"))
        print("--- QRoiFileChooser ---")
        print("Selected:", os.path.join(test_path, "6_rois.zip"))
    else:
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
