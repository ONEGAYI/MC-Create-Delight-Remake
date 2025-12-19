---
name: search-mods-and-summarize
description: 当用户需要为(游戏)模组建档、搜索时，使用该技能。典型提示词:"请为模组建档"
allowed-tools: Write, Edit, Bash(python D:\games\MC\.minecraft\versions\Create-Delight-Remake\scripts\mods_manager.py:*), Bash(python mods_manager.py:*)
---

# 搜索模组信息并总结建档
你的目标是正确的为**没有建档**的模组进行建档，这需要你进行搜索和总结。

## 注意事项
- 你应该优先使用 `exa` MCP 工具进行搜索
- 你应该尽量调用 agent 完成搜索，并将使用 `exa` 的信息提示给他
- 使用agent的时候，要求他只能进行搜索，并将最后结果汇报给你，最终由你进行总结更新

## 环境变量
1. 数据库文件夹 = `D:\games\MC\.minecraft\versions\Create-Delight-Remake\docs\`

## 流程
1. 阅读`references/how-to-use-mods-manager.md`了解模组管理器使用方式
2. 备份数据库
3. 初始化
   - 使用 `scripts/reset_updated_info.py` 还原 `updated_info.csv`
4. 获取未完成建档的模组(check)
   - 使用 `scripts/check_missing_fields.py` 后在 `configs/updated_missing_names.txt` 获取，一行一个
5. 根据需建档模组列表，构建信息搜索计划
6. 阅读`references/how-to-search-mod-info.md`了解模组信息搜索方式
7. 使用搜索工具进行搜索(优先使用 agent + `exa`)
8. 归纳总结信息，更新数据库(update)
    - 更新的字段包括: env, tags, description, number
    - 将信息按照 `configs/updated_info.csv` 的表头填在下方
      - 使用 `<safely-jump>` 占位可以跳过某个字段的更新
      > 如 `{{sha}},{{filename}},<safely-jump>,{{tags}},{{description}},{{number}}` 会跳过 `tags` 的更新
