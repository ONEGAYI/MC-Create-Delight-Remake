#!/usr/bin/env python3
"""
还原 updated_info.csv 的标题行
"""

import csv

# 输出文件路径
output_path = r"D:\games\MC\.minecraft\versions\Create-Delight-Remake\.claude\skills\build-archive-for-mod\configs\updated_info.csv"

# 写入标题行（updated_at 由 batch_update_manager.py 自动生成）
with open(output_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['sha', 'filename', 'env', 'tags', 'description'])

print(f"已还原 updated_info.csv 的标题行: {output_path}")