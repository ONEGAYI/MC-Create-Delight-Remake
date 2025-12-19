#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import argparse
import sys
import os

# 默认文件路径
DEFAULT_MODLIST = "D:\\games\\MC\\.minecraft\\versions\\Create-Delight-Remake\\docs\\mods-list.md"
DEFAULT_MODLIST_JSON = "D:\\games\\MC\\.minecraft\\versions\\Create-Delight-Remake\\docs\\mods-list.json"


def extract_table_to_json(input_file=None, output_file=None):
    """
    从mods-list.md文件中提取mod-table表格数据并保存为JSON格式

    Args:
        input_file: 输入的markdown文件路径，默认使用DEFAULT_MODLIST
        output_file: 输出的JSON文件路径，默认使用DEFAULT_MODLIST_JSON
    """
    # 使用默认路径
    if input_file is None:
        input_file = DEFAULT_MODLIST
    if output_file is None:
        output_file = DEFAULT_MODLIST_JSON

    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 找不到文件 {input_file}")
        return False

    # 读取文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
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

    # 准备结果数据结构
    result = {
        "mods": []
    }

    # 解析表格行
    for line in lines:
        # 跳过空行
        if not line.strip():
            continue

        # 跳过表头行
        if any(keyword in line for keyword in ['编号', '名称', '环境', '标签', '描述', ':---']):
            continue

        # 分割行内容
        parts = line.split('|')

        # 检查是否是有效的表格行（数据行通常是5列）
        if len(parts) >= 5:
            # 提取各列数据
            number = parts[0].strip()
            name = parts[1].strip()
            env = parts[2].strip()
            tags = parts[3].strip()
            description = parts[4].strip()

            # 转换编号为整数
            try:
                number = int(number)
            except ValueError:
                # 如果不是数字，跳过这一行
                continue

            # 即使名称为空，只要有编号就添加
            mod_data = {
                "number": number,
                "name": name,
                "env": env,
                "tags": tags,
                "description": description
            }
            result["mods"].append(mod_data)

    # 保存JSON文件
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"成功: 已提取 {len(result['mods'])} 个模组数据到 {output_file}")
        return True
    except Exception as e:
        print(f"错误: 保存JSON文件时出错 - {e}")
        return False


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description='模组列表处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s -e                           # 使用默认路径提取表格
  %(prog)s -e -i input.md -o out.json   # 指定输入输出文件
  %(prog)s -e -i custom.md              # 指定输入文件，使用默认输出
        """
    )

    # 添加参数
    parser.add_argument('-e', '--extract', action='store_true',
                        help='提取<mod-table>表格数据并保存为JSON格式')
    parser.add_argument('-i', '--input', type=str,
                        help=f'输入的markdown文件路径 (默认: {DEFAULT_MODLIST})')
    parser.add_argument('-o', '--output', type=str,
                        help=f'输出的JSON文件路径 (默认: {DEFAULT_MODLIST_JSON})')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')

    # 解析参数
    args = parser.parse_args()

    # 如果没有提供任何参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # 执行相应功能
    if args.extract:
        input_file = args.input if args.input else DEFAULT_MODLIST
        output_file = args.output if args.output else DEFAULT_MODLIST_JSON

        print(f"正在从 {input_file} 提取表格数据...")
        success = extract_table_to_json(input_file, output_file)

        if success:
            print("表格提取完成！")
        else:
            print("表格提取失败！")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()