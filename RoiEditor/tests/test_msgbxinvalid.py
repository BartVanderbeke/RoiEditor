import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget
from PyQt6.QtCore import QTimer
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))

from MessageBoxInvalidValues import MessageBoxInvalidValues
from Stylesheet import overall

def test_msgbxinvalid():
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    parent = QWidget()
    parent.setStyleSheet(overall)

    msgbox = MessageBoxInvalidValues(parent)
    if auto_close_ms > 0:
        QTimer.singleShot(auto_close_ms, msgbox.correct_button.click)
    result = msgbox.exec()

    if msgbox.clickedButton() == msgbox.correct_button:
        print("User clicked 'Correct'")
    else:
        print("User did magic: this cannot happen")
if __name__ == "__main__":
    test_msgbxinvalid()
