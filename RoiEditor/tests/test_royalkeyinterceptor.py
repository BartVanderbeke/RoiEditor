import os
import sys

from PyQt6.QtWidgets import QApplication, QLabel,QMainWindow
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


from RoiEditor.Lib.RoyalKeyInterceptor import RoyalKeyInterceptor


def test_keyinterceptor():

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
    app.exec()

if __name__ == "__main__":
    test_keyinterceptor()