package com.vpet.mobile

/**
 * 菜单树对照桌面 pet.py `_open_mode_menu` / `_open_panel_menu` 等。
 * status: READY=已接；STUB=尚未开发完全；LATER=后期
 *
 * 看视频 / App 跟听：不是菜单模式，由 AppSceneMonitor 自动检测切换姿势。
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
                // 菜单「音乐」= 本地曲漫步（对照桌面）；App 跟听为自动检测，无单独菜单项
                Item("mode_music", "音乐", Status.READY),
                Item(
                    "mode_work", "工作 ▶", Status.READY,
                    listOf(
                        Item("work_free", "自由运送", Status.READY),
                        Item("work_end", "结束运送", Status.READY),
                        Item("work_custom", "自定义箱数 / 时间…", Status.READY),
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
                        Item("game_rhythm", "音乐音游", Status.READY),
                        Item("game_rpg", "RPG", Status.READY),
                    ),
                ),
            ),
        ),
        Item(
            "panel", "面板", Status.READY,
            // 顺序对照桌面 _open_panel_menu
            listOf(
                Item("panel_open", "打开面板", Status.READY),
                Item("panel_companion", "智能伴侣", Status.READY),
                Item("panel_persona", "人格切换", Status.READY),
                Item("panel_outfit", "装扮", Status.READY),
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
                        Item("act_adult", "×生活", Status.READY),
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
                        Item("dialog_preset", "普通对话 ▶", Status.READY, dialogChildren),
                        Item("dialog_ai", "AI 对话", Status.STUB),
                    ),
                ),
                Item(
                    "tools", "工具 ▶", Status.READY,
                    listOf(
                        Item("tool_sw", "秒表", Status.READY),
                        Item("tool_timer", "计时器…", Status.READY),
                        Item(
                            "tool_pomo", "番茄钟 ▶", Status.READY,
                            listOf(
                                Item("tool_pomo_custom", "自定义…", Status.READY),
                                Item("tool_pomo_end", "结束番茄钟", Status.READY),
                            ),
                        ),
                        Item("tool_schedule", "日程提醒", Status.READY),
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
                            "sys_memories", "回忆 ▶", Status.READY,
                            listOf(
                                Item("sys_gallery", "画廊", Status.READY),
                                Item("sys_phonograph", "留声", Status.READY),
                            ),
                        ),
                    ),
                ),
                Item(
                    "sys_settings", "设置 ▶", Status.READY,
                    listOf(
                        Item("sys_settings_page", "打开设置", Status.READY),
                        Item("set_voice_vol", "语音音量…", Status.READY),
                        Item("set_sfx_vol", "音效音量…", Status.READY),
                        Item("set_sound", "音效 开/关", Status.READY),
                        Item("set_voice", "语音模式 开/关", Status.READY),
                        Item("set_layer", "显示层级说明", Status.READY),
                    ),
                ),
                Item(
                    "sys_community", "社区 ▶", Status.READY,
                    listOf(
                        Item("sys_about", "关于", Status.READY),
                        Item("sys_feedback", "问题反馈", Status.READY),
                        Item("sys_submit", "投稿创意", Status.LATER),
                        Item("sys_guide", "操作说明", Status.READY),
                    ),
                ),
                Item("sys_reset", "重置", Status.READY),
                Item("sys_exit", "退出悬浮", Status.READY),
            ),
        ),
    )
}
