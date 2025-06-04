"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import QObject, QEvent, Qt


class RoyalKeyInterceptor(QObject):
    def __init__(self, mapping=None, parent=None):
        super(RoyalKeyInterceptor, self).__init__(parent)
        self.mapping = mapping if mapping else {}

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in self.mapping:
                action, argument, should_block = self.mapping[key]
                try:
                    action(argument)
                except Exception as ex:
                    print(f"[Royal Error] Key {key}: {ex}")
                return should_block
        return False


if __name__ == "__main__":
    app = QApplication([])

    # 👑 A noble window
    window = QMainWindow()
    window.setWindowTitle("Royal key listener")
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
