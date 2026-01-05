// 禁用原版生物生成
EntityEvents.spawned((e) => {
  // 幻翼生成
  if (e.entity.type == "minecraft:phantom") {
    e.cancel();
  }
});
