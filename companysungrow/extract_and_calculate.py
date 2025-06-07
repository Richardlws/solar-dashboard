import sys
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
from Serial_Data_Processor import extract_and_calculate


class SerialDataGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("光伏发电数据解析器")
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
                key_map = {
                    'start time': '开始时间',
                    'end time': '结束时间',
                    'total_kwh': '电网用电',
                    'special_kwh': '电网返送'

                }
                unit_map = {
                    'start time': '',
                    'end time': '',
                    'total_kwh': 'kWh',
                    'special_kwh': 'kWh'

                }
                for key in ['start time', 'end time','total_kwh', 'special_kwh']:
                    label = key_map.get(key, key)
                    value = result.get(key, '')
                    # 正确格式化时间为“到秒”
                    if isinstance(value, datetime.datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    unit = unit_map.get(key, '')
                    output += f"{label}: {value} {unit}\n"

                self.result_box.setText(output)

            except Exception as e:
                self.result_box.setText(f"处理出错: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = SerialDataGUI()
    gui.show()
    sys.exit(app.exec_())
