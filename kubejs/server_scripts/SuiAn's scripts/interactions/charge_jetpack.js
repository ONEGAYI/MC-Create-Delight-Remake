let baseAir = 1800
let increaseAirPerLvl = 300

BlockEvents.rightClicked('create_jetpack:netherite_jetpack', event => {
    let {player, block: jetpack, server, level, hand} = event
    if (hand == "off_hand" || player.mainHandItem != 'air') return //不考虑副手，主手需要空手
    if (!player.crouching) return 0
    player.swing()

    let jetPos = [jetpack.pos.x, jetpack.pos.y, jetpack.pos.z]
    let jetState = String(jetpack.properties).replace("{", '[').replace('}', "]");
    let jetData = jetpack.entityData;
    let jetTag = jetData.get("VanillaTag")
    let jetCapacityLvl = jetData.get("CapacityEnchantment") //扩容等级
    if (jetCapacityLvl == null) jetCapacityLvl = 0;
    let jetAir = Number(jetData.get("Air")) //剩余空气
    let jetAirMax = baseAir + jetCapacityLvl * increaseAirPerLvl; //最大容量
    let needAir = jetAirMax - jetAir;

    let sideblocks = [jetpack.up, jetpack.down, jetpack.north, jetpack.west, jetpack.south, jetpack.east] //获取背包周围方块
    let needPlayParticle = false
    sideblocks.forEach(sideblock => {
        if (needAir <= 0) return //从一个罐子充满就不再充
        if (sideblock.id != 'create:copper_backtank' && sideblock.id != 'create:netherite_backtank') return
        let tankData = sideblock.entityData;
        let tankTag = tankData.get("VanillaTag")
        let tankAir = Number(tankData.get("Air"))
        let tankPos = [sideblock.pos.x, sideblock.pos.y, sideblock.pos.z]
        let tankState = String(sideblock.properties).replace("{", '[').replace('}', "]");

        console.log(jetAir)

        //填装逻辑部分
        if (tankAir <= 0) return
        if (tankAir >= needAir) {
            jetAir = jetAirMax
            tankAir = tankAir - needAir
        }
        else {
            jetAir = jetAir + tankAir
            tankAir = 0
        }
        needAir = jetAirMax - jetAir
        tankData = tankData.merge(`{Air: ${tankAir}}`).merge(tankTag.merge(`{Air: ${tankAir}}`))
        needPlayParticle = true

        //替换方块
        server.runCommandSilent(`setblock ${tankPos[0]} ${tankPos[1]} ${tankPos[2]} air replace`)
        server.runCommandSilent(`setblock ${tankPos[0]} ${tankPos[1]} ${tankPos[2]} ${sideblock.id}${tankState}${tankData} replace`)
        jetData = jetData.merge(`{Air: ${jetAir}}`).merge(jetTag.merge(`{Air: ${jetAir}}`))
        server.runCommandSilent(`setblock ${jetPos[0]} ${jetPos[1]} ${jetPos[2]} air replace`)
        server.runCommandSilent(`setblock ${jetPos[0]} ${jetPos[1]} ${jetPos[2]} ${jetpack.id}${jetState}${jetData} replace`)
    })
    //播放粒子效果
    if (needPlayParticle) {
        level.spawnParticles('minecraft:angry_villager', false, jetpack.pos.x + 0.5, jetpack.pos.y + 0.25, jetpack.pos.z + 0.5, 0.25, 0.1, 0.25, 15, 0)
    }
})

BlockEvents.rightClicked('create_jetpack:jetpack', event => {
    let {player, block: jetpack, server, level, hand} = event
    if (hand == "off_hand" || player.mainHandItem != 'air') return //不考虑副手，主手需要空手
    if (!player.crouching) return 0
    player.swing()

    let jetPos = [jetpack.pos.x, jetpack.pos.y, jetpack.pos.z]
    let jetState = String(jetpack.properties).replace("{", '[').replace('}', "]");
    let jetData = jetpack.entityData;
    let jetTag = jetData.get("VanillaTag")
    let jetCapacityLvl = jetData.get("CapacityEnchantment") //扩容等级
    if (jetCapacityLvl == null) jetCapacityLvl = 0;
    let jetAir = Number(jetData.get("Air")) //剩余空气
    let jetAirMax = baseAir + jetCapacityLvl * increaseAirPerLvl; //最大容量
    let needAir = jetAirMax - jetAir;

    let sideblocks = [jetpack.up, jetpack.down, jetpack.north, jetpack.west, jetpack.south, jetpack.east] //获取背包周围方块
    let needPlayParticle = false
    sideblocks.forEach(sideblock => {
        if (needAir <= 0) return //从一个罐子充满就不再充
        if (sideblock.id != 'create:copper_backtank' && sideblock.id != 'create:netherite_backtank') return
        let tankData = sideblock.entityData;
        let tankTag = tankData.get("VanillaTag")
        let tankAir = Number(tankData.get("Air"))
        let tankPos = [sideblock.pos.x, sideblock.pos.y, sideblock.pos.z]
        let tankState = String(sideblock.properties).replace("{", '[').replace('}', "]");

        console.log(jetAir)

        //填装逻辑部分
        if (tankAir <= 0) return
        if (tankAir >= needAir) {
            jetAir = jetAirMax
            tankAir = tankAir - needAir
        }
        else {
            jetAir = jetAir + tankAir
            tankAir = 0
        }
        needAir = jetAirMax - jetAir
        tankData = tankData.merge(`{Air: ${tankAir}}`).merge(tankTag.merge(`{Air: ${tankAir}}`))
        needPlayParticle = true

        //替换方块
        server.runCommandSilent(`setblock ${tankPos[0]} ${tankPos[1]} ${tankPos[2]} air replace`)
        server.runCommandSilent(`setblock ${tankPos[0]} ${tankPos[1]} ${tankPos[2]} ${sideblock.id}${tankState}${tankData} replace`)
        jetData = jetData.merge(`{Air: ${jetAir}}`).merge(jetTag.merge(`{Air: ${jetAir}}`))
        server.runCommandSilent(`setblock ${jetPos[0]} ${jetPos[1]} ${jetPos[2]} air replace`)
        server.runCommandSilent(`setblock ${jetPos[0]} ${jetPos[1]} ${jetPos[2]} ${jetpack.id}${jetState}${jetData} replace`)
    })
    //播放粒子效果
    if (needPlayParticle) {
        level.spawnParticles('minecraft:angry_villager', false, jetpack.pos.x + 0.5, jetpack.pos.y + 0.25, jetpack.pos.z + 0.5, 0.25, 0.1, 0.25, 15, 0)
    }
})

// function getEnchantments(enchantmentsList, target) {
//     target = '"' + target + '"'
//     let hasFound = false
//     let targetLevel = 0
//     enchantmentsList.forEach(enchantment => {
//         if (hasFound) return

//         let type = enchantment.get("id");
//         let lvl = String(enchantment.get("lvl"));

//         let lvlEndWithS = false
//         if (lvl.charAt(lvl.length - 1) == 's') {
//            lvl = lvl.substring(0, lvl.length - 1) //去除末尾's' 
//            lvlEndWithS = true
//         }
//         lvl = Number(lvl)

//         if (type != null && type == target) {
//             targetLevel = lvl;
//             hasFound = true;
//             return;
//         }
//     })
//     return targetLevel
// }