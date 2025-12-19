# Mod Manager 使用指南

## 概述

`mods_manager.py` 是一个功能强大的 Minecraft 模组文件管理工具，用于自动化管理模组文件的元数据。该工具使用 SQLite 数据库存储模组文件的 SHA256 哈希值和其他自定义信息，支持文件同步、字段管理、批量操作和高级搜索等功能。

## 核心功能

### 1. 文件同步与版本控制
- 自动扫描指定文件夹中的模组文件
- 计算并存储每个文件的 SHA256 哈希值
- 检测新增、删除、移动和重命名的文件
- 智能同步本地文件系统与数据库记录

### 2. 动态字段管理
- 支持动态添加自定义字段（如环境、标签、描述等）
- 字段类型支持：TEXT、INTEGER、REAL
- 允许重命名和删除字段（核心字段除外）
- 自动显示当前数据库结构

### 3. 灵活的更新机制
- 单个文件更新：通过 SHA 前缀精确更新
- 批量更新：支持 SQL WHERE 条件过滤
- 空值检查：快速识别缺失信息的文件

### 4. 强大的搜索功能
- 支持任意字段的搜索
- 三种搜索模式：
  - 模糊匹配（默认）
  - 精确匹配（使用引号包围）
  - 正则表达式（使用 -r 参数）
- 结果显示文件名、SHA、字段值和相对路径

### 5. 数据库备份与恢复
- 支持数据库备份到指定目录
- 自动生成带时间戳的备份文件
- 支持从备份文件恢复数据库
- 支持列出所有备份文件

### 6. CSV数据导出
- 将数据库表导出为CSV格式
- 支持UTF-8 BOM编码（兼容Excel）
- 自动处理包含逗号的字段（使用双引号包围）
- 支持指定表名和导出路径

## 安装与配置

### 环境要求
- Python 3.6+
- SQLite3（Python 标准库）
- 无需额外依赖

### 配置文件
脚本开头的配置区域可以根据需要调整：

```python
# 数据库文件路径
DB_NAME = '../docs/mods_metadata.db'

# 默认扫描的文件夹路径
DEFAULT_FOLDER = '..\\mods'

# 核心字段定义（不可删除）
CORE_FIELDS = {
    'sha': 'TEXT PRIMARY KEY',
    'filename': 'TEXT',
    'filepath': 'TEXT',
    'created_at': 'TIMESTAMP'
}
```

## 命令行接口

### 基本语法
```bash
python mods_manager.py <命令> [参数...]
```

### 命令详解

#### 1. sync - 同步文件夹
扫描指定文件夹并同步到数据库。

```bash
# 使用默认路径同步
python mods_manager.py sync

# 指定路径同步
python mods_manager.py sync --folder "D:\path\to\mods"

# 自动确认删除（无需用户交互）
python mods_manager.py sync --force

# 组合使用：指定路径并自动确认
python mods_manager.py sync --folder "D:\path\to\mods" --force
```

功能：
- 检测新增文件并添加到数据库
- 检测已删除文件并询问是否清理
- 更新重命名或移动文件的路径信息

**参数说明**：
- `--folder`: 指定扫描的文件夹路径（可选，默认：`../mods`）
- `--force`: 自动确认删除数据库中缺失文件的记录，无需用户交互（适用于自动化脚本）

#### 2. add_field - 添加字段
为数据库表添加新的自定义字段。

```bash
# 添加文本字段
python mods_manager.py add_field env

# 添加带类型的字段
python mods_manager.py add_field rating --type INTEGER
```

#### 3. check - 检查缺失
检查指定字段为空的记录。

```bash
# 检查缺失环境标签的文件
python mods_manager.py check env
```

#### 4. update - 单个更新
更新特定文件的字段值。

没有固定的最小位数要求，但建议：
- 至少 6-8 位：通常能确保唯一性
- 8 位或更安全：对于大量文件的数据库更可靠
- 完整 SHA（64 位）：最保险，但输入较长

```bash
# 使用 SHA 前缀更新
python mods_manager.py update a1b2c3d4 env "客户端"
```

#### 5. batch_write - 批量更新
批量更新多个记录的字段值。

```bash
# 批量更新所有记录
python mods_manager.py batch_write env "客户端"

# 带条件批量更新
python mods_manager.py batch_write env "服务端" --where "filename LIKE '%server%'"
```

#### 6. info - 查看字段
显示当前数据库的所有字段。

```bash
python mods_manager.py info
```

#### 7. delete_field - 删除字段
删除指定的自定义字段（核心字段无法删除）。

```bash
python mods_manager.py delete_field old_field
```

#### 8. rename_field - 重命名字段
重命名现有字段。

```bash
python mods_manager.py rename_field old_name new_name
```

#### 9. search - 搜索功能
在指定字段中搜索目标值。

```bash
# 模糊搜索
python mods_manager.py search filename "JEI"

# 精确搜索
python mods_manager.py search env "'客户端'"

# 正则表达式搜索
python mods_manager.py search filename "^[A-Z].*Mod$" -r
```

#### 10. backup - 备份与恢复
数据库备份和恢复功能。

```bash
# 备份数据库（使用默认路径 ../docs/bak/）
python mods_manager.py backup --save

# 备份到指定目录
python mods_manager.py backup --save --dir "D:\backups"

# 从备份恢复（会自动选择最新备份）
python mods_manager.py backup --load

# 从指定目录恢复
python mods_manager.py backup --load --dir "D:\backups"
```

**参数说明**：
- `--save, -s`: 保存数据库备份（必需参数，与--load互斥）
- `--load, -l`: 从备份恢复数据库（必需参数，与--save互斥）
- `--dir, -d`: 自定义备份目录路径（可选，默认：数据库同目录下的bak文件夹）

#### 11. export - 导出CSV
将数据库表导出为CSV文件。

```bash
# 使用默认设置导出（默认导出files表到 ../docs/mods_metadata.csv）
python mods_manager.py export

# 导出到指定路径
python mods_manager.py export --dir "D:\exports\mods_data.csv"

# 导出指定表名
python mods_manager.py export --table files

# 组合使用：导出指定表到指定路径
python mods_manager.py export -d "D:\exports\custom.csv" -t files
```

**参数说明**：
- `--dir, -d`: 指定导出路径（默认：../docs/mods_metadata.csv）
- `--table, -t`: 指定要导出的表名（默认：files）

**输出格式**：
- 使用UTF-8 BOM编码，确保Excel正确打开
- CSV列标题：编号,名称,环境,标签,描述（针对files表）
- 自动处理包含逗号的字段，使用双引号包围
- 自动创建输出目录（如果不存在）

## 使用场景示例

### 场景 1：建立模组数据库
```bash
# 1. 同步所有模组文件
python mods_manager.py sync

# 或者在自动化脚本中使用
python mods_manager.py sync --force

# 2. 添加自定义字段
python mods_manager.py add_field env
python mods_manager.py add_field tags
python mods_manager.py add_field description

# 3. 检查哪些文件需要填写环境信息
python mods_manager.py check env
```

### 场景 2：分类管理模组
```bash
# 1. 批量标记为客户端模组
python mods_manager.py batch_write env "客户端" --where "filename LIKE '%-client.jar'"

# 2. 搜索特定类型的模组
python mods_manager.py search env "客户端"

# 3. 更新特定模组的标签
python mods_manager.py update 1a2b3c4d "tools, automation"
```

### 场景 3：模组维护
```bash
# 1. 同步检查新增文件
python mods_manager.py sync

# 2. 搜索特定模组
python mods_manager.py search description "Create"

# 3. 更新字段名称
python mods_manager.py rename_field env environment
```

### 场景 4：数据备份与恢复
```bash
# 1. 定期备份数据库
python mods_manager.py backup --save

# 2. 导出到CSV进行数据分析
python mods_manager.py export --dir "monthly_report.csv"

# 3. 恢复之前的备份（如有需要）
python mods_manager.py backup --load
```

### 场景 5：多人协作与数据共享
```bash
# 1. 导出最新的模组列表为CSV
python mods_manager.py export --dir "shared/mods_list.csv"

# 2. 团队成员编辑CSV文件（在Excel中）

# 3. 使用update_from_modlist.py批量更新数据库
python update_from_modlist.py
```

## 数据库结构

### 核心字段（不可删除）
- `sha`: 文件的 SHA256 哈希值（主键）
- `filename`: 文件名
- `filepath`: 完整文件路径
- `created_at`: 记录创建时间

### 自定义字段示例
- `env`: 运行环境（客户端/服务端/双端）
- `tags`: 标签（用逗号分隔）
- `description`: 模组描述
- `author`: 作者
- `version`: 版本号

## 注意事项

1. **SHA 前缀匹配**：使用 update 命令时，SHA 前缀必须唯一，建议使用前 8 位以上。

2. **批量操作确认**：所有批量操作都需要输入 'yes' 确认，防止误操作。

3. **字段命名**：字段名应为英文，避免使用 SQL 关键字。

4. **正则表达式**：搜索功能支持正则表达式，注意语法正确性。

5. **数据库备份**：重要数据建议定期备份数据库文件。

## 常见问题

### Q: 如何查看数据库文件位置？
A: 数据库文件路径在脚本开头的 `DB_NAME` 变量中定义，默认为 `../docs/mods_metadata.db`。

### Q: 批量操作失败了怎么办？
A: 批量操作有事务保护，失败时会自动回滚，不会影响数据完整性。

### Q: 如何处理重复的模组文件？
A: 系统使用 SHA256 哈希值唯一标识文件，即使文件名不同，内容相同的文件也会有相同的 SHA 值。

### Q: 可以在多个文件夹中使用同一个数据库吗？
A: 不建议。每个数据库应该对应一个特定的模组文件夹，避免混淆。

### Q: 正则表达式搜索如何使用？
A: 使用 `-r` 参数启用正则表达式模式，支持标准的 Python 正则表达式语法。

## 更新日志

- **v1.0**: 基础文件同步和字段管理功能
- **v1.1**: 添加搜索功能，支持正则表达式
- **v1.2**: 添加字段重命名和删除功能
- **v1.3**: 优化批量操作的用户体验
- **v1.4**: 添加数据库备份与恢复功能
- **v1.5**: 添加CSV导出功能，支持Excel兼容格式
- **v1.6**: 为sync命令添加--force参数，支持自动确认删除数据库记录，适用于自动化脚本