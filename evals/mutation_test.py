#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutation_test.py — 證明「是那條規則抓到的」，而不是碰巧。

self_test.py 只證明「壞樣本會紅」。它證明不了紅燈是哪條規則點亮的：
一個樣本可能同時踩到三條規則，而我們以為抓到它的那一條其實從未執行。
這種假覆蓋率比沒有測試更危險——它讓人以為某條規則有效。

本檔的作法：對每一條 check，把它的**判定條件**（不是 self.add 那一行）
在 format_check.py 的**暫存副本**上削弱，然後重跑它的樣本。

    削弱後那個 check id 消失  → 這條規則確實是抓到該樣本的原因（PASS）
    削弱後那個 check id 還在  → 抓到它的另有其人，這條規則沒有被證明有效（FAIL）

削弱的是條件而非回報行，是刻意的：把 self.add 刪掉當然會讓 finding 消失，
那證明不了任何事。動條件才會暴露「另一條規則其實也在抓同一件事」。

原始的 evals/format_check.py 全程唯讀，突變體只寫進 tempfile 建立的暫存目錄。

用法：
    python evals/mutation_test.py
    python evals/mutation_test.py -v      # 連附帶觸發的 check 一起列出

離開碼：0 每條規則都被證明有偵測力；1 有規則無法證明。
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "format_check.py")
FIXTURES = os.path.join(HERE, "fixtures")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# (check id, fixture, 這個突變在削弱什麼, 原始片段, 削弱後片段)
# 原始片段必須在 format_check.py 中「恰好出現一次」，否則突變位置不明確，
# 本檔會直接判為 FAIL——模稜兩可的突變證明不了東西。
MUTATIONS = [
    (
        "STRUCT-01", "missing_trace_section.md",
        "把〈檢索紀錄〉從必要區段清單裡拿掉",
        '        for kind, label in (("survivors", "二、存活候選"), ("pending", "三、待確認"),\n'
        '                            ("killed", "四、已淘汰"), ("trace", "六、檢索紀錄")):',
        '        for kind, label in (("survivors", "二、存活候選"), ("pending", "三、待確認"),\n'
        '                            ("killed", "四、已淘汰")):',
    ),
    (
        "STRUCT-02", "no_tool_tier.md",
        "不再檢查〈文獻工具〉的值是不是佔位符",
        '                if is_placeholder(val):\n                    self.add("STRUCT-02"',
        '                if False:\n                    self.add("STRUCT-02"',
    ),
    (
        "COUNT-01", "count_mismatch.md",
        "不再比對宣告存活數與實際候選區塊數",
        "        if self.rep.declared_survived != actual:",
        "        if False:",
    ),
    (
        "COUNT-02", "count_inverted.md",
        "把「生成數不得小於存活數」的門檻放寬 100",
        "        if self.rep.declared_generated is not None and self.rep.declared_generated < self.rep.declared_survived:",
        "        if self.rep.declared_generated is not None and self.rep.declared_generated < self.rep.declared_survived - 100:",
    ),
    (
        "RECON-01", "recon_mismatch.md",
        "結算數字直接用實際列數回填——等於不再對帳",
        "        n, m, p, q = rep.settlement\n",
        "        n, m, p, q = rep.settlement\n"
        "        m, p, q = len(rep.candidates), len(rep.pending_rows), len(rep.kill_rows)\n"
        "        n = m + p + q\n",
    ),
    (
        "VERDICT-01", "bad_verdict.md",
        "把 NOVEL 當成合法的存活判定",
        'SURVIVOR_VERDICTS = {"ADJACENT", "OPEN", "INCREMENTAL"}',
        'SURVIVOR_VERDICTS = {"ADJACENT", "OPEN", "INCREMENTAL", "NOVEL"}',
    ),
    (
        "VERDICT-02", "done_in_survivors.md",
        "把 DONE 加進「可以出現在存活清單」的判定",
        'SURVIVOR_VERDICTS = {"ADJACENT", "OPEN", "INCREMENTAL"}',
        'SURVIVOR_VERDICTS = {"ADJACENT", "OPEN", "INCREMENTAL", "DONE"}',
    ),
    (
        "ASSUM-01", "assumption_no_frame.md",
        "把每一條預設都當成印象級，量化檢查整段不執行",
        '            if a["impression"]:\n                continue',
        "            if True:\n                continue",
    ),
    (
        "ASSUM-01", "inherited_framed_partial.md",
        "把所有承接來的預設都當成未補框，取樣框檢查對它們整段不執行",
        '            if a["inherited"] and not a["framed"]:',
        '            if a["inherited"]:',
    ),
    (
        "ASSUM-02", "impression_as_g3.md",
        "不再檢查 G3 的輸入是不是印象級預設",
        '                elif a["impression"]:',
        "                elif False:",
    ),
    (
        "ASSUM-02", "inherited_unframed_as_g3.md",
        "不再檢查 G3 的輸入是不是承接自地形、尚未補取樣框的預設",
        '                elif a["inherited"] and not a["framed"]:',
        "                elif False:",
    ),
    (
        "EVID-01", "missing_evidence_field.md",
        "把〈佐證資料〉也認成搜尋證據欄的別名",
        '    "evidence": ("搜尋證據", "檢索證據", "證據", "查詢證據", "search evidence"),',
        '    "evidence": ("搜尋證據", "檢索證據", "證據", "查詢證據", "search evidence", "佐證資料"),',
    ),
    (
        "EVID-02", "no_evidence.md",
        "不再檢查搜尋證據欄是不是佔位符",
        '                if is_placeholder(val):\n                    self.add("EVID-02"',
        '                if False:\n                    self.add("EVID-02"',
    ),
    (
        "EVID-03", "vague_evidence.md",
        "不再要求搜尋證據欄含具體查詢詞",
        "                elif not degraded and not extract_queries(val):",
        "                elif False:",
    ),
    (
        "NEIGH-01", "neighbour_no_id.md",
        "不再要求「指名了文獻就要帶識別碼」",
        "                elif YEAR_RE.search(strip_md(val)) and not has_identifier(val):",
        "                elif False:",
    ),
    (
        "KILL-01", "unnamed_kill.md",
        "不再檢查淘汰列有沒有指名關鍵文獻",
        "            if not named:",
        "            if False:",
    ),
    (
        "KILL-02", "crowded_two_papers.md",
        "把 CROWDED 的篇數門檻從 3 降到 1",
        "                if n < 3:",
                "                if n < 1:",
    ),
    (
        "KILL-03", "done_no_quote.md",
        "不再要求 DONE 的淘汰原因含摘要逐字引句",
        "                if not has_verbatim_quote(reason):",
        "                if False:",
    ),
    (
        "ID-01", "kill_no_identifier.md",
        "不再要求被指名的關鍵文獻帶識別碼",
        "            if not has_identifier(ident) and not has_identifier(lit):",
        "            if False:",
    ),
    (
        "TRACE-01", "untraced_candidate.md",
        "不再檢查候選在〈檢索紀錄〉有沒有對應列",
        "                if not hit:",
        "                if False:",
    ),
    (
        "TRACE-02", "trace_placeholder_query.md",
        "不再檢查〈檢索紀錄〉的查詢詞是不是佔位符",
        "            if is_placeholder(q) or not extract_queries(q):",
        "            if False:",
    ),
    (
        "LANG-01", "assertive_language.md",
        "斷言措辭比對到了也不回報",
        "                m = re.search(pat, ln)\n                if m:",
        "                m = re.search(pat, ln)\n                if False:",
    ),
    (
        "TIER-01", "no_search_with_verdicts.md",
        "宣告未檢索時整條規則不再啟動",
        "        if not self.rep.no_search_declared:\n            return",
        "        if True:\n            return",
    ),
    # ---- 領域地形報告的五條 ------------------------------------------------
    # 這幾條規則都有數個臂（例如〈狀態〉同時查詞彙與檢索句型）。突變削弱的是
    # **樣本真的踩到的那一個臂**，其餘的臂由規則本身保守，不由本檔證明——
    # 這一點寫在 evals/README.md，不要讓綠燈被讀成「每個臂都被證過」。
    (
        "LHEAD-01", "landscape_no_disclaimer.md",
        "不再檢查表頭有沒有〈這份報告不做什麼〉那一行",
        "        if disclaimer is None:",
        "        if False:",
    ),
    (
        "LVOCAB-01", "landscape_verdict_word.md",
        "新穎性判定詞彙比對到了也不回報",
        "            token = NOVELTY_TOKEN_RE.search(ln)\n            if token:",
        "            token = NOVELTY_TOKEN_RE.search(ln)\n            if False:",
    ),
    (
        "LCOST-01", "landscape_no_cost.md",
        "不再檢查家族有沒有同時寫出買到什麼與付出什麼",
        "            if offenders:",
        "            if False:",
    ),
    (
        "LSTAT-01", "landscape_status_asserted.md",
        "〈狀態〉查出問題也不回報（詞彙、檢索句型、逐字查詢詞三個臂一起關掉）",
        "            problem = self._status_problem(val)\n            if problem:",
        "            problem = self._status_problem(val)\n            if False:",
    ),
    (
        "LWALL-01", "landscape_orphan_assumption.md",
        "不再檢查第二節的預設有沒有落進第六節任何一道牆",
        "            if aid not in used:",
        "            if False:",
    ),
]


def run(checker, report):
    """跑一次查核器，回傳 (exit code, set of check ids, stderr)。"""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, checker, report, "--json"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    try:
        data = json.loads(out)
    except ValueError:
        return proc.returncode, None, (err or out).strip()[:300]
    return proc.returncode, set(f["check"] for f in data["findings"]), err


def main():
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    with io.open(CHECKER, encoding="utf-8") as fh:
        source = fh.read()

    # 每個突變體都要對**三份**合規基準重跑：缺口報告、地形報告，以及承接地形的
    # 缺口報告。少了地形那一份，一個把地形規則整條關掉的突變會看起來人畜無害；
    # 少了承接那一份，一個只在「有承接標籤時」才踩壞的突變同樣不會被看見。
    clean = [os.path.join(FIXTURES, n)
             for n in ("good_report.md", "good_landscape.md", "good_inherited_report.md")]
    tmp = tempfile.mkdtemp(prefix="gaphunter-mut-")
    failures = []
    collateral_notes = []

    print("突變測試：削弱每條規則的判定條件，確認對應樣本因此轉綠")
    print("（原始 format_check.py 唯讀；突變體寫在 %s）\n" % tmp)
    print("%-11s %-28s %-8s %s" % ("check", "fixture", "結果", "說明"))
    print("-" * 92)

    try:
        for check, fixture, what, old, new in MUTATIONS:
            report = os.path.join(FIXTURES, fixture)
            if not os.path.isfile(report):
                failures.append("%s：樣本 %s 不存在" % (check, fixture))
                print("%-11s %-28s %-8s %s" % (check, fixture, "FAIL", "樣本不存在"))
                continue

            # 突變片段必須唯一，否則不知道改到哪裡
            n = source.count(old)
            if n != 1:
                failures.append("%s：突變片段在原始碼出現 %d 次（需恰好 1 次）" % (check, n))
                print("%-11s %-28s %-8s %s" % (check, fixture, "FAIL", "突變片段不唯一（%d 次）" % n))
                continue

            # 1) 基準線：原始查核器必須真的在這個樣本上報出這個 check
            base_code, base_ids, base_err = run(CHECKER, report)
            if base_ids is None:
                failures.append("%s：基準線 JSON 解析失敗（%s）" % (check, base_err))
                print("%-11s %-28s %-8s %s" % (check, fixture, "FAIL", "基準線輸出不是 JSON"))
                continue
            if check not in base_ids:
                failures.append("%s：樣本 %s 根本沒觸發這個 check（實得 %s）"
                                % (check, fixture, sorted(base_ids) or "無"))
                print("%-11s %-28s %-8s %s" % (check, fixture, "FAIL", "基準線未觸發"))
                continue

            # 2) 突變體
            mutant = os.path.join(tmp, "mutant_%s.py" % check.replace("-", "_"))
            with io.open(mutant, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(source.replace(old, new))

            mut_code, mut_ids, mut_err = run(mutant, report)
            if mut_ids is None:
                failures.append("%s：突變體壞掉，不是合法 Python 或崩潰（%s）" % (check, mut_err))
                print("%-11s %-28s %-8s %s" % (check, fixture, "FAIL", "突變體崩潰"))
                continue

            # 3) 突變不得讓任何一份合規報告變紅——那代表改壞了別的東西
            for good in clean:
                good_code, good_ids, _ = run(mutant, good)
                if good_code != 0:
                    failures.append("%s：突變後 %s 由綠轉紅（%s），突變波及其他規則"
                                    % (check, os.path.basename(good), sorted(good_ids or [])))

            if check in mut_ids:
                failures.append(
                    "%s：削弱後樣本 %s 仍報這個 check——這條規則沒有被證明有偵測力"
                    % (check, fixture)
                )
                print("%-11s %-28s %-8s %s" % (check, fixture, "FAIL", "削弱後仍觸發"))
                continue

            extra = sorted(mut_ids)
            note = what
            if extra:
                note = "%s（後備規則接手：%s）" % (what, " ".join(extra))
                collateral_notes.append((check, fixture, extra))
            print("%-11s %-28s %-8s %s" % (check, fixture, "PASS", note))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("-" * 92)
    # 條數一律從 format_check.py 現況推導，不寫死——寫死的數字遲早會與程式碼脫節。
    sys.path.insert(0, HERE)
    declared = None
    try:
        import format_check
    except ImportError as exc:
        failures.append("無法匯入 format_check 做覆蓋率比對：%s" % exc)
    else:
        declared = set(format_check.CHECK_DESCRIPTIONS)
        mutated = set(m[0] for m in MUTATIONS)
        print("%d 條規則受測（format_check.py 共宣告 %d 條）" % (len(mutated), len(declared)))
        missing = sorted(declared - mutated)
        stray = sorted(mutated - declared)
        if missing:
            failures.append("這些 check 沒有突變體，偵測力未經證明：%s" % ", ".join(missing))
        if stray:
            failures.append("MUTATIONS 指到不存在的 check id：%s" % ", ".join(stray))
    if declared is None:
        print("%d 條規則受測" % len(MUTATIONS))

    if collateral_notes and verbose:
        print("\n附帶觸發（削弱目標規則後，改由別條規則抓到同一個樣本）：")
        for check, fixture, extra in collateral_notes:
            print("  %s → %s 由 %s 接手" % (check, fixture, " ".join(extra)))
        print("  這不是缺陷：代表同一個缺陷有兩層防線。但要知道哪一層先擋。")

    print("")
    if failures:
        print("❌ %d 條規則無法證明偵測力：\n" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("✅ 每條規則削弱後，對應樣本都不再報該 check——偵測力成立。")
    print("   這仍然只是形式層的偵測力：它不證明任何一篇被指名的文獻是真的。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
