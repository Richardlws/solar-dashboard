# -*- coding: utf-8 -*-
import re
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QFileDialog, QMessageBox
import sys
import os

# 屏蔽部分无关的系统日志（可选）
sys.stderr = open(os.devnull, 'w')

# 工具函数：从帧中提取连续字节序列
def extract_bytes_from_text_frame(frame_lines):
    hex_bytes = []
    for line in frame_lines:
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        hex_part = parts[1].strip().split()
        hex_bytes.extend(hex_part)
    return hex_bytes

# 主处理逻辑
def parse_modbus_data(file_path):
    try:
        with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        QMessageBox.critical(None, "文件错误", f"无法读取文件: {e}")
        return pd.DataFrame()

    grouped_frames = []
    current_frame = []
    current_timestamp = ""
    collecting = False

    for line in lines:
        line = line.strip()

        if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line):
            current_timestamp = re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line).group(0)

        if "01 04 46" in line:
            if collecting and current_frame:
                grouped_frames.append((current_timestamp, current_frame))
                current_frame = []
            collecting = True
            current_frame = [line]
        elif collecting and re.match(r"^\d{4}:", line):
            current_frame.append(line)
        elif collecting and line == "":
            if current_frame:
                grouped_frames.append((current_timestamp, current_frame))
                current_frame = []
            collecting = False

    if collecting and current_frame:
        grouped_frames.append((current_timestamp, current_frame))

    results = []
    for timestamp, frame_lines in grouped_frames:
        byte_list = extract_bytes_from_text_frame(frame_lines)
        if len(byte_list) < 75:
            continue
        try:
            daily_energy = int(byte_list[3] + byte_list[4], 16) * 0.1
            total_energy = int(byte_list[7] + byte_list[8] + byte_list[5] + byte_list[6], 16)
            total_power = int(byte_list[61] + byte_list[62] + byte_list[59] + byte_list[60], 16)
            if total_power >= 0x80000000:
                total_power -= 0x100000000
            total_power *= 0.001
            timestamp = timestamp.split('.')[0] if timestamp else ""
            results.append((timestamp, daily_energy, total_energy, total_power))
        except:
            continue

    df = pd.DataFrame(results, columns=["时间", "日发电量_kWh", "总发电量_kWh", "总有功功率_kW"])
    return df

# PyQt5 图形界面类
class ModbusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modbus 电量分析工具 (PyQt5)")
        self.resize(800, 600)

        self.text_edit = QTextEdit(self)
        self.btn_load = QPushButton("选择数据文件", self)
        self.btn_load.clicked.connect(self.load_file)

        layout = QVBoxLayout()
        layout.addWidget(self.btn_load)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "Text Files (*.txt)")
        if not file_path:
            return

        df = parse_modbus_data(file_path)
        if df.empty:
            self.text_edit.setPlainText("未能解析出任何有效数据。")
            return

        last_row = df.iloc[-1]
        max_power_row = df.loc[df["总有功功率_kW"].idxmax()]

        output = "最后一帧数据：\n"
        output += f"时间: {last_row['时间']}\n日发电量: {last_row['日发电量_kWh']} kWh\n总发电量: {last_row['总发电量_kWh']} kWh\n总有功功率: {last_row['总有功功率_kW']} kW\n\n"

        output += "最大功率帧：\n"
        output += f"时间: {max_power_row['时间']}\n日发电量: {max_power_row['日发电量_kWh']} kWh\n总发电量: {max_power_row['总发电量_kWh']} kWh\n总有功功率: {max_power_row['总有功功率_kW']} kW"

        self.text_edit.setPlainText(output)

# 主程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModbusApp()
    window.show()
    sys.exit(app.exec_())
