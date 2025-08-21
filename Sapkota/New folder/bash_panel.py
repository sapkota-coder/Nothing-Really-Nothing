from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt

class BashPanel(QTextEdit):
    command_executed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Bash Terminal - type commands and press Enter")
        self.setStyleSheet("background-color: black; color: green;")
        self.append("$ ")  # prompt

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            cursor.select(cursor.LineUnderCursor)
            line = cursor.selectedText().strip()
            if line.startswith("$"):
                line = line[1:].strip()
            if line:
                self.command_executed.emit(line)
                self.append("\n$ ")
            e.accept()
        else:
            super().keyPressEvent(e)
