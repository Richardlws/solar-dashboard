import sys
import hashlib
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt, QMimeData
from collections import defaultdict
import os

def get_file_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

class DragDropWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信文件去重 - 拖拽MD5比较工具")
        self.setGeometry(300, 300, 800, 500)
        self.setAcceptDrops(True)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.text_edit.setText("请拖入多个文件到此窗口，程序将自动对比内容（MD5）...\n")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls() if os.path.isfile(url.toLocalFile())]
        if files:
            self.compare_files(files)

    def compare_files(self, files):
        self.text_edit.clear()
        md5_map = defaultdict(list)

        for file in files:
            try:
                md5 = get_file_md5(file)
                md5_map[md5].append(file)
                self.text_edit.append(f"✅ {os.path.basename(file)}\n    MD5: {md5}\n")
            except Exception as e:
                self.text_edit.append(f"❌ 读取失败: {file}，原因：{e}\n")

        self.text_edit.append("\n🔍 内容相同的文件组：")
        for md5, file_list in md5_map.items():
            if len(file_list) > 1:
                self.text_edit.append(f"\n⚠️ MD5: {md5}")
                for f in file_list:
                    self.text_edit.append(f"   - {f}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DragDropWindow()
    window.show()
    sys.exit(app.exec_())
