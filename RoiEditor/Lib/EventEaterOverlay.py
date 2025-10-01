# PyQt6
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class EventEaterOverlay(QWidget):
    """Transparent overlay eating all events"""
    def __init__(self, target: QWidget, message: str | None = None):
        # parent = target → overlay remains within target, also with resize
        super().__init__(parent=target)
        self.setObjectName("EventEaterOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
        self._install_parent_watcher(target)

        # center label (status/“Busy...”)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch()
        self._label = QLabel(message or "", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("QLabel { color: #ddd; font-size: 14px; }")
        lay.addWidget(self._label)
        lay.addStretch()

        self.hide()  # start uit

    # ————— public API —————
    def activate(self, message: str | None = None):
        if message is not None:
            self._label.setText(message)
        self._resize_to_parent()
        self.raise_()
        self.show()
        self.setFocus()
        self.grabKeyboard()
        self.grabMouse()

    def deactivate(self):
        try:
            self.releaseKeyboard()
            self.releaseMouse()
        except Exception:
            pass
        self.hide()

    # ————— helpers —————
    def _install_parent_watcher(self, target: QWidget):
        self._parent = target
        target.installEventFilter(self)
        self._resize_to_parent()

    def _resize_to_parent(self):
        if self._parent:
            self.setGeometry(self._parent.rect())

    # keep overlay on top of parent
    def eventFilter(self, obj, ev):
        if obj is self._parent and ev.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show):
            self._resize_to_parent()
            if self.isVisible():
                self.raise_()
        return False

    # ————— eat all —————
    def event(self, ev):
        t = ev.type()
        # eet alle relevante input/events
        if t in (
            QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseMove,
            QEvent.Type.Wheel, QEvent.Type.HoverEnter, QEvent.Type.HoverMove, QEvent.Type.HoverLeave,
            QEvent.Type.KeyPress, QEvent.Type.KeyRelease,
            QEvent.Type.ContextMenu, QEvent.Type.Gesture,
            QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.DragLeave, QEvent.Type.Drop,
            QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd,
            QEvent.Type.FocusIn, QEvent.Type.FocusOut
        ):
            return True  # NIET doorgeven
        return super().event(ev)

# in the QMainWindow subclass (RoiEditorControlPanel)
# # in je QMainWindow-subclass (RoiEditorControlPanel)
#self.overlay = EventEaterOverlay(self,"Even geduld…")
# … wanneer je wilt blokkeren:
#self.overlay.activate("Bestanden laden…")
# … en om vrij te geven:
#self.overlay.deactivate()

# ... when you want to block:
# self.overlay.activate("Loading files...")
# ... and to release:
# self.overlay.deactivate()

