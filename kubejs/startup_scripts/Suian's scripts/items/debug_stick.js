StartupEvents.registry('item', event => {
    event
        .create("suian:debug_stick", 'basic')
        .translationKey("item.suian.debug_stick")
        .texture("suian:item/debug_stick")
        .unstackable()
        .rarity("epic")
        .tooltip(Text.translate("tooltips.suian.debug_stick").yellow())
})