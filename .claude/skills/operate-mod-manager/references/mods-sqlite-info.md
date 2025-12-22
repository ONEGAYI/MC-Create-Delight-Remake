# 模组数据库结构文档

**注意:** 本信息具有时效性! 十分可能已经过时

## 数据库基本信息

- **数据库文件位置**: `docs/mods_metadata.db`
- **数据库类型**: SQLite
- **表名**: `files`
- **总模组数量**: 341个

## 数据库表结构

```sql
CREATE TABLE files (
    sha TEXT PRIMARY KEY,        -- 模组文件的SHA哈希值（主键）
    filename TEXT,               -- 模组文件名
    filepath TEXT,               -- 模组文件路径
    created_at TIMESTAMP,        -- 创建时间戳
    env TEXT,                    -- 环境信息（如：客户端、服务端、双端等）
    tags TEXT,                   -- 标签（如：#工具、#装饰、#食物等）
    description TEXT,            -- 模组描述
    updated_at TIMESTAMP         -- 更新时间戳
)
```

## 字段说明

### 核心字段
- **sha**: 模组文件的唯一标识符，使用SHA哈希值作为主键，用于精确识别模组文件
- **filename**: 模组文件的名称，如 `create-1.20.1-6.0.6.jar`
- **filepath**: 模组文件的相对路径，如 `../mods\create-1.20.1-6.0.6.jar`

### 时间戳字段
- **created_at**: 记录创建时间，使用TIMESTAMP格式
- **updated_at**: 记录最后更新时间，使用TIMESTAMP格式

### 信息字段
- **env**: 环境信息，用于标识模组适用的环境
  - 常见值：客户端、服务端、双端类等
- **tags**: 标签信息，用于分类和搜索
  - 格式：使用`#`前缀
  - 可以包含多个标签，用逗号分隔
  - 目前只包含: 工业自动化、库与依赖、食物与农业、装备与战斗、装饰与建筑、世界扩展、交通与运输、性能优化、界面增强、辅助工具、魔法与特殊、整合与联动
- **description**: 模组的详细描述信息

## 数据完整性

当前数据库中的所有341个模组记录都已完整填写了以下信息：
- ✅ 环境信息（env）：0个缺失
- ✅ 标签信息（tags）：0个缺失
- ✅ 描述信息（description）：0个缺失

## 使用示例

### 模组记录示例
1. **文件名**: AlwaysEat-5.2.jar
   - SHA: e416a69d...
   - 路径: ../mods\AlwaysEat-5.2.jar

2. **文件名**: supplementaries-1.20-3.1.37.jar
   - SHA: c0c4c038...
   - 路径: ../mods\supplementaries-1.20-3.1.37.jar

3. **文件名**: create-1.20.1-6.0.6.jar
   - SHA: 6cb1e5b2...
   - 路径: ../mods\create-1.20.1-6.0.6.jar

## 管理工具

数据库通过以下Python脚本进行管理：
- **管理脚本位置**: `scripts/mods_manager.py`
- **主要功能**：
  - 同步模组文件
  - 搜索模组信息
  - 更新模组记录
  - 导出数据
  - 备份和恢复数据库

## 备份信息

数据库定期备份到以下位置：
- **备份目录**: `docs/backups/` 和 `docs/bak/`
- **备份文件格式**: `mods_metadata_backup_YYYYMMDD_HHMMSS.db`
- **最新备份**: 可在备份目录中查看最近的备份文件