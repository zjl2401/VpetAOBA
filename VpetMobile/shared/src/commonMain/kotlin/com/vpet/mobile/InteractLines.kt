package com.vpet.mobile

/** 对照桌面 pet.py：HI_TEXT / CALL_TEXT / INTERACT_BANTER / WORK_MODE_BANTER。 */
object InteractLines {
    const val HI_TEXT = "你好呀！今天也要加油哦~"
    const val CALL_TEXT = "你好，这里是旧货店「平凡」，我是苍叶，谢谢你的来电"
    const val YESNO_ANSWER_TEXT = "你所问问题的答案是"
    const val FOLLOW_DIZZY_TEXT = "我晕了……"

    /** 长拖无 yuqi 资源时的回落台词（对照 DRAG_DIZZY_LINES）。 */
    val DRAG_DIZZY = listOf(
        "别晃啦我晕了……",
        "慢—慢—点—拖—我—",
        "鼠标在飞吗？",
        "天旋地转……",
        "呕……别摇了",
        "再晃要吐了啦！",
        "拖我别当甩干机啊！",
    )

    val META = mapOf(
        "drag_long" to listOf(
            "你在挪窗口，不是在遛我……",
            "鼠标拖我，算不算出门？",
            "又被拎起来了。",
        ),
        "work_flag" to listOf(
            "终点又被你改了。",
            "旗子搬家，箱子跟着倒霉。",
            "目的地不稳定啊……",
        ),
        "idle_long" to listOf(
            "屏幕暗了？还是你去忙了？",
            "……还在吗？",
            "安静好久了呢。",
        ),
    )

    fun meta(event: String): String = META[event]?.random() ?: ""

    val FOLLOW_WAIT = listOf("等等我！", "别走那么快嘛~", "等等我啦！", "等等我嘛…")

    val WORK_MODE = listOf(
        "一起加油，努力工作！",
        "嘿咻嘿咻~ 货物交给我！",
        "打工人打工魂，认真运送每一批货物~",
        "你今天也很努力呢，一起加油吧！",
        "苍叶在平凡也要把活干漂亮！",
        "加油加油，终点就在前面！",
        "运完这批还有下一批…但我们会坚持的！",
        "旧货店的活儿，交给苍叶就好~",
    )

    private val banter = mapOf(
        "squat" to listOf("嗯…歇一下~", "蹲蹲更健康！"),
        "kick" to listOf("哈！", "吃我一脚！"),
        "eat" to listOf("谢谢投喂！", "肚子已经鼓鼓啦~", "还要吃吗？"),
        "sleep" to listOf("Zzz…", "好困呀…"),
        "work" to listOf("打工人加油！", "货物交给我~"),
        "angry" to listOf("哼！", "气鼓鼓！"),
        "question" to listOf("嗯？", "这是怎么回事？"),
        "sad" to listOf("呜…", "心里下雨了呢…"),
        "idea" to listOf("有了！", "灵光一闪~"),
        "happy" to listOf("耶——！", "超开心！"),
        "shy" to listOf("///", "脸红了啦…"),
        "like" to listOf("棒棒！", "给你点赞~"),
        "bixin" to listOf("比心~", "爱你哦！", "传给你啦~"),
        "yes" to listOf("是！", "嗯嗯！"),
        "no" to listOf("否~", "不要啦…"),
        "yesno" to listOf("命运揭晓…", "答案是…"),
        "music" to listOf("♪~", "一起听歌吧~"),
        "expose" to listOf("…", "屏住呼吸…"),
        "wink" to listOf("Wink~", "看这边~"),
        "walk" to listOf("走走走~", "去哪儿呢？"),
        "stand" to listOf("站好啦。", "待命中~"),
    )

    fun line(key: String): String =
        banter[key]?.random() ?: ""

    fun lines(key: String): List<String> = banter[key].orEmpty()
}
