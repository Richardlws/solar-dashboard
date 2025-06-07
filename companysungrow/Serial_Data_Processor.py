import re
import os
from datetime import datetime


def extract_and_calculate(filepath):
    # 读取文本内容（默认按 gbk 编码）
    with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
        lines = f.readlines()

    # 提取全部时间戳（以“接收”开头的行）
    recv_time_format = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}).*?接收'
    timestamps = [re.match(recv_time_format, line).group(1) for line in lines if re.match(recv_time_format, line)]

    # 计算真实采样时间（秒）
    if len(timestamps) >= 2:
        start_time = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S.%f")
        end_time = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S.%f")
        real_sampling_time = (end_time - start_time).total_seconds()
    else:
        real_sampling_time = 0

    # 提取“接收”段十六进制数据块
    recv_blocks = []
    i = 0
    while i < len(lines) - 2:
        if re.match(recv_time_format, lines[i]):
            recv_blocks.append((lines[i + 1], lines[i + 2]))
            i += 3
        else:
            i += 1

    hex_segments = []
    for line1, line2 in recv_blocks:
        hex_str = (line1.strip() + ' ' + line2.strip()).strip()
        hex_str = re.sub(r'[^\dA-Fa-f ]', '', hex_str)
        hex_bytes = hex_str.split()
        for i in range(len(hex_bytes) - 6):
            if hex_bytes[i:i + 4] == ['33', '33', '36', '35']:
                segment = hex_bytes[i + 4:i + 7]
                if len(segment) == 3:
                    hex_segments.append(segment)

    # 减去 0x33 并首尾互换
    swapped_segments = []
    for row in hex_segments:
        try:
            decoded = [(int(b, 16) - 0x33) & 0xFF for b in row]
            decoded[0], decoded[2] = decoded[2], decoded[0]
            swapped_segments.append(decoded)
        except:
            continue

    # 计算采样点间隔时间（秒）
    sampling_interval = real_sampling_time / len(swapped_segments) if swapped_segments else 0

    # 分为 80 开头和非 80 开头两类
    starts_80 = [r for r in swapped_segments if r[0] == 0x80]
    not_80 = [r for r in swapped_segments if r[0] != 0x80]

    # 处理非 80 开头
    normal_values = [int(''.join(f"{b:02X}" for b in r)) for r in not_80]
    normal_total = sum(normal_values)
    normal_kw = normal_total / 10000 * 30
    normal_kwh = normal_kw * sampling_interval / 3600

    # 处理 80 开头（去掉首字节再拼接）
    special_values = [int(''.join(f"{b:02X}" for b in r[1:])) for r in starts_80]
    special_sum = sum(special_values)
    special_kw = special_sum / 10000 * 30
    special_kwh = special_kw * sampling_interval / 3600

    # 计算采样点间隔时间（秒）
    sampling_interval = real_sampling_time / len(swapped_segments) if swapped_segments else 0

    # 返回结果
    return {
        'records_normal': len(not_80),
        'records_80': len(starts_80),
        'total_normal': normal_total,
        'total_kwh': round(normal_kwh, 3),
        'special_sum': special_sum,
        'special_kwh': round(special_kwh, 3),
        'real_sampling_time_seconds': round(real_sampling_time, 1),
        'sampling_interval_seconds': round(sampling_interval, 3),
        'swapped_segments': len(swapped_segments),
        'start time': start_time,
        'end time': end_time
    }


# 用法示例：
result = extract_and_calculate("D:\\2.txt")
print(result)
