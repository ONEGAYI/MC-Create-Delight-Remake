#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模组列表行号更新脚本
自动为mods-list.md中<mod-table>标签内的表格更新行号
"""

import re
import sys
from pathlib import Path


def update_modlist_numbers(file_path):
    """
    更新模组列表表格的行号

    Args:
        file_path: mods-list.md文件路径
    """
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return False
    except Exception as e:
        print(f"错误: 读取文件时出错 - {e}")
        return False

    # 查找<mod-table>标签内的内容
    table_pattern = r'<mod-table>(.*?)</mod-table>'
    table_match = re.search(table_pattern, content, re.DOTALL)

    if not table_match:
        print("错误: 未找到<mod-table>标签")
        return False

    table_content = table_match.group(1)
    lines = table_content.split('\n')

    # 处理表格行
    updated_lines = []
    current_number = 1
    updated_count = 0  # 记录实际更新的行数

    for line in lines:
        # 跳过空行和表头行
        if not line.strip():
            updated_lines.append(line)
            continue

        # 检查是否是表头行（包含"编号"、"名称"等）
        if any(keyword in line for keyword in ['编号', '名称', '环境', '标签', '描述', ':---']):
            updated_lines.append(line)
            continue

        # 分割行内容
        parts = line.split('|')

        # 检查是否是有效的表格行（至少有5个部分：编号, 名称, 环境, 标签, 描述）
        if len(parts) >= 5:
            # 获取第一列（编号列）
            first_col = parts[0].strip()

            # 检查第一列是否为空、数字或已经是正确的编号
            if not first_col or first_col.isdigit() or (first_col and first_col[0].isdigit()):
                # 更新编号
                parts[0] = str(current_number)
                updated_line = '|'.join(parts)
                updated_lines.append(updated_line)
                current_number += 1
                updated_count += 1  # 记录实际更新的行数
            else:
                # 如果不是有效的表格行，保持原样
                updated_lines.append(line)
        else:
            # 如果不是有效的表格行，保持原样
            updated_lines.append(line)

    # 重新组合表格内容
    updated_table = '\n'.join(updated_lines)

    # 替换原表格内容
    new_content = content.replace(table_content, updated_table)

    # 写回文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"成功更新 {file_path}")
        print(f"总共更新了 {updated_count} 个模组条目")
        return True
    except Exception as e:
        print(f"错误: 写入文件时出错 - {e}")
        return False


def main():
    """主函数"""
    # 获取文件路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    file_path = project_root / 'docs' / 'mods-list.md'

    # 检查文件是否存在
    if not file_path.exists():
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)

    print(f"正在更新文件: {file_path}")

    # 更新行号
    if update_modlist_numbers(file_path):
        print("更新完成！")
    else:
        print("更新失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()