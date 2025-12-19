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
- `mods_manager.py` 和 `batch_update_manager.py` 在 `D:\games\MC\.minecraft\versions\Create-Delight-Remake\scripts`
- 其余的脚本在skill所在的文件下

## 环境变量
1. 数据库文件夹 = `D:\games\MC\.minecraft\versions\Create-Delight-Remake\docs\`

## 模组建档完整流程

### 第一步：准备工作
1. **阅读模组使用指南** - 了解模组管理器的使用方法 `references/how-to-use-mods-manager.md`

### 第二步：初始化工作环境
1. **重置更新信息文件** - 清空之前的更新记录
   ```bash
   python scripts/reset_updated_info.py
   ```
   此操作会重置 `configs/updated_info.csv` 文件，准备接收新的更新数据。

2. **同步模组数据库** - 确保数据库与模组文件夹同步
   ```bash
   python scripts/mods_manager.py sync --folder ../mods [--force]
   ```
   - **关键步骤**
   - 自动检测新增的模组文件
   - 识别已删除的模组（需确认）
   - 更新模组文件的路径信息
   - 保持数据库与实际文件夹的一致性

### 第三步：获取待建档模组列表
1. **检查缺失字段** - 找出需要补充信息的模组
   ```bash
   python scripts/check_missing_fields.py
   ```
2. **查看结果** - 在 `configs/updated_missing_names.txt` 中查看需要建档的模组列表
   - 每行一个模组名称
   - 按照优先级排序

### 第四步：制定搜索计划
根据待建档模组列表，合理安排搜索顺序：
- 优先处理知名模组（信息容易获取）
- 批量处理相似模组（提高效率）
- 记录搜索进度，避免遗漏
- 诚实汇报，没有信源时交由用户搜索，更加稳妥; 禁止胡编乱造

### 第五步：搜索模组信息
1. **阅读搜索指南** - 查看 `references/how-to-search-mod-info.md`
2. **使用搜索工具** - 优先使用 agent + `exa` 工具
   - 让 agent 专注于搜索
   - 自己负责信息整理和总结

### 第六步：更新数据库
1. **准备更新数据** - 将搜集到的信息填入 `configs/updated_info.csv`
   - 表头格式：`sha,updated_at,filename,env,tags,description`
   - 使用 `<safely-jump>` 占位符跳过不需要更新的字段 (若用户指定)
   - `updated_at` 可以不填，将自动生成
   - 示例：`a1b2c3d4,2025-12-19 18:18:46,mod.jar,客户端,#工具,<safely-jump>`

2. **执行批量更新** - 使用批量更新脚本
   ```bash
   python scripts/batch_update_manager.py
   ```
   - 支持干运行模式预览更改
   - 自动备份数据库
   - SHA前缀智能匹配
   - 详细的更新日志
