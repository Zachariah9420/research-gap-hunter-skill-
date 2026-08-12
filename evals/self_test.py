#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_test.py — 對 format_check.py 跑固定樣本，核對每個樣本該過還是該壞。

沒有網路、沒有金鑰、沒有 LLM，秒級完成。改動 format_check.py 之後一定要跑。

每個壞樣本相對於 good_report.md 只壞掉**一個維度**，所以它應該剛好觸發
**一個** check id。若某個壞樣本觸發了兩個以上的 check，代表查核規則彼此重疊，
失敗訊息就無法定位缺陷——那本身就是要修的東西，不是可以忽略的雜訊。

用法：
    python evals/self_test.py

離開碼：0 全數符合預期；1 有任何一項不符。
"""

import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "format_check.py")
FIXTURES = os.path.join(HERE, "fixtures")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# fixture -> (expected exit code, expected set of check ids)
# 每個 check id 都要有一個專屬樣本；沒有樣本的 check 等於沒有被測過。
EXPECTED = [
    ("good_report.md", 0, set()),
    # SKILL.md 另外規定了一種合規輸出：完全沒有檢索工具時的階 3 降級報告
    # （零個存活候選、全部進待確認、任何一節都不得出現判定）。
    # 它也必須是綠的，否則查核器在跟自己的規格打架。
    ("good_nosearch_report.md", 0, set()),
    # 括號態〔待驗證〕後面接補充語，是 SKILL.md 的合法寫法，必須是綠的。
    ("bracketed_verdict_ok.md", 0, set()),
    # 敘事型文件：報告本體用 report-start／report-end 包起來，區塊外的教學文字
    # （包含它為了警告而引用的斷言措辭）不受查核。必須是綠的。
    ("narrative_wrapper.md", 0, set()),
    # SKILL.md〈互鎖的例外〉：第三節裡〔未驗證〕與「卡在術語」的〔UNSEARCHABLE〕
    # 不需要第六節的對應列——它們之所以在第三節，正是因為沒被搜過。這一份是誠實的
    # 「只搜了一部分」的報告，必須是綠的；它一旦轉紅，就代表查核器又在逼報告去寫
    # 一次沒跑過的搜尋，而最便宜的變綠方式是捏造一列檢索紀錄。
    ("unsearched_pending.md", 0, set()),
    # 表頭〈中文索引〉的第三個合法值（不適用）＋一份與 good_report.md 不同基底的
    # 手寫報告。必須是綠的：兩個例外都不成立的題目不該被逼著掛覆蓋率警語。
    ("chinese_index_na.md", 0, set()),
    # 第二種文件形狀：領域地形報告。它不判新穎性，所以缺口報告那一套規則裡
    # 大部分在它身上沒有對象；查核器必須從第一行的 H1 認出型別再套規則。
    # 這一份必須是綠的，否則就是拿缺口報告的門檻去量一份不下判決的報告。
    ("good_landscape.md", 0, set()),
    # 同一個模式的另一種地形：一個**比年份視窗還年輕**的領域。六個家族有五個讀到的
    # 那一頁幾乎全部落在切分年之後，於是〔判不出〕的三項條件同時成立，那五族標
    # 〔判不出〕是正確答案。它必須是綠的——否則新增的第六個值只在紅樣本裡出現過，
    # 「條件滿足時它是被接受的」就是一句沒有人驗過的話，而一個永遠不被接受的值
    # 等於把作者逼回四個值裡挑措辭，也就是這次改動要消滅的東西。
    ("good_landscape_young.md", 0, set()),
    # 兩個模式接起來的那一份：表頭帶〈地形來源〉，第一節同時有本輪量化的預設、
    # 承接自地形但未補取樣框的預設、以及承接後補了取樣框的預設。它必須是綠的，
    # 而且是「承接後補了框的預設拿去當 G3 輸入」這一種綠——那正是 SKILL.md
    # 允許的完整路徑，一旦轉紅，照規格寫的報告就變成不合格。
    ("good_inherited_report.md", 0, set()),
    # 承接未補框的預設躺在第一節、沒有餵給任何 G3：ASSUM-01 不得跟它要取樣框，
    # TRACE-01 也不得跟它要第六節的對應列（它不是這一輪搜出來的）。
    ("inherited_unframed_ok.md", 0, set()),
    # 預設行的**形狀**現在不決定任何一條規則的適用性（效力與取樣框都從 rgh-block 讀，
    # 散文那一行只被問 containment）。這一份把那句話釘成可執行的東西：A3 改寫成
    # SKILL.md 第 1 步自己用來展示的引用區塊形狀，而它正是 C02 反轉的那一條，
    # 所以綠燈是**有內容的綠**——見下面的解析回讀。
    ("assumption_blockquote_ok.md", 0, set()),
    # SKILL.md〈偵察模式〉規定的第三種合規輸出：沒有跑第 1 步、不產生存活候選、
    # 不執行淘汰，所以它是**唯一**可以交出 `"assumptions": []` 的缺口報告。
    # 它必須是綠的：那條豁免的兩側都要有樣本，否則「空清單一律違規」會把一份
    # 照規格寫的偵察報告判成不合格，而那是查核器在跟自己的規格打架。
    ("good_recon_report.md", 0, set()),
    ("missing_trace_section.md", 1, {"STRUCT-01"}),
    ("no_tool_tier.md", 1, {"STRUCT-02"}),
    # ---- rgh-block：載體、JSON、schema、結算（EXACT，沒有寬容可談）--------
    # 沒有區塊＝第一節與結算完全沒有被查過，而沒有被查過不能長得像通過。
    ("block_absent.md", 1, {"BLOCK-01"}),
    # 「整份恰好一個」單獨就關掉一整類誘餌：放一個算術自洽的假區塊搶走對帳。
    ("block_duplicate.md", 1, {"BLOCK-01"}),
    ("block_bad_json.md", 1, {"BLOCK-01"}),
    # 結算在區塊裡就對不起來時，查核器**不再**拿它去跟散文列數比對——
    # 一個缺陷不該變成三句話，其中兩句還會把作者送去改沒有壞的東西。
    ("block_settlement_mismatch.md", 1, {"BLOCK-01"}),
    # 預設的效力是一個四值列舉，寫錯就是違規，不是靜默降級。
    ("block_status_unknown.md", 1, {"ASSUM-01"}),
    # 空的 `assumptions` 是一個**宣稱**（第 1 步整步沒跑），不是缺席——所以它查得動。
    # 這一份與 good_recon_report.md 是同一條規則的兩側：宣告了偵察模式的可以空，
    # 沒宣告的不行。只釘一側的話，那一側會慢慢變成全部。
    ("recon_undeclared_empty.md", 1, {"BLOCK-01"}),
    # 地形報告不寫區塊（SKILL.md〈rgh-block〉）。寫了就是一塊沒有任何規則會驗的區域，
    # 而以前它同時被剝出散文與禁語掃描——不被驗證、也不被掃描，是這個模式最不能有的東西。
    ("landscape_stray_block.md", 1, {"BLOCK-01"}),
    # 編號用全形數字寫。以前 `\d` 讓它通過形狀測試，接著 NFKC 只發生在 containment 那一側，
    # 於是三筆 finding 指著三行沒有壞的東西。這一份釘的是「訊息要落在壞掉的那個東西上」。
    ("block_fullwidth_id.md", 1, {"ASSUM-01"}),
    # ---- ANCHOR-01：區塊寫的字，散文裡要找得到（containment，不是解析）----
    ("anchor_prose_missing.md", 1, {"ANCHOR-01"}),
    # 錨點藏在 HTML 註解裡不算「出現在散文」。這一份與先前那個「檔首註解假結算」
    # 是同一個機制，所以剝註解是正規化的強制步驟。
    ("anchor_in_html_comment.md", 1, {"ANCHOR-01"}),
    # 反方向：散文寫了、區塊漏了。containment 只問區塊→散文，這一條補另一邊。
    ("anchor_orphan_assumption.md", 1, {"ANCHOR-01"}),
    # 錨點的第二個問題：**位置**。整條預設行從第一節搬進候選底下，字一個都沒改，
    # 所以「文件裡有沒有這個字串」問不出任何問題。SKILL.md 的錨點規則寫的是
    # 「出現在第一節那條預設行上」——這一份釘的是那半句，也是一條回歸樣本
    # （重構之前的樹抓得到它，重構之後一度抓不到）。
    ("anchor_line_relocated.md", 1, {"ANCHOR-01"}),
    # 錨點的第三個問題：**掛在哪一條上**。標籤離開它該在的那一行（正向），
    # 以及標籤出現在 status 對不上的那一行（反向）。兩側各一份：只釘正向的話，
    # 把標籤從一條撕下來貼到另一條上只會被說中一半。
    ("anchor_label_off_line.md", 1, {"ANCHOR-01"}),
    ("anchor_label_wrong_status.md", 1, {"ANCHOR-01"}),
    ("count_mismatch.md", 1, {"COUNT-01"}),
    ("recon_mismatch.md", 1, {"RECON-01"}),
    ("bad_verdict.md", 1, {"VERDICT-01"}),
    ("done_in_survivors.md", 1, {"VERDICT-02"}),
    ("assumption_no_frame.md", 1, {"ASSUM-01"}),
    # 承接後宣稱「已補取樣框」（status=inherited_framed），取樣框卻不完整——
    # 補框一旦宣稱出去，就與本輪量化的預設同標準。這一份釘的是 ASSUM-01 的承接臂
    # （訊息的退路也不得是〔印象，未驗證〕：效力相同，但來源要留著）。
    ("inherited_framed_partial.md", 1, {"ASSUM-01"}),
    ("impression_as_g3.md", 1, {"ASSUM-02"}),
    # 承接未補框的預設被拿去當 G3 輸入。這一份釘的是 ASSUM-02 的承接臂，
    # 連同它的訊息：那一條**在**第一節裡，說它「不存在」會把讀者送去找錯東西。
    ("inherited_unframed_as_g3.md", 1, {"ASSUM-02"}),
    ("missing_evidence_field.md", 1, {"EVID-01"}),
    ("no_evidence.md", 1, {"EVID-02"}),
    ("vague_evidence.md", 1, {"EVID-03"}),
    ("neighbour_no_id.md", 1, {"NEIGH-01"}),
    ("unnamed_kill.md", 1, {"KILL-01"}),
    ("crowded_two_papers.md", 1, {"KILL-02"}),
    ("done_no_quote.md", 1, {"KILL-03"}),
    ("kill_no_identifier.md", 1, {"ID-01"}),
    ("untraced_candidate.md", 1, {"TRACE-01"}),
    # 同一條互鎖的另一臂：第一節的預設。豁免由區塊的 status 決定，所以兩邊都要有樣本
    # ——只釘豁免那一側的話，「framed 一定要有對應列」就是一句沒人驗過的話。
    ("assumption_untraced.md", 1, {"TRACE-01"}),
    ("trace_placeholder_query.md", 1, {"TRACE-02"}),
    ("assertive_language.md", 1, {"LANG-01"}),
    ("no_search_with_verdicts.md", 1, {"TIER-01"}),
    # 地形報告的規則集（刻意薄，理由見 evals/README.md）。前五條是它專屬的，
    # 後幾條是跨模式共用的規則——共用不是宣告出來的，是這些樣本釘住的：
    # 少了它們，「LANG-01／STRUCT-02／PARSE-01／SECT-01 在地形模式也有效」就只是一句沒人驗過的話。
    ("landscape_no_disclaimer.md", 1, {"LHEAD-01"}),
    ("landscape_verdict_word.md", 1, {"LVOCAB-01"}),
    ("landscape_no_cost.md", 1, {"LCOST-01"}),
    ("landscape_status_asserted.md", 1, {"LSTAT-01"}),
    ("landscape_orphan_assumption.md", 1, {"LWALL-01"}),
    ("landscape_assertive.md", 1, {"LANG-01"}),
    ("landscape_no_tier.md", 1, {"STRUCT-02"}),
    # STRUCT-02 的第二個臂：〈文獻工具〉不是佔位符，而是**跨欄照抄**——地形報告寫了
    # 降級階梯表 hunt 那一欄的階 0 字串，於是表頭宣告了三件這個模式被禁止做的檢查。
    # 舊契約（非佔位符即可）看不到它，而每一份地形報告都是照規格逐字抄來的。
    ("landscape_hunt_tier_string.md", 1, {"STRUCT-02"}),
    # LSTAT-01 的三個新臂，一份一種，因為它們的條件互相獨立：
    #   glued        兩段子句被「其中」黏回一段（＝規格改掉的那個舊句型本身）
    #   n_exceeds_m  第二段的 N > M，而 N 數在 M 那一頁裡——這條算術在舊句型下不存在
    #   undecidable  〔判不出〕的方向（第二項）與多數（第三項）條件
    # 方向那一份只能從 good_landscape_young.md 長出來（第三項在那裡是成立的），
    # 多數那一份只能從 good_landscape.md 長出來（第二項在那裡不可能成立）——
    # 兩個臂在同一份基準上會一起亮，而一起亮的樣本證明不了是哪一個亮的。
    ("landscape_status_glued.md", 1, {"LSTAT-01"}),
    ("landscape_status_n_exceeds_m.md", 1, {"LSTAT-01"}),
    ("landscape_undecidable_alone.md", 1, {"LSTAT-01"}),
    ("landscape_undecidable_wrong_direction.md", 1, {"LSTAT-01"}),
    # 讀不進來的行、列與表。這一條規則守的不是「報告寫錯了什麼」，是「查核器讀不到什麼」——
    # 以前這些全部靜默丟掉，於是缺陷要嘛完全不出現，要嘛偽裝成計數對不起來（RECON-01
    # 說「結算寫已淘汰 6、第四節實際有 5 列」，而 6 是對的、壞的是那一列的形狀）。
    # 每一份釘一種讀不到的方式，一份一種，因為 PARSE-01 是**定位**規則：它的一個臂失效
    # 不是弱化一條檢查，是把底下每一條檢查一起關掉，所以每個臂都要有自己的樣本與突變體。
    ("candidate_head_unreadable.md", 1, {"PARSE-01"}),
    ("kill_row_short.md", 1, {"PARSE-01"}),
    ("landscape_wall_row_short.md", 1, {"PARSE-01"}),
    ("kill_row_no_verdict.md", 1, {"VERDICT-01"}),
    # 「掉了行首那一根直線」的資料列。刪一個字元，整列在上一版是無聲消失的：
    # parse_table 只吃 `|` 開頭的行，ROWISH_RE 也錨在行首。這一份釘的是那一根直線。
    ("glance_row_lost_pipe.md", 1, {"PARSE-01"}),
    # 整張表讀不到（貼回渲染後的版本＝連表頭都沒有直線，或整張表沒寫）。
    # 這一份是「節名只能多報一筆、不能決定要不要解析」那條界線的樣本。
    ("glance_table_gone.md", 1, {"PARSE-01"}),
    # 同一條規則的文件層那一臂：不問那張表在哪一節、那一節叫什麼名字。
    # 「表被貼成純文字」與「節標題被改寫」同時發生時，只剩這一臂看得到。
    ("landscape_no_glance.md", 1, {"PARSE-01"}),
    # 標題認不出來、但區塊形狀認得出來的兩種：家族少了 F 編號、候選少了「候選」二字。
    # 兩份都必須只報 PARSE-01——區塊照樣建起來，所以 LWALL-01／COUNT-01／RECON-01
    # 不得跟著響；它們一響就代表查核器又在把人送去改對帳數字，而壞的是一行標題。
    ("family_head_no_id.md", 1, {"PARSE-01"}),
    ("candidate_head_no_keyword.md", 1, {"PARSE-01"}),
    # 同一條規則的另一個臂：報告結構藏進圍欄區塊裡。圍欄在讀者眼裡是程式碼，
    # 查核器也不保證把它當結構讀——**兩邊都不算的區域什麼都裝得下**。
    ("fenced_assumption_line.md", 1, {"PARSE-01"}),
    # 同一個缺陷、換一個圍欄符號。`~~~` 在讀者眼裡與 ``` 一模一樣，所以只認一種
    # 就是留一個一字元的繞道；這一份釘的就是「兩種都算」。
    ("tilde_fenced_assumption_line.md", 1, {"PARSE-01"}),
    # 區段標題被改寫。兩種模式各一份：缺口報告的第一節（改名後預設整批消失，
    # 而 G3 候選會收到「指到第一節沒有的預設」那句誤導）、地形報告的一眼表
    # （改名後 LSTAT-01 與 LCOST-01 對每一列同時熄燈）。兩份都必須**只**報 SECT-01——
    # 底下的規則照常執行，所以除了標題本身以外不該有第二筆。
    ("consensus_section_renamed.md", 1, {"SECT-01"}),
    ("trace_section_renamed.md", 1, {"SECT-01"}),
    ("landscape_section_renamed.md", 1, {"SECT-01"}),
]

# 手寫的基準樣本；其餘全部由 make_fixtures.py 生成。
HANDWRITTEN = {"good_report.md", "good_nosearch_report.md", "chinese_index_na.md",
               "good_landscape.md", "good_landscape_young.md",
               "good_inherited_report.md", "good_recon_report.md"}
# 「差幾行」是單一維度的**代理指標**，而有三種缺陷它算不準。豁免掉的是這個代理，
# 不是「只壞一個維度」那條規則本身——三份都由 make_fixtures.py 生成，所以單一維度
# 照樣是被建構出來的，不是靠肉眼維持。每一份的理由不同，各自寫出來：
#   narrative_wrapper.md          整份報告被包進敘事文字，本來就不是「壞掉一行」
#   landscape_stray_block.md      一個圍欄區塊最少三行，區塊本身就是那一個維度
#   tilde_fenced_assumption_line.md  `~~~` 的開頭與結尾是同一個字串，基準裡兩個都沒有，
#                                 於是同一個構造被這個指標數成兩行（```` ``` ```` 那一份
#                                 只算一行，因為基準裡本來就有 ``` ——差別在基準，不在缺陷）
LINE_COUNT_EXEMPT = {"narrative_wrapper.md", "landscape_stray_block.md",
                     "tilde_fenced_assumption_line.md"}

# 敘事型文件的處理方式（見 evals/README.md〈敘事型文件〉）：
# 報告本體用這兩個標記包起來，查核器只查標記之內。examples/ 底下的走查檔
# 若已經標了，就必須是綠的；還沒標的話這裡只會提醒，不會假裝它被查過。
# 清單從磁碟掃出來，不寫死檔名：新增一份走查而忘了加進來，等於那份沒被查過。
EXAMPLES_DIR = os.path.join(os.path.dirname(HERE), "examples")
# 要的是真的標記，不是在內文裡提到這個標記；所以連 <!-- --> 一起比對。
BLOCK_MARK = "<!-- format-check: report-start -->"


def read_back(fc, path):
    """把一份樣本讀回解析結果，順便拿到它的 check id 集合。

    綠燈證明不了「讀到了」——靜默丟掉一行也是綠的。回讀是這個套件唯一分得出
    「乾淨」與「根本沒讀到」的辦法。
    """
    with io.open(path, encoding="utf-8") as fh:
        rep = fc.parse_report(fh.read())
    checker = fc.LandscapeChecker if rep.mode == "landscape" else fc.Checker
    ids = set(f["check"] for f in checker(rep, path).run())
    return rep, ids


def run_checker(path, as_json=True):
    cmd = [sys.executable, CHECKER, path]
    if as_json:
        cmd.append("--json")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
    )
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    return proc.returncode, out, err


def main():
    failures = []
    print("format_check.py 自我測試（%d 個樣本，無網路）\n" % len(EXPECTED))
    print("%-24s %-6s %-6s %s" % ("fixture", "exit", "預期", "check ids"))
    print("-" * 78)

    for name, want_code, want_checks in EXPECTED:
        path = os.path.join(FIXTURES, name)
        if not os.path.isfile(path):
            failures.append("%s：樣本檔不存在" % name)
            print("%-24s %-6s %-6s 檔案不存在" % (name, "-", want_code))
            continue

        code, out, err = run_checker(path)
        try:
            data = json.loads(out)
        except ValueError:
            failures.append("%s：--json 輸出不是合法 JSON（stderr: %s）" % (name, err.strip()[:120]))
            print("%-24s %-6s %-6s JSON 解析失敗" % (name, code, want_code))
            continue

        got_checks = set(f["check"] for f in data["findings"])
        ok = (code == want_code) and (got_checks == want_checks)

        print("%-24s %-6s %-6s %s%s"
              % (name, code, want_code,
                 " ".join(sorted(got_checks)) or "（無）",
                 "" if ok else "   <-- 不符"))

        if code != want_code:
            failures.append("%s：離開碼 %d，預期 %d" % (name, code, want_code))
        if got_checks != want_checks:
            failures.append(
                "%s：check ids %s，預期 %s"
                % (name, sorted(got_checks) or "[]", sorted(want_checks) or "[]")
            )
        if data["ok"] != (not want_checks):
            failures.append("%s：JSON 的 ok 欄位與預期不符" % name)

        # 每一筆 finding 都要能定位：非空 check、正整數行號、非空訊息
        for f in data["findings"]:
            if not f.get("check"):
                failures.append("%s：有 finding 缺 check id" % name)
            if not isinstance(f.get("line"), int) or f["line"] < 1:
                failures.append("%s：check %s 的行號無效（%r）" % (name, f.get("check"), f.get("line")))
            if not f.get("message"):
                failures.append("%s：check %s 缺訊息" % (name, f.get("check")))

        # 人類可讀模式必須與 --json 給出一致的離開碼
        code_h, out_h, _ = run_checker(path, as_json=False)
        if code_h != want_code:
            failures.append("%s：非 JSON 模式離開碼 %d，預期 %d" % (name, code_h, want_code))
        if want_checks and not any(c in out_h for c in want_checks):
            failures.append("%s：人類可讀輸出沒有印出 check id" % name)

    # 讀檔錯誤要回 2，不能跟「有違規」的 1 混在一起
    missing = os.path.join(FIXTURES, "__does_not_exist__.md")
    code, _out, _err = run_checker(missing)
    print("-" * 78)
    print("%-24s %-6s %-6s （不存在的檔案應回 2）" % ("__does_not_exist__.md", code, 2))
    if code != 2:
        failures.append("不存在的檔案：離開碼 %d，預期 2" % code)

    # 互鎖的例外，用程式釘住而不是靠散文宣稱。
    # SKILL.md〈互鎖的例外〉：承接自地形、且尚未補取樣框的預設不需要第六節的對應列
    # ——它不是這一輪搜出來的，逼它附檢索紀錄就是逼報告去寫一次沒跑過的搜尋。
    # 豁免的**依據**這一輪換了（從散文的括號標籤換成區塊的 status），理由一個字沒變；
    # 而依據一換，「這份樣本真的沒有那一列」就更該直接讀，不能靠綠燈推。
    sys.path.insert(0, HERE)
    try:
        import format_check as fc
    except ImportError as exc:
        failures.append("無法匯入 format_check 驗證互鎖例外：%s" % exc)
    else:
        print("")
        for name in ("good_inherited_report.md", "inherited_unframed_ok.md"):
            p = os.path.join(FIXTURES, name)
            if not os.path.isfile(p):
                failures.append("互鎖例外：樣本 %s 不存在" % name)
                continue
            rep, ids = read_back(fc, p)
            unframed = [a for a in rep.assumptions if a.get("status") == "inherited"]
            if not unframed:
                failures.append("%s：區塊裡沒有任何 status=inherited 的預設，"
                                "互鎖例外在這份樣本上沒有對象" % name)
                continue
            logged = []
            for a in unframed:
                pat = re.compile(r"(?<![A-Za-z0-9])%s(?![0-9])" % re.escape(a["id"]), re.I)
                for r in rep.trace_rows:
                    if pat.search(fc.strip_md(r.get("candidate", ""))):
                        logged.append((a["id"], r["_line"]))
            print("互鎖例外：%s 有 %d 條 status=inherited 的預設（%s），第六節對應列 %d 筆（應為 0）"
                  % (name, len(unframed), "、".join(a["id"] for a in unframed), len(logged)))
            if logged:
                failures.append(
                    "%s：承接未補框的預設 %s 在第六節有對應列（第 %d 行）——"
                    "這份樣本已經證明不了互鎖例外，它只是有紀錄所以沒被罰"
                    % (name, logged[0][0], logged[0][1]))

        # 反過來的那一半：status 是 framed／inherited_framed 的預設**必須**有
        # `第1步-推翻A<n>` 的對應列。豁免是靠 status 分流的，所以兩邊都要有樣本釘住，
        # 否則「豁免」會退化成「這條規則對誰都沒開過火」。
        p = os.path.join(FIXTURES, "good_inherited_report.md")
        rep, _ids = read_back(fc, p)
        framed = [a for a in rep.assumptions
                  if a.get("status") in ("framed", "inherited_framed")]
        cells = [re.sub(r"\s+", "", fc.strip_md(r.get("candidate", "")))
                 for r in rep.trace_rows]
        missing = [a["id"] for a in framed
                   if not any(("第1步-推翻" + a["id"]) in c for c in cells)]
        print("互鎖正面：good_inherited_report.md 有 %d 條 framed／inherited_framed 的預設（%s），"
              "第六節都有對應列（缺 %d 筆）"
              % (len(framed), "、".join(a["id"] for a in framed), len(missing)))
        if not framed:
            failures.append("good_inherited_report.md：沒有任何 framed 的預設，"
                            "TRACE-01 的預設臂在這份樣本上沒有對象")
        if missing:
            failures.append("good_inherited_report.md：預設 %s 沒有第六節的對應列，"
                            "但這份樣本應該是綠的" % "、".join(missing))

        # 綠燈證明不了「讀到了」。這一份樣本的價值全在一句話上：**預設行的形狀
        # 不再決定任何一條規則的適用性**。所以要回讀三件事：A3 真的在區塊裡、
        # 被歸成 inherited_framed、而且真的有一個 G3 候選指著它——三件都成立，
        # 那個引用區塊寫法的綠燈才是「效力仍然被判對了」的證據，而不是「沒人看它」。
        print("")
        for name, aid, want_status in (("assumption_blockquote_ok.md", "A3", "inherited_framed"),):
            p = os.path.join(FIXTURES, name)
            if not os.path.isfile(p):
                failures.append("預設行形狀：樣本 %s 不存在" % name)
                continue
            rep, _ids = read_back(fc, p)
            got = [a for a in rep.assumptions if a.get("id") == aid]
            if not got:
                failures.append("%s：區塊裡沒有預設 %s" % (name, aid))
                continue
            a = got[0]
            if a.get("status") != want_status:
                failures.append("%s：預設 %s 的 status 是 %r，應為 %r"
                                % (name, aid, a.get("status"), want_status))
            fed = [c for c in rep.candidates
                   if "gap_type" in c["fields"]
                   and aid in fc.strip_md(c["fields"]["gap_type"][1]).upper()]
            if not fed:
                failures.append(
                    "%s：沒有任何 G3 候選指到 %s，這份樣本的綠燈因此不含資訊"
                    "（改壞那一行也不會轉紅）" % (name, aid))
            # 散文那一行被改寫成引用區塊之後，錨點仍然要找得到——這才是「形狀無關」
            # 真正的意思：規則沒有停用，只是不再看那一行長什麼樣子。
            if "ANCHOR-01" in _ids:
                failures.append("%s：改寫成引用區塊之後 ANCHOR-01 開火了——"
                                "正規化沒有吃掉 `> `，這是假紅燈" % name)
            print("預設行形狀：%s 的 %s 在區塊裡（status=%s），有 %d 個 G3 候選指著它，"
                  "散文改寫成引用區塊後錨點仍然找得到"
                  % (name, aid, a.get("status"), len(fed)))

        # 措辭漂移那一類：以前把 `- 預設 A1：…` 改寫成 `- 前提 A1：…` 會讓那一條
        # 整條從查核裡消失（預設 2→0、unreadable 0、離開碼 0、零 finding），而那是
        # 這批洞裡唯一**不必刻意構造就會發生**的一個。現在預設的身分是 JSON 欄位，
        # 改寫散文只會讓錨點找不到——這裡就地構造一次，確認它是紅的。
        print("")
        p = os.path.join(FIXTURES, "good_nosearch_report.md")
        with io.open(p, encoding="utf-8") as fh:
            original = fh.read()
        drifted = original.replace("- 預設 A1：", "- 前提 A1：")
        if drifted == original:
            failures.append("措辭漂移：在 good_nosearch_report.md 裡找不到 `- 預設 A1：`，"
                            "這個檢查因此沒有對象")
        else:
            ids = set(f["check"] for f in fc.Checker(fc.parse_report(drifted), p).run())
            print("措辭漂移：`- 預設 A1：` → `- 前提 A1：` ⇒ %s（應含 ANCHOR-01）"
                  % (" ".join(sorted(ids)) or "（無）"))
            if "ANCHOR-01" not in ids:
                failures.append(
                    "措辭漂移：把預設行改寫成「前提 A1」之後沒有任何 ANCHOR-01——"
                    "那一條的編號與那句話都從查核裡消失了，正是這次重構要關掉的那一類")

        # 偵察模式豁免的**第二個條件**。第一個條件（表頭逐字宣告偵察抽樣）由
        # recon_undeclared_empty.md 釘住；第二個沒辦法用一次替換表達，就地構造：
        # 拿一份有 3 個存活候選、6 個淘汰的完整獵捕報告，宣告自己是偵察抽樣、
        # 再把預設清單清空——如果一句宣告就能買到豁免，這裡會是綠的，而那等於在
        # 剛關上的門旁邊開一扇窗。SKILL.md〈偵察模式〉同時規定了那一份長什麼樣
        # （不產生存活候選、不執行淘汰，所以結算的存活與已淘汰都是 0），
        # 而那兩個數字又被 COUNT-01／RECON-01 對到散文的實際列數——它不是自我宣告。
        print("")
        p = os.path.join(FIXTURES, "good_report.md")
        with io.open(p, encoding="utf-8") as fh:
            full = fh.read()
        claimed = full.replace("**模式**：完整獵捕", "**模式**：偵察抽樣（非新穎性判定）")
        emptied = re.sub(r'"assumptions": \[.*?\n\]', '"assumptions": []', claimed, flags=re.S)
        if claimed == full or emptied == claimed:
            failures.append("偵察豁免：在 good_report.md 裡改不出「宣告偵察模式＋空預設清單」"
                            "這一份，這個檢查因此沒有對象")
        else:
            ids = set(f["check"] for f in fc.Checker(fc.parse_report(emptied), p).run())
            print("偵察豁免：宣告偵察抽樣但存活 3／已淘汰 6，且 `assumptions` 清空 ⇒ %s"
                  "（應含 BLOCK-01）" % (" ".join(sorted(ids)) or "（無）"))
            if "BLOCK-01" not in ids:
                failures.append(
                    "偵察豁免：一份存活 3、已淘汰 6 的報告只要宣告一行〈模式：偵察抽樣〉"
                    "就能交出空預設清單而不被說——那條豁免因此是一扇門，不是一個條件")

        # 標題改名的那三份：綠燈證明不了「內容還讀得到」，紅燈也只證明有一筆 SECT-01。
        # 真正要釘的是「改名之後底下的東西照樣被讀進來」——所以直接回讀解析結果。
        # 第一節那一份現在釘的是**形狀定位本身**：節名認不出來時，是「裡面有 預設 A<n>」
        # 這個 token 掃描把它認回來的，而不是有人放棄。
        print("")
        for name, attr, least in (("trace_section_renamed.md", "trace_rows", 22),
                                  ("landscape_section_renamed.md", "glance_rows", 7)):
            p = os.path.join(FIXTURES, name)
            if not os.path.isfile(p):
                failures.append("區段改名：樣本 %s 不存在" % name)
                continue
            rep, _ids = read_back(fc, p)
            got = len(getattr(rep, attr))
            print("區段改名：%s 改名後仍讀到 %s %d 筆（應為 %d），renamed_sections=%d"
                  % (name, attr, got, least, len(rep.section_renames)))
            if got < least:
                failures.append(
                    "%s：改名之後只讀到 %s %d 筆（應為 %d）——"
                    "SECT-01 報了，但底下的東西還是消失了，那條規則因此只是裝飾"
                    % (name, attr, got, least))
            if not rep.section_renames:
                failures.append("%s：解析結果沒有記到任何被改名的區段" % name)
        p = os.path.join(FIXTURES, "consensus_section_renamed.md")
        rep, _ids = read_back(fc, p)
        by_shape = [s for s in rep.section_renames if s["kind"] == "consensus"]
        print("區段改名：consensus_section_renamed.md 的第一節靠形狀認回來 %d 筆"
              "（renamed_sections=%d）" % (len(by_shape), len(rep.section_renames)))
        if not by_shape:
            failures.append(
                "consensus_section_renamed.md：改名之後沒有任何一節被**靠形狀**認成第一節"
                "——SECT-01 就退化成「認不出來所以不報」，而那正是它存在要擋的東西")

    # 樣本的單一維度保證：衍生樣本與它自己的基準只能差在少數幾行。
    # 「它自己的基準」從 make_fixtures.py 推導，不在這裡另寫一份對照表——
    # 兩份對照表遲早會各自漂移，而漂移的那一天沒有人會發現。
    sys.path.insert(0, HERE)
    try:
        import make_fixtures
    except ImportError as exc:
        failures.append("無法匯入 make_fixtures 取得基準對照：%s" % exc)
        bases = {}
    else:
        bases = make_fixtures.derived_bases()
    base_lines = {}
    for name, _c, _want in EXPECTED:
        if name in HANDWRITTEN or name in LINE_COUNT_EXEMPT:
            continue
        base_name = bases.get(name)
        if not base_name:
            failures.append("%s：make_fixtures.py 沒有宣告它的基準樣本" % name)
            continue
        if base_name not in base_lines:
            bp = os.path.join(FIXTURES, base_name)
            if not os.path.isfile(bp):
                continue
            with io.open(bp, encoding="utf-8") as fh:
                base_lines[base_name] = set(fh.read().splitlines())
        p = os.path.join(FIXTURES, name)
        if not os.path.isfile(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        # 允許：1 行被改 + 1 行說明本檔改了哪裡
        novel = [ln for ln in lines if ln not in base_lines.get(base_name, set())]
        if len(novel) > 2:
            failures.append(
                "%s：與 %s 差了 %d 行，樣本應只動一個維度" % (name, base_name, len(novel))
            )

    # 單一維度不能只靠肉眼：所有衍生樣本必須與 make_fixtures.py 的輸出逐字相同。
    # 手改樣本會在這裡被抓到——手改的樣本遲早會壞第二個維度。
    gen = subprocess.run(
        [sys.executable, os.path.join(HERE, "make_fixtures.py"), "--check"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    gen_out = gen.stdout.decode("utf-8", "replace").strip()
    print("")
    print(gen_out or gen.stderr.decode("utf-8", "replace").strip())
    if gen.returncode != 0:
        failures.append("衍生樣本與 make_fixtures.py 不同步（見上）")

    # examples/ 底下的走查是敘事文件，不是報告。標了報告區塊就該是綠的；
    # 沒標的話它目前不受查核——這件事要講出來，不能讓人以為它被驗過。
    for name in sorted(os.listdir(EXAMPLES_DIR)) if os.path.isdir(EXAMPLES_DIR) else []:
        if not name.endswith(".md"):
            continue
        path = os.path.join(EXAMPLES_DIR, name)
        with io.open(path, encoding="utf-8") as fh:
            example_text = fh.read()
        if BLOCK_MARK in example_text:
            code, out, _err = run_checker(path)
            print("examples/%s（已標報告區塊）：離開碼 %d" % (name, code))
            if code != 0:
                try:
                    ids = sorted(set(f["check"] for f in json.loads(out)["findings"]))
                except ValueError:
                    ids = ["（輸出不是 JSON）"]
                failures.append(
                    "examples/%s 標了報告區塊卻不合格：%s" % (name, ", ".join(ids))
                )
        else:
            print("⚠️ examples/%s 沒有 %s 標記，"
                  "本次未受查核（見 evals/README.md〈敘事型文件〉）" % (name, BLOCK_MARK))

    # 覆蓋率：format_check.py 宣告的每個 check 都必須有專屬樣本。
    # 沒有樣本的 check 只是「good_report.md 剛好沒踩到」，不算被測過。
    sys.path.insert(0, HERE)
    try:
        import format_check
    except ImportError as exc:
        failures.append("無法匯入 format_check 做覆蓋率檢查：%s" % exc)
    else:
        declared = set(format_check.CHECK_DESCRIPTIONS)
        covered = set()
        for _n, _c, checks in EXPECTED:
            covered |= checks
        uncovered = sorted(declared - covered)
        stray = sorted(covered - declared)
        print("check 覆蓋率：%d / %d" % (len(declared & covered), len(declared)))
        if uncovered:
            failures.append("這些 check 沒有專屬樣本，等於沒被測過：%s" % ", ".join(uncovered))
        if stray:
            failures.append("EXPECTED 指到不存在的 check id：%s" % ", ".join(stray))

    print("")
    if failures:
        print("❌ %d 項不符：\n" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("✅ 全部符合預期。")
    print("   提醒：這只證明查核器抓得到**格式**缺陷，不證明任何一份報告的文獻是真的。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
