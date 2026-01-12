// /**
//  * @format
//  * 覆盖 Create Ender Transmission 模组包中的 AE2 处理器配方
//  */

// ServerEvents.recipes((event) => {
//   const { create } = event.recipes;

//   // 新配方：产出24个赛特斯石英晶体 + 8个赛特斯石英晶体（50%概率）
//   // 必须让配方id比较靠前，才能覆盖原有配方
//   create
//     .mixing(
//       [
//         "24x ae2:certus_quartz_crystal",
//         Item.of("ae2:certus_quartz_crystal", 8).withChance(0.5),
//       ],
//       [
//         Fluid.water(500),
//         "8x ae2:certus_quartz_dust",
//         "8x ae2:charged_certus_quartz_crystal",
//       ]
//     )
//     .id("create:compat/mixing/amend_certus_quartz_crystal");
// });
