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

def save_missing_to_csv(missing_items, output_path):
    """保存缺失项到 CSV 格式（updated_at 由 batch_update_manager.py 自动生成）"""
    with open(output_path, 'a', encoding='utf-8') as f:
        # 写入数据（sha, filename, env, tags, description）
        for item in missing_items:
            f.write(f"{item['sha']},{item['filename']},,,\n")

def main():
    # 初始化数据库管理器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    db_path = os.path.join(project_root, 'docs', 'mods_metadata.db')
    folder_path = os.path.join(project_root, 'mods')
    manager = mods_manager.AssetManager(db_path, folder_path)

    # 检查的字段
    field = 'description'

    # 输出文件路径
    csv_output = os.path.join(os.path.dirname(__file__), '..', 'configs', 'updated_info.csv')

    # 获取缺失项
    print(f"检查缺失 '{field}' 字段的项...")
    missing_items = get_missing_items(manager, field)

    if not missing_items:
        print(f"✨ 所有文件的 '{field}' 字段都已填写完整！")
        # 创建空 CSV 文件（只包含表头）
        # with open(csv_output, 'w', encoding='utf-8') as f:
        #     f.write("sha,name,env,tags,description\n")
        # print(f"已创建空文件: {csv_output}")
        return

    print(f"\n🟠 共有 {len(missing_items)} 个文件缺失 '{field}' 字段:")
    for item in missing_items:
        print(f"   [SHA: {item['sha'][:8]}] {item['filename']}")

    # 保存为 CSV 格式
    save_missing_to_csv(missing_items, csv_output)

    print(f"\n结果已保存到: {csv_output} ({len(missing_items)} 项)")

if __name__ == '__main__':
    main()