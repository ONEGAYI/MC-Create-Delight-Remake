#!/usr/bin/env python3
"""
还原 updated_info.csv 的标题行
"""

import csv
import os

# 输出文件路径（基于脚本位置的相对路径）
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, '..', 'configs', 'updated_info.csv')

# 写入标题行（updated_at 由 batch_update_manager.py 自动生成）
with open(output_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['sha', 'filename', 'env', 'tags', 'description'])

print(f"已还原 updated_info.csv 的标题行: {output_path}")