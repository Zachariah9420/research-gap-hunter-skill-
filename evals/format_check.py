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
LAND_FAMILY_HEAD_RE = re.compile(r"^[Ff](\d{1,2})\b[\s：:.\-]*(.*)$")

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

# 第一節的預設行。編號與冒號之間允許一個括號標籤：SKILL.md 第 1 步（甲）承接
# 地形報告時，來源就寫在那裡（`預設 A1〔承接自地形 W3，支撐家族 F1、F4〕：…`），
# 而承接是兩個模式唯一的介面。這個括號一旦不被解析，承接來的預設對查核器就是
# 不存在——既不會被算進去，也不會被檢查，而 G3 指到它時的錯誤訊息會說「第一節
# 沒有這一條」，把讀者送去找一個不存在的缺漏。
ASSUM_LINE_RE = re.compile(
    r"^\s*[-*+]\s*\*{0,2}預設\s*([A-Za-z]?\d{0,3})\s*\*{0,2}"
    r"(?:\s*[〔【\[]([^〕】\]]*)[〕】\]])?"
    r"\s*\*{0,2}\s*[：:]\s*(.*)$"
)
IMPRESSION_RE = re.compile(r"[〔【\[]\s*印象\s*[，,]\s*未驗證\s*[〕】\]]")
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


def detect_mode(lines, first_h2):
    """判別這是哪一種報告。第一行的 H1 是主判別點，表頭〈模式〉是第二個。

    兩者都認不出來時回 "gap"：缺口報告是這支查核器原本唯一的對象，
    保守回退才不會讓既有報告因為新增了一個模式而突然不受查核。
    """
    head = lines[:first_h2] if first_h2 > 0 else lines
    for ln in head:
        s = strip_md(ln)
        if LANDSCAPE_H1_RE.match(s):
            return "landscape"
        if GAP_H1_RE.match(s):
            return "gap"
        if LANDSCAPE_MODE_RE.match(s):
            return "landscape"
    return "gap"


def parse_table(lines, start, end, aliases=None):
    """把某區段裡的第一張 markdown 表格解析成 (columns, rows)。"""
    if aliases is None:
        aliases = COLUMN_ALIASES
    rows = []
    header = None
    for i in range(start, end):
        raw = lines[i].strip()
        if not raw.startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if re.fullmatch(r"[\s:\-—–|]+", raw):
            continue
        if all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip()):
            continue
        if header is None:
            header = cells
            continue
        rows.append((i + 1, cells))
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
        rec = {"_line": lineno, "_cells": cells}
        for canon, idx in colmap.items():
            rec[canon] = cells[idx] if idx < len(cells) else ""
        out.append(rec)
    return header, out


def parse_assumption(lineno, raw):
    """把第一節的一條「預設」行拆成編號、來源標籤、是否印象級、五個取樣框數字。"""
    m = ASSUM_LINE_RE.match(raw)
    if not m:
        return None
    aid = m.group(1).strip().upper()
    if aid and aid[0].isdigit():
        aid = "A" + aid
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
        fm = re.match(r"^\s*[-*+]\s*\*{0,2}([^*：:]+?)\*{0,2}\s*[：:]\s*(.*)$", lines[j])
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


def parse_landscape(rep, heads):
    """地形報告：家族區塊（### F1 …）、一眼表、牆表。

    家族靠 `### F<n>` 認，不靠它落在哪一節——節名一旦被改寫，
    整份報告就會變成「沒有家族因此沒有違規」，那是最壞的一種綠燈。
    """
    lines = rep.lines
    fam_heads = []
    for i, lvl, t in heads:
        if lvl != 3:
            continue
        m = LAND_FAMILY_HEAD_RE.match(strip_md(t))
        if m:
            fam_heads.append((i, "F" + m.group(1), m.group(2).strip()))
    for n, (i, fid, name) in enumerate(fam_heads):
        end = fam_heads[n + 1][0] if n + 1 < len(fam_heads) else len(lines)
        nxt_h2 = next((s["start"] for s in rep.sections if s["start"] > i), len(lines))
        end = min(end, nxt_h2)
        rep.families.append(
            {"fid": fid, "name": name, "line": i + 1,
             "fields": parse_fields(lines, i + 1, end, LAND_LABEL_ALIASES)}
        )

    for s in rep.sections:
        if s["kind"] == "glance":
            _h, rows = parse_table(lines, s["start"], s["end"], LAND_GLANCE_COLUMNS)
            rep.glance_rows.extend(rows)
        elif s["kind"] == "walls":
            _h, rows = parse_table(lines, s["start"], s["end"], LAND_WALL_COLUMNS)
            rep.wall_rows.extend(rows)
    return rep


def parse_report(text):
    rep = Report()
    text, rep.report_blocks = apply_report_blocks(text)
    rep.lines = text.splitlines()
    lines = rep.lines

    heads = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))

    first_h2 = next((i for i, lvl, _ in heads if lvl == 2), len(lines))
    rep.header_lines = [(i + 1, lines[i]) for i in range(0, first_h2)]
    rep.mode = detect_mode(lines, first_h2)
    classify = classify_landscape_section if rep.mode == "landscape" else classify_section

    h2s = [(i, t) for i, lvl, t in heads if lvl == 2]
    for n, (i, t) in enumerate(h2s):
        end = h2s[n + 1][0] if n + 1 < len(h2s) else len(lines)
        rep.sections.append({"kind": classify(t), "title": t, "start": i, "end": end, "line": i + 1})

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

    # 候選區塊： ### 候選 1（C03）：… ；括號內的編號可省略（舊格式相容）
    cand_heads = []
    for i, lvl, t in heads:
        if lvl != 3:
            continue
        m = re.match(
            r"^(?:候選|候補|Candidate)\s*([0-9]+)\s*(?:[（(]\s*([Cc]\d{1,3})\s*[)）])?\s*[：:.\-]?\s*(.*)$",
            t,
        )
        if m:
            cid = m.group(2).upper() if m.group(2) else None
            cand_heads.append((i, int(m.group(1)), cid, m.group(3).strip()))
    for n, (i, ordinal, cid, title) in enumerate(cand_heads):
        end = cand_heads[n + 1][0] if n + 1 < len(cand_heads) else len(lines)
        nxt_h2 = next((s["start"] for s in rep.sections if s["start"] > i), len(lines))
        end = min(end, nxt_h2)
        fields = {}
        for j in range(i + 1, end):
            fm = re.match(r"^\s*[-*+]\s*\*{0,2}([^*：:]+?)\*{0,2}\s*[：:]\s*(.*)$", lines[j])
            if not fm:
                continue
            label = norm_key(fm.group(1))
            value = fm.group(2).strip()
            for canon, aliases in LABEL_ALIASES.items():
                if canon in fields:
                    continue
                if any(norm_key(a) in label for a in aliases):
                    fields[canon] = (j + 1, value)
                    break
        rep.candidates.append(
            {"ordinal": ordinal, "cid": cid, "title": title, "line": i + 1,
             "fields": fields, "start": i, "end": end}
        )

    for s in rep.sections:
        if s["kind"] == "killed":
            _h, rows = parse_table(lines, s["start"], s["end"])
            rep.kill_rows.extend(rows)
        elif s["kind"] == "pending":
            _h, rows = parse_table(lines, s["start"], s["end"])
            rep.pending_rows.extend(rows)
        elif s["kind"] == "trace":
            _h, rows = parse_table(lines, s["start"], s["end"])
            rep.trace_rows.extend(rows)
        elif s["kind"] == "consensus":
            for j in range(s["start"], s["end"]):
                rec = parse_assumption(j + 1, lines[j])
                if rec:
                    rep.assumptions.append(rec)

    return rep


# --------------------------------------------------------------------------
# 查核
# --------------------------------------------------------------------------

CHECK_DESCRIPTIONS = {
    "STRUCT-01": "報告必須有〈存活候選〉〈待確認〉〈已淘汰〉〈檢索紀錄〉四個區段",
    "STRUCT-02": "表頭必須宣告文獻工具階層（第 0/1/2/3 階）",
    "COUNT-01": "「生成 N → 存活 M」的 M 必須等於實際候選區塊數",
    "COUNT-02": "生成數 N 不得小於存活數 M",
    "RECON-01": "候選結算必須對得起來：生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q，且每個候選編號只出現一次",
    "VERDICT-01": "判定／暫定狀態必須是該區段允許的值",
    "VERDICT-02": "存活候選只能是 ADJACENT／OPEN／INCREMENTAL",
    "ASSUM-01": "量化預設必須帶完整取樣框（N／檢索詞／limit／M′／pick／M／推翻性檢索／K′／K／樣本來源）；"
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
            head = "### 候選 %d：%s" % (c["ordinal"], c["title"])
            if not c["cid"]:
                self.add("RECON-01", c["line"], head,
                         "候選區塊沒有候選編號（應寫成 `### 候選 %d（C01）：…`），無法與三、四節對帳"
                         % c["ordinal"])
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
                    self.add("VERDICT-01", c["line"], "### 候選 %d：%s" % (c["ordinal"], c["title"]),
                             "候選缺少〈新穎性判定〉欄")
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

        for row in self.rep.pending_rows:
            raw = row.get("state", "")
            if not strip_md(raw):
                continue
            v = self._clean_verdict(raw)
            if v not in PENDING_STATES:
                self.add("VERDICT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "待確認的暫定狀態「%s」不在允許詞彙表內（允許：%s）"
                         % (v, "／".join(sorted(PENDING_STATES))))

        for row in self.rep.kill_rows:
            raw = row.get("verdict", "")
            if not strip_md(raw):
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
            head = "### 候選 %d：%s" % (c["ordinal"], c["title"])
            if "evidence" not in c["fields"]:
                self.add("EVID-01", c["line"], head,
                         "候選缺少〈搜尋證據〉欄（也接受「證據」「檢索證據」）")
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
                    self.add("NEIGH-01", c["line"], head, "候選缺少〈最接近的既有研究〉欄")
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
                targets.append((c["line"], "### 候選 %d：%s" % (c["ordinal"], c["title"]),
                                c["cid"], c["ordinal"], c["title"],
                                c["cid"] or ("候選 %d" % c["ordinal"]),
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
            head = "### %s %s" % (fam["fid"], fam["name"])
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
                         "查不到就逐字寫「還沒查到」，不要留白讓讀者以為它免費" % (fam["fid"], label, why))
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
                self.add("LSTAT-01", fam["line"], "### %s %s" % (fam["fid"], fam["name"]),
                         "家族 %s 缺〈狀態〉欄" % fam["fid"])
                continue
            lineno, val = fam["fields"]["status"]
            problem = self._status_problem(val)
            if problem:
                self.add("LSTAT-01", lineno, self.rep.lines[lineno - 1],
                         "家族 %s 的%s" % (fam["fid"], problem))
        for row in self.rep.glance_rows:
            cell = row.get("status", "")
            if not strip_md(cell):
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
                self.add("LWALL-01", fam["line"], "### %s %s" % (fam["fid"], fam["name"]),
                         "家族 %s 沒有〈默默預設〉欄；第六節的牆只能從這一欄長出來，"
                         "缺了它，這份地形圖最後一節就沒有原料" % fam["fid"])
                continue
            lineno, val = fam["fields"]["assumptions"]
            ids = ["F%s-%s" % (m.group(1), m.group(2).lower())
                   for m in LAND_ASSUM_ID_RE.finditer(val)]
            if not ids:
                self.add("LWALL-01", lineno, self.rep.lines[lineno - 1],
                         "家族 %s 的〈默默預設〉沒有可對帳的編號，要寫成「F<n>-a〈…〉；F<n>-b〈…〉」"
                         % fam["fid"])
            for aid in ids:
                declared.append((aid, fam["fid"], lineno))

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
