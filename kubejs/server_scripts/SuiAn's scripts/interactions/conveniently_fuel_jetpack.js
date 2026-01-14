// ==================== 常量定义 ====================
// 统一的日志前缀
const LOG_PREFIX = "[JetpackFuel]";
// Debug 模式开关（设为 true 启用日志输出）
const debugMode = false;
// 基础容量和每级扩容增量
const BASE_AIR = 1800;
const INCREASE_AIR_PER_LVL = 300;

// ==================== 顶部定义 ====================
const $JetpackCuriosApi = Java.loadClass(
  "top.theillusivec4.curios.api.CuriosApi"
);
const $ForgeRegistries = Java.loadClass(
  "net.minecraftforge.registries.ForgeRegistries"
);

/**
 * 获取玩家拥有的喷气背包详细信息
 */
function getJetpackInfo(player) {
  if (!player) return null;

  const targetIds = [
    "create_jetpack:netherite_jetpack",
    "create_jetpack:jetpack",
  ];

  const result = {
    netherite_jetpack: {
      itemId: "create_jetpack:netherite_jetpack",
      items: [],
    },
    jetpack: { itemId: "create_jetpack:jetpack", items: [] },
    totalCount: 0,
  };

  // 【关键修复】所有中间变量全部在最外层声明，防止循环内重复声明报错
  let handler,
    curiosMap,
    stackHandler,
    i,
    rawStack,
    itemDef,
    rawId,
    isTarget,
    ti,
    targetKey,
    curioStack;
  let inventory, invStack, currentId, location;

  // ---------------------------------------------------------
  // 1. 扫描饰品栏
  // ---------------------------------------------------------
  $JetpackCuriosApi.getCuriosInventory(player).ifPresent((h) => {
    handler = h;
    curiosMap = handler.getCurios();

    if (debugMode) console.log(LOG_PREFIX + " [DEBUG] 开始扫描Curios饰品栏");

    curiosMap.forEach((slotIdentifier, stacksHandler) => {
      stackHandler = stacksHandler.getStacks();

      for (i = 0; i < stackHandler.getSlots(); i++) {
        // 【修复】只赋值，不声明
        rawStack = stackHandler.getStackInSlot(i);

        if (rawStack && rawStack.getCount() > 0) {
          try {
            // 【修复】使用 Forge 注册表安全获取 ID (解决服务端 PoseStack 报错)
            itemDef = rawStack.getItem();
            rawId = $ForgeRegistries.ITEMS.getKey(itemDef).toString();
          } catch (e) {
            if (debugMode)
              console.log(LOG_PREFIX + " [ERROR] 获取ID失败: " + e);
            continue;
          }

          if (debugMode)
            console.log(LOG_PREFIX + " [DEBUG] Curios物品: " + rawId);

          // 匹配逻辑
          isTarget = false;
          for (ti = 0; ti < targetIds.length; ti++) {
            if (
              rawId === targetIds[ti] ||
              (rawId.indexOf("netherite_jetpack") >= 0 &&
                targetIds[ti].indexOf("netherite_jetpack") >= 0) ||
              (rawId.indexOf(":jetpack") >= 0 &&
                rawId.indexOf("netherite") < 0 &&
                targetIds[ti] === "create_jetpack:jetpack")
            ) {
              isTarget = true;
              break;
            }
          }

          if (isTarget) {
            try {
              curioStack = Item.of(rawStack);
              targetKey =
                rawId.indexOf("netherite_jetpack") >= 0
                  ? "netherite_jetpack"
                  : "jetpack";

              if (debugMode) {
                console.log(
                  LOG_PREFIX +
                    " [DEBUG] 找到喷气背包: " +
                    targetKey +
                    ", 槽位: " +
                    slotIdentifier +
                    ", 索引: " +
                    i
                );
              }

              result[targetKey].items.push({
                location: "curios",
                slotId: slotIdentifier,
                slotIndex: i,
                nbt: curioStack.nbt,
                stack: curioStack,
              });
              result.totalCount++;
            } catch (e) {
              if (debugMode)
                console.log(LOG_PREFIX + " [ERROR] 转换物品失败: " + e);
            }
          }
        }
      }
    });

    if (debugMode)
      console.log(
        LOG_PREFIX +
          " [DEBUG] Curios扫描完成，总计: " +
          result.totalCount +
          "个"
      );
  });

  // ---------------------------------------------------------
  // 2. 扫描物品栏
  // ---------------------------------------------------------
  inventory = player.inventory;

  for (i = 0; i < inventory.getContainerSize(); i++) {
    // 【修复】只赋值，不声明
    invStack = inventory.getItem(i);

    if (invStack && !invStack.isEmpty()) {
      currentId = invStack.id;

      // 这里可以直接用 KubeJS 的 ID，因为它已经封装好了
      if (targetIds.indexOf(currentId) >= 0) {
        location = i < 9 ? "hotbar" : "inventory";
        targetKey =
          currentId === "create_jetpack:netherite_jetpack"
            ? "netherite_jetpack"
            : "jetpack";

        result[targetKey].items.push({
          location: location,
          slotIndex: i,
          nbt: invStack.nbt,
          stack: invStack,
        });
        result.totalCount++;
      }
    }
  }

  return result;
}

/**
 * 获取喷气背包的容量信息
 * @param {Item} jetpackItem - 喷气背包物品
 * @returns {Object} 包含当前空气、最大容量、扩容等级
 */
function getJetpackCapacity(jetpackItem) {
  var nbt = jetpackItem.nbt;
  if (!nbt) {
    nbt = {};
  }

  var air = Number(nbt.Air || 0);

  // 获取扩容附魔等级
  var capacityLvl = 0;

  // 尝试多种方式获取附魔数据
  if (nbt.Enchantments) {
    var enchantments = nbt.Enchantments;
    if (debugMode) {
      console.log("[JetpackFuel] [DEBUG] 附魔数据: " + String(enchantments));
    }

    for (var i = 0; i < enchantments.length; i++) {
      var ench = enchantments[i];
      var enchId = ench.id || ""; // 防止空值

      if (debugMode) {
        console.log(
          "[JetpackFuel] [DEBUG] 检查附魔: id=" +
            String(enchId) +
            ", lvl=" +
            ench.lvl
        );
      }

      // 尝试匹配多种可能的ID格式
      if (
        String(enchId).indexOf("capacity") >= 0 ||
        String(enchId).indexOf(" Capacity") >= 0 ||
        String(enchId) === "create_jetpack:capacity"
      ) {
        capacityLvl = Number(ench.lvl);
        if (debugMode) {
          console.log(
            "[JetpackFuel] [DEBUG] 找到扩容附魔，等级: " + capacityLvl
          );
        }
        break;
      }
    }
  } else if (debugMode) {
    console.log("[JetpackFuel] [DEBUG] 没有附魔数据");
  }

  var maxAir = BASE_AIR + capacityLvl * INCREASE_AIR_PER_LVL;

  if (debugMode) {
    console.log(
      "[JetpackFuel] [DEBUG] 容量信息: 当前=" +
        air +
        ", 最大=" +
        maxAir +
        ", 扩容等级=" +
        capacityLvl
    );
  }

  return {
    air: air,
    maxAir: maxAir,
    needAir: maxAir - air,
    capacityLvl: capacityLvl,
  };
}

/**
 * 更新物品栏中的喷气背包NBT
 * @param {Player} player - 玩家
 * @param {Object} jetpackInfo - 喷气背包信息
 * @param {number} newAir - 新的空气值
 */
function updateJetpackInInventory(player, jetpackInfo, newAir) {
  var inventory = player.inventory;

  if (jetpackInfo.location === "curios") {
    // 更新饰品栏中的喷气背包
    $JetpackCuriosApi.getCuriosInventory(player).ifPresent(function (handler) {
      var curiosMap = handler.getCurios();
      var stackHandler;
      var rawStack;
      var rawId;
      var updatedStack;
      var slotIdentifier;
      var stacksHandler;
      var i;

      // 遍历curios条目
      var curiosKeys = curiosMap.keySet().toArray();
      for (var c = 0; c < curiosKeys.length; c++) {
        slotIdentifier = curiosKeys[c];
        stacksHandler = curiosMap.get(slotIdentifier);
        stackHandler = stacksHandler.getStacks();

        // 匹配槽位标识符（使用字符串比较）
        if (String(slotIdentifier) !== String(jetpackInfo.slotId)) {
          continue;
        }

        for (i = 0; i < stackHandler.getSlots(); i++) {
          // 匹配槽位索引
          if (i !== jetpackInfo.slotIndex) {
            continue;
          }

          rawStack = stackHandler.getStackInSlot(i);

          if (rawStack && !rawStack.isEmpty()) {
            rawId = rawStack.getItem().toString();

            // 使用与getJetpackInfo相同的匹配逻辑
            var isMatch =
              (rawId.indexOf("netherite_jetpack") >= 0 &&
                jetpackInfo.stack.id.indexOf("netherite_jetpack") >= 0) ||
              (rawId.indexOf(":jetpack") >= 0 &&
                rawId.indexOf("netherite") < 0 &&
                jetpackInfo.stack.id.indexOf("jetpack") >= 0);

            if (isMatch) {
              // 找到目标物品，使用KubeJS方式更新NBT
              if (debugMode) {
                console.log(
                  "[JetpackFuel] [DEBUG] 找到目标，开始更新: 槽位=" +
                    slotIdentifier +
                    ", 索引=" +
                    i +
                    ", 新Air=" +
                    newAir
                );
              }

              // 使用KubeJS的Item.withNBT方法创建新物品
              var currentItem = Item.of(rawStack);
              if (debugMode) {
                console.log("[JetpackFuel] [DEBUG] currentItem创建");
              }

              // 获取当前NBT并修改
              var currentNbt = currentItem.nbt || {};
              currentNbt.Air = newAir;
              if (debugMode) {
                console.log(
                  "[JetpackFuel] [DEBUG] NBT修改: Air=" + currentNbt.Air
                );
              }

              // 创建带新NBT的物品
              var newItem = Item.of(rawStack.getId()).withNBT(currentNbt);
              if (debugMode) {
                console.log("[JetpackFuel] [DEBUG] newItem创建: " + newItem);
              }

              // 使用Curios API设置物品
              var result = stackHandler.setStackInSlot(i, newItem);
              if (debugMode) {
                console.log(
                  "[JetpackFuel] [DEBUG] setStackInSlot结果: " + result
                );
              }
              return;
            }
          }
        }
      }

      if (debugMode) {
        console.log("[JetpackFuel] [DEBUG] 未找到匹配的Curios物品进行更新");
      }
    });
  } else {
    // 更新物品栏中的喷气背包（避免重复声明变量）
    var currentStack = inventory.getItem(jetpackInfo.slotIndex);

    if (currentStack && currentStack.id === jetpackInfo.stack.id) {
      var updatedStack = Item.of(currentStack);
      updatedStack.nbt.Air = newAir;
      inventory.setItem(jetpackInfo.slotIndex, updatedStack);
    }
  }
}

// ==================== 事件监听 ====================
// 功能概述：玩家空手潜行右键背罐，从背罐提取气体为喷气背包充能
// 逻辑链条：
// 1. 检测玩家是否空手且潜行右键背罐
// 2. 检测玩家是否拥有至少一个非满喷气背包
// 3. 获取背罐信息：位置、NBT（剩余气体）、附魔（有个"扩容"附魔可以提升容量）
// 4. 遍历所有喷气背包，尝试从背罐中提取气体进行充能
// 5. 更新物品NBT并反馈粒子效果

BlockEvents.rightClicked("create:netherite_backtank", (event) => {
  const { player, block, level, server } = event;

  // 1. 检测玩家是否空手且潜行右键背罐
  if (event.hand !== "MAIN_HAND") return;
  if (!player.shiftKeyDown) return;
  if (player.mainHandItem.id !== "minecraft:air") return;

  player.swing();

  // 2. 检测玩家是否拥有至少一个非满喷气背包
  const jetpackInfo = getJetpackInfo(player);
  if (!jetpackInfo || jetpackInfo.totalCount === 0) {
    if (debugMode) {
      console.log(`${LOG_PREFIX} 玩家 ${player.name} 没有喷气背包`);
    }
    return;
  }

  // 收集所有需要充能的喷气背包（Rhino兼容：不用扩展运算符）
  const allJetpacks = [];
  var netheriteItems = jetpackInfo.netherite_jetpack.items;
  for (var i = 0; i < netheriteItems.length; i++) {
    allJetpacks.push(netheriteItems[i]);
  }
  var jetpackItems = jetpackInfo.jetpack.items;
  for (var j = 0; j < jetpackItems.length; j++) {
    allJetpacks.push(jetpackItems[j]);
  }

  // 过滤出非满的喷气背包（Rhino兼容：不用箭头函数）
  var needRefuelJetpacks = [];
  for (var k = 0; k < allJetpacks.length; k++) {
    var jp = allJetpacks[k];
    var capacity = getJetpackCapacity(jp.stack);
    if (capacity.needAir > 0) {
      needRefuelJetpacks.push(jp);
    }
  }

  if (needRefuelJetpacks.length === 0) {
    if (debugMode) {
      console.log(`${LOG_PREFIX} 玩家 ${player.name} 的所有喷气背包已满`);
    }
    player.tell("§e你的喷气背包已经充满了！");
    return;
  }

  // 3. 获取背罐信息
  var tankData = block.entityData;
  var tankTag = tankData.get("VanillaTag");
  var tankAir = Number(tankData.get("Air"));
  var tankPos = [block.pos.x, block.pos.y, block.pos.z];
  var tankState = String(block.properties).replace("{", "[").replace("}", "]");

  if (tankAir <= 0) {
    player.tell("§c这个背罐是空的！");
    return;
  }

  if (debugMode) {
    console.log(`${LOG_PREFIX} ===== 开始充能 =====`);
    console.log(`${LOG_PREFIX} 玩家: ${player.name}`);
    console.log(`${LOG_PREFIX} 背罐剩余空气: ${tankAir}`);
    console.log(
      `${LOG_PREFIX} 需要充能的喷气背包: ${needRefuelJetpacks.length}个`
    );
  }

  // 4. 遍历所有喷气背包，尝试从背罐中提取气体进行充能
  let needPlayParticle = false;
  let totalTransferred = 0;

  for (const jetpackData of needRefuelJetpacks) {
    if (tankAir <= 0) break;

    const capacity = getJetpackCapacity(jetpackData.stack);
    let transferAmount = Math.min(capacity.needAir, tankAir);

    if (transferAmount > 0) {
      // 计算新的空气值
      const newJetpackAir = capacity.air + transferAmount;
      tankAir -= transferAmount;
      totalTransferred += transferAmount;

      // 5. 更新物品NBT
      updateJetpackInInventory(player, jetpackData, newJetpackAir);

      needPlayParticle = true;

      if (debugMode) {
        const locName =
          jetpackData.location === "curios"
            ? "饰品"
            : jetpackData.location === "hotbar"
            ? "快捷"
            : "背包";
        console.log(
          `${LOG_PREFIX} [${locName}] 充能: ${capacity.air} -> ${newJetpackAir} (转移${transferAmount})`
        );
      }
    }
  }

  // 更新背罐的NBT（使用setblock命令）
  tankData = tankData
    .merge("{Air: " + tankAir + "}")
    .merge(tankTag.merge("{Air: " + tankAir + "}"));
  server.runCommandSilent(
    "setblock " +
      tankPos[0] +
      " " +
      tankPos[1] +
      " " +
      tankPos[2] +
      " air replace"
  );
  server.runCommandSilent(
    "setblock " +
      tankPos[0] +
      " " +
      tankPos[1] +
      " " +
      tankPos[2] +
      " " +
      block.id +
      tankState +
      tankData +
      " replace"
  );

  // 反馈信息
  if (totalTransferred > 0) {
    player.tell(`§a成功为喷气背包充能 ${totalTransferred} 单位气体！`);
    if (tankAir <= 0) {
      player.tell("§e背罐已耗尽！");
    } else {
      player.tell(`§7背罐剩余: ${tankAir} 单位`);
    }
  }

  // 5. 播放粒子效果
  if (needPlayParticle) {
    const pos = block.pos;
    level.spawnParticles(
      "minecraft:campfire_cosy_smoke",
      false,
      pos.x + 0.5,
      pos.y + 0.5,
      pos.z + 0.5,
      0.2,
      0.3,
      0.2,
      20,
      0.05
    );

    // 额外的闪光效果
    level.spawnParticles(
      "minecraft:end_rod",
      false,
      pos.x + 0.5,
      pos.y + 0.25,
      pos.z + 0.5,
      0.1,
      0.1,
      0.1,
      8,
      0.02
    );
  }

  if (debugMode) {
    console.log(`${LOG_PREFIX} ===== 充能完成 =====`);
    console.log(`${LOG_PREFIX} 总转移: ${totalTransferred} 单位`);
    console.log(`${LOG_PREFIX} 背罐剩余: ${tankAir} 单位`);
  }
});

// 同时也支持铜背罐
BlockEvents.rightClicked("create:copper_backtank", (event) => {
  const { player, block, level, server } = event;

  // 1. 检测玩家是否空手且潜行右键背罐
  if (event.hand !== "MAIN_HAND") return;
  if (!player.shiftKeyDown) return;
  if (player.mainHandItem.id !== "minecraft:air") return;

  player.swing();

  // 2. 检测玩家是否拥有至少一个非满喷气背包
  const jetpackInfo = getJetpackInfo(player);
  if (!jetpackInfo || jetpackInfo.totalCount === 0) {
    if (debugMode) {
      console.log(`${LOG_PREFIX} 玩家 ${player.name} 没有喷气背包`);
    }
    return;
  }

  // 收集所有需要充能的喷气背包（Rhino兼容：不用扩展运算符）
  const allJetpacks = [];
  var netheriteItems = jetpackInfo.netherite_jetpack.items;
  for (var i = 0; i < netheriteItems.length; i++) {
    allJetpacks.push(netheriteItems[i]);
  }
  var jetpackItems = jetpackInfo.jetpack.items;
  for (var j = 0; j < jetpackItems.length; j++) {
    allJetpacks.push(jetpackItems[j]);
  }

  // 过滤出非满的喷气背包（Rhino兼容：不用箭头函数）
  var needRefuelJetpacks = [];
  for (var k = 0; k < allJetpacks.length; k++) {
    var jp = allJetpacks[k];
    var capacity = getJetpackCapacity(jp.stack);
    if (capacity.needAir > 0) {
      needRefuelJetpacks.push(jp);
    }
  }

  if (needRefuelJetpacks.length === 0) {
    if (debugMode) {
      console.log(`${LOG_PREFIX} 玩家 ${player.name} 的所有喷气背包已满`);
    }
    player.tell("§e你的喷气背包已经充满了！");
    return;
  }

  // 3. 获取背罐信息
  var tankData = block.entityData;
  var tankTag = tankData.get("VanillaTag");
  var tankAir = Number(tankData.get("Air"));
  var tankPos = [block.pos.x, block.pos.y, block.pos.z];
  var tankState = String(block.properties).replace("{", "[").replace("}", "]");

  if (tankAir <= 0) {
    player.tell("§c这个背罐是空的！");
    return;
  }

  if (debugMode) {
    console.log(`${LOG_PREFIX} ===== 开始充能 =====`);
    console.log(`${LOG_PREFIX} 玩家: ${player.name}`);
    console.log(`${LOG_PREFIX} 背罐剩余空气: ${tankAir}`);
    console.log(
      `${LOG_PREFIX} 需要充能的喷气背包: ${needRefuelJetpacks.length}个`
    );
  }

  // 4. 遍历所有喷气背包，尝试从背罐中提取气体进行充能
  let needPlayParticle = false;
  let totalTransferred = 0;

  for (const jetpackData of needRefuelJetpacks) {
    if (tankAir <= 0) break;

    const capacity = getJetpackCapacity(jetpackData.stack);
    let transferAmount = Math.min(capacity.needAir, tankAir);

    if (transferAmount > 0) {
      // 计算新的空气值
      const newJetpackAir = capacity.air + transferAmount;
      tankAir -= transferAmount;
      totalTransferred += transferAmount;

      // 5. 更新物品NBT
      updateJetpackInInventory(player, jetpackData, newJetpackAir);

      needPlayParticle = true;

      if (debugMode) {
        const locName =
          jetpackData.location === "curios"
            ? "饰品"
            : jetpackData.location === "hotbar"
            ? "快捷"
            : "背包";
        console.log(
          `${LOG_PREFIX} [${locName}] 充能: ${capacity.air} -> ${newJetpackAir} (转移${transferAmount})`
        );
      }
    }
  }

  // 更新背罐的NBT（使用setblock命令）
  tankData = tankData
    .merge("{Air: " + tankAir + "}")
    .merge(tankTag.merge("{Air: " + tankAir + "}"));
  server.runCommandSilent(
    "setblock " +
      tankPos[0] +
      " " +
      tankPos[1] +
      " " +
      tankPos[2] +
      " air replace"
  );
  server.runCommandSilent(
    "setblock " +
      tankPos[0] +
      " " +
      tankPos[1] +
      " " +
      tankPos[2] +
      " " +
      block.id +
      tankState +
      tankData +
      " replace"
  );

  // 反馈信息
  if (totalTransferred > 0) {
    player.tell(`§a成功为喷气背包充能 ${totalTransferred} 单位气体！`);
    if (tankAir <= 0) {
      player.tell("§e背罐已耗尽！");
    } else {
      player.tell(`§7背罐剩余: ${tankAir} 单位`);
    }
  }

  // 5. 播放粒子效果
  if (needPlayParticle) {
    const pos = block.pos;
    level.spawnParticles(
      "minecraft:campfire_cosy_smoke",
      false,
      pos.x + 0.5,
      pos.y + 0.5,
      pos.z + 0.5,
      0.2,
      0.3,
      0.2,
      20,
      0.05
    );

    // 额外的闪光效果
    level.spawnParticles(
      "minecraft:end_rod",
      false,
      pos.x + 0.5,
      pos.y + 0.25,
      pos.z + 0.5,
      0.1,
      0.1,
      0.1,
      8,
      0.02
    );
  }

  if (debugMode) {
    console.log(`${LOG_PREFIX} ===== 充能完成 =====`);
    console.log(`${LOG_PREFIX} 总转移: ${totalTransferred} 单位`);
    console.log(`${LOG_PREFIX} 背罐剩余: ${tankAir} 单位`);
  }
});
