---
name: search-mods-and-summarize
description: 当用户需要为(游戏)模组建档、搜索时，使用该技能。典型提示词:"请继续为模组建档"
allowed-tools: Write, Edit
---

# 搜索模组信息并总结建档
你的目标是正确的为**没有建档**的模组进行建档，这需要你进行搜索和总结。

## 注意事项
- 你应该优先使用 `exa` MCP 工具进行搜索
- 你应该尽量调用 agent 完成搜索，并将使用 `exa` 的信息提示给他
- 使用agent的时候，要求他只能进行搜索，并将最后结果汇报给你，最终由你进行总结更新

## 流程
你必须先阅读 `references/how-to-search-mod-info.md` 来了解具体的搜索流程

完成 mod-list.md 的更新后，请使用 `scripts/compare_modlist.py -c` 来确保准确无误

