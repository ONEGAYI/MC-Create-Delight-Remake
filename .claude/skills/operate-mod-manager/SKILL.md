---
name: operate-mod-manager
description: 提供操控本项目中模组管理器（mod_manager）的能力。模组管理器是帮助管理MC模组、为模组建立SQLITE数据库、提供数据库操作接口的程序。
---

# 模组管理器使用指南

## 概述

本指南整合了模组管理器的详细使用方法，帮助您高效地管理和维护模组数据库。

模组管理器位置: `../../../scripts/mods_manager.py`

## 文件结构
```
Create-Delight-Remake
├── .claude/skills/operate-mod-manager/
│   ├── SKILL.md                           # 本技能配置文件
│   └── references/
│       ├── how-to-use-mods-manager.md    # 模组管理器使用指南
│       └── mods-sqlite-info.md           # 数据库结构说明
│
├── docs/
│   └── mods_metadata.db                  # 模组元数据库 (SQLite)
│
└── scripts/
    ├── MC 整合包更新工具.bat
    ├── batch_update_manager.py           # 批量更新管理
    ├── mods_manager.py                   # 模组管理器主程序
    └── update_from_modlist.py            # 从模组列表更新
```

## 数据库概要
模组管理器主要对模组数据库进行管理，这个数据库的概要在`references/mods-sqlite-info.md`

操作数据库前，你需要前往阅读了解数据库结构

## 模组管理器核心命令

你需要查看 `../../../docs/how-to-use-mods-manager.md` 来了解模组管理器的使用方式