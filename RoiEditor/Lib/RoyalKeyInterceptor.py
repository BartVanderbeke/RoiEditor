"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QToolTip
from PyQt6.QtGui import QCursor

from TinyLog import log


class RoyalKeyInterceptor(QObject):
    def __init__(self, mapping=None, parent=None):
        super(RoyalKeyInterceptor, self).__init__(parent)
        self.mapping = mapping if mapping else {}

    def eventFilter(self, a0, a1):
        # a0 = object, a1 = event
        t = a1.type()
        # hover enter & leave
        if t == QEvent.Type.Enter:
            if a0 and a0.toolTip():
                QToolTip.showText(QCursor.pos(), a0.toolTip(), a0)
        if t == QEvent.Type.Leave:
                QToolTip.hideText()


        if a1.type() == QEvent.Type.KeyPress:
            key = a1.key()
            if key in self.mapping:
                action, argument, should_block = self.mapping[key]
                #try:
                action(argument)
                #except Exception as ex:
                #    log(f"[Royal Error] Key {key}: {ex}",type="error")
                return should_block
        return False

