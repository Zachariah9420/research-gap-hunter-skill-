#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""format_check.py — research-gap-hunter 報告的「格式」查核器。

純標準函式庫、不連網、不呼叫任何 LLM。輸入一份 research-gap-hunter 產出的
報告（.md 或 .txt），輸出違規清單。

兩種報告、兩套規則，型別看第一行的 H1（表頭〈模式〉是第二判別點）：
  - `# 研究缺口報告：…`  → 候選、判定、淘汰、檢索紀錄那一套（Checker）
  - `# 領域地形報告：…`  → 家族、成本、狀態、牆那一套（LandscapeChecker）
地形報告不判新穎性、不淘汰，所以缺口那一套規則多數在它身上沒有對象；
兩套互不套用。認不出型別時當成缺口報告——新增模式不該讓舊模式悄悄失去查核。

**定位一律靠形狀，不靠節名。** 這一條是本檔的骨幹，不是某幾個地方的補丁：
表要靠表頭欄位認、家族與候選區塊要靠它們自己帶的欄位行認、預設行要靠它自己的
行形狀認。任何「先看這一節叫什麼名字、再決定要不要解析底下的東西」的寫法，
都等於把一整批規則掛在一個字串上——節名一改，那批規則就安靜地失去對象，
整份報告變成「沒有這一節因此沒有違規」，那是最壞的一種綠燈（比漏抓更壞：
它讓作者以為跑過了）。節名本身**不得改寫**（SKILL.md〈輸出格式〉），
所以改寫過的節名是它自己的一條違規（SECT-01），不是停止檢查的理由。

它檢查的是**形式**，不是**真假**：
  - 它能抓到「這個 DONE 沒有指名殺死候選的文獻」；
  - 它抓不到「這篇被指名的文獻其實不存在，或講的是別的事」。

存在性、撤稿、書目正確性是 lit-review 的工作（verify / retract / check）。
本檔只保證報告的自我宣稱是完整的、可稽核的、措辭沒有越界。

敘事型文件（教學走查、README 片段）不是報告：在報告區塊前後各放一行
    <!-- format-check: report-start -->
    <!-- format-check: report-end -->
本檔就只查兩個標記之間的內容，行號仍以原檔為準。沒有標記時整份檔案都會被查。

用法：
    python evals/format_check.py <report.md>
    python evals/format_check.py <report.md> --json

離開碼：
    0  無違規
    1  有違規
    2  用法或讀檔錯誤
"""

import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# --------------------------------------------------------------------------
# 詞彙表：與 SKILL.md〈第 3 步〉的判定表、〈第 5 步〉的輸出格式對齊
# --------------------------------------------------------------------------

# 只有這三個可以出現在「二、存活候選」的〈新穎性判定〉
SURVIVOR_VERDICTS = {"ADJACENT", "OPEN", "INCREMENTAL"}

# 只有這兩個可以出現在「四、已淘汰」的〈判定〉欄
KILL_VERDICTS = {"DONE", "CROWDED"}

# 只有這些可以出現在「三、待確認」的〈暫定狀態〉欄。
# SKILL.md 用〔〕標記，括號可有可無；逗號分句的簡寫形式一併收進來。
PENDING_STATES = {
    "DONE?", "待驗證", "待全文查證", "矛盾已觀察，機制未知", "矛盾已觀察",
    "已排隊", "已有人在做（預印本）", "已有人在做", "待再查", "UNSEARCHABLE",
    "未驗證",
}

# 任何「判定／狀態」欄位允許的值（跨區段的聯集，區段限制由 VERDICT-02 負責）
ALLOWED_VERDICTS = SURVIVOR_VERDICTS | KILL_VERDICTS | PENDING_STATES


# --------------------------------------------------------------------------
# 領域地形報告（landscape）：另一種文件形狀，另一套規則
#
# 這一份不判新穎性、不淘汰，所以缺口報告那 21 條裡有 19 條在它身上沒有對象。
# 反過來，它自己會壞的地方缺口報告沒有——最主要是「悄悄漂移成判決」。
# 判別型別看第一行的 H1，退而求其次看表頭〈模式〉。
# --------------------------------------------------------------------------

LANDSCAPE_H1_RE = re.compile(r"^#\s*領域地形報告")
GAP_H1_RE = re.compile(r"^#\s*研究缺口報告")
LANDSCAPE_MODE_RE = re.compile(r"^模式\s*[：:]\s*領域地形")

# 表頭那一行是固定句，逐字比對（SKILL.md〈landscape 輸出格式〉）
LANDSCAPE_DISCLAIMER_LABEL = "這份報告不做什麼"
LANDSCAPE_DISCLAIMER = (
    "不淘汰任何做法、不判斷新穎性、不宣稱任何做法沒有人做過。要新穎性判定請跑缺口獵捕。"
)

# 新穎性判定詞彙：地形報告裡出現任何一個，就是這個模式最主要的失效方式。
# 詞表**推導自**缺口報告的兩個集合，不另抄一份——獵捕新增判定時這道防線自動跟上。
# 大小寫敏感：判定值在規格裡一律全大寫，若忽略大小寫，英文標題裡的 open／done
# 會被誤殺，而那正是「守則寬到沒人理它」的起手式。
NOVELTY_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_\-])(%s)(?![A-Za-z0-9_\-])"
    % "|".join(sorted(SURVIVOR_VERDICTS | KILL_VERDICTS))
)

# 〈狀態〉只有五個合法值；前四個必須在同一欄掛上檢索句型
LAND_STATUS_VALUES = ("飽和", "活躍", "新興", "衰退", "涵蓋不足")
LAND_STATUS_EVIDENCE_RE = re.compile(r"回傳\s*\d+\s*筆")

# 第二節的預設編號 F1-a，與第六節〈來源預設〉欄對帳用
LAND_ASSUM_ID_RE = re.compile(r"(?<![A-Za-z0-9])[Ff](\d{1,2})-([A-Za-z])(?![A-Za-z0-9])")
# 家族標題。允許「家族」前綴（`### 家族 F1：遙測綠覆指數`）——樣板寫的是 `### F1 <名稱>`，
# 而加一個詞是散文最常見的漂移方式，多認一種形狀不花任何東西。
LAND_FAMILY_HEAD_RE = re.compile(r"^(?:家族\s*)?[Ff](\d{1,2})\b[\s：:.\-]*(.*)$")
LAND_FAMILY_LOOKALIKE_RE = re.compile(r"家族|(?<![A-Za-z0-9])[Ff]\s*\d")

LAND_LABEL_ALIASES = {
    "oneline": ("一句話",),
    "buys": ("買到什麼", "買到"),
    "costs": ("付出什麼", "付出"),
    "anchors": ("錨定文獻",),
    "status": ("狀態",),
    "cannot": ("結構上做不到",),
    "assumptions": ("默默預設",),
    "entry": ("進入成本",),
}

# 一眼表與牆表各用自己的欄位別名：兩張表都有「家族」字樣，共用一份會互相搶欄
LAND_GLANCE_COLUMNS = {
    "family": ("家族",),
    "oneline": ("一句話",),
    "buys": ("買到",),
    "costs": ("付出",),
    "status": ("狀態",),
    "anchors": ("錨定文獻數", "錨定"),
}
LAND_WALL_COLUMNS = {
    "wall": ("牆",),
    "sources": ("來源預設",),
    "famcount": ("家族數",),
    "nature": ("性質",),
    "breaking": ("拆的可能性",),
    "statement": ("這條預設",),
}


# --------------------------------------------------------------------------
# 標籤同義詞：容忍 SKILL.md 的小幅措辭漂移
# --------------------------------------------------------------------------

LABEL_ALIASES = {
    "evidence": ("搜尋證據", "檢索證據", "證據", "查詢證據", "search evidence"),
    "verdict": ("新穎性判定", "判定", "新穎性", "verdict"),
    "gap_type": ("缺口類型", "生成器", "gap type"),
    "neighbour": ("最接近的既有研究", "最近鄰文獻", "最接近文獻", "最近鄰", "nearest"),
    "queued": ("已排隊檢查", "排隊檢查", "queued"),
    "feasible": ("可行性", "feasibility"),
    "advisor": ("指導教授適配", "指導教授", "advisor"),
    "failure": ("最可能失敗的原因", "失敗原因", "failure"),
}

COLUMN_ALIASES = {
    "candidate": ("候選", "題目", "candidate"),
    "verdict": ("判定", "新穎性判定", "verdict"),
    "state": ("暫定狀態", "狀態", "state"),
    "missing": ("還缺", "缺哪一項", "缺少的證據"),
    "action": ("補齊", "具體動作", "action"),
    "reason": ("淘汰原因", "原因", "理由", "reason"),
    "literature": ("關鍵文獻", "殺手文獻", "文獻", "literature"),
    "identifier": ("識別碼", "doi", "id", "identifier"),
    "pubtype": ("發表型態", "型態", "type"),
    "retract": ("撤稿檢查", "撤稿", "retract"),
    "query": ("查詢詞", "查詢", "檢索詞", "query"),
    "hits": ("回傳筆數", "筆數", "命中", "hits"),
    "titles": ("前三筆標題", "標題", "titles"),
    "index": ("#", "序", "no", "編號"),
}


# --------------------------------------------------------------------------
# 佔位符與斷言用語
# --------------------------------------------------------------------------

PLACEHOLDERS = {
    "", "-", "--", "—", "–", "_", ".", "。", "略", "(略)", "（略）", "同上", "同前",
    "見上", "如上", "同左", "tbd", "todo", "n/a", "na", "none", "null", "無",
    "待補", "待查", "待填", "未填", "省略", "...", "…", "?", "??", "???",
    "xxx", "yyy", "zzz", "同上表", "見前", "略同", "同候選1", "見第五節",
}

# 斷言「不存在」的措辭。報告只能寫「這次搜尋沒有回傳」，不能寫「沒有人做過」。
ASSERTIVE_PATTERNS = [
    (r"沒有人做過", "沒有人做過"),
    (r"沒人做過", "沒人做過"),
    (r"無人做過", "無人做過"),
    (r"沒有人研究過", "沒有人研究過"),
    (r"沒人研究過", "沒人研究過"),
    (r"沒有任何人做過", "沒有任何人做過"),
    (r"完全沒有人碰過", "完全沒有人碰過"),
    (r"從來沒有人", "從來沒有人"),
    (r"從未有人", "從未有人"),
    (r"學界從未", "學界從未"),
    (r"目前不存在", "目前不存在"),
    (r"不存在[^，。；、\s]{0,3}(?:研究|文獻|論文|先例|工作)", "不存在…研究／文獻"),
    # 同一句話的中文語序常常是反過來的（「相關文獻並不存在」而不是「不存在相關文獻」）。
    # 少了這一條，只要把主詞挪到前面，同一個斷言就整條穿過去。
    # 間隔字元排除「存」，否則「不查文獻存不存在」這種**在否定該說法**的寫法會被誤判。
    (r"(?:研究|文獻|論文|先例|工作)[^，。；、\s存]{0,4}不存在", "…研究／文獻不存在"),
    # 「尚未／迄今未有人做過」與「尚無相關文獻」是同一個斷言的另外兩種寫法。
    (r"(?:尚未|迄今未|至今未|還未)有?人(?:做過|研究過|探討過|碰過|處理過)", "尚未有人做過"),
    (r"(?:尚無|迄今無|至今無)[^，。；、\s]{0,4}(?:研究|文獻|論文|先例)", "尚無…研究／文獻"),
    (r"確定(?:是|為)全新", "確定是全新"),
    (r"可以確定是新的", "可以確定是新的"),
    (r"保證(?:是|為)?新的", "保證是新的"),
    (r"絕對新穎", "絕對新穎"),
    (r"(?:世界|國內|全球)首創", "首創"),
    (r"前無古人", "前無古人"),
    (r"肯定沒有人", "肯定沒有人"),
    (r"一定沒有人", "一定沒有人"),
    (r"獨一無二的題目", "獨一無二的題目"),
]

# 同一行出現這些字樣時，上面的比對視為「在講規則／在否定該說法」，不算違規。
ASSERTIVE_GUARD = re.compile(
    r"(≠|!=|不等於|不代表|不能寫|不能說|不可寫|不可說|不得寫|不得說|並非|禁止|誤寫|錯誤示範|反例)"
)

IDENTIFIER_RE = re.compile(
    r"(10\.\d{4,9}/\S+|arxiv\s*[:：]\s*\d{4}\.\d{4,5}|arxiv\.org/abs/\S+"
    r"|corpus\s*id\s*[:：]?\s*\d+|s2cid\s*[:：]?\s*\d+|ncl\.edu\.tw|airiti)",
    re.IGNORECASE,
)

YEAR_RE = re.compile(r"[（(]\s*(?:19|20)\d{2}[a-z]?\s*[)）]")

QUOTE_RE = re.compile(r"「([^」]{8,})」|『([^』]{8,})』|“([^”]{8,})”|\"([^\"]{8,})\"")

# 標籤括號的四對。evals/README.md 對外承諾 〔〕／【】／［］／（） 都收，而全形
# ［］（U+FF3B/U+FF3D）跟半形 [] 是不同的字元——少收那一對，一份**照著本 repo
# 自己的文件**寫的報告會被判違規。那是假紅燈，而假紅燈跟假綠燈一樣是查核器的錯：
# 它把作者送去改一個沒有壞的東西。寫成常數是為了「一改改全部」——以前每個樣式
# 各自抄一份字元類，補好其中一份不會讓其他份跟著補好，doc_scan 也看不到字元類裡少了什麼。
BRA_OPEN = r"〔【\[［（"
BRA_CLOSE = r"〕】\]］）"

# 反引號／引號包住的字串，或連續兩個以上的拉丁詞——都算「具體查詢詞」
BACKTICK_RE = re.compile(r"`([^`]{3,})`")
QUOTED_ANY_RE = re.compile(r"「([^」]{3,})」|『([^』]{3,})』|“([^”]{3,})”|\"([^\"]{3,})\"")
LATIN_PHRASE_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9\-\+\*/\.]{1,}(?:\s+[A-Za-z0-9][A-Za-z0-9\-\+\*/\.]{1,}){1,}"
)

COUNT_RE = re.compile(
    r"(?:生成|產生|共生成|共產生)\s*(\d+)\s*個?\s*(?:→|->|➜|=>|—>|~>|至|到)\s*"
    r"(?:存活|倖存|留下)\s*(\d+)\s*個?"
)

# 表頭的候選結算行：生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q（半形 = + 也接受）
SETTLE_RE = re.compile(
    r"生成\s*(\d+)\s*個?\s*[＝=]\s*存活\s*(\d+)\s*個?\s*[＋+]\s*"
    r"待確認\s*(\d+)\s*個?\s*[＋+]\s*已淘汰\s*(\d+)\s*個?"
)
SETTLE_LABEL_RE = re.compile(r"候選結算")

NO_SEARCH_RE = re.compile(r"本次未執行任何檢索|無法執行淘汰步驟|本次無檢索工具")

# 〔UNSEARCHABLE〕的豁免只給「卡住的是術語」的那一種，不給「還沒空去搜」的那一種。
# SKILL.md〈互鎖的例外〉要求〈還缺哪一項證據〉欄自己講清楚是哪一種，這條就是在讀那一欄。
TERMINOLOGY_RE = re.compile(
    r"術語|詞彙|用語|正規詞|措辭|命名|叫法|講法|terminology|vocabulary|wording|nomenclature",
    re.IGNORECASE,
)

# 候選編號 C01…：生成當下指派，全程沿用，二／三／四節靠它對帳
CID_RE = re.compile(r"(?<![A-Za-z0-9])(C\d{1,3})(?![0-9])")

# 敘事型文件裡的報告區塊標記
BLOCK_START_RE = re.compile(r"<!--\s*format-check\s*:\s*report-(?:start|begin)\s*-->", re.I)
BLOCK_END_RE = re.compile(r"<!--\s*format-check\s*:\s*report-end\s*-->", re.I)

# --------------------------------------------------------------------------
# 行首標記：容忍 blockquote、清單符號（含有序清單）、粗體
#
# SKILL.md 是散文，而它展示格式的方式**本身就有好幾種**：第 1 步用 `> ` 引用區塊
# 展示預設行的格式，第 5 步的輸出樣板用 `- ` 清單。讀者（那個要照抄的模型）看到的是
# 形狀，不是規格作者心裡的那一種形狀。**規格顯示得出來的形狀，解析器就要吃得下**——
# 否則一份照著規格寫的報告會被查核器判成「這一條不存在」，而那是最壞的一種錯誤訊息：
# 它把讀者送去找一個不存在的缺漏。
#
# 這一段的三個常數是所有「行級」解析共用的，改一個地方就好；以前欄位行、預設行、
# 標題行各自寫死一份前綴，於是修好其中一種形狀不會讓另外兩種跟著修好。
_LEAD = r"\s*(?:>\s*)*"          # 行首空白 ＋ 任意層 blockquote
_BULLET = r"(?:(?:[-*+]|\d{1,2}[.)])\s*)?"   # 清單符號（可省略）

# markdown 標題。允許 blockquote 包住——一份被引用起來的報告仍然是報告。
HEAD_RE = re.compile(_LEAD + r"(#{1,6})\s+(.*)$")

# 井號後面沒有空白的「標題」（`###F1 遙測綠覆指數`）。markdown 規格不把它當標題，
# HEAD_RE 也不認——於是它對整支解析器**完全隱形**：那個家族既不會被建出來，
# 也不會有任何一句話說「這一行讀不到」，而第六節的牆還指得到它的預設編號。
# 掃標題一律用這個較寬的樣式，「到底算不算合法標題」另外記在 spaced 上。
HEADISH_RE = re.compile(_LEAD + r"(#{1,6})[ \t]*(\S.*)$")

# `- **標籤**：值` 這種欄位行。標籤裡允許 `*` 與括號註記（`- **搜尋證據**（三輪）：…`），
# 因為 norm_key 本來就會把它們清掉；以前標籤不許含 `*`，那種行整條讀不到，
# 查核器接著說「候選缺少〈搜尋證據〉欄」——欄位就在那裡，訊息卻叫人去補一個已經有的東西。
FIELD_LINE_RE = re.compile(
    _LEAD + r"(?:[-*+]|\d{1,2}[.)])\s*\*{0,2}([^：:]+?)\*{0,2}\s*[：:]\s*(.*)$"
)

# 第一節的預設行。編號與冒號之間允許**一串**括號標籤：SKILL.md 第 1 步（甲）承接
# 地形報告時，來源就寫在那裡（`預設 A1〔承接自地形 W3，支撐家族 F1、F4〕：…`），
# 而承接是兩個模式唯一的介面。補了取樣框之後很自然會寫成兩個相鄰的括號
# （`預設 A2〔承接自地形 W2〕〔已補取樣框〕：…`），所以括號是「一串」不是「一個」。
# 分隔符除了冒號也收全形直線：SKILL.md 第 1 步示範補框後的寫法時，寫的正是
# `預設 A1〔承接自地形 W3，已補取樣框〕｜標題層掃描 …`（沒有冒號）。
# 這個括號一旦不被解析，承接來的預設對查核器就是不存在——既不會被算進去，
# 也不會被檢查，而 G3 指到它時的錯誤訊息會說「第一節沒有這一條」。
ASSUM_LINE_RE = re.compile(
    _LEAD + _BULLET + r"\*{0,2}預設\s*([A-Za-z]?\d{0,3})\s*\*{0,2}"
    r"((?:\s*\*{0,2}\s*[" + BRA_OPEN + r"][^" + BRA_CLOSE + r"]*[" + BRA_CLOSE + r"])*)"
    r"\s*\*{0,2}\s*[：:｜|]\s*(.*)$"
)

# 「看起來是一條預設、卻不是可解析的形式」的偵測器（比 ASSUM_LINE_RE 寬）。
# 寬到連表格列（`| 預設 A1 | …`）都認得出來，因為靜默丟掉一行畸形的預設，
# 比誤報一次昂貴得多：前者讓報告帶著沒被讀過的一行拿到綠燈。
#
# **這裡刻意不加任何「後面必須跟著什麼」的 lookahead，而那是一個已經犯過一次的錯。**
# 上一輪為了讓 `- 預設 A1 與 A2 都與量測方式有關`（在**講**那兩條預設的散文）
# 不要被報成「這一行讀不到」，在編號後面加了一個結構字元的 lookahead
# （：: ｜ | 〈 或標籤括號）。代價是：分隔符只要落在那個字元類之外——例如
# `- 預設 A2——〈…〉`——這一行就同時對 ASSUM_LINE_RE 與本樣式隱形，
# 於是預設 3→0、unreadable 0、離開碼 0、零筆 finding。修掉一次假紅燈，
# 換回了上一輪整條規則存在的理由：那個假綠燈。
#
# 所以取捨明講，寫在這裡是為了讓下一個人不要「順手修好」它：
# **假紅燈與假綠燈不等價。** 假紅燈讓讀者花五分鐘看懂那一行沒壞；
# 假綠燈是查核器對一份它沒讀過的文件說「通過」。兩者衝突時取假紅燈。
# 因此，凡是以 `預設` ＋ 編號開頭的行，只要 ASSUM_LINE_RE 讀不出來，
# 一律回報——包括真的只是在講那兩條預設的散文（見樣本
# fixtures/assumption_prose_mention.md，它現在是紅的，而那是正確的行為）。
# 要避開它，把那句話寫成不以 `預設 A1` 開頭的句子即可。
ASSUM_LOOKALIKE_RE = re.compile(
    r"^\s*(?:[>|｜]\s*)*" + _BULLET + r"\*{0,2}\s*預設\s*[A-Za-z]?\d{1,3}"
)

# 候選區塊標題。比對前先過 strip_md，所以 `### **候選 1（C01）**：…` 也讀得到。
CAND_HEAD_RE = re.compile(
    r"^(?:候選|候補|Candidate)\s*([0-9]+)\s*(?:[（(]\s*([Cc]\d{1,3})\s*[)）])?\s*[：:.\-]?\s*(.*)$",
    re.I,
)
CAND_LOOKALIKE_RE = re.compile(r"^(?:候選|候補|Candidate)", re.I)

# 「看起來是表格列」：行首（容許 blockquote）就是直線，全形半形都算。
ROWISH_RE = re.compile(r"^\s*(?:>\s*)*[|｜]")
# 未跳脫的半形直線。用來數「這一行像不像一列表格」——見 parse_table 的漏行首直線偵測。
PIPE_RE = re.compile(r"(?<!\\)\|")
IMPRESSION_RE = re.compile(
    r"[" + BRA_OPEN + r"]\s*印象\s*[，,]\s*未驗證\s*[" + BRA_CLOSE + r"]")
# 承接自地形報告的兩種標籤。未補取樣框者效力等同〔印象，未驗證〕（不得當 G3 輸入），
# 補了取樣框者與本輪量化的預設同等看待。兩者都**保留原標籤**：效力相同、來源不同，
# 讀者要看得出這一條是別份報告帶進來的，所以查核器不得叫報告改寫成〔印象，未驗證〕。
INHERIT_RE = re.compile(r"承接\s*自\s*地形")
FRAMED_RE = re.compile(r"已\s*補\s*取樣框")
AREF_RE = re.compile(r"(?<![A-Za-z0-9])[Aa](\d{1,2})(?![0-9])")

# 量化預設的五個取樣框欄位（缺一不可）
ASSUM_SEGMENTS = [
    ("標題層掃描 N 篇", re.compile(r"標題層掃描\s*(\d+)\s*篇"), "N"),
    ("檢索詞", re.compile(r"檢索詞"), None),
    ("limit", re.compile(r"limit\s*(\d+)", re.I), None),
    ("摘要層精讀 M′ 篇", re.compile(r"摘要層精讀\s*(\d+)\s*篇"), "Mp"),
    ("pick 索引", re.compile(r"pick\s*索引", re.I), None),
    ("其中 M 篇沿用", re.compile(r"其中\s*(\d+)\s*篇沿用"), "M"),
    ("推翻性檢索", re.compile(r"推翻性檢索"), None),
    ("回傳 K′ 篇", re.compile(r"回傳\s*(\d+)\s*篇"), "Kp"),
    ("讀後 K 篇", re.compile(r"讀後\s*(\d+)\s*篇"), "K"),
    ("樣本來源", re.compile(r"樣本來源"), None),
]


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------

def strip_md(s):
    """去掉 markdown 強調、反引號、全形空白，供比對用。"""
    s = s.replace("\u3000", " ")
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"\*{1,3}|_{2,}|`", "", s)
    return s.strip()


def norm_key(s):
    """欄位／標籤正規化：去強調、去空白、小寫、去尾標點。"""
    s = strip_md(s).lower()
    s = re.sub(r"[\s（）()\[\]〔〕【】:：]+", "", s)
    return s


def is_placeholder(s):
    v = strip_md(s)
    v = v.strip(" 　.、,，;；:：")
    if not v:
        return True
    return v.lower() in PLACEHOLDERS


def has_identifier(s):
    return bool(IDENTIFIER_RE.search(strip_md(s)))


def has_verbatim_quote(s):
    return bool(QUOTE_RE.search(s))


def extract_queries(s):
    """從證據欄抓出看起來像「真的跑過的查詢詞」的片段。"""
    out = []
    for m in BACKTICK_RE.finditer(s):
        out.append(m.group(1).strip())
    for m in QUOTED_ANY_RE.finditer(s):
        out.append(next(g for g in m.groups() if g).strip())
    for m in LATIN_PHRASE_RE.finditer(strip_md(s)):
        out.append(m.group(0).strip())
    # 過濾掉佔位符與純數字
    return [q for q in out if not is_placeholder(q) and not re.fullmatch(r"[\d\s.,]+", q)]


def count_papers(cell):
    """粗估一個「關鍵文獻」欄位裡列了幾篇。"""
    text = strip_md(cell)
    years = len(YEAR_RE.findall(text))
    parts = [p for p in re.split(r"[；;、,，]|\s{2,}", text) if p.strip()]
    return max(years, len(parts) if len(parts) > 1 else 0, 1 if text else 0)


def first_cid(s):
    m = CID_RE.search(strip_md(s or ""))
    return m.group(1).upper() if m else None


def strip_quote(s):
    """去掉行首的 blockquote 標記，供「這一行是不是某某結構」的判別用。"""
    return re.sub(r"^\s*(?:>\s*)+", "", s or "")


def cand_ref(c):
    """候選在訊息裡的稱呼。標題解析不出序號時不能用 %d，否則查核器自己會炸。"""
    if c.get("cid"):
        return c["cid"]
    if c.get("ordinal") is not None:
        return "候選 %d" % c["ordinal"]
    return "（標題解析不出編號的候選）"


def cand_head_text(c):
    if c.get("ordinal") is not None:
        return "### 候選 %d：%s" % (c["ordinal"], c.get("title") or "")
    return "### %s" % (c.get("title") or "")


def fam_ref(fam):
    return fam.get("fid") or "（標題解析不出編號）"


def apply_report_blocks(text):
    """敘事型文件：只保留 <!-- format-check: report-start/end --> 之間的內容。

    做法是把區塊外的行**清空**而不是切掉，行號因此仍然對得上原始檔案，
    使用者拿到的每一筆 finding 都能直接跳轉。沒有標記時原樣回傳。
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if BLOCK_START_RE.search(ln)]
    if not starts:
        return text, 0
    ends = [i for i, ln in enumerate(lines) if BLOCK_END_RE.search(ln)]
    keep = [False] * len(lines)
    for s in starts:
        e = next((x for x in ends if x > s), len(lines))
        for i in range(s + 1, min(e, len(lines))):
            keep[i] = True
    out = [ln if keep[i] else "" for i, ln in enumerate(lines)]
    return "\n".join(out), len(starts)


# --------------------------------------------------------------------------
# 解析
# --------------------------------------------------------------------------

class Report(object):
    def __init__(self):
        self.mode = "gap"               # "gap"（研究缺口報告）或 "landscape"（領域地形報告）
        self.families = []              # landscape：dict(fid, name, line, fields{key:(lineno,value)})
        self.glance_rows = []           # landscape：第一節一眼表
        self.wall_rows = []             # landscape：第六節牆表
        self.lines = []
        self.header_lines = []          # (lineno, text) 到第一個 ## 為止
        self.sections = []              # dict(kind, title, start, end)
        self.candidates = []            # dict(ordinal, cid, title, line, fields{key:(lineno,value)})
        self.assumptions = []           # dict(aid, line, text, impression, numbers)
        self.pending_rows = []          # dict(cells{col:value}, line)
        self.kill_rows = []             # dict(cells{col:value}, line)
        self.trace_rows = []            # dict(cells{col:value}, line)
        self.declared_generated = None
        self.declared_survived = None
        self.count_line = None
        self.settlement = None          # (N, M, P, Q)
        self.settlement_line = None
        self.no_search_declared = False
        self.report_blocks = 0
        # 讀不進來的東西。解析器可以寬容，但不可以安靜：凡是「看起來是報告的一部分、
        # 卻沒被讀進任何結構」的行，都堆在這裡，由 PARSE-01／ASSUM-01 回報。
        self.table_strays = []          # dict(line, text, why)：表格列讀不到／欄數不符
        self.head_strays = []           # dict(line, text, why)：候選或家族標題讀不到
        self.assumption_strays = []     # dict(line, text)：看起來是預設、卻解析不出來
        # 標題被改寫過、只能靠內容認出來的區段。這一份**不是**「讀不到」——內容
        # 讀得到、規則照跑——而是「這一節的名字不對」，所以它有自己的 id（SECT-01）。
        self.section_renames = []       # dict(line, text, title, kind, title_kind)
        self.table_missing = []         # dict(line, text, kind)：這一節該有表，卻讀不到任何一張


def classify_section(title):
    t = norm_key(title)
    if "待確認" in t or "待定" in t:
        return "pending"
    if "淘汰" in t:
        return "killed"
    if "檢索紀錄" in t or "檢索記錄" in t or "搜尋紀錄" in t:
        return "trace"
    if "存活候選" in t or ("候選" in t and "檢索" not in t):
        return "survivors"
    if "共識" in t or "預設" in t:
        return "consensus"
    if "下一步" in t:
        return "next"
    if "可查證" in t:
        return "verifiable"
    return "other"


def classify_landscape_section(title):
    """地形報告的六個區段。與 classify_section 分開，因為兩份文件的節名沒有交集。"""
    t = norm_key(title)
    if "牆" in t or "默默預設" in t:
        return "walls"
    if "一眼" in t:
        return "glance"
    if "家族" in t:
        return "families"
    if "檢索紀錄" in t or "檢索記錄" in t or "搜尋紀錄" in t:
        return "trace"
    if "疊" in t:
        return "stack"
    if "能量" in t:
        return "energy"
    return "other"


# --------------------------------------------------------------------------
# 靠形狀定位（而不是靠節名）
#
# 上一輪已經把這條原則寫進 parse_landscape 的 docstring：「家族靠 `### F<n>` 認，
# 不靠它落在哪一節」。但它只被套用在家族與候選區塊上；一眼表與預設行仍然靠節名
# 找得到，於是把 `## 一、一眼表` 改名成 `## 一、總覽表`、把 `## 一、領域共識…`
# 改名成 `## 一、這個領域大家都同意什麼`，底下每一列、每一條預設就整批消失而報告是綠的。
# 下面這幾個函式是那條原則的**唯一**實作：表看表頭、區塊看欄位行、預設看行形狀。
# --------------------------------------------------------------------------

def _alias_hits(header, aliases):
    """這個表頭對得上哪些欄位別名。這是「這是哪一張表」的唯一判準。"""
    got = set()
    for name in header or []:
        key = norm_key(name)
        if not key:
            continue
        for canon, names in aliases.items():
            for a in names:
                na = norm_key(a)
                if na and na in key:
                    got.add(canon)
                    break
    return got


def first_table_header(lines, start, end):
    """區段裡第一張表的表頭儲存格。表頭的判定規則與 parse_table 逐字一致——
    兩邊若各寫一套，遲早會對同一張表得出不同的答案。"""
    for i in range(start, end):
        raw = lines[i].strip()
        if not raw.startswith("|"):
            continue
        if re.fullmatch(r"[\s:\-—–|]+", raw):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", raw.strip("|"))]
        if all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip()):
            continue
        return cells
    return None


def table_kind(header, mode):
    """表頭欄位決定這是哪一張表。**不看它落在哪一節、那一節叫什麼名字。**"""
    if not header:
        return None
    if mode == "landscape":
        cols = _alias_hits(header, LAND_WALL_COLUMNS)
        if "wall" in cols and "sources" in cols:
            return "walls"
        cols = _alias_hits(header, LAND_GLANCE_COLUMNS)
        # 牆表要先判掉：它的〈家族數〉欄含「家族」二字，會對上一眼表的〈家族〉。
        # 一眼表以〈狀態〉為必要欄，牆表沒有這一欄，兩張表因此分得開。
        if "family" in cols and "status" in cols and (cols & set(("buys", "costs"))):
            return "glance"
        return None
    cols = _alias_hits(header, COLUMN_ALIASES)
    if "query" in cols and "hits" in cols:
        return "trace"
    if "verdict" in cols and (cols & set(("literature", "reason"))):
        return "killed"
    if "state" in cols and (cols & set(("missing", "action"))):
        return "pending"
    return None


# 一個 ###／#### 區塊「是什麼」，由它自己帶的欄位行決定；標題只負責取名字。
# 這兩組欄位是 S1／S2 的修法：`### 遙測綠覆指數`（沒有 F 編號）、`### C01：<題目>`
# （沒有「候選」二字）以前整塊消失，只留下 LWALL-01 指著第六節、或 COUNT-01 指著
# 一個數字——而壞掉的是第二節的一行標題。要求兩個欄位（不是一個）才算，
# 是為了不把一段剛好提到〈狀態〉的散文認成家族。
CAND_BLOCK_KEYS = ("gap_type", "verdict", "evidence", "neighbour")
FAM_BLOCK_KEYS = ("assumptions", "status", "buys", "costs")


def block_field_hits(lines, start, end):
    """這個標題底下帶了幾個家族欄位、幾個候選欄位。兩組欄位沒有交集
    （家族有〈狀態〉〈買到什麼〉，候選有〈缺口類型〉〈新穎性判定〉），
    所以同一個區塊不會兩邊都中。"""
    fam = parse_fields(lines, start, end, LAND_LABEL_ALIASES)
    cand = parse_fields(lines, start, end, LABEL_ALIASES)
    return (len([k for k in FAM_BLOCK_KEYS if k in fam]),
            len([k for k in CAND_BLOCK_KEYS if k in cand]))


def block_kind(famhits, candhits):
    """這個標題底下裝的是家族、候選、還是都不是。門檻只寫在這裡一處：
    要兩個以上的欄位才算，免得把一段剛好提到〈狀態〉的散文認成一個家族。"""
    if famhits >= 2:
        return "family"
    if candhits >= 2:
        return "candidate"
    return None


def scan_heads(lines):
    """掃出所有標題，含「井號後面沒空白」那一種，並算好每個標題的區塊範圍。

    回傳 dict(line0, level, title, spaced, end)。end 一律到下一個標題為止——
    欄位行不會跨過一個標題歸給前一個區塊，那會讓兩個家族的欄位混在一起。
    """
    heads = []
    for i, ln in enumerate(lines):
        m = HEADISH_RE.match(ln)
        if not m:
            continue
        heads.append({"line0": i, "level": len(m.group(1)),
                      "title": m.group(2).strip(),
                      "spaced": bool(HEAD_RE.match(ln)), "end": len(lines)})
    for n, h in enumerate(heads):
        h["end"] = heads[n + 1]["line0"] if n + 1 < len(heads) else len(lines)
    return heads


# 每一種區段「長什麼樣子」與「標題該含哪個字」——只用在 SECT-01 的訊息裡，
# 讓那句話能同時說出「我怎麼認出它的」與「標題該改回什麼」。
SECTION_SHAPE_HINT = {
    "glance": "一眼表（表頭有〈家族〉〈狀態〉欄）",
    "walls": "牆表（表頭有〈牆〉〈來源預設〉欄）",
    "families": "各家族（底下的區塊帶〈默默預設〉〈狀態〉〈買到什麼〉等欄位行）",
    "survivors": "存活候選（底下的區塊帶〈缺口類型〉〈新穎性判定〉〈搜尋證據〉等欄位行）",
    "consensus": "領域共識與未被質疑的預設（裡面有第一節的預設行）",
    "pending": "待確認表（表頭有〈暫定狀態〉〈還缺…〉欄）",
    "killed": "已淘汰表（表頭有〈判定〉〈關鍵文獻〉欄）",
    "trace": "檢索紀錄表（表頭有〈查詢詞〉〈回傳筆數〉欄）",
}
SECTION_TITLE_KEYWORD = {
    "glance": "一眼", "walls": "牆／默默預設", "families": "家族",
    "survivors": "存活候選", "consensus": "共識／預設",
    "pending": "待確認", "killed": "淘汰", "trace": "檢索紀錄",
}
# 內部的 kind 名稱不進訊息：讀者沒有義務知道 "other" 是什麼。
SECTION_KIND_LABEL = dict(SECTION_SHAPE_HINT)
SECTION_KIND_LABEL.update({
    "next": "下一步", "verifiable": "可查證清單", "stack": "實際上怎麼疊",
    "energy": "能量在哪裡", "other": "認不出來的一節",
})
# 訊息裡「缺的是什麼」用短名，不用上面那個帶括號說明的長名——巢狀括號沒人讀得下去。
SECTION_SHORT_NAME = {
    "glance": "一眼表", "walls": "牆表", "families": "各家族", "survivors": "存活候選",
    "consensus": "領域共識與未被質疑的預設", "pending": "待確認表",
    "killed": "已淘汰表", "trace": "檢索紀錄表",
}


def section_shape_kind(rep, heads, s, mode):
    """一個 `## ` 區段是哪一節，由它**裝了什麼**決定。認不出來回 None。"""
    kind = table_kind(first_table_header(rep.lines, s["start"], s["end"]), mode)
    if kind:
        return kind
    kinds = set(h.get("block") for h in heads
                if s["start"] < h["line0"] < s["end"])
    if mode == "landscape":
        return "families" if "family" in kinds else None
    if "candidate" in kinds:
        return "survivors"
    for j in range(s["start"], s["end"]):
        if ASSUM_LINE_RE.match(rep.lines[j]) or ASSUM_LOOKALIKE_RE.match(rep.lines[j]):
            return "consensus"
    return None


# 「這一節依規格該有一張表」——只用來在**找不到任何表**時多報一筆，
# 不用來決定要不要解析（那正是這一輪在拆掉的東西）。地形報告的〈五、檢索紀錄〉
# 不在裡面：那張表本檔根本不解析，沒有任何規則掛在它上面。
TABLE_SECTIONS = {
    "gap": ("killed", "pending", "trace"),
    "landscape": ("glance", "walls"),
}


def resolve_sections(rep, heads, mode):
    """節名只是名字：內容認得出來就以內容為準，名字對不上就自己記一筆。

    認不出形狀時才退回節名——一節可以是空的（那由 STRUCT-01 管），
    也可以是本檔不解析的〈五、下一步〉〈七、可查證清單〉那種。
    """
    for s in rep.sections:
        head = first_table_header(rep.lines, s["start"], s["end"])
        shape = section_shape_kind(rep, heads, s, mode)
        title_kind = s["kind"]
        if shape and shape != title_kind:
            rep.section_renames.append({
                "line": s["line"], "text": rep.lines[s["start"]],
                "title": s["title"], "kind": shape, "title_kind": title_kind,
            })
            s["kind"] = shape
        if head is None and title_kind in TABLE_SECTIONS.get(mode, ()):
            # 一張表若被從渲染畫面複製回來，它連**表頭**都沒有直線了；沒有表頭，
            # parse_table 的漏行首直線偵測就沒有欄數可比，靠形狀再也認不出這裡
            # 曾經有一張表。這是節名唯一被允許的用法：它只能**多**出一筆 finding，
            # 永遠不能決定要不要解析。整張表根本沒寫，也走這一筆——兩種情況
            # 對讀者的下一步不同，但都不是「這一節沒問題」。
            # 條件是「連一張表都沒有」，不是「表頭欄位認不出來」：欄位標籤被改寫時
            # 表**在**那裡，列照樣解析（欄對不上會由 LSTAT-01／VERDICT-01 大聲說出來），
            # 這時再說「讀不到任何一張表」就是假話。
            rep.table_missing.append({
                "line": s["line"], "text": rep.lines[s["start"]], "kind": title_kind,
                "whole_doc": False,
            })

    # 兩件事同時壞掉的那一格：一眼表被貼成沒有直線的純文字（形狀認不出來），
    # 而它的節標題也被改寫（節名也認不出來）。兩個定位管道同時失效，上面那一筆就不會出現，
    # 而一眼表是這份報告裡唯一沒有交叉對帳的結構——沒有任何規則會數它的列數，
    # 於是整張表消失而報告全綠。這一條補的是文件層的存在性：**整份地形報告裡
    # 有沒有一張一眼表**，不問它落在哪一節、那一節叫什麼名字。
    # 牆表不必再補一條：它的存在性已經由 LWALL-01 顧著（第二節寫下來的預設
    # 必須落進某一道牆，牆表不見時它會說出來）。
    if mode == "landscape" and not any(s["kind"] == "glance" for s in rep.sections) \
            and not any(t["kind"] == "glance" for t in rep.table_missing):
        anchor = rep.sections[0]["line"] if rep.sections else 1
        rep.table_missing.append({"line": anchor, "text": "", "kind": "glance",
                                  "whole_doc": True})


def detect_mode(lines, first_h2):
    """判別這是哪一種報告。第一行的 H1 是主判別點，表頭〈模式〉是第二個。

    兩者都認不出來時回 "gap"：缺口報告是這支查核器原本唯一的對象，
    保守回退才不會讓既有報告因為新增了一個模式而突然不受查核。
    """
    head = lines[:first_h2] if first_h2 > 0 else lines
    for ln in head:
        # 去掉 blockquote：一份被引用起來的報告仍然是那一種報告，而型別認錯
        # 會讓整份文件套到另一套規則上，那是所有誤導性訊息裡最貴的一種。
        s = strip_md(strip_quote(ln))
        if LANDSCAPE_H1_RE.match(s):
            return "landscape"
        if GAP_H1_RE.match(s):
            return "gap"
        if LANDSCAPE_MODE_RE.match(s):
            return "landscape"
    return "gap"


def parse_table(lines, start, end, aliases=None, strays=None, where=""):
    """把某區段裡的第一張 markdown 表格解析成 (columns, rows)。

    讀不到的列會寫進 `strays`，不會安靜消失。三種讀不到的方式都真的發生過：
      - 被 blockquote 包住（`> | C07 … |`）；
      - 用全形直線（`｜C07｜…｜`）；
      - 表格中間插了一行非表格內容，之後的列整批不再被讀。
    第三種最惡毒：**列數會少一半而報告仍然綠**，或者只在 RECON-01 那裡顯示成
    「結算寫已淘汰 6，第四節實際有 5 列」——那句話會把作者送去改數字，而數字是對的，
    壞掉的是那一列的形狀。欄數與表頭不符也一併記下：欄一旦錯位，後面每個檢查
    讀到的都是別欄的值，而空掉的那一欄會讓整列**完全不受檢查**。
    """
    if aliases is None:
        aliases = COLUMN_ALIASES
    rows = []
    header = None
    consumed = set()
    for i in range(start, end):
        raw = lines[i].strip()
        if not raw.startswith("|"):
            if header is not None and rows:
                break
            continue
        consumed.add(i)
        # 跳過跳脫過的直線：`\|` 在 markdown 表格裡是儲存格內容，不是欄位分隔。
        # 拿它當分隔的話，一句含 OR 的查詢詞會讓那一列多出一欄，而欄數檢查會
        # 對一列**寫對了的**紀錄開槍——查核器最不該做的事就是罰正確的寫法。
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", raw.strip("|"))]
        if re.fullmatch(r"[\s:\-—–|]+", raw):
            continue
        if all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip()):
            continue
        if header is None:
            header = cells
            continue
        rows.append((i + 1, cells))

    if strays is not None:
        for i in range(start, end):
            if i in consumed or not ROWISH_RE.match(lines[i]):
                continue
            raw = lines[i]
            if raw.strip().startswith(">"):
                why = "被 blockquote（`>`）包住，markdown 不把它當表格列"
            elif strip_quote(raw).lstrip().startswith("｜"):
                why = "用的是全形直線「｜」，markdown 表格只認半形 `|`"
            else:
                why = "不在被解析的那張表裡（表格中間一旦插進非表格的一行，後面的列就整批不再被讀）"
            strays.append({"line": i + 1, "text": raw, "why": why, "where": where})

        # 掉了**行首**那一根直線的資料列。這一種是所有讀不到的方式裡最惡毒的：
        # parse_table 只吃 startswith("|") 的行，而上面那一輪的 ROWISH_RE 也錨在行首，
        # 於是它既不被讀進表、也不被回報。如果它剛好是第一列，表格連斷都不會斷——
        # 整列連同掛在它身上的每一條規則一起無聲消失（一眼表少一列＝LSTAT-01／LCOST-01
        # 對那一列沒有對象；檢索紀錄少一列＝TRACE-02 沒有對象）。若不是第一列，
        # 它會偽裝成 RECON-01 的算術對不起來，而最便宜的變綠方式是把結算數字改小——
        # 那等於把一列真的寫出來的紀錄從對帳裡刪掉。
        # 門檻取 max(2, 欄數-1)：一列少了行首直線之後還剩「欄數」根，少了頭尾兩根
        # 則剩「欄數-1」根，兩種都收得到；散文句子要湊到兩根未跳脫的半形 `|` 極罕見。
        # 只數半形 `|`：全形「｜」是第一節預設行與地形〈狀態〉欄的合法內容分隔符
        # （`飽和｜\`query\` 回傳 318 筆`），數它會對寫對了的行開槍。
        if header is not None:
            need = max(2, len(header) - 1)
            for i in range(start, end):
                if i in consumed or not lines[i].strip():
                    continue
                if ROWISH_RE.match(lines[i]):
                    continue                       # 上面那一輪已經處理過
                if len(PIPE_RE.findall(lines[i])) < need:
                    continue
                strays.append({
                    "line": i + 1, "text": lines[i], "where": where,
                    "why": "少了**行首**的直線 `|`（這一行有 %d 個 `|`，表頭有 %d 欄）——"
                           "markdown 只把 `|` 開頭的行當表格列，所以這一列沒有進表"
                           % (len(PIPE_RE.findall(lines[i])), len(header)),
                })
        strays.sort(key=lambda s: s["line"])

    if header is None:
        return [], []
    colmap = {}
    for idx, name in enumerate(header):
        key = norm_key(name)
        for canon, names in aliases.items():
            if canon in colmap:
                continue
            for a in names:
                if norm_key(a) and norm_key(a) in key:
                    colmap[canon] = idx
                    break
    out = []
    for lineno, cells in rows:
        rec = {"_line": lineno, "_cells": cells, "_ncells": len(cells), "_ncols": len(header)}
        if strays is not None and len(cells) != len(header):
            strays.append({
                "line": lineno, "text": lines[lineno - 1], "where": where,
                "why": "這一列有 %d 欄，表頭有 %d 欄" % (len(cells), len(header)),
            })
        for canon, idx in colmap.items():
            rec[canon] = cells[idx] if idx < len(cells) else ""
        out.append(rec)
    return header, out


def parse_assumption(lineno, raw):
    """把第一節的一條「預設」行拆成編號、來源標籤、是否印象級、五個取樣框數字。

    讀不到就回 None，由呼叫端決定怎麼處理——**不是**丟掉。丟掉一行畸形的預設，
    報告會少一條預設而查核器一聲不吭，那是最壞的一種綠燈。
    """
    m = ASSUM_LINE_RE.match(raw)
    if not m:
        return None
    aid = m.group(1).strip().upper()
    if aid and aid[0].isdigit():
        aid = "A" + aid
    # 標籤可能有好幾個相鄰的括號（`〔承接自地形 W2〕〔已補取樣框〕`），整串一起看：
    # 分開看的話，第二個括號裡的〔已補取樣框〕會落在解析範圍外，一條補過框的預設
    # 就會被當成沒補框，訊息叫作者去補一個他已經補過的東西。
    label = m.group(2) or ""
    body = m.group(3)
    inherited = bool(INHERIT_RE.search(label))
    rec = {
        "aid": aid or None,
        "line": lineno,
        "text": raw,
        "label": label.strip(),
        "inherited": inherited,
        "framed": inherited and bool(FRAMED_RE.search(label)),
        # 承接的預設**按標籤分類，不按內文措辭**。SKILL.md 的寫法會在句尾補一句
        # 「效力同〔印象，未驗證〕」；那是說明，不是這一條的來源。照字面歸成印象級，
        # 訊息就會把承接來的預設講成本輪憑印象寫的，來源當場消失。
        "impression": bool(IMPRESSION_RE.search(raw)) and not inherited,
        "missing": [],
        "numbers": {},
    }
    for label, rx, key in ASSUM_SEGMENTS:
        mm = rx.search(body)
        if not mm:
            rec["missing"].append(label)
        elif key:
            rec["numbers"][key] = int(mm.group(1))
    return rec


def parse_fields(lines, start, end, aliases):
    """把 `- **標籤**：值` 這種欄位行收成 {canon: (lineno, value)}。"""
    fields = {}
    for j in range(start, end):
        fm = FIELD_LINE_RE.match(lines[j])
        if not fm:
            continue
        label = norm_key(fm.group(1))
        value = fm.group(2).strip()
        for canon, names in aliases.items():
            if canon in fields:
                continue
            if any(norm_key(a) in label for a in names):
                fields[canon] = (j + 1, value)
                break
    return fields


def _salvage_fid(fields, title):
    """家族編號優先從〈默默預設〉欄的 F<n>-<字母> 撈——LWALL-01 本來就是讀那一欄
    對帳的，從那裡撈到的編號一定跟第六節對得起來；撈不到才退回標題裡的 F<n>。"""
    if "assumptions" in fields:
        m = LAND_ASSUM_ID_RE.search(fields["assumptions"][1])
        if m:
            return "F" + m.group(1)
    m = re.search(r"(?<![A-Za-z0-9])[Ff](\d{1,2})(?![0-9])", title or "")
    return ("F" + m.group(1)) if m else None


def parse_landscape(rep, heads):
    """地形報告：家族區塊、一眼表、牆表——三者一律靠形狀定位。

    家族靠它**自己帶的欄位行**認（〈默默預設〉〈狀態〉〈買到什麼〉…），
    不靠 `### F<n>` 這個標題形狀，也不靠它落在哪一節。上一輪只做到後者：
    `### 遙測綠覆指數`（沒有編號）、`### 一、遙測綠覆指數`、`###F1 …`（井號後
    沒空白，HEAD_RE 根本看不見）三種標題照樣讓整個家族消失，留下的是 LWALL-01
    指著第六節說「指到第二節沒有的預設」——把作者送去看第六節，而壞的是第二節
    的一行標題。所以認不出來的標題**照樣建成家族**（欄位還是要被檢查），
    編號從〈默默預設〉欄撈，另外回報一筆「這個標題讀不到」。

    一眼表與牆表同理：看表頭欄位，不看節名。`## 一、一眼表` 改成 `## 一、總覽表`
    以前會讓整張表消失，而 check_status／check_cost 都是逐列跑 glance_rows 的——
    於是 LSTAT-01 與 LCOST-01 對每一列同時熄燈，報告全綠。
    """
    lines = rep.lines
    fam_heads = []
    for h in heads:
        if h["level"] < 3:
            continue
        title = strip_md(h["title"])
        m = LAND_FAMILY_HEAD_RE.match(title)
        # 三條入口，任何一條成立就建成家族：標題是規範形狀、區塊形狀像家族、
        # 或標題「看起來像」家族而區塊至少帶一個家族欄位。第三條是舊的容忍度
        # （`### 家族一：…`），以前綁在「要落在家族那一節裡」——而那一節本身
        # 現在正是由家族區塊定義的，綁著就成了循環，所以改綁到欄位上。
        shaped = h["block"] == "family"
        looks = bool(LAND_FAMILY_LOOKALIKE_RE.search(title)) and h["famhits"] >= 1
        if not m and not shaped and not looks:
            continue
        canonical = bool(m) and h["spaced"]
        fields = parse_fields(lines, h["line0"] + 1, h["end"], LAND_LABEL_ALIASES)
        if m:
            fid, name = "F" + m.group(1), m.group(2).strip()
        else:
            fid, name = _salvage_fid(fields, title), title
        fam_heads.append((h["line0"], fid, name, fields))
        if canonical:
            continue
        rep.head_strays.append({
            "line": h["line0"] + 1, "text": lines[h["line0"]], "kind": "family",
            "why": "這一行是家族區塊的標題（底下帶〈默默預設〉〈狀態〉這些欄位行），"
                   "卻不是可解析的形式——要寫成 `### F<n> <家族名稱>`，"
                   "井號後面要有空白。家族本身照樣建起來了（編號從〈默默預設〉欄撈），"
                   "所以它的欄位仍然受檢；要修的是這一行",
        })
    for i, fid, name, fields in fam_heads:
        rep.families.append({"fid": fid, "name": name, "line": i + 1, "fields": fields})

    for s in rep.sections:
        if s["kind"] == "glance":
            _h, rows = parse_table(lines, s["start"], s["end"], LAND_GLANCE_COLUMNS,
                                   rep.table_strays, "一眼表")
            rep.glance_rows.extend(rows)
        elif s["kind"] == "walls":
            _h, rows = parse_table(lines, s["start"], s["end"], LAND_WALL_COLUMNS,
                                   rep.table_strays, "牆表")
            rep.wall_rows.extend(rows)
    return rep


def parse_report(text):
    rep = Report()
    text, rep.report_blocks = apply_report_blocks(text)
    rep.lines = text.splitlines()
    lines = rep.lines

    heads = scan_heads(lines)

    first_h2 = next((h["line0"] for h in heads if h["level"] == 2), len(lines))
    rep.header_lines = [(i + 1, lines[i]) for i in range(0, first_h2)]
    rep.mode = detect_mode(lines, first_h2)
    # 節名只用來**取名字**：真正決定一節是什麼的是它裝了什麼（resolve_sections）。
    classify = classify_landscape_section if rep.mode == "landscape" else classify_section

    h2s = [h for h in heads if h["level"] == 2]
    for n, h in enumerate(h2s):
        end = h2s[n + 1]["line0"] if n + 1 < len(h2s) else len(lines)
        rep.sections.append({"kind": classify(h["title"]), "title": h["title"],
                             "start": h["line0"], "end": end, "line": h["line0"] + 1})

    # 每個 ###／#### 區塊「是什麼」先算好；區段的形狀、家族／候選的建立都用它。
    for h in heads:
        h["famhits"], h["candhits"] = (
            block_field_hits(lines, h["line0"] + 1, h["end"]) if h["level"] >= 3 else (0, 0))
        h["block"] = block_kind(h["famhits"], h["candhits"])
    resolve_sections(rep, heads, rep.mode)

    if rep.mode == "landscape":
        parse_landscape(rep, heads)
        return rep

    # 生成 N → 存活 M（第二節標題）
    for i, ln in enumerate(lines):
        m = COUNT_RE.search(ln)
        if m:
            rep.declared_generated = int(m.group(1))
            rep.declared_survived = int(m.group(2))
            rep.count_line = i + 1
            break

    # 表頭的候選結算行
    for i, ln in enumerate(lines):
        if not SETTLE_LABEL_RE.search(ln):
            continue
        m = SETTLE_RE.search(ln)
        rep.settlement_line = i + 1
        if m:
            rep.settlement = tuple(int(g) for g in m.groups())
        break

    for i, ln in enumerate(lines):
        if NO_SEARCH_RE.search(ln):
            rep.no_search_declared = True
            break

    # 候選區塊。**靠區塊自己帶的欄位行認**（〈缺口類型〉〈新穎性判定〉〈搜尋證據〉…），
    # 標題形狀只用來取序號與編號。`### C01：<題目>`、`### C01 題目：…`、
    # `###候選 1（C01）：…`（井號後沒空白，HEAD_RE 看不見）以前整塊消失，
    # 只留下 COUNT-01／RECON-01 的純算術，而最便宜的變綠方式是把宣告數字改小——
    # 那等於把一個真的寫出來的候選從對帳裡抹掉。所以認不出來的標題**照樣建成候選**，
    # 編號盡量撈出來，另外回報一筆「這個標題讀不到」。
    cand_heads = []
    for h in heads:
        if h["level"] < 3:
            continue
        title = strip_md(h["title"])
        m = CAND_HEAD_RE.match(title)
        shaped = h["block"] == "candidate"
        looks = bool(CAND_LOOKALIKE_RE.match(title)) and h["candhits"] >= 1
        if not m and not shaped and not looks:
            continue
        if m:
            cid = m.group(2).upper() if m.group(2) else None
            cand_heads.append((h["line0"], int(m.group(1)), cid, m.group(3).strip(), h["end"]))
        else:
            cand_heads.append((h["line0"], None, first_cid(title), title, h["end"]))
        if m and h["spaced"]:
            continue
        rep.head_strays.append({
            "line": h["line0"] + 1, "text": lines[h["line0"]], "kind": "candidate",
            "why": "這一行是候選區塊的標題（底下帶〈缺口類型〉〈新穎性判定〉這些欄位行），"
                   "卻不是可解析的形式——要寫成 `### 候選 1（C01）：<題目>`，"
                   "序號用阿拉伯數字，井號後面要有空白。候選本身照樣建起來了"
                   "（編號從標題裡的 C<nn> 撈），對帳與各欄位仍然受檢；要修的是這一行",
        })
    for i, ordinal, cid, title, end in cand_heads:
        rep.candidates.append(
            {"ordinal": ordinal, "cid": cid, "title": title, "line": i + 1,
             "fields": parse_fields(lines, i + 1, end, LABEL_ALIASES),
             "start": i, "end": end}
        )

    for s in rep.sections:
        if s["kind"] == "killed":
            _h, rows = parse_table(lines, s["start"], s["end"], None,
                                   rep.table_strays, "四、已淘汰")
            rep.kill_rows.extend(rows)
        elif s["kind"] == "pending":
            _h, rows = parse_table(lines, s["start"], s["end"], None,
                                   rep.table_strays, "三、待確認")
            rep.pending_rows.extend(rows)
        elif s["kind"] == "trace":
            _h, rows = parse_table(lines, s["start"], s["end"], None,
                                   rep.table_strays, "六、檢索紀錄")
            rep.trace_rows.extend(rows)

    # 第一節的預設行：**整份文件掃**，不限於某一節。
    # 這一條是 B3 的修法，也是本檔那條原則最直接的一次應用：以前只在
    # kind == "consensus" 的區段裡掃，於是把 `## 一、領域共識與未被質疑的預設`
    # 改名成 `## 一、這個領域大家都同意什麼`（甚至只是把那一行標題刪掉），
    # 預設就 2→0、unreadable 0、離開碼 0；而一份有 G3 候選的報告會多出一句
    # 「G3 候選 C01 的輸入 A1 不在第一節」——把作者送去補一條就躺在那裡的預設。
    # 預設行本身就有夠獨特的形狀（見 ASSUM_LOOKALIKE_RE 的結構字元要求），
    # 不需要靠節名找。表格區段跳過：那裡的 `| … |` 由 parse_table 負責。
    table_spans = [(s["start"], s["end"]) for s in rep.sections
                   if s["kind"] in ("killed", "pending", "trace")]
    for j, raw in enumerate(lines):
        if any(a <= j < b for a, b in table_spans):
            continue
        rec = parse_assumption(j + 1, raw)
        if rec:
            rep.assumptions.append(rec)
        elif ASSUM_LOOKALIKE_RE.match(raw):
            # 看起來是一條預設、卻讀不出來。丟掉它的代價：這一條既不被算進去
            # 也不被檢查，而 G3 指到它時的訊息會說「第一節沒有這一條」。
            rep.assumption_strays.append({"line": j + 1, "text": raw})

    return rep


# --------------------------------------------------------------------------
# 查核
# --------------------------------------------------------------------------

CHECK_DESCRIPTIONS = {
    "PARSE-01": "看起來是報告結構的一部分、卻讀不進來的行、列或表，一律回報："
                "表格列沒被讀進表（blockquote／全形直線／漏了行首直線／表格中間插了非表格的一行）、"
                "欄數與表頭不符、候選或家族的標題認不出來、"
                "以及一整張該在那裡卻讀不到的表",
    "SECT-01": "區段標題不得改寫（SKILL.md〈輸出格式〉：「區段標題與欄位標籤不得改寫」）。"
               "標題認不出來的區段一律改以內容定位、底下的規則照常執行，"
               "但標題本身是一條違規——不是停止檢查的理由",
    "STRUCT-01": "報告必須有〈存活候選〉〈待確認〉〈已淘汰〉〈檢索紀錄〉四個區段",
    "STRUCT-02": "表頭必須宣告文獻工具階層（第 0/1/2/3 階）",
    "COUNT-01": "「生成 N → 存活 M」的 M 必須等於實際候選區塊數",
    "COUNT-02": "生成數 N 不得小於存活數 M",
    "RECON-01": "候選結算必須對得起來：生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q，且每個候選編號只出現一次",
    "VERDICT-01": "判定／暫定狀態必須是該區段允許的值",
    "VERDICT-02": "存活候選只能是 ADJACENT／OPEN／INCREMENTAL",
    "ASSUM-01": "預設行要寫成讀得出來的形式（`預設 A1〔可選標籤〕：…`），且量化預設必須帶完整取樣框"
                "（N／檢索詞／limit／M′／pick／M／推翻性檢索／K′／K／樣本來源）；"
                "〔承接自地形 W…〕未補框者免（它不是這一輪抽樣出來的），標了〔已補取樣框〕就同標準",
    "ASSUM-02": "標〔印象，未驗證〕、或〔承接自地形 W…〕尚未補取樣框的預設，不得成為 G3 候選的輸入",
    "EVID-01": "每個存活候選都要有搜尋證據欄",
    "EVID-02": "搜尋證據欄不得為空或佔位符",
    "EVID-03": "搜尋證據欄必須含至少一個具體查詢詞",
    "NEIGH-01": "最接近的既有研究欄要存在；若指名了文獻就要帶識別碼",
    "KILL-01": "每一個淘汰列都必須指名關鍵文獻",
    "KILL-02": "CROWDED 必須指名 ≥3 篇",
    "KILL-03": "DONE 的淘汰原因必須含摘要逐字引句",
    "ID-01": "被指名的關鍵文獻必須帶識別碼（DOI／arXiv／S2）",
    "TRACE-01": "二／三／四節的每個候選都要在〈檢索紀錄〉有對應列"
                "（唯一例外：三、待確認裡〔未驗證〕、以及卡在術語的〔UNSEARCHABLE〕）",
    "TRACE-02": "〈檢索紀錄〉的查詢詞不得為佔位符",
    "LANG-01": "不得斷言「不存在／沒有人做過」，只能寫「這次搜尋沒有回傳」",
    "TIER-01": "宣告未執行檢索時不得填寫任何新穎性判定或淘汰判定",
    # ---- 以下五條只作用在領域地形報告（landscape）------------------------
    "LHEAD-01": "地形報告的表頭要宣告〈模式〉是領域地形，並逐字帶〈這份報告不做什麼〉那一行",
    "LVOCAB-01": "地形報告不得出現新穎性判定詞彙（ADJACENT／OPEN／INCREMENTAL／DONE／CROWDED）",
    "LCOST-01": "每個家族都要同時寫出〈買到什麼〉與〈付出什麼〉，查不到就寫「還沒查到」，不得留白或佔位符",
    "LSTAT-01": "〈狀態〉必須是五個合法值之一；不是〔涵蓋不足〕就要在同一欄掛上檢索句型",
    "LWALL-01": "第六節的牆與第二節的〈默默預設〉要雙向對得起來，〈家族數〉等於去重後的家族數",
}


class BaseChecker(object):
    """兩種報告共用的東西：findings 的收集、以及跨模式都成立的規則。"""

    def __init__(self, rep, path):
        self.rep = rep
        self.path = path
        self.findings = []

    def add(self, check, line, text, message):
        self.findings.append(
            {
                "check": check,
                "line": max(1, int(line or 1)),
                "text": (text or "").strip()[:200],
                "message": message,
                "rule": CHECK_DESCRIPTIONS.get(check, ""),
            }
        )

    # ---- 讀不進來的行與列（兩種報告共用）----------------------------------
    def check_parse(self):
        """解析器可以寬容，但不可以安靜。

        這條規則守的不是「報告寫錯了什麼」，而是「查核器讀不到什麼」。
        兩者的差別在下游：讀不到的那一列會讓依賴它的每一條規則失去對象，
        而**計數類的規則會把它顯示成算術對不起來**——RECON-01 說「結算寫已淘汰 6、
        第四節實際有 5 列」，作者於是去改那個 6，而 6 是對的，壞的是那一列的形狀。
        分開一個 id 就是為了不要再把人送去改對的東西。
        """
        for s in self.rep.table_strays:
            where = s.get("where") or "表格"
            self.add("PARSE-01", s["line"], s["text"],
                     "〈%s〉這一列讀不進來：%s。讀不到的列不會被任何規則檢查，"
                     "而它會讓對帳的數字看起來像算錯，把人送去改對的東西"
                     % (where, s["why"]))
        for s in self.rep.head_strays:
            self.add("PARSE-01", s["line"], s["text"], s["why"])
        for s in self.rep.table_missing:
            where = ("整份報告裡" if s.get("whole_doc")
                     else "這一節的標題說它是%s，這裡卻"
                          % SECTION_SHAPE_HINT.get(s["kind"], s["kind"]))
            self.add("PARSE-01", s["line"], s["text"],
                     "%s讀不到任何一張〈%s〉。最常見的原因是那張表是從渲染畫面複製回來的"
                     "——每一列都沒有直線 `|`，連表頭都沒有，於是沒有任何形狀可以認；"
                     "第二種原因是整張表沒寫。兩種都不是「沒問題」："
                     "底下每一條逐列跑的規則都沒有對象，而沒有對象的規則永遠是綠的"
                     % (where, SECTION_SHORT_NAME.get(s["kind"], s["kind"])))

    # ---- 被改寫的區段標題（兩種報告共用）----------------------------------
    def check_sections(self):
        """SKILL.md 說區段標題不得改寫，而以前沒有任何一條規則在讀這件事——
        改寫的後果是「底下那一批規則安靜地失去對象」，然後由別的規則假裝沒事
        （或根本沒有別的規則）。現在後果只剩一個：這一行自己被指出來。
        """
        for s in self.rep.section_renames:
            self.add(
                "SECT-01", s["line"], s["text"],
                "這一節的標題「%s」認不出它是哪一節（照標題只能歸成%s），"
                "但它的內容是%s。SKILL.md〈輸出格式〉要求區段標題不得改寫，"
                "因為下游查核器是逐字比對的。本次已改用內容定位，底下的規則照常執行"
                "——標題請改回含「%s」的固定寫法。"
                "（靠標題定位的查核器碰到改寫過的標題，會變成「沒有這一節、"
                "因此沒有違規」，那是最壞的一種綠燈。）"
                % (strip_md(s["title"])[:40],
                   SECTION_KIND_LABEL.get(s["title_kind"], s["title_kind"]),
                   SECTION_SHAPE_HINT.get(s["kind"], s["kind"]),
                   SECTION_TITLE_KEYWORD.get(s["kind"], s["kind"])))

    # ---- 表頭的文獻工具階層（兩種報告都要宣告）-----------------------------
    def check_tool_tier(self):
        header_text = "\n".join(t for _, t in self.rep.header_lines)
        if not re.search(r"文獻工具", header_text):
            self.add("STRUCT-02", 1, "", "表頭缺少「**文獻工具**：…」宣告，無法判斷這份報告的查核階層")
            return
        for lineno, t in self.rep.header_lines:
            if "文獻工具" in t:
                val = t.split("：", 1)[-1] if "：" in t else t.split(":", 1)[-1]
                if is_placeholder(val):
                    self.add("STRUCT-02", lineno, t, "「文獻工具」宣告是空的或佔位符")
                break

    # ---- 措辭（兩種報告都適用）--------------------------------------------
    def lang_exempt(self, line):
        """規格要求這個模式逐字寫出、因此不受 LANG-01 管的整行。預設一行都沒有。"""
        return False

    def check_language(self):
        for i, ln in enumerate(self.rep.lines):
            if ASSERTIVE_GUARD.search(ln):
                continue
            if self.lang_exempt(ln):
                continue
            for pat, label in ASSERTIVE_PATTERNS:
                m = re.search(pat, ln)
                if m:
                    self.add("LANG-01", i + 1, ln,
                             "斷言式措辭「%s」：搜不到是搜尋結果，不存在是斷言，報告只能寫前者" % m.group(0))


class Checker(BaseChecker):
    # ---- 結構 -----------------------------------------------------------
    def check_structure(self):
        kinds = set(s["kind"] for s in self.rep.sections)
        for kind, label in (("survivors", "二、存活候選"), ("pending", "三、待確認"),
                            ("killed", "四、已淘汰"), ("trace", "六、檢索紀錄")):
            if kind not in kinds:
                # 缺整個區段是「全檔級」缺陷，沒有肇事行；錨在第 1 行，
                # 讓每一筆 finding 都有可定位的行號（下游工具靠這個跳轉）。
                self.add("STRUCT-01", 1, "", "找不到〈%s〉區段（以 `## ` 標題辨識）" % label)
        self.check_tool_tier()

    # ---- 數量 -----------------------------------------------------------
    def check_counts(self):
        actual = len(self.rep.candidates)
        if self.rep.declared_survived is None:
            self.add(
                "COUNT-01",
                self.rep.sections[0]["line"] if self.rep.sections else 1,
                "",
                "找不到「生成 N 個 → 存活 M 個」宣告，無法核對候選數",
            )
            return
        if self.rep.declared_survived != actual:
            self.add(
                "COUNT-01",
                self.rep.count_line,
                self.rep.lines[self.rep.count_line - 1],
                "宣告存活 %d 個，實際只有 %d 個候選區塊（### 候選 N）"
                % (self.rep.declared_survived, actual),
            )
        if self.rep.declared_generated is not None and self.rep.declared_generated < self.rep.declared_survived:
            self.add(
                "COUNT-02",
                self.rep.count_line,
                self.rep.lines[self.rep.count_line - 1],
                "生成數 %d 小於存活數 %d" % (self.rep.declared_generated, self.rep.declared_survived),
            )

    # ---- 候選結算（二＋三＋四 要蓋住每一個生成出來的候選） ----------------
    def check_reconciliation(self):
        rep = self.rep
        line_of = {}
        seen = {}
        dup_reported = set()

        def register(cid, lineno, where, raw):
            if cid in seen:
                if cid not in dup_reported:
                    self.add("RECON-01", lineno, raw,
                             "候選編號 %s 重複出現（%s 與 %s）——每個編號只能落在二／三／四其中一節一次"
                             % (cid, seen[cid], where))
                    dup_reported.add(cid)
                return
            seen[cid] = where
            line_of[cid] = lineno

        for c in rep.candidates:
            head = cand_head_text(c)
            if not c["cid"]:
                self.add("RECON-01", c["line"], head,
                         "候選區塊沒有候選編號（應寫成 `### 候選 %s（C01）：…`），無法與三、四節對帳"
                         % ("%d" % c["ordinal"] if c["ordinal"] is not None else "N"))
            else:
                register(c["cid"], c["line"], "二、存活候選", head)
        for r in rep.pending_rows:
            raw = rep.lines[r["_line"] - 1]
            cid = first_cid(r.get("candidate", ""))
            if not cid:
                self.add("RECON-01", r["_line"], raw,
                         "待確認列的〈候選〉欄沒有以候選編號（C01…）開頭，無法與其他兩節對帳")
            else:
                register(cid, r["_line"], "三、待確認", raw)
        for r in rep.kill_rows:
            raw = rep.lines[r["_line"] - 1]
            cid = first_cid(r.get("candidate", ""))
            if not cid:
                self.add("RECON-01", r["_line"], raw,
                         "已淘汰列的〈候選〉欄沒有以候選編號（C01…）開頭，無法與其他兩節對帳")
            else:
                register(cid, r["_line"], "四、已淘汰", raw)

        if rep.settlement is None:
            lineno = rep.settlement_line or 1
            raw = rep.lines[lineno - 1] if rep.settlement_line else ""
            self.add("RECON-01", lineno, raw,
                     "表頭缺少可解析的「**候選結算**：生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q」")
            return

        n, m, p, q = rep.settlement
        lineno = rep.settlement_line
        raw = rep.lines[lineno - 1]
        if n != m + p + q:
            self.add("RECON-01", lineno, raw,
                     "候選結算對不起來：生成 %d ≠ 存活 %d ＋ 待確認 %d ＋ 已淘汰 %d（＝%d），差額就是被靜默丟掉的候選"
                     % (n, m, p, q, m + p + q))
        if m != len(rep.candidates):
            self.add("RECON-01", lineno, raw,
                     "結算寫存活 %d，第二節實際有 %d 個候選區塊" % (m, len(rep.candidates)))
        if p != len(rep.pending_rows):
            self.add("RECON-01", lineno, raw,
                     "結算寫待確認 %d，第三節實際有 %d 列" % (p, len(rep.pending_rows)))
        if q != len(rep.kill_rows):
            self.add("RECON-01", lineno, raw,
                     "結算寫已淘汰 %d，第四節實際有 %d 列" % (q, len(rep.kill_rows)))

    # ---- 第一節的預設 ----------------------------------------------------
    @staticmethod
    def _frame_advice(a, problem):
        """取樣框不完整時該怎麼辦——本輪自己盤的與承接來的，退路不一樣。

        自己盤的退回〔印象，未驗證〕；承接來的退回〔承接自地形 W…〕，**不是**
        〔印象，未驗證〕。兩者效力相同（都不得當 G3 輸入），但把承接的標籤改寫掉，
        讀者就再也看不出這一條是別份報告帶進來的，而那正是〈地形來源〉那一行要交代的事。
        """
        if a["inherited"]:
            return ("%s。這一條標了〔已補取樣框〕，就要與本輪量化的預設同標準：五個數字補齊，"
                    "或把標籤改回〔承接自地形 W…〕退回未補框（效力同〔印象，未驗證〕、不得作為 G3 輸入）"
                    "——不要改寫成〔印象，未驗證〕，來源要留給讀者看得見" % problem)
        return "量化預設的%s；未量化的預設一律標〔印象，未驗證〕" % problem

    def check_assumptions(self):
        for s in self.rep.assumption_strays:
            # 「看起來是一條預設、卻讀不出來」。以前這種行是靜默丟掉的，於是：
            # 這一條不被算進去、不被檢查，報告照樣綠；而它若被 G3 指到，
            # 訊息會說「第一節沒有這一條」——把讀者送去找一個不存在的缺漏。
            self.add("ASSUM-01", s["line"], s["text"],
                     "這一行看起來是一條預設，卻不是讀得出來的形式，因此**整條沒有被檢查**。"
                     "固定寫法：`- 預設 A1〔可選的來源標籤〕：〈一句話〉｜標題層掃描 …`"
                     "（行首可以是 `-` 或 `> `，編號與冒號之間可以有一串〔…〕標籤，"
                     "冒號也可以用全形直線；除此之外的形狀讀不到）。"
                     "若這一行其實只是**在講**那幾條預設的散文，那這是一次刻意留下的假紅燈"
                     "——把句子改成不以「預設 A1」開頭即可。理由見 ASSUM_LOOKALIKE_RE 的註解："
                     "假紅燈花讀者五分鐘，假綠燈是查核器對沒讀過的文件說通過")
        for a in self.rep.assumptions:
            raw = self.rep.lines[a["line"] - 1]
            if not a["aid"]:
                self.add("ASSUM-01", a["line"], raw,
                         "預設沒有編號（應寫成「預設 A1：…」）——第 3 步的 G3 與第六節的推翻性檢索都靠它對帳")
            if a["inherited"] and not a["framed"]:
                # 承接自地形報告、尚未補取樣框。地形模式在定義上就沒有跑過
                # N／M′／M／K′／K（它的錨定文獻是代表性的，不是抽樣的），
                # 要求它補一個取樣框，等於逼報告去編一組沒跑過的數字。
                # 它的效力等同〔印象，未驗證〕，而那個效力由 ASSUM-02 落實在
                # 「不得當 G3 輸入」上——不是在這裡罰它沒有取樣框。
                continue
            if a["impression"]:
                continue  # 印象級預設本來就不必量化，但也不得當 G3 輸入（ASSUM-02）
            if a["missing"]:
                self.add("ASSUM-01", a["line"], raw,
                         self._frame_advice(a, "取樣框缺少欄位：%s" % "、".join(a["missing"])))
                continue
            num = a["numbers"]
            if num.get("Mp", 0) < 3:
                self.add("ASSUM-01", a["line"], raw,
                         self._frame_advice(a, "摘要層精讀只有 %d 篇（M′ < 3）" % num.get("Mp", 0)))
            if num.get("M", 0) > num.get("Mp", 0):
                self.add("ASSUM-01", a["line"], raw,
                         "沿用篇數 M=%d 大於摘要層精讀 M′=%d——沿用只能在讀過摘要的樣本裡數"
                         % (num.get("M", 0), num.get("Mp", 0)))
            if num.get("K", 0) > num.get("Kp", 0):
                self.add("ASSUM-01", a["line"], raw,
                         "推翻性檢索讀後 K=%d 大於回傳 K′=%d" % (num.get("K", 0), num.get("Kp", 0)))

    def check_g3_inputs(self):
        by_id = {}
        for a in self.rep.assumptions:
            if a["aid"]:
                by_id.setdefault(a["aid"], a)
        # 讀不出來的那些預設行，編號還是撈得到。撈它是為了**閉嘴**：ASSUM-01 已經
        # 指著那一行說「這一條讀不出來」，這裡若再說一次「第一節沒有這一條」，
        # 就是把讀者送去找一個不存在的缺漏——正是這次要消滅的那句話。
        stray_ids = set()
        for s in self.rep.assumption_strays:
            m = re.search(r"預設\s*([A-Za-z]?\d{1,3})", strip_md(s["text"]))
            if not m:
                continue
            sid = m.group(1).upper()
            if sid and sid[0].isdigit():
                sid = "A" + sid
            stray_ids.add(sid)
        for c in self.rep.candidates:
            if "gap_type" not in c["fields"]:
                continue
            lineno, val = c["fields"]["gap_type"]
            if not re.search(r"G3", strip_md(val), re.I):
                continue
            raw = self.rep.lines[lineno - 1]
            refs = ["A" + g for g in AREF_RE.findall(strip_md(val))]
            if not refs:
                self.add("ASSUM-02", lineno, raw,
                         "G3 候選沒有指名它反轉的是哪一條預設（寫成「G3 預設反轉（反轉 A1）」）")
                continue
            for ref in refs:
                a = by_id.get(ref)
                if a is None:
                    if ref in stray_ids:
                        continue  # 那一行在第一節裡，只是讀不出來——ASSUM-01 已經報過
                    self.add("ASSUM-02", lineno, raw,
                             "G3 候選指到第一節沒有的預設 %s" % ref)
                elif a["inherited"] and not a["framed"]:
                    # 這一條**在**第一節裡，只是還沒付檢索成本。訊息一定要講清楚是哪一種：
                    # 說它「不存在」會把讀者送去找一個不存在的缺漏，而真正的動作
                    # 是對這一條（只有這一條）補跑取樣框。
                    self.add("ASSUM-02", lineno, raw,
                             "G3 候選的輸入 %s 是〔承接自地形 W…〕、尚未補取樣框（見第 %d 行）"
                             "——它在第一節裡，但地形模式沒有跑過 N／M′／M／K′／K，效力等同"
                             "〔印象，未驗證〕，不得長出候選。要反轉它就只對這一條補跑取樣框，"
                             "補完標成〔承接自地形 W…，已補取樣框〕再進 G3"
                             % (ref, a["line"]))
                elif a["impression"]:
                    self.add("ASSUM-02", lineno, raw,
                             "G3 候選的輸入 %s 標了〔印象，未驗證〕——印象級預設不得長出候選（見第 %d 行）"
                             % (ref, a["line"]))

    # ---- 判定詞彙 --------------------------------------------------------
    # 括號態：SKILL.md 用〔…〕標記中繼狀態，後面常接補充語
    # （例：`〔待驗證〕**不列入存活**`、`〔矛盾已觀察，機制未知〕**不列入存活**`）。
    # 括號內就是判定值，括號外是說明，不能一起丟進詞彙表比對。
    BRACKETED_RE = re.compile(r"^[〔【\[]\s*([^〕】\]]+?)\s*[〕】\]]")

    def _clean_verdict(self, raw):
        v = strip_md(raw)
        m = self.BRACKETED_RE.match(v)
        if m:
            return m.group(1).strip().rstrip("：:")
        v = v.strip("〔〕[]（）() 　")
        v = re.split(r"[，,。；;（(]", v)[0].strip()
        v = v.rstrip("：:")
        return v

    def check_verdicts(self):
        # 降級模式：報告已宣告「本次未執行任何檢索」。SKILL.md 對這個模式的規定是
        # 「不得填寫任何判定欄」，所以此時「沒有判定欄」是遵守規格，不是缺陷。
        # 這個模式底下唯一該抓的相反錯誤（沒檢索卻給判定）由 TIER-01 負責。
        degraded = self.rep.no_search_declared
        for c in self.rep.candidates:
            if "verdict" not in c["fields"]:
                if not degraded:
                    self.add("VERDICT-01", c["line"], cand_head_text(c),
                             "候選缺少〈新穎性判定〉欄（欄位要寫成 `- **新穎性判定**：…` 這種清單行；"
                             "行首可以是 `-` 或 `> `，沒有標記的行讀不到）")
                continue
            lineno, raw = c["fields"]["verdict"]
            v = self._clean_verdict(raw)
            if v not in ALLOWED_VERDICTS:
                self.add("VERDICT-01", lineno, self.rep.lines[lineno - 1],
                         "判定值「%s」不在允許詞彙表內（存活只能是 %s）"
                         % (v, "／".join(sorted(SURVIVOR_VERDICTS))))
                continue  # 未知值已報，不再重複報 VERDICT-02
            if v not in SURVIVOR_VERDICTS and not degraded:
                # 降級模式下 未驗證／UNSEARCHABLE 正是唯一合規的值，不能反過來罰它
                self.add("VERDICT-02", lineno, self.rep.lines[lineno - 1],
                         "「%s」不能出現在存活候選；存活只能是 %s"
                         % (v, "／".join(sorted(SURVIVOR_VERDICTS))))

        # 空白的判定欄以前是直接跳過的，而跳過它等於**整列不受檢查**：
        # check_kills 也是看到空判定就 continue，於是一列沒有判定的淘汰，
        # KILL-01／02／03 與 ID-01 全部沒有對象，報告拿到綠燈。
        # 「這一欄是空的」本來就不在允許詞彙表內，該由這條規則說出來。
        for row in self.rep.pending_rows:
            raw = row.get("state", "")
            if not strip_md(raw):
                self.add("VERDICT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "待確認這一列沒有〈暫定狀態〉值（欄位空白，或表頭根本沒有這一欄）——"
                         "空白不在允許詞彙表內（允許：%s）" % "／".join(sorted(PENDING_STATES)))
                continue
            v = self._clean_verdict(raw)
            if v not in PENDING_STATES:
                self.add("VERDICT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "待確認的暫定狀態「%s」不在允許詞彙表內（允許：%s）"
                         % (v, "／".join(sorted(PENDING_STATES))))

        for row in self.rep.kill_rows:
            raw = row.get("verdict", "")
            if not strip_md(raw):
                self.add("VERDICT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "淘汰這一列沒有〈判定〉值（欄位空白，或表頭根本沒有這一欄）——"
                         "沒有判定的列，指名文獻／逐字引句／識別碼那幾條規則全部沒有對象，"
                         "整列等於沒有被檢查；已淘汰只能是 DONE／CROWDED")
                continue
            v = self._clean_verdict(raw)
            if v not in KILL_VERDICTS:
                self.add("VERDICT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "淘汰表的判定值「%s」不在允許詞彙表內（已淘汰只能是 DONE／CROWDED；"
                         "其他狀態一律進第三節待確認）" % v)

    # ---- 存活候選的證據 ---------------------------------------------------
    def check_survivor_evidence(self):
        degraded = self.rep.no_search_declared
        for c in self.rep.candidates:
            head = cand_head_text(c)
            if "evidence" not in c["fields"]:
                self.add("EVID-01", c["line"], head,
                         "候選缺少〈搜尋證據〉欄（也接受「證據」「檢索證據」；"
                         "欄位要寫成 `- **搜尋證據**：…` 這種清單行，沒有標記的行讀不到）")
            else:
                lineno, val = c["fields"]["evidence"]
                if is_placeholder(val):
                    self.add("EVID-02", lineno, self.rep.lines[lineno - 1],
                             "搜尋證據是空的或佔位符（「%s」）——沒有查詢詞就不能給新穎性判定" % strip_md(val))
                elif not degraded and not extract_queries(val):
                    # 降級模式沒有查詢詞可寫；此時要求逐字查詢詞等於逼報告捏造
                    self.add("EVID-03", lineno, self.rep.lines[lineno - 1],
                             "搜尋證據裡找不到具體查詢詞；查詢詞要逐字寫出，讓使用者能複製重跑")

            if "neighbour" not in c["fields"]:
                if not degraded:
                    # 沒檢索就找不出最近鄰；但只要報告指名了文獻，識別碼照樣要有（見下）
                    self.add("NEIGH-01", c["line"], head,
                             "候選缺少〈最接近的既有研究〉欄（欄位要寫成 "
                             "`- **最接近的既有研究**：…` 這種清單行）")
            else:
                lineno, val = c["fields"]["neighbour"]
                if is_placeholder(val):
                    self.add("NEIGH-01", lineno, self.rep.lines[lineno - 1],
                             "〈最接近的既有研究〉是空的或佔位符")
                elif YEAR_RE.search(strip_md(val)) and not has_identifier(val):
                    self.add("NEIGH-01", lineno, self.rep.lines[lineno - 1],
                             "指名了文獻卻沒有識別碼（DOI／arXiv／S2 corpus ID），使用者無法拿去查核")

    # ---- 淘汰列 ----------------------------------------------------------
    def check_kills(self):
        for row in self.rep.kill_rows:
            lineno = row["_line"]
            raw_line = self.rep.lines[lineno - 1]
            v = self._clean_verdict(row.get("verdict", ""))
            if not v:
                continue
            lit = row.get("literature", "")
            reason = row.get("reason", "")
            ident = row.get("identifier", "")

            named = not is_placeholder(lit)
            if not named:
                self.add("KILL-01", lineno, raw_line,
                         "判定 %s 卻沒有指名關鍵文獻——每一個淘汰都必須指名殺死它的那篇文獻；"
                         "指不出來就不是淘汰，該進第三節待確認" % v)
                continue  # 沒指名文獻，後面的識別碼／篇數檢查沒有對象

            if not has_identifier(ident) and not has_identifier(lit):
                self.add("ID-01", lineno, raw_line,
                         "關鍵文獻「%s」沒有識別碼，無法餵給 lit-review 的 retract／verify 查核"
                         % strip_md(lit)[:60])

            if v == "CROWDED":
                n = count_papers(lit)
                if n < 3:
                    self.add("KILL-02", lineno, raw_line,
                             "CROWDED 只列了 %d 篇；必須 ≥3 篇並逐篇寫出各自涵蓋哪個子問題，否則改判 ADJACENT" % n)

            if v == "DONE":
                if not has_verbatim_quote(reason):
                    self.add("KILL-03", lineno, raw_line,
                             "DONE 的淘汰原因沒有摘要逐字引句（「…」）——只憑標題像不能淘汰")

    # ---- 檢索紀錄 --------------------------------------------------------
    def _trace_covers(self, cell, cid, ordinal, title):
        c = strip_md(cell)
        if not c:
            return False
        if cid:
            return bool(re.search(r"(?<![A-Za-z0-9])%s(?![0-9])" % re.escape(cid), c.upper()))
        if ordinal is not None and re.search(r"(?<!\d)0*%d(?!\d)" % ordinal, c):
            return True
        t = strip_md(title or "")
        if len(t) >= 6:
            for i in range(0, len(t) - 5):
                if t[i:i + 6] in c:
                    return True
        return False

    def _pending_trace_exempt(self, row):
        """第三節裡「一次也沒被搜過」的列，不必附檢索紀錄。

        SKILL.md〈互鎖的例外〉：〔未驗證〕之所以在第三節，正是因為它沒被搜過；
        要求它附一列檢索紀錄，等於逼報告去寫一次沒跑過的搜尋——那是這支查核器
        存在的理由的反面。〔UNSEARCHABLE〕同理，但只限於卡住的是**術語**，
        不是檢索工作量；分辨這兩者的依據是〈還缺哪一項證據〉欄自己怎麼寫。

        豁免到此為止：第二節的存活候選、第四節的淘汰列，以及第三節其他所有
        暫定狀態，都是**搜過才寫得出來**的宣稱，一律要拿得出檢索紀錄。
        """
        state = self._clean_verdict(row.get("state", ""))
        if state == "未驗證":
            return True
        if state.upper() == "UNSEARCHABLE":
            return bool(TERMINOLOGY_RE.search(strip_md(row.get("missing", ""))))
        return False

    def check_trace(self):
        if not any(s["kind"] == "trace" for s in self.rep.sections):
            return  # STRUCT-01 已報
        degraded = self.rep.no_search_declared
        if not self.rep.trace_rows:
            if not degraded:
                # 降級模式下本表本來就該是空的——空表正是「這次沒檢索」的證據
                line = next(s["line"] for s in self.rep.sections if s["kind"] == "trace")
                self.add("TRACE-01", line, "",
                         "〈檢索紀錄〉區段沒有任何資料列；沒有檢索紀錄的候選不得給新穎性判定")
            return
        if not degraded:
            targets = []
            for c in self.rep.candidates:
                targets.append((c["line"], cand_head_text(c),
                                c["cid"], c["ordinal"], c["title"], cand_ref(c),
                                "沒有紀錄的候選不得給判定，一律標〔未驗證〕移進第三節"))
            for r in self.rep.pending_rows:
                cid = first_cid(r.get("candidate", ""))
                if not cid:
                    continue  # 沒編號的列已由 RECON-01 報過，這裡不重複開槍
                if self._pending_trace_exempt(r):
                    continue  # 真的一次也沒搜過的列——見 _pending_trace_exempt
                targets.append((r["_line"], self.rep.lines[r["_line"] - 1],
                                cid, None, r.get("candidate", ""), cid,
                                "這個暫定狀態是搜過才寫得出來的；如果真的一次也沒搜過，"
                                "改標〔未驗證〕（那一種才免附紀錄）"))
            for r in self.rep.kill_rows:
                cid = first_cid(r.get("candidate", ""))
                if not cid:
                    continue
                targets.append((r["_line"], self.rep.lines[r["_line"] - 1],
                                cid, None, r.get("candidate", ""), cid,
                                "沒有檢索紀錄的淘汰不成立，退回第三節待確認"))
            for lineno, text, cid, ordinal, title, label, remedy in targets:
                hit = any(
                    self._trace_covers(r.get("candidate", ""), cid, ordinal, title)
                    for r in self.rep.trace_rows
                )
                if not hit:
                    self.add("TRACE-01", lineno, text,
                             "%s 在〈檢索紀錄〉裡沒有對應列——%s" % (label, remedy))
        for r in self.rep.trace_rows:
            q = r.get("query", "")
            if is_placeholder(q) or not extract_queries(q):
                self.add("TRACE-02", r["_line"], self.rep.lines[r["_line"] - 1],
                         "檢索紀錄的查詢詞欄不是具體查詢詞（「%s」）" % strip_md(q))

    # ---- 階層一致性 ------------------------------------------------------
    def check_tier(self):
        if not self.rep.no_search_declared:
            return
        for c in self.rep.candidates:
            if "verdict" in c["fields"]:
                lineno, raw = c["fields"]["verdict"]
                v = self._clean_verdict(raw)
                if v and v not in ("未驗證", "UNSEARCHABLE"):
                    self.add("TIER-01", lineno, self.rep.lines[lineno - 1],
                             "報告已宣告未執行檢索，卻仍填了判定「%s」" % v)
        for row in self.rep.kill_rows:
            v = self._clean_verdict(row.get("verdict", ""))
            if v in KILL_VERDICTS:
                self.add("TIER-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "報告已宣告未執行檢索，卻仍淘汰了候選（判定「%s」）" % v)

    def run(self):
        self.check_parse()
        self.check_sections()
        self.check_structure()
        self.check_counts()
        self.check_reconciliation()
        self.check_assumptions()
        self.check_g3_inputs()
        self.check_verdicts()
        self.check_survivor_evidence()
        self.check_kills()
        self.check_trace()
        self.check_language()
        self.check_tier()
        self.findings.sort(key=lambda f: (f["line"], f["check"]))
        return self.findings


class LandscapeChecker(BaseChecker):
    """領域地形報告的規則集——**刻意只有五條**，外加兩條跨模式共用的。

    為什麼這麼薄：這個模式存在的理由，就是缺口獵捕的舉證門檻對「我只想先知道
    自己在哪裡」太重（一次實測裡有一半的候選最後只能寫〔待確認〕）。在這裡把規則
    疊回去，等於把那個門檻原封不動搬過來，於是又回到同一個結局。

    所以這五條各自對應一種「照著格式寫、但已經在騙人」的方式，其餘一律不查：
    漂移成判決（LVOCAB-01）、只講好處不講代價（LCOST-01）、把趨勢寫成領域事實
    而不是檢索結果（LSTAT-01）、牆與預設對不起來（LWALL-01）、以及報告自己不肯
    宣告它是什麼（LHEAD-01）。哪些沒查、為什麼沒查，寫在 evals/README.md。
    """

    def lang_exempt(self, line):
        """〈這份報告不做什麼〉那一行逐字含有「沒有人做過」，是規格要求的固定句。

        豁免窄到只認那一整句：必須是那個欄位、而且欄位值**恰好**等於固定句。
        在後面續寫任何一個字，這一行就回到 LANG-01 管轄——否則這條豁免會變成
        「把斷言接在免死金牌後面」的通道。
        """
        s = strip_md(line)
        if LANDSCAPE_DISCLAIMER_LABEL not in s:
            return False
        return s.split("：", 1)[-1].strip() == LANDSCAPE_DISCLAIMER

    # ---- 表頭：報告要自己講出它是什麼、不做什麼 ---------------------------
    def check_header(self):
        mode_declared = False
        disclaimer = None
        for lineno, t in self.rep.header_lines:
            s = strip_md(t)
            if LANDSCAPE_MODE_RE.match(s):
                mode_declared = True
            if LANDSCAPE_DISCLAIMER_LABEL in s and disclaimer is None:
                disclaimer = (lineno, t, s)
        if not mode_declared:
            self.add("LHEAD-01", 1, "",
                     "表頭缺少「**模式**：領域地形…」那一行——讀者無從知道這一份不是新穎性判定")
        if disclaimer is None:
            self.add("LHEAD-01", 1, "",
                     "表頭缺少〈這份報告不做什麼〉那一行；這是這個模式唯一的自我限制宣告，"
                     "逐字寫：%s" % LANDSCAPE_DISCLAIMER)
        if disclaimer is not None and disclaimer[2].split("：", 1)[-1].strip() != LANDSCAPE_DISCLAIMER:
            self.add("LHEAD-01", disclaimer[0], disclaimer[1],
                     "〈這份報告不做什麼〉不是逐字的固定句（多一字少一字都算）。應為：%s"
                     % LANDSCAPE_DISCLAIMER)

    # ---- 模式混淆：地形報告裡不得有新穎性判定詞彙 -------------------------
    def check_mode_vocabulary(self):
        for i, ln in enumerate(self.rep.lines):
            token = NOVELTY_TOKEN_RE.search(ln)
            if token:
                self.add("LVOCAB-01", i + 1, ln,
                         "地形報告出現新穎性判定詞彙「%s」。這個模式不淘汰、不判新穎性，"
                         "寫得出判定就表示它已經在下一個它沒有付舉證成本的判決；"
                         "要判定請跑缺口獵捕，那邊每個判定都要附檢索紀錄" % token.group(1))

    # ---- 兩面都要寫：只有買到、沒有付出，就是描述不誠實 -------------------
    def check_cost(self):
        for fam in self.rep.families:
            head = "### %s %s" % (fam_ref(fam), fam["name"])
            offenders = []
            for key, label in (("buys", "買到什麼"), ("costs", "付出什麼")):
                if key not in fam["fields"]:
                    offenders.append((fam["line"], head, label, "整欄不見了"))
                elif is_placeholder(fam["fields"][key][1]):
                    offenders.append((fam["fields"][key][0],
                                      self.rep.lines[fam["fields"][key][0] - 1], label,
                                      "是空的或佔位符（「%s」）" % strip_md(fam["fields"][key][1])))
            if offenders:
                lineno, raw, label, why = offenders[0]
                self.add("LCOST-01", lineno, raw,
                         "家族 %s 的〈%s〉%s。一個做法如果真的沒有代價，它早就把其他家族清光了；"
                         "查不到就逐字寫「還沒查到」，不要留白讓讀者以為它免費" % (fam_ref(fam), label, why))
        for row in self.rep.glance_rows:
            blank = [label for key, label in (("buys", "買到什麼"), ("costs", "付出什麼"))
                     if is_placeholder(row.get(key, ""))]
            if blank:
                self.add("LCOST-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "一眼表這一列的〈%s〉是空的或佔位符——兩邊都要寫得出來才算描述完一個家族"
                         % "〉〈".join(blank))

    # ---- 狀態：飽和／活躍是檢索結果，不是領域事實 -------------------------
    def _status_problem(self, value):
        v = strip_md(value or "")
        v = re.split(r"[｜|]", v)[0]
        v = v.strip("〔〕【】[]（）() 　").strip()
        if not v:
            return "〈狀態〉是空的"
        if v not in LAND_STATUS_VALUES:
            return ("〈狀態〉值「%s」不在五個合法值內（%s）"
                    % (v, "／".join(LAND_STATUS_VALUES)))
        if v == "涵蓋不足":
            return None      # 誠實的退場：標了就走，不必附證據
        if not LAND_STATUS_EVIDENCE_RE.search(strip_md(value)):
            return ("〈狀態〉「%s」沒有掛檢索句型——同一欄要寫「`<查詢詞>` 在 <索引> 回傳 X 筆，"
                    "其中 <年份> 之後 Y 筆」。判不出來就寫〔涵蓋不足〕，那是這個模式允許的答案" % v)
        if not (BACKTICK_RE.search(value) or QUOTED_ANY_RE.search(value)):
            return ("〈狀態〉「%s」有筆數卻沒有逐字查詢詞——讀者要能把那個詞複製去重跑一次" % v)
        return None

    def check_status(self):
        for fam in self.rep.families:
            if "status" not in fam["fields"]:
                self.add("LSTAT-01", fam["line"], "### %s %s" % (fam_ref(fam), fam["name"]),
                         "家族 %s 缺〈狀態〉欄" % fam_ref(fam))
                continue
            lineno, val = fam["fields"]["status"]
            problem = self._status_problem(val)
            if problem:
                self.add("LSTAT-01", lineno, self.rep.lines[lineno - 1],
                         "家族 %s 的%s" % (fam_ref(fam), problem))
        for row in self.rep.glance_rows:
            cell = row.get("status", "")
            if not strip_md(cell):
                # 空白以前是跳過的，而〈買到什麼〉〈付出什麼〉那兩欄空白是會被 LCOST-01
                # 抓的——同一張表的同一種缺陷不該有兩套待遇。空白也是「不在五個合法值內」。
                self.add("LSTAT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "一眼表這一列的〈狀態〉是空的（欄位空白，或表頭沒有這一欄）——"
                         "五個合法值是 %s，判不出來就寫〔涵蓋不足〕"
                         % "／".join(LAND_STATUS_VALUES))
                continue
            gv = strip_md(cell).strip("〔〕【】[]（）() 　").strip()
            if gv not in LAND_STATUS_VALUES:
                self.add("LSTAT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "一眼表的〈狀態〉「%s」不在五個合法值內（%s）"
                         % (gv, "／".join(LAND_STATUS_VALUES)))

    # ---- 牆與預設的雙向對帳（這一節是要交棒給獵捕的，對不起來就交不出去）----
    def check_walls(self):
        declared = []
        for fam in self.rep.families:
            if "assumptions" not in fam["fields"]:
                self.add("LWALL-01", fam["line"], "### %s %s" % (fam_ref(fam), fam["name"]),
                         "家族 %s 沒有〈默默預設〉欄；第六節的牆只能從這一欄長出來，"
                         "缺了它，這份地形圖最後一節就沒有原料" % fam_ref(fam))
                continue
            lineno, val = fam["fields"]["assumptions"]
            ids = ["F%s-%s" % (m.group(1), m.group(2).lower())
                   for m in LAND_ASSUM_ID_RE.finditer(val)]
            if not ids:
                self.add("LWALL-01", lineno, self.rep.lines[lineno - 1],
                         "家族 %s 的〈默默預設〉沒有可對帳的編號，要寫成「F<n>-a〈…〉；F<n>-b〈…〉」"
                         % fam_ref(fam))
            for aid in ids:
                declared.append((aid, fam_ref(fam), lineno))

        if not self.rep.wall_rows:
            if declared:
                line = next((s["line"] for s in self.rep.sections if s["kind"] == "walls"), 1)
                self.add("LWALL-01", line, "",
                         "找不到第六節的牆表（欄位：牆｜這條預設｜來源預設｜家族數｜性質｜拆的可能性），"
                         "第二節的 %d 條預設全部沒有歸屬——那一節正是要交給缺口獵捕的東西"
                         % len(declared))
            return

        known = set(a for a, _f, _l in declared)
        used = {}
        for row in self.rep.wall_rows:
            lineno = row["_line"]
            raw = self.rep.lines[lineno - 1]
            wall = strip_md(row.get("wall", "")) or "（無編號）"
            ids = ["F%s-%s" % (m.group(1), m.group(2).lower())
                   for m in LAND_ASSUM_ID_RE.finditer(row.get("sources", ""))]
            if not ids:
                self.add("LWALL-01", lineno, raw,
                         "牆 %s 的〈來源預設〉沒有任何預設編號（F<n>-<字母>）。"
                         "牆只能從第二節已經寫下來的預設長出來，不能直接想" % wall)
                continue
            unknown = sorted(set(a for a in ids if a not in known))
            if unknown:
                self.add("LWALL-01", lineno, raw,
                         "牆 %s 的〈來源預設〉指到第二節沒有的預設：%s"
                         % (wall, "、".join(unknown)))
            for aid in ids:
                if aid in used and used[aid] != wall:
                    self.add("LWALL-01", lineno, raw,
                             "預設 %s 同時掛在牆 %s 與牆 %s 底下；每條預設只歸一道牆，"
                             "否則〈家族數〉會把同一票算兩次" % (aid, used[aid], wall))
                used.setdefault(aid, wall)
            got = re.search(r"\d+", strip_md(row.get("famcount", "")))
            distinct = len(set(a.split("-")[0] for a in ids))
            if got is not None and int(got.group(0)) != distinct:
                self.add("LWALL-01", lineno, raw,
                         "牆 %s 的〈家族數〉寫 %s，〈來源預設〉去重後是 %d 個家族。"
                         "這一欄決定整張表的排序，數錯就等於把牆排錯"
                         % (wall, got.group(0), distinct))

        for aid, fid, lineno in declared:
            if aid not in used:
                self.add("LWALL-01", lineno, self.rep.lines[lineno - 1],
                         "第二節的預設 %s（家族 %s）沒有出現在第六節任何一道牆的〈來源預設〉欄——"
                         "它被寫下來然後不見了，接手的缺口獵捕拿不到它" % (aid, fid))

    def run(self):
        self.check_parse()
        self.check_sections()
        self.check_header()
        self.check_tool_tier()
        self.check_mode_vocabulary()
        self.check_cost()
        self.check_status()
        self.check_walls()
        self.check_language()
        self.findings.sort(key=lambda f: (f["line"], f["check"]))
        return self.findings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="研究缺口報告的格式查核器（檢查形式，不檢查真假）"
    )
    ap.add_argument("report", help="報告檔路徑（.md 或 .txt）")
    ap.add_argument("--json", action="store_true", dest="as_json", help="輸出機器可讀的 JSON")
    args = ap.parse_args(argv)

    path = args.report
    if not os.path.isfile(path):
        sys.stderr.write("找不到檔案：%s\n" % path)
        return 2
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".md", ".txt", ".markdown", ""):
        sys.stderr.write("提醒：預期 .md 或 .txt，收到 %s，仍以純文字解析。\n" % ext)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write("讀檔失敗（本工具只讀 UTF-8）：%s\n" % exc)
        return 2

    rep = parse_report(text)
    checker = LandscapeChecker if rep.mode == "landscape" else Checker
    findings = checker(rep, path).run()

    if args.as_json:
        print(json.dumps(
            {
                "report": os.path.abspath(path),
                "ok": not findings,
                "mode": rep.mode,
                "report_blocks": rep.report_blocks,
                "families": len(rep.families),
                "glance_rows": len(rep.glance_rows),
                "wall_rows": len(rep.wall_rows),
                "candidate_sections": len(rep.candidates),
                "declared_generated": rep.declared_generated,
                "declared_survived": rep.declared_survived,
                "settlement": list(rep.settlement) if rep.settlement else None,
                "assumptions": len(rep.assumptions),
                # 讀不進來的東西也要出現在解析摘要裡：包裝這支工具的人要能分辨
                # 「乾淨」與「根本沒讀到」，而那正是靜默丟行最擅長偽裝的差別。
                "unreadable": (len(rep.table_strays) + len(rep.head_strays)
                               + len(rep.assumption_strays)),
                # 靠內容才認出來的區段數。它與 unreadable 是不同的東西：那些行**讀得到**，
                # 是節名不對。包裝這支工具的人要能分辨「格式漂了」與「內容有問題」。
                "renamed_sections": len(rep.section_renames),
                "pending_rows": len(rep.pending_rows),
                "kill_rows": len(rep.kill_rows),
                "trace_rows": len(rep.trace_rows),
                "finding_count": len(findings),
                "findings": findings,
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 1 if findings else 0

    print("格式查核：%s" % os.path.basename(path))
    if rep.report_blocks:
        print("  （敘事型文件：只查 %d 個 report-start／report-end 區塊之內的內容）" % rep.report_blocks)
    if rep.mode == "landscape":
        print("  報告型別：領域地形（規則集刻意薄，見 evals/README.md）")
        print("  家族區塊 %d ／ 一眼表列 %d ／ 牆表列 %d"
              % (len(rep.families), len(rep.glance_rows), len(rep.wall_rows)))
    else:
        print("  候選區塊 %d ／ 待確認列 %d ／ 淘汰列 %d ／ 檢索紀錄列 %d"
              % (len(rep.candidates), len(rep.pending_rows), len(rep.kill_rows), len(rep.trace_rows)))
    if not findings:
        print("\n✅ 格式無違規。")
        print("   注意：本檢查只驗形式，不驗真假——文獻是否存在、是否被撤稿、")
        print("   摘要是否真的支持那句話，要跑 lit-review 的 verify／retract／check。")
        return 0

    print("\n❌ 發現 %d 項違規：\n" % len(findings))
    for f in findings:
        print("[%s] 第 %d 行" % (f["check"], f["line"]))
        print("    %s" % f["message"])
        if f["text"]:
            print("    原文：%s" % f["text"])
        print("")
    print("規則對照：")
    for cid in sorted(set(f["check"] for f in findings)):
        print("  %s — %s" % (cid, CHECK_DESCRIPTIONS.get(cid, "")))
    return 1


if __name__ == "__main__":
    sys.exit(main())
