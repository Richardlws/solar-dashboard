import hashlib
import os
import sys

def get_file_md5(filepath):
    """计算文件的MD5值"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def compare_files(file_list):
    md5_dict = {}
    for file in file_list:
        if not os.path.isfile(file):
            print(f"❌ 文件不存在：{file}")
            continue
        try:
            md5 = get_file_md5(file)
            md5_dict.setdefault(md5, []).append(file)
            print(f"✅ {file} => MD5: {md5}")
        except Exception as e:
            print(f"❌ 无法读取文件：{file}，原因：{e}")

    print("\n🔍 比较结果：")
    for md5, files in md5_dict.items():
        if len(files) > 1:
            print(f"⚠️ 以下文件内容一致（MD5: {md5}）:")
            for f in files:
                print(f"   - {f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python compare_md5.py 文件1 文件2 ...")
    else:
        compare_files(sys.argv[1:])
