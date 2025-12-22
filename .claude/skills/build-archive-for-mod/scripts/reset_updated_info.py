#!/usr/bin/env python3
"""
还原 updated_info.csv 的标题行
"""

import csv

# 输出文件路径
output_path = r"D:\games\MC\.minecraft\versions\Create-Delight-Remake\.claude\skills\search-mods-info\configs\updated_info.csv"

# 写入标题行和一行空行
with open(output_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['sha', 'updated_at', 'filename', 'env', 'tags', 'description'])

print(f"已还原 updated_info.csv 的标题行: {output_path}")