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

def get_missing_items(manager, field):
    """获取缺失指定字段的项"""
    # 直接查询数据库，获取缺失项
    sql = f"SELECT sha, filename FROM files WHERE {field} IS NULL OR {field} = ''"
    cursor = manager.conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()

    missing_items = []
    for row in rows:
        missing_items.append({
            'sha': row['sha'],
            'filename': row['filename']
        })

    return missing_items

def save_missing_sha(missing_items, output_path):
    """保存缺失项的 SHA"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in missing_items:
            f.write(f"{item['sha']}\n")

def save_missing_names(missing_items, output_path):
    """保存缺失项的文件名"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in missing_items:
            f.write(f"{item['filename']}\n")

def main():
    # 初始化数据库管理器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    db_path = os.path.join(project_root, 'docs', 'mods_metadata.db')
    folder_path = os.path.join(project_root, 'mods')
    manager = mods_manager.AssetManager(db_path, folder_path)

    # 检查的字段
    field = 'number'

    # 输出文件路径
    sha_output = os.path.join(os.path.dirname(__file__), '..', 'configs', 'updated_missing_sha.txt')
    names_output = os.path.join(os.path.dirname(__file__), '..', 'configs', 'updated_missing_names.txt')

    # 获取缺失项
    print(f"检查缺失 '{field}' 字段的项...")
    missing_items = get_missing_items(manager, field)

    if not missing_items:
        print(f"✨ 所有文件的 '{field}' 字段都已填写完整！")
        # 创建空文件
        with open(sha_output, 'w', encoding='utf-8') as f:
            pass
        with open(names_output, 'w', encoding='utf-8') as f:
            pass
        print(f"已创建空文件: {sha_output}")
        print(f"已创建空文件: {names_output}")
        return

    print(f"\n🟠 共有 {len(missing_items)} 个文件缺失 '{field}' 字段:")
    for item in missing_items:
        print(f"   [SHA: {item['sha'][:8]}] {item['filename']}")

    # 分别保存 SHA 和文件名
    save_missing_sha(missing_items, sha_output)
    save_missing_names(missing_items, names_output)

    print(f"\n结果已保存:")
    print(f"  SHA 文件: {sha_output} ({len(missing_items)} 项)")
    print(f"  文件名文件: {names_output} ({len(missing_items)} 项)")

if __name__ == '__main__':
    main()