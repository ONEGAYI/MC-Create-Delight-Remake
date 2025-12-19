#!/usr/bin/env python3
"""
分类统计脚本
统计新分类体系中各分类的模组数量分布
"""

import re
from collections import defaultdict

def analyze_classification():
    """分析分类统计"""
    with open('D:/games/MC/.minecraft/versions/Create-Delight-Remake/docs/mods-list.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计各分类的模组数量
    category_count = defaultdict(int)
    category_mods = defaultdict(list)

    # 解析模组行
    lines = content.split('\n')
    for line in lines:
        if '|' in line and not line.startswith('|:---') and not line.startswith('**建档情况'):
            parts = line.split('|')
            if len(parts) >= 4:
                mod_name = parts[1].strip()
                tags = parts[3].strip()

                if mod_name and tags:
                    # 解析标签
                    tag_list = [tag.strip() for tag in tags.split(',')]
                    main_category = tag_list[0] if tag_list else "未分类"

                    # 只统计主分类（不带#的）
                    if main_category.startswith('#'):
                        main_category = main_category[1:]

                    category_count[main_category] += 1
                    category_mods[main_category].append(mod_name)

    # 打印统计结果
    print("📊 Create-Delight-Remake 模组包分类统计 (150个模组)")
    print("=" * 60)

    # 按数量排序
    sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)

    total_mods = sum(category_count.values())

    for category, count in sorted_categories:
        percentage = (count / total_mods) * 100
        print(f"🏷️  {category:<15} : {count:>3} 个模组 ({percentage:>5.1f}%)")

    print("=" * 60)
    print(f"📈 总计: {total_mods} 个模组")

    # 详细分类分析
    print("\n📋 详细分析:")
    print("-" * 60)

    for category, count in sorted_categories:
        print(f"\n🔹 {category} ({count}个模组):")
        for mod in category_mods[category][:5]:  # 显示前5个
            print(f"   • {mod}")
        if len(category_mods[category]) > 5:
            print(f"   ... 还有 {len(category_mods[category]) - 5} 个模组")

if __name__ == "__main__":
    analyze_classification()