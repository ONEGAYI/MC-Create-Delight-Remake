# 模组管理器使用指南

## 概述

本指南整合了模组管理器的详细使用方法，帮助您高效地管理和维护模组数据库。


## 模组管理器核心命令

### 基础操作

#### 1. 同步模组文件
```bash
# 扫描默认文件夹（../mods）
python scripts/mods_manager.py sync

# 扫描指定文件夹
python scripts/mods_manager.py sync --folder "D:\path\to\mods"
```

#### 2. 查看数据库结构
```bash
python scripts/mods_manager.py info
```

#### 3. 检查缺失信息
```bash
# 检查缺少环境信息的模组
python scripts/mods_manager.py check env

# 检查缺少标签的模组
python scripts/mods_manager.py check tags
```

### 字段管理

#### 1. 添加新字段
```bash
# 添加文本字段（默认类型）
python scripts/mods_manager.py add_field author

# 添加指定类型的字段
python scripts/mods_manager.py add_field rating --type INTEGER
```

#### 2. 管理现有字段
```bash
# 重命名字段
python scripts/mods_manager.py rename_field old_name new_name

# 删除自定义字段（核心字段无法删除）
python scripts/mods_manager.py delete_field field_name
```

### 更新操作

#### 1. 单个模组更新
```bash
# 使用SHA前缀更新（建议使用12位以上）
python scripts/mods_manager.py update a1b2c3d4 env "客户端"
```

#### 2. 批量更新
```bash
# 更新所有记录
python scripts/mods_manager.py batch_write env "客户端"

# 带条件的批量更新
python scripts/mods_manager.py batch_write env "服务端" --where "filename LIKE '%server%'"
```

### 搜索功能

#### 1. 模糊搜索（默认）
```bash
python scripts/mods_manager.py search filename "JEI"
```

#### 2. 精确搜索
```bash
# 使用引号包围进行精确匹配
python scripts/mods_manager.py search env "'客户端'"
```

#### 3. 正则表达式搜索
```bash
# 搜索以大写字母开头并以Mod结尾的文件
python scripts/mods_manager.py search filename "^[A-Z].*Mod$" -r
```

### 数据管理

#### 1. 备份数据库
```bash
# 备份到默认位置
python scripts/mods_manager.py backup --save

# 备份到指定目录
python scripts/mods_manager.py backup --save --dir "D:\backups"
```

#### 2. 恢复数据库
```bash
# 从最新备份恢复
python scripts/mods_manager.py backup --load

# 从指定目录恢复
python scripts/mods_manager.py backup --load --dir "D:\backups"
```

#### 3. 导出CSV
```bash
# 导出默认表到默认位置
python scripts/mods_manager.py export

# 导出到指定路径
python scripts/mods_manager.py export --dir "D:\exports\mods.csv"

# 导出指定表
python scripts/mods_manager.py export --table files
```

## 实用脚本说明

### 1. check_missing_fields.py
- **功能**：检查数据库中缺失字段的模组
- **输出**：生成缺失模组名称列表和CSV格式的报告
- **使用**：
  ```bash
  python scripts/check_missing_fields.py
  ```

### 2. reset_updated_info.py
- **功能**：重置updated_info.csv文件，准备新一轮更新
- **使用**：
  ```bash
  python scripts/reset_updated_info.py
  ```

### 3. batch_update_manager.py
- **功能**：从CSV文件批量更新模组数据库
- **特性**：
  - SHA前缀匹配
  - 占位符跳过功能
  - 干运行模式预览
  - 自动备份
- **使用**：
  ```bash
  # 预览更新（不实际执行）
  python scripts/batch_update_manager.py --dry-run

  # 执行更新
  python scripts/batch_update_manager.py
  ```

## 常见使用场景

### 场景1：首次建立模组数据库
```bash
# 1. 同步所有模组
python scripts/mods_manager.py sync

# 2. 添加必要字段
python scripts/mods_manager.py add_field env
python scripts/mods_manager.py add_field tags
python scripts/mods_manager.py add_field description

# 3. 查看需要建档的模组
python scripts/check_missing_fields.py
```

### 场景2：批量更新模组信息
```bash
# 1. 重置更新文件
python scripts/reset_updated_info.py

# 2. 填写updated_info.csv
# 3. 执行批量更新
python scripts/batch_update_manager.py
```

### 场景3：维护和查询
```bash
# 1. 同步检查新文件
python scripts/mods_manager.py sync

# 2. 搜索特定模组
python scripts/mods_manager.py search description "Create"

# 3. 导出数据进行分析
python scripts/mods_manager.py export
```

## 最佳实践

1. **定期备份**：每次重要操作前都要备份数据库
2. **使用SHA前缀**：更新时使用12位以上SHA前缀确保唯一性
3. **批量确认**：批量操作前使用干运行模式预览
4. **字段命名**：使用英文字段名，避免SQL关键字
5. **信息验证**：确保搜集的信息准确可靠

## 注意事项

- SHA前缀匹配要求唯一，建议使用12位以上
- 批量操作需要输入 'yes' 确认
- 字段名应避免使用SQL关键字
- 重要操作前务必备份数据库
- 搜集模组信息时，确保信息来源可靠