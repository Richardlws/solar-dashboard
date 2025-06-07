import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
from Serial_Data_Processor import extract_and_calculate


class SerialDataGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("串口接收数据分析器")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        self.select_btn = QPushButton("选择数据文件")
        self.select_btn.clicked.connect(self.select_file)
        layout.addWidget(self.select_btn)

        self.result_label = QLabel("结果：")
        layout.addWidget(self.result_label)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开TXT文件", "", "Text Files (*.txt)")
        if file_path:
            try:
                result = extract_and_calculate(file_path)
                output = ""
                unit_map = {
                    '电网用电': 'kWh',
                    '电网返送': 'kWh',
                    ##'real_sampling_time_seconds': '秒',
                    ##'sampling_interval_seconds': '秒',
                    ##'total_normal': '',
                    ##'special_sum': '',
                    ##'records_normal': '条',
                    ##'records_80': '条',
                    ##'swapped_segments': '条',
                    '开始时间': '',
                    '结束时间': ''
                }
                for k, v in result.items():
                    unit = unit_map.get(k, '')
                    output += f"{k}: {v} {unit}\n"
                    self.result_box.setText(output)
            except Exception as e:
                    self.result_box.setText(f"处理出错: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = SerialDataGUI()
    gui.show()
    sys.exit(app.exec_())
