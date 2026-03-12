from PyQt6.QtWidgets import QFileDialog, QWidget

from file_choosers import QLabelFileChooser, QOriginalFileChooser, QRoiFileChooser
from stylesheet import overall

from RoiEditor.tests._helpers import data_path, fail


def test_choosers(qapp):
    parent = QWidget()
    parent.setStyleSheet(overall)

    original_chooser = QOriginalFileChooser(parent=parent)
    original_selection = [str(data_path("A_stitch.tiff")), str(data_path("C_stitch.tiff"))]
    original_chooser.dialog.showDialog = lambda: QFileDialog.DialogCode.Accepted
    original_chooser.dialog.selectedFiles = lambda: original_selection
    selected, hint = original_chooser.showDialog()
    if selected != original_selection[0] or hint != original_selection[1]:
        fail("QOriginalFileChooser did not return the mocked selection")

    label_chooser = QLabelFileChooser(hint=hint, parent=parent)
    label_selection = [str(data_path("A_stitch_cp_masks.png"))]
    label_chooser.dialog.showDialog = lambda: QFileDialog.DialogCode.Accepted
    label_chooser.dialog.selectedFiles = lambda: label_selection
    if label_chooser.showDialog(hint) != label_selection[0]:
        fail("QLabelFileChooser did not return the mocked selection")

    roi_chooser = QRoiFileChooser(parent=parent)
    roi_selection = [str(data_path("A_stitch_roiset.zip"))]
    roi_chooser.dialog.showDialog = lambda: QFileDialog.DialogCode.Accepted
    roi_chooser.dialog.selectedFiles = lambda: roi_selection
    if roi_chooser.showDialog() != roi_selection[0]:
        fail("QRoiFileChooser did not return the mocked selection")
