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
```

功能：
- 检测新增文件并添加到数据库
- 检测已删除文件并询问是否清理
- 更新重命名或移动文件的路径信息

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

## 使用场景示例

### 场景 1：建立模组数据库
```bash
# 1. 同步所有模组文件
python mods_manager.py sync

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