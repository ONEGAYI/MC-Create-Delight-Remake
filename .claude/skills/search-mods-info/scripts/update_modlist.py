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

    # 需要更新的模组信息
    mod_updates = {
        261: ("双端类", "#装备与战斗", "机械动力附加模组，提供蒸汽朋克风格装甲"),
        262: ("双端类", "#库与依赖", "Fuzs模组的核心库，提供模组加载器抽象层"),
        263: ("双端类", "#食物与农业", "为食物添加品质系统，提升营养和饱和度"),
        264: ("双端类", "#辅助工具", "模块化模组，添加大量小型原版风格功能"),
        265: ("双端类", "#装饰与建筑", "Quark的附属模组，添加背包、管道等特殊功能"),
        266: ("双端类", "#辅助工具", "FTB任务系统的扩展，添加新任务类型和奖励"),
        267: ("双端类", "#界面增强", "Curios/Trinkets API与动态光源模组的兼容桥"),
        268: ("双端类", "#性能优化", "Lithium模组的Forge非官方分支，优化游戏性能"),
        269: ("双端类", "#装饰与建筑", "MrCrayfish家具模组的重制版，添加新家具"),
        270: ("客户端", "#库与依赖", "KubeJS的渲染支持库，用于绘制HUD和物品渲染"),
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