// kubejs/server_scripts/SuiAn's scripts/commands/ban_gamerule_command.js

// ====================================================================
// 0. 环境检测
// ====================================================================
if (Platform.isClientEnvironment()) {
    console.info("[GameruleBan] 检测到单机/客户端环境，脚本已跳过加载。");
} else {
    console.info("[GameruleBan] 检测到专用服务器环境，正在启用 gamerule 命令拦截器...");

    // ====================================================================
    // 1. 拦截 gamerule 指令
    // ====================================================================
    ServerEvents.command((event) => {
        let input = event.input.trim();
        let command = input.toLowerCase();
        let banPattern = /^gamerule(\s|$)/;

        if (banPattern.test(command)) {
            let entity = event.parseResults.context.source.entity;

            // entity 为 null 表示控制台执行，放行
            if (entity === null) {
                return;
            }

            // 玩家执行，检查 flag
            if (entity.isPlayer()) {
                if (entity.persistentData.bypassGameruleBan) {
                    entity.persistentData.bypassGameruleBan = false;
                    return; // 放行
                }

                // 拦截并提示
                let jsonMessage = JSON.stringify([
                    "",
                    { text: "❌ gamerule 命令已禁用，仅限控制台使用！", color: "red" }
                ]);
                Utils.server.runCommandSilent(`tellraw ${entity.username} ${jsonMessage}`);
                Utils.server.runCommandSilent(`playsound entity.villager.no master ${entity.username} ~ ~ ~ 1 1`);
                event.cancel();
            }
        }
    });
}
