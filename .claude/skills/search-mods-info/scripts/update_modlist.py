#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新模组列表脚本
用于为指定的模组编号填写缺失的信息
"""

import re
import sys
import os

def update_mod_info(file_path, mod_updates):
    """
    更新指定模组的信息

    Args:
        file_path: 文件路径
        mod_updates: 需要更新的模组信息字典 {编号: (环境, 标签, 描述)}
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 逐行处理
        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            # 匹配表格行
            match = re.match(r'^(\d+)\|([^|]+)\|([^|]*)\|([^|]*)\|([^|]*)$', line)
            if match:
                num = int(match.group(1))
                name = match.group(2).strip()

                # 如果这个编号需要更新
                if num in mod_updates:
                    env, tags, desc = mod_updates[num]
                    # 保持原名称，只更新后面的信息
                    updated_line = f"{num}|{name}| {env} | {tags} | {desc}"
                    updated_lines.append(updated_line)
                    print(f"更新 {num}号模组: {name}")
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))

        print(f"成功更新 {len(mod_updates)} 个模组的信息")

    except Exception as e:
        print(f"更新文件时出错: {e}")
        return False

    return True

def main():
    # 文件路径 - 使用绝对路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    file_path = os.path.join(base_dir, 'docs', 'mods-list.md')

    # 需要更新的模组信息 - 72-76号模组（71号create无需更新）
    mod_updates = {
        72: ("双端类", "#装饰与建筑, #辅助工具", "为Create扩展更大容量的存储解决方案"),
        73: ("双端类", "#食物与农业", "为Create添加糖果和甜点制作功能"),
        74: ("双端类", "#食物与农业, #整合与联动[Create & Farmer's Delight]", "Create与农夫乐事的联动核心模组"),
        75: ("双端类", "#工业自动化, #装备与战斗", "为Create添加原子能和高级科技内容"),
        76: ("双端类", "#装备与战斗, #交通与运输", "添加使用Create动力的装备和工具")
    }

    print("准备更新以下模组信息：")
    for num, (env, tags, desc) in mod_updates.items():
        print(f"  {num}号: {env} | {tags} | {desc}")

    print("\n开始更新...")
    success = update_mod_info(file_path, mod_updates)

    if success:
        print("\n更新完成！")
    else:
        print("\n更新失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()