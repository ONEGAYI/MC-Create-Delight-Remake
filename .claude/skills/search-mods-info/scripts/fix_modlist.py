import json
import re

modlist = "D:\\games\\MC\\.minecraft\\versions\\Create-Delight-Remake\\docs\\mods-list.md"
modlist_json = "D:\\games\\MC\\.minecraft\\versions\\Create-Delight-Remake\\docs\\mods-list.json"


def extract_table_to_json(input_file=None, output_file=None):
    """
    从mods-list.md文件中提取mod-table表格数据并保存为JSON格式

    Args:
        input_file: 输入的markdown文件路径，默认使用modlist变量
        output_file: 输出的JSON文件路径，默认使用modlist_json变量
    """
    # 使用默认路径
    if input_file is None:
        input_file = modlist
    if output_file is None:
        output_file = modlist_json

    # 读取文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        return
    except Exception as e:
        print(f"错误: 读取文件时出错 - {e}")
        return

    # 查找<mod-table>标签内的内容
    table_pattern = r'<mod-table>(.*?)</mod-table>'
    table_match = re.search(table_pattern, content, re.DOTALL)

    if not table_match:
        print("错误: 未找到<mod-table>标签")
        return

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
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"成功: 已提取 {len(result['mods'])} 个模组数据到 {output_file}")
    except Exception as e:
        print(f"错误: 保存JSON文件时出错 - {e}")


if __name__ == '__main__':
    extract_table_to_json()