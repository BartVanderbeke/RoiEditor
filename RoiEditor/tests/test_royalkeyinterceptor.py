import os
import sys

from PyQt6.QtWidgets import QApplication, QLabel,QMainWindow
from PyQt6.QtCore import Qt, QTimer
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lib')))


from royal_key_interceptor import RoyalKeyInterceptor


def test_keyinterceptor():
    auto_close_ms = int(os.getenv("ROI_TEST_AUTOCLOSE_MS", "0") or "0")

    app = QApplication([])
    app.setQuitOnLastWindowClosed(True)

    # 👑 A noble window
    window = QMainWindow()
    window.setWindowTitle("👑 Royal key listener")
    window.setGeometry(100, 100, 400, 200)

    label = QLabel("press Escape or F1", window)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)

    # 🎩 Royal interceptor
    # a dictionary describes the action associated with which key
    # key -> (action, argument, should_block)
    # "if not should_block", the key is passed on to regular key handler
    interceptor = RoyalKeyInterceptor({
        Qt.Key.Key_Escape: (lambda _: label.setText("We are on the move!"), None, True),
        Qt.Key.Key_F1: (lambda _: label.setText("Help is on its way!"), None, True),
        Qt.Key.Key_F5: (lambda _: label.setText("The screen has been refreshed!"), None, True),
    })

    # 🪄 attach to the window
    window.installEventFilter(interceptor)

    window.show()
    if auto_close_ms > 0:
        QTimer.singleShot(auto_close_ms, app.quit)
    app.exec()

if __name__ == "__main__":
    test_keyinterceptor()
