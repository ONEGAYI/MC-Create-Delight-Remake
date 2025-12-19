#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模组信息转移脚本（安全版本）
将mods-list copy.md中已建档的模组信息（环境、标签、描述）转移到mods-list.md中
根据模组名称进行匹配，保持原有编号和名称完全不变
"""

import re
import sys
from pathlib import Path


def extract_core_name(mod_name):
    """
    提取模组的核心名称，移除版本号等后缀

    Args:
        mod_name: 原始模组名称

    Returns:
        模组的核心名称
    """
    # 移除.jar扩展名
    if mod_name.endswith('.jar'):
        mod_name = mod_name[:-4]

    # 移除常见的版本号模式和后缀
    patterns = [
        r'-\d+\.\d+(\.\d+)?[-\d\w.]*',  # -1.20.1-xxx
        r'_\d+\.\d+(\.\d+)?[-\d\w.]*',  # _1.20.1_xxx
        r'-forge-\d+\.\d+',             # -forge-1.20.1
        r'-neoforge-\d+\.\d+',          # -neoforge-1.20.1
        r'-mc\d+\.\d+',                 # -mc1.20.1
        r'-\d+\.+\d+-for(?:ge)?',      # -1.20.1-forge
        r'-Forge-.*',                   # -Forge-xxx
        r'-for(?:ge)?$',                # -forge 或 -for 结尾
        r'_for(?:ge)?$',                # _forge 或 _for 结尾
    ]

    core_name = mod_name
    for pattern in patterns:
        core_name = re.sub(pattern, '', core_name)

    return core_name.lower()


def parse_mod_table(content):
    """
    解析markdown文件中的模组表格

    Args:
        content: markdown文件内容

    Returns:
        (模组信息字典, 核心名称映射字典)
    """
    mods = {}
    core_name_map = {}  # 核心名称到模组信息的映射
    lines = content.split('\n')

    # 查找表格开始和结束
    in_table = False
    table_started = False

    for line in lines:
        # 检查表格开始
        if '<mod-table>' in line:
            table_started = True
            continue

        # 检查表格结束
        if '</mod-table>' in line:
            break

        # 跳过表头和分隔符
        if not table_started:
            continue

        if '编号 | 名称 | 环境 | 标签 | 描述' in line or '编号|名称|环境|标签|描述' in line:
            in_table = True
            continue

        if ':---' in line:
            continue

        # 解析表格行
        if in_table and line.strip():
            # 匹配表格行格式: 编号|名称|环境|标签|描述
            match = re.match(r'^\s*(\d+)\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*(.*)$', line)
            if match:
                number = int(match.group(1))
                name = match.group(2).strip()
                env = match.group(3).strip()
                tags = match.group(4).strip()
                desc = match.group(5).strip()

                # 如果模组名称不为空，则记录
                if name:
                    mod_info = {
                        'number': number,
                        'name': name,
                        'env': env,
                        'tags': tags,
                        'desc': desc
                    }
                    mods[name] = mod_info

                    # 同时创建核心名称映射
                    core_name = extract_core_name(name)
                    if core_name not in core_name_map:
                        core_name_map[core_name] = []
                    core_name_map[core_name].append(mod_info)

    return mods, core_name_map


def read_file_content(file_path):
    """
    读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        文件内容字符串，如果失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"错误: 无法读取文件 {file_path} - {e}")
        return None


def write_file_content(file_path, content):
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        成功返回True，失败返回False
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"错误: 无法写入文件 {file_path} - {e}")
        return False


def transfer_mod_info(source_file, target_file, dry_run=False):
    """
    转移模组信息，支持基于核心名称的模糊匹配
    只修改环境、标签、描述，绝不修改模组名称和编号

    Args:
        source_file: 源文件路径（mods-list copy.md）
        target_file: 目标文件路径（mods-list.md）
        dry_run: 是否为试运行模式

    Returns:
        成功转移的模组数量
    """
    # 读取两个文件
    source_content = read_file_content(source_file)
    target_content = read_file_content(target_file)

    if not source_content or not target_content:
        return 0

    # 解析两个文件的模组表格，获取核心名称映射
    source_mods, source_core_map = parse_mod_table(source_content)

    print(f"源文件中的模组数量: {len(source_mods)}")
    print(f"目标文件中的模组数量: {target_content.count('|') - 3}")  # 简单统计

    # 统计匹配情况
    matched_count = 0
    transferred_count = 0
    fuzzy_matched_count = 0

    # 创建目标文件的新内容
    lines = target_content.split('\n')
    new_lines = []

    # 查找表格区域
    in_table = False
    table_started = False

    for line in lines:
        # 检查表格开始
        if '<mod-table>' in line:
            table_started = True
            new_lines.append(line)
            continue

        # 检查表格结束
        if '</mod-table>' in line:
            in_table = False
            new_lines.append(line)
            continue

        # 跳过表头和分隔符
        if not table_started:
            new_lines.append(line)
            continue

        if '编号 | 名称 | 环境 | 标签 | 描述' in line or '编号|名称|环境|标签|描述' in line:
            in_table = True
            new_lines.append(line)
            continue

        if ':---' in line:
            new_lines.append(line)
            continue

        # 处理表格行
        if in_table and line.strip():
            # 匹配表格行格式
            match = re.match(r'^\s*(\d+)\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*(.*)$', line)
            if match:
                number = int(match.group(1))
                name = match.group(2).strip()  # 保持原有名称不变
                env = match.group(3).strip()
                tags = match.group(4).strip()
                desc = match.group(5).strip()

                source_info = None
                match_type = "未知"

                # 1. 首先尝试精确匹配
                if name in source_mods:
                    source_info = source_mods[name]
                    match_type = "精确匹配"
                    matched_count += 1
                else:
                    # 2. 如果精确匹配失败，尝试核心名称模糊匹配
                    target_core = extract_core_name(name)
                    if target_core in source_core_map:
                        # 在源文件中找到相同核心名称的模组
                        source_candidates = source_core_map[target_core]
                        if source_candidates:
                            source_info = source_candidates[0]  # 取第一个匹配项
                            match_type = f"模糊匹配({target_core})"
                            fuzzy_matched_count += 1

                if source_info:
                    # 只有当源文件有信息且目标文件没有信息时才转移
                    if (source_info['env'] or source_info['tags'] or source_info['desc']) and not (env or tags or desc):
                        # 使用源文件的信息，但保持目标文件的名称不变
                        new_env = source_info['env']
                        new_tags = source_info['tags']
                        new_desc = source_info['desc']
                        transferred_count += 1

                        # 创建新的表格行 - 保持原有名称和编号
                        new_line = f"{number}| {name} | {new_env} | {new_tags} | {new_desc}"
                        new_lines.append(new_line)

                        if not dry_run:
                            print(f"  ✓ 转移: {name} ({match_type})")
                        else:
                            print(f"  • 将转移: {name} ({match_type})")
                    else:
                        # 保持原样
                        new_lines.append(line)
                        if source_info['env'] or source_info['tags'] or source_info['desc']:
                            if env or tags or desc:
                                print(f"  - 跳过: {name} ({match_type}, 目标已有信息)")
                            else:
                                print(f"  - 跳过: {name} ({match_type}, 源无信息)")
                else:
                    # 在源文件中未找到匹配
                    new_lines.append(line)
                    if not dry_run:
                        print(f"  ? 未找到: {name}")
                    else:
                        print(f"  • 将保持: {name} (源文件中未找到)")
            else:
                # 不匹配表格行格式，保持原样
                new_lines.append(line)
        else:
            # 非表格行，保持原样
            new_lines.append(line)

    # 写入更新后的内容
    if not dry_run and transferred_count > 0:
        new_content = '\n'.join(new_lines)
        if write_file_content(target_file, new_content):
            print(f"\n已成功更新文件: {target_file}")

    # 输出统计信息
    print(f"\n匹配统计:")
    print(f"  精确匹配: {matched_count}")
    print(f"  模糊匹配: {fuzzy_matched_count}")
    print(f"  总转移数: {transferred_count}")

    return transferred_count


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='将mods-list copy.md中的模组信息转移到mods-list.md中（安全版本）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 试运行模式，查看将要进行的操作
  python transfer_mod_info_safe.py --dry-run

  # 执行信息转移
  python transfer_mod_info_safe.py
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，只显示将要进行的操作，不实际修改文件')

    args = parser.parse_args()

    # 获取文件路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    source_file = project_root / 'docs' / 'mods-list copy.md'
    target_file = project_root / 'docs' / 'mods-list.md'

    print(f"===== 模组信息转移工具（安全版本） =====")
    print(f"源文件: {source_file}")
    print(f"目标文件: {target_file}")
    print(f"模式: {'试运行' if args.dry_run else '实际执行'}")
    print(f"注意: 只转移环境、标签、描述信息，保持模组名称和编号完全不变")
    print()

    # 检查文件是否存在
    if not source_file.exists():
        print(f"错误: 源文件不存在 {source_file}")
        return

    if not target_file.exists():
        print(f"错误: 目标文件不存在 {target_file}")
        return

    # 执行转移
    if args.dry_run:
        print("===== 试运行模式 =====")
        print("以下是将要进行的操作:")
        print()

    transferred_count = transfer_mod_info(source_file, target_file, args.dry_run)

    print()
    if args.dry_run:
        print(f"试运行完成! 将转移 {transferred_count} 个模组的信息")
        print("使用不带--dry-run参数的命令来执行实际转移")
    else:
        print(f"转移完成! 成功转移 {transferred_count} 个模组的信息")


if __name__ == '__main__':
    main()