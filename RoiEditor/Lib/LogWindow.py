"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtWidgets import QWidget,  QVBoxLayout
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtCore import Qt
import re

from PyQt6.QtGui import QFont
class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        super().move(-5000,-5000)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle("RoiEditor - Log Window")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.textbox = QPlainTextEdit()
        self.textbox.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        font = QFont("Courier New", 12)  # naam + grootte
        self.textbox.setFont(font)
        self.textbox.setReadOnly(True)
        layout.addWidget(self.textbox)

    def append_text(self, html):
        self.textbox.appendHtml(html)
        self.textbox.verticalScrollBar().setValue(self.textbox.verticalScrollBar().maximum())

class StdoutRedirector(QObject):
    html_written = pyqtSignal(str)

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self._buffer = ""

    def write(self, text):
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                html_line = str(self.ansi_to_html(line))
                self.html_written.emit(html_line)

    def flush(self):
        if self._buffer.strip():
            html_line = self.ansi_to_html(self._buffer)
            self.html_written.emit(html_line)
        self._buffer = ""

    def ansi_to_html(self, text):
        # ANSI-code naar HTML-kleur
        ansi_colors = {
            '30': 'black',
            '31': 'red',
            '32': 'green',
            '33': 'orange',         # yellow/orange
            '34': 'blue',
            '35': 'magenta',
            '36': 'cyan',
            '37': 'lightgrey',      # grayish white
            '90': 'gray',
            '91': 'lightcoral',     # red
            '92': 'lightgreen',
            '93': 'khaki',          # bright yellow?
            '94': 'lightskyblue',
            '95': 'plum',           # pink
            '96': 'lightcyan',
            '97': 'white'
        }

        span_stack = []

        # Eerst HTML escapen (maar ANSI behouden)
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def replace(match):
            code = match.group(1)
            if code == '0':  # reset
                closing = '</span>' * len(span_stack)
                span_stack.clear()
                return closing
            elif code in ansi_colors:
                color = ansi_colors[code]
                span_stack.append('span')
                return f'<span style="color:{color}">'
            else:
                return ''

        ansi_escape = re.compile(r'\x1b\[(\d{1,3})m')
        html = ansi_escape.sub(replace, text)

        if span_stack:
            html += '</span>' * len(span_stack)
            span_stack.clear()

        return f'<div style="white-space: pre;">{html}</div>'