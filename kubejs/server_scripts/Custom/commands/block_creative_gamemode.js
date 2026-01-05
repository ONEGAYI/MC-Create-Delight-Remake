// kubejs/server_scripts/Custom/commands/block_creative_gamemode.js

// ====================================================================
// 0. 环境检测：使用 KubeJS 安全 API 判断环境
// ====================================================================

// Platform.isClientEnvironment() 在单机模式下返回 true，在专用服务端下返回 false
if (Platform.isClientEnvironment()) {
  // 打印一条日志提示（可选）
  console.info(
    "[GamemodeBlock] 检测到单机/客户端环境，脚本已跳过加载。"
  );

  // 直接在这里结束，不执行后续的事件注册
  // 注意：在 KubeJS 脚本顶层使用 return 有时依赖于具体 JS 引擎实现
  // 最稳妥的方式是将下面的代码包裹在 else 中，或者利用 return 阻断
} else {
  // ====================================================================
  // 文件存在，执行核心逻辑
  // ====================================================================

  console.info(
    "[GamemodeBlock] 检测到专用服务器环境，正在启用创造模式拦截器..."
  );

  // 1. 注册后门命令 (保持不变)
  ServerEvents.commandRegistry((event) => {
    const { commands: Commands } = event;
    event.register(
      Commands.literal("sudo").then(
        Commands.literal("gamemode").then(
          Commands.literal("creative").executes((ctx) => {
            const player = ctx.source.player;
            if (!player) return 0;
            // 后门执行
            Utils.server.runCommandSilent(
              `gamemode creative ${player.username}`
            );
            player.tell(Text.green("✔ 已通过后门强制获取创造模式！"));
            return 1;
          })
        )
      )
    );
  });

  // 2. 拦截普通指令 (无延迟，先报错后拦截)
  ServerEvents.command((event) => {
    // 获取输入
    let input = event.input.trim(); // 去除首尾空格
    let command = input.toLowerCase();

    // 正则匹配
    let banPattern = /^gamemode\s+(creative|c|1)(\s|$)/;

    if (banPattern.test(command)) {
      let source = event.parseResults.context.source;
      let entity = source.entity;

      // 必须是玩家，且不是由上面的 sudo 触发的
      if (entity && entity.isPlayer()) {
        // 获取玩家ID (转字符串确保安全)
        let playerName = entity.username.toString();

        // --- 构建报错文本逻辑开始 ---

        // 设置截取长度（模仿原版，只显示最后约12-15个字符）
        const maxLength = 15;
        let displayInput = input;

        // 如果命令太长，截取后半部分并在前面加 "..."
        if (input.length > maxLength) {
          displayInput = "..." + input.substring(input.length - maxLength);
        }

        // 防御性替换：防止玩家输入双引号导致 JSON 格式崩坏
        let safeInput = displayInput.replace(/"/g, '\\"');

        // 构建 JSON 数组字符串
        // 格式：["", {"text":"...命令部分", "underlined":true}, {"text":"<--[此处]", "underlined":false}]
        // 整个文本都是红色的
        let jsonMessage = JSON.stringify([
          "",
          {
            text: "未知或不完整的命令。错误见下",
            color: "red",
          },
          "\n", // 换行
          {
            text: safeInput,
            color: "red",
            underlined: true,
          },
          {
            text: "<--[此处]",
            color: "red",
            underlined: false,
          },
        ]);

        // --- 构建报错文本逻辑结束 ---

        // 【关键步骤 1】：先发送报错信息 (使用 tellraw)
        Utils.server.runCommandSilent(`tellraw ${playerName} ${jsonMessage}`);

        // 【关键步骤 2】：播放拒绝音效
        Utils.server.runCommandSilent(
          `playsound entity.villager.no master ${playerName} ~ ~ ~ 1 1`
        );

        // 【关键步骤 3】：最后拦截命令
        // 此时消息已经发送给客户端，cancel 不会撤回已发送的消息
        event.cancel();
      }
    }
  });
}
