#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模组列表自动填充脚本
基于compare_modlist.py的输出信息，自动填充或修正mods-list.md文件
"""

import re
import subprocess
import sys
import json
from pathlib import Path


def get_compare_output(mods_dir, count, start=1):
    """
    获取compare_modlist.py的输出结果

    Args:
        mods_dir: mods文件夹路径
        count: 要比较的模组数量
        start: 起始位置（从1开始）

    Returns:
        compare脚本的标准输出
    """
    script_dir = Path(__file__).parent
    compare_script = script_dir / 'compare_modlist.py'

    cmd = [
        sys.executable,
        str(compare_script),
        '-c', str(count),
        '-s', str(start)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout
    except Exception as e:
        print(f"错误: 运行compare脚本失败 - {e}")
        return ""


def parse_compare_output(output):
    """
    解析compare脚本的输出，提取错误信息

    Args:
        output: compare脚本的标准输出

    Returns:
        错误信息列表
    """
    errors = []
    lines = output.split('\n')

    # 查找"错误详情"部分
    details_started = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line == '错误详情:':
            details_started = True
            i += 1
            continue

        if details_started and line.startswith(('错误详情', '详细对比', '=')):
            # 到达下一个部分，停止解析
            break

        if details_started and line and line[0].isdigit() and '.' in line:
            # 解析错误行，例如: "1. 位置 2: 模组不在modlist中"
            parts = line.split('.', 1)
            if len(parts) >= 2:
                error_part = parts[1].strip()

                # 提取位置信息
                position_match = re.search(r'位置\s*(\d+)', error_part)
                if position_match:
                    position = int(position_match.group(1))

                    # 默认错误类型
                    error_type = 'unknown'
                    mod_file = ''

                    # 检查错误类型
                    if '不在modlist中' in error_part:
                        error_type = 'missing'
                    elif '位置不匹配' in error_part:
                        error_type = 'position'
                    elif '名称不匹配' in error_part:
                        error_type = 'name_mismatch'

                    # 查找下一行的文件信息
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('文件:'):
                            mod_file = next_line.replace('文件:', '').strip()

                    if mod_file:
                        errors.append({
                            'position': position,
                            'type': error_type,
                            'mod_file': mod_file
                        })

        i += 1

    return errors


def get_actual_mod_names(mods_dir, count, start=1):
    """
    获取mods文件夹中实际的模组名称

    Args:
        mods_dir: mods文件夹路径
        count: 要获取的模组数量
        start: 起始位置（从1开始）

    Returns:
        位置到模组名称的映射字典
    """
    script_dir = Path(__file__).parent
    compare_script = script_dir / 'compare_modlist.py'

    cmd = [
        sys.executable,
        str(compare_script),
        '-n', str(count),
        '-s', str(start)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode != 0:
            return {}

        mod_names = {}
        lines = result.stdout.split('\n')

        for line in lines:
            # 匹配模组列表行
            match = re.search(r'^\s*(\d+)\.\s+(.+\.jar)', line)
            if match:
                position = int(match.group(1))
                mod_file = match.group(2)
                mod_names[position] = mod_file

        return mod_names

    except Exception as e:
        print(f"错误: 获取模组名称失败 - {e}")
        return {}


def clean_mod_name(mod_name):
    """
    清理模组名称，移除版本后缀和.jar扩展名

    Args:
        mod_name: 原始模组文件名

    Returns:
        清理后的模组名称
    """
    if mod_name.endswith('.jar'):
        mod_name = mod_name[:-4]

    patterns = [
        r'-\d+\.\d+(\.\d+)?[-\d\w.]*',
        r'_\d+\.\d+(\.\d+)?[-\d\w.]*',
        r'-forge-\d+\.\d+',
        r'-neoforge-\d+\.\d+',
        r'-mc\d+\.\d+',
    ]

    for pattern in patterns:
        mod_name = re.sub(pattern, '', mod_name)

    return mod_name


def read_modlist_md(md_file):
    """
    读取mods-list.md文件内容

    Args:
        md_file: markdown文件路径

    Returns:
        文件内容和表格区域位置
    """
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找表格区域
        table_start = content.find('<mod-table>')
        table_end = content.find('</mod-table>')

        if table_start == -1 or table_end == -1:
            return content, None, None

        return content, table_start, table_end

    except Exception as e:
        print(f"错误: 读取markdown文件失败 - {e}")
        return None, None, None


def update_modlist_table(content, errors, mod_names):
    """
    重建整个modlist表格，填入所有模组

    Args:
        content: 原始文件内容
        errors: 错误信息列表（实际上会被忽略）
        mod_names: 实际模组名称映射

    Returns:
        更新后的文件内容
    """
    lines = content.split('\n')

    # 找到表格开始和结束位置
    table_start_line = -1
    table_end_line = -1
    header_line = -1
    separator_line = -1

    for i, line in enumerate(lines):
        if '<mod-table>' in line:
            table_start_line = i
        elif '编号 | 名称 | 环境 | 标签 | 描述' in line or '编号|名称|环境|标签|描述' in line:
            header_line = i
        elif ':---' in line:
            separator_line = i
        elif '</mod-table>' in line:
            table_end_line = i
            break

    if table_start_line == -1 or header_line == -1 or separator_line == -1 or table_end_line == -1:
        print("错误: 无法找到完整的表格结构")
        return content

    # 构建新的表格内容
    new_content = []

    # 保留表格开始前的内容
    for i in range(table_start_line + 1):
        new_content.append(lines[i])

    # 添加空行（如果原表格有空行）
    if lines[header_line - 1].strip() == '':
        new_content.append('')

    # 保留表头和分隔符
    new_content.append(lines[header_line])
    new_content.append(lines[separator_line])

    # 按位置顺序添加所有模组
    for position in sorted(mod_names.keys()):
        mod_file = mod_names[position]
        clean_name = clean_mod_name(mod_file)
        # 创建新行: 编号|名称|环境|标签|描述
        new_row = f"{position}| {clean_name} |  |  | "
        new_content.append(new_row)

    # 添加空行和结束标签
    new_content.append('')
    new_content.append(lines[table_end_line])

    # 保留表格结束后的内容
    for i in range(table_end_line + 1, len(lines)):
        new_content.append(lines[i])

    return '\n'.join(new_content)


def get_mods_directly(mods_dir, count, start=1):
    """
    直接从mods文件夹获取模组列表，按字典序排序

    Args:
        mods_dir: mods文件夹路径
        count: 要获取的模组数量
        start: 起始位置（从1开始）

    Returns:
        位置到模组名称的映射字典
    """
    mods_path = Path(mods_dir)
    if not mods_path.exists():
        print(f"错误: 找不到mods文件夹 {mods_dir}")
        return {}

    # 获取所有jar文件并按字典序排序
    jar_files = list(mods_path.glob('*.jar'))
    jar_files.sort(key=lambda x: x.name.lower())

    # 调整起始位置和结束位置
    start_index = max(0, start - 1)
    end_index = min(len(jar_files), start_index + count)

    mod_names = {}
    for i in range(start_index, end_index):
        position = i + 1
        mod_file = jar_files[i].name
        mod_names[position] = mod_file

    return mod_names


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='直接从mods文件夹读取模组并自动填充mods-list.md',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 自动填充前50个模组
  python auto_fill_modlist.py -c 50

  # 从第51个开始，填充50个模组（第51-100号）
  python auto_fill_modlist.py -s 51 -c 50
        """
    )

    parser.add_argument('-c', '--count', type=int, required=True,
                       help='要处理的模组数量')
    parser.add_argument('-s', '--start', type=int, default=1,
                       help='起始位置（从1开始，默认为1）')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，只显示将要进行的操作，不实际修改文件')

    args = parser.parse_args()

    # 获取路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    mods_dir = project_root / 'mods'
    md_file = project_root / 'docs' / 'mods-list.md'

    print(f"===== 模组列表自动填充工具 =====")
    print(f"处理范围: 第 {args.start} 到 {args.start + args.count - 1} 个模组")
    print(f"mods目录: {mods_dir}")
    print(f"markdown文件: {md_file}")
    print()

    # 检查文件是否存在
    if not md_file.exists():
        print(f"错误: 文件不存在 {md_file}")
        return

    # 直接从mods文件夹获取模组列表
    print("1. 从mods文件夹读取模组列表...")
    mod_names = get_mods_directly(mods_dir, args.count, args.start)

    if not mod_names:
        print("错误: 无法获取模组列表")
        return

    print(f"   找到 {len(mod_names)} 个模组")

    # 显示将要填充的模组
    print("2. 将要填充的模组:")
    for position in sorted(mod_names.keys()):
        mod_file = mod_names[position]
        clean_name = clean_mod_name(mod_file)
        print(f"   位置 {position:3d}: {clean_name}")

    if args.dry_run:
        print()
        print("试运行模式: 未实际修改文件")
        return

    # 更新markdown文件
    print("3. 重建markdown表格...")
    content, table_start, table_end = read_modlist_md(md_file)

    if content is None:
        print("错误: 无法读取markdown文件")
        return

    # 使用所有模组重建表格
    updated_content = update_modlist_table(content, [], mod_names)

    # 备份原文件
    backup_file = md_file.with_suffix('.md.backup')
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   已备份原文件到: {backup_file}")
    except Exception as e:
        print(f"警告: 备份失败 - {e}")

    # 写入更新内容
    try:
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"   已更新文件: {md_file}")
        print(f"   成功填充 {len(mod_names)} 个模组")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")

    print()
    print("完成！")


if __name__ == '__main__':
    import argparse
    main()