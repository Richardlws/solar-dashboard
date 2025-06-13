import re
from datetime import datetime

def extract_bytes_from_text_frame(frame_lines):
    hex_bytes = []
    for line in frame_lines:
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        hex_part = parts[1].strip().split()
        hex_bytes.extend(hex_part)
    return hex_bytes

def parse_modbus_data(file_path):
    try:
        with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return []

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
            dt = datetime.strptime(timestamp.split('.')[0], "%Y-%m-%d %H:%M:%S")
            results.append((dt, daily_energy, total_energy, total_power))
        except:
            continue

    return results
