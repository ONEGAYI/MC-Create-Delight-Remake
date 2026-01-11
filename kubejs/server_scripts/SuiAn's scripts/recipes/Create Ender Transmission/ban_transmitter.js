ServerEvents.recipes(event => {
    // 使用通配符删除所有传输器（能量、流体、物品）
    event.remove({ id: /createendertransmission:\w+_transmitter/ })
})
