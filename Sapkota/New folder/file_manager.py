import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QTextEdit, QLabel, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class FileManager(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter folder path here and press Enter")
        self.address_bar.returnPressed.connect(self.load_files_or_folders)

        self.filter_tree = QTreeWidget()
        self.filter_tree.setHeaderHidden(True)
        self.filter_tree.setMaximumWidth(250)
        self.filter_tree.itemClicked.connect(self.filter_changed)

        file_root = QTreeWidgetItem(["File"])
        for f in ["JPG", "PNG", "MP4", "MP3", "Documents", "Pictures", "GIF", "All"]:
            QTreeWidgetItem(file_root, [f])
        folder_root = QTreeWidgetItem(["Folder"])

        self.filter_tree.addTopLevelItem(file_root)
        self.filter_tree.addTopLevelItem(folder_root)
        self.filter_tree.expandAll()

        top_layout.addWidget(self.address_bar)
        top_layout.addWidget(self.filter_tree)
        layout.addLayout(top_layout)

        splitter = QSplitter(Qt.Horizontal)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Name", "Path"])
        self.table.cellClicked.connect(self.show_preview)

        splitter.addWidget(self.table)

        preview_splitter = QSplitter(Qt.Vertical)
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        preview_splitter.addWidget(self.text_preview)

        self.image_preview = QLabel("Image Preview")
        self.image_preview.setAlignment(Qt.AlignCenter)
        preview_splitter.addWidget(self.image_preview)

        splitter.addWidget(preview_splitter)

        layout.addWidget(splitter)

        self.current_path = ""
        self.current_filter_category = "File"
        self.current_filter = "All"

    def load_files_or_folders(self):
        path = self.address_bar.text().strip()
        if not os.path.exists(path) or not os.path.isdir(path):
            self.table.setRowCount(0)
            self.text_preview.clear()
            self.image_preview.clear()
            return
        self.current_path = path
        self.load_table()

    def filter_changed(self, item, column):
        parent = item.parent()
        if parent is None:
            self.current_filter_category = item.text(0)
            if item.childCount() > 0:
                self.current_filter = item.child(0).text(0)
                self.filter_tree.setCurrentItem(item.child(0))
            else:
                self.current_filter = "All"
        else:
            self.current_filter = item.text(0)
            self.current_filter_category = parent.text(0)
        self.load_table()

    def load_table(self):
        if not self.current_path:
            return
        entries = []
        try:
            for entry in os.listdir(self.current_path):
                full_path = os.path.join(self.current_path, entry)
                if self.current_filter_category == "File" and os.path.isfile(full_path):
                    if self.matches_filter(entry):
                        entries.append((entry, full_path))
                elif self.current_filter_category == "Folder" and os.path.isdir(full_path):
                    entries.append((entry, full_path))
        except Exception as e:
            print(f"Error reading directory: {e}")
            entries = []

        self.table.setRowCount(len(entries))
        for row, (name, path) in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(path))

        self.text_preview.clear()
        self.image_preview.clear()

    def matches_filter(self, filename):
        f = self.current_filter.lower()
        filename_lower = filename.lower()
        if f == "all":
            return True
        elif f == "documents":
            return filename_lower.endswith((".txt", ".docx", ".xlsx", ".pdf"))
        elif f == "pictures":
            return filename_lower.endswith((".jpg", ".jpeg", ".png", ".gif"))
        else:
            return filename_lower.endswith(f".{f}")

    def show_preview(self, row, column):
        path = self.table.item(row, 1).text()
        if os.path.isdir(path):
            self.text_preview.setText("[Folder selected - no preview]")
            self.image_preview.clear()
            return
        ext = path.lower().split('.')[-1]
        if ext in ["txt", "py", "md"]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(1000)
                self.text_preview.setText(content)
            except Exception as e:
                self.text_preview.setText(f"Error reading file:\n{e}")
            self.image_preview.clear()
        elif ext in ["jpg", "jpeg", "png", "gif"]:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(400, 300, Qt.KeepAspectRatio)
                self.image_preview.setPixmap(scaled)
            else:
                self.image_preview.setText("Cannot preview image")
            self.text_preview.clear()
        else:
            self.text_preview.clear()
            self.image_preview.clear()
