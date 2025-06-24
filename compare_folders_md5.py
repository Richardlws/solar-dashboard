import sys
import os
import hashlib
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QFileDialog, QLabel, QHBoxLayout
)
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
            except Exception:
                continue
    return file_md5_map

class FolderCompareWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信文件内容对比（按 MD5）")
        self.setGeometry(200, 200, 800, 500)

        self.folder1 = ""
        self.folder2 = ""

        self.label1 = QLabel("未选择文件夹 1")
        self.label2 = QLabel("未选择文件夹 2")

        self.btn_select1 = QPushButton("选择文件夹 1")
        self.btn_select1.clicked.connect(self.select_folder1)

        self.btn_select2 = QPushButton("选择文件夹 2")
        self.btn_select2.clicked.connect(self.select_folder2)

        self.btn_compare = QPushButton("开始比较")
        self.btn_compare.clicked.connect(self.compare_folders_md5)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.btn_select1)
        top_layout.addWidget(self.label1)

        mid_layout = QHBoxLayout()
        mid_layout.addWidget(self.btn_select2)
        mid_layout.addWidget(self.label2)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(mid_layout)
        layout.addWidget(self.btn_compare)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def select_folder1(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹 1")
        if folder:
            self.folder1 = folder
            self.label1.setText(folder)

    def select_folder2(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹 2")
        if folder:
            self.folder2 = folder
            self.label2.setText(folder)

    def compare_folders_md5(self):
        self.result_text.clear()
        if not self.folder1 or not self.folder2:
            self.result_text.setText("❌ 请先选择两个文件夹。")
            return

        self.result_text.append(f"📁 文件夹 1: {self.folder1}")
        self.result_text.append(f"📁 文件夹 2: {self.folder2}\n")

        md5_1 = collect_files_md5(self.folder1)
        md5_2 = collect_files_md5(self.folder2)

        common_md5 = set(md5_1.keys()) & set(md5_2.keys())
        if not common_md5:
            self.result_text.append("✅ 没有发现内容相同的文件。")
            return

        self.result_text.append("⚠️ 发现内容相同的文件：\n")
        for md5 in common_md5:
            self.result_text.append(f"MD5: {md5}")
            for f1 in md5_1[md5]:
                self.result_text.append(f"  - 📂 文件夹 1: {f1}")
            for f2 in md5_2[md5]:
                self.result_text.append(f"  - 📂 文件夹 2: {f2}")
            self.result_text.append("")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FolderCompareWindow()
    window.show()
    sys.exit(app.exec_())
