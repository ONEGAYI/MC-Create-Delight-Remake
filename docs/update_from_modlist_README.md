# Modlist 数据库更新工具

## 概述

`update_from_modlist.py` 是一个用于从 `mods-list.csv` 文件中提取模组信息并更新到 `mods_metadata.db` 数据库的工具。

## 功能特性

- 从 CSV 文件读取模组元数据（编号、环境、标签、描述）
- 通过文件名自动匹配数据库记录
- 批量更新数据库字段
- 生成详细的更新报告
- 自动处理编码问题（支持 UTF-8、GBK 等）
- 保存未匹配的记录到文件

## 使用前准备

1. **确保数据库存在**
   ```bash
   python scripts/mods_manager.py sync
   ```

2. **确保 CSV 文件存在**
   - 文件路径：`docs/mods-list.csv`
   - 包含列：编号、名称、环境、标签、描述

3. **备份数据库**（可选）
   ```bash
   # 手动备份
   cp docs/mods_metadata.db docs/mods_metadata_backup_$(date +%Y%m%d_%H%M%S).db
   ```

## 使用方法

### 基本用法

```bash
cd scripts
python update_from_modlist.py
```

### 输出示例

```
============================================================
模组数据库更新工具
============================================================
✓ 成功连接数据库: ../docs/mods_metadata.db

检查数据库结构...
✓ 添加字段: number
✓ 添加字段: env
✓ 添加字段: tags
✓ 添加字段: description

正在读取CSV文件...
✓ 成功读取CSV文件，共340条记录

开始更新数据库记录...
------------------------------------------------------------
[340/340] 正在处理: twilightforest-1.20.1-4.3.2149-universal
------------------------------------------------------------
✓ 数据库更新已提交

============================================================
更新统计报告
============================================================
总记录数:      340
成功更新:      298
未找到匹配:    35
更新错误:      7
成功率:        87.6%

------------------------------------------------------------
问题记录详情

[未找到的文件] (35个):
  #  1 0World2Create-Universal-1.19-1.20.X-1.0.0.jar
  # 15 some-mod-not-in-database.jar
  ... 还有 25 个未显示

✓ 未匹配的记录已保存到: ../docs/unmatched_mods.txt

✓ 更新完成！
```

## 数据映射关系

| CSV 列 | 数据库字段 | 说明 |
|--------|------------|------|
| 编号 | number | 模组编号（整数） |
| 名称 + .jar | filename | 用于匹配的文件名 |
| 环境 | env | 客户端/服务端/双端类 |
| 标签 | tags | 以 # 开头的标签 |
| 描述 | description | 模组描述 |

## 注意事项

1. **文件名匹配**：
   - CSV 中的名称会自动添加 `.jar` 后缀进行匹配
   - 确保数据库中的文件名与 CSV 中的名称一致

2. **编码问题**：
   - 脚本自动尝试多种编码（UTF-8、GBK 等）
   - 如果仍有问题，请检查 CSV 文件编码

3. **未匹配记录**：
   - 未找到匹配的文件会保存到 `docs/unmatched_mods.txt`
   - 可以手动检查这些文件是否需要添加到数据库

4. **事务安全**：
   - 所有更新在单个事务中执行
   - 失败时会自动回滚

## 故障排除

### 问题：找不到数据库文件
```
✗ 数据库文件不存在: ../docs/mods_metadata.db
```
**解决方案**：
```bash
cd scripts
python mods_manager.py sync --folder ../mods
```

### 问题：CSV 文件读取失败
```
✗ 无法使用任何编码读取CSV文件
```
**解决方案**：
1. 检查 CSV 文件是否存在
2. 确认文件编码，可尝试用记事本另存为 UTF-8

### 问题：成功率较低
可能原因：
1. 数据库中的文件名与 CSV 中的名称不匹配
2. 某些模组文件已被删除或重命名

**解决方案**：
1. 检查 `unmatched_mods.txt` 文件
2. 运行 `mods_manager.py sync` 更新数据库

## 工作流程建议

1. **初次使用**：
   ```bash
   # 1. 扫描模组文件
   python scripts/mods_manager.py sync

   # 2. 更新数据库信息
   python scripts/update_from_modlist.py

   # 3. 检查未匹配的文件
   cat docs/unmatched_mods.txt
   ```

2. **定期维护**：
   ```bash
   # 1. 同步新文件
   python scripts/mods_manager.py sync

   # 2. 更新信息
   python scripts/update_from_modlist.py
   ```

## 相关文件

- `scripts/mods_manager.py` - 模组管理主脚本
- `docs/mods-list.csv` - 模组列表 CSV 文件
- `docs/mods_metadata.db` - SQLite 数据库文件
- `docs/unmatched_mods.txt` - 未匹配记录输出文件