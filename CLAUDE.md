## 注意事项
- `CLAUDE.md`, 模组列表的更新提交时只需说明更新了相关文档(文档名称)即可，不需要完整列出具体改动
- 为模组建档一定使用对应技能，并完整遵循流程，即便有建档的历史行为（除非用户要求参照之前或省略步骤）
- 没有找到模组的信息，一定要询问并告知用户，**不允许自己猜测**

## 使用脚本修改游戏

### 导出的事件、类型注册文件

执行 `/kubejs export` 后，导出数据保存在 `local/kubejs/export/`：

```
local/
├── ftbquests/              # FTB 任务数据
│   └── client-config.snbt
├── kubejs/
│   ├── event_groups/       # KubeJS 事件组数据（29种）
│   │   ├── BlockEvents         # 方块事件
│   │   ├── EntityEvents        # 实体事件
│   │   ├── ItemEvents          # 物品事件
│   │   ├── PlayerEvents        # 玩家事件
│   │   ├── ServerEvents        # 服务器事件
│   │   ├── StartupEvents       # 启动事件
│   │   ├── ClientEvents        # 客户端事件
│   │   ├── LevelEvents         # 世界事件
│   │   ├── LootJS              # 战利品表
│   │   ├── WorldgenEvents      # 世界生成
│   │   ├── NetworkEvents       # 网络事件
│   │   ├── CreateEvents        # 机械动力
│   │   ├── CustomMachineryEvents # 自定义机器
│   │   ├── FTBQuestsEvents     # FTB 任务
│   │   ├── FTBTeamsEvents      # FTB 队伍
│   │   ├── FTBChunksEvents     # FTB 小地图
│   │   ├── CuriosEvents        # 饰品栏
│   │   ├── JEIEvents           # JEI 物品栏
│   │   ├── Ponder              # 机械教学
│   │   ├── LycheeEvents        # Lychee 后处理
│   │   ├── MBDMachineEvents    # MBD 机器
│   │   ├── MBDRecipeTypeEvents # MBD 配方类型
│   │   ├── MBDRegistryEvents   # MBD 注册表
│   │   ├── MoreJSEvents        # 更多 JS
│   │   ├── CapabilityEvents    # 能力事件
│   │   ├── CDGEvents           # CDG
│   │   ├── LDLibUI             # LDL UI
│   │   ├── ProbeJSEvents       # Probe JS
│   │   └── RenderJSEvents      # 渲染事件
│   └── export/             # /kubejs export 导出数据
│       ├── added_recipes/  # KubeJS 添加的配方
│       ├── loot_tables/    # 战利品表（按模组分类）
│       ├── predicates/     # 谓词
│       ├── recipes/        # 所有配方（按模组分类）
│       ├── registries/     # 注册表数据（方块、实体、流体等）
│       ├── removed_recipes/# 被移除的配方
│       ├── tags/           # 标签数据
│       ├── errors.log      # 导出错误日志
│       └── index.json      # 配方索引文件
├── ftbchunks/              # FTB 小地图数据
└── ftbultimine-client.snbt
```

**关键文件**：
- `export/registries/entity_type.json` - 所有实体类型列表
- `export/registries/block.json` - 所有方块列表
- `export/registries/fluid.json` - 所有流体列表
- `export/tags/` - 游戏内标签（物品、方块、实体等）
- `export/errors.log` - 导出错误记录

### KubeJS 事件类型

`event_groups/` 包含 29 种事件类型：

| 事件类型 | 说明 |
|---------|------|
| `BlockEvents` | 方块事件（破坏、放置、右键等） |
| `EntityEvents` | 实体事件（生成、死亡、攻击等） |
| `ItemEvents` | 物品事件（右键、拾取、使用等） |
| `PlayerEvents` | 玩家事件（登录、登出、聊天等） |
| `ServerEvents` | 服务器事件（加载、 tick 等） |
| `StartupEvents` | 启动事件（脚本加载时） |
| `ClientEvents` | 客户端事件（渲染、 GUI 等） |
| `LevelEvents` | 世界事件（爆炸、天气等） |
| `LootJS` | 战利品表修改 |
| `WorldgenEvents` | 世界生成事件（矿石、结构等） |
| `NetworkEvents` | 网络事件 |
| `CreateEvents` | 机械动力模组事件 |
| `CustomMachineryEvents` | 自定义机器事件 |
| `FTBQuestsEvents` | FTB 任务事件 |
| `FTBTeamsEvents` | FTB 队伍事件 |
| `FTBChunksEvents` | FTB 小地图事件 |
| `CuriosEvents` | 饰品栏事件 |
| `JEIEvents` | JEI 物品栏事件 |
| `Ponder` | 机械动力教学场景 |
| `LycheeEvents` | Lychee 后处理事件 |
| `MBDMachineEvents` | MBD 机器事件 |
| `MBDRecipeTypeEvents` | MBD 配方类型事件 |
| `MBDRegistryEvents` | MBD 注册表事件 |
| `MoreJSEvents` | 更多 JS 事件 |
| `CapabilityEvents` | 能力事件 |
| `CDGEvents` | CDG 事件 |
| `LDLibUI` | LDL UI 事件 |
| `ProbeJSEvents` | Probe JS 事件 |
| `RenderJSEvents` | 渲染事件 |
