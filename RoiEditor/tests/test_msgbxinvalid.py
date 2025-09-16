import os
import sys
from PyQt6.QtWidgets import QApplication,QWidget

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from MessageBoxInvalidValues import MessageBoxInvalidValues
from Stylesheet import overall

def test_msgbxinvalid():

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    parent = QWidget()
    parent.setStyleSheet(overall)

    msgbox = MessageBoxInvalidValues(parent)
    result = msgbox.exec()

    if msgbox.clickedButton() == msgbox.correct_button:
        print("User clicked 'Correct'")
    else:
        print("User did magic: this cannot happen")
if __name__ == "__main__":
    test_msgbxinvalid()
