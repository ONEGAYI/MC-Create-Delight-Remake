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

        # [修复] 跳过表头行
        # 原来的代码会导致包含"描述"、"环境"等词的正常数据行被跳过
        # 例如编号125的描述是"为所有附魔添加详细的中文描述..."，会被误判
        if ':---' in line:  # 跳过分割线
            continue
        if line.strip().startswith('编号') and '|' in line: # 跳过标题行
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


def json_to_md(json_file=None, output_file=None):
    """
    将JSON文件中的模组数据写入到markdown文件的表格中

    Args:
        json_file: 输入的JSON文件路径，默认使用DEFAULT_MODLIST_JSON
        output_file: 输出的markdown文件路径，默认使用DEFAULT_MODLIST
    """
    # 使用默认路径
    if json_file is None:
        json_file = DEFAULT_MODLIST_JSON
    if output_file is None:
        output_file = DEFAULT_MODLIST

    # 检查JSON文件是否存在
    if not os.path.exists(json_file):
        print(f"错误: 找不到JSON文件 {json_file}")
        return False

    # 读取JSON文件
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误: 读取JSON文件时出错 - {e}")
        return False

    # 检查JSON结构
    if 'mods' not in data:
        print("错误: JSON文件中缺少 'mods' 字段")
        return False

    # 读取markdown文件
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"错误: 读取markdown文件时出错 - {e}")
        return False

    # 查找<mod-table>标签
    table_start_pattern = r'<mod-table>'
    table_end_pattern = r'</mod-table>'

    start_match = re.search(table_start_pattern, content)
    end_match = re.search(table_end_pattern, content)

    if not start_match or not end_match:
        print("错误: 未找到<mod-table>标签")
        return False

    # 构建新的表格内容
    # 获取所有模组并按编号排序
    mods = data['mods']
    mods_sorted = sorted(mods, key=lambda x: x.get('number', 0))

    # 构建表格行
    table_lines = []

    # 添加表头
    table_lines.append("编号 | 名称 | 环境 | 标签 | 描述")
    table_lines.append(":---|:---:|:---:|:---:|:---:")

    # 添加数据行
    for mod in mods_sorted:
        number = mod.get('number', '')
        name = mod.get('name', '')
        env = mod.get('env', '')
        tags = mod.get('tags', '')
        description = mod.get('description', '')

        # 构建表格行
        line = f"{number}| {name} | {env} | {tags} | {description}"
        table_lines.append(line)

    # 创建新的表格内容
    new_table_content = '\n'.join(table_lines)

    # 替换原有表格内容
    # 保留<mod-table>标签，在标签后添加两个空行再插入新表格
    before_table = content[:start_match.end()]
    after_table = content[end_match.start():]

    # 构建新内容，在<mod-table>后添加两个空行（保持原始格式）
    new_content = before_table + '\n\n' + new_table_content + '\n' + after_table

    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"成功: 已将 {len(mods_sorted)} 个模组数据写入 {output_file}")
        return True
    except Exception as e:
        print(f"错误: 写入markdown文件时出错 - {e}")
        return False


def parse_swap_string(swap_str):
    """
    解析交换字符串格式："[1-30, 10-9]"
    返回：[(1, 30), (10, 9)]

    Args:
        swap_str: 交换字符串，格式如 "[1-30, 10-9]"

    Returns:
        list: 交换对列表，如 [(1, 30), (10, 9)]
    """
    # 去除空格和方括号
    swap_str = swap_str.strip()
    if swap_str.startswith('[') and swap_str.endswith(']'):
        swap_str = swap_str[1:-1]

    # 分割交换对
    pairs = []
    for pair_str in swap_str.split(','):
        pair_str = pair_str.strip()
        if not pair_str:
            continue

        # 解析 from-to 格式
        if '-' in pair_str:
            try:
                from_num, to_num = map(int, pair_str.split('-', 1))
                if from_num <= 0 or to_num <= 0:
                    print(f"警告: 跳过无效的交换对 '{pair_str}' (编号必须大于0)")
                    continue
                pairs.append((from_num, to_num))
            except ValueError:
                print(f"警告: 跳过无效的交换对 '{pair_str}' (格式错误)")
        else:
            print(f"警告: 跳过格式错误的交换对 '{pair_str}' (缺少连字符)")

    return pairs


def swap_mod_numbers(json_file, swap_pairs, output_file=None):
    """
    只交换编号字段，其他字段保持不变

    Args:
        json_file: JSON文件路径
        swap_pairs: 交换对列表，如 [(1, 30), (10, 9)]
        output_file: 输出文件路径，默认覆盖原文件

    Returns:
        tuple: (successful_swaps, failed_swaps)
    """
    # 检查JSON文件是否存在
    if not os.path.exists(json_file):
        print(f"错误: 找不到JSON文件 {json_file}")
        return [], []

    # 读取 JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误: 读取JSON文件时出错 - {e}")
        return [], []

    # 检查JSON结构
    if 'mods' not in data:
        print("错误: JSON文件中缺少 'mods' 字段")
        return [], []

    # 创建编号到模组对象的映射
    mod_dict = {}
    for mod in data['mods']:
        if 'number' in mod:
            mod_dict[mod['number']] = mod

    # 执行交换
    successful_swaps = []
    failed_swaps = []

    for from_num, to_num in swap_pairs:
        # 检查编号存在
        if from_num not in mod_dict:
            failed_swaps.append((from_num, to_num, f"编号 {from_num} 不存在"))
            continue
        if to_num not in mod_dict:
            failed_swaps.append((from_num, to_num, f"编号 {to_num} 不存在"))
            continue

        # 只交换编号字段
        mod_dict[from_num]['number'], mod_dict[to_num]['number'] = to_num, from_num
        successful_swaps.append((from_num, to_num))

    # 保存文件
    output_path = output_file or json_file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"错误: 保存JSON文件时出错 - {e}")
        return successful_swaps, failed_swaps + [(0, 0, f"保存失败: {e}")]

    return successful_swaps, failed_swaps


def check_number_range(json_file, start_num, end_num):
    """
    检查指定范围内的编号是否在JSON中存在且内容完整

    Args:
        json_file: JSON文件路径
        start_num: 起始编号
        end_num: 结束编号

    Returns:
        bool: 检查是否通过（无错误时返回True）
    """
    # 检查JSON文件是否存在
    if not os.path.exists(json_file):
        print(f"错误: 找不到JSON文件 {json_file}")
        return False

    # 读取JSON文件
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误: 读取JSON文件时出错 - {e}")
        return False

    # 检查JSON结构
    if 'mods' not in data:
        print("错误: JSON文件中缺少 'mods' 字段")
        return False

    # 创建编号到模组数据的映射
    mod_dict = {}
    for mod in data['mods']:
        if 'number' in mod:
            mod_dict[mod['number']] = mod

    # 统计信息
    total_check = end_num - start_num + 1
    missing_numbers = []
    incomplete_mods = []

    print(f"正在检查编号范围 {start_num} 到 {end_num}...")
    print(f"总共需要检查 {total_check} 个编号")

    # 检查每个编号
    for num in range(start_num, end_num + 1):
        if num not in mod_dict:
            missing_numbers.append(num)
        else:
            mod = mod_dict[num]
            # 检查内容完整性
            missing_fields = []

            if not mod.get('name', '').strip():
                missing_fields.append('名称')
            if not mod.get('env', '').strip():
                missing_fields.append('环境')
            if not mod.get('tags', '').strip():
                missing_fields.append('标签')
            if not mod.get('description', '').strip():
                missing_fields.append('描述')

            if missing_fields:
                incomplete_mods.append({
                    'number': num,
                    'name': mod.get('name', ''),
                    'missing_fields': missing_fields
                })

    # 输出检查结果
    print(f"\n========== 检查结果 ==========")
    print(f"检查范围: {start_num} - {end_num}")
    print(f"总编号数: {total_check}")
    print(f"存在的编号: {total_check - len(missing_numbers)}")
    print(f"缺失的编号: {len(missing_numbers)}")
    print(f"内容不完整的编号: {len(incomplete_mods)}")

    # 输出具体错误信息
    if missing_numbers:
        print(f"\n❌ 缺失的编号 ({len(missing_numbers)} 个):")
        for i, num in enumerate(missing_numbers, 1):
            print(f"  {i}. 编号 {num}: 完全缺失")

    if incomplete_mods:
        print(f"\n⚠️  内容不完整的编号 ({len(incomplete_mods)} 个):")
        for i, mod_info in enumerate(incomplete_mods, 1):
            num = mod_info['number']
            name = mod_info['name'] or '(无名称)'
            fields = ', '.join(mod_info['missing_fields'])
            print(f"  {i}. 编号 {num} ({name}): 缺少 {fields}")

    # 总结
    success_count = total_check - len(missing_numbers) - len(incomplete_mods)
    error_rate = ((len(missing_numbers) + len(incomplete_mods)) / total_check) * 100

    print(f"\n✅ 完整的编号: {success_count} 个 ({(success_count/total_check)*100:.1f}%)")
    print(f"❌ 错误总数: {len(missing_numbers) + len(incomplete_mods)} 个 ({error_rate:.1f}%)")

    if missing_numbers or incomplete_mods:
        print(f"\n⚠️  检查未通过，发现 {len(missing_numbers) + len(incomplete_mods)} 个问题")
        return False
    else:
        print(f"\n✅ 检查通过！所有编号都存在且内容完整")
        return True


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
  %(prog)s -w                           # 使用默认路径将JSON写入MD
  %(prog)s -w -j in.json -o out.md      # 指定JSON输入和MD输出文件
  %(prog)s -w -j custom.json            # 指定JSON文件，使用默认MD输出
  %(prog)s --check-number-from 1 --check-number-to 50    # 检查1-50号编号
  %(prog)s --swap "[1-30]"              # 交换编号1和30的模组
  %(prog)s --swap "[1-30, 10-9]"        # 交换多对模组编号
  %(prog)s --swap "[1-30]" -w           # 交换并自动更新markdown
  %(prog)s --swap "[1-30]" -j custom.json -o output.json  # 使用自定义文件

⚠️  重要提示:
  - 使用 --swap 参数时，如果不指定 -j 输出文件，默认不会覆盖源JSON文件
  - 多次swap操作需要指定 -j 参数覆盖源文件，否则每次swap都基于原始数据
  - 推荐做法: --swap "[1-30, 10-9]" -j source.json -o source.json
        """
    )

    # 添加参数
    parser.add_argument('-e', '--extract', action='store_true',
                        help='提取<mod-table>表格数据并保存为JSON格式')
    parser.add_argument('-w', '--write', action='store_true',
                        help='将JSON数据写入到markdown文件的表格中')
    parser.add_argument('-i', '--input', type=str,
                        help=f'输入的markdown文件路径 (默认: {DEFAULT_MODLIST})')
    parser.add_argument('-o', '--output', type=str,
                        help=f'输出文件路径 (根据模式决定是JSON还是MD)')
    parser.add_argument('-j', '--json-file', type=str,
                        help=f'JSON文件路径 (用于-w或检查模式，默认: {DEFAULT_MODLIST_JSON})')
    parser.add_argument('--swap', type=str,
                        help='交换指定编号的模组，格式："[1-30, 10-9]" (支持多对交换)。注意：默认不会覆盖源JSON文件，需配合-j参数')
    parser.add_argument('--check-number-from', type=int,
                        help='检查编号范围的起始编号')
    parser.add_argument('--check-number-to', type=int,
                        help='检查编号范围的结束编号')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')

    # 解析参数
    args = parser.parse_args()

    # 如果没有提供任何参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # 参数验证
    if (args.check_number_from is not None) != (args.check_number_to is not None):
        print("错误: --check-number-from 和 --check-number-to 必须同时提供")
        sys.exit(1)

    if args.check_number_from is not None and args.check_number_from > args.check_number_to:
        print("错误: 起始编号不能大于结束编号")
        sys.exit(1)

    # 检查 -e 和 -w 互斥
    if args.extract and args.write:
        print("错误: -e/--extract 和 -w/--write 参数不能同时使用")
        sys.exit(1)

    # 检查 --swap 与其他参数的互斥性
    if args.swap:
        if args.extract:
            print("错误: --swap 参数不能与 -e/--extract 同时使用")
            sys.exit(1)
        if args.check_number_from is not None:
            print("错误: --swap 参数不能与 --check-number-from/to 同时使用")
            sys.exit(1)

    # 执行相应功能，--swap 优先级最高
    if args.swap:
        json_file = args.json_file if args.json_file else DEFAULT_MODLIST_JSON

        # 如果同时使用 -w，-o 参数指向的是 markdown 文件，不是 JSON 文件
        if args.write:
            # 交换输出到临时 JSON 文件，然后再写入 markdown
            import tempfile
            temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            temp_json.close()
            swap_output_file = temp_json.name
            md_output_file = args.output if args.output else DEFAULT_MODLIST
        else:
            # 只进行交换，-o 参数指向的是 JSON 输出文件
            swap_output_file = args.output if args.output else json_file
            md_output_file = None

        print(f"正在从 {json_file} 交换模组编号...")
        print(f"交换规则: {args.swap}")

        # 解析交换字符串
        swap_pairs = parse_swap_string(args.swap)
        if not swap_pairs:
            print("错误: 没有有效的交换对")
            sys.exit(1)

        print(f"解析到 {len(swap_pairs)} 个交换对")
        for i, (from_num, to_num) in enumerate(swap_pairs, 1):
            print(f"  {i}. {from_num} ↔ {to_num}")

        # 执行交换
        successful_swaps, failed_swaps = swap_mod_numbers(json_file, swap_pairs, swap_output_file)

        # 输出结果
        print(f"\n========== 交换结果 ==========")
        print(f"总交换对: {len(swap_pairs)}")
        print(f"成功交换: {len(successful_swaps)}")
        print(f"失败交换: {len(failed_swaps)}")

        if successful_swaps:
            print(f"\n✅ 成功的交换:")
            for i, (from_num, to_num) in enumerate(successful_swaps, 1):
                print(f"  {i}. 编号 {from_num} ↔ {to_num}")

        if failed_swaps:
            print(f"\n❌ 失败的交换:")
            for i, (from_num, to_num, reason) in enumerate(failed_swaps, 1):
                print(f"  {i}. 编号 {from_num} ↔ {to_num} ({reason})")

        # 如果需要同时写入 markdown
        if args.write:
            print(f"\n正在更新 markdown 文件: {md_output_file}...")
            success = json_to_md(swap_output_file, md_output_file)
            if success:
                print("✅ Markdown 文件已更新")
                # 清理临时文件
                os.unlink(swap_output_file)
            else:
                print("❌ Markdown 文件更新失败")
                # 保留临时文件以便调试
                print(f"临时 JSON 文件保存在: {swap_output_file}")
        elif args.output:
            print(f"\n✅ 交换结果已保存到: {swap_output_file}")

        # 如果有失败的交换，退出码为1
        if failed_swaps:
            sys.exit(1)
    elif args.write:
        json_file = args.json_file if args.json_file else DEFAULT_MODLIST_JSON
        output_file = args.output if args.output else DEFAULT_MODLIST

        print(f"正在将 JSON 数据写入 markdown 文件...")
        print(f"JSON 源文件: {json_file}")
        print(f"MD 输出文件: {output_file}")

        success = json_to_md(json_file, output_file)
        if success:
            print(f"✅ 已成功将 JSON 数据写入 {output_file}")
        else:
            print(f"❌ 写入失败")
            sys.exit(1)
    elif args.check_number_from is not None:
        json_file = args.json_file if args.json_file else DEFAULT_MODLIST_JSON

        success = check_number_range(json_file, args.check_number_from, args.check_number_to)

        if not success:
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()