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

from RoiEditor.Lib.FileChoosers import QOriginalFileChooser,QLabelFileChooser,QRoiFileChooser
from RoiEditor.Lib.TinyLog import log
from RoiEditor.Lib.LogWindow import StdoutRedirector, LogWindow
from RoiEditor.Lib.Stylesheet import overall
from RoiEditor.Lib.RoiEditorControlPanel import RoiEditorControlPanel
""" the class hierarchy of RoiEditor is explained in RoiEditorControlPanel """
""" RoiEditorControlPanel is the top level (window/widget) class"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")

def launch():

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./Lib/icon.png"))
    app.setQuitOnLastWindowClosed(True)

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

    window = RoiEditorControlPanel()


    log_window = LogWindow(parent=window)

    log_window.setObjectName("log window")
    log_window.setStyleSheet(overall)

    redirector = StdoutRedirector(parent=window)
    redirector.setObjectName("redirector")
    redirector = redirector
    redirector.html_written.connect(log_window.append_text)
    sys.stdout = redirector
    sys.stderr = redirector


    QTimer.singleShot(0, lambda: show())

    def show():
        window.show()
        log_window.show()


    def move_in_view():
        screen = QApplication.primaryScreen().availableGeometry()
        y = max(0,(screen.height() - log_window.height())-100)
        window.move(0,0)
        log_window.move(0,y)

    QTimer.singleShot(9, lambda: window.set_up_key_interceptor())

    QTimer.singleShot(12, lambda: window.connect_all_handlers())

    QTimer.singleShot(15, lambda: move_in_view())

    QTimer.singleShot(750, lambda: attach_choosers())


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
