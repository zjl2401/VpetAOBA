# -*- coding: utf-8 -*-
"""Expand CN/EN banks and rebuild JP typing targets as kana/romaji."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BANK = ROOT / "word_banks"

# Minimal romaji -> hiragana (longest match). Enough for JLPT bank rebuild.
_ROMAJI_TABLE: list[tuple[str, str]] = [
    ("kya", "きゃ"), ("kyu", "きゅ"), ("kyo", "きょ"),
    ("gya", "ぎゃ"), ("gyu", "ぎゅ"), ("gyo", "ぎょ"),
    ("sha", "しゃ"), ("shu", "しゅ"), ("sho", "しょ"), ("shi", "し"),
    ("ja", "じゃ"), ("ju", "じゅ"), ("jo", "じょ"), ("ji", "じ"),
    ("cha", "ちゃ"), ("chu", "ちゅ"), ("cho", "ちょ"), ("chi", "ち"),
    ("nya", "にゃ"), ("nyu", "にゅ"), ("nyo", "にょ"),
    ("hya", "ひゃ"), ("hyu", "ひゅ"), ("hyo", "ひょ"),
    ("bya", "びゃ"), ("byu", "びゅ"), ("byo", "びょ"),
    ("pya", "ぴゃ"), ("pyu", "ぴゅ"), ("pyo", "ぴょ"),
    ("mya", "みゃ"), ("myu", "みゅ"), ("myo", "みょ"),
    ("rya", "りゃ"), ("ryu", "りゅ"), ("ryo", "りょ"),
    ("tsu", "つ"), ("dzu", "づ"), ("dzu", "づ"),
    ("kk", "っk"), ("ss", "っs"), ("tt", "っt"), ("pp", "っp"),
    ("cc", "っc"), ("gg", "っg"), ("dd", "っd"), ("bb", "っb"),
    ("ka", "か"), ("ki", "き"), ("ku", "く"), ("ke", "け"), ("ko", "こ"),
    ("ga", "が"), ("gi", "ぎ"), ("gu", "ぐ"), ("ge", "げ"), ("go", "ご"),
    ("sa", "さ"), ("su", "す"), ("se", "せ"), ("so", "そ"),
    ("za", "ざ"), ("zu", "ず"), ("ze", "ぜ"), ("zo", "ぞ"),
    ("ta", "た"), ("te", "て"), ("to", "と"),
    ("da", "だ"), ("de", "で"), ("do", "ど"),
    ("na", "な"), ("ni", "に"), ("nu", "ぬ"), ("ne", "ね"), ("no", "の"),
    ("ha", "は"), ("hi", "ひ"), ("fu", "ふ"), ("he", "へ"), ("ho", "ほ"),
    ("ba", "ば"), ("bi", "び"), ("bu", "ぶ"), ("be", "べ"), ("bo", "ぼ"),
    ("pa", "ぱ"), ("pi", "ぴ"), ("pu", "ぷ"), ("pe", "ぺ"), ("po", "ぽ"),
    ("ma", "ま"), ("mi", "み"), ("mu", "む"), ("me", "め"), ("mo", "も"),
    ("ya", "や"), ("yu", "ゆ"), ("yo", "よ"),
    ("ra", "ら"), ("ri", "り"), ("ru", "る"), ("re", "れ"), ("ro", "ろ"),
    ("wa", "わ"), ("wo", "を"), ("nn", "ん"), ("n", "ん"),
    ("a", "あ"), ("i", "い"), ("u", "う"), ("e", "え"), ("o", "お"),
    ("-", "ー"),
]
_ROMAJI_TABLE.sort(key=lambda x: len(x[0]), reverse=True)


def romaji_to_hiragana(romaji: str) -> str:
    s = re.sub(r"[^a-zA-Z\-]", "", romaji).lower()
    out: list[str] = []
    i = 0
    while i < len(s):
        matched = False
        for roma, kana in _ROMAJI_TABLE:
            if s.startswith(roma, i):
                if kana.startswith("っ") and len(kana) == 2:
                    out.append("っ")
                    # keep the consonant for next syllable (kk -> っ + k…)
                    i += 1
                else:
                    out.append(kana)
                    i += len(roma)
                matched = True
                break
        if not matched:
            # skip unknown char
            i += 1
    return "".join(out)


def is_kana(text: str) -> bool:
    return bool(text) and all(
        ("\u3040" <= c <= "\u30ff") or c in "ー・ 　" for c in text
    )


def fetch_text(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "VpetBankExpand/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def expand_english() -> None:
    """CEFR-ish English: word + Chinese gloss from free lists + local hard set."""
    words: dict[str, str] = {}
    # Local harder seed (B1–C1)
    seed = {
        "abandon": "放弃；遗弃",
        "ability": "能力",
        "absolute": "绝对的",
        "abstract": "抽象的",
        "academic": "学术的",
        "accelerate": "加速",
        "access": "通道；访问",
        "accommodate": "容纳；适应",
        "accompany": "陪伴",
        "accomplish": "完成",
        "accumulate": "积累",
        "accurate": "准确的",
        "accuse": "指责",
        "achieve": "达成",
        "acknowledge": "承认",
        "acquire": "获得",
        "adapt": "适应",
        "adequate": "足够的",
        "adjust": "调整",
        "administration": "管理；行政",
        "advocate": "提倡；拥护者",
        "aesthetic": "美学的",
        "agenda": "议程",
        "aggressive": "好斗的；积极的",
        "agriculture": "农业",
        "allocate": "分配",
        "alter": "改变",
        "ambiguous": "模棱两可的",
        "amend": "修正",
        "analogy": "类比",
        "analyze": "分析",
        "annual": "每年的",
        "anticipate": "预期",
        "anxiety": "焦虑",
        "apology": "道歉",
        "apparatus": "器械；装置",
        "apparent": "明显的",
        "appeal": "呼吁；上诉",
        "appetite": "食欲",
        "appliance": "电器",
        "applicant": "申请人",
        "appreciate": "欣赏；感激",
        "approach": "接近；方法",
        "appropriate": "合适的",
        "approximate": "大约的",
        "arbitrary": "任意的",
        "architecture": "建筑学",
        "argue": "争论",
        "arise": "出现；产生",
        "arrogant": "傲慢的",
        "artificial": "人造的",
        "aspire": "渴望",
        "assemble": "组装；集合",
        "assert": "断言",
        "assess": "评估",
        "assign": "指派",
        "assist": "协助",
        "assume": "假定",
        "assure": "保证",
        "athlete": "运动员",
        "atmosphere": "大气；氛围",
        "attach": "附着",
        "attain": "获得",
        "attempt": "尝试",
        "attitude": "态度",
        "attribute": "属性；归因",
        "auction": "拍卖",
        "audience": "观众",
        "authentic": "真正的",
        "authority": "权威",
        "automatic": "自动的",
        "available": "可用的",
        "avenue": "大街；途径",
        "average": "平均的",
        "avoid": "避免",
        "aware": "意识到的",
        "awkward": "尴尬的",
        "bachelor": "学士；单身汉",
        "background": "背景",
        "balance": "平衡",
        "bankrupt": "破产的",
        "barrier": "障碍",
        "basic": "基本的",
        "battery": "电池",
        "behavior": "行为",
        "benefit": "益处",
        "bias": "偏见",
        "bid": "出价；投标",
        "biology": "生物学",
        "blame": "责备",
        "blank": "空白的",
        "bleed": "流血",
        "blend": "混合",
        "bless": "祝福",
        "boast": "吹嘘",
        "bold": "大胆的",
        "bond": "纽带；债券",
        "boost": "推动；提升",
        "border": "边界",
        "bother": "打扰",
        "boundary": "界限",
        "brake": "刹车",
        "brand": "品牌",
        "breach": "违反；缺口",
        "breakthrough": "突破",
        "breathe": "呼吸",
        "brief": "简短的",
        "brilliant": "杰出的",
        "broad": "宽阔的",
        "budget": "预算",
        "burden": "负担",
        "bureaucracy": "官僚制度",
        "cabin": "小屋；机舱",
        "calculate": "计算",
        "campaign": "运动；战役",
        "candidate": "候选人",
        "capable": "有能力的",
        "capacity": "容量；能力",
        "capital": "首都；资本",
        "capture": "俘获",
        "career": "职业",
        "careful": "小心的",
        "cargo": "货物",
        "carve": "雕刻",
        "casual": "随便的",
        "catalogue": "目录",
        "category": "类别",
        "cause": "原因；引起",
        "caution": "谨慎",
        "cease": "停止",
        "celebrate": "庆祝",
        "ceremony": "仪式",
        "challenge": "挑战",
        "chamber": "房间；议院",
        "champion": "冠军",
        "chaos": "混乱",
        "character": "性格；角色",
        "characteristic": "特征",
        "charge": "收费；指控",
        "charity": "慈善",
        "charm": "魅力",
        "chase": "追逐",
        "chat": "聊天",
        "cheat": "作弊",
        "cheer": "欢呼",
        "chemical": "化学的",
        "chief": "主要的；首领",
        "chip": "芯片；碎片",
        "choice": "选择",
        "choke": "窒息",
        "chronic": "慢性的",
        "circuit": "电路；巡回",
        "circumstance": "环境；情况",
        "cite": "引用",
        "citizen": "公民",
        "civil": "公民的；民事的",
        "claim": "声称；索赔",
        "clarify": "澄清",
        "classic": "经典的",
        "classify": "分类",
        "client": "客户",
        "climate": "气候",
        "cling": "紧贴",
        "clinic": "诊所",
        "clip": "夹子；剪辑",
        "clockwise": "顺时针",
        "clone": "克隆",
        "closet": "壁橱",
        "clue": "线索",
        "coarse": "粗糙的",
        "code": "代码；密码",
        "coincide": "同时发生",
        "collapse": "倒塌",
        "colleague": "同事",
        "collect": "收集",
        "collision": "碰撞",
        "colony": "殖民地",
        "column": "柱；专栏",
        "combat": "战斗",
        "combine": "结合",
        "comfort": "舒适；安慰",
        "command": "命令",
        "comment": "评论",
        "commerce": "商业",
        "commission": "委员会；佣金",
        "commit": "承诺；犯（罪）",
        "commodity": "商品",
        "common": "常见的",
        "communicate": "交流",
        "community": "社区",
        "commute": "通勤",
        "compact": "紧凑的",
        "companion": "同伴",
        "company": "公司；陪伴",
        "compare": "比较",
        "compassion": "同情",
        "compatible": "兼容的",
        "compel": "强迫",
        "compensate": "补偿",
        "compete": "竞争",
        "competent": "能胜任的",
        "compile": "编译；汇编",
        "complain": "抱怨",
        "complement": "补充",
        "complete": "完整的；完成",
        "complex": "复杂的",
        "complicate": "使复杂",
        "comply": "遵守",
        "component": "部件",
        "compose": "组成；作曲",
        "compound": "化合物；复合的",
        "comprehend": "理解",
        "comprehensive": "全面的",
        "comprise": "包含",
        "compromise": "妥协",
        "compute": "计算",
        "conceal": "隐藏",
        "concede": "承认；让步",
        "concentrate": "集中",
        "concept": "概念",
        "concern": "关心；担忧",
        "concert": "音乐会",
        "conclude": "得出结论",
        "concrete": "具体的；混凝土",
        "condemn": "谴责",
        "condense": "浓缩",
        "condition": "条件；状况",
        "conduct": "进行；行为",
        "confer": "商议；授予",
        "confess": "坦白",
        "confidence": "信心",
        "confine": "限制",
        "confirm": "确认",
        "conflict": "冲突",
        "conform": "遵从",
        "confront": "面对",
        "confuse": "使困惑",
        "congratulate": "祝贺",
        "congress": "国会",
        "connect": "连接",
        "conscience": "良心",
        "conscious": "有意识的",
        "consecutive": "连续的",
        "consensus": "共识",
        "consent": "同意",
        "consequence": "后果",
        "conservative": "保守的",
        "consider": "考虑",
        "consist": "由…组成",
        "console": "安慰；控制台",
        "consolidate": "巩固",
        "constant": "不断的",
        "constitute": "构成",
        "constrain": "约束",
        "construct": "建造",
        "consult": "咨询",
        "consume": "消耗",
        "contact": "接触",
        "contain": "包含",
        "contemporary": "当代的",
        "contempt": "轻蔑",
        "contend": "竞争；主张",
        "content": "内容；满足的",
        "contest": "比赛",
        "context": "语境；背景",
        "continent": "大陆",
        "continue": "继续",
        "contract": "合同；收缩",
        "contradict": "反驳",
        "contrary": "相反的",
        "contrast": "对比",
        "contribute": "贡献",
        "controversy": "争论",
        "convenience": "便利",
        "convention": "惯例；大会",
        "converse": "交谈；相反的",
        "convert": "转换",
        "convey": "传达",
        "convict": "定罪",
        "convince": "说服",
        "cooperate": "合作",
        "coordinate": "协调",
        "cope": "应付",
        "copyright": "版权",
        "core": "核心",
        "corporate": "公司的",
        "correct": "正确的；纠正",
        "correspond": "通信；相符",
        "corridor": "走廊",
        "corrupt": "腐败的",
        "cost": "成本",
        "council": "委员会",
        "counsel": "劝告；律师",
        "count": "计数",
        "counter": "柜台；反击",
        "county": "郡；县",
        "couple": "一对；夫妇",
        "courage": "勇气",
        "course": "课程；过程",
        "court": "法院；球场",
        "courtesy": "礼貌",
        "cover": "覆盖",
        "crack": "裂缝；破解",
        "craft": "手艺",
        "crash": "碰撞；崩溃",
        "crawl": "爬行",
        "create": "创造",
        "creature": "生物",
        "credible": "可信的",
        "credit": "信用；学分",
        "creep": "爬行；蔓延",
        "crew": "全体船员",
        "crime": "犯罪",
        "crisis": "危机",
        "criterion": "标准",
        "critic": "批评家",
        "critical": "关键的；批评的",
        "criticism": "批评",
        "crop": "作物",
        "cross": "穿过；交叉",
        "crowd": "人群",
        "crucial": "至关重要的",
        "crude": "粗糙的；原油",
        "cruel": "残忍的",
        "crush": "压碎",
        "crystal": "水晶",
        "cultivate": "耕作；培养",
        "culture": "文化",
        "cunning": "狡猾的",
        "cure": "治愈",
        "curious": "好奇的",
        "current": "当前的；电流",
        "curriculum": "课程",
        "curve": "曲线",
        "custom": "习俗；海关",
        "cycle": "循环",
        "cynical": "愤世嫉俗的",
        "damage": "损害",
        "damp": "潮湿的",
        "dare": "敢于",
        "dash": "猛冲",
        "data": "数据",
        "debate": "辩论",
        "debt": "债务",
        "decade": "十年",
        "decay": "腐烂；衰败",
        "deceive": "欺骗",
        "decent": "像样的",
        "decide": "决定",
        "declare": "宣布",
        "decline": "下降；婉拒",
        "decorate": "装饰",
        "decrease": "减少",
        "dedicate": "奉献",
        "deduce": "推断",
        "defeat": "击败",
        "defect": "缺陷",
        "defend": "保卫",
        "deficit": "赤字",
        "define": "定义",
        "definite": "明确的",
        "degree": "程度；学位",
        "delay": "延迟",
        "delegate": "代表；委派",
        "delete": "删除",
        "deliberate": "故意的；深思熟虑",
        "delicate": "精致的；脆弱的",
        "delight": "高兴",
        "deliver": "递送",
        "demand": "要求",
        "democracy": "民主",
        "demonstrate": "证明；演示",
        "dense": "密集的",
        "deny": "否认",
        "depart": "离开",
        "depend": "依赖",
        "depict": "描绘",
        "deposit": "存款；沉积",
        "depress": "使沮丧",
        "deprive": "剥夺",
        "derive": "源自",
        "descend": "下降",
        "describe": "描述",
        "desert": "沙漠；遗弃",
        "deserve": "值得",
        "design": "设计",
        "desire": "欲望",
        "desperate": "绝望的",
        "despite": "尽管",
        "destination": "目的地",
        "destroy": "摧毁",
        "detail": "细节",
        "detect": "察觉",
        "determine": "决定；确定",
        "develop": "发展",
        "device": "装置",
        "devote": "致力于",
        "diagnose": "诊断",
        "diagram": "图表",
        "dialect": "方言",
        "dialogue": "对话",
        "diameter": "直径",
        "dictate": "口授；支配",
        "differ": "不同",
        "difficult": "困难的",
        "diffuse": "扩散",
        "digest": "消化；摘要",
        "digital": "数字的",
        "dignity": "尊严",
        "dilemma": "困境",
        "diligent": "勤奋的",
        "dimension": "维度",
        "diminish": "减少",
        "dine": "进餐",
        "diploma": "文凭",
        "direct": "直接的；指导",
        "disable": "使残疾；禁用",
        "disagree": "不同意",
        "disappear": "消失",
        "disappoint": "使失望",
        "disaster": "灾难",
        "discard": "丢弃",
        "discharge": "排放；解雇",
        "discipline": "纪律",
        "disclose": "披露",
        "discount": "折扣",
        "discourage": "使气馁",
        "discover": "发现",
        "discrete": "离散的",
        "discriminate": "歧视；辨别",
        "discuss": "讨论",
        "disease": "疾病",
        "disguise": "伪装",
        "disgust": "厌恶",
        "disk": "磁盘",
        "dismiss": "解雇；驳回",
        "disorder": "紊乱",
        "dispatch": "派遣",
        "disperse": "分散",
        "displace": "取代",
        "display": "展示",
        "dispose": "处理；处置",
        "dispute": "争论",
        "disrupt": "扰乱",
        "dissolve": "溶解",
        "distance": "距离",
        "distinct": "明显不同的",
        "distinguish": "区分",
        "distort": "扭曲",
        "distract": "分心",
        "distribute": "分发",
        "district": "区域",
        "disturb": "打扰",
        "dive": "潜水",
        "diverse": "多样的",
        "divide": "分开",
        "divine": "神圣的",
        "division": "部门；除法",
        "divorce": "离婚",
        "document": "文件",
        "domain": "领域",
        "domestic": "国内的；家庭的",
        "dominant": "占优势的",
        "donate": "捐赠",
        "dose": "剂量",
        "double": "双倍的",
        "doubt": "怀疑",
        "downtown": "市中心",
        "draft": "草稿；征兵",
        "drain": "排水",
        "drama": "戏剧",
        "drastic": "激烈的",
        "draw": "画；吸引",
        "drift": "漂流",
        "drill": "钻孔；训练",
        "drought": "干旱",
        "drown": "淹死",
        "drug": "药物",
        "due": "到期的",
        "dull": "乏味的",
        "dump": "倾倒",
        "durable": "耐用的",
        "duration": "持续时间",
        "during": "在…期间",
        "dust": "灰尘",
        "duty": "职责",
        "dwell": "居住",
        "dynamic": "动态的",
    }
    words.update(seed)

    # Try free CEFR word list (English only); keep existing Chinese gloss or placeholder.
    try:
        raw = fetch_text(
            "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt"
        )
        for line in raw.splitlines()[:3500]:
            w = line.split()[0].strip().lower()
            if not w.isalpha() or len(w) < 4 or len(w) > 14:
                continue
            words.setdefault(w, "（英）常用词")
    except Exception as e:
        print("EN freq fetch failed:", e)

    # Prefer entries with real Chinese gloss
    items = [{"word": w, "meaning": m, "lang": "英语", "hint": "B1+"} for w, m in sorted(words.items()) if m != "（英）常用词"]
    # Add some frequency words with placeholder meanings for typing variety
    typing_extra = [w for w, m in words.items() if m == "（英）常用词"][:800]
    for w in typing_extra:
        items.append({"word": w, "meaning": "常用英语词", "lang": "英语", "hint": "freq"})

    BANK.joinpath("english.json").write_text(
        json.dumps({"source": "expanded-b1c1", "words": items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    typing = [{"display": it["word"], "target": it["word"].lower()} for it in items]
    BANK.joinpath("typing_english.json").write_text(
        json.dumps({"source": "expanded-b1c1", "items": typing}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("english vocab", len(items), "typing", len(typing))


def expand_chinese() -> None:
    """HSK-style harder Chinese + pinyin targets for typing."""
    # word, meaning, pinyin(no tone)
    seed: list[tuple[str, str, str]] = [
        ("尴尬", "处境为难，难为情", "ganga"),
        ("犹豫", "拿不定主意", "youyu"),
        ("谨慎", "小心慎重", "jinshen"),
        ("敷衍", "做事不认真，表面应付", "fuyan"),
        ("挑剔", "过分在意缺点", "tiaoti"),
        ("苛刻", "要求过于严厉", "keke"),
        ("固执", "坚持己见不改变", "guzhi"),
        ("委婉", "说话婉转不生硬", "weiwan"),
        ("含蓄", "不直接表达", "hanxu"),
        ("讽刺", "用反话批评", "fengci"),
        ("讽刺画", "带讽刺意味的画", "fengcihua"),
        ("隐喻", "暗含的比喻", "yinyu"),
        ("象征", "用具体事物表示抽象意义", "xiangzheng"),
        ("抽象", "概括的、不具体的", "chouxiang"),
        ("具体", "明确细致的", "juti"),
        ("辩证", "用对立统一看问题", "bianzheng"),
        ("逻辑", "思维规律；条理", "luoji"),
        ("推理", "由已知推出未知", "tuili"),
        ("假设", "姑且认定", "jiashe"),
        ("论证", "用论据证明", "lunzheng"),
        ("批判", "分析并评价", "pipan"),
        ("审视", "仔细察看", "shenshi"),
        ("洞察", "看穿本质", "dongcha"),
        ("敏锐", "感觉灵敏", "minrui"),
        ("迟钝", "反应慢", "chidun"),
        ("麻木", "感觉缺失；无动于衷", "mamu"),
        ("冷漠", "不关心", "lengmo"),
        ("热情", "热烈的感情", "reqing"),
        ("真诚", "真实诚恳", "zhencheng"),
        ("虚伪", "不真实，做作", "xuwei"),
        ("谦虚", "不自满", "qianxu"),
        ("傲慢", "看不起人", "aoman"),
        ("偏见", "不公正的看法", "pianjian"),
        ("歧视", "不公平对待", "qishi"),
        ("包容", "宽容接纳", "baorong"),
        ("妥协", "互相让步", "tuoxie"),
        ("协商", "共同商量", "xieshang"),
        ("谈判", "协商议定", "tanpan"),
        ("协议", "共同议定的条款", "xieyi"),
        ("契约", "合同；约定", "qiyue"),
        ("义务", "应尽的责任", "yiwu"),
        ("权利", "依法享有的利益", "quanli"),
        ("权力", "支配力量", "quanli2"),
        ("权威", "使人信从的力量", "quanwei"),
        ("威望", "声誉与影响力", "weiwang"),
        ("声望", "众所周知的好名声", "shengwang"),
        ("名誉", "名声", "mingyu"),
        ("信誉", "信用和名誉", "xinyu"),
        ("诚信", "诚实守信", "chengxin"),
        ("欺诈", "欺骗讹诈", "qizha"),
        ("贿赂", "用财物收买", "huilu"),
        ("腐败", "堕落；糜烂", "fubai"),
        ("廉洁", "不贪污", "lianjie"),
        ("公正", "公平正直", "gongzheng"),
        ("公平", "不偏不倚", "gongping"),
        ("平等", "同等待遇", "pingdeng"),
        ("自由", "不受拘束", "ziyou"),
        ("民主", "人民当家作主", "minzhu"),
        ("专制", "独断专行", "zhuanzhi"),
        ("独裁", "独自裁断一切", "ducai"),
        ("改革", "改掉弊病", "gaige"),
        ("革命", "根本变革", "geming"),
        ("创新", "创造出新事物", "chuangxin"),
        ("发明", "创造出新方法等", "faming"),
        ("发现", "找到未知事物", "faxian"),
        ("探索", "多方寻求", "tansuo"),
        ("研究", "钻研探求", "yanjiu"),
        ("实验", "为检验而做的操作", "shiyan"),
        ("观察", "仔细察看", "guancha"),
        ("测量", "用仪器量度", "celiang"),
        ("统计", "汇总分析数据", "tongji"),
        ("概率", "可能性大小", "gailv"),
        ("比例", "数量之比", "bili"),
        ("效率", "单位时间完成量", "xiaolv"),
        ("效益", "效果和利益", "xiaoyi"),
        ("成本", "生产耗费", "chengben"),
        ("利润", "盈利", "lirun"),
        ("投资", "投入资金", "touzi"),
        ("消费", "消耗使用", "xiaofei"),
        ("市场", "买卖场所；供求关系", "shichang"),
        ("竞争", "互相争胜", "jingzheng"),
        ("垄断", "独占", "longduan"),
        ("供应", "提供所需", "gongying"),
        ("需求", "需要", "xuqiu"),
        ("短缺", "不足", "duanque"),
        ("过剩", "超过需要", "guosheng"),
        ("通胀", "通货膨胀简称", "tongzhang"),
        ("通缩", "通货紧缩简称", "tongsuo"),
        ("预算", "预先计算收支", "yusuan"),
        ("决算", "最终核算", "juesuan"),
        ("审计", "检查账目", "shenji"),
        ("税务", "税收事务", "shuiwu"),
        ("关税", "进出口税", "guanshui"),
        ("补贴", "财政补助", "butie"),
        ("津贴", "额外补助", "jintie"),
        ("薪酬", "工资报酬", "xinchou"),
        ("绩效", "成绩与效果", "jixiao"),
        ("考核", "考查审核", "kaohe"),
        ("晋升", "提升职位", "jinsheng"),
        ("解雇", "解除雇佣", "jiegu"),
        ("辞职", "请求解除职务", "cizhi"),
        ("退休", "离开工作岗位养老", "tuixiu"),
        ("合同", "双方约定文书", "hetong"),
        ("条款", "条文项目", "tiaokuan"),
        ("违约", "不履行约定", "weiyue"),
        ("赔偿", "补偿损失", "peichang"),
        ("诉讼", "打官司", "susong"),
        ("仲裁", "由第三方裁决", "zhongcai"),
        ("证据", "证明事实的材料", "zhengju"),
        ("证人", "作证的人", "zhengren"),
        ("被告", "被起诉的一方", "beigao"),
        ("原告", "提起诉讼的一方", "yuangao"),
        ("判决", "法院裁断", "panjue"),
        ("上诉", "向上级法院请求改判", "shangsu"),
        ("辩护", "提出理由保护", "bianhu"),
        ("指控", "指责控告", "zhikong"),
        ("嫌疑", "被怀疑", "xianyi"),
        ("审讯", "审问", "shenxun"),
        ("刑罚", "刑事处罚", "xingfa"),
        ("赦免", "免除刑罚", "shemian"),
        ("通缉", "通令缉拿", "tongji2"),
        ("逮捕", "捉拿归案", "daibu"),
        ("拘留", "临时关押", "juliu"),
        ("保释", "交保释放", "baoshi"),
        ("监狱", "关押犯人的处所", "jianyu"),
        ("囚犯", "被关押的人", "qiufan"),
        ("受害者", "受害的人", "shouhaizhe"),
        ("目击者", "亲眼看见的人", "mujizhe"),
        ("幸存者", "活下来的人", "xingcunzhe"),
        ("志愿者", "自愿服务的人", "zhiyuanzhe"),
        ("公民", "具有国籍的人", "gongmin"),
        ("居民", "固定居住的人", "jumin"),
        ("移民", "迁移到他国的人", "yimin"),
        ("难民", "因灾难逃亡的人", "nanmin"),
        ("精英", "出类拔萃的人", "jingying"),
        ("平民", "普通百姓", "pingmin"),
        ("贵族", "享有特权的阶层", "guizu"),
        ("官僚", "官员；官僚主义", "guanliao"),
        ("政客", "从事政治活动的人", "zhengke"),
        ("外交", "国与国交往", "waijiao"),
        ("同盟", "结成的联盟", "tongmeng"),
        ("条约", "国家间协议", "tiaoyue"),
        ("制裁", "惩罚约束", "zhicai"),
        ("干预", "过问插手", "ganyu"),
        ("干涉", "强行介入", "ganshe"),
        ("独立", "不依赖他人", "duli"),
        ("主权", "国家最高权力", "zhuquan"),
        ("领土", "国家管辖土地", "lingtu"),
        ("边境", "靠近边界一带", "bianjing"),
        ("海关", "监管进出境机关", "haiguan"),
        ("签证", "入境许可证明", "qianzheng"),
        ("护照", "国籍身份证件", "huzhao"),
        ("身份", "人的社会地位", "shenfen"),
        ("地位", "所处位置", "diwei"),
        ("阶层", "社会等级层次", "jieceng"),
        ("贫富", "贫穷与富裕", "pinfu"),
        ("差距", "事物间的差别程度", "chaju"),
        ("贫困", "生活困难", "pinkun"),
        ("富裕", "财物充裕", "fuyu"),
        ("温饱", "吃穿基本满足", "wenbao"),
        ("小康", "生活比较宽裕", "xiaokang"),
        ("繁荣", "昌盛兴旺", "fanrong"),
        ("萧条", "冷落不景气", "xiaotiao"),
        ("复苏", "恢复生机", "fusu"),
        ("危机", "严重困难关头", "weiji"),
        ("风险", "可能发生的危险", "fengxian"),
        ("机遇", "好的机会", "jiyu"),
        ("挑战", "激励人的难题", "tiaozhan"),
        ("机遇与挑战", "机会和困难并存", "jiyuyutiaozhan"),
        ("战略", "全局性谋划", "zhanlue"),
        ("战术", "具体作战方法", "zhanshu"),
        ("策略", "计策谋略", "celue"),
        ("规划", "长远计划", "guihua"),
        ("蓝图", "建设规划", "lantu"),
        ("愿景", "向往的前景", "yuanjing"),
        ("使命", "重大责任", "shiming"),
        ("价值观", "价值判断标准", "jiazhiguan"),
        ("世界观", "对世界的总看法", "shijieguan"),
        ("人生观", "对人生的看法", "renshengguan"),
        ("道德", "行为规范", "daode"),
        ("伦理", "人伦道德之理", "lunli"),
        ("良知", "先天的道德意识", "liangzhi"),
        ("良心", "内心的是非感", "liangxin"),
        ("忏悔", "认识错误并悔改", "chanhui"),
        ("救赎", "挽救使脱离苦难", "jiushu"),
        ("信仰", "极度相信并尊奉", "xinyang"),
        ("迷信", "盲目信仰", "mixin"),
        ("宗教", "对神的信仰体系", "zongjiao"),
        ("哲学", "世界观理论", "zhexue"),
        ("美学", "研究美的学科", "meixue"),
        ("艺术", "创造性审美活动", "yishu"),
        ("文学", "以语言文字为工具的艺术", "wenxue"),
        ("诗歌", "韵文作品", "shige"),
        ("小说", "叙事性文学体裁", "xiaoshuo"),
        ("戏剧", "舞台表演艺术", "xiju"),
        ("电影", "影像艺术", "dianying"),
        ("摄影", "用相机记录影像", "sheying"),
        ("雕塑", "立体造型艺术", "diaosu"),
        ("建筑", "建造房屋等", "jianzhu"),
        ("遗产", "留下的财富或文化", "yichan"),
        ("文物", "历史文化遗物", "wenwu"),
        ("古迹", "古代遗迹", "guji"),
        ("遗址", "古代建筑残迹", "yizhi"),
        ("出土", "从地下发掘出来", "chutu"),
        ("考古", "研究古代遗迹", "kaogu"),
        ("文明", "社会发展高水平状态", "wenming"),
        ("野蛮", "不文明", "yeman"),
        ("原始", "最初的；未开化的", "yuanshi"),
        ("现代", "当前这个时代", "xiandai"),
        ("当代", "目前这个时代", "dangdai"),
        ("古代", "过去很久的时代", "gudai"),
        ("近代", "离现代较近的时代", "jindai"),
        ("未来", "将来", "weilai"),
        ("过去", "以前的时间", "guoqu"),
        ("现在", "当前", "xianzai"),
        ("瞬间", "极短的时间", "shunjian"),
        ("永恒", "长久不变", "yongheng"),
        ("短暂", "时间短", "duanzan"),
        ("漫长", "时间很长", "manchang"),
        ("迅速", "非常快", "xunsu"),
        ("缓慢", "速度慢", "huanman"),
        ("剧烈", "猛烈", "juliie"),
        ("剧烈", "猛烈强烈", "julie"),
        ("温和", "不剧烈；平和", "wenhe"),
        ("激烈", "剧烈紧张", "jilie"),
        ("平静", "安定安宁", "pingjing"),
        ("喧嚣", "声音嘈杂", "xuanxiao"),
        ("寂静", "没有声音", "jijing"),
        ("热闹", "景象繁荣活跃", "renao"),
        ("冷清", "冷落凄清", "lengqing"),
        ("繁荣昌盛", "兴旺发达", "fanrongchangsheng"),
        ("日新月异", "发展很快", "rixinyueyi"),
        ("与时俱进", "随时代进步", "yushijujin"),
        ("实事求是", "从实际出发", "shishiquishi"),
        ("举一反三", "由一事推知其他", "juyifansan"),
        ("触类旁通", "掌握一类通晓相似", "chuleipangtong"),
        ("融会贯通", "融合理解透彻", "ronghuiguantong"),
        ("循序渐进", "按步骤推进", "xunxujianjin"),
        ("持之以恒", "长久坚持", "chizhiyiheng"),
        ("半途而废", "做事中途停止", "bantuerfei"),
        ("一丝不苟", "做事认真细致", "yisibugou"),
        ("精益求精", "好了还求更好", "jingyiqiujing"),
        ("敷衍了事", "随便应付完事", "fuyanliaoshi"),
        ("弄虚作假", "用虚假手段欺骗", "nongxuzuojia"),
        ("实事求是", "按实际情况办事", "shishiquishi2"),
        ("脚踏实地", "做事踏实", "jiaotashidi"),
        ("好高骛远", "不切实际追求过高", "haogaowuyuan"),
        ("急功近利", "急于求成贪图眼前", "jigongjinli"),
        ("深谋远虑", "计划周密考虑长远", "shenmouyuanlv"),
        ("未雨绸缪", "事先做好准备", "weiyuchoumou"),
        ("临阵磨枪", "事到临头才准备", "linzhenmoqiang"),
        ("亡羊补牢", "出了问题及时补救", "wangyangbulao"),
        ("防患未然", "在祸患发生前预防", "fanghuanweiran"),
        ("居安思危", "安定时想到危险", "juansisiwei"),
        ("戒骄戒躁", "防止骄傲急躁", "jieqiaojiezao"),
        ("谦虚谨慎", "虚心又慎重", "qianxujinshen"),
        ("戒骄戒躁", "去掉骄傲急躁", "jieqiaojiezao2"),
        ("集思广益", "集中众人智慧", "jisiguangyi"),
        ("群策群力", "大家共同出力出主意", "quncequnli"),
        ("独断专行", "凭自己意思行事", "duduanxingzhuan"),
        ("一意孤行", "不听劝告坚持己见", "yiyiguxing"),
        ("从善如流", "接受好意见很快", "congshanruli"),
        ("刚愎自用", "固执任性自以为是", "gangbiziyong"),
        ("虚怀若谷", "胸怀宽广能接受意见", "xuhuairuogu"),
        ("海纳百川", "包容一切", "hainabaichuan"),
        ("兼容并包", "把各个方面都容纳进来", "jianrongbingbao"),
        ("求同存异", "找出共同点保留不同点", "qiutongcunyi"),
        ("和而不同", "和谐但不盲从", "heerbutong"),
        ("同舟共济", "同心协力渡过困难", "tongzhougongji"),
        ("风雨同舟", "共同经历患难", "fengyutongzhou"),
        ("患难与共", "一同承受困难", "huannanyugong"),
        ("荣辱与共", "荣耀耻辱共同承担", "rongruyugong"),
        ("肝胆相照", "真诚相待", "gandanxianzhao"),
        ("推心置腹", "真心待人", "tuixinzhifu"),
        ("尔虞我诈", "互相欺骗", "eryuwuzha"),
        ("钩心斗角", "互相排挤倾轧", "gouxindoujiao"),
        ("阳奉阴违", "表面遵从暗地违背", "yangfengyinwei"),
        ("口是心非", "嘴里说的和心里想的不一致", "koushixinfei"),
        ("言不由衷", "说的话不是真心话", "yanbuyouzhong"),
        ("心口如一", "心里想的和嘴上说的一致", "xinkouruyi"),
        ("光明磊落", "正直坦率", "guangmingleiluo"),
        ("光明正大", "行为正当无可指责", "guangmingzhengda"),
        ("偷偷摸摸", "瞒着人做事", "toutoumomo"),
        ("鬼鬼祟祟", "行动偷偷摸摸", "guiguisuisui"),
        ("堂堂正正", "光明正大", "tangtangzhengzheng"),
        ("正大光明", "公正无私", "zhengdaguangming"),
    ]
    # dedupe by word
    seen: set[str] = set()
    words = []
    typing = []
    for w, m, py in seed:
        if w in seen:
            continue
        seen.add(w)
        words.append({"word": w, "meaning": m, "lang": "中文", "hint": "进阶"})
        typing.append({"display": w, "target": py.lower()})

    # Try HSK list if available
    try:
        raw = fetch_text(
            "https://raw.githubusercontent.com/krmanik/HSK-3.0/main/HSK%20List/HSK%205.txt"
        )
        for line in raw.splitlines():
            parts = line.strip().split()
            if not parts:
                continue
            w = parts[0]
            if w in seen or len(w) < 2:
                continue
            seen.add(w)
            # rough pinyin absent; skip typing or use word itself for IME typing
            words.append({"word": w, "meaning": "HSK5 词汇", "lang": "中文", "hint": "HSK5"})
            typing.append({"display": w, "target": w})  # 可用输入法直接打汉字
    except Exception as e:
        print("HSK fetch failed:", e)

    try:
        raw = fetch_text(
            "https://raw.githubusercontent.com/krmanik/HSK-3.0/main/HSK%20List/HSK%206.txt"
        )
        for line in raw.splitlines():
            parts = line.strip().split()
            if not parts:
                continue
            w = parts[0]
            if w in seen or len(w) < 2:
                continue
            seen.add(w)
            words.append({"word": w, "meaning": "HSK6 词汇", "lang": "中文", "hint": "HSK6"})
            typing.append({"display": w, "target": w})
    except Exception as e:
        print("HSK6 fetch failed:", e)

    BANK.joinpath("chinese.json").write_text(
        json.dumps({"source": "expanded-hsk-plus", "words": words}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    BANK.joinpath("typing_chinese.json").write_text(
        json.dumps({"source": "expanded-hsk-plus", "items": typing}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("chinese vocab", len(words), "typing", len(typing))


def rebuild_japanese_typing() -> None:
    """Prompt = Chinese meaning; type kana (or romaji). Prefer kana-only readings."""
    vocab = json.loads((BANK / "japanese.json").read_text(encoding="utf-8"))
    words = vocab.get("words") if isinstance(vocab, dict) else vocab
    old = json.loads((BANK / "typing_japanese.json").read_text(encoding="utf-8"))
    old_items = old.get("items") if isinstance(old, dict) else old
    romaji_by_display = {}
    for it in old_items:
        if isinstance(it, dict) and it.get("display") and it.get("target"):
            romaji_by_display[str(it["display"])] = str(it["target"]).lower()

    items = []
    seen = set()
    for it in words:
        if not isinstance(it, dict):
            continue
        word = str(it.get("word", "")).strip()
        meaning = str(it.get("meaning", "")).strip()
        if not word:
            continue
        roma = romaji_by_display.get(word, "")
        if is_kana(word):
            kana = word
            if not roma:
                # leave empty; game can still accept kana
                roma = ""
        else:
            if not roma:
                continue
            kana = romaji_to_hiragana(roma)
            if not kana:
                continue
        # display prompt: Chinese gloss + show kana hint
        prompt = meaning.split("；")[0].split(";")[0].strip() if meaning else "日语词"
        if not prompt:
            prompt = "日语词"
        key = (kana, roma)
        if key in seen:
            continue
        seen.add(key)
        entry = {
            "display": f"{prompt}（{kana}）",
            "target": kana,
        }
        if roma:
            entry["romaji"] = roma
        items.append(entry)

    # also add pure kana drills from old bank
    for it in old_items:
        if not isinstance(it, dict):
            continue
        disp = str(it.get("display", ""))
        roma = str(it.get("target", "")).lower()
        if not is_kana(disp):
            continue
        key = (disp, roma)
        if key in seen:
            continue
        seen.add(key)
        items.append({"display": f"读音（{disp}）", "target": disp, "romaji": roma})

    BANK.joinpath("typing_japanese.json").write_text(
        json.dumps(
            {
                "source": "jlpt-kana-romaji",
                "note": "display=中文释义提示；target=平假名；romaji=可替代输入",
                "items": items,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("japanese typing", len(items), "sample", items[:3])


if __name__ == "__main__":
    expand_english()
    expand_chinese()
    rebuild_japanese_typing()
    print("done")
