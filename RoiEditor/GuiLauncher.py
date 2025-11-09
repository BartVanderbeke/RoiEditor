"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer

from FileChoosers import QOriginalFileChooser,QLabelFileChooser,QRoiFileChooser
from TinyLog import log
from LogWindow import StdoutRedirector, LogWindow
from Stylesheet import overall
from RoiEditorControlPanel import RoiEditorControlPanel
""" the class hierarchy of RoiEditor is explained in RoiEditorControlPanel """
""" RoiEditorControlPanel is the top level (window/widget) class"""

from UserInfo import UserInfoDialog
from PyQt6.QtCore import QSettings

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")

# on Windows settings are stored in the registry:
# HKEY_CURRENT_USER\Software\RoiEditor\RoiEditor
settings = QSettings("RoiEditor", "RoiEditor")
first_name = settings.value("UserInfo/first_name", "")
last_name = settings.value("UserInfo/last_name", "")
organization = settings.value("UserInfo/organization", "")
dummy=None

def launch():
    global settings
    global first_name
    global last_name
    global organization
    global dummy

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./Lib/icon.png"))
    app.setQuitOnLastWindowClosed(False)

    from PyQt6.QtWidgets import QGraphicsTextItem
    _ = QGraphicsTextItem("warm up")

    """" 90% of the stuff below prevents the windows to first flash a white canvas when they appear """

    dummy=QWidget()

    dummy.setStyleSheet(overall)
    dummy.hide()
    dummy.move(0,0)

    original_chooser = QOriginalFileChooser(parent=dummy)
    label_chooser = QLabelFileChooser(parent=dummy)
    roi_chooser = QRoiFileChooser(parent=dummy)

    window = RoiEditorControlPanel(parent=dummy)


    log_window = LogWindow(parent=window)

    log_window.setObjectName("log window")
    log_window.setStyleSheet(overall)

    redirector = StdoutRedirector(parent=window)
    redirector.setObjectName("redirector")
    redirector = redirector
    redirector.html_written.connect(log_window.append_text)
    sys.stdout = redirector
    sys.stderr = redirector

    

    user_info_ok = (first_name and last_name and organization)
    if not user_info_ok:
        log("Requesting user info", type="info", log_level=1000)
        dlg = UserInfoDialog(parent=dummy)
        result = dlg.exec()
        if result:
            user_info = dlg.get_values()
            first_name = user_info.get("first_name", "")
            last_name = user_info.get("last_name", "")
            organization = user_info.get("organization", "")
            user_info_ok = (first_name and last_name and organization)
            if user_info_ok:
                settings.setValue("UserInfo/first_name", first_name)
                settings.setValue("UserInfo/last_name", last_name)
                settings.setValue("UserInfo/organization", organization)
    if not user_info_ok:
        log("User info dialog was cancelled or invalid. Proceeding without user info", type="warning")
    QTimer.singleShot(0, lambda: show())



    def show():
        global first_name
        window.show()
        log_window.show()
        if not first_name:
            log(f"Good day, esteemed user.", type="happy", log_level=0)
        else:
            log(f"Good day, esteemed {first_name}.", type="happy", log_level=0)
        log(f"How may I be of service to you today?", type="happy", log_level=0)

    def move_in_view():
        screen = QApplication.primaryScreen().availableGeometry()
        y = max(0,(screen.height() - log_window.height())-100)
        window.move(0,0)
        log_window.move(0,y)

    QTimer.singleShot(9, lambda: window.set_up_key_interceptor())

    QTimer.singleShot(12, lambda: window.connect_all_handlers())

    QTimer.singleShot(15, lambda: move_in_view())

    QTimer.singleShot(20, lambda: attach_choosers())


    def attach_choosers():
        window.original_chooser = original_chooser
        window.original_chooser.setParent(window)
        original_chooser.setWindowFlag(Qt.WindowType.Window)
        window.label_chooser = label_chooser
        window.label_chooser.setParent(window)
        label_chooser.setWindowFlag(Qt.WindowType.Window)
        window.roi_chooser = roi_chooser
        window.roi_chooser.setParent(window)
        roi_chooser.setWindowFlag(Qt.WindowType.Window)


    sys.exit(app.exec())
