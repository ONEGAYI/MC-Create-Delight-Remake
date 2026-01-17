ServerEvents.recipes((e) => {
  // 砂纸打磨配方
  e.recipes.create
    .sandpaper_polishing(
      [
        Item.of("minecraft:diamond", 1), // 必得1个钻石
        Item.of("minecraft:diamond", 1).withChance(0.1), // 10%概率额外1个钻石
      ],
      "createdelight:mmd_diamond",
    )
    .id("suian:sandpaper_polishing/mmd_diamond");

  // 研磨机配方
  e.recipes.createmetallurgy.grinding(
    [
      "minecraft:diamond", // 必得1个钻石
      Item.of("minecraft:diamond").withChance(0.5), // 50%概率额外1个钻石
    ],
    "createdelight:mmd_diamond",
  ).id("suian:grinding/mmd_diamond_to_diamond");
});
