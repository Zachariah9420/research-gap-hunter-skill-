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

**兩塊東西不從散文讀，改從報告最後的 `rgh-block` 結構化區塊讀**：第一節的預設清單、
與表頭的候選結算四個數字。理由是四輪對抗測試的結果——用正規表達式解析散文，要同時做到
「寬容」（SKILL.md 是散文，模型的措辭會漂）與「絕不靜默」（丟掉一行就是假綠燈）是矛盾的，
每一次修補都只是**移動**那條界線。所以這兩塊改成：

  - **EXACT**：區塊是 JSON，形狀由 schema 強制，壞掉一定大聲（`BLOCK-01`／`ASSUM-01`）。
    結構化資料沒有「寬容」的問題，因為 JSON 沒有形狀變體。
  - **CONTAINMENT**：對散文只問「這個字串有沒有出現」（`ANCHOR-01`）。這個問題**不可能
    靜默丟東西**——答案只有出現或沒出現，而沒出現就是一筆 finding。

區塊裡每一個有散文對應物的欄位都自帶一段**必須逐字出現在散文裡的錨點字串**；區塊因此不是
散文的平行摘要，而是指著散文的索引。containment 的比對跑在**剝掉 HTML 註解之後**的文字上：
少了這一步，藏在註解裡的誘餌就能滿足 containment，而讀者看到的是另一回事。

**這把信任的界線往前移，不是把它移走。** 寫區塊的和寫散文的是同一個模型：一份區塊完全合法、
數字全是編的報告，照樣離開碼 0。錨點出現在否定語境裡（「本研究不採此立場」）也抓不到——
containment 在定義上看不見否定。

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
import unicodedata

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
# rgh-block：報告最後的結構化區塊（SKILL.md〈第 5 步〉的〈rgh-block〉小節）
#
# 只裝兩樣東西：第一節的預設清單、與候選結算的四個數字。其餘一切留在散文，
# 查法一個字都沒變。裝什麼進來的判準是**經濟性**：需要被「算」的（計數、對帳、
# 列舉值、數字大小關係）才進區塊；只需要「有沒有寫」的留在散文，因為那是 containment。
# --------------------------------------------------------------------------

# 圍欄的 info string，**逐字**。用 info string 而不是 HTML 註解，因為註解在
# containment 正規化階段會被剝掉，而區塊必須先被抽出、再被剝除。
BLOCK_FENCE_INFO = "json rgh-block"
BLOCK_SCHEMA_VERSION = "rgh-block/1"

# 頂層恰好三個鍵，不多不少
BLOCK_TOP_KEYS = ("schema", "settlement", "assumptions")
SETTLEMENT_KEYS = ("generated", "survived", "pending", "killed")

# 預設的四種效力。**這是這次重構的核心**：預設的身分從此是一個 JSON 列舉值，
# 不是「預設」那兩個字加一個分隔符——換個寫法（`前提 A1`、引用區塊、破折號分隔）
# 不再讓它從查核裡消失，只會讓它變成一筆違規。
ASSUM_STATUS_VALUES = ("framed", "impression", "inherited", "inherited_framed")
ASSUM_ENTRY_KEYS = ("id", "status", "anchor", "frame", "wall", "families")
# 取樣框十欄，缺一不可、多一個也不行
FRAME_FIELDS = ("N", "query", "limit", "Mp", "pick", "M", "refute_query", "Kp", "K", "sample")

# 編號的形狀。**`[0-9]` 不是 `\d`**：`\d` 在 Python 3 比對整個 Unicode Nd 類別，
# 於是 `{"id": "A１"}`（全形一）通過形狀測試，NFKC 之後錨點又剛好對上散文的 `預設 A1`，
# 而每一個**原字串**比對（反向覆蓋、G3 的 by_id 查表、TRACE-01 的互鎖標籤）全部落空。
# 結果是三筆 finding 指著三行沒有壞的東西，沒有一句提到那個編號。編號是對帳的鍵，
# 鍵就要是逐位元組相同的東西。
BLOCK_AID_RE = re.compile(r"^A[0-9]{1,3}$")
BLOCK_WALL_RE = re.compile(r"^W[0-9]{1,3}$")
BLOCK_FAMILY_RE = re.compile(r"^F[0-9]{1,2}$")

# 反引號圍欄。只認反引號、不認 `~~~`——一個被 `~~~` 包起來當範例展示的區塊，
# 對本檔仍然是「第二個區塊」，而那正是要它變成 BLOCK-01 的那一類（誘餌）。
FENCE_OPEN_RE = re.compile(r"^\s{0,3}(`{3,})\s*([^`]*?)\s*$")

# 結構掃描用的圍欄樣式：反引號與波浪號都認。與上面那一條的差別是**問題不同**——
# 上面問「這是不是那個區塊」（只有一種寫法算），這裡問「這一塊在讀者眼裡是不是程式碼」
# （兩種寫法看起來一樣，所以兩種都算）。見 _find_fences_for_scan。
FENCE_SCAN_OPEN_RE = re.compile(r"^\s{0,3}((?:`{3,})|(?:~{3,}))\s*([^`]*?)\s*$")

# HTML 註解（含跨行）。containment 與禁語掃描都跑在剝掉它之後的文字上。
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)

# 散文裡的預設編號 token。**這不是解析預設行**——它只回答「這一行有沒有提到
# 預設 A<n>」，用在兩個地方：反向覆蓋掃描（散文寫了、區塊沒有），以及第一節的
# 形狀定位。失效方向是假紅燈（一句剛好提到預設 A1 的散文會被算進去），這是刻意的。
PROSE_AID_RE = re.compile(r"預設\s*[Aa](\d{1,3})")


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

# 偵察模式（SKILL.md〈偵察模式〉）。表頭〈模式〉逐字寫「偵察抽樣（非新穎性判定）」，
# 它是**唯一**可以交出空預設清單的缺口報告：那一種明講自己沒有跑第 1 步。
# 這條豁免不是一句宣告就能買到的——見 Checker._recon_declared()。
RECON_MODE_RE = re.compile(r"^模式\s*[：:]\s*偵察抽樣")

# 表頭裡「這一輪是偵察模式」的自我宣告，不限〈模式〉那一行（〈降級聲明〉也算）。
# 只用在〈文獻工具〉的逐字豁免上，見 Checker.tier_verbatim_exempt()——刻意與
# RECON_MODE_RE 分開：那一條買到的是「空預設清單」，這一條買到的只是
# 「階梯表沒有你這一列，所以你自己造句」，兩者的代價差很多，不該共用一個判準。
RECON_SELFDECL_RE = re.compile(r"偵察(?:抽樣|模式)")

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

# 〈狀態〉的合法值。**〔涵蓋不足〕以外每一個都要在同一欄掛上檢索句型**，
# 〔判不出〕也要——那兩段數字就是「儀器分不出來」的證據本身，少了它，
# 這個值會變成一個不必舉證的躲避處。
LAND_STATUS_VALUES = ("飽和", "活躍", "新興", "衰退", "判不出", "涵蓋不足")
LAND_STATUS_EXEMPT = "涵蓋不足"          # 唯一免掛檢索句型的值（它宣告的正是沒有數字可掛）
LAND_STATUS_UNDECIDABLE = "判不出"

# 檢索句型的**兩段子句**（SKILL.md〈證據標準〉）。以前這裡只找「回傳 X 筆」，
# 而規格當時的句型是「回傳 X 筆，其中 <年份> 之後 Y 筆」——那個「其中」宣告
# Y 是 X 的子集，而它不是：X 是索引對這組關鍵字的寬鬆計數，Y 數在相關性排序後
# 真的回給你的那一頁裡，兩者之間沒有子集關係。句型拆成兩段之後，這裡也跟著拆：
# 第一段有兩種形狀（工具回不回報總數），第二段一個字都不變，而第二段的「其中」
# 是真的——N 數在 M 那一頁裡，所以 **N ≤ M 是可查的算術**。
LAND_EV_TOTAL_RE = re.compile(r"寬鬆關鍵字總數\s*(\d+)\s*筆")
LAND_EV_NOTOTAL_RE = re.compile(r"未回傳總數")
LAND_EV_READ_RE = re.compile(r"本次實際讀取回傳的前\s*(\d+)\s*筆")
# 「其中 <年份> 之後 <N> 筆」允許重複出現（同時報兩個切分年，都對同一個 M）
LAND_EV_AFTER_RE = re.compile(r"其中\s*((?:19|20)\d{2})\s*年?之後\s*(\d+)\s*筆")

# 〔判不出〕第二項條件的門檻：那一頁「幾乎全部」落在切分年之後（實務上八成以上）。
# 方向很重要——幾乎全部落在切分年**之前**是〔飽和〕〔衰退〕的證據，不是判不出。
LAND_UNDECIDABLE_RATIO = 0.8

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
# 降級階梯：〈文獻工具〉那一行的合法值（兩種報告共用這一段，各讀自己那一欄）
#
# references/elimination-engine.md〈四、降級階梯〉是這八個字串的唯一出處，
# 而那張表現在**兩個模式各一欄**。以前只有一欄，它的階 0 寫的是
# 「存在性、撤稿、滾雪球均已機器查核」——那三件事是 hunt 的淘汰配備，
# landscape 在定義上不跑（SKILL.md〈證據標準〉的〈不跑〉那一條），於是每一份
# 地形報告的表頭都在逐字宣告三件它被禁止做的檢查，再由內文另寫一段去追認。
# 分欄之後兩邊都逐字照抄、兩邊都是實話，而這裡的契約也跟著變嚴：
# 合法值從「非佔位符」變成「**該欄**那四個字串之一」，**跨欄照抄是一筆違規**。
#
# 階 2 是唯一有變數的一格：`<實際用的工具名>` 由報告自己填，其後的尾巴逐字固定。
# 這也是階與階之間必須看得出差別的理由——階 0 那一格點名 `lit_api.py` 並寫
# 「僅用 search／brief／pick」，階 1／2 寫「無 brief／pick」，階 2 還要填工具名：
# **一份階 2 的報告拿不出階 0 那一格的形狀**，階 2 就讀不成階 0。
#
# 這八個字串是寫死的，但它們不是本檔的私有事實：doc_scan.py 會逐字回查它們
# 在 references/elimination-engine.md 裡真的存在、而且落在正確那一欄。
# 規格改字而這裡沒跟上，是一筆紅燈，不是一個安靜的分歧。
# --------------------------------------------------------------------------

TIER_FIXED = {
    "gap": {
        0: "lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）",
        1: "僅程序沿用 lit-review，未執行機器查核；存在性與撤稿未經驗證",
        3: "本次無法執行淘汰步驟",
    },
    "landscape": {
        0: "lit-review lit_api.py（本模式僅用 search／brief／pick，未執行機器查核）",
        1: "僅程序沿用 lit-review，未執行機器查核；本模式無 brief／pick，"
           "筆數來自實際使用的檢索工具",
        3: "本次無檢索能力，家族與錨定文獻均無工具回傳可依據",
    },
}
# 階 2 那一格：前綴是變數（真的用過的工具名），尾巴逐字固定
TIER2_TAIL = {
    "gap": "；未做撤稿查核，存在性僅單源",
    "landscape": "；本模式無 brief／pick，錨定文獻可能無識別碼",
}
TIER_MODE_LABEL = {"gap": "hunt 缺口獵捕", "landscape": "landscape 領域地形"}


def tier_of(mode, value):
    """〈文獻工具〉的值落在該欄的哪一階；不是那一欄的任何一格就回 None。"""
    v = strip_md(value or "").strip()
    for tier, s in TIER_FIXED[mode].items():
        if v == strip_md(s):
            return tier
    tail = strip_md(TIER2_TAIL[mode])
    if v.endswith(tail) and not is_placeholder(v[:-len(tail)]):
        return 2
    return None


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
# 這個常數是所有「行級」解析共用的，改一個地方就好；以前欄位行、預設行、標題行
# 各自寫死一份前綴，於是修好其中一種形狀不會讓另外兩種跟著修好。
# （原本還有一個 _BULLET，只有預設行的兩個樣式在用；那兩個樣式已經連同它一起刪掉。）
_LEAD = r"\s*(?:>\s*)*"          # 行首空白 ＋ 任意層 blockquote

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

# **第一節的預設行不再被解析。** 以前這裡有兩個樣式：一個把 `預設 A1〔標籤〕：〈一句話〉｜…`
# 拆成編號／標籤／五個數字，一個負責偵測「看起來像預設、卻讀不出來」的行。四輪對抗測試裡
# 有三輪的戰場是它們，唯一一個不必刻意構造就會發生的破口（`前提 A1`／`假設 A1`）也在它們身上。
# 兩個都刪了：預設的身分現在是 `rgh-block` 裡的一個 JSON 欄位，散文那一行只被問
# containment（那句話有沒有出現）。換一種寫法不再讓它從查核裡消失——區塊照樣要求那些字串
# 出現在散文，找不到就是 ANCHOR-01。
#
# 這不是「把界線再移一次」的另一個名字，差別在**失效方向**：解析失敗會靜默丟掉一行，
# containment 失敗只會是一筆 finding。前者是查核器對沒讀過的東西說通過，後者是假紅燈。

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
# 候選的〈缺口類型〉欄裡指名的預設編號（`G3 預設反轉（反轉 A1）`）。**這一條留在散文**：
# 候選不在本次搬進區塊的範圍內，所以「這個 G3 反轉的是誰」還是從候選欄位讀；
# 「那一條有沒有資格被反轉」則改讀區塊的 status（見 check_g3_inputs）。
AREF_RE = re.compile(r"(?<![A-Za-z0-9])[Aa](\d{1,2})(?![0-9])")


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
# rgh-block：抽出、正規化、驗證
# --------------------------------------------------------------------------

def find_fenced_blocks(text):
    """掃出所有反引號圍欄區塊：[{info, body, start, end}]（行號 0-based，含圍欄行）。

    只認反引號、不認 `~~~`。這是刻意的：一個被 `~~~` 包起來「當範例展示」的
    rgh-block，對本檔仍然是文件裡的第二個區塊——而「整份恰好一個」正是關掉
    誘餌那一類的唯一規則，開一個「這只是範例」的例外就等於把它交回去。
    """
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        m = FENCE_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        ticks = len(m.group(1))
        close_re = re.compile(r"^\s{0,3}`{%d,}\s*$" % ticks)
        body, j, closed = [], i + 1, None
        while j < len(lines):
            if close_re.match(lines[j]):
                closed = j
                break
            body.append(lines[j])
            j += 1
        out.append({
            "info": m.group(2).strip(),
            "body": "\n".join(body),
            "start": i,
            "end": closed if closed is not None else len(lines) - 1,
            "closed": closed is not None,
        })
        i = (closed + 1) if closed is not None else len(lines)
    return out


def extract_rgh_blocks(text):
    """(逐字符合圍欄標籤的區塊, 標籤不對但內容像 rgh-block 的區塊)。

    第二項只用來把 BLOCK-01 的訊息講清楚：一個把圍欄寫成 ```json 的作者，
    得到的訊息應該是「標籤要逐字寫 json rgh-block」，不是「這份報告沒有區塊」。
    """
    blocks = find_fenced_blocks(text)
    exact = [b for b in blocks if b["info"] == BLOCK_FENCE_INFO]
    near = []
    for b in blocks:
        if b["info"] == BLOCK_FENCE_INFO or BLOCK_SCHEMA_VERSION not in b["body"]:
            continue
        try:
            data = json.loads(b["body"])
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("schema") == BLOCK_SCHEMA_VERSION:
            near.append(b)
    return exact, near


def _fence_structure_why(line, mode):
    """這一行像不像「報告結構」。回傳一句說明，或 None。

    判準刻意窄，只認**報告自己的**結構：分類得出來的區段標題、候選／家族區塊標題、
    表格列、提到 `預設 A<n>` 的行、以及標籤在別名表裡的欄位行。不認「任何長得像
    markdown 的東西」——圍欄裡本來就常有 `# 這是註解` 與管線符號，把它們一律當成結構
    就是天天假紅燈，而一條天天誤報的規則最後會被關掉，那等於把這塊區域整個交還回去。
    """
    if not line.strip():
        return None
    m = HEADISH_RE.match(line)
    if m:
        title = strip_md(m.group(2).strip())
        classify = classify_landscape_section if mode == "landscape" else classify_section
        if classify(title) != "other":
            return "區段標題「%s」" % title[:30]
        if CAND_HEAD_RE.match(title):
            return "候選區塊的標題「%s」" % title[:30]
        if mode == "landscape" and LAND_FAMILY_HEAD_RE.match(title):
            return "家族區塊的標題「%s」" % title[:30]
        return None
    if ROWISH_RE.match(line) and len(re.findall(r"[|｜]", line)) >= 2:
        return "表格列"
    if PROSE_AID_RE.search(strip_md(line)):
        return "第一節的預設行（提到「預設 A<n>」）"
    fm = FIELD_LINE_RE.match(line)
    if fm:
        key = norm_key(fm.group(1))
        for aliases in (LABEL_ALIASES, LAND_LABEL_ALIASES):
            for names in aliases.values():
                if any(norm_key(a) == key for a in names if norm_key(a)):
                    return "欄位行〈%s〉" % strip_md(fm.group(1)).strip()[:20]
    return None


def _find_fences_for_scan(lines):
    """掃出所有圍欄區塊，**反引號與波浪號都算**。只給結構掃描用。

    `find_fenced_blocks` 只認反引號，那是刻意的，理由寫在它自己的 docstring 裡：
    `BLOCK-01` 的「整份恰好一個」不能因為換一種圍欄符號就被繞開，所以一個被 `~~~`
    包起來當範例展示的 rgh-block，對那個函式仍然是第二個區塊。

    這裡問的是**另一個問題**：有沒有一塊區域，讀者看到的是程式碼。`~~~` 在讀者眼裡
    與 ``` 一模一樣，所以只認一種就是留一個一字元的繞道——而這條規則存在的理由，
    正是「兩邊都不算的區域什麼都裝得下」。
    """
    out = []
    i = 0
    while i < len(lines):
        m = FENCE_SCAN_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        marks = m.group(1)
        close_re = re.compile(r"^\s{0,3}%s{%d,}\s*$" % (re.escape(marks[0]), len(marks)))
        body, j, closed = [], i + 1, None
        while j < len(lines):
            if close_re.match(lines[j]):
                closed = j
                break
            body.append(lines[j])
            j += 1
        out.append({"char": marks[0], "info": m.group(2).strip(), "body": "\n".join(body),
                    "start": i, "end": closed if closed is not None else len(lines) - 1})
        i = (closed + 1) if closed is not None else len(lines)
    return out


def scan_fences_for_structure(lines, mode):
    """圍欄區塊裡不得藏報告結構。回傳 [dict(line, text, why, info, hits)]。

    **這一條守的是「查核器不讀的地方」，不是「報告寫錯了什麼」。** 一個圍欄區塊在
    讀者眼裡是程式碼，在查核器眼裡則視情況：地形報告的 `rgh-block` 圍欄以前兩邊都不算
    ——不被驗證、也不被掃描——於是它是文件裡一塊沒有人讀的地方，而沒有人讀的地方
    只要夠大就什麼都裝得下。這一條把它變成一句話：**凡是我不打算讀的區域，
    裡面若有東西長得像報告結構，就要說出來。**

    逐字符合圍欄標籤的 `rgh-block` 是唯一的例外，**兩種模式都例外，但理由不同**：
    缺口報告裡它被讀了（`validate_block` 逐欄驗證），內容歸 `BLOCK-01` 管；
    地形報告裡它整個不該存在，`LandscapeChecker.check_stray_block` 已經指著那一行說了，
    再對它的內容多說一句只會把一個缺陷變成兩句話。要緊的是那個區域**不再靜默**：
    模式判別移到剝除之前以後，地形報告的區塊內容照樣進 LANG-01 與 LVOCAB-01 的掃描。
    """
    out = []
    for b in _find_fences_for_scan(lines):
        # 例外只給**反引號寫的**逐字圍欄標籤：`~~~json rgh-block` 不是 rgh-block
        # （`find_fenced_blocks` 不認它），所以它沒有「已經被驗過」這個豁免理由。
        if b["char"] == "`" and b["info"] == BLOCK_FENCE_INFO:
            continue
        hits = []
        for off, ln in enumerate(b["body"].splitlines()):
            why = _fence_structure_why(ln, mode)
            if why:
                hits.append((b["start"] + 1 + off, ln, why))
        if hits:
            lineno, raw, why = hits[0]
            out.append({"line": lineno + 1, "text": raw, "why": why,
                        "info": b["info"], "hits": len(hits),
                        "char": b["char"] * 3,   # 訊息要叫作者去找他真的寫的那三個字元
                        "fence_line": b["start"] + 1})
    return out


def blank_html_comments(text):
    """把 HTML 註解的內容換成空白，但保留換行——行號因此不動。"""
    if "<!--" not in text:
        return text
    chars = list(text)
    for m in HTML_COMMENT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def normalize_for_containment(s):
    """containment 比對用的正規化。**兩邊做同一套，順序寫死在這裡。**

    1. （呼叫端先做）移除 rgh-block 區塊本身
    2. 移除 HTML 註解——**這一步是強制的**。少了它，一段藏在註解裡的誘餌就能
       滿足 containment，而讀者在畫面上看到的是另一句話；那正是先前那個結算誘餌
       的機制，把它留下來等於換一個地方重演一次。
    3. NFKC（＝→=、＋→+、｜→|、，→,、（）→()）
    4. 去掉 markdown 強調與反引號
    5. 空白摺疊成單一空格
    6. 去掉逗號兩側的空白（`pick 索引 0, 2, 3` 與 `0,2,3` 要相等）
    7. casefold（英文查詢詞的大小寫不該決定紅綠）

    正規化在這裡是安全的：每一步都**兩邊都做**，而且只會讓「找得到」更容易。
    它的失效方向是假紅燈，不是假綠燈。
    """
    s = HTML_COMMENT_RE.sub(" ", s)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[*_`]", "", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*,\s*", ",", s)
    return s.casefold()


def _is_int(v):
    """JSON 的 true/false 在 Python 裡是 int 的子類，不能算數字。"""
    return isinstance(v, int) and not isinstance(v, bool)


def _wide_digit_note(value):
    """編號裡有非 ASCII 數字時的補充句；沒有就回空字串。

    存在的理由是**訊息要落在壞掉的那個東西上**。全形數字寫的 `A１` 形狀不合，
    而它接下來造成的三筆 finding（散文有 `預設 A1` 區塊卻沒有、G3 指到不存在的 A1、
    第六節缺 `第1步-推翻A１` 對應列）全部指著沒有壞的行——因為 NFKC 只發生在
    containment 那一側，原字串比對兩邊仍然不同。多這一句，作者才知道要改的是那一位數字。
    """
    if not isinstance(value, str):
        return ""
    bad = sorted(set(c for c in value if c.isdigit() and not ("0" <= c <= "9")))
    if not bad:
        return ""
    return ("——注意「%s」不是半形阿拉伯數字（是 Unicode 的數字類別，NFKC 之後才會變成 "
            "0-9）。編號是二／三／四節與第六節對帳的鍵，鍵一律用半形數字寫"
            % "".join(bad))


def _frame_problems(frame):
    """取樣框十欄的形狀與算術。回傳 [(欄位路徑, 訊息)]，空 list 代表沒問題。"""
    out = []
    if not isinstance(frame, dict):
        return [("frame", "`frame` 必須是物件（十個欄位），收到 %s" % type(frame).__name__)]
    missing = [k for k in FRAME_FIELDS if k not in frame]
    extra = [k for k in frame if k not in FRAME_FIELDS]
    if missing:
        out.append(("frame", "`frame` 少了欄位：%s（十欄缺一不可）" % "、".join(missing)))
    if extra:
        out.append(("frame", "`frame` 有規格外的欄位：%s" % "、".join(sorted(extra))))

    def num(key, low):
        v = frame.get(key)
        if key in missing:
            return None
        if not _is_int(v):
            out.append(("frame.%s" % key, "`%s` 必須是整數，收到 %r" % (key, v)))
            return None
        if v < low:
            out.append(("frame.%s" % key, "`%s` 必須 ≥ %d，收到 %d" % (key, low, v)))
            return None
        return v

    def text(key):
        v = frame.get(key)
        if key in missing:
            return None
        if not isinstance(v, str) or not v.strip():
            out.append(("frame.%s" % key, "`%s` 必須是非空字串，收到 %r" % (key, v)))
            return None
        if is_placeholder(v):
            out.append(("frame.%s" % key, "`%s` 是佔位符（「%s」）——查詢詞要逐字寫出，"
                                          "使用者要能複製重跑" % (key, v.strip())))
            return None
        return v

    # N 與 M′ 之間**沒有**大小關係，這裡刻意不比：N 是 `brief` 的標題層行數，
    # M′ 是真的 `pick` 出來讀過摘要的篇數，SKILL.md 第 1 步逐字寫著「N 不是 M 的分母」。
    num("N", 1)
    text("query")
    num("limit", 1)
    # M′ < 3 的預設只能是 impression：這是 SKILL.md 第 1 步的門檻，不是風格偏好
    mp = frame.get("Mp")
    if "Mp" not in missing:
        if not _is_int(mp):
            out.append(("frame.Mp", "`Mp` 必須是整數，收到 %r" % (mp,)))
            mp = None
        elif mp < 3:
            out.append(("frame.Mp", "摘要層精讀只有 %d 篇（M′ < 3）——這樣的預設只能寫成 "
                                    "`\"status\": \"impression\"`，而印象級預設不得作為 G3 輸入" % mp))
            mp = None
    else:
        mp = None
    pick = frame.get("pick")
    if "pick" not in missing:
        if not isinstance(pick, list) or not all(_is_int(x) and x >= 0 for x in pick):
            out.append(("frame.pick", "`pick` 必須是非負整數的陣列，收到 %r" % (pick,)))
            pick = None
        elif len(set(pick)) != len(pick):
            out.append(("frame.pick", "`pick` 有重複的索引：%r" % (pick,)))
            pick = None
        elif mp is not None and len(pick) != mp:
            out.append(("frame.pick", "`pick` 列了 %d 個索引，`Mp` 卻是 %d——"
                                      "pick 出來的就是讀過摘要的那幾篇，兩者必須相等"
                        % (len(pick), mp)))
    m = num("M", 0)
    if m is not None and mp is not None and m > mp:
        out.append(("frame.M", "沿用篇數 M=%d 大於摘要層精讀 M′=%d——沿用只能在讀過摘要的樣本裡數"
                    % (m, mp)))
    text("refute_query")
    kp = num("Kp", 0)
    k = num("K", 0)
    if k is not None and kp is not None and k > kp:
        out.append(("frame.K", "推翻性檢索讀後 K=%d 大於回傳 K′=%d" % (k, kp)))
    v = frame.get("sample")
    if "sample" not in missing and (not isinstance(v, str) or not v.strip()):
        out.append(("frame.sample", "`sample` 必須是非空字串（年份範圍＋索引名），收到 %r" % (v,)))
    return out


def validate_block(data):
    """驗證整個區塊。回傳 [(check_id, 定位用的字串, 訊息)]。

    **結構化資料沒有「寬容」的問題**：JSON 沒有形狀變體，所以這裡一律 EXACT，
    不符就是一筆大聲的 finding。定位字串是給呼叫端拿去在區塊內文裡找行號用的。

    分工：`BLOCK-01` 管載體與結算（整份區塊的形狀、schema 版本、四個數字的算術），
    `ASSUM-01` 管 `assumptions[]` 的每一條。分兩個 id 是為了訊息會落在對的地方——
    一個作者看到 ASSUM-01 要去改 A2 那一條，看到 BLOCK-01 要去改整個區塊。
    """
    out = []
    if not isinstance(data, dict):
        return [("BLOCK-01", None, "區塊的最外層必須是一個 JSON 物件，收到 %s" % type(data).__name__)]

    declared = data.get("schema")
    if declared != BLOCK_SCHEMA_VERSION:
        out.append(("BLOCK-01", "\"schema\"",
                    "這份報告宣告的 schema 版本是 %r，本查核器認得的是 %r"
                    % (declared, BLOCK_SCHEMA_VERSION)))
    missing = [k for k in BLOCK_TOP_KEYS if k not in data]
    extra = [k for k in data if k not in BLOCK_TOP_KEYS]
    if missing:
        out.append(("BLOCK-01", None, "區塊少了必填的頂層欄位：%s" % "、".join(missing)))
    if extra:
        out.append(("BLOCK-01", None,
                    "區塊有規格外的頂層欄位：%s。頂層恰好三個鍵（%s）——多裝東西進來，"
                    "區塊就開始變成第二份報告，而它只該是「需要被算的那兩樣」的機器可讀副本"
                    % ("、".join(sorted(extra)), "、".join(BLOCK_TOP_KEYS))))

    st = data.get("settlement")
    if "settlement" in data:
        if not isinstance(st, dict):
            out.append(("BLOCK-01", "\"settlement\"",
                        "`settlement` 必須是物件（四個整數），收到 %s" % type(st).__name__))
        else:
            miss = [k for k in SETTLEMENT_KEYS if k not in st]
            more = [k for k in st if k not in SETTLEMENT_KEYS]
            if miss:
                out.append(("BLOCK-01", "\"settlement\"",
                            "`settlement` 少了欄位：%s" % "、".join(miss)))
            if more:
                out.append(("BLOCK-01", "\"settlement\"",
                            "`settlement` 有規格外的欄位：%s" % "、".join(sorted(more))))
            bad = [k for k in SETTLEMENT_KEYS if k in st and not (_is_int(st[k]) and st[k] >= 0)]
            for k in bad:
                out.append(("BLOCK-01", "\"settlement\"",
                            "`settlement.%s` 必須是 ≥ 0 的整數，收到 %r" % (k, st[k])))
            if not miss and not bad:
                g, s, p, q = (st[k] for k in SETTLEMENT_KEYS)
                if g != s + p + q:
                    out.append(("BLOCK-01", "\"settlement\"",
                                "候選結算對不起來：生成 %d ≠ 存活 %d ＋ 待確認 %d ＋ 已淘汰 %d（＝%d），"
                                "差額就是被靜默丟掉的候選" % (g, s, p, q, s + p + q)))

    ass = data.get("assumptions")
    if "assumptions" in data:
        if not isinstance(ass, list):
            out.append(("BLOCK-01", "\"assumptions\"",
                        "`assumptions` 必須是陣列（可以是空的），收到 %s" % type(ass).__name__))
        else:
            seen = set()
            for idx, e in enumerate(ass):
                out.extend(_validate_assumption(idx, e, seen))
    return out


def _validate_assumption(idx, e, seen):
    """`assumptions[]` 的一條。回傳 [(check_id, 定位字串, 訊息)]，一律 ASSUM-01。"""
    where = "assumptions[%d]" % idx
    if not isinstance(e, dict):
        return [("ASSUM-01", None, "%s 必須是物件，收到 %s" % (where, type(e).__name__))]
    aid = e.get("id")
    loc = ("\"id\": \"%s\"" % aid) if isinstance(aid, str) else None
    out = []
    if not isinstance(aid, str) or not BLOCK_AID_RE.match(aid):
        out.append(("ASSUM-01", loc, "%s 的 `id` 要寫成 `A` 加數字（A1…A999），收到 %r%s"
                    % (where, aid, _wide_digit_note(aid))))
    elif aid in seen:
        out.append(("ASSUM-01", loc, "預設編號 %s 在區塊裡出現不只一次——編號是第 3 步 G3 與"
                                     "第六節推翻性檢索的對帳依據，重複就對不了帳" % aid))
    else:
        seen.add(aid)
    name = aid if isinstance(aid, str) else where

    more = [k for k in e if k not in ASSUM_ENTRY_KEYS]
    if more:
        out.append(("ASSUM-01", loc, "%s 有規格外的欄位：%s" % (name, "、".join(sorted(more)))))

    status = e.get("status")
    status_ok = isinstance(status, str) and status in ASSUM_STATUS_VALUES
    if not status_ok:
        out.append(("ASSUM-01", loc,
                    "%s 的 `status` 是 %r，不在四個列舉值內（%s）。這一欄是預設的**效力**："
                    "framed 與 inherited_framed 可以當 G3 輸入、要有第六節的推翻性檢索列；"
                    "impression 與 inherited 不行、也免附紀錄"
                    % (name, status, "／".join(ASSUM_STATUS_VALUES))))

    anchor = e.get("anchor")
    if not isinstance(anchor, str) or not anchor.strip():
        out.append(("ASSUM-01", loc, "%s 的 `anchor` 必須是非空字串（那條預設的一句話，不含〈〉），"
                                     "收到 %r" % (name, anchor)))

    if "frame" not in e:
        out.append(("ASSUM-01", loc, "%s 少了 `frame` 欄位——它一律要在，沒有取樣框就寫 `null`，"
                                     "「沒寫」與「明講沒有」不是同一件事" % name))
    elif status_ok:
        frame = e.get("frame")
        if status in ("framed", "inherited_framed"):
            if frame is None:
                out.append(("ASSUM-01", loc,
                            "%s 的 `status` 是 %s，`frame` 卻是 null——宣稱跑完（或補完）取樣框，"
                            "就要與本輪量化的預設同標準：十個欄位齊全。做不到就把 status 改成 %s"
                            % (name, status,
                               "impression" if status == "framed" else "inherited")))
            else:
                for path, msg in _frame_problems(frame):
                    out.append(("ASSUM-01", loc, "%s 的 %s" % (name, msg)))
        elif frame is not None:
            out.append(("ASSUM-01", loc,
                        "%s 的 `status` 是 %s，`frame` 必須是 null——地形模式在定義上沒有跑過 "
                        "N／M′／M／K′／K，印象級預設也沒有；填一組數字進去就是把沒跑過的搜尋寫出來"
                        % (name, status)))

    inherited = status in ("inherited", "inherited_framed")
    wall = e.get("wall")
    if inherited:
        if not isinstance(wall, str) or not BLOCK_WALL_RE.match(wall or ""):
            out.append(("ASSUM-01", loc, "%s 承接自地形報告，`wall` 要寫成 `W` 加數字，收到 %r%s"
                        % (name, wall, _wide_digit_note(wall))))
    elif "wall" in e and status_ok:
        out.append(("ASSUM-01", loc, "%s 不是承接來的（status=%s），不該有 `wall`" % (name, status)))

    fams = e.get("families")
    if status == "inherited":
        # 只有 inherited 必填：inherited_framed 的散文標籤是〔承接自地形 W…，已補取樣框〕，
        # 照 SKILL.md 第 1 步的規格本來就不列家族，要求它就是一天到晚的假紅燈。
        if not isinstance(fams, list) or not fams:
            out.append(("ASSUM-01", loc, "%s 是承接未補框的預設，`families` 必填（至少一個 "
                                         "`F` 加數字），收到 %r" % (name, fams)))
        elif not all(isinstance(f, str) and BLOCK_FAMILY_RE.match(f) for f in fams):
            out.append(("ASSUM-01", loc, "%s 的 `families` 要全部是 `F` 加數字，收到 %r%s"
                        % (name, fams,
                           _wide_digit_note("".join(f for f in fams if isinstance(f, str))))))
        elif len(set(fams)) != len(fams):
            out.append(("ASSUM-01", loc, "%s 的 `families` 有重複：%r" % (name, fams)))
    elif "families" in e and status_ok:
        if status == "inherited_framed":
            if not isinstance(fams, list) or not fams or not all(
                    isinstance(f, str) and BLOCK_FAMILY_RE.match(f) for f in fams):
                out.append(("ASSUM-01", loc, "%s 的 `families` 寫了就要是 `F` 加數字的非空陣列，"
                                             "收到 %r" % (name, fams)))
        else:
            out.append(("ASSUM-01", loc, "%s 不是承接來的（status=%s），不該有 `families`"
                        % (name, status)))
    return out


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
        self.pending_rows = []          # dict(cells{col:value}, line)
        self.kill_rows = []             # dict(cells{col:value}, line)
        self.trace_rows = []            # dict(cells{col:value}, line)
        self.no_search_declared = False
        self.report_blocks = 0
        # ---- rgh-block（結構化區塊）------------------------------------
        # 從**原始檔案文字**抽出，在 report-start／report-end 開窗之前——否則標記
        # 就能把區塊藏起來，而那時的 BLOCK-01 訊息會是錯的（說「沒有區塊」，
        # 其實是「區塊被標記排除了」）。
        self.raw_blocks = []            # 圍欄標籤逐字符合的區塊
        self.near_blocks = []           # 標籤不對、內容卻像 rgh-block 的區塊
        self.block = None               # json.loads 之後的 dict（解析失敗時 None）
        self.block_error = None         # (lineno, colno, msg)
        self.block_line = 1             # 區塊圍欄的行號（findings 的錨點）
        self.settlement = None          # (生成, 存活, 待確認, 已淘汰)，來自區塊
        self.settlement_ok = False      # 四個數字齊全且算術成立才是 True
        self.assumptions = []           # 區塊裡形狀合法的預設條目（dict）
        self.assumptions_ok = False     # `assumptions` 存在而且是一個陣列
        # 區塊**試圖**宣告的每一個編號，含形狀不合法的那些。用途只有一個：閉嘴。
        # ASSUM-01 已經指著那一條說它壞了，反向掃描若再說一次「區塊裡沒有這一條」，
        # 就是把讀者送去補一個已經在那裡的東西——正是這支查核器一路在刪的那句話。
        self.block_declared_ids = set()
        self.prose = ""                 # 剝掉區塊之後的散文（未正規化）
        self.prose_norm = ""            # containment 比對用的正規化散文
        self.prose_lines_norm = []      # 同一套正規化，但**逐行**——行內共現要靠它問
        self.scan_lines = []            # 禁語掃描用：剝區塊與 HTML 註解，行號對齊 lines
        # 讀不進來的東西。解析器可以寬容，但不可以安靜：凡是「看起來是報告的一部分、
        # 卻沒被讀進任何結構」的行，都堆在這裡，由 PARSE-01 回報。
        self.table_strays = []          # dict(line, text, why)：表格列讀不到／欄數不符
        self.head_strays = []           # dict(line, text, why)：候選或家族標題讀不到
        # 圍欄區塊裡長得像報告結構的東西。圍欄在讀者眼裡是程式碼，所以報告結構躲進去
        # 就有機會兩邊落空（查核器不當它是結構、讀者不當它是內容）——說出來就好。
        self.fence_strays = []          # dict(line, text, why, info, hits, fence_line)
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
    # 第一節靠「裡面有沒有提到預設 A<n>」認。這是一個 **token 掃描**，不是預設行的
    # 解析——它不決定任何一條預設的內容，只回答「這一節是哪一節」。失效方向是假紅燈
    # （一段剛好提到預設 A1 的散文會讓那一節被歸成第一節，於是 SECT-01 誤報）。
    for j in range(s["start"], s["end"]):
        if PROSE_AID_RE.search(strip_md(rep.lines[j])):
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
    # 區塊先抽，而且是從**原始文字**抽——在 report-start／report-end 開窗之前。
    # 反過來的話，兩個標記就能把區塊排除掉，而 BLOCK-01 雖然照樣會響，訊息卻是錯的。
    rep.raw_blocks, rep.near_blocks = extract_rgh_blocks(text)
    text, rep.report_blocks = apply_report_blocks(text)
    rep.lines = text.splitlines()
    lines = rep.lines

    heads = scan_heads(lines)
    first_h2 = next((h["line0"] for h in heads if h["level"] == 2), len(lines))
    rep.header_lines = [(i + 1, lines[i]) for i in range(0, first_h2)]
    # **型別要先判、再決定散文扣掉什麼。** 剝掉 rgh-block 的理由是「它已經被讀過了」
    # （`validate_block` 逐欄驗證，而它合法地含有判定詞彙），那個理由只在缺口報告成立。
    # 以前這一段寫在 detect_mode 之前，於是地形報告裡的一個 `json rgh-block` 圍欄
    # 同時滿足兩件事：LandscapeChecker 從不驗它，而它又被剝出散文與禁語掃描——
    # 一塊沒有人讀的區域。evals/README 說 LVOCAB-01 不能有 mention／use 豁免，
    # 「因為那會是吞掉它的那個洞」；那正是這裡不小心開出來的一個。
    rep.mode = detect_mode(lines, first_h2)

    # 散文＝開窗之後的文字，缺口報告再扣掉區塊本身。containment 與禁語掃描跑在這上面。
    prose_lines = list(lines)
    if rep.mode == "gap":
        for b in rep.raw_blocks:
            for i in range(b["start"], min(b["end"] + 1, len(prose_lines))):
                prose_lines[i] = ""
    rep.prose = "\n".join(prose_lines)
    rep.prose_norm = normalize_for_containment(rep.prose)
    rep.prose_lines_norm = [normalize_for_containment(ln) for ln in prose_lines]
    # 禁語掃描要逐行報行號，所以另存一份「剝過註解、行號仍然對得上」的副本。
    rep.scan_lines = blank_html_comments(rep.prose).splitlines()
    if len(rep.scan_lines) < len(lines):
        rep.scan_lines += [""] * (len(lines) - len(rep.scan_lines))

    # 圍欄裡不得藏報告結構（兩種模式共用；缺口報告已驗過的那個區塊除外）。
    rep.fence_strays = scan_fences_for_structure(lines, rep.mode)

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

    # 候選結算與第二節標題的四個數字**不再從散文讀**：它們的唯一來源是區塊
    # （Checker.check_block 填 rep.settlement），散文那兩行改由 ANCHOR-01 比對。
    # 以前這裡是「全文第一個 match 就 break」，於是檔首一行 HTML 註解裡的假結算
    # 就能搶走整條對帳，而讀者在畫面上看不到那一行。
    if rep.raw_blocks:
        rep.block_line = rep.raw_blocks[0]["start"] + 1

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

    # 第一節的預設**不在這裡解析**——它的唯一來源是 rgh-block，由
    # Checker.check_block() 驗證後填進 rep.assumptions。散文那幾行只會被問
    # containment（ANCHOR-01）：區塊寫的那句話、那五段數字，散文裡找不找得到。
    return rep


# --------------------------------------------------------------------------
# 查核
# --------------------------------------------------------------------------

CHECK_DESCRIPTIONS = {
    "BLOCK-01": "缺口報告最後必須恰好有一個 `json rgh-block` 圍欄區塊，內容是合法 JSON、"
                "schema 版本認得、頂層恰好三個鍵，候選結算滿足 生成 ＝ 存活 ＋ 待確認 ＋ 已淘汰，"
                "且 `assumptions` 非空（只有偵察模式可以交空清單，見規則訊息）。"
                "沒有區塊就是第一節與結算完全沒有被查過，而沒有被查過不能長得像通過。"
                "反過來，**地形報告不寫區塊**：那裡出現一個區塊，就是一塊沒有任何規則會驗的區域",
    "ANCHOR-01": "區塊裡每一段有散文對應物的字串，都必須逐字出現在**剝掉 HTML 註解之後**的散文裡，"
                 "而且綁在某一條預設上的那些要出現在**寫著「預設 A<n>」的那一行上**、"
                 "那一行不得只落在別的區段裡；效力標籤反過來也不得掛在 status 對不上的預設行上。"
                 "反向，散文裡每一個 `預設 A<n>` 也都要在區塊裡有一條。"
                 "這是 containment，不是解析：答案只有出現或沒出現，沒有「靜默丟掉」這個選項",
    "PARSE-01": "看起來是報告結構的一部分、卻讀不進來的行、列或表，一律回報："
                "表格列沒被讀進表（blockquote／全形直線／漏了行首直線／表格中間插了非表格的一行）、"
                "欄數與表頭不符、候選或家族的標題認不出來、一整張該在那裡卻讀不到的表，"
                "以及**藏在圍欄區塊裡的報告結構**（圍欄在讀者眼裡是程式碼，"
                "查核器也不保證讀它——兩邊都不算的區域什麼都裝得下）",
    "SECT-01": "區段標題不得改寫（SKILL.md〈輸出格式〉：「區段標題與欄位標籤不得改寫」）。"
               "標題認不出來的區段一律改以內容定位、底下的規則照常執行，"
               "但標題本身是一條違規——不是停止檢查的理由",
    "STRUCT-01": "報告必須有〈存活候選〉〈待確認〉〈已淘汰〉〈檢索紀錄〉四個區段",
    "STRUCT-02": "表頭必須宣告文獻工具階層（第 0/1/2/3 階），而且逐字等於降級階梯表中"
                 "**本報告型別那一欄**的那一格（階 2 只有 `<實際用的工具名>` 是變數）；"
                 "跨欄照抄（地形報告寫 hunt 欄、缺口報告寫 landscape 欄）是一筆違規",
    "COUNT-01": "區塊結算的〈存活〉必須等於第二節實際寫出來的候選區塊數"
                "（數字來自區塊、列數來自散文，這是一次真的交叉比對）",
    "RECON-01": "區塊結算的〈待確認〉〈已淘汰〉必須等於第三、四節的實際列數，"
                "且每個候選編號只在二／三／四其中一節出現一次",
    "VERDICT-01": "判定／暫定狀態必須是該區段允許的值",
    "VERDICT-02": "存活候選只能是 ADJACENT／OPEN／INCREMENTAL",
    "ASSUM-01": "區塊 `assumptions[]` 的每一條：`id` 是 A 加數字且不重複、`status` 是四個列舉值之一"
                "（framed／impression／inherited／inherited_framed）、`anchor` 非空、"
                "`frame` 在 framed／inherited_framed 必填十欄（Mp ≥ 3、len(pick) = Mp、M ≤ Mp、K ≤ Kp）"
                "其餘必須是 null、`wall` 在承接時必填、`families` 在承接未補框時必填",
    "ASSUM-02": "區塊 `status` 是 impression 或 inherited（承接未補框）的預設，不得成為 G3 候選的輸入",
    "EVID-01": "每個存活候選都要有搜尋證據欄",
    "EVID-02": "搜尋證據欄不得為空或佔位符",
    "EVID-03": "搜尋證據欄必須含至少一個具體查詢詞",
    "NEIGH-01": "最接近的既有研究欄要存在；若指名了文獻就要帶識別碼",
    "KILL-01": "每一個淘汰列都必須指名關鍵文獻",
    "KILL-02": "CROWDED 必須指名 ≥3 篇",
    "KILL-03": "DONE 的淘汰原因必須含摘要逐字引句",
    "ID-01": "被指名的關鍵文獻必須帶識別碼（DOI／arXiv／S2）",
    "TRACE-01": "二／三／四節的每個候選、以及區塊裡 status 是 framed／inherited_framed 的每一條預設"
                "（`第1步-推翻A<n>`），都要在〈檢索紀錄〉有對應列"
                "（例外：三、待確認裡〔未驗證〕、卡在術語的〔UNSEARCHABLE〕，"
                "以及 status 是 impression／inherited 的預設）",
    "TRACE-02": "〈檢索紀錄〉的查詢詞不得為佔位符",
    "LANG-01": "不得斷言「不存在／沒有人做過」，只能寫「這次搜尋沒有回傳」",
    "TIER-01": "宣告未執行檢索時不得填寫任何新穎性判定或淘汰判定",
    # ---- 以下五條只作用在領域地形報告（landscape）------------------------
    "LHEAD-01": "地形報告的表頭要宣告〈模式〉是領域地形，並逐字帶〈這份報告不做什麼〉那一行",
    "LVOCAB-01": "地形報告不得出現新穎性判定詞彙（ADJACENT／OPEN／INCREMENTAL／DONE／CROWDED）",
    "LCOST-01": "每個家族都要同時寫出〈買到什麼〉與〈付出什麼〉，查不到就寫「還沒查到」，不得留白或佔位符",
    "LSTAT-01": "〈狀態〉必須是六個合法值之一（飽和／活躍／新興／衰退／判不出／涵蓋不足）；"
                "除〔涵蓋不足〕外都要在同一欄掛上**兩段子句**的檢索句型，"
                "而第二段的 N ≤ M；〔判不出〕另外要滿足它自己的方向與多數條件",
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
        for s in self.rep.fence_strays:
            self.add("PARSE-01", s["line"], s["text"],
                     "這一行在一個圍欄區塊裡（第 %d 行開的 %s%s），內容卻是%s"
                     "%s。圍欄在讀者眼裡是程式碼、不是報告內容，"
                     "查核器也不保證會把它當成報告結構讀——**兩邊都不算的區域，"
                     "就是什麼都裝得下的區域**。報告結構請寫在圍欄外面；"
                     "真的要展示一段範例，就把它放進 report-start／report-end 之外"
                     % (s["fence_line"], s.get("char", "```"),
                        s["info"] or "（無標籤）", s["why"],
                        ("，同一個圍欄裡另有 %d 行同類" % (s["hits"] - 1)) if s["hits"] > 1 else ""))
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
    def tier_verbatim_exempt(self):
        """這一份報告可不可以不逐字照抄階梯表。預設一份都不行。"""
        return False

    def check_tool_tier(self):
        header_text = "\n".join(t for _, t in self.rep.header_lines)
        if not re.search(r"文獻工具", header_text):
            self.add("STRUCT-02", 1, "", "表頭缺少「**文獻工具**：…」宣告，無法判斷這份報告的查核階層")
            return
        mode = self.rep.mode if self.rep.mode in TIER_FIXED else "gap"
        other = "landscape" if mode == "gap" else "gap"
        for lineno, t in self.rep.header_lines:
            if "文獻工具" in t:
                val = t.split("：", 1)[-1] if "：" in t else t.split(":", 1)[-1]
                # 唯一的判定條件是「逐字等於這一欄的某一格」。底下三個分支只決定
                # **訊息**，不決定要不要開火——佔位符與跨欄照抄都是同一件事的兩種形狀
                # （都不是那一欄的四個字串之一），分開寫是為了把作者送到對的地方。
                if tier_of(mode, val) is not None:
                    break
                cross = tier_of(other, val)
                if is_placeholder(val):
                    self.add("STRUCT-02", lineno, t,
                             "「文獻工具」宣告是空的或佔位符。這一行的值必須逐字等於"
                             "降級階梯表「%s」那一欄、本次實際落到那一階的那一格"
                             % TIER_MODE_LABEL[mode])
                elif cross is not None:
                    self.add(
                        "STRUCT-02", lineno, t,
                        "〈文獻工具〉照抄的是降級階梯表**另一欄**（%s）的階 %s 字串。"
                        "這一份是%s，合法值只有那一欄的四個字串——"
                        "同一個字串在一邊是實話、在另一邊是假話，"
                        "這正是那張表要分兩欄的理由。應為：%s"
                        % (TIER_MODE_LABEL[other], cross, TIER_MODE_LABEL[mode],
                           TIER_FIXED[mode].get(cross)
                           or ("<實際用的工具名>" + TIER2_TAIL[mode])))
                elif not self.tier_verbatim_exempt():
                    self.add(
                        "STRUCT-02", lineno, t,
                        "〈文獻工具〉不是降級階梯表「%s」那一欄的四個字串之一"
                        "（references/elimination-engine.md〈四、降級階梯〉是這一行的唯一出處，"
                        "本次落到哪一階就逐字照抄那一格，不要另外造句）。"
                        "階 2 是唯一要自己填的一格，形狀是「<實際用的工具名>%s」"
                        % (TIER_MODE_LABEL[mode], TIER2_TAIL[mode]))
                break

    # ---- 措辭（兩種報告都適用）--------------------------------------------
    def lang_exempt(self, line):
        """規格要求這個模式逐字寫出、因此不受 LANG-01 管的整行。預設一行都沒有。"""
        return False

    def check_language(self):
        """禁語掃描跑在 **scan_lines** 上：剝掉 HTML 註解、剝掉 rgh-block 區塊本身。

        剝註解是 containment 正規化的第 2 步，這裡沿用同一條管線（行號仍對得上原檔）。
        剝區塊是因為**區塊不是散文**：hunt 的區塊合法地含有判定詞彙，而 LVOCAB-01
        在地形模式禁的正是那些字——把區塊算成散文，一個模式會誤放、另一個會誤殺。
        """
        for i, ln in enumerate(self.rep.lines):
            scan = self.rep.scan_lines[i] if i < len(self.rep.scan_lines) else ln
            if not scan.strip():
                continue
            if ASSERTIVE_GUARD.search(scan):
                continue
            if self.lang_exempt(scan):
                continue
            for pat, label in ASSERTIVE_PATTERNS:
                m = re.search(pat, scan)
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

    # ---- rgh-block：載體與結算（EXACT）------------------------------------
    def _block_line(self, needle):
        """把區塊內文裡的一段字對回檔案行號。找不到就退回圍欄那一行。"""
        b = self.rep.raw_blocks[0] if self.rep.raw_blocks else None
        if b is None or not needle:
            return self.rep.block_line
        for off, ln in enumerate(b["body"].splitlines()):
            if needle in ln:
                return b["start"] + 2 + off      # +1 圍欄行、+1 轉成 1-based
        return self.rep.block_line

    def _recon_declared(self):
        """這一份是不是**真的**偵察模式報告。

        豁免不能只靠一句宣告買到，否則「空預設清單」的關法就等於在旁邊開一扇門：
        任何報告寫一行〈模式：偵察抽樣〉就能跳過第 1 步、照樣給判定。SKILL.md
        〈偵察模式〉同時規定了那一份長什麼樣——`settlement` 的存活與已淘汰都是 0
        （只輸出〔DONE?〕與〔待再查〕、全部進第三節、不做淘汰）。兩件都成立才算，
        而第二件同時被 COUNT-01／RECON-01 對到散文的實際列數，所以它不是自我宣告。
        """
        declared = any(RECON_MODE_RE.match(strip_md(t)) for _n, t in self.rep.header_lines)
        if not declared:
            return False
        st = self.rep.settlement
        return bool(st) and self.rep.settlement_ok and st[1] == 0 and st[3] == 0

    def tier_verbatim_exempt(self):
        """表頭自己宣告是偵察模式的報告：不逐字比對階梯表。
        **跨欄照抄照樣是違規**，豁免只到「這一欄的四個字串之一」為止。

        理由是階梯表沒有偵察模式這一列，而 hunt 的階 0 那一格寫的是
        「存在性、撤稿、滾雪球均已機器查核」——偵察模式依 SKILL.md〈偵察模式〉
        本來就不做撤稿與品質檢查，它跑得動 lit_api 卻不是階 1／2／3。
        逼它照抄階 0，等於在這個角落重新製造分兩欄要消滅的那件事：
        規格要求一份報告寫下自己知道是假的東西。所以這裡讓它自己造句，
        代價寫清楚——**這一階的字串沒有被逐字比對過**。缺的是階梯表裡的一列
        （那是規格的事，不是查核器的），不是一條規則。

        判準刻意比 `_recon_declared()` 寬：只要表頭任何一行宣告了偵察模式
        （〈模式〉或〈降級聲明〉都算）。窄成「只認〈模式〉那一行」的話，
        recon_undeclared_empty.md 改掉〈模式〉之後會同時亮 BLOCK-01 與 STRUCT-02，
        而它只壞了一個維度——一次編輯不該產生兩句話，其中一句還指著沒有壞的那一行。
        """
        return any(RECON_SELFDECL_RE.search(strip_md(t))
                   for _n, t in self.rep.header_lines)

    def _check_assumptions_present(self):
        """空的 `assumptions` 是一個**明講出來的宣稱**，不是缺席——所以它查得動。

        以前這裡什麼都沒有：STRUCT-01 只要求二／三／四／六四個區段，沒有任何規則
        要求 `assumptions` 非空，於是刪掉第一節的每一條預設、把 `assumptions` 寫成 `[]`、
        把唯一的 G3 候選改成 G1，整份報告就跳過了這個技能的第 1 步而離開碼 0。
        這是**普通的偷懶**會掉進去的洞，不是對抗者才構造得出來的——第 1 步最貴，
        而它是後面每一個 G3 的原料。
        """
        rep = self.rep
        if rep.block is None or not rep.assumptions_ok:
            return                       # 區塊本身讀不到／容器壞了，BLOCK-01 已經報過
        if rep.block.get("assumptions"):
            return
        if self._recon_declared():
            return                       # 偵察模式：明講沒跑第 1 步，空清單是誠實的
        self.add("BLOCK-01", self._block_line("\"assumptions\""),
                 rep.lines[self._block_line("\"assumptions\"") - 1]
                 if 0 < self._block_line("\"assumptions\"") <= len(rep.lines) else "",
                 "區塊的 `assumptions` 是空的——這是在宣稱本次一條預設都沒有盤出來，"
                 "也就是 SKILL.md 第 1 步整步沒跑。第 1 步是後面 G3 的唯一原料，"
                 "而它是這個流程最貴的一步，所以「跳過它」不能長得像通過。"
                 "只有偵察模式可以交出空清單，而且要兩件事同時成立："
                 "表頭〈模式〉逐字寫「偵察抽樣（非新穎性判定）」，"
                 "且結算的存活與已淘汰都是 0（那一種明講自己不產生存活候選、不執行淘汰）。"
                 "階 3 完全沒有檢索工具時**不是**這一種：預設照寫，"
                 "status 一律 `impression`（SKILL.md 第 5 步）")

    def check_block(self):
        """抽出、解析、驗證 rgh-block，並把結果填進 rep（給下游規則用）。

        **沒有區塊就是離開碼 1，不是警告、不是降級模式。** 第一節與結算的所有判斷
        都只從區塊讀，沒有區塊就是這兩塊完全沒有被查過——而沒有被查過不能長得像通過。
        留一條降級模式等於留一句「不想被查就別寫區塊」。
        """
        rep = self.rep
        # **誰需要區塊**：缺口報告。地形報告沒有第一節的預設清單、也沒有候選結算，
        # 所以它不寫區塊、也不會因為沒有區塊被判違規（SKILL.md〈rgh-block〉）。
        # 這一行同時是這條規則唯一可以被削弱的地方：把它放寬成「沒有區塊就跳過」，
        # 就是那條被否決掉的降級模式——而降級模式只是一句「不想被查就別寫區塊」。
        if rep.mode != "gap":
            return
        if len(rep.raw_blocks) > 1:
            lines = "、".join(str(b["start"] + 1) for b in rep.raw_blocks)
            self.add("BLOCK-01", rep.raw_blocks[0]["start"] + 1,
                     rep.lines[rep.raw_blocks[0]["start"]] if rep.raw_blocks[0]["start"] < len(rep.lines) else "",
                     "整份報告找到 %d 個 `%s` 區塊（第 %s 行），必須恰好一個。"
                     "**引用在範例裡的區塊也算一個**——這一條單獨就關掉「在檔案某處放一個算術"
                     "自洽的假區塊、讓查核器讀到它而不是真的那一個」那一類誘餌"
                     % (len(rep.raw_blocks), BLOCK_FENCE_INFO, lines))
            return
        if not rep.raw_blocks:
            if rep.near_blocks:
                b = rep.near_blocks[0]
                self.add("BLOCK-01", b["start"] + 1,
                         rep.lines[b["start"]] if b["start"] < len(rep.lines) else "",
                         "這個圍欄區塊的內容看起來就是 rgh-block（它宣告了 "
                         "`\"schema\": \"%s\"`），但圍欄標籤是 `%s`——必須**逐字**是 `%s`，"
                         "查核器是照標籤找它的"
                         % (BLOCK_SCHEMA_VERSION, b["info"], BLOCK_FENCE_INFO))
                return
            self.add("BLOCK-01", 1, "",
                     "這份報告沒有 `%s` 區塊。第一節的預設清單與表頭的候選結算只從區塊讀，"
                     "沒有區塊就是這兩塊完全沒有被查過——**沒有被查過不能長得像通過**。"
                     "寫法見 SKILL.md〈第 5 步〉的〈rgh-block〉小節：放在第七節之後、"
                     "不加區段標題、圍欄標籤逐字寫 `%s`。散文一個字都不必改"
                     % (BLOCK_FENCE_INFO, BLOCK_FENCE_INFO))
            return

        b = rep.raw_blocks[0]
        rep.block_line = b["start"] + 1
        if not b["closed"]:
            self.add("BLOCK-01", rep.block_line, rep.lines[b["start"]],
                     "`%s` 區塊沒有收尾的三個反引號，整份檔案的其餘部分都被吃進區塊裡"
                     % BLOCK_FENCE_INFO)
            return
        try:
            data = json.loads(b["body"])
        except ValueError as exc:
            lineno = getattr(exc, "lineno", None)
            colno = getattr(exc, "colno", None)
            msg = getattr(exc, "msg", str(exc))
            at = (b["start"] + 1 + lineno) if lineno else rep.block_line
            self.add("BLOCK-01", at,
                     rep.lines[at - 1] if 0 < at <= len(rep.lines) else "",
                     "區塊不是合法 JSON：%s（第 %s 行第 %s 欄）。JSON 沒有形狀變體，"
                     "所以這裡沒有「寬容」可談——解析不了就是解析不了"
                     % (msg, lineno if lineno else "?", colno if colno else "?"))
            return

        problems = validate_block(data)
        for check, loc, msg in problems:
            self.add(check, self._block_line(loc), loc or "", msg)

        rep.block = data if isinstance(data, dict) else None
        if rep.block is None:
            return
        st = rep.block.get("settlement")
        if isinstance(st, dict) and all(_is_int(st.get(k)) and st[k] >= 0 for k in SETTLEMENT_KEYS):
            nums = tuple(st[k] for k in SETTLEMENT_KEYS)
            rep.settlement = nums
            # 算術不成立時 settlement_ok 維持 False：BLOCK-01 已經說了結算是壞的，
            # 再拿一個壞掉的數字去跟散文列數比對，只會把一個缺陷變成三句話，
            # 而其中兩句會把作者送去改沒有壞的東西。
            rep.settlement_ok = nums[0] == nums[1] + nums[2] + nums[3]
        ass = rep.block.get("assumptions")
        if isinstance(ass, list):
            rep.assumptions_ok = True
            bad = set()
            for check, loc, _msg in problems:
                if check == "ASSUM-01" and loc:
                    bad.add(loc)
            for e in ass:
                if not isinstance(e, dict):
                    continue
                aid = e.get("id")
                if isinstance(aid, str):
                    # **NFKC 再進這個集合。** 它唯一的用途是閉嘴（下游別再指著一個
                    # 已經被 ASSUM-01 指過的東西），而全形數字寫的 `A１` 正是最需要
                    # 閉嘴的那一種：containment 那一側會 NFKC，原字串比對那一側不會，
                    # 於是同一個編號在兩邊長得不一樣，反向掃描與 G3 查表各報一筆，
                    # 三句話沒有一句提到那位數字。形狀不合由 ASSUM-01 一句講完。
                    rep.block_declared_ids.add(
                        unicodedata.normalize("NFKC", aid).strip().upper())
                if not isinstance(aid, str) or not BLOCK_AID_RE.match(aid):
                    continue
                rec = dict(e)
                rec["_line"] = self._block_line("\"id\": \"%s\"" % aid)
                rec["_clean"] = ("\"id\": \"%s\"" % aid) not in bad
                rep.assumptions.append(rec)
        # 空清單是一個宣稱，不是缺席——放在最後，因為它要用上面剛填好的結算。
        self._check_assumptions_present()

    # ---- 數量：區塊說存活幾個，第二節就要寫得出幾個 -----------------------
    def check_counts(self):
        """數字來自**區塊**，列數來自**散文**——兩個不同的來源，所以這是一次真的交叉比對。

        以前兩邊都是同一份散文（第二節標題的「生成 N → 存活 M」對上候選區塊數），
        而那一行還是「全文第一個 match」找到的，於是一行 HTML 註解就能決定它讀到什麼。
        """
        rep = self.rep
        if not rep.settlement_ok:
            return                       # 沒有區塊或結算本身壞掉，BLOCK-01 已經報過
        actual = len(rep.candidates)
        survived = rep.settlement[1]
        if survived != actual:
            self.add("COUNT-01", self._block_line("\"settlement\""),
                     rep.lines[self._block_line("\"settlement\"") - 1],
                     "區塊的結算寫存活 %d，第二節實際有 %d 個候選區塊（`### 候選 N（C0n）：…`）。"
                     "兩個數字來自不同的地方——一個是區塊自己宣告的，一個是散文裡真的寫出來的，"
                     "對不上就是其中一邊漏了" % (survived, actual))

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

        # 結算的四個數字來自區塊；算術本身由 BLOCK-01 驗（生成 ＝ 存活 ＋ 待確認 ＋ 已淘汰），
        # 存活那一項由 COUNT-01 對到第二節。這裡只剩下面兩項對到第三、四節的列數。
        if not rep.settlement_ok:
            return
        _n, _m, p, q = rep.settlement
        lineno = self._block_line("\"settlement\"")
        raw = rep.lines[lineno - 1] if 0 < lineno <= len(rep.lines) else ""
        if p != len(rep.pending_rows):
            self.add("RECON-01", lineno, raw,
                     "區塊結算寫待確認 %d，第三節實際有 %d 列" % (p, len(rep.pending_rows)))
        if q != len(rep.kill_rows):
            self.add("RECON-01", lineno, raw,
                     "區塊結算寫已淘汰 %d，第四節實際有 %d 列" % (q, len(rep.kill_rows)))

    # ---- 錨點：區塊寫的每一段字，散文裡都要找得到 -------------------------
    #
    # **錨點問的是三個問題，不是一個。** SKILL.md〈rgh-block〉的錨點規則逐字寫的是
    # 「每條預設的 `anchor`（那一句話）→ 出現在**第一節那條預設行上**」、
    # 「`impression` → **該預設行**要有〔印象，未驗證〕」。以前查核器只問了最寬的那一版
    # （「文件裡有沒有這個字串」），於是兩種構造全綠，而重構之前的那棵樹兩種都會紅：
    #   1. 把整條預設行從第一節搬進某個候選的〈可行性〉段落——字都在，位置全錯；
    #   2. 把〔印象，未驗證〕從 A3 撕下來貼到 framed 的 A1 上——讀者看到的效力是反的。
    # 差別不在寬容度，在**問題問得夠不夠具體**：三個問題的答案都只有「有／沒有」，
    # 所以沒有一個會靜默丟東西；它們只是把「文件裡某處」收斂成「那一條的那一行、
    # 而且那一行不在別節裡」。
    #
    # 這一節（consensus）與「認不出來的一節」不算外人：節名被改寫而形狀也認不回來時，
    # 預設行落在一個未分類的區段裡，那是既有的降級路徑，不是搬家。
    FOREIGN_HOST_KINDS = set(SECTION_KIND_LABEL) - set(("consensus", "other"))

    # 效力標籤：寫在**哪一條**上是有意義的，所以每一個都同時是正向與反向錨點。
    # （標籤, 必須帶它的 status, 不得帶它的 status, 人話）
    # `inherited` 刻意不在〔印象，未驗證〕的禁用側：SKILL.md〈互鎖的例外〉要求那一行
    # 保持〔承接自地形 W…〕，而它照規格會寫「效力同〔印象，未驗證〕」——那是比較，不是改標。
    STATUS_DECORATIONS = (
        ("〔印象，未驗證〕", ("impression",), ("framed", "inherited_framed"), "印象級"),
        ("承接自地形", ("inherited", "inherited_framed"), ("framed", "impression"), "承接自地形"),
        ("已補取樣框", ("inherited_framed",), ("framed", "impression", "inherited"), "已補取樣框"),
    )

    def _anchors(self):
        """由區塊**算出**期望字串。回傳 [(字串, 這是什麼, 定位用的區塊片段, 綁哪一條預設)]。

        第四項是這一輪加的：`None` 代表這段字該出現在文件的某處（表頭那兩行），
        `A<n>` 代表它該出現在**那一條預設自己的那一行上**。分開才問得出上面第 2 種構造。
        """
        rep = self.rep
        out = []
        if rep.settlement_ok:
            g, s, p, k = rep.settlement
            loc = "\"settlement\""
            out.append(("生成 %d ＝ 存活 %d ＋ 待確認 %d ＋ 已淘汰 %d" % (g, s, p, k),
                        "表頭的〈候選結算〉那一行", loc, None))
            out.append(("生成 %d 個 → 存活 %d 個" % (g, s),
                        "第二節標題括號裡的那兩個數字", loc, None))
        for a in rep.assumptions:
            if not a.get("_clean"):
                continue        # 這一條本身就不合 schema，ASSUM-01 已經報過
            aid = a["id"]
            loc = "\"id\": \"%s\"" % aid
            status = a.get("status")
            out.append(("預設 %s" % aid, "第一節的預設編號", loc, aid))
            out.append((a.get("anchor") or "", "預設 %s 的那一句話" % aid, loc, aid))
            if status == "impression":
                out.append(("〔印象，未驗證〕", "預設 %s 的效力標籤" % aid, loc, aid))
            if status in ("inherited", "inherited_framed"):
                out.append(("承接自地形 %s" % a.get("wall"), "預設 %s 的來源標籤" % aid, loc, aid))
                # 這一個**是**文件層的：它指的是表頭那一行，不是預設行。
                out.append(("地形來源", "表頭的〈地形來源〉那一行", loc, None))
            if status == "inherited":
                fams = a.get("families") or []
                out.append(("支撐家族 %s" % "、".join(fams), "預設 %s 的支撐家族" % aid, loc, aid))
            if status == "inherited_framed":
                out.append(("已補取樣框", "預設 %s 的補框標籤" % aid, loc, aid))
            f = a.get("frame")
            if isinstance(f, dict) and not _frame_problems(f):
                out.append(("標題層掃描 %s 篇" % f["N"], "預設 %s 的 N" % aid, loc, aid))
                out.append((f["query"], "預設 %s 的檢索詞" % aid, loc, aid))
                out.append(("limit %s" % f["limit"], "預設 %s 的 limit" % aid, loc, aid))
                out.append(("摘要層精讀 %s 篇" % f["Mp"], "預設 %s 的 M′" % aid, loc, aid))
                out.append(("pick 索引 %s" % ",".join(str(x) for x in f["pick"]),
                            "預設 %s 的 pick 索引" % aid, loc, aid))
                out.append(("其中 %s 篇沿用此預設" % f["M"], "預設 %s 的 M" % aid, loc, aid))
                out.append((f["refute_query"], "預設 %s 的推翻性檢索詞" % aid, loc, aid))
                out.append(("回傳 %s 篇" % f["Kp"], "預設 %s 的 K′" % aid, loc, aid))
                out.append(("讀後 %s 篇確實檢驗過此預設" % f["K"], "預設 %s 的 K" % aid, loc, aid))
                out.append(("樣本來源：%s" % f["sample"], "預設 %s 的樣本來源" % aid, loc, aid))
        return [(t, why, loc, aid) for t, why, loc, aid in out if t]

    def _assumption_lines(self):
        """每個預設編號在散文裡落在哪幾行（0-based，可能不只一行）。

        這是 token 掃描，不是預設行的解析——它只回答「這一行有沒有提到 預設 A<n>」，
        與第一節的形狀定位、與反向覆蓋掃描是同一個問題。多認幾行是安全的：
        底下每一條規則問的都是「**有沒有一行**同時滿足」，多一個候選行只會讓紅燈更難出現。
        """
        cached = getattr(self, "_aid_lines_cache", None)
        if cached is not None:
            return cached
        out = {}
        for i, ln in enumerate(self.rep.prose_lines_norm):
            if not ln.strip():
                continue
            for m in PROSE_AID_RE.finditer(ln):
                out.setdefault("A" + m.group(1), []).append(i)
        self._aid_lines_cache = out
        return out

    def _section_kind_at(self, idx):
        for s in self.rep.sections:
            if s["start"] <= idx < s["end"]:
                return s["kind"]
        return None

    def _anchor_missing(self, text, why, loc):
        self.add("ANCHOR-01", self._block_line(loc), text[:120],
                 "區塊寫了「%s」（%s），散文裡找不到逐字相同的一份。"
                 "比對前兩邊都做過正規化（全形轉半形、去掉粗體與反引號、空白摺疊、大小寫不計），"
                 "所以這不是標點的問題——是區塊與讀者看到的內容不一致。"
                 "**HTML 註解裡的字不算「出現在散文」**：藏在註解裡的漂亮數字騙不過這一條"
                 % (text[:120], why))

    def check_anchors(self):
        rep = self.rep
        if rep.block is None:
            return                      # BLOCK-01 已經說了整個區塊讀不到
        aid_lines = self._assumption_lines()
        no_line = set()
        for text, why, loc, aid in self._anchors():
            norm = normalize_for_containment(text)
            if aid is None:
                if norm not in rep.prose_norm:
                    self._anchor_missing(text, why, loc)
                continue
            lines = aid_lines.get(aid) or []
            if not lines:
                # 連 `預設 A<n>` 都沒有任何一行寫著＝這一條整條不在散文裡。
                # 一個缺陷一句話：只報一次，這一條的其餘錨點閉嘴。
                if aid not in no_line:
                    no_line.add(aid)
                    self._anchor_missing("預設 %s" % aid, "第一節的預設編號", loc)
                continue
            if any(norm in rep.prose_lines_norm[i] for i in lines):
                continue
            if norm not in rep.prose_norm:
                self._anchor_missing(text, why, loc)
                continue
            self.add("ANCHOR-01", lines[0] + 1, rep.lines[lines[0]],
                     "區塊寫了「%s」（%s）。這段字在文件裡找得到，"
                     "但**不在寫著「預設 %s」的那一行上**（第 %s 行）。"
                     "SKILL.md〈rgh-block〉的錨點規則是「出現在第一節那條預設行上」，"
                     "不是「出現在文件的某處」——散在別處的字讀者不會把它讀成這一條預設的內容，"
                     "而區塊卻拿它當作對得上"
                     % (text[:120], why, aid, "、".join(str(i + 1) for i in lines)))
        self._check_assumption_hosts(aid_lines)
        self._check_status_decorations(aid_lines)
        self._check_reverse_coverage()

    def _check_assumption_hosts(self, aid_lines):
        """那一行**落在哪一節**：整條預設行搬進候選、淘汰表或檢索紀錄裡，字都在、位置全錯。

        判準是「**至少有一行**不在別節裡」，不是「每一行都要在第一節」——
        候選的〈缺口類型〉本來就可能順手寫一句「反轉預設 A1」，那種交叉引用不該變成紅燈。
        只有當這個編號**每一次**出現都落在一個已經被認成別種區段的地方時才報：
        那時第一節裡真的沒有這一條。
        """
        for a in self.rep.assumptions:
            if not a.get("_clean"):
                continue
            aid = a["id"]
            lines = aid_lines.get(aid) or []
            if not lines:
                continue            # check_anchors 已經說了它整條不在散文裡
            hosts = [(i, self._section_kind_at(i)) for i in lines]
            if any(k not in self.FOREIGN_HOST_KINDS for _i, k in hosts):
                continue
            i, kind = hosts[0]
            self.add("ANCHOR-01", i + 1, self.rep.lines[i],
                     "「預設 %s」在散文裡只出現在%s裡（第 %d 行），第一節沒有這一條。"
                     "第 1 步的預設清單要留在第一節：那一節是接手的人（下一輪、或缺口獵捕）"
                     "唯一會去讀的地方，而把整條搬進別節，區塊的每一個錨點照樣對得上——"
                     "這正是 containment 只問「文件裡有沒有」時看不見的那一種"
                     % (aid, SECTION_SHORT_NAME.get(kind, SECTION_KIND_LABEL.get(kind, kind)),
                        i + 1))

    def _check_status_decorations(self, aid_lines):
        """效力標籤的**反面**：不該帶這個標籤的預設行上，不得出現這個標籤。

        正面（該有的要有）由 `_anchors` 出題。少了反面，把〔印象，未驗證〕從 A3 撕下來
        貼到 framed 的 A1 上，只會報「A3 那一行少了標籤」一句，而讀者眼前的 A1 被標成
        印象級、A3 沒有標——兩條都被讀錯，查核器卻只說了一半。
        """
        for a in self.rep.assumptions:
            if not a.get("_clean"):
                continue
            status = a.get("status")
            for label, want, forbid, human in self.STATUS_DECORATIONS:
                if status not in forbid:
                    continue
                needle = normalize_for_containment(label)
                for i in aid_lines.get(a["id"], []):
                    if needle not in self.rep.prose_lines_norm[i]:
                        continue
                    self.add("ANCHOR-01", i + 1, self.rep.lines[i],
                             "「預設 %s」那一行寫著「%s」，區塊卻說它的 `status` 是 `%s`。"
                             "這個標籤只屬於 status 是 %s 的預設——效力是讀者唯一看得到的東西，"
                             "掛錯一條，兩條都被讀錯（這一條被讀成%s，真正是%s的那一條沒有標記）"
                             % (a["id"], label, status,
                                "／".join("`%s`" % s for s in want), human, human))
                    break

    def _check_reverse_coverage(self):
        """反向：散文裡寫了 `預設 A<n>`，區塊裡卻沒有這一條。

        containment 只問 區塊→散文，所以一條「區塊整個漏掉」的預設會安靜地通過。
        這是本次唯一還在對散文做 token 掃描的地方，而它的失效方向是**假紅燈**
        （一句剛好提到「預設 A9」的散文會被要求進區塊），不是假綠燈。
        它抓不到的是措辭漂移過的那一條（`前提 A9`）——那一條會落進「隱形」，
        而不是落進「假宣稱」：它不在區塊裡，就不能餵給 G3，referential integrity 會擋。
        """
        rep = self.rep
        if not rep.assumptions_ok:
            # `assumptions` 不是一個陣列。BLOCK-01 已經說了那個容器壞了，這裡再逐條
            # 說「區塊裡沒有這一條」只會把一個缺陷變成 N 句話，而那 N 句都指錯方向。
            return
        known = set(a["id"] for a in rep.assumptions if a.get("id"))
        known |= rep.block_declared_ids
        seen = set()
        for i, ln in enumerate(rep.scan_lines):
            if not ln.strip():
                continue
            for m in PROSE_AID_RE.finditer(normalize_for_containment(ln)):
                aid = "A" + m.group(1)
                if aid in known or aid in seen:
                    continue
                seen.add(aid)
                self.add("ANCHOR-01", i + 1,
                         rep.lines[i] if i < len(rep.lines) else "",
                         "散文寫了「預設 %s」，區塊的 `assumptions` 裡卻沒有這一條。"
                         "兩邊是一對一：區塊漏掉一條，那一條的取樣框、效力與 G3 資格就完全沒有被查過"
                         % aid)

    def check_g3_inputs(self):
        """G3 反轉的是誰，從**候選欄位**（散文）讀；那一條有沒有資格，從**區塊**讀。

        以前兩件事都要從第一節那一行的括號標籤解析出來，而那一行的形狀正是四輪拉鋸的戰場。
        現在效力是一個列舉值，換寫法不再改變任何一條規則的適用性。
        """
        if self.rep.block is None or not self.rep.assumptions_ok:
            return
        by_id = {}
        for a in self.rep.assumptions:
            by_id.setdefault(a["id"], a)
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
                    if ref in self.rep.block_declared_ids:
                        continue      # 那一條在區塊裡，只是形狀壞了——ASSUM-01 已經報過
                    self.add("ASSUM-02", lineno, raw,
                             "G3 候選指到區塊 `assumptions` 裡沒有的預設 %s——"
                             "第一節寫了而區塊漏掉的話，ANCHOR-01 會指著那一行" % ref)
                    continue
                status = a.get("status")
                if status == "inherited":
                    # 這一條**在**報告裡，只是還沒付檢索成本。訊息一定要講清楚是哪一種：
                    # 說它「不存在」會把讀者送去找一個不存在的缺漏，而真正的動作
                    # 是對這一條（只有這一條）補跑取樣框。
                    self.add("ASSUM-02", lineno, raw,
                             "G3 候選的輸入 %s 的 `status` 是 `inherited`（承接自地形 %s、尚未補取樣框，"
                             "見第 %d 行）——它在報告裡，但地形模式沒有跑過 N／M′／M／K′／K，"
                             "效力等同〔印象，未驗證〕，不得長出候選。要反轉它就只對這一條補跑取樣框，"
                             "補完把 status 改成 `inherited_framed`、散文標成〔承接自地形 W…，已補取樣框〕再進 G3"
                             % (ref, a.get("wall"), a["_line"]))
                elif status == "impression":
                    self.add("ASSUM-02", lineno, raw,
                             "G3 候選的輸入 %s 的 `status` 是 `impression`——印象級預設不得長出候選"
                             "（見第 %d 行）" % (ref, a["_line"]))

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
            # 第一節預設的互鎖。**豁免與否改由區塊的 status 決定**，不再從那一行的
            # 括號標籤讀出來：framed／inherited_framed 付過檢索成本，要有
            # `第1步-推翻A<n>` 那一列；impression／inherited 沒付過，逼它附紀錄
            # 就是逼報告去寫一次沒跑過的搜尋。豁免的**理由一個字都沒變**，
            # 變的只是判斷依據。
            cells = [strip_md(r.get("candidate", "")) for r in self.rep.trace_rows]
            for a in self.rep.assumptions:
                if a.get("status") not in ("framed", "inherited_framed"):
                    continue
                if not a.get("_clean"):
                    continue                  # 這一條本身不合 schema，ASSUM-01 已經報過
                want = "第1步-推翻%s" % a["id"]
                if any(want in re.sub(r"\s+", "", c) for c in cells):
                    continue
                self.add("TRACE-01", a["_line"], "\"id\": \"%s\"" % a["id"],
                         "預設 %s 的 `status` 是 `%s`（跑過或補過取樣框），"
                         "第六節卻沒有標成「%s」的對應列——宣稱跑過那一輪推翻性檢索，"
                         "就要拿得出那一列。真的沒跑就把 status 改成 `%s`"
                         % (a["id"], a.get("status"), want,
                            "impression" if a.get("status") == "framed" else "inherited"))
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
        # 區塊先驗：它填 rep.settlement／rep.assumptions，下游好幾條規則要用。
        self.check_block()
        self.check_anchors()
        self.check_parse()
        self.check_sections()
        self.check_structure()
        self.check_counts()
        self.check_reconciliation()
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

    # ---- 地形報告不寫區塊：寫了就是一塊沒有人讀的地方 ---------------------
    def check_stray_block(self):
        """SKILL.md〈rgh-block〉：地形報告沒有第一節的預設清單、也沒有候選結算，
        **不寫區塊**。所以這裡出現一個區塊不是「多寫了一份沒用的東西」——
        它是文件裡一塊不會被驗證的區域（`LandscapeChecker` 沒有 `check_block`，
        也不該有：驗一個規格說不存在的東西，等於默認它可以存在）。

        兩件事分開做，理由不同：這一條說「這個區塊本身不該在」，
        `PARSE-01` 的圍欄掃描說「而且它裡面裝了報告結構」。前者是規格，後者是掃描；
        一個區塊可以只犯前者（裡面只有合法 JSON），所以兩條都要在。
        """
        # 波浪號寫的區塊也算。`find_fenced_blocks` 只認反引號是刻意的（見它的
        # docstring），但那個理由屬於 BLOCK-01 的「整份恰好一個」，不屬於這一條：
        # 這裡問的是「有沒有一塊不受查核的區域」，而 `~~~json rgh-block` 在讀者
        # 眼裡跟反引號那種一模一樣。只認一種就是留一個一字元的繞道。
        tilde = [{"start": b["start"], "info": b["info"]}
                 for b in _find_fences_for_scan(self.rep.lines)
                 if b["char"] == "~" and b["info"] == BLOCK_FENCE_INFO]
        for b in list(self.rep.raw_blocks) + list(self.rep.near_blocks) + tilde:
            lineno = b["start"] + 1
            self.add("BLOCK-01", lineno,
                     self.rep.lines[b["start"]] if b["start"] < len(self.rep.lines) else "",
                     "地形報告裡出現 `%s` 區塊。SKILL.md〈rgh-block〉寫著地形報告不寫區塊"
                     "（它沒有第一節的預設清單、也沒有候選結算），所以**沒有任何規則會驗它**"
                     "——它是這份文件裡一塊不受查核的區域，而不受查核的區域裝什麼都不會有人說話。"
                     "第一節的預設要交棒給缺口獵捕，走的是第六節的牆表；"
                     "要寫區塊就把這一份寫成缺口報告"
                     % (b["info"] or BLOCK_FENCE_INFO))

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
            scan = self.rep.scan_lines[i] if i < len(self.rep.scan_lines) else ln
            token = NOVELTY_TOKEN_RE.search(scan)
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
    def _evidence(self, value):
        """讀出檢索句型的兩段子句：(M, [(切分年, N), …])。讀不成句型就回 None。

        第一段（索引的寬鬆關鍵字總數，或「未回傳總數」）只問形狀，因為 X 與 M
        分屬兩個母體、彼此之間沒有算術；第二段的 M 與 N **在同一頁裡**，所以
        它們之間有一條可查的算術（N ≤ M），而那正是「其中」在這裡是真的的理由。
        """
        v = strip_md(value or "")
        first = bool(LAND_EV_TOTAL_RE.search(v) or LAND_EV_NOTOTAL_RE.search(v))
        read = LAND_EV_READ_RE.search(v)
        afters = [(int(y), int(n)) for y, n in LAND_EV_AFTER_RE.findall(v)]
        if not first or read is None or not afters:
            return None
        return int(read.group(1)), afters

    def _undecidable_majority(self):
        """這份報告是不是「多數家族讀到的那一頁都幾乎全部落在切分年之後」。

        〔判不出〕的第三項條件。它把兩件事分開：一個成熟領域裡某一族的近年占比
        特別高，那是〔活躍〕、資訊是真的；整份報告每一族都貼著上限，那是**這個
        領域比視窗還年輕**——「近三年占比低」在構造上不可能出現，四個值退化成兩個。
        沒有任何家族拿得出數字時回 None（那是別條臂的事，不在這裡判）。
        """
        scored = []
        for fam in self.rep.families:
            if "status" not in fam["fields"]:
                continue
            ev = self._evidence(fam["fields"]["status"][1])
            if ev is None:
                continue
            read, afters = ev
            top = max(n for _y, n in afters)
            if read <= 0 or top > read:
                continue          # 算術本身就壞了的那一列，不拿去左右別的家族
            scored.append(top / float(read))
        if not scored:
            return None
        return len([r for r in scored if r >= LAND_UNDECIDABLE_RATIO]) * 2 > len(scored)

    def _status_problem(self, value, majority=None):
        v = strip_md(value or "")
        v = re.split(r"[｜|]", v)[0]
        v = v.strip("〔〕【】[]（）() 　").strip()
        if not v:
            return "〈狀態〉是空的"
        if v not in LAND_STATUS_VALUES:
            return ("〈狀態〉值「%s」不在 %d 個合法值內（%s）"
                    % (v, len(LAND_STATUS_VALUES), "／".join(LAND_STATUS_VALUES)))
        if v == LAND_STATUS_EXEMPT:
            return None      # 誠實的退場：標了就走，不必附證據
        ev = self._evidence(value)
        if ev is None:
            return ("〈狀態〉「%s」沒有掛完整的兩段子句檢索句型——同一欄要寫"
                    "「`<查詢詞>` 在 <索引> 的寬鬆關鍵字總數 <X> 筆（工具自報，未加年份條件）；"
                    "本次實際讀取回傳的前 <M> 筆，其中 <年份> 之後 <N> 筆」"
                    "（工具沒回報總數時第一段換成「未回傳總數（<原因>）」，第二段一個字不變）。"
                    "兩段之間沒有「其中」，因為 X 與 M 不是同一個母體。"
                    "湊不出數字就寫〔涵蓋不足〕，那是這個模式允許的答案" % v)
        read, afters = ev
        bad = [(y, n) for y, n in afters if n > read]
        if bad:
            return ("〈狀態〉「%s」的第二段子句算術不成立：讀到的是前 %d 筆，"
                    "卻說其中 %d 之後有 %d 筆。N 數在 M 那一頁裡，所以 N ≤ M；"
                    "會超過通常是把索引的寬鬆關鍵字總數（第一段的 X）當成了母體，"
                    "而那正是這個句型拆成兩段要擋掉的事"
                    % (v, read, bad[0][0], bad[0][1]))
        if not (BACKTICK_RE.search(value) or QUOTED_ANY_RE.search(value)):
            return ("〈狀態〉「%s」有筆數卻沒有逐字查詢詞——讀者要能把那個詞複製去重跑一次" % v)
        if v == LAND_STATUS_UNDECIDABLE:
            ratio = max(n for _y, n in afters) / float(read) if read > 0 else 0.0
            if ratio < LAND_UNDECIDABLE_RATIO:
                return ("〈狀態〉〔判不出〕的第二項條件不成立：這一頁只有 %d／%d "
                        "（%.0f%%）落在切分年之後，不到八成。**方向很重要**——"
                        "幾乎全部落在切分年之前是〔飽和〕〔衰退〕的證據，不是判不出。"
                        "〔判不出〕說的是「切分年在這個領域沒有鑑別力」，"
                        "而這一頁的切分年正在分得出東西"
                        % (max(n for _y, n in afters), read,
                           100.0 * ratio))
            if majority is False:
                return ("〈狀態〉〔判不出〕的第三項條件不成立：這份報告**多數家族並不是這樣**。"
                        "一個成熟領域裡有一族的近年占比特別高，那是〔活躍〕、資訊是真的；"
                        "〔判不出〕要的是整份報告每一族都貼著上限的那一種——"
                        "那時候「近三年占比低」在構造上不可能出現，四個值才真的退化成兩個")
        return None

    def check_status(self):
        majority = self._undecidable_majority()
        for fam in self.rep.families:
            if "status" not in fam["fields"]:
                self.add("LSTAT-01", fam["line"], "### %s %s" % (fam_ref(fam), fam["name"]),
                         "家族 %s 缺〈狀態〉欄" % fam_ref(fam))
                continue
            lineno, val = fam["fields"]["status"]
            problem = self._status_problem(val, majority)
            if problem:
                self.add("LSTAT-01", lineno, self.rep.lines[lineno - 1],
                         "家族 %s 的%s" % (fam_ref(fam), problem))
        for row in self.rep.glance_rows:
            cell = row.get("status", "")
            if not strip_md(cell):
                # 空白以前是跳過的，而〈買到什麼〉〈付出什麼〉那兩欄空白是會被 LCOST-01
                # 抓的——同一張表的同一種缺陷不該有兩套待遇。空白也是「不在合法值內」。
                self.add("LSTAT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "一眼表這一列的〈狀態〉是空的（欄位空白，或表頭沒有這一欄）——"
                         "%d 個合法值是 %s，證據撐不起任何一個就寫〔涵蓋不足〕"
                         % (len(LAND_STATUS_VALUES), "／".join(LAND_STATUS_VALUES)))
                continue
            gv = strip_md(cell).strip("〔〕【】[]（）() 　").strip()
            if gv not in LAND_STATUS_VALUES:
                self.add("LSTAT-01", row["_line"], self.rep.lines[row["_line"] - 1],
                         "一眼表的〈狀態〉「%s」不在 %d 個合法值內（%s）"
                         % (gv, len(LAND_STATUS_VALUES), "／".join(LAND_STATUS_VALUES)))

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
        self.check_stray_block()
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
                # 區塊：包裝這支工具的人要能分辨「沒有區塊」與「區塊在但壞了」。
                "rgh_blocks": len(rep.raw_blocks),
                "block_ok": rep.block is not None,
                "settlement": list(rep.settlement) if rep.settlement else None,
                "settlement_reconciles": rep.settlement_ok,
                "assumptions": len(rep.assumptions),
                # 讀不進來的東西也要出現在解析摘要裡：包裝這支工具的人要能分辨
                # 「乾淨」與「根本沒讀到」，而那正是靜默丟行最擅長偽裝的差別。
                "unreadable": len(rep.table_strays) + len(rep.head_strays),
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
        print("  rgh-block %d 個／預設 %d 條／結算 %s"
              % (len(rep.raw_blocks), len(rep.assumptions),
                 ("＝".join(["生成 %d" % rep.settlement[0],
                             "存活 %d ＋ 待確認 %d ＋ 已淘汰 %d" % rep.settlement[1:]])
                  if rep.settlement else "（讀不到）")))
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
