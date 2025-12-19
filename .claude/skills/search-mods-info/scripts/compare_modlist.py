#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模组列表对比脚本
用于比较mods文件夹中的模组与modlist文档的一致性
"""

import re
import sys
import argparse
from pathlib import Path


def clean_mod_name(mod_name):
    """
    清理模组名称，移除版本后缀和.jar扩展名

    Args:
        mod_name: 原始模组文件名

    Returns:
        清理后的模组名称
    """
    # 移除.jar扩展名
    if mod_name.endswith('.jar'):
        mod_name = mod_name[:-4]

    # 移除版本号模式 (如 -1.20.1-1.0.0)
    # 匹配 -版本号 或 _版本号
    patterns = [
        r'-\d+\.\d+(\.\d+)?[-\d\w.]*',  # -1.20.1-1.0.0
        r'_\d+\.\d+(\.\d+)?[-\d\w.]*',  # _1.20.1_1.0.0
        r'-forge-\d+\.\d+',            # -forge-1.20.1
        r'-neoforge-\d+\.\d+',         # -neoforge-1.20.1
        r'-mc\d+\.\d+',                # -mc1.20.1
    ]

    for pattern in patterns:
        mod_name = re.sub(pattern, '', mod_name)

    return mod_name


def get_mods_list(mods_dir):
    """
    获取mods文件夹中所有jar文件（字典序排序）

    Args:
        mods_dir: mods文件夹路径

    Returns:
        排序后的模组文件名列表
    """
    mods_path = Path(mods_dir)
    if not mods_path.exists():
        print(f"错误: 找不到mods文件夹 {mods_dir}")
        return []

    # 获取所有jar文件并排序
    jar_files = list(mods_path.glob('*.jar'))
    jar_files.sort(key=lambda x: x.name.lower())

    return [jar.name for jar in jar_files]


def extract_modlist_from_md(md_file):
    """
    从mods-list.md文件中提取已记录的模组列表

    Args:
        md_file: mods-list.md文件路径

    Returns:
        字典: {位置: 模组名称}
    """
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {md_file}")
        return {}
    except Exception as e:
        print(f"错误: 读取文件时出错 - {e}")
        return {}

    # 查找<mod-table>标签内的内容
    table_pattern = r'<mod-table>(.*?)</mod-table>'
    table_match = re.search(table_pattern, content, re.DOTALL)

    if not table_match:
        print("错误: 未找到<mod-table>标签")
        return {}

    table_content = table_match.group(1)
    lines = table_content.split('\n')

    mod_dict = {}
    position = 1

    for line in lines:
        # 跳过空行
        if not line.strip():
            continue
            
        # [修复] 优化表头过滤逻辑
        # 原逻辑会误删描述中包含"描述"的行 (如 EnchantmentDescriptions)
        if ':---' in line:  # 跳过分割线
            continue
        if line.strip().startswith('编号'):  # 跳过表头
            continue

        # 分割行内容
        parts = line.split('|')

        # 检查是否是有效的表格行（至少有5个部分）
        if len(parts) >= 5:
            # 获取第二列（名称列）
            mod_name = parts[1].strip()
            if mod_name:
                # 清理模组名称（移除可能的编号前缀）
                mod_name = re.sub(r'^\d+\|\s*', '', mod_name)
                mod_dict[position] = mod_name
                position += 1

    return mod_dict

def list_mods(mods_dir, count, start=1):
    """
    列出模组（支持起始位置）

    Args:
        mods_dir: mods文件夹路径
        count: 要列出的模组数量
        start: 起始位置（从1开始）
    """
    mods = get_mods_list(mods_dir)

    if not mods:
        return

    # 调整起始位置和结束位置
    start_index = max(0, start - 1)
    end_index = min(len(mods), start_index + count)
    actual_count = end_index - start_index

    print(f"第 {start} 到 {start + actual_count - 1} 个模组（共 {actual_count} 个）：")
    print("-" * 60)

    for i in range(start_index, end_index):
        position = i + 1
        mod = mods[i]
        clean_name = clean_mod_name(mod)
        print(f"{position:3d}. {mod}")
        print(f"     清理后: {clean_name}")


def compare_mods(mods_dir, md_file, count, start=1):
    """
    比较模组的一致性（支持起始位置）

    Args:
        mods_dir: mods文件夹路径
        md_file: mods-list.md文件路径
        count: 要比较的模组数量
        start: 起始位置（从1开始）
    """
    # 获取模组列表和modlist
    mods = get_mods_list(mods_dir)
    modlist_dict = extract_modlist_from_md(md_file)

    if not mods or not modlist_dict:
        return

    errors = []
    # 调整起始位置和结束位置
    start_index = max(0, start - 1)
    end_index = min(len(mods), start_index + count)
    checked_count = end_index - start_index

    print(f"===== 模组对比报告 =====")
    print(f"检查范围: 第 {start} 到 {start + checked_count - 1} 个（共 {checked_count} 个）")
    print()

    for i in range(start_index, end_index):
        mod_file = mods[i]
        clean_name = clean_mod_name(mod_file)
        position = i + 1  # 位置从1开始

        # 检查1: 模组是否在modlist中存在
        found_in_modlist = False
        for pos, mod_in_list in modlist_dict.items():
            if clean_mod_name(mod_in_list) == clean_name:
                found_in_modlist = True
                # 检查2: 位置是否正确
                if pos != position:
                    errors.append({
                        'type': 'position',
                        'position': position,
                        'mod_file': mod_file,
                        'expected_pos': pos,
                        'message': f"位置不匹配 - 在modlist中位置为 {pos}，期望位置 {position}"
                    })
                break

        if not found_in_modlist:
            errors.append({
                'type': 'missing',
                'position': position,
                'mod_file': mod_file,
                'message': f"模组不在modlist中"
            })

        # 检查3: 期望位置的模组是否匹配
        if position in modlist_dict:
            expected_mod = clean_mod_name(modlist_dict[position])
            if expected_mod != clean_name:
                errors.append({
                    'type': 'name_mismatch',
                    'position': position,
                    'mod_file': mod_file,
                    'expected': expected_mod,
                    'actual': clean_name,
                    'message': f"名称不匹配 - 期望 '{expected_mod}'，实际 '{clean_name}'"
                })

    # 输出结果
    if errors:
        print(f"发现错误: {len(errors)}")
        print()
        print("错误详情:")
        for i, error in enumerate(errors, 1):
            print(f"{i}. 位置 {error['position']}: {error['message']}")
            if 'mod_file' in error:
                print(f"   文件: {error['mod_file']}")
            if error['type'] == 'name_mismatch':
                print(f"   期望: {error['expected']}")
                print(f"   实际: {error['actual']}")
            print()
    else:
        print("✓ 所有模组都匹配！")

    # 如果需要，可以输出详细的对比信息
    print("\n详细对比:")
    print("-" * 60)
    for i in range(start_index, end_index):
        mod_file = mods[i]
        clean_name = clean_mod_name(mod_file)
        position = i + 1

        status = "✓"
        if position in modlist_dict:
            expected = clean_mod_name(modlist_dict[position])
            if expected != clean_name:
                status = "✗"
        else:
            status = "?"

        print(f"{position:3d}. {status} {mod_file}")
        if position in modlist_dict:
            print(f"     modlist: {modlist_dict[position]}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='比较mods文件夹中的模组与modlist文档的一致性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 显示前10个模组
  python compare_modlist.py -n 10

  # 比较前10个模组的一致性
  python compare_modlist.py -c 10

  # 从第51个开始，比较50个模组（即第51-100号）
  python compare_modlist.py -s 51 -c 50

  # 从第51个开始，显示20个模组
  python compare_modlist.py -s 51 -n 20
        """
    )

    parser.add_argument('-n', '--number', type=int,
                       help='显示N个模组名称（从起始位置开始）')
    parser.add_argument('-c', '--compare', type=int,
                       help='比较N个模组的一致性（从起始位置开始）')
    parser.add_argument('-s', '--start', type=int, default=1,
                       help='起始位置（从1开始，默认为1）')

    args = parser.parse_args()

    # 检查参数
    if not args.number and not args.compare:
        parser.error('必须指定 -n 或 -c 参数')
    if args.number and args.compare:
        parser.error('-n 和 -c 参数不能同时使用')

    # 验证起始位置
    if args.start < 1:
        parser.error('起始位置必须大于0')

    # 验证数量参数
    if args.number and args.number < 1:
        parser.error('显示数量必须大于0')
    if args.compare and args.compare < 1:
        parser.error('比较数量必须大于0')

    # 获取路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    mods_dir = project_root / 'mods'
    md_file = project_root / 'docs' / 'mods-list.md'

    # 执行相应操作
    if args.number:
        list_mods(mods_dir, args.number, args.start)
    elif args.compare:
        compare_mods(mods_dir, md_file, args.compare, args.start)


if __name__ == '__main__':
    main()