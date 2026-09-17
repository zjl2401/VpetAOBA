package com.vpet.mobile

/**
 * 菜单树（手机精简）：去 RPG/家园/莱姆/暴露；工作一键开关；
 * 档案·音乐与字号大小等同层平铺（无「打开设置」中间层）；我的去掉回忆/成就。
 */
object DesktopMenuCatalog {

    enum class Status { READY, STUB, LATER }

    data class Item(
        val id: String,
        val title: String,
        val status: Status = Status.STUB,
        val children: List<Item> = emptyList(),
    )

    private val dialogChildren: List<Item> =
        PresetDialogs.all.mapIndexed { i, e ->
            Item("dialog_q_$i", e.question, Status.READY)
        }

    val root: List<Item> = listOf(
        Item(
            "mode", "模式", Status.READY,
            listOf(
                Item("mode_free", "自由", Status.READY),
                Item("mode_follow", "跟随", Status.READY),
                Item("mode_stroll", "漫步", Status.READY),
                Item("mode_quiet", "睡眠", Status.READY),
                Item("mode_music", "音乐", Status.READY),
                Item("mode_work", "工作", Status.READY),
                Item(
                    "mode_game", "游戏", Status.READY,
                    listOf(
                        Item("game_collect", "采集", Status.READY),
                        Item("game_type", "打字", Status.STUB),
                        Item("game_vocab", "背单词", Status.STUB),
                        Item("game_rhythm", "音游", Status.READY),
                    ),
                ),
            ),
        ),
        Item(
            "panel", "面板", Status.READY,
            listOf(
                Item("panel_open", "状态", Status.READY),
                Item("panel_companion", "伴侣", Status.READY),
                Item("panel_persona", "人格", Status.READY),
                Item("panel_invite", "邀请", Status.STUB),
            ),
        ),
        Item(
            "interact", "互动", Status.READY,
            listOf(
                Item(
                    "act", "动作", Status.READY,
                    listOf(
                        Item("act_eat", "吃", Status.READY),
                        Item("act_hi", "打招呼", Status.READY),
                        Item("act_call", "电话", Status.READY),
                        Item("act_adult", "×生活", Status.STUB),
                        Item("act_work", "工作", Status.READY),
                        Item("act_sleep", "小憩", Status.READY),
                        Item("act_squat", "蹲", Status.READY),
                        Item("act_kick", "踢", Status.READY),
                        Item("act_judge", "判断", Status.READY),
                        Item("act_yes", "是", Status.READY),
                        Item("act_no", "否", Status.READY),
                        Item("act_walk", "走", Status.READY),
                        Item("act_stand", "站", Status.READY),
                    ),
                ),
                Item(
                    "expr", "表情", Status.READY,
                    listOf(
                        Item("expr_idea", "主意", Status.READY),
                        Item("expr_happy", "开心", Status.READY),
                        Item("expr_angry", "生气", Status.READY),
                        Item("expr_question", "疑惑", Status.READY),
                        Item("expr_sad", "伤心", Status.READY),
                        Item("expr_shy", "脸红", Status.READY),
                        Item("expr_wink", "wink", Status.READY),
                        Item("expr_like", "赞", Status.READY),
                        Item("expr_bixin", "比心", Status.READY),
                    ),
                ),
                Item(
                    "dialog", "对话", Status.READY,
                    listOf(
                        Item("dialog_ai", "AI", Status.STUB),
                        Item("dialog_preset", "问答", Status.READY, dialogChildren),
                    ),
                ),
                Item(
                    "tools", "工具", Status.READY,
                    listOf(
                        Item("tool_sw", "秒表", Status.READY),
                        Item(
                            "tool_timer", "计时", Status.READY,
                            listOf(
                                Item("tool_timer_1", "1 分", Status.READY),
                                Item("tool_timer_5", "5 分", Status.READY),
                                Item("tool_timer_10", "10 分", Status.READY),
                            ),
                        ),
                        Item(
                            "tool_pomo", "番茄", Status.READY,
                            listOf(
                                Item("tool_pomo_25_5", "25/5", Status.READY),
                                Item("tool_pomo_15_5", "15/5", Status.READY),
                                Item("tool_pomo_1_1", "试玩 1/1", Status.READY),
                                Item("tool_pomo_end", "结束", Status.READY),
                            ),
                        ),
                        Item("tool_weather", "天气", Status.LATER),
                        Item(
                            "tool_birthday", "生日", Status.READY,
                            listOf(Item("tool_bday_set", "设定", Status.READY)),
                        ),
                    ),
                ),
            ),
        ),
        Item(
            "system", "系统", Status.READY,
            listOf(
                Item(
                    "sys_mine", "我的", Status.READY,
                    listOf(
                        Item("sys_owner", "所属", Status.READY),
                        Item("sys_diary", "日记", Status.READY),
                        Item("sys_sync", "同步", Status.READY),
                    ),
                ),
                // 大小/字体/音效/文本框/语音/难度/档案等合并进设置面板
                Item("sys_settings", "设置", Status.READY),
                Item(
                    "sys_community", "社区", Status.READY,
                    listOf(
                        Item("sys_about", "关于", Status.READY),
                        Item("sys_feedback", "反馈", Status.READY),
                        Item("sys_submit", "投稿", Status.READY),
                        Item("sys_guide", "说明", Status.READY),
                    ),
                ),
                Item("sys_reset", "重置", Status.READY),
                Item("sys_exit", "退出", Status.READY),
            ),
        ),
    )
}
