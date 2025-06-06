"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""

from PyQt6.QtCore import QObject, QEvent


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

