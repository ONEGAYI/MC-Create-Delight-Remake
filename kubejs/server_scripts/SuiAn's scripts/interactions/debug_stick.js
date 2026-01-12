//调试棒右击方块事件
ItemEvents.rightClicked("suian:debug_stick", event => {
    var player = event.player;
    player.swing();
    try {
        var target = event.target;
        //检测是block还是entity
        if (target.block != null) {
            let block = target.block
            let blockState = block.blockState
            let blockEntity = block.entity
            player.tell(Text.of("[BlockID]").aqua().append(Text.literal(block.id.toString()).green().clickCopy(block.id.toString()).hover(Text.of("click to copy").darkPurple())))
            //标签
            player.tell(Text.of("[BlockTags]").aqua())
            block.tags.forEach(tag => {
                player.tell(Text.of(`   #${tag}`).white().clickCopy(`#${tag}`).hover(Text.of("click to copy").darkPurple()))
            })
            player.tell(Text.of("[BlockState]").aqua().append(Text.prettyPrintNbt(block.properties).white().clickCopy(block.properties).hover(Text.of("click to copy").darkPurple())))
            if (blockEntity != null) {
                player.tell(Text.of("[BlockEntity]").aqua().append(Text.of(blockEntity.toString()).clickCopy(blockEntity.toString()).darkGreen().hover(Text.of("click to copy").darkPurple())))
                player.tell(Text.of("[BlockEntityData]").aqua().append(Text.prettyPrintNbt(block.entityData).white().clickCopy(block.entityData).hover(Text.of("click to copy").darkPurple())))
            }
            // player.tell(Text.of("[BlockEntity]").aqua().append(Text.prettyPrintNbt(blockEntity).clickCopy(blockState).hover(Text.of("click to copy").darkPurple())))
        }
        else if (target.entity != null) {
            let entity = target.entity;
            let nbt = entity.nbt;
            // let len = (String(nbt).length <= 2000) ? String(nbt).length : 2000;
            player.tell(Text.of("[EntityType]").aqua().append(Text.literal(entity.entityType.toString()).clickCopy(entity.entityType).hover(Text.of("click to copy").darkPurple()).green()))
            player.tell(Text.of("[EntityNBT]").aqua().append(Text.prettyPrintNbt(nbt).clickCopy(nbt).white().hover(Text.of("click to copy").darkPurple())))
        }
        else return
    } catch (error) {
        console.log(error)
    }
})