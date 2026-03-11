import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from stylesheet import overall
from file_dialog import FileDialog

def test_dialog():
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    w = QWidget()
    w.setStyleSheet(overall)
    

    x = 500
    y = 500

    if auto_close_ms > 0:
        print("Skipping modal file dialog in auto-close mode")
        return

    fd = FileDialog(x,y,title="This my title",filter="*.*",parent = w)
    result = fd.showDialog()


if __name__ == "__main__":
    test_dialog()
    sys.exit()
