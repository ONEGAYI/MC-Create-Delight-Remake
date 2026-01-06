#!/usr/bin/env python3
"""
从导出的CSV中匹配模组信息到更新列表
"""
import csv
import re
from pathlib import Path

# 文件路径
SCRIPTS_DIR = Path(__file__).parent
SKILL_DIR = SCRIPTS_DIR.parent  # scripts的上级是技能目录
CONFIG_DIR = SKILL_DIR / "configs"
# 使用绝对路径
EXPORTED_CSV = Path(r"D:\games\MC\.minecraft\versions\Create-Delight-Remake\docs\mods_metadata.csv")
UPDATED_CSV = CONFIG_DIR / "updated_info.csv"


def extract_mod_base_name(filename):
    """从文件名提取模组基础名，用于匹配"""
    # 移除 .jar 后缀
    name = filename.replace('.jar', '')

    # 移除版本号模式 (如 1.20.1, 1.20, 0.7.35.93 等)
    # 匹配常见的版本号格式
    patterns = [
        r'-\d+\.\d+.*$',  # -1.20.1-xxx 或 -1.20-xxx
        r'_\d+\.\d+.*$',  # _1.20.1-xxx
        r'-forge$',       # 移除 -forge 后缀
        r'-neoforge$',    # 移除 -neoforge 后缀
        r'-fabric$',      # 移除 -fabric 后缀
    ]

    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    return name.lower()


def load_exported_data():
    """加载导出的CSV数据，建立索引"""
    mod_info = {}

    with open(EXPORTED_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['文件名']
            env = row['环境']
            tags = row['标签']
            description = row['描述']

            # 使用多种键进行索引
            base_name = extract_mod_base_name(filename)

            # 存储完整文件名和基础名的映射
            mod_info[filename.lower()] = (env, tags, description)
            mod_info[base_name] = (env, tags, description)

    return mod_info


def match_and_update():
    """匹配并更新updated_info.csv"""
    # 加载导出的数据
    exported_data = load_exported_data()

    # 读取更新列表
    updated_rows = []
    matched_count = 0
    unmatched = []

    with open(UPDATED_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['filename']
            base_name = extract_mod_base_name(filename)

            # 尝试匹配
            env, tags, description = None, None, None

            # 1. 首先尝试完整文件名匹配
            if filename.lower() in exported_data:
                env, tags, description = exported_data[filename.lower()]
                matched_count += 1
            # 2. 尝试基础名匹配
            elif base_name in exported_data:
                env, tags, description = exported_data[base_name]
                matched_count += 1
            # 3. 尝试更宽松的匹配（移除更多后缀）
            else:
                # 尝试从原文件名提取更短的基础名
                short_base = re.sub(r'-.*$', '', base_name)
                for key in exported_data:
                    if short_base in key.lower() or key in short_base:
                        env, tags, description = exported_data[key]
                        matched_count += 1
                        break

            if env:
                row['env'] = env
                row['tags'] = tags
                row['description'] = description
            else:
                unmatched.append(filename)

            updated_rows.append(row)

    # 写回更新文件
    with open(UPDATED_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['sha', 'filename', 'env', 'tags', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"✅ 匹配完成！")
    print(f"📊 成功匹配: {matched_count} 个模组")
    print(f"❓ 未匹配: {len(unmatched)} 个模组")

    if unmatched:
        print(f"\n未匹配的模组列表:")
        for i, mod in enumerate(unmatched, 1):
            print(f"   {i}. {mod}")


if __name__ == '__main__':
    match_and_update()
