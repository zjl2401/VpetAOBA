package com.vpet.mobile

/**
 * 菜单树对照桌面 pet.py。
 * status: READY=已接；STUB=尚未开发完全；LATER=后期
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
                Item(
                    "mode_work", "工作 ▶", Status.READY,
                    listOf(
                        Item("work_free", "自由运送", Status.READY),
                        Item("work_end", "结束运送", Status.READY),
                        Item(
                            "work_custom", "自定义 ▶", Status.READY,
                            listOf(
                                Item("work_n3", "运送 3 箱", Status.READY),
                                Item("work_n5", "运送 5 箱", Status.READY),
                                Item("work_n8", "运送 8 箱", Status.READY),
                                Item("work_t1", "定时 1 分钟", Status.READY),
                                Item("work_t3", "定时 3 分钟", Status.READY),
                                Item("work_t5", "定时 5 分钟", Status.READY),
                            ),
                        ),
                        Item(
                            "work_settings", "设置 ▶", Status.READY,
                            listOf(
                                Item("work_show_props", "显示目的地 开/关", Status.READY),
                                Item("work_show_stack", "显示运送货物 开/关", Status.READY),
                            ),
                        ),
                    ),
                ),
                Item(
                    "mode_game", "游戏 ▶", Status.READY,
                    listOf(
                        Item("game_collect", "采集", Status.READY),
                        Item("game_type", "打字", Status.STUB),
                        Item("game_vocab", "背单词", Status.STUB),
                        Item("game_rhythm", "音乐音游", Status.READY),
                        Item("game_rpg", "RPG", Status.READY),
                    ),
                ),
            ),
        ),
        Item(
            "panel", "面板", Status.READY,
            listOf(
                Item("panel_open", "打开面板", Status.READY),
                Item("panel_companion", "智能伴侣", Status.READY),
                Item("panel_persona", "人格切换", Status.READY),
                Item("panel_home", "家园", Status.READY),
                Item("panel_invite", "邀请", Status.STUB),
                Item("panel_rhyme", "莱姆", Status.READY),
                Item("panel_expose", "暴露", Status.READY),
            ),
        ),
        Item(
            "interact", "互动", Status.READY,
            listOf(
                Item(
                    "act", "动作 ▶", Status.READY,
                    listOf(
                        Item("act_eat", "吃东西", Status.READY),
                        Item("act_hi", "打招呼", Status.READY),
                        Item("act_call", "打电话", Status.READY),
                        Item("act_adult", "×生活", Status.STUB),
                        Item("act_work", "工作", Status.READY),
                        Item("act_sleep", "睡眠", Status.READY),
                        Item("act_squat", "下蹲", Status.READY),
                        Item("act_kick", "侧踢", Status.READY),
                        Item("act_judge", "判断", Status.READY),
                        Item("act_yes", "是", Status.READY),
                        Item("act_no", "否", Status.READY),
                        Item("act_walk", "走路", Status.READY),
                        Item("act_stand", "站立", Status.READY),
                    ),
                ),
                Item(
                    "expr", "表情 ▶", Status.READY,
                    listOf(
                        Item("expr_idea", "有主意", Status.READY),
                        Item("expr_happy", "开心", Status.READY),
                        Item("expr_angry", "生气", Status.READY),
                        Item("expr_question", "疑问", Status.READY),
                        Item("expr_sad", "伤心", Status.READY),
                        Item("expr_shy", "脸红", Status.READY),
                        Item("expr_wink", "wink", Status.READY),
                        Item("expr_like", "点赞", Status.READY),
                        Item("expr_bixin", "比心", Status.READY),
                    ),
                ),
                Item(
                    "dialog", "对话 ▶", Status.READY,
                    listOf(
                        Item("dialog_ai", "AI 对话", Status.STUB),
                        Item("dialog_preset", "普通对话 ▶", Status.READY, dialogChildren),
                    ),
                ),
                Item(
                    "tools", "工具 ▶", Status.READY,
                    listOf(
                        Item("tool_sw", "秒表", Status.READY),
                        Item(
                            "tool_timer", "计时器 ▶", Status.READY,
                            listOf(
                                Item("tool_timer_1", "1 分钟", Status.READY),
                                Item("tool_timer_5", "5 分钟", Status.READY),
                                Item("tool_timer_10", "10 分钟", Status.READY),
                            ),
                        ),
                        Item(
                            "tool_pomo", "番茄钟 ▶", Status.READY,
                            listOf(
                                Item("tool_pomo_25_5", "25分工作 / 5分休息", Status.READY),
                                Item("tool_pomo_15_5", "15分工作 / 5分休息", Status.READY),
                                Item("tool_pomo_1_1", "1分/1分（试玩）", Status.READY),
                                Item("tool_pomo_end", "结束番茄钟", Status.READY),
                            ),
                        ),
                        Item("tool_schedule", "日程提醒", Status.READY),
                        Item("tool_weather", "天气预报", Status.LATER),
                        Item(
                            "tool_birthday", "生日祝福 ▶", Status.READY,
                            listOf(Item("tool_bday_set", "设定日期 / 礼物", Status.READY)),
                        ),
                        Item("tool_archive", "档案与音乐导入", Status.READY),
                    ),
                ),
            ),
        ),
        Item(
            "system", "系统", Status.READY,
            listOf(
                Item(
                    "sys_mine", "我的 ▶", Status.READY,
                    listOf(
                        Item("sys_owner", "所属人", Status.READY),
                        Item("sys_diary", "日记", Status.READY),
                        Item("sys_achievements", "成就", Status.READY),
                        Item(
                            "sys_memory", "回忆 ▶", Status.READY,
                            listOf(
                                Item("sys_gallery", "画廊", Status.READY),
                                Item("sys_phonograph", "留声", Status.READY),
                            ),
                        ),
                        Item("sys_sync", "与电脑同步档案", Status.READY),
                    ),
                ),
                Item(
                    "sys_settings", "设置 ▶", Status.READY,
                    listOf(
                        Item("sys_settings_page", "打开设置（大小/字体/声音/难度）", Status.READY),
                        Item("set_size_s", "大小·小", Status.READY),
                        Item("set_size_m", "大小·中", Status.READY),
                        Item("set_size_l", "大小·大", Status.READY),
                        Item("set_font_s", "字体·小", Status.READY),
                        Item("set_font_m", "字体·中", Status.READY),
                        Item("set_font_l", "字体·大", Status.READY),
                        Item("set_font_xl", "字体·特大", Status.READY),
                        Item("set_sound", "音效 开/关", Status.READY),
                        Item("set_voice", "语音模式 开/关", Status.READY),
                        Item("set_voice_vol_down", "语音音量 −", Status.READY),
                        Item("set_voice_vol_up", "语音音量 +", Status.READY),
                        Item("set_diff_low", "难度·低", Status.READY),
                        Item("set_diff_mid", "难度·中", Status.READY),
                        Item("set_diff_high", "难度·高", Status.READY),
                        Item("set_layer", "显示层级", Status.READY),
                    ),
                ),
                Item(
                    "sys_community", "社区 ▶", Status.READY,
                    listOf(
                        Item("sys_about", "关于", Status.READY),
                        Item("sys_feedback", "问题反馈", Status.READY),
                        Item("sys_submit", "投稿创意", Status.READY),
                        Item("sys_guide", "操作说明", Status.READY),
                    ),
                ),
                Item("sys_reset", "重置", Status.READY),
                Item("sys_exit", "退出悬浮", Status.READY),
            ),
        ),
    )
}
