package com.vpet.mobile

/** 食物目录：对照桌面 FOODS 全部 18 种（含 ×0 展示）。 */
object FoodCatalog {
    data class Food(val id: String, val label: String, val emoji: String, val stamina: Int, val mood: Int)

    val ALL: List<Food> = listOf(
        Food("bread", "面包", "🍞", 8, 3),
        Food("apple", "苹果", "🍎", 12, 6),
        Food("cake", "蛋糕", "🍰", 5, 14),
        Food("fish", "烤鱼", "🐟", 20, 4),
        Food("onigiri", "饭团", "🍙", 10, 5),
        Food("candy", "糖果", "🍬", 3, 12),
        Food("tea", "热茶", "🍵", 6, 8),
        Food("meat", "烤肉", "🥩", 18, 5),
        Food("berry", "草莓", "🍓", 8, 10),
        Food("donut", "甜甜圈", "🍩", 7, 11),
        Food("milk", "牛奶", "🥛", 9, 7),
        Food("ramen", "拉面", "🍜", 16, 8),
        Food("sushi", "寿司", "🍣", 14, 9),
        Food("cookie", "曲奇", "🍪", 4, 10),
        Food("juice", "果汁", "🧃", 7, 9),
        Food("taco", "卷饼", "🌮", 13, 6),
        Food("icecream", "冰淇淋", "🍦", 5, 13),
        Food("corn", "玉米", "🌽", 11, 4),
    )

    /** 新增种类首次入库种子：对照 FOOD_NEW_KIND_SEED=3 */
    const val NEW_KIND_SEED = 3

    fun byId(id: String): Food? = ALL.find { it.id == id }

    fun randomCollectId(): String = ALL.random().id
}
