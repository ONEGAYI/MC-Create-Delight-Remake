EntityEvents.spawned((e) => {
  // 苍蝇生成
  if (e.entity.type == "alexsmobs:fly") {
    e.cancel();
  }
  // 蜈蚣生成
  if (e.entity.type == "alexsmobs:centipede_head") {
    e.cancel();
  }
  // 轻语灵生成
  if (e.entity.type == "alexsmobs:murmur") {
    e.cancel();
  }
  // 蟑螂生成
  if (e.entity.type == "alexsmobs:cockroach") {
    e.cancel();
  }
  // 蟑螂蛋生成
  if (e.entity.type == "alexsmobs:cockroach_egg") {
    e.cancel();
  }
});
