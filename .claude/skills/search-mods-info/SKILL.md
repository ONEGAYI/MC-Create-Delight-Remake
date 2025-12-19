---
name: search-mods-and-summarize
description: 当用户需要为(游戏)模组建档、搜索时，使用该技能。典型提示词:"请继续为模组建档"
allowed-tools: Write, Edit
---

# 搜索模组信息并总结建档
你的目标是正确的为没有建档的模组进行建档，这需要你进行搜索和总结。

## 注意事项
- 你应该优先使用 `exa` MCP 工具进行搜索
- 你应该尽量调用 agent 完成搜索，并将使用 `exa` 的信息提示给他

## 流程
你必须先阅读 `references/how-to-search-mod-info.md` 来了解具体的搜索流程

完成 mod-list.md 的更新后，请使用 `scripts/compare_modlist.py -c` 来确保准确无误

## 可以使用的工具
1. `scripts/classify_statistics.py`
   - 分类统计脚本
   - 统计新分类体系中各分类的模组数量分布

2. `scripts/update_modlist_numbers.py`
   - 模组列表行号更新脚本
   - 自动为mods-list.md中`<mod-table>`标签内的表格更新行号

3. `scripts/compare_modlist.py`
   - 模组列表对比脚本
   > options:
   >    -h, --help            show this help message and exit
   >    -n, --number NUMBER   显示N个模组名称（从起始位置开始）
   >    -c, --compare COMPARE
   >                          比较N个模组的一致性（从起始位置开始）
   >    -s, --start START     起始位置（从1开始，默认为1）