from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QDialogButtonBox, QGridLayout
)
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QRect

from stylesheet import overall

class UserInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome, dear user")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._center_on_parent_or_screen()

        # Unicode letters + . - ( ) + spatie
        self._rx = QRegularExpression(r"^[\p{L}\.\-\(\) ]*$")
        self._validator = QRegularExpressionValidator(self._rx, self)

        # Widgets
        self.lbl_first_name = QLabel("First name:"); self.lbl_first_name.setObjectName("lbl_first_name")
        self.tb_first_name = QLineEdit(); self.tb_first_name.setObjectName("tb_first_name"); self.tb_first_name.setClearButtonEnabled(True); self.tb_first_name.setValidator(self._validator)

        self.lbl_last_name = QLabel("Last name:"); self.lbl_last_name.setObjectName("lbl_last_name")
        self.tb_last_name = QLineEdit(); self.tb_last_name.setObjectName("tb_last_name"); self.tb_last_name.setClearButtonEnabled(True); self.tb_last_name.setValidator(self._validator)

        self.lbl_organization = QLabel("Organization:"); self.lbl_organization.setObjectName("lbl_organization")
        self.tb_organization = QLineEdit(); self.tb_organization.setObjectName("tb_organization"); self.tb_organization.setClearButtonEnabled(True); self.tb_organization.setValidator(self._validator)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttons.accepted.connect(self.accept)

        # Layout
        grid = QGridLayout(self)
        grid.addWidget(self.lbl_first_name,   0, 0); grid.addWidget(self.tb_first_name,    0, 1)
        grid.addWidget(self.lbl_last_name,    1, 0); grid.addWidget(self.tb_last_name,     1, 1)
        grid.addWidget(self.lbl_organization, 2, 0); grid.addWidget(self.tb_organization,  2, 1)
        grid.addWidget(self.buttons,          3, 0, 1, 2)

        self.setMinimumWidth(360)
        self.setStyleSheet(overall)

        # Live highlight
        for le in (self.tb_first_name, self.tb_last_name, self.tb_organization):
            le.textChanged.connect(lambda _=None, w=le: self._update_invalid_state(w))

        # Laatste berekende result (leeg of ingevuld) wordt hier opgeslagen
        self._result_dict = {"first_name": "", "last_name": "", "organization": ""}



    def accept(self):

        self._store_result()
        super().accept()

    def reject(self):

        self._store_result(force_empty_if_invalid=True)
        super().reject()

    def closeEvent(self, e):
        # Bij sluiten met X: idem
        self._store_result(force_empty_if_invalid=True)
        e.accept()


    def get_values(self) -> dict:

        return dict(self._result_dict)


    def _has_invalid(self) -> bool:
        for w in (self.tb_first_name, self.tb_last_name, self.tb_organization):
            if self._validator.validate(w.text(), 0)[0].name == "Invalid":
                return True
        return False

    def _store_result(self, force_empty_if_invalid: bool = True):

        invalid = self._has_invalid()

        for w in (self.tb_first_name, self.tb_last_name, self.tb_organization):
            self._update_invalid_state(w)

        if force_empty_if_invalid and invalid:
            self._result_dict = {"first_name": "", "last_name": "", "organization": ""}
        else:
            self._result_dict = {
                "first_name": self.tb_first_name.text(),
                "last_name": self.tb_last_name.text(),
                "organization": self.tb_organization.text(),
            }

    def _update_invalid_state(self, w: QLineEdit):
        state = self._validator.validate(w.text(), 0)[0]
        w.setProperty("invalid", state.name == "Invalid")
        w.style().unpolish(w); w.style().polish(w)

    def _center_on_parent_or_screen(self):
        parent = self.parent()
        if parent and parent.isVisible() and parent.screen():
            screen = parent.screen()
        elif self.screen():
            screen = self.screen()
        else:
            screen = QGuiApplication.primaryScreen()


        avail: QRect = screen.availableGeometry()
        fg = self.frameGeometry()
        fg.moveCenter(avail.center())
        self.move(fg.topLeft())

# --- Minimal usage example ---
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dlg = UserInfoDialog()
    result = dlg.exec()  # 1=Accepted, 0=Rejected
    print("dialog result:", result)
    print(dlg.get_values())
