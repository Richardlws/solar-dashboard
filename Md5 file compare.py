import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import hashlib
import os
from collections import defaultdict

def get_file_md5(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def handle_drop(event):
    raw_files = event.data.strip().split()
    files = [f.strip('{}') for f in raw_files if os.path.isfile(f.strip('{}'))]
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
            result_text.insert(tk.END, f"❌ 读取失败: {file}，原因：{e}\n\n")

    result_text.insert(tk.END, "\n🔍 内容相同的文件组：\n")
    for md5, file_list in md5_map.items():
        if len(file_list) > 1:
            result_text.insert(tk.END, f"\n⚠️ MD5: {md5}\n")
            for f in file_list:
                result_text.insert(tk.END, f"   - {f}\n")

# 创建拖曳窗口
root = TkinterDnD.Tk()
root.title("拖拽文件比较 MD5 - 微信文件去重工具")
root.geometry("700x500")

label = tk.Label(root, text="请将文件拖入此窗口进行 MD5 比较", font=("Arial", 14), fg="gray")
label.pack(pady=10)

result_text = tk.Text(root, wrap=tk.WORD, font=("Consolas", 10))
result_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# 设置拖拽监听
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', handle_drop)

root.mainloop()
