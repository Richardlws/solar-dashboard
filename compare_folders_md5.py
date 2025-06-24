import os
import hashlib
from collections import defaultdict
from send2trash import send2trash
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QCheckBox, QMessageBox,QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys

def get_file_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def collect_files(folder):
    all_files = []
    for root, _, files in os.walk(folder):
        for f in files:
            all_files.append(os.path.join(root, f))
    return all_files

class CompareThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)

    def __init__(self, folder1, folder2):
        super().__init__()
        self.folder1 = folder1
        self.folder2 = folder2

    def run(self):
        files1 = collect_files(self.folder1)
        files2 = collect_files(self.folder2)
        total = len(files1) + len(files2)
        count = 0

        md5_map1 = defaultdict(list)
        for f in files1:
            try:
                md5 = get_file_md5(f)
                md5_map1[md5].append(f)
            except:
                pass
            count += 1
            self.progress.emit(int(count * 100 / total), os.path.basename(f))

        md5_map2 = defaultdict(list)
        for f in files2:
            try:
                md5 = get_file_md5(f)
                md5_map2[md5].append(f)
            except:
                pass
            count += 1
            self.progress.emit(int(count * 100 / total), os.path.basename(f))

        duplicates = []
        for md5 in set(md5_map1.keys()) & set(md5_map2.keys()):
            for f1 in md5_map1[md5]:
                for f2 in md5_map2[md5]:
                    duplicates.append((f1, f2))

        self.finished.emit(duplicates)

class DuplicateViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("重复文件比较与删除工具（支持多选）")
        self.setFixedSize(1000, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setMinimumWidth(1000)

        self.folder1 = ""
        self.folder2 = ""
        self.left_checks = []
        self.right_checks = []

        layout = QVBoxLayout()

        # 选择与进度部分
        folder_layout = QHBoxLayout()
        self.label1 = QLabel("未选择文件夹 1")
        self.label2 = QLabel("未选择文件夹 2")
        btn1 = QPushButton("选择文件夹 1")
        btn2 = QPushButton("选择文件夹 2")
        btn1.clicked.connect(self.select_folder1)
        btn2.clicked.connect(self.select_folder2)
        folder_layout.addWidget(btn1)
        folder_layout.addWidget(self.label1)
        folder_layout.addWidget(btn2)
        folder_layout.addWidget(self.label2)

        self.progress = QProgressBar()
        self.status = QLabel("")

        self.compare_btn = QPushButton("开始比较")
        self.compare_btn.clicked.connect(self.start_compare)

        self.delete_btn = QPushButton("🗑️ 删除勾选文件（移入回收站）")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)

        self.select_left_btn = QPushButton("全选左边")
        self.select_right_btn = QPushButton("全选右边")
        self.select_left_btn.clicked.connect(self.select_all_left)
        self.select_right_btn.clicked.connect(self.select_all_right)

        # 统一设置按钮高度
        for btn in [btn1, btn2, self.compare_btn, self.select_left_btn, self.select_right_btn, self.delete_btn]:
            btn.setFixedHeight(32)

        # 文件展示区域
        # 左列滚动区域
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_widget = QWidget()
        self.left_col = QVBoxLayout(self.left_widget)
        self.left_widget.setLayout(self.left_col)
        self.left_scroll.setWidget(self.left_widget)

        # 👉 设置滚动高度
        self.left_scroll.setFixedHeight(300)

        # 右列滚动区域
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_widget = QWidget()
        self.right_col = QVBoxLayout(self.right_widget)
        self.right_widget.setLayout(self.right_col)
        self.right_scroll.setWidget(self.right_widget)

        # 👉 设置滚动高度
        self.right_scroll.setFixedHeight(300)

        # 添加到水平布局中
        file_area = QHBoxLayout()
        file_area.addWidget(self.left_scroll)
        file_area.addWidget(self.right_scroll)

        layout.addLayout(folder_layout)
        layout.addWidget(self.compare_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addLayout(file_area)

        control_btns = QHBoxLayout()
        control_btns.addWidget(self.select_left_btn)
        control_btns.addStretch()
        control_btns.addWidget(self.delete_btn)
        control_btns.addStretch()
        control_btns.addWidget(self.select_right_btn)
        layout.addLayout(control_btns)

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

    def start_compare(self):
        if not self.folder1 or not self.folder2:
            QMessageBox.warning(self, "提示", "请先选择两个文件夹。")
            return

        self.clear_checks()
        self.clear_layout(self.left_col)
        self.clear_layout(self.right_col)
        self.progress.setValue(0)
        self.status.setText("正在比较，请稍候...")
        self.compare_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.thread = CompareThread(self.folder1, self.folder2)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.display_duplicates)
        self.thread.start()

    def update_progress(self, percent, filename):
        self.progress.setValue(percent)
        self.status.setText(f"正在处理：{filename}（{percent}%）")

    def display_duplicates(self, duplicates):
        if not duplicates:
            self.status.setText("✅ 没有发现重复文件。")
            self.compare_btn.setEnabled(True)
            return

        for left, right in duplicates:
            cb1 = QCheckBox(left)
            cb2 = QCheckBox(right)
            self.left_col.addWidget(cb1)
            self.right_col.addWidget(cb2)
            self.left_checks.append(cb1)
            self.right_checks.append(cb2)

        self.status.setText(f"共发现 {len(duplicates)} 对重复文件。")
        self.compare_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def delete_selected(self):
        def clean_path(path):
            # 清理多余前缀、统一分隔符
            return os.path.normpath(path).replace("\\\\?\\", "").strip('"')

        deleted = []
        for cb in self.left_checks + self.right_checks:
            if cb.isChecked():
                raw_path = cb.text()
                path = clean_path(raw_path)
                if os.path.isfile(path):
                    try:
                        send2trash(path)
                        deleted.append(path)
                        cb.setEnabled(False)
                        cb.setChecked(False)
                    except Exception as e:
                        QMessageBox.warning(self, "删除失败", f"{path}\n{e}")
                else:
                    QMessageBox.warning(self, "文件不存在", f"找不到文件：{path}")

        QMessageBox.information(self, "删除完成", f"成功删除 {len(deleted)} 个文件（已移入回收站）")

    def select_all_left(self):
        for cb in self.left_checks:
            cb.setChecked(True)

    def select_all_right(self):
        for cb in self.right_checks:
            cb.setChecked(True)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def clear_checks(self):
        self.left_checks.clear()
        self.right_checks.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DuplicateViewer()
    window.show()
    sys.exit(app.exec_())
