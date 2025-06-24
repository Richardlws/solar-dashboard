import sys
import os
import hashlib
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QFileDialog,
    QLabel, QHBoxLayout, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

def get_all_files(folder):
    """返回文件夹内所有文件路径列表"""
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            full_path = os.path.join(root, f)
            files.append(full_path)
    return files

def get_file_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

# --- 线程类：后台执行比较 ---
class CompareThread(QThread):
    progress = pyqtSignal(int, str)         # 百分比进度 + 当前文件名
    finished = pyqtSignal(str)

    def __init__(self, folder1, folder2):
        super().__init__()
        self.folder1 = folder1
        self.folder2 = folder2

    def run(self):
        output = []
        all_files_1 = get_all_files(self.folder1)
        all_files_2 = get_all_files(self.folder2)
        total_files = len(all_files_1) + len(all_files_2)
        processed = 0

        md5_1 = defaultdict(list)
        for file in all_files_1:
            try:
                md5 = get_file_md5(file)
                md5_1[md5].append(file)
            except:
                pass
            processed += 1
            self.progress.emit(int(processed * 100 / total_files), os.path.basename(file))

        md5_2 = defaultdict(list)
        for file in all_files_2:
            try:
                md5 = get_file_md5(file)
                md5_2[md5].append(file)
            except:
                pass
            processed += 1
            self.progress.emit(int(processed * 100 / total_files), os.path.basename(file))

        output.append(f"📁 文件夹 1: {self.folder1}")
        output.append(f"📁 文件夹 2: {self.folder2}\n")

        common_md5 = set(md5_1.keys()) & set(md5_2.keys())
        if not common_md5:
            output.append("✅ 没有发现内容相同的文件。")
        else:
            output.append("⚠️ 发现内容相同的文件：\n")
            for md5 in common_md5:
                output.append(f"MD5: {md5}")
                for f1 in md5_1[md5]:
                    output.append(f"  - 📂 文件夹 1: {f1}")
                for f2 in md5_2[md5]:
                    output.append(f"  - 📂 文件夹 2: {f2}")
                output.append("")

        self.finished.emit('\n'.join(output))

# --- 主界面类 ---
class FolderCompareWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件夹内容对比（按 MD5）- 带进度条")
        self.setGeometry(200, 200, 800, 580)

        self.folder1 = ""
        self.folder2 = ""

        self.label1 = QLabel("未选择文件夹 1")
        self.label2 = QLabel("未选择文件夹 2")

        self.btn_select1 = QPushButton("选择文件夹 1")
        self.btn_select1.clicked.connect(self.select_folder1)

        self.btn_select2 = QPushButton("选择文件夹 2")
        self.btn_select2.clicked.connect(self.select_folder2)

        self.btn_compare = QPushButton("开始比较")
        self.btn_compare.clicked.connect(self.start_comparison)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

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
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.result_text)

        self.setLayout(layout)
        self.compare_thread = None

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

    def start_comparison(self):
        if not self.folder1 or not self.folder2:
            self.result_text.setText("❌ 请先选择两个文件夹。")
            return

        self.status_label.setText("🕐 正在比较，请稍候...")
        self.progress_bar.setValue(0)
        self.btn_compare.setEnabled(False)
        self.result_text.clear()

        self.compare_thread = CompareThread(self.folder1, self.folder2)
        self.compare_thread.progress.connect(self.update_progress)
        self.compare_thread.finished.connect(self.display_result)
        self.compare_thread.start()

    def update_progress(self, percent, filename):
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"🧾 正在处理：{filename}（{percent}%）")

    def display_result(self, result_text):
        self.result_text.setText(result_text)
        self.status_label.setText("✅ 比较完成。")
        self.btn_compare.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FolderCompareWindow()
    window.show()
    sys.exit(app.exec_())
