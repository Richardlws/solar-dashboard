# 新版 /get_hourly_summary 接口：不依赖旧函数，直接逐条分析 port1 和 port2 文本
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import re
import os
from app import DATA_DIR

app = Flask(__name__)


@app.route('/get_hourly_summary')
def get_hourly_summary():
    start_str = request.args.get('start_time')
    end_str = request.args.get('end_time')
    print("start_time =", start_str)
    print("end_time =", end_str)

    if not start_str or not end_str:
        return jsonify({'error': '缺少 start 或 end 参数'}), 400

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
        if start_dt > end_dt:
            return jsonify({'error': '起始时间不能晚于结束时间'}), 400
    except ValueError:
        return jsonify({'error': '时间格式应为 YYYY-MM-DD HH:MM'}), 400

    def parse_port1(file_path):
        total_kw = 0
        timestamps = []
        with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
            lines = f.readlines()

        current_time = None
        # sample_debug = []
        # b3_debug = []
        for i, line in enumerate(lines):
            if '接收' in line and re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line):
                time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                current_time = datetime.strptime(time_match.group(1), "%Y-%m-%d %H:%M:%S.%f")
            elif '0000:' in line and current_time:
                if start_dt <= current_time <= end_dt:
                    hex_str = line.strip().split('0000:')[-1].strip().replace(' ', '')
                    if '33333635' in hex_str:
                        idx = hex_str.find('33333635')
                        raw_data = hex_str[idx + 8:idx + 14]
                        if len(raw_data) == 6:
                            try:
                                if raw_data[4:6].upper() == 'B3':
                                    # if len(b3_debug) < 3:
                                    #    b3_debug.append(current_time.strftime('%H:%M:%S.%f'))
                                    continue
                                a, b, c = raw_data[0:2], raw_data[2:4], raw_data[4:6]

                                def decode_byte(byte_hex):
                                    high = int(byte_hex[0], 16) - 3
                                    low = int(byte_hex[1], 16) - 3
                                    return int(f"{high}{low}")

                                v1 = decode_byte(c)
                                v2 = decode_byte(b)
                                v3 = decode_byte(a)
                                val = int(f"{v1:02d}{v2:02d}{v3:02d}") / 10000 * 30
                                # if len(sample_debug) < 3:
                                #    sample_debug.append({'time': current_time.strftime('%H:%M:%S.%f'), 'val': val})
                                total_kw += val
                                timestamps.append(current_time)
                            except:
                                continue

        if len(timestamps) >= 2:
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            interval = duration / (len(timestamps) - 1)
            # print(duration)
            # print(interval)
        else:
            interval = 0.5

        # print(f"📋 Port1 前三条样本: {sample_debug}")
        # print(f"🟦 B3 开头帧前3个时间点: {b3_debug}")
        return round(total_kw * interval / 3600, 1)

    def parse_port2(file_path):
        total_kwh = 0
        timestamps = []
        power_values = []

        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                lines = f.readlines()
        except:
            return 0

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

        def extract_bytes_from_text_frame(frame_lines):
            hex_bytes = []
            for line in frame_lines:
                parts = line.split(":", 1)
                if len(parts) != 2:
                    continue
                hex_part = parts[1].strip().split()
                hex_bytes.extend(hex_part)
            return hex_bytes

        for timestamp, frame_lines in grouped_frames:
            byte_list = extract_bytes_from_text_frame(frame_lines)
            if len(byte_list) < 75:
                continue
            try:
                total_power = int(byte_list[61] + byte_list[62] + byte_list[59] + byte_list[60], 16)
                if total_power >= 0x80000000:
                    total_power -= 0x100000000
                total_power *= 0.001  # W → kW

                ts = datetime.strptime(timestamp.split('.')[0], "%Y-%m-%d %H:%M:%S")
                if start_dt <= ts <= end_dt:
                    power_values.append(total_power)
                    timestamps.append(ts)
            except:
                continue

        if len(timestamps) >= 2:
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            interval = duration / (len(timestamps) - 1)
        else:
            interval = 5  # 默认间隔

        for val in power_values:
            total_kwh += val * interval / 3600

        return round(total_kwh, 2)

    date_strs = set()
    current = start_dt
    while current <= end_dt:
        date_strs.add(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    total_kwh = 0.0
    total_solar = 0.0

    for date in date_strs:
        base = f"[192.168.1.254] {date}"
        port1_path = os.path.join(DATA_DIR, base + "-port1.txt")
        port2_path = os.path.join(DATA_DIR, base + "-port2.txt")

        if os.path.exists(port1_path):
            total_kwh += parse_port1(port1_path)
        if os.path.exists(port2_path):
            total_solar += parse_port2(port2_path)

    return jsonify({
        'total_kwh': round(total_kwh, 1),
        'total_solar': round(total_solar, 1)
    })


if __name__ == '__main__':
    # 手动测试用例
    from types import SimpleNamespace

    with app.test_request_context('/get_hourly_summary?start_time=2025-06-11 00:00&end_time=2025-06-11 23:59'):
        print(get_hourly_summary().get_json())
