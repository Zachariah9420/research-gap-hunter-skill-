#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_fixtures.py — 由手寫基準樣本生成所有衍生樣本。

樣本的價值來自「只壞一個維度」：一個樣本若同時壞了三處，紅燈就無法定位缺陷。
用手改檔案守不住這個性質，所以每個衍生樣本都由本檔用**一次替換**產生，
單一維度是被建構出來的，不是靠肉眼維持的。

規則：
  - 每個樣本 = 它自己的基準 ＋ 恰好一處實質修改（或一組同性質的刪行）
    ＋ 一行說明本檔壞在哪的註記。self_test.py 會驗這個「≤2 行」上限。
  - 被替換的原文必須在該基準中**恰好出現一次**，否則直接中止：
    位置模稜兩可的替換，生出來的樣本也是模稜兩可的。
  - 手寫基準樣本不由本檔生成，也不會被覆寫：good_report.md（完整獵捕）、
    good_nosearch_report.md（階 3 降級）、chinese_index_na.md、
    good_landscape.md（領域地形）、good_inherited_report.md（承接地形的獵捕）。

用法：
    python evals/make_fixtures.py          # 重新生成
    python evals/make_fixtures.py --check  # 只比對磁碟上的檔案是否與生成結果一致
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
BASE = os.path.join(FIXTURES, "good_report.md")
# 第二個基準：領域地形報告。它是**另一種文件形狀**，不是缺口報告的變體，
# 所以它的衍生樣本從它自己長出來，不從 good_report.md 長。
LAND_BASE = os.path.join(FIXTURES, "good_landscape.md")
# 第三個基準：承接地形報告的缺口報告。它是**兩個模式接起來的那一份**——
# 表頭帶〈地形來源〉、第一節同時有本輪量化的預設、承接未補框的預設、
# 與承接後補了取樣框的預設。這三種在同一份裡並存才是真實的形狀，
# 而它們的差別只能靠改一行來釘，所以它得自己當基準，不能是 good_report.md 的變體。
INHERIT_BASE = os.path.join(FIXTURES, "good_inherited_report.md")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 註記插在這一行之後（仍在開頭的引言區塊內）
NOTE_ANCHOR = "> 識別碼使用 Crossref 測試前綴 10.5555，不對應任何真實出版品。"

# 敘事型樣本的包裹文字（唯一一個不是「壞掉」的衍生樣本）
NARRATIVE_HEAD = """# 教學走查：一份報告長什麼樣子

這一段是教學說明，不是報告內容。學生最常犯的錯是在報告裡寫「沒人做過」——
那是斷言，不是搜尋結果。下面用一份完整的示範報告說明正確的寫法。
報告本體以 report-start／report-end 標記包起來，查核器只查標記之內。

<!-- format-check: report-start -->
"""

NARRATIVE_TAIL = """<!-- format-check: report-end -->

## 教學後記

回頭看上面那份報告：它從頭到尾沒有一句「沒人做過」，每一個淘汰都指名了文獻。
這一段同樣是教學說明，即使它引用了被禁止的措辭，也不該讓查核器變紅——
因為它不在報告區塊裡。
"""

# name -> (note, [(old, new), ...] 或 ("drop", 子字串))
FIXTURES_SPEC = [
    (
        "missing_trace_section.md",
        "相對於 good_report.md，本檔刻意壞掉一處：〈六、檢索紀錄〉整節被改成別的標題，稽核軌跡因此消失。",
        [("## 六、檢索紀錄（不得省略）", "## 六、附錄：查詢筆記")],
    ),
    (
        "no_tool_tier.md",
        "相對於 good_report.md，本檔刻意壞掉一處：表頭的〈文獻工具〉宣告是佔位符，讀者無從判斷這份報告的查核階層。",
        [("**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）",
          "**文獻工具**：待補")],
    ),
    (
        "count_mismatch.md",
        "相對於 good_report.md，本檔刻意壞掉一處：第二節標題宣告存活 4 個，實際只寫了 3 個候選區塊。",
        [("## 二、存活候選（生成 12 個 → 存活 3 個）",
          "## 二、存活候選（生成 12 個 → 存活 4 個）")],
    ),
    (
        "count_inverted.md",
        "相對於 good_report.md，本檔刻意壞掉一處：第二節標題寫成生成 2 個卻存活 3 個，算術上不可能。",
        [("## 二、存活候選（生成 12 個 → 存活 3 個）",
          "## 二、存活候選（生成 2 個 → 存活 3 個）")],
    ),
    (
        "recon_mismatch.md",
        "相對於 good_report.md，本檔刻意壞掉一處：表頭的候選結算把待確認寫成 4，與第三節的 3 列對不起來，總數也不等於生成數。",
        [("**候選結算**：生成 12 ＝ 存活 3 ＋ 待確認 3 ＋ 已淘汰 6",
          "**候選結算**：生成 12 ＝ 存活 3 ＋ 待確認 4 ＋ 已淘汰 6")],
    ),
    (
        "bad_verdict.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 1 的判定寫成詞彙表以外的 NOVEL。",
        [("- **新穎性判定**：ADJACENT", "- **新穎性判定**：NOVEL")],
    ),
    (
        "done_in_survivors.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 2 給了 DONE，卻仍留在存活清單裡。",
        [("- **新穎性判定**：OPEN", "- **新穎性判定**：DONE")],
    ),
    (
        "assumption_no_frame.md",
        "相對於 good_report.md，本檔刻意壞掉一處：預設 A2 少了摘要層精讀那一段取樣框，量化預設變成無法追溯的數字。",
        [("｜摘要層精讀 5 篇（pick 索引 1,4,6,8,12），其中 4 篇沿用此預設", "")],
    ),
    (
        "impression_as_g3.md",
        "相對於 good_report.md，本檔刻意壞掉一處：預設 A1 降級為〔印象，未驗證〕，但候選 1 仍拿它當 G3 的輸入。",
        [("- 預設 A1：〈住家周邊的綠地面積可以代表居民實際獲得的綠地暴露〉｜標題層掃描 24 篇"
          "（檢索詞 `urban green space physical activity`，limit 24）｜摘要層精讀 8 篇"
          "（pick 索引 0,2,3,5,7,9,11,14），其中 6 篇沿用此預設｜推翻性檢索 "
          "`park use versus residential greenness exposure` 回傳 9 篇，讀後 3 篇確實檢驗過此預設"
          "｜樣本來源：2019–2025，Semantic Scholar ＋ Crossref",
          "- 預設 A1：〈住家周邊的綠地面積可以代表居民實際獲得的綠地暴露〉〔印象，未驗證〕"
          "——摘要層精讀只有 2 篇（M′ < 3），不得作為 G3 輸入")],
    ),
    (
        "missing_evidence_field.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 1 的搜尋證據欄改成查核器不認得的標籤，等於整欄消失。",
        [("- **搜尋證據**：查詢 1 `green space exposure measurement physical activity`",
          "- **佐證資料**：查詢 1 `green space exposure measurement physical activity`")],
    ),
    (
        "no_evidence.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 1 的搜尋證據是佔位符「同上」。",
        [("- **搜尋證據**：查詢 1 `green space exposure measurement physical activity`（回傳 12 筆）；"
          "查詢 2 `park visitation frequency accelerometer physical activity`（回傳 9 筆）；"
          "查詢 3 `residential greenness buffer versus park use exposure`（回傳 7 筆）",
          "- **搜尋證據**：同上")],
    ),
    (
        "vague_evidence.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 1 的搜尋證據只有敘述，沒有任何可複製重跑的查詢詞。",
        [("- **搜尋證據**：查詢 1 `green space exposure measurement physical activity`（回傳 12 筆）；"
          "查詢 2 `park visitation frequency accelerometer physical activity`（回傳 9 筆）；"
          "查詢 3 `residential greenness buffer versus park use exposure`（回傳 7 筆）",
          "- **搜尋證據**：跑了三輪檢索，涵蓋暴露量測與到訪行為兩個方向，命中數都不多。")],
    ),
    (
        "neighbour_no_id.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 1 指名了最近鄰文獻卻拿掉識別碼，讀者無法查核。",
        [("Author C et al. (2023)〈Residential greenness and moderate-to-vigorous physical activity in adults〉，DOI:10.5555/synthetic-0002。",
          "Author C et al. (2023)〈Residential greenness and moderate-to-vigorous physical activity in adults〉。")],
    ),
    (
        "unnamed_kill.md",
        "相對於 good_report.md，本檔刻意壞掉一處：C07 判了 DONE，卻沒有指名殺死它的那篇文獻。",
        [("| Author D et al. (2024) | DOI:10.5555/synthetic-0003 | 期刊 |",
          "|  | DOI:10.5555/synthetic-0003 | 期刊 |")],
    ),
    (
        "crowded_two_papers.md",
        "相對於 good_report.md，本檔刻意壞掉一處：C10 判了 CROWDED，關鍵文獻只列兩篇。",
        [("| Author E et al. (2022)；Author F et al. (2023)；Author G et al. (2024) |",
          "| Author E et al. (2022)；Author F et al. (2023) |")],
    ),
    (
        "done_no_quote.md",
        "相對於 good_report.md，本檔刻意壞掉一處：C07 的 DONE 只有轉述，沒有摘要逐字引句。",
        [("摘要逐字引句：「Using distance from home to the nearest public park, we find that each "
          "additional 100 metres is associated with 3.4 fewer minutes of weekly moderate-to-vigorous "
          "physical activity among 5,200 urban adults.」母體、自變項、結果變項、研究設計四項全中。",
          "該研究用住家到最近公園的距離預測身體活動量，效果顯著，四項條件看起來都對得上。")],
    ),
    (
        "kill_no_identifier.md",
        "相對於 good_report.md，本檔刻意壞掉一處：C08 指名了關鍵文獻，識別碼欄卻是空的。",
        [("| Author N et al. (2023) | DOI:10.5555/synthetic-0013 | 會議 |",
          "| Author N et al. (2023) |  | 會議 |")],
    ),
    (
        "untraced_candidate.md",
        "相對於 good_report.md，本檔刻意壞掉一處：C03 在〈檢索紀錄〉裡沒有任何對應列，卻仍給了新穎性判定。",
        [("drop", "| C03 | ")],
    ),
    (
        "trace_placeholder_query.md",
        "相對於 good_report.md，本檔刻意壞掉一處：〈檢索紀錄〉第 5 列的查詢詞是「（略）」。",
        [("| 5 | C01 | `green space exposure measurement physical activity` | 12 |",
          "| 5 | C01 | （略） | 12 |")],
    ),
    (
        "assertive_language.md",
        "相對於 good_report.md，本檔刻意壞掉一處：候選 1 的失敗原因欄改寫成三句斷言式措辭。",
        [("- **最可能失敗的原因**：到訪紀錄若倚賴受訪者回憶，量測誤差可能大到蓋掉兩種暴露的差異；"
          "社會性風險是口委可能認為換一種暴露量測只是操作化細節，不是研究問題。",
          "- **最可能失敗的原因**：這個方向沒有人做過，目前不存在相關研究，可以確定是新的，"
          "所以風險只剩下量測誤差。")],
    ),
    (
        "no_search_with_verdicts.md",
        "相對於 good_report.md，本檔刻意壞掉一處：表頭宣告本次未執行任何檢索，卻仍然給了判定與淘汰。",
        [("**降級聲明**：無",
          "**降級聲明**：本次未執行任何檢索，以下僅為候選生成，不含新穎性驗證")],
    ),
    (
        "unsearched_pending.md",
        "本檔相對 good_report.md 動兩列，且**應該是綠的**：C06 改成〔未驗證〕（本輪一次也沒搜過）、"
        "C05 維持術語卡關的〔UNSEARCHABLE〕，兩列在第六節的對應紀錄都被拿掉——"
        "SKILL.md〈互鎖的例外〉正是說這兩種列免附檢索紀錄，查核器不得反過來逼報告補一次沒跑過的搜尋。"
        "（檢索紀錄的 # 因此跳過 15、16，那是刪列造成的，不是缺陷。）",
        [
            ("| C06 現行公園品質評估量表其實測到的是景觀美感而非活動支持度 | 待全文查證 | "
             "量表題項只存在於全文，DOI:10.5555/synthetic-0012 無 OA 版本，尚未讀到方法—測量段落 | "
             "走館際合作取得全文，讀方法段並逐字引出題項文字，才可以下構念質疑 |",
             "| C06 現行公園品質評估量表其實測到的是景觀美感而非活動支持度 | 未驗證 | "
             "本輪的檢索預算在 C05 就用完了，這個候選一次也沒有被搜過，因此第六節沒有它的紀錄 | "
             "下一輪優先對它跑兩種查詢（量表構念效度、活動支持度測量），有了檢索紀錄才回來給判定 |"),
            ("drop", "| 15 | C05 | "),
            ("drop", "| 16 | C06 | "),
        ],
    ),
    (
        "bracketed_verdict_ok.md",
        "本檔相對 good_report.md 只改一處，且**應該是綠的**：待確認表用了 SKILL.md 的括號態寫法〔待驗證〕加補充語，查核器必須看懂括號內才是狀態值。",
        [("| C05 以穿戴裝置的 GPS 軌跡切出居民在公園內的活動片段 | UNSEARCHABLE |",
          "| C05 以穿戴裝置的 GPS 軌跡切出居民在公園內的活動片段 | 〔待驗證〕**不列入存活** |")],
    ),
]


# 領域地形報告的衍生樣本。刻意各自只壞一個「臂」，因為地形規則集的每條規則
# 都有數個臂，而突變測試削弱的是樣本真的踩到的那一個。
LAND_FIXTURES_SPEC = [
    (
        "landscape_no_disclaimer.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：表頭那一行自我限制宣告被刪掉，"
        "讀者無從知道這一份不判新穎性。",
        [("**這份報告不做什麼**：不淘汰任何做法、不判斷新穎性、不宣稱任何做法沒有人做過。"
          "要新穎性判定請跑缺口獵捕。", "")],
    ),
    (
        "landscape_verdict_word.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：第三節混進一個缺口獵捕才有的判定詞彙，"
        "地形圖悄悄變成一份沒有付舉證成本的判決。",
        [("這是政策報告最常見的組合。",
          "這是政策報告最常見的組合，這個方向已經 CROWDED，不值得再投入。")],
    ),
    (
        "landscape_no_cost.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：F5 只寫了買到什麼，付出什麼被填成佔位符——"
        "只有一面的描述，是這個模式最容易誤導人的方式。",
        [("- **付出什麼**：願意交出定位資料的人本身就是特定族群，樣本自選；都市峽谷的定位誤差可達數十公尺，"
          "公園邊界附近的判定不穩；資料授權與隱私審查的行政成本高於方法本身。",
          "- **付出什麼**：—")],
    ),
    (
        "landscape_status_asserted.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：F5 的〈狀態〉把趨勢寫成領域事實，"
        "同一欄沒有掛上「回傳 X 筆」的檢索句型。",
        [("- **狀態**：活躍｜`gps trajectory green space exposure dwell time` 在 Semantic Scholar "
          "回傳 143 筆，其中 2023 之後 71 筆",
          "- **狀態**：活躍（近三年明顯在加速，投稿量逐年上升）")],
    ),
    (
        "landscape_orphan_assumption.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：W3 少收了 F6-a，那條預設在第二節寫下來之後"
        "就從第六節消失了，接手的缺口獵捕拿不到它。",
        [("| W3 | 量測到的那個時點或那一段，可以代表更長的期間 | F1-b、F6-a | 2 | 真的必要 |",
          "| W3 | 量測到的那個時點或那一段，可以代表更長的期間 | F1-b | 1 | 真的必要 |")],
    ),
    (
        "landscape_assertive.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：第三節把「本次檢索沒有回傳」寫成斷言。"
        "措辭規則在兩種模式都成立，這一份就是釘住它在地形報告裡也有效。",
        [("成本落在資料授權與倫理審查，通常比方法本身貴。",
          "成本落在資料授權與倫理審查，通常比方法本身貴；這種疊法沒有人做過。")],
    ),
    (
        "landscape_no_tier.md",
        "相對於 good_landscape.md，本檔刻意壞掉一處：表頭的工具階層宣告是佔位符。"
        "這條規則兩種模式共用，這一份釘住它在地形報告裡也有效。",
        [("**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）",
          "**文獻工具**：待補")],
    ),
]


# 承接地形報告的缺口報告的衍生樣本。這三個釘的是兩個模式之間那道橋：
# 承接來的預設在第一節裡**看得見**（不是不存在），未補框者不得長出 G3 候選，
# 補了框者與本輪量化的預設同標準。
INHERIT_FIXTURES_SPEC = [
    (
        "inherited_unframed_ok.md",
        "本檔相對 good_inherited_report.md 只改一處，且**應該是綠的**：C02 改成反轉本輪量化的 A1，"
        "於是承接未補框的 A2 只是躺在第一節裡、沒有餵進任何 G3。這一份釘的是承接進來的預設**不必**"
        "補取樣框（ASSUM-01 不得罰它），也**不必**在第六節有對應列——它不是這一輪搜出來的，"
        "逼它附檢索紀錄就是逼報告去寫一次沒跑過的搜尋。",
        [("- **缺口類型**：G3 預設反轉（反轉 A3）", "- **缺口類型**：G3 預設反轉（反轉 A1）")],
    ),
    (
        "inherited_unframed_as_g3.md",
        "相對於 good_inherited_report.md，本檔刻意壞掉一處：C02 拿承接未補框的 A2 當 G3 的輸入。"
        "A2 在第一節裡，只是還沒付檢索成本——訊息要說它是承接未補框，不是說第一節沒有這一條。",
        [("- **缺口類型**：G3 預設反轉（反轉 A3）", "- **缺口類型**：G3 預設反轉（反轉 A2）")],
    ),
    (
        "inherited_framed_partial.md",
        "相對於 good_inherited_report.md，本檔刻意壞掉一處：A3 標了〔已補取樣框〕，"
        "摘要層精讀那一段卻不見了——補框宣稱了就要跟本輪量化的預設同標準。",
        [("｜摘要層精讀 6 篇（pick 索引 0,1,3,5,8,11），其中 5 篇沿用此預設", "")],
    ),
]


def derived_bases():
    """每個衍生樣本是從哪一份基準長出來的。self_test.py 的「單一維度」檢查要用。"""
    out = dict((name, os.path.basename(BASE)) for name, _n, _e in FIXTURES_SPEC)
    out["narrative_wrapper.md"] = os.path.basename(BASE)
    out.update((name, os.path.basename(LAND_BASE)) for name, _n, _e in LAND_FIXTURES_SPEC)
    out.update((name, os.path.basename(INHERIT_BASE)) for name, _n, _e in INHERIT_FIXTURES_SPEC)
    return out


def load_base(path=BASE):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def build(base, note, edits):
    text = base
    for edit in edits:
        if edit[0] == "drop":
            needle = edit[1]
            kept = [ln for ln in text.splitlines() if needle not in ln]
            dropped = len(text.splitlines()) - len(kept)
            if dropped < 1:
                raise SystemExit("刪行找不到目標：%r" % needle)
            text = "\n".join(kept) + "\n"
            continue
        old, new = edit
        n = text.count(old)
        if n != 1:
            raise SystemExit("替換片段在基準樣本出現 %d 次（需恰好 1 次）：%r" % (n, old[:60]))
        text = text.replace(old, new)
    if note:
        if text.count(NOTE_ANCHOR) != 1:
            raise SystemExit("找不到註記錨點")
        text = text.replace(NOTE_ANCHOR, NOTE_ANCHOR + "\n> " + note)
    return text


def build_narrative(base):
    return NARRATIVE_HEAD + base + NARRATIVE_TAIL


def main():
    check_only = "--check" in sys.argv
    base = load_base()
    outputs = [(name, build(base, note, edits)) for name, note, edits in FIXTURES_SPEC]
    outputs.append(("narrative_wrapper.md", build_narrative(base)))
    land_base = load_base(LAND_BASE)
    outputs += [(name, build(land_base, note, edits)) for name, note, edits in LAND_FIXTURES_SPEC]
    inherit_base = load_base(INHERIT_BASE)
    outputs += [(name, build(inherit_base, note, edits))
                for name, note, edits in INHERIT_FIXTURES_SPEC]

    diffs = []
    for name, text in outputs:
        path = os.path.join(FIXTURES, name)
        if check_only:
            if not os.path.isfile(path):
                diffs.append("%s：檔案不存在" % name)
                continue
            with io.open(path, encoding="utf-8") as fh:
                if fh.read() != text:
                    diffs.append("%s：磁碟內容與生成結果不同" % name)
        else:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)

    if check_only:
        if diffs:
            print("❌ %d 個樣本與生成器不同步：" % len(diffs))
            for d in diffs:
                print("  - %s" % d)
            return 1
        print("✅ %d 個衍生樣本與生成器一致。" % len(outputs))
        return 0

    print("已由 %s／%s／%s 生成 %d 個衍生樣本："
          % (os.path.basename(BASE), os.path.basename(LAND_BASE),
             os.path.basename(INHERIT_BASE), len(outputs)))
    for name, _t in outputs:
        print("  %s" % name)
    print("（good_report.md、good_nosearch_report.md、chinese_index_na.md、good_landscape.md、"
          "good_inherited_report.md 是手寫基準，未被覆寫）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
