from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
from message_box_invalid_values import MessageBoxInvalidValues
from stylesheet import overall

from RoiEditor.tests._helpers import fail


def test_msgbxinvalid(qapp):
    try:
        parent = QWidget()
        parent.setStyleSheet(overall)
        msgbox = MessageBoxInvalidValues(parent)
        QTimer.singleShot(100, msgbox.correct_button.click)
        msgbox.exec()
        if msgbox.clickedButton() != msgbox.correct_button:
            fail("MessageBoxInvalidValues did not close via the correct button")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
