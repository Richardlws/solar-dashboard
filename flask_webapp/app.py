import json
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from flask import Flask, request, jsonify, render_template
import os
import re
from datetime import datetime
from Serial_Data_Processor import extract_and_calculate
from modbus_parser import parse_modbus_data  # 已从 modbus_gui 中拆出
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger



app = Flask(__name__)

DATA_DIR = r'C:\csgatewaynew20241104\log'
PLOT_DIR = 'static/plots'
os.makedirs(PLOT_DIR, exist_ok=True)


def get_combined_result_for_date(date_str):
    log_dir = r"C:\csgatewaynew20241104\log"
    port1_file = f"[192.168.1.254] {date_str}-port1.txt"
    port2_file = f"[192.168.1.254] {date_str}-port2.txt"
    path1 = os.path.join(log_dir, port1_file)
    path2 = os.path.join(log_dir, port2_file)

    result_text = ""
    daily_energy = None

    # 处理 port1（电网用电）
    if os.path.exists(path1):
        try:
            data1 = extract_and_calculate(path1)
            result_text += (
                f"📥 电网用电\n"
                f"开始时间：{data1['start time']}\n"
                f"结束时间：{data1['end time']}\n"
                f"总用电量（付费电量）：{data1['total_kwh']} kWh\n"
                f"返送电网电量：{data1['special_kwh']} kWh\n"
            )
            daily_energy = data1['total_kwh']
        except Exception as e:
            result_text += f"[port1] 数据解析失败：{e}\n"
    else:
        result_text += "未找到电网用电数据文件（port1）\n"

    # 处理 port2（太阳能发电）
    if os.path.exists(path2):
        try:
            data2 = parse_modbus_data(path2)
            if data2:
                # 按最大功率值排序，取 max_power 最大的那条记录
                max_power_entry = max(data2, key=lambda x: x[3])  # x[3] 是 max_power
                max_time, day_kwh, total_kwh, max_power = max_power_entry

                latest_entry = max(data2, key=lambda x: x[0])
                latest_time = latest_entry[0]  # 最新数据点时间

                result_text += (
                    f"\n🔆 太阳能发电\n"
                    f"结束时间：{latest_time}\n"
                    f"当日发电量：{day_kwh:.1f} kWh\n"
                    f"装机后总发电量：{total_kwh / 100:.2f} kWh\n"
                    f"当日最大功率：{max_power:.3f} kW\n"
                    f"最大功率时间：{max_time}\n"
                )

        except Exception as e:
            result_text += f"[port2] 数据解析失败：{e}\n"
    else:
        result_text += "未找到太阳能发电数据文件（port2）\n"

    # 写入缓存文件
    result = {
        "text": result_text.strip(),
        "daily_energy": daily_energy,
        "plot_url": "",  # 可选：用于图表数据的 Base64 图像
    }

    os.makedirs("cache", exist_ok=True)
    with open(os.path.join("cache", f"{date_str}.json"), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_data')
def get_data():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'text': '无效日期参数', 'plot_url': ''})

    base = f"[192.168.1.254] {date_str}"
    file1 = os.path.join(DATA_DIR, base + "-port1.txt")
    file2 = os.path.join(DATA_DIR, base + "-port2.txt")

    cache_file = os.path.join('cache', f"{date_str}.json")
    os.makedirs('cache', exist_ok=True)

    # 判断是否可以使用缓存
    def is_cache_valid():
        if not os.path.exists(cache_file):
            return False
        cache_mtime = os.path.getmtime(cache_file)
        file1_mtime = os.path.getmtime(file1) if os.path.exists(file1) else 0
        file2_mtime = os.path.getmtime(file2) if os.path.exists(file2) else 0
        return cache_mtime > max(file1_mtime, file2_mtime)

    today_str = datetime.today().strftime('%Y-%m-%d')

    # ✅ 当天数据不使用缓存
    if date_str != today_str and is_cache_valid():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception as e:
            print(f"读取缓存失败，回退重算：{e}")

    output_lines = []
    plot_url = ''
    daily_energy = None

    # 电网用电（port1）
    if os.path.exists(file1):
        try:
            result = extract_and_calculate(file1)
            output_lines.append("📥 电网用电")
            if 'start time' in result:
                output_lines.append(f"开始时间：{result['start time'].strftime('%Y-%m-%d %H:%M:%S')}")
            if 'end time' in result:
                output_lines.append(f"结束时间：{result['end time'].strftime('%Y-%m-%d %H:%M:%S')}")
            if 'total_kwh' in result:
                output_lines.append(f"总用电量（付费电量）：{result['total_kwh']:.3f} kWh")
            if 'special_kwh' in result:
                output_lines.append(f"返送电网电量：{result['special_kwh']:.3f} kWh")
        except Exception as e:
            output_lines.append(f"电网用电数据解析失败：{e}")
    else:
        output_lines.append("未找到电网用电数据文件")

    # 太阳能发电（port2）
    if os.path.exists(file2):
        try:
            data = parse_modbus_data(file2)
            if data:
                last = data[-1]
                maxrow = max(data, key=lambda x: x[3])
                daily_energy = last[1]

                output_lines.append("\n🔆 太阳能发电")
                output_lines.append(f"结束时间：{last[0]}")
                output_lines.append(f"当日发电量：{daily_energy:.1f} kWh")
                output_lines.append(f"装机后总发电量：{last[2]:.2f} kWh")
                output_lines.append(f"当日最大功率：{maxrow[3]:.3f} kW")
                output_lines.append(f"最大功率时间：{maxrow[0]}")

                # 生成图
                times = [x[0] for x in data]
                powers = [x[3] for x in data]
                plt.figure(figsize=(10, 4))
                plt.plot(times, powers)
                plt.title("太阳能发电功率曲线")
                plt.xlabel("时间")
                plt.ylabel("功率 (kW)")
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
                plt.xticks(rotation=0)
                ymax = max(powers) if powers else 1
                plt.yticks(np.arange(0, int(ymax) + 2, 1))
                plot_path = os.path.join(PLOT_DIR, f"{date_str}.png")
                plt.tight_layout()
                plt.savefig(plot_path)
                plt.close()
                plot_url = '/' + plot_path.replace('\\', '/')
            else:
                output_lines.append("太阳能发电文件无有效数据")
        except Exception as e:
            output_lines.append(f"太阳能发电解析失败：{e}")
    else:
        output_lines.append("未找到太阳能发电数据文件")

    # 返回数据 + 写入缓存
    result_json = {
        'text': '\n'.join(output_lines),
        'plot_url': plot_url,
        'daily_energy': daily_energy
    }
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写入缓存失败：{e}")

    return jsonify(result_json)


@app.route('/get_summary')
def get_summary():
    start_date = request.args.get('start', '').strip()
    end_date = request.args.get('end', '').strip()

    print(f"[get_summary] start={start_date}, end={end_date}")

    # ✅ 如果提供了时间范围参数，就走“区间统计”逻辑
    if start_date and end_date and start_date.lower() != 'null' and end_date.lower() != 'null':
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

            def get_range_dates(start, end):
                return [(start + timedelta(days=i)).strftime('%Y-%m-%d')
                        for i in range((end - start).days + 1)]

            def sum_energy(dates):
                total_kwh = 0
                total_solar = 0
                for date in dates:
                    cache_file = os.path.join('cache', f"{date}.json")
                    if os.path.exists(cache_file):
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                text = data.get("text", "")
                                if "总用电量" in text:
                                    for line in text.splitlines():
                                        if "总用电量" in line:
                                            total_kwh += float(line.split("：")[-1].split()[0])
                                if "当日发电量" in text:
                                    for line in text.splitlines():
                                        if "当日发电量" in line:
                                            total_solar += float(line.split("：")[-1].split()[0])
                        except:
                            pass
                return total_kwh, total_solar

            date_list = get_range_dates(start_dt, end_dt)
            kwh, solar = sum_energy(date_list)
            return jsonify({
                "total_kwh": round(kwh, 2),
                "total_solar": round(solar, 2)
            })

        except Exception as e:
            return jsonify({"error": f"时间范围解析失败: {e}"}), 400


    try:
        today = datetime.today().date()
        today_str = datetime.today().strftime('%Y-%m-%d')
        summary_cache_path = os.path.join('summary_cache', f"{today_str}.json")

        # ✅ 如果缓存已存在，直接返回
        if os.path.exists(summary_cache_path):
            try:
                with open(summary_cache_path, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))
            except Exception as e:
                print(f"[get_summary] 读取缓存失败：{e}")

        # ✅ 缓存不存在时，立即补算“到昨天为止”的数据并缓存
        print("[get_summary] 首次访问，无缓存，正在即时生成...")

        yesterday = today - timedelta(days=1)
        start_of_month = yesterday.replace(day=1)
        start_of_year = yesterday.replace(month=1, day=1)

        def get_range_dates(start, end):
            return [(start + timedelta(days=i)).strftime('%Y-%m-%d')
                    for i in range((end - start).days + 1)]

        def sum_energy(from_date, to_date):
            dates = get_range_dates(from_date, to_date)
            total_kwh = 0
            total_solar = 0
            for date in dates:
                cache_file = os.path.join('cache', f"{date}.json")
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            text = data.get("text", "")
                            if "总用电量" in text:
                                for line in text.splitlines():
                                    if "总用电量" in line:
                                        total_kwh += float(line.split("：")[-1].split()[0])
                            if "当日发电量" in text:
                                for line in text.splitlines():
                                    if "当日发电量" in line:
                                        total_solar += float(line.split("：")[-1].split()[0])
                    except:
                        pass
            return total_kwh, total_solar

        m_kwh, m_solar = sum_energy(start_of_month, yesterday)
        y_kwh, y_solar = sum_energy(start_of_year, yesterday)

        result = {
            "monthly_kwh": round(m_kwh, 2),
            "monthly_solar": round(m_solar, 2),
            "yearly_kwh": round(y_kwh, 2),
            "yearly_solar": round(y_solar, 2),
        }

        os.makedirs("summary_cache", exist_ok=True)
        with open(summary_cache_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        'hourly_kwh': round(total_kwh, 1),
        'hourly_solar': round(total_solar, 1)
    })





def generate_yesterday_cache():
    from datetime import datetime, timedelta
    import json

    date_obj = datetime.today().date() - timedelta(days=1)
    date_str = date_obj.strftime('%Y-%m-%d')
    base = f"[192.168.1.254] {date_str}"
    file1 = os.path.join(DATA_DIR, base + "-port1.txt")
    file2 = os.path.join(DATA_DIR, base + "-port2.txt")
    cache_file = os.path.join('cache', f"{date_str}.json")

    if not os.path.exists(file1) and not os.path.exists(file2):
        print(f"[定时任务] {date_str} 无可用数据文件，跳过缓存生成。")
        return

    print(f"[定时任务] 正在生成 {date_str} 的缓存文件...")

    # 调用与 /get_data 相似的逻辑（只构建输出，不返回）
    output_lines = []
    plot_url = ''
    daily_energy = None

    if os.path.exists(file1):
        try:
            result = extract_and_calculate(file1)
            output_lines.append("📥 电网用电")
            if 'start time' in result:
                output_lines.append(f"开始时间：{result['start time'].strftime('%Y-%m-%d %H:%M:%S')}")
            if 'end time' in result:
                output_lines.append(f"结束时间：{result['end time'].strftime('%Y-%m-%d %H:%M:%S')}")
            if 'total_kwh' in result:
                output_lines.append(f"总用电量（付费电量）：{result['total_kwh']:.3f} kWh")
            if 'special_kwh' in result:
                output_lines.append(f"返送电网电量：{result['special_kwh']:.3f} kWh")
        except Exception as e:
            output_lines.append(f"电网用电数据解析失败：{e}")

    if os.path.exists(file2):
        try:
            data = parse_modbus_data(file2)
            if data:
                last = data[-1]
                maxrow = max(data, key=lambda x: x[3])
                daily_energy = last[1]

                output_lines.append("\n🔆 太阳能发电")
                output_lines.append(f"结束时间：{last[0]}")
                output_lines.append(f"当日发电量：{daily_energy:.1f} kWh")
                output_lines.append(f"装机后总发电量：{last[2]:.2f} kWh")
                output_lines.append(f"当日最大功率：{maxrow[3]:.3f} kW")
                output_lines.append(f"最大功率时间：{maxrow[0]}")

                # 图也生成（但是否展示没关系）
                times = [x[0] for x in data]
                powers = [x[3] for x in data]
                plt.figure(figsize=(10, 4))
                plt.plot(times, powers)
                plt.title("太阳能发电功率曲线")
                plt.xlabel("时间")
                plt.ylabel("功率 (kW)")
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
                plt.xticks(rotation=0)
                ymax = max(powers) if powers else 1
                plt.yticks(np.arange(0, int(ymax) + 2, 1))
                plot_path = os.path.join(PLOT_DIR, f"{date_str}.png")
                plt.tight_layout()
                plt.savefig(plot_path)
                plt.close()
                plot_url = '/' + plot_path.replace('\\', '/')
        except Exception as e:
            output_lines.append(f"太阳能发电解析失败：{e}")

    result_json = {
        'text': '\n'.join(output_lines),
        'plot_url': plot_url,
    }
    if daily_energy is not None:
        result_json['daily_energy'] = daily_energy

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)
        print(f"[定时任务] 缓存文件 {cache_file} 写入成功")
    except Exception as e:
        print(f"[定时任务] 写入缓存失败：{e}")

def generate_yesterday_summary():
    print("[定时任务] 正在生成 summary 汇总缓存...")

    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    start_of_month = yesterday.replace(day=1)
    start_of_year = yesterday.replace(month=1, day=1)

    def get_range_dates(start, end):
        return [(start + timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range((end - start).days + 1)]

    def sum_energy(from_date, to_date):
        dates = get_range_dates(from_date, to_date)
        total_kwh = 0
        total_solar = 0
        for date in dates:
            cache_file = os.path.join('cache', f"{date}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        text = data.get("text", "")
                        if "总用电量" in text:
                            for line in text.splitlines():
                                if "总用电量" in line:
                                    total_kwh += float(line.split("：")[-1].split()[0])
                        if "当日发电量" in text:
                            for line in text.splitlines():
                                if "当日发电量" in line:
                                    total_solar += float(line.split("：")[-1].split()[0])
                    continue
                except:
                    pass
        return total_kwh, total_solar

    m_kwh, m_solar = sum_energy(start_of_month, yesterday)
    y_kwh, y_solar = sum_energy(start_of_year, yesterday)

    result = {
        "monthly_kwh": round(m_kwh, 2),
        "monthly_solar": round(m_solar, 2),
        "yearly_kwh": round(y_kwh, 2),
        "yearly_solar": round(y_solar, 2),
    }

    os.makedirs("summary_cache", exist_ok=True)
    cache_file = os.path.join("summary_cache", f"{today.strftime('%Y-%m-%d')}.json")
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[定时任务] 已生成 summary 汇总缓存：{cache_file}")
    except Exception as e:
        print(f"[定时任务] 写入 summary 缓存失败：{e}")

def generate_all_cache():
    print("[初始化] 正在批量缓存 C:\\csgatewaynew20241104\\log 目录下所有数据文件...")
    log_dir = r"C:\\csgatewaynew20241104\\log"
    files = os.listdir(log_dir)
    date_set = set()

    import re
    for filename in files:
        match = re.match(r"\[192\.168\.1\.254\] (\d{4}-\d{2}-\d{2})-port1\.txt", filename)
        if match:
            date_part = match.group(1)
            date_set.add(date_part)

    for date_str in sorted(date_set):
        try:
            cache_file = os.path.join('cache', f"{date_str}.json")
            if os.path.exists(cache_file):
                print(f"[{date_str}] 缓存已存在，跳过。")
                continue
            print(f"生成缓存：{date_str}")


            base = f"[192.168.1.254] {date_str}"
            file1 = os.path.join(log_dir, base + "-port1.txt")
            file2 = os.path.join(log_dir, base + "-port2.txt")
            cache_file = os.path.join('cache', f"{date_str}.json")

            if not os.path.exists(file1) and not os.path.exists(file2):
                print(f"[{date_str}] 无可用数据文件，跳过缓存生成。")
                continue

            output_lines = []
            plot_url = ''
            daily_energy = None

            if os.path.exists(file1):
                try:
                    result = extract_and_calculate(file1)
                    output_lines.append("📥 电网用电")
                    if 'start time' in result:
                        output_lines.append(f"开始时间：{result['start time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    if 'end time' in result:
                        output_lines.append(f"结束时间：{result['end time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    if 'total_kwh' in result:
                        output_lines.append(f"总用电量（付费电量）：{result['total_kwh']:.3f} kWh")
                    if 'special_kwh' in result:
                        output_lines.append(f"返送电网电量：{result['special_kwh']:.3f} kWh")
                except Exception as e:
                    output_lines.append(f"电网用电数据解析失败：{e}")

            if os.path.exists(file2):
                try:
                    data = parse_modbus_data(file2)
                    if data:
                        last = data[-1]
                        maxrow = max(data, key=lambda x: x[3])
                        daily_energy = last[1]

                        output_lines.append("\n🔆 太阳能发电")
                        output_lines.append(f"结束时间：{last[0]}")
                        output_lines.append(f"当日发电量：{daily_energy:.1f} kWh")
                        output_lines.append(f"装机后总发电量：{last[2]:.2f} kWh")
                        output_lines.append(f"当日最大功率：{maxrow[3]:.3f} kW")
                        output_lines.append(f"最大功率时间：{maxrow[0]}")

                        times = [x[0] for x in data]
                        powers = [x[3] for x in data]
                        plt.figure(figsize=(10, 4))
                        plt.plot(times, powers)
                        plt.title("太阳能发电功率曲线")
                        plt.xlabel("时间")
                        plt.ylabel("功率 (kW)")
                        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
                        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
                        plt.xticks(rotation=0)
                        ymax = max(powers) if powers else 1
                        plt.yticks(np.arange(0, int(ymax) + 2, 1))
                        plot_path = os.path.join('static/plots', f"{date_str}.png")
                        plt.tight_layout()
                        plt.savefig(plot_path)
                        plt.close()
                        plot_url = '/' + plot_path.replace('\\', '/')
                except Exception as e:
                    output_lines.append(f"太阳能发电解析失败：{e}")

            result_json = {
                'text': '\n'.join(output_lines),
                'plot_url': plot_url,
            }
            if daily_energy is not None:
                result_json['daily_energy'] = daily_energy

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)
            print(f"缓存文件 {cache_file} 写入成功")

        except Exception as e:
            print(f"⚠️ 生成 {date_str} 缓存失败：{e}")









scheduler = BackgroundScheduler()
scheduler.add_job(generate_yesterday_cache, CronTrigger(hour=3, minute=0))
scheduler.add_job(generate_yesterday_summary, CronTrigger(hour=2, minute=0))
scheduler.start()


if __name__ == '__main__':
    generate_all_cache()
    #generate_yesterday_summary()
    app.run(debug=True, host='0.0.0.0', port=5000)


