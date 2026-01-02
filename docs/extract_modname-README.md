# 模组名称批量提取工具说明

## 概述

`extract_modname.py` 是一个用于从 Minecraft 模组 JAR 文件中批量提取模组名称并更新数据库的工具。它采用双来源策略：优先从 JAR 文件内部的元数据读取，失败时降级使用文件名规则提取。

## 功能特性

### 双来源提取策略

1. **JAR 元数据读取（首选）**
   - 读取 JAR 文件根目录的 `pack.mcmeta` 文件
   - 解析 `pack.description` 字段获取模组名称
   - 支持 JSON 文本组件格式：`{'text': 'xxx'}`
   - 自动过滤占位符（如 `${mod_name}`）

2. **文件名规则提取（降级）**
   - 使用正则表达式从文件名中提取模组名称
   - 移除版本号（如 `1.20.1`, `5.2`）
   - 移除加载器标识（`forge`, `fabric`, `neoforge`, `quilt`）
   - 移除 MC 版本（如 `MC_1.20.1`）

### 智能占位符过滤

工具会自动识别并过滤以下通用占位符：
- `examplemod` / `example mod`
- `mod resources` / `examplemod resources`
- `mod` / `resources`
- `minecraft mod`

### 数据安全

- 执行前自动备份数据库
- 支持 `--dry-run` 预览模式
- 交互式确认机制
- 详细的统计报告

## 使用方法

### 基本语法

```bash
python scripts/extract_modname.py [选项]
```

### 命令行选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--db <路径>` | 数据库文件路径 | `../docs/mods_metadata.db` |
| `--mods <路径>` | 模组文件夹路径 | `../mods` |
| `--dry-run` | 预览模式，不实际更新 | - |
| `--force` | 跳过确认直接执行 | - |
| `--no-backup` | 跳过数据库备份（不推荐） | - |

### 使用示例

#### 1. 预览模式（推荐先执行）

查看将要提取的 modname，不实际更新数据库：

```bash
python scripts/extract_modname.py --dry-run
```

#### 2. 交互式执行

预览后确认执行（需要手动输入 `yes`）：

```bash
python scripts/extract_modname.py
```

#### 3. 自动执行

跳过确认直接执行：

```bash
python scripts/extract_modname.py --force
```

或通过管道输入确认：

```bash
echo yes | python scripts/extract_modname.py
```

#### 4. 自定义路径

指定数据库和模组文件夹路径：

```bash
python scripts/extract_modname.py --db custom.db --mods "D:\path\to\mods"
```

## 执行流程

1. **初始化检查**
   - 验证数据库文件存在
   - 初始化 AssetManager

2. **预览展示**
   - 显示测试用例的提取结果
   - 📦 表示从 JAR 读取
   - 📝 表示从文件名提取

3. **用户确认**
   - 非预览模式需要输入 `yes` 确认
   - `--force` 参数可跳过确认

4. **数据库备份**
   - 自动备份到 `docs/backups/`
   - 文件名格式：`mods_metadata_backup_YYYYMMDD_HHMMSS.db`

5. **批量提取更新**
   - 遍历所有数据库记录
   - 显示实时进度

6. **生成报告**
   - 总记录数
   - 成功更新数
   - 数据来源统计（JAR / 文件名）
   - 成功率和 JAR 读取率

## 输出示例

### 预览输出

```
提取预览:
--------------------------------------------------------------------------------
📦 = 从 JAR pack.mcmeta 读取
📝 = 从文件名规则提取
--------------------------------------------------------------------------------
AlwaysEat-5.2.jar                                       => AlwaysEat                                📦
supplementaries-1.20-3.1.37.jar                         => Supplementaries                          📦
konkrete_forge_1.8.0_MC_1.20-1.20.1.jar                => konkrete                                 📝
kubejs-forge-2001.6.5-build.16.jar                      => KubeJS                                   📦
--------------------------------------------------------------------------------
```

### 统计报告

```
================================================================================
批量更新统计报告
================================================================================
总记录数:          349
成功更新:          349
从 JAR 读取:       301 📦
从文件名提取:      48 📝
更新失败:          0
成功率:            100.0%
JAR 读取率:        86.2%
```

## 文件名提取规则

### 支持的命名格式

| 文件名示例 | 提取结果 |
|-----------|---------|
| `AlwaysEat-5.2.jar` | `AlwaysEat` |
| `supplementaries-1.20-3.1.37.jar` | `supplementaries` |
| `kubejs-forge-2001.6.5-build.16.jar` | `kubejs` |
| `konkrete_forge_1.8.0_MC_1.20-1.20.1.jar` | `konkrete` |
| `drippyloadingscreen_forge_3.0.12_MC_1.20.1.jar` | `Drippy Loading Screen` |

### 清理规则

1. **移除版本号**
   - `5.2`, `1.20.1`, `2001.6.5` 等数字版本号
   - `build.10`, `alpha3.0.1` 等构建标识

2. **移除加载器**
   - `forge`, `fabric`, `neoforge`, `quilt`

3. **移除 MC 版本**
   - `MC_1.20.1`, `mc1.20.1`

4. **清理后缀**
   - `-build`, `-rc`, `-beta`, `-alpha`
   *`-v1.2.3`, `-hotfix`

## 常见问题

### Q: 为什么有些模组从文件名提取而不是 JAR？

**A:** 可能的原因：
- JAR 文件中没有 `pack.mcmeta` 文件
- `pack.mcmeta` 中的 description 是占位符
- description 包含模板变量（如 `${mod_name}`）
- JAR 文件不存在或损坏

### Q: 如何确认更新结果？

**A:** 使用 modname 字段查询数据库：

```bash
python scripts/mods_manager.py search modname "konkrete"
```

### Q: 如何恢复到更新前的状态？

**A:** 从备份文件恢复：

```bash
python scripts/mods_manager.py backup --load --dir "docs/backups"
```

### Q: JAR 读取率较低怎么办？

**A:** 这是正常现象。许多模组使用通用的 `pack.mcmeta` 模板，导致 description 为占位符。文件名提取作为降级方案能保证 100% 的提取成功率。

## 技术细节

### JAR 元数据读取

```python
# pack.mcmeta 文件格式示例
{
    "pack": {
        "description": "模组名称",  # 直接字符串
        "pack_format": 8
    }
}

# 或 JSON 文本组件格式
{
    "pack": {
        "description": {"text": "模组名称"},  # 文本组件
        "pack_format": 8
    }
}
```

### 占位符检测正则

```python
GENERIC_PATTERNS = [
    r'^examplemod$',
    r'^example\s+mod$',
    r'^examplemod\s+resources?$',
    r'^mod\s*resources?$',
    r'^mod$',
    r'^resources$',
    r'^minecraft\s+mod$',
]
```

### 版本号匹配正则

```python
VERSION_PATTERNS = [
    r'^\d+\.\d+',           # 5.2, 1.20.1
    r'^\d+$',                # 纯数字
    r'^mc\d',                # mc1.20.1
    r'^MC\d',                # MC1.20.1
    r'^r\d+',                # r5.5.1
    r'^\d+\.\d+\.\d+',       # 1.2.3
]
```

## 相关文件

- `scripts/extract_modname.py` - 主脚本
- `scripts/mods_manager.py` - 模组管理器
- `docs/mods_metadata.db` - 模组数据库
- `docs/backups/` - 数据库备份目录
- `docs/how-to-use-mods-manager.md` - 模组管理器使用指南

## 更新日志

### v1.0.0 (2026-01-02)
- 初始版本
- 实现 JAR pack.mcmeta 读取功能
- 实现文件名规则提取降级方案
- 支持占位符过滤
- 支持预览模式和自动备份

### v1.1.0 (2026-01-02)
- 优化占位符检测逻辑
- 使用正则表达式模式匹配
- 在清理后缀前后都进行检查
- 修复 `examplemod resources` 类占位符未被过滤的问题

## 最佳实践

1. **首次使用**：先用 `--dry-run` 预览效果
2. **定期备份**：重要操作前确保有备份
3. **验证结果**：更新后抽查几个模组的 modname
4. **增量更新**：新增模组后可重新运行，不会影响已有数据
