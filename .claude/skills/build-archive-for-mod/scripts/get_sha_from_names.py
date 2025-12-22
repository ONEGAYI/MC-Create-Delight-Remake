#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加路径以便导入 mods_manager
# 当前路径: .claude/skills/search-mods-info/scripts
# 目标路径: scripts/
script_dir = os.path.dirname(os.path.abspath(__file__))
# 向上4级到项目根目录，然后进入 scripts
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
scripts_dir = os.path.join(project_root, 'scripts')
sys.path.insert(0, scripts_dir)

# 导入 mods_manager（不带 .py 扩展名）
import mods_manager

def read_mod_names(filepath):
    """读取模组名称列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        names = [line.strip() for line in f if line.strip()]
    return names

def get_sha_for_mod(manager, mod_name):
    """根据模组名称获取 SHA"""
    # 使用 * 通配符进行模糊搜索
    search_term = f"{mod_name}*"
    results = manager.search_items('filename', search_term)

    if results:
        # 取第一个匹配结果的 SHA
        return results[0]['sha']
    return None

def save_sha_results(sha_pairs, output_path):
    """保存 SHA 结果到文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for mod_name, sha in sha_pairs:
            if sha:
                f.write(f"{sha}\n")
            else:
                f.write(f"NOT_FOUND\n")

def main():
    # 初始化数据库管理器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    db_path = os.path.join(project_root, 'docs', 'mods_metadata.db')
    folder_path = os.path.join(project_root, 'mods')
    manager = mods_manager.AssetManager(db_path, folder_path)

    # 文件路径
    input_file = os.path.join(os.path.dirname(__file__), '..', 'configs', 'updated_names.txt')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'configs', 'updated_SHA.txt')

    # 读取模组名称
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return

    mod_names = read_mod_names(input_file)
    print(f"读取到 {len(mod_names)} 个模组名称")

    if not mod_names:
        print("警告：输入文件为空")
        # 创建空输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            pass
        print(f"已创建空文件 {output_file}")
        return

    # 获取每个模组的 SHA
    sha_pairs = []
    found_count = 0
    for i, name in enumerate(mod_names, 1):
        print(f"处理 {i}/{len(mod_names)}: {name}", end="")
        sha = get_sha_for_mod(manager, name)
        sha_pairs.append((name, sha))
        if sha:
            found_count += 1
            print(f" -> 找到: {sha[:12]}...")
        else:
            print(" -> 未找到")

    # 保存结果
    save_sha_results(sha_pairs, output_file)
    print(f"\n处理完成！")
    print(f"共处理 {len(mod_names)} 个模组，找到 {found_count} 个")
    print(f"结果已保存到 {output_file}")

if __name__ == '__main__':
    main()