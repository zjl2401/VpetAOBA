package com.vpet.mobile

/**
 * 说明类文案：对照电脑版 pet.py 原文尽量照抄（ABOUT / GUIDE / FEEDBACK / 投稿）。
 * 仅在确有平台差异处追加极短【手机】注记。
 */
object DesktopGuideCopy {
    const val ABOUT_DEVELOPER = "翛然而往"
    const val ABOUT_REPO_URL = "https://github.com/zjl2401/VpetAOBA"
    const val ABOUT_STEAM_URL = "https://store.steampowered.com/search/?term=DRAMatical+Murder"
    const val ABOUT_NITROCHIRAL_URL = "https://www.nitrochiral.com/"
    const val RHYTHM_CARNIVAL_URL = "https://www.nitrochiral.com/game/rhythm-carnival/"
    const val RHYTHM_CARNIVAL_TITLE = "THE CHiRAL NIGHT rhythm carnival"
    const val FEEDBACK_ISSUE_URL = "$ABOUT_REPO_URL/issues"
    const val FEEDBACK_XHS_URL = "https://www.xiaohongshu.com/user/profile/444225910"
    const val FEEDBACK_BILI_URL = "https://space.bilibili.com/696083047"

    const val RHYTHM_CARNIVAL_INTRO =
        "· 官方节奏作：《THE CHiRAL NIGHT rhythm carnival》。\n" +
            "　　桌宠内音游为同人小品，完整体验请支持正版。"

    const val ABOUT_TEXT =
        "本桌宠免费开放，供大家下载游玩。\n\n" +
            "角色：濑良垣苍叶（《DRAMAtical Murder》 / Nitro+CHiRAL）。\n" +
            "同人像素桌宠，非官方作品。\n" +
            "完整剧情与官方内容请下载并支持正版《戏剧性谋杀》。\n" +
            "当前功能尚不完全；更多关注与支持，会带来更多更新与优化。\n" +
            "可基于本仓库二次开发；欢迎社区投稿，若被后续版本用上，贡献者可按意愿加入「致谢」。\n" +
            "小红书有相关讨论群聊，感兴趣可加入。"

    val ABOUT_CREDITS: List<Pair<String, String>> = listOf(
        "翛然而往" to
            "企划构思 · 程序开发 · 像素立绘与界面 · 模式与互动玩法 · " +
            "小游戏与莱姆对战 · 语音/音乐整合 · 打包发行 · 测试与维护",
        "扶桑 · 阿斯代伦重度依赖（猫爪） · 青石大反派 · 玥浅 · 酒池桜" to "一轮测试",
    )

    const val FEEDBACK_NOTE = "反馈时请附：现象、复现步骤、构建版本；如有系统环境信息更佳。"

    const val COMMUNITY_FOLLOW_BLURB =
        "关注B站/小红书可及时获得最新进展与更新公告。\n\n" +
            "小红书有相关讨论群聊，感兴趣可加入。\n\n" +
            "源码见GitHub，拉取时请顺手点上小星星。\n\n" +
            "本桌宠免费开放，为《戏剧性谋杀》同人二创。" +
            "功能尚不完全；更多支持会带来更多更新与优化。" +
            "完整体验请下载正版。感谢游玩，祝游玩愉快 (´∀｀)♡"

    const val CREATOR_PACK_INTRO =
        "【手机版】投稿创意与打包投稿包功能暂未开放。\n\n" +
            "后续开发中可能重新开放（含勾选模块打包 zip、署名致谢等）。\n" +
            "预计可打包：DIY 地图 / 像素画与素材 / 家园布置 / 音游谱面 / 自导入音频。\n" +
            "届时会在此页与更新说明中告知。\n\n" +
            "目前若有文案、画、音频、音游谱面或功能点子，欢迎先到「问题反馈」里说说；\n" +
            "正式投稿通道开放前，请先自行备份创作内容。"

    const val OPERATION_GUIDE_INDEX =
        "【总览】\n" +
            "· 本桌宠免费开放，同人作品、非官方；\n" +
            "　　完整体验请下载正版《戏剧性谋杀》。\n" +
            "· 右键打开菜单；F1 可随时打开本说明。\n" +
            "· 请点下方专题查看说明。"

    const val OPERATION_GUIDE_TIPS =
        "【温馨提示】\n" +
            "· 部分功能切换时需要等待，属正常现象。\n" +
            "· 大部分音频与画面为手工录制、重绘，\n" +
            "　　音质与画面可能欠佳。\n" +
            "· 欢迎投稿文案、音频、像素画、DIY 地图、音游谱面与功能创意；\n" +
            "　　手机版投稿打包通道后续可能开放，可先到「问题反馈」交流。"

    const val MOBILE_GUIDE_FOOT =
        "\n\n【手机】\n" +
            "· 点立绘打开菜单（对应电脑右键）\n" +
            "· 系统 → 社区 → 操作说明（对应 F1）\n" +
            "· 返回键 / 关闭页 ≈ Esc"

    const val DISPLAY_LAYER_HINT = "顶部：置顶；中层：应用之下；底部：最底层"

    const val RESET_CONFIRM =
        "确定恢复初始设置？\n所属人、相伴时间、装扮与背包会保留；日记/成就标记等将清空。"

    data class Topic(val id: String, val title: String, val body: String, val links: List<Pair<String, String>> = emptyList())

    val GUIDE_TOPICS: List<Topic> = listOf(
        Topic(
            "basic", "基本操作",
            "· 右键：模式 / 面板 / 互动 / 系统\n" +
                "· 拖拽蓝色区域：移动桌宠\n" +
                "· Esc：退出当前玩法或关闭子窗口\n" +
                "· F1：打开本操作说明\n" +
                "· Ctrl+Shift+Q：强制退出（跳过结束动画）\n" +
                "· 更多全局快捷键见「系统 · 我的 · 快捷键」",
        ),
        Topic(
            "modes", "模式说明",
            "· 自由：走动，偶发动作\n" +
                "· 跟随：点空白处引路；急转可能眩晕\n" +
                "· 漫步：仅走动\n" +
                "· 睡眠：休息\n" +
                "· 音乐：菜单可开本地曲漫步；打开音乐 App 也会自动切音乐立绘\n" +
                "· 工作 / 游戏：见对应入口\n\n" +
                "· 看视频、玩游戏姿势：不是菜单模式\n" +
                "　　打开 B站/抖音等视频 App、或游戏 App 时自动切换\n" +
                "　　需在设置中授权「使用情况访问」",
        ),
        Topic(
            "game", "小游戏总览",
            "· 入口：模式 → 游戏\n\n" +
                "· 采集 / 打字 / 背单词 / 音乐：短局，结算可获金币\n" +
                "· RPG：冒险与宝箱；编辑器可自创地图\n" +
                "· 音游：可自制谱面；电脑版投稿时可勾选「音游谱面」\n" +
                "· 家园：布置；室外可开「经营」",
        ),
        Topic(
            "home_farm", "家园经营",
            "· 入口：面板 → 家园 → 室外 →「经营」\n\n" +
                "· 布置：左键铺放；右键上色；可画素材、保存\n" +
                "· 经营：数字键切换工具，确定后再于脚下执行\n" +
                "　　工具含锄、种、浇、收、砍、钓、采\n" +
                "· 采下的花可插入室内花瓶，也可戴在头顶\n" +
                "· 首次进入会弹出经营说明",
        ),
        Topic(
            "music_game", "音乐玩法 · 官方音游",
            "· 键位：D / F / J / K\n" +
                "· 音符到达判定线时按键\n" +
                "· Esc 退出\n\n" +
                "· 电脑版可制作谱面，并在「投稿创意」勾选「音游谱面」打包\n\n" +
                RHYTHM_CARNIVAL_INTRO,
            links = listOf(
                RHYTHM_CARNIVAL_TITLE to RHYTHM_CARNIVAL_URL,
                "Nitro+CHiRAL 官网" to ABOUT_NITROCHIRAL_URL,
            ),
        ),
        Topic(
            "panel", "面板 · 家园 · 互动",
            "· 面板：体力 / 心情 / 好感 / 背包、\n" +
                "　　智能伴侣、人格切换、家园、莱姆等\n" +
                "· 互动：动作 / 表情 / 对话 / 工具\n" +
                "· 系统设置开启「时间显示」时，\n" +
                "　　睡眠 / 音乐 / 工作旁会显示秒表或定时\n" +
                "· 部分条目尚未开发完全",
        ),
        Topic(
            "system", "系统 · 我的 · 快捷键",
            "· 系统菜单：我的 / 设置 / 社区 / 重置 / 退出\n" +
                "· 我的：所属人、日记、成就、回忆\n" +
                "· 互动 → 工具：秒表、计时器、番茄钟、日程、天气、生日祝福\n\n" +
                "【全局快捷键】按住 Ctrl+Shift 再按字母（可不点中桌宠）：\n" +
                "· H：打招呼\n" +
                "· E：喂食菜单\n" +
                "· T：打电话\n" +
                "· J：下蹲\n" +
                "· N：睡眠互动\n" +
                "· V：打开 / 关闭主菜单\n" +
                "· Q：强制退出（跳过结束语音与出场）\n" +
                "· A：AI 对话（尚未开放）\n\n" +
                "【窗口内】\n" +
                "· F1：操作说明\n" +
                "· Esc：退出当前玩法或关闭子窗口\n\n" +
                "【玩法内另有键位】\n" +
                "· 音游：D / F / J / K（见「音乐玩法」）\n" +
                "· 家园经营：数字键切换工具（见「家园经营」）\n" +
                "· RPG 编辑器：Ctrl+S 保存；Ctrl+E 或 Ctrl+Shift+S 导出等",
        ),
        Topic(
            "notes", "制作说明 · 诚邀",
            "· 本作为爱好向同人桌宠，免费开放，持续完善中。\n" +
                "· 切换功能时若出现短暂等待，还请耐心。\n" +
                "· 音画多为手工录制与重绘，可能较为粗糙。\n" +
                "· 欢迎投稿文案、音频、像素画、DIY 地图、音游谱面与功能创意。\n" +
                "· 手机版投稿打包暂未开放，详见专题「导出与投稿」。",
        ),
        Topic(
            "submit", "导出与投稿",
            "【手机版】投稿创意与打包投稿包功能暂未开放。\n\n" +
                "后续开发中可能重新开放（勾选模块打包、署名致谢等）。\n" +
                "预计可打包：DIY 地图 / 像素画与素材 / 家园布置 / 音游谱面 / 自导入音频。\n" +
                "开放后会在「系统 → 社区 → 投稿创意」与更新说明中告知。\n\n" +
                "现阶段：\n" +
                "· 有想法可先到「问题反馈」交流\n" +
                "· 家园 / 地图 / 谱面等创作请自行在本机备份\n" +
                "· 正式投稿通道以日后开放说明为准",
        ),
        Topic(
            "community", "关注 · 源码 · Star",
            COMMUNITY_FOLLOW_BLURB,
            links = listOf(
                "B站主页" to FEEDBACK_BILI_URL,
                "小红书" to FEEDBACK_XHS_URL,
                "GitHub 源码" to ABOUT_REPO_URL,
            ),
        ),
    )

    val FIRST_PLAY: Map<String, Topic> = mapOf(
        "gather" to Topic(
            "gather", "采集 · 操作说明",
            "· 移动鼠标接取下落物\n" +
                "· 部分物品会加减时间或造成眩晕\n" +
                "· Esc：结算并退出",
        ),
        "rhythm_game" to Topic(
            "rhythm_game", "音乐 · 操作说明",
            "· 键位：D F J K；音符到达判定线时按键\n" +
                "· 短音点按；长音按住至结束\n" +
                "· Esc 退出\n\n" +
                RHYTHM_CARNIVAL_INTRO,
            links = listOf(RHYTHM_CARNIVAL_TITLE to RHYTHM_CARNIVAL_URL),
        ),
        "expose" to Topic(
            "expose", "暴露 · 操作说明",
            "· 指针进入蓝色区域时按 Enter 判定。连续命中即可通关。Esc 中断。",
        ),
        "rhyme" to Topic(
            "rhyme", "莱姆 · 操作说明",
            "· 回合制练习对战：攻击 / 防御 / 必杀\n" +
                "· 双方选招后掷骰判定，再同时结算\n" +
                "· Esc 结束",
        ),
    )

    fun guideHomeBody(): String =
        "【操作说明】\n\n$OPERATION_GUIDE_INDEX\n\n$OPERATION_GUIDE_TIPS$MOBILE_GUIDE_FOOT"

    fun aboutBody(): String = buildString {
        append(ABOUT_TEXT)
        append("\n\n作者菌：")
        append(ABOUT_DEVELOPER)
        append("\n\n【致谢】\n")
        for ((name, role) in ABOUT_CREDITS) {
            append("· ")
            append(name)
            append("\n　　")
            append(role)
            append('\n')
        }
        append("\nGitHub：")
        append(ABOUT_REPO_URL)
    }

    fun feedbackBody(): String =
        "$FEEDBACK_NOTE\n\n" +
            "· GitHub Issues\n" +
            "· 小红书 / B站私信或评论\n\n" +
            COMMUNITY_FOLLOW_BLURB

    fun submitBody(): String = CREATOR_PACK_INTRO
}
