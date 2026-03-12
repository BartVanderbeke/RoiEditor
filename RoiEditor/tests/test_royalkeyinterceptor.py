from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMainWindow

from royal_key_interceptor import RoyalKeyInterceptor

from RoiEditor.tests._helpers import fail, run_qt_loop


def test_keyinterceptor(qapp):
    try:
        window = QMainWindow()
        label = QLabel("press Escape or F1", window)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        window.setCentralWidget(label)
        interceptor = RoyalKeyInterceptor(
            {
                Qt.Key.Key_Escape: (lambda _: label.setText("We are on the move!"), None, True),
                Qt.Key.Key_F1: (lambda _: label.setText("Help is on its way!"), None, True),
                Qt.Key.Key_F5: (lambda _: label.setText("The screen has been refreshed!"), None, True),
            }
        )
        window.installEventFilter(interceptor)
        window.show()
        run_qt_loop(qapp, cleanup=window.close)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
