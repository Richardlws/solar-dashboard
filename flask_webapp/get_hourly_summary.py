# 新版 /get_hourly_summary 接口：不依赖旧函数，直接逐条分析 port1 和 port2 文本
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import re
import os
from app import DATA_DIR

app = Flask(__name__)


@app.route('/get_hourly_summary')
def get_hourly_summary():
    start_str = request.args.get('start')
    end_str = request.args.get('end')

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
        sample_debug = []
        b3_debug = []
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
                                if raw_data.startswith('B3'):
                                    if len(b3_debug) < 3:
                                        b3_debug.append(current_time.strftime('%H:%M:%S.%f'))
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
                                if len(sample_debug) < 3:
                                    sample_debug.append({'time': current_time.strftime('%H:%M:%S.%f'), 'val': val})
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

        print(f"📋 Port1 前三条样本: {sample_debug}")
        print(f"🟦 B3 开头帧前3个时间点: {b3_debug}")
        return total_kw * interval / 3600

    def parse_port2(file_path):
        total_kwh = 0
        timestamps = []
        power_values = []

        with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()

        pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)[\s\S]{0,200}?0000:((?:[0-9A-Fa-f]{2} ?)+)')
        for match in pattern.finditer(content):
            ts_str, hex_line = match.groups()
            try:
                ts = datetime.strptime(ts_str.strip(), "%Y-%m-%d %H:%M:%S.%f")
                if not (start_dt <= ts <= end_dt):
                    continue
                hex_str = hex_line.replace(' ', '')
                if hex_str.startswith('010446') and len(hex_str) >= 80:
                    power_hex = hex_str[40:48]
                    power_val = int(power_hex, 16) / 10.0
                    power_values.append(power_val)
                    timestamps.append(ts)
            except:
                continue

        if len(timestamps) >= 2:
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            interval = duration / (len(timestamps) - 1)
        else:
            interval = 5  # 实测默认采样间隔约为 5 秒

        for val in power_values:
            total_kwh += val * interval / 3600

        return round(total_kwh, 3)

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
        'total_kwh': round(total_kwh, 3),
        'total_solar': round(total_solar, 3)
    })


if __name__ == '__main__':
    # 手动测试用例
    from types import SimpleNamespace

    with app.test_request_context('/get_hourly_summary?start=2025-06-17 00:00&end=2025-06-17 23:59'):
        print(get_hourly_summary().get_json())
