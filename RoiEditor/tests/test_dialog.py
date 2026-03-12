from PyQt6.QtWidgets import QFileDialog, QWidget

from file_dialog import FileDialog
from stylesheet import overall

from RoiEditor.tests._helpers import fail


def test_dialog(qapp):
    parent = QWidget()
    parent.setStyleSheet(overall)
    dialog = FileDialog(500, 500, title="This my title", filter="*.*", parent=parent)
    dialog.exec = lambda: QFileDialog.DialogCode.Accepted
    result = dialog.showDialog()
    if result != QFileDialog.DialogCode.Accepted:
        fail("FileDialog did not report an accepted selection")
