// kubejs/server_scripts/SuiAn's scripts/commands/ban_locate_command.js

// ====================================================================
// 0. 环境检测
// ====================================================================
if (Platform.isClientEnvironment()) {
    console.info("[LocateBlock] 检测到单机/客户端环境，脚本已跳过加载。");
} else {
    console.info("[LocateBlock] 检测到专用服务器环境，正在启用 locate 命令拦截器...");

    // 2. 拦截普通指令
    ServerEvents.command((event) => {
        let input = event.input.trim();
        let command = input.toLowerCase();
        let banPattern = /^locate(\s|$)/;

        if (banPattern.test(command)) {
            let entity = event.parseResults.context.source.entity;

            if (entity && entity.isPlayer()) {
                // 检查 flag
                if (entity.persistentData.bypassLocateBan) {
                    entity.persistentData.bypassLocateBan = false;
                    return; // 放行
                }

                // 拦截
                let jsonMessage = JSON.stringify([
                    "",
                    { text: "❌ locate 命令已禁用，请自行探索或使用罗盘！", color: "red" }
                ]);
                Utils.server.runCommandSilent(`tellraw ${entity.username} ${jsonMessage}`);
                Utils.server.runCommandSilent(`playsound entity.villager.no master ${entity.username} ~ ~ ~ 1 1`);
                event.cancel();
            }
        }
    });
}