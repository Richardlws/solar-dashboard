import os
import hashlib
import stat
from collections import defaultdict

def get_file_md5(filepath):
    """计算文件的MD5值"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def delete_duplicate_files(base_dir):
    print(f"扫描路径: {base_dir}")
    md5_map = defaultdict(list)

    # 遍历所有文件
    for root, _, files in os.walk(base_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                file_md5 = get_file_md5(file_path)
                md5_map[file_md5].append(file_path)
            except Exception as e:
                print(f"读取失败：{file_path}，原因：{e}")

    # 删除重复文件
    deleted_count = 0
    for file_list in md5_map.values():
        if len(file_list) > 1:
            # 保留第一个，其余删除
            for duplicate_file in file_list[1:]:
                try:
                    if not os.access(duplicate_file, os.W_OK):
                        os.chmod(duplicate_file, stat.S_IWRITE)  # 取消只读
                    os.remove(duplicate_file)
                    print(f"删除重复文件：{duplicate_file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除失败：{duplicate_file}，原因：{e}")

    print(f"\n✅ 清理完成，共删除 {deleted_count} 个重复文件。")

# 示例：替换成你实际的PC微信文件路径
wechat_download_folder = r"C:\Users\LENOVO\Documents\WeChat Files\wxid_th3x9nq7tlmy11\FileStorage\File"
delete_duplicate_files(wechat_download_folder)
