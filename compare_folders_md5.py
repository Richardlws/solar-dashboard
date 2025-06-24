import sys
import os
import hashlib
from collections import defaultdict
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

def get_file_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def collect_files_md5(folder):
    file_md5_map = {}
    for root, _, files in os.walk(folder):
        for f in files:
            full_path = os.path.join(root, f)
            try:
                md5 = get_file_md5(full_path)
                file_md5_map.setdefault(md5, []).append(full_path)
            except Exception as e:
                continue
    return file_md5_map

class FolderCompareWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件夹内容对比（按MD5） - 拖入两个文件夹")
        self.setGeometry(200, 200, 800, 500)
        self.setAcceptDrops(True)

        self.label = QLabel("请将两个文件夹拖入窗口进行比较：", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.folder_paths = []

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        folders = [u.toLocalFile() for u in urls if os.path.isdir(u.toLocalFile())]
        if len(folders) != 2:
            self.text_edit.setText("❌ 请拖入两个文件夹。")
            return
        self.folder_paths = folders
        self.compare_folders_md5()

    def compare_folders_md5(self):
        folder1, folder2 = self.folder_paths
        self.text_edit.setText(f"📁 比较文件夹:\n1️⃣ {folder1}\n2️⃣ {folder2}\n\n")

        md5_1 = collect_files_md5(folder1)
        md5_2 = collect_files_md5(folder2)

        common_md5 = set(md5_1.keys()) & set(md5_2.keys())
        if not common_md5:
            self.text_edit.append("✅ 没有发现内容相同的文件。")
            return

        self.text_edit.append("⚠️ 发现内容相同的文件：\n")
        for md5 in common_md5:
            self.text_edit.append(f"MD5: {md5}")
            for f1 in md5_1[md5]:
                self.text_edit.append(f"  - 📂 文件夹1: {f1}")
            for f2 in md5_2[md5]:
                self.text_edit.append(f"  - 📂 文件夹2: {f2}")
            self.text_edit.append("")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FolderCompareWindow()
    window.show()
    sys.exit(app.exec_())
