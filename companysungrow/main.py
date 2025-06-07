import re
import os


def extract_and_calculate(filepath):
    # 读取文本内容（默认按 gbk 编码）
    with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
        text = f.read()

    # 提取“接收”段十六进制内容
    recv_blocks = re.findall(r'接收.*?\n(.*?)\n(.*?)\n', text, re.DOTALL)
    hex_segments = []
    for line1, line2 in recv_blocks:
        hex_str = (line1 + ' ' + line2).strip()
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

    # 分为 80 开头和非 80 开头两类
    starts_80 = [r for r in swapped_segments if r[0] == 0x80]
    not_80 = [r for r in swapped_segments if r[0] != 0x80]

    # 处理非 80 开头
    normal_values = [int(''.join(f"{b:02X}" for b in r)) for r in not_80]
    normal_total = sum(normal_values)
    # 使用全部记录数量估算真实采样时间
    real_sampling_time = (3600 * 24)/len(swapped_segments)
    normal_kw = normal_total / 10000 * 30
    normal_kwh = normal_kw * real_sampling_time / 3600

    # 处理 80 开头（去掉首字节再拼接）
    special_values = [int(''.join(f"{b:02X}" for b in r[1:])) for r in starts_80]
    special_sum = sum(special_values)
    special_kw = special_sum / 10000 * 30
    special_kwh = special_kw * real_sampling_time / 3600

    # 返回结果
    return {
        'records_normal': len(not_80),
        'records_80': len(starts_80),
        'total_normal': normal_total,
        'total_kwh': round(normal_kwh, 3),
        'special_sum': special_sum,
        'special_kwh': round(special_kwh, 3),
        'real_sampling_time': round(real_sampling_time, 3),
       'swapped_seggments':len(swapped_segments)
    }


# 用法示例：
result = extract_and_calculate("D:\\1.txt")
print(result)
