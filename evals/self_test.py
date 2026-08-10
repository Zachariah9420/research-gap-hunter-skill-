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
    # 有十九條在它身上沒有對象；查核器必須從第一行的 H1 認出型別再套規則。
    # 這一份必須是綠的，否則就是拿缺口報告的門檻去量一份不下判決的報告。
    ("good_landscape.md", 0, set()),
    # 兩個模式接起來的那一份：表頭帶〈地形來源〉，第一節同時有本輪量化的預設、
    # 承接自地形但未補取樣框的預設、以及承接後補了取樣框的預設。它必須是綠的，
    # 而且是「承接後補了框的預設拿去當 G3 輸入」這一種綠——那正是 SKILL.md
    # 允許的完整路徑，一旦轉紅，照規格寫的報告就變成不合格。
    ("good_inherited_report.md", 0, set()),
    # 承接未補框的預設躺在第一節、沒有餵給任何 G3：ASSUM-01 不得跟它要取樣框，
    # TRACE-01 也不得跟它要第六節的對應列（它不是這一輪搜出來的）。
    ("inherited_unframed_ok.md", 0, set()),
    ("missing_trace_section.md", 1, {"STRUCT-01"}),
    ("no_tool_tier.md", 1, {"STRUCT-02"}),
    ("count_mismatch.md", 1, {"COUNT-01"}),
    ("count_inverted.md", 1, {"COUNT-02"}),
    ("recon_mismatch.md", 1, {"RECON-01"}),
    ("bad_verdict.md", 1, {"VERDICT-01"}),
    ("done_in_survivors.md", 1, {"VERDICT-02"}),
    ("assumption_no_frame.md", 1, {"ASSUM-01"}),
    # 承接後宣稱「已補取樣框」，取樣框卻不完整——補框一旦宣稱出去，就與本輪
    # 量化的預設同標準。這一份釘的是 ASSUM-01 的承接臂（訊息也不得叫它改寫成
    # 〔印象，未驗證〕：效力相同，但來源要留著）。
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
    ("trace_placeholder_query.md", 1, {"TRACE-02"}),
    ("assertive_language.md", 1, {"LANG-01"}),
    ("no_search_with_verdicts.md", 1, {"TIER-01"}),
    # 地形報告的規則集（刻意薄，理由見 evals/README.md）。前五條是它專屬的，
    # 後兩條是跨模式共用的規則——共用不是宣告出來的，是這兩份樣本釘住的：
    # 少了它們，「LANG-01／STRUCT-02 在地形模式也有效」就只是一句沒人驗過的話。
    ("landscape_no_disclaimer.md", 1, {"LHEAD-01"}),
    ("landscape_verdict_word.md", 1, {"LVOCAB-01"}),
    ("landscape_no_cost.md", 1, {"LCOST-01"}),
    ("landscape_status_asserted.md", 1, {"LSTAT-01"}),
    ("landscape_orphan_assumption.md", 1, {"LWALL-01"}),
    ("landscape_assertive.md", 1, {"LANG-01"}),
    ("landscape_no_tier.md", 1, {"STRUCT-02"}),
]

# 手寫的基準樣本；其餘全部由 make_fixtures.py 生成。
HANDWRITTEN = {"good_report.md", "good_nosearch_report.md", "chinese_index_na.md",
               "good_landscape.md", "good_inherited_report.md"}
# 這個樣本刻意把基準報告包進敘事文字裡，不適用「只差兩行」的單一維度規則。
WRAPPED = {"narrative_wrapper.md"}

# 敘事型文件的處理方式（見 evals/README.md〈敘事型文件〉）：
# 報告本體用這兩個標記包起來，查核器只查標記之內。examples/ 底下的走查檔
# 若已經標了，就必須是綠的；還沒標的話這裡只會提醒，不會假裝它被查過。
# 清單從磁碟掃出來，不寫死檔名：新增一份走查而忘了加進來，等於那份沒被查過。
EXAMPLES_DIR = os.path.join(os.path.dirname(HERE), "examples")
# 要的是真的標記，不是在內文裡提到這個標記；所以連 <!-- --> 一起比對。
BLOCK_MARK = "<!-- format-check: report-start -->"


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
    # 上面那兩個綠燈只有在「樣本真的沒有那一列」的前提下才是證據；有人日後順手替
    # 它補一列，綠燈就退化成巧合。所以這裡直接讀樣本：確認承接未補框的預設存在、
    # 且第六節沒有它的列——綠燈才是這條例外真的成立的證據。
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
            with io.open(p, encoding="utf-8") as fh:
                rep = fc.parse_report(fh.read())
            unframed = [a for a in rep.assumptions if a["inherited"] and not a["framed"]]
            if not unframed:
                failures.append("%s：解析不到任何〔承接自地形 W…〕未補框的預設，"
                                "互鎖例外在這份樣本上沒有對象（parser 又壞了？）" % name)
                continue
            logged = []
            for a in unframed:
                if not a["aid"]:
                    continue
                pat = re.compile(r"(?<![A-Za-z0-9])%s(?![0-9])" % re.escape(a["aid"]), re.I)
                for r in rep.trace_rows:
                    if pat.search(fc.strip_md(r.get("candidate", ""))):
                        logged.append((a["aid"], r["_line"]))
            print("互鎖例外：%s 有 %d 條承接未補框的預設（%s），第六節對應列 %d 筆（應為 0）"
                  % (name, len(unframed),
                     "、".join(a["aid"] or "（無編號）" for a in unframed), len(logged)))
            if logged:
                failures.append(
                    "%s：承接未補框的預設 %s 在第六節有對應列（第 %d 行）——"
                    "這份樣本已經證明不了互鎖例外，它只是有紀錄所以沒被罰"
                    % (name, logged[0][0], logged[0][1]))

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
        if name in HANDWRITTEN or name in WRAPPED:
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
