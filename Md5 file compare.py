import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import hashlib
import os
from collections import defaultdict

def get_file_md5(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def select_files():
    files = filedialog.askopenfilenames(title="选择要比较的文件")
    if files:
        compare_files(files)

def compare_files(files):
    result_text.delete(1.0, tk.END)
    md5_map = defaultdict(list)

    for file in files:
        try:
            md5 = get_file_md5(file)
            md5_map[md5].append(file)
            result_text.insert(tk.END, f"✅ {os.path.basename(file)}\n    MD5: {md5}\n\n")
        except Exception as e:
            result_text.insert(tk.END, f"❌ 无法读取 {file}，原因：{e}\n\n")

    result_text.insert(tk.END, "\n🔍 内容相同的文件组：\n")
    for md5, file_list in md5_map.items():
        if len(file_list) > 1:
            result_text.insert(tk.END, f"\n⚠️ MD5: {md5}\n")
            for f in file_list:
                result_text.insert(tk.END, f"   - {f}\n")

# 创建窗口
root = tk.Tk()
root.title("微信文件内容去重 - MD5对比工具")
root.geometry("700x500")

frame = tk.Frame(root)
frame.pack(pady=10)

select_btn = tk.Button(frame, text="选择文件进行比较", command=select_files, font=("Arial", 12))
select_btn.pack()

result_text = scrolledtext.ScrolledText(root, width=80, height=25, font=("Consolas", 10))
result_text.pack(padx=10, pady=10)

root.mainloop()
