"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
import sys

class MessageBoxInvalidValues(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Incorrect values")
        self.setText("Please provide valid values\nfor Min size\nand/or\nSpecified unit & scale")

        # Remove close button
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        #self.default_button = self.addButton("Default", QMessageBox.ButtonRole.AcceptRole)
        self.correct_button = self.addButton("Correct", QMessageBox.ButtonRole.ActionRole)

        self.setDefaultButton(self.correct_button)
        self.setIcon(QMessageBox.Icon.Critical)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        #self.default_button.setToolTip("Restore default values and continue")
        self.correct_button.setToolTip("Go back and edit the input values")

