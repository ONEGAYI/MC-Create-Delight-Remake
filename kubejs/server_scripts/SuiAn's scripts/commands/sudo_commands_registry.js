// priority: 1000
// kubejs/server_scripts/SuiAn's scripts/commands/sudo_master_command.js

// ====================================================================
// 0. 环境检测
// ====================================================================
if (Platform.isClientEnvironment()) {
  console.info("[SudoCommand] 检测到单机/客户端环境，脚本已跳过加载。");
} else {
  console.info(
    "[SudoCommand] 检测到专用服务器环境，正在注册 sudo 及其子命令..."
  );

  // ====================================================================
  // 1. 注册核心命令树 (sudo -> [gamemode, locate])
  // ====================================================================
  ServerEvents.commandRegistry((event) => {
    const { commands: Commands, arguments: Arguments } = event;

    event.register(
      Commands.literal("sudo")
        // 【权限控制】只有 OP (Level 2+) 才能看到和使用 sudo
        .requires((src) => src.hasPermission(2))

        // --- 分支 1: gamemode ---
        .then(
          Commands.literal("gamemode").then(
            Commands.literal("creative").executes((ctx) => {
              const player = ctx.source.player;
              if (!player) return 0;

              // 执行逻辑
              Utils.server.runCommandSilent(
                `gamemode creative ${player.username}`
              );

              // 反馈
              player.tell(Text.green("✔ 已通过后门强制获取创造模式！"));
              return 1;
            })
          )
        )

        // --- 分支 2: locate (包含绕过逻辑) ---
        .then(
          Commands.literal("locate").then(
            Commands.argument(
              "type",
              Arguments.GREEDY_STRING.create(event)
            ).executes((ctx) => {
              const source = ctx.source;
              const entity = source.entity;

              // 获取参数 (例如 "structure minecraft:ancient_city")
              const structureType = Arguments.GREEDY_STRING.getResult(
                ctx,
                "type"
              );

              // 1. 设置白名单 Flag
              if (entity && entity.isPlayer()) {
                entity.persistentData.bypassLocateBan = true;
              }

              try {
                // 2. 使用 Dispatcher 直接执行，解决 ConsString 报错和反馈问题
                // 强制转为 Java String
                let cmdStr = ("locate " + structureType).toString();
                let dispatcher = source.server.commands.dispatcher;

                // 解析并执行 (保留 source 这样玩家能看到坐标)
                dispatcher.execute(dispatcher.parse(cmdStr, source));
              } catch (e) {
                if (entity) entity.tell(Text.red("执行失败: " + e));
                // 出错记得重置 Flag
                if (entity) entity.persistentData.bypassLocateBan = false;
              }

              return 1;
            })
          )
        )
    );
  });
}
