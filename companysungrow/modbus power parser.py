# -*- coding: utf-8 -*-
import re
import pandas as pd

# 文本文件路径（自行替换）
file_path = "d:\\2.txt"

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

# 加载所有行
def load_file_lines(path):
    with open(path, 'r', encoding='gbk') as f:
        return f.readlines()

# 主处理逻辑
def parse_modbus_data(file_path):
    lines = load_file_lines(file_path)
    grouped_frames = []
    current_frame = []
    current_timestamp = ""
    collecting = False

    for line in lines:
        line = line.strip()

        # 匹配时间戳格式行
        if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line):
            current_timestamp = re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line).group(0)

        # 开始采集帧
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

    # 最后一帧补上
    if collecting and current_frame:
        grouped_frames.append((current_timestamp, current_frame))

    # 解析每帧
    results = []
    for timestamp, frame_lines in grouped_frames:
        byte_list = extract_bytes_from_text_frame(frame_lines)
        if len(byte_list) < 75:
            continue
        try:
            # 日发电量（5002）
            daily_energy = int(byte_list[3] + byte_list[4], 16) * 0.1
            # 总发电量（5003+5004 CDAB）
            total_energy = int(byte_list[7] + byte_list[8] + byte_list[5] + byte_list[6], 16)
            # 总有功功率（5030+5031 CDAB 有符号）
            total_power = int(byte_list[61] + byte_list[62] + byte_list[59] + byte_list[60], 16)
            if total_power >= 0x80000000:
                total_power -= 0x100000000
            total_power *= 0.001
            # 时间仅保留到秒
            timestamp = timestamp.split('.')[0] if timestamp else ""
            results.append((timestamp, daily_energy, total_energy, total_power))
        except:
            continue

    # 转为DataFrame
    df = pd.DataFrame(results, columns=["时间", "日发电量_kWh", "总发电量_kWh", "总有功功率_kW"])
    return df

# 使用示例
df_result = parse_modbus_data(file_path)
print(df_result.tail(10))

# 获取关键指标
if not df_result.empty:
    last_row = df_result.iloc[-1]
    max_power_row = df_result.loc[df_result["总有功功率_kW"].idxmax()]
    print("\n最后一帧:", last_row.to_dict())
    print("最大功率帧:", max_power_row.to_dict())
