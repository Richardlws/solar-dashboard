import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
from Serial_Data_Processor import extract_and_calculate
from modbus_parser import parse_modbus_data  # 已从 modbus_gui 中拆出

app = Flask(__name__)

DATA_DIR = r'C:\csgatewaynew20241104\log'
PLOT_DIR = 'static/plots'
os.makedirs(PLOT_DIR, exist_ok=True)

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

    output_lines = []

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

    plot_url = ''
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

    return jsonify({
        'text': '\n'.join(output_lines),
        'plot_url': plot_url
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
