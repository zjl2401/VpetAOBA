package com.vpet.mobile

/** 跟随 / 工作引擎常量（宿主调度仍在平台层）。 */
object FollowMath {
    const val FOLLOW_MOVE_INTERVAL_MS = 40L
    const val FOLLOW_STOP_DIST = 65
    const val FOLLOW_FAR_DIST = 220
    const val FOLLOW_DIZZY_STAND_MS = 3000L
    const val FOLLOW_DIZZY_SPIN_STEPS = 4
    const val FOLLOW_DIZZY_TEXT = "我晕了……"
    const val MOVE_STEP = 2
}

object WorkMath {
    const val WORK_ARRIVE_DIST = 18
    const val WORK_MIN_SPAN = 300
    const val WORK_BOX_TOTAL_DEFAULT = 5
    const val WORK_MOVE_INTERVAL_MS = 55L
    const val WORK_PROP_SIZE = 72
    const val MOVE_STEP = 2
}

/** 家园经营目录常量。 */
object HomeFarmCatalog {
    const val MATURITY_MAX = 100.0
    const val MATURITY_PER_HOUR = 5.0
    const val WATER_BOOST_SEC = 3600.0
    const val WATER_MAX_PER_DAY = 2
    const val TREE_REGROW_SEC = 48 * 3600.0
    const val CHOP_DICE_MIN = 2
    const val CHOP_DICE_MAX = 6

    enum class Tool(val id: String, val label: String, val hint: String) {
        TILL("till", "锄地", "先清上面，再锄两下草地→土地"),
        PLANT("plant", "播种", "仅土地可种"),
        WATER("water", "浇水", "每天最多2次；浇后1小时×2"),
        HARVEST("harvest", "收获", "成熟度满100可收"),
        CHOP("chop", "砍树", "点树四周格子"),
        FISH("fish", "钓鱼", "点水面四周；上钩后再点"),
        PICK("pick", "采花", "采小花入背包"),
    }

    data class CropDef(val label: String, val seed: String, val item: String, val colors: List<String>)

    val CROP_DEFS = mapOf(
        "wheat" to CropDef("小麦", "seed_wheat", "crop_wheat", listOf("#c8b070", "#d4c078", "#e8d888", "#f0e090")),
        "berry" to CropDef("莓果", "seed_berry", "crop_berry", listOf("#886688", "#aa6688", "#cc6688", "#ee5588")),
        "corn" to CropDef("玉米", "seed_corn", "crop_corn", listOf("#889944", "#aaba44", "#ccdd55", "#ffe066")),
    )

    val SEED_TO_CROP = mapOf(
        "seed_wheat" to "wheat",
        "seed_berry" to "berry",
        "seed_corn" to "corn",
    )

    val SHOP_PRICES = mapOf(
        "seed_wheat" to 3,
        "seed_berry" to 4,
        "seed_corn" to 4,
        "wood" to 5,
    )

    val SELL_PRICES = mapOf(
        "crop_wheat" to 4,
        "crop_berry" to 5,
        "crop_corn" to 5,
        "fish" to 6,
        "flower_cut" to 2,
    )

    data class CraftRecipe(
        val id: String,
        val label: String,
        val costs: Map<String, Int>,
        val resultType: String,
        val resultId: String,
        val desc: String,
    )

    val CRAFT_RECIPES = listOf(
        CraftRecipe("bread", "烤面包", mapOf("crop_wheat" to 2), "food", "bread", "2小麦→面包"),
        CraftRecipe("berry_snack", "莓果点心", mapOf("crop_berry" to 2), "food", "berry", "2莓果→草莓"),
        CraftRecipe("corn_food", "烤玉米", mapOf("crop_corn" to 2), "food", "corn", "2玉米穗→玉米"),
        CraftRecipe("juice", "果汁", mapOf("crop_berry" to 1, "crop_wheat" to 1), "food", "juice", "莓+麦→果汁"),
        CraftRecipe("sofa", "解锁沙发", mapOf("wood" to 3, "crop_wheat" to 1), "furniture", "sofa", "3木+1麦"),
        CraftRecipe("shelf", "解锁柜子", mapOf("wood" to 2, "crop_berry" to 1), "furniture", "shelf", "2木+1莓"),
    )
}
