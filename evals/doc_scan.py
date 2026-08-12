#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doc_scan.py — 掃描「文件宣稱」與「實際檔案／程式」是否同步。

format_check.py 查的是**一份報告**的形式；本檔查的是**這個 repo 自己**：
README 說得出口的東西，倉庫裡到底有沒有。

這一類缺陷不會讓任何測試變紅，卻是讀者第一個踩到的坑——
文件叫他跑 `python evals/rubric_check.py`，而那個檔案根本不存在；
文件說查核器有 18 條規則，程式裡其實是 21 條；
文件連到 `references/`，而那個目錄還沒被建出來。
所以這裡的每一個數字都是**從程式或 SKILL.md 現場推導**的，不寫死在本檔裡。

用法：
    python evals/doc_scan.py
    python evals/doc_scan.py -v      # 連通過的項目一起列出

離開碼：
    0  文件與程式一致
    1  有不同步（清單印在最後）
    2  掃描器自己壞了（讀不到必要檔案）

與 lit-review 的同名工具的差別：那一份把 repo 路徑寫死成作者的家目錄；
本檔一律從 __file__ 往上推，clone 到任何位置都能跑。
"""

import importlib.util
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# repo 根目錄一律相對於本檔推導，不依賴 cwd，也不寫死任何人的家目錄
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# 這些名字指向本 repo 之外的東西（姊妹 skill、使用者自己的檔案），
# 不該被當成「文件指到不存在的檔案」。列在這裡是為了可稽核。
EXTERNAL_BASENAMES = {
    "lit_api.py",        # lit-review 的腳本，本 repo 只呼叫、不收錄
    "AGENTS.md",         # 使用者自己的 Codex 設定檔
    "MEMORY.md",
}
EXTERNAL_PREFIXES = ("lit-review/", "lit-review-skill/", "../", "~", "$", "<", "http")

# 本機絕對路徑：打包出去會外洩使用者名稱，也讓別人 clone 之後跑不動。
# 使用者名稱那一段必須是真的名字字元，`C:\Users\…` 這種「在描述樣式」的寫法不算——
# 門檻刻意與 evals/zip_check.py 的同一條規則對齊，兩支工具不該給出相反的判斷。
ABS_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:[\\/]{1,2}Users[\\/]{1,2}[A-Za-z0-9_.\-]+"),
    re.compile(r"(?<![\w:])/(?:home|Users)/[A-Za-z0-9_.\-]+/"),
]

TEXT_EXT = (".md", ".py", ".txt", ".json", ".yml", ".yaml", ".cfg", ".toml")
SKIP_DIRS = {".git", "__pycache__", ".venv", ".pytest_cache", ".idea", ".vscode"}

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "eighteen": 18, "twenty": 20,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
    "八": 8, "九": 9, "十": 10,
}

issues = []
notes = []
VERBOSE = "-v" in sys.argv or "--verbose" in sys.argv


def fail(msg):
    issues.append(msg)


def ok(msg):
    if VERBOSE:
        print("    ✓ %s" % msg)


def rel(path):
    return os.path.relpath(path, REPO).replace("\\", "/")


def read(relpath):
    with open(os.path.join(REPO, relpath), encoding="utf-8") as fh:
        return fh.read()


def exists(relpath):
    return os.path.exists(os.path.join(REPO, relpath))


def load_module(relpath, name):
    """把 repo 裡的一支腳本當模組載入，好直接讀它宣告的常數。

    比用正規表達式去啃原始碼可靠：常數改名、換行、加註解都不會讓推導失準。
    """
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def walk_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            yield os.path.join(root, f)


def to_int(tok):
    tok = tok.strip().lower()
    if tok.isdigit():
        return int(tok)
    return NUM_WORDS.get(tok)


# 「those two generators」數的是剛才提到的兩個，不是宣稱總共有幾個。
# 指示詞開頭的片語一律不當成總數宣稱，否則掃描器會對正確的句子開槍。
PARTITIVE_GUARD = re.compile(
    r"(?:those|these|both|other|remaining|first|last|next|上述|前述|這|那)\s*$", re.I
)


def claim_check(label, actual, patterns, files):
    """在文件裡找「宣稱的數字」，和推導出來的實際值比對。

    patterns 每一條都必須只抓一個數字群組。抓不到就當作「文件沒宣稱」，
    不算缺陷——本檔的職責是抓**說錯**，不是強迫文件必須提到每個數字。
    """
    found = 0
    for f in files:
        if not exists(f):
            continue
        txt = read(f)
        for pat in patterns:
            for m in pat.finditer(txt):
                claimed = to_int(m.group(1))
                if claimed is None:
                    continue
                if PARTITIVE_GUARD.search(txt[max(0, m.start() - 24):m.start()]):
                    continue
                found += 1
                if claimed != actual:
                    line = txt[:m.start()].count("\n") + 1
                    fail("%s L%d 宣稱 %s %s，實際 %s"
                         % (f, line, m.group(1), label, actual))
                else:
                    ok("%s L%d：%s = %s"
                       % (f, txt[:m.start()].count("\n") + 1, label, actual))
    if not found:
        notes.append("文件沒有任何一處宣稱「%s」（實際 %s），本項無從比對" % (label, actual))


# ==========================================================================
# 0. 前置：載入程式裡的事實
# ==========================================================================

print("■ repo 根目錄：%s" % REPO)

for required in ("SKILL.md", "evals/format_check.py", "evals/self_test.py",
                 "evals/mutation_test.py", "README.md", "README.zh-TW.md"):
    if not exists(required):
        sys.stderr.write("掃描器無法運作：缺少 %s\n" % required)
        sys.exit(2)

try:
    fc = load_module("evals/format_check.py", "_ds_format_check")
    st = load_module("evals/self_test.py", "_ds_self_test")
    mt = load_module("evals/mutation_test.py", "_ds_mutation_test")
except Exception as exc:                                   # noqa: BLE001
    sys.stderr.write("掃描器無法載入 evals 的腳本：%s\n" % exc)
    sys.exit(2)

skill = read("SKILL.md")

DOC_FILES = ["README.md", "README.zh-TW.md", "SKILL.md", "evals/README.md",
             "references/elimination-engine.md", "references/generators.md",
             "examples/worked_example.md"]
DOC_FILES = [f for f in DOC_FILES if exists(f)]
READMES = ["README.md", "README.zh-TW.md"]

n_checks = len(fc.CHECK_DESCRIPTIONS)
n_fixtures = len([f for f in os.listdir(os.path.join(REPO, "evals", "fixtures"))
                  if f.endswith(".md")]) if exists("evals/fixtures") else 0
n_expected = len(st.EXPECTED)
n_mutants = len(mt.MUTATIONS)

print("■ format_check.py 宣告的 check 條數：%d" % n_checks)
print("■ evals/fixtures/ 實際樣本數：%d（self_test.EXPECTED %d 筆）" % (n_fixtures, n_expected))
print("■ mutation_test.py 的突變體數：%d" % n_mutants)


# ==========================================================================
# 1. 文件提到的檔案路徑是否存在
# ==========================================================================

print("\n■ 檢查 1：文件提到的檔案路徑")

PATH_TOKEN_RE = re.compile(r"`([^`\n]+)`")


def is_external(tok):
    if tok.startswith(EXTERNAL_PREFIXES):
        return True
    return os.path.basename(tok) in EXTERNAL_BASENAMES


checked_paths = 0
for f in DOC_FILES:
    txt = read(f)
    for m in PATH_TOKEN_RE.finditer(txt):
        tok = m.group(1).strip()
        if not re.fullmatch(r"[\w][\w./\-]*\.(?:md|py)", tok):
            continue
        if is_external(tok):
            continue
        checked_paths += 1
        if "/" in tok:
            if not exists(tok):
                line = txt[:m.start()].count("\n") + 1
                fail("%s L%d 提到 `%s`，但這個檔案不存在" % (f, line, tok))
            continue
        # 只寫檔名沒寫路徑：在 repo 裡找同名檔
        hit = any(os.path.basename(p) == tok for p in walk_files())
        if not hit:
            line = txt[:m.start()].count("\n") + 1
            fail("%s L%d 提到 `%s`，但 repo 裡找不到同名檔案" % (f, line, tok))
print("    掃了 %d 個路徑提及（本 repo 之外的名字略過：%s）"
      % (checked_paths, "、".join(sorted(EXTERNAL_BASENAMES))))


# ==========================================================================
# 2. 文件裡的 python 指令是否有檔案在後面
# ==========================================================================

print("■ 檢查 2：文件裡的 `python evals/…` ／ `python scripts/…` 指令")

CMD_RE = re.compile(r"python3?\s+((?:evals|scripts)/[\w./\-]+\.py)")
cmds = set()
for f in DOC_FILES:
    txt = read(f)
    for m in CMD_RE.finditer(txt):
        cmds.add((f, txt[:m.start()].count("\n") + 1, m.group(1)))
for f, line, cmd in sorted(cmds):
    if not exists(cmd):
        fail("%s L%d 叫讀者執行 `python %s`，但這個檔案不存在" % (f, line, cmd))
    else:
        ok("%s L%d：python %s" % (f, line, cmd))
print("    掃了 %d 條指令" % len(cmds))


# ==========================================================================
# 3. 相對 markdown 連結是否解析得到
# ==========================================================================

print("■ 檢查 3：markdown 相對連結")

LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
n_links = 0
for f in DOC_FILES:
    txt = read(f)
    base = os.path.dirname(os.path.join(REPO, f))
    for m in LINK_RE.finditer(txt):
        target = m.group(1).split("#")[0]
        if not target or target.startswith(("http", "mailto:", "~", "$", "<")):
            continue
        n_links += 1
        if not os.path.exists(os.path.normpath(os.path.join(base, target))):
            line = txt[:m.start()].count("\n") + 1
            fail("%s L%d 的連結 `%s` 解析不到（相對於 %s/）" % (f, line, target, os.path.dirname(f) or "."))
print("    掃了 %d 個相對連結" % n_links)


# ==========================================================================
# 4. 雙語 README 的節數
# ==========================================================================

print("■ 檢查 4：README 雙語節數")

sec_counts = {}
for f in READMES:
    sec_counts[f] = len(re.findall(r"^## ", read(f), re.M))
print("    %s %d 節 vs %s %d 節"
      % (READMES[0], sec_counts[READMES[0]], READMES[1], sec_counts[READMES[1]]))
if sec_counts[READMES[0]] != sec_counts[READMES[1]]:
    fail("雙語 README 節數不一致：%s=%d，%s=%d——鏡像壞了，一邊會少掉一整段承諾"
         % (READMES[0], sec_counts[READMES[0]], READMES[1], sec_counts[READMES[1]]))


# ==========================================================================
# 5. 文字裡的數字宣稱 vs 程式現況
# ==========================================================================

print("■ 檢查 5：文件宣稱的數字")

# 英文樣式一律用 [ \t] 而不是 \s：\s 會跨行，把「…EX.81」＋下一行的「check:」
# 讀成「81 checks」，那是掃描器自己製造的假警報。
claim_check(
    "查核規則條數", n_checks,
    [re.compile(r"\*{0,2}(\d+)\*{0,2}[ \t]+checks?\b(?![:：])"),
     re.compile(r"\*{0,2}(\d+)\s*條(?:規則|查核|檢查)\*{0,2}")],
    DOC_FILES,
)
claim_check(
    "fixture 數", n_fixtures,
    [re.compile(r"(\d+)[ \t]+fixtures?\b"),
     re.compile(r"(\d+)\s*個(?:樣本|樣本檔)")],
    DOC_FILES,
)
claim_check(
    "突變體數", n_mutants,
    [re.compile(r"(\d+)[ \t]+mutants?\b"),
     re.compile(r"(\d+)\s*個突變(?:體)?")],
    DOC_FILES,
)

# 生成器數：以 references/generators.md 實際定義的 G 編號為準
if exists("references/generators.md"):
    gens = sorted(set(re.findall(r"\bG([1-9])\b", read("references/generators.md"))))
else:
    gens = sorted(set(re.findall(r"\bG([1-9])\b", skill)))
n_gens = len(gens)
print("    生成器實際定義：G%s（共 %d 種）" % ("、G".join(gens), n_gens))
claim_check(
    "生成器數", n_gens,
    # 數詞不列舉白名單：抓到什麼就交給 to_int，認不得的詞（the、these…）自動略過。
    # 白名單漏掉一個數詞，等於這條檢查對那個數字失明。
    [re.compile(r"\b(\w+)[ \t]+(?:structural[ \t]+)?generators\b", re.I),
     re.compile(r"([一二三四五六七八九十]|\d+)\s*種(?:結構性)?生成器")],
    DOC_FILES,
)

# 輸出格式的區段數：以 SKILL.md 那個 fenced block 裡的 `## ` 行為準
tmpl = re.search(r"```\n(# 研究缺口報告.*?)```", skill, re.S)
if not tmpl:
    fail("SKILL.md 找不到輸出格式的樣板區塊（``` 內以「# 研究缺口報告」開頭），"
         "無法推導區段數與區段名稱")
    tmpl_sections = []
else:
    tmpl_sections = re.findall(r"^## (.+)$", tmpl.group(1), re.M)
    print("    SKILL.md 輸出樣板的區段：%d 個（%s）"
          % (len(tmpl_sections), "／".join(s.split("（")[0] for s in tmpl_sections)))
    claim_check(
        "輸出區段數", len(tmpl_sections),
        [re.compile(r"\b(\w+)[- ]section\b", re.I),
         re.compile(r"([一二三四五六七八九十]|\d+)\s*(?:個)?區段的?(?:固定)?結構"),
         re.compile(r"固定的?([一二三四五六七八九十]|\d+)\s*節")],
        DOC_FILES,
    )

# 樣板的區段名稱必須和 good_report.md 對得上（樣板改了、樣本沒跟上就會被抓到）
if tmpl_sections and exists("evals/fixtures/good_report.md"):
    want = [s.split("（")[0].strip() for s in tmpl_sections]
    got = [s.split("（")[0].strip()
           for s in re.findall(r"^## (.+)$", read("evals/fixtures/good_report.md"), re.M)]
    if want != got:
        fail("SKILL.md 輸出樣板的區段名稱與 evals/fixtures/good_report.md 不一致：\n"
             "        樣板：%s\n        樣本：%s" % ("／".join(want), "／".join(got)))
    else:
        ok("輸出樣板的 %d 個區段名稱與 good_report.md 逐字一致" % len(want))


# ==========================================================================
# 6. 判定詞彙：SKILL.md 說的 vs format_check.py 認的
# ==========================================================================

print("■ 檢查 6：判定詞彙表（SKILL.md ↔ format_check.py）")

# 6a. SKILL.md 判定表列出的每一個判定，查核器都要認得
table_verdicts = set(re.findall(r"^\|\s*\*\*([A-Z][A-Z?]{2,})\*\*\s*\|", skill, re.M))
unknown = sorted(v for v in table_verdicts if v not in fc.ALLOWED_VERDICTS)
print("    SKILL.md 判定表列出：%s" % "、".join(sorted(table_verdicts)))
if unknown:
    fail("SKILL.md 判定表有 %s，但 format_check.ALLOWED_VERDICTS 不認得——"
         "報告照 SKILL.md 寫會被查核器判違規" % "、".join(unknown))

# 6b. 查核器認的每一個值，SKILL.md 都要寫過（不然是沒有文件依據的暗規則）
undocumented = sorted(v for v in fc.ALLOWED_VERDICTS if v not in skill)
if undocumented:
    fail("format_check.py 接受 %s，但 SKILL.md 完全沒提到——查核器比規格寬"
         % "、".join(undocumented))

# 6c. 存活判定：SKILL.md 的輸出樣板寫死了哪三個
m = re.search(r"新穎性判定\*{0,2}\s*[：:]\s*([A-Z／/、 ]+)", skill)
if m:
    doc_survivors = set(re.findall(r"[A-Z]{3,}", m.group(1)))
    print("    存活判定：SKILL.md %s ／ format_check %s"
          % ("、".join(sorted(doc_survivors)), "、".join(sorted(fc.SURVIVOR_VERDICTS))))
    if doc_survivors != set(fc.SURVIVOR_VERDICTS):
        fail("存活判定不一致：SKILL.md 寫 %s，format_check.SURVIVOR_VERDICTS 是 %s"
             % ("、".join(sorted(doc_survivors)), "、".join(sorted(fc.SURVIVOR_VERDICTS))))
else:
    notes.append("SKILL.md 的輸出樣板找不到〈新穎性判定〉那一行，存活判定無從比對")

# 6d. 淘汰判定
m = re.search(r"〈判定〉只能是\s*([A-Z 或/、]+)", skill)
if m:
    doc_kills = set(re.findall(r"[A-Z]{3,}", m.group(1)))
    print("    淘汰判定：SKILL.md %s ／ format_check %s"
          % ("、".join(sorted(doc_kills)), "、".join(sorted(fc.KILL_VERDICTS))))
    if doc_kills != set(fc.KILL_VERDICTS):
        fail("淘汰判定不一致：SKILL.md 寫 %s，format_check.KILL_VERDICTS 是 %s"
             % ("、".join(sorted(doc_kills)), "、".join(sorted(fc.KILL_VERDICTS))))
else:
    notes.append("SKILL.md 找不到「〈判定〉只能是…」的句子，淘汰判定無從比對")


# ==========================================================================
# 7. 測試套件自己的覆蓋率宣稱
# ==========================================================================

print("■ 檢查 7：測試套件的覆蓋率")

if n_fixtures != n_expected:
    fail("evals/fixtures/ 有 %d 個 .md，self_test.EXPECTED 只列了 %d 筆——"
         "有樣本沒被跑到，或 EXPECTED 指到不存在的樣本" % (n_fixtures, n_expected))

# 每個樣本都要在 evals/README.md 的樣本表裡被點名。
# 這條的由來：樣本表是手維護的，而 EXPECTED 是程式讀的，兩者曾經各自漂移兩次
# ——加樣本的人改了 EXPECTED、忘了改表，而當時沒有任何一道閘看得到那張表。
_evals_readme = read("evals/README.md")
_unnamed = sorted(f for f in os.listdir(os.path.join(REPO, "evals", "fixtures"))
                  if f.endswith(".md") and f not in _evals_readme)
if _unnamed:
    fail("這些樣本存在於磁碟但沒有在 evals/README.md 的樣本表裡被點名：%s"
         % "、".join(_unnamed))
else:
    ok("%d 個樣本全部在 evals/README.md 有記載" % n_fixtures)

mut_ids = set(m[0] for m in mt.MUTATIONS)
missing_mut = sorted(set(fc.CHECK_DESCRIPTIONS) - mut_ids)
stray_mut = sorted(mut_ids - set(fc.CHECK_DESCRIPTIONS))
if missing_mut:
    fail("這些 check 沒有對應的突變體，偵測力未被證明：%s" % "、".join(missing_mut))
if stray_mut:
    fail("mutation_test.py 指到不存在的 check id：%s" % "、".join(stray_mut))
if not missing_mut and not stray_mut:
    ok("%d 條 check 全部有突變體" % n_checks)


# ==========================================================================
# 8. 本機絕對路徑
# ==========================================================================

print("■ 檢查 8：本機絕對路徑")

try:
    r = subprocess.run(["git", "-C", REPO, "ls-files"], capture_output=True,
                       text=True, encoding="utf-8", timeout=30)
    tracked = set(p.strip() for p in r.stdout.splitlines() if p.strip()) if r.returncode == 0 else set()
except (OSError, subprocess.SubprocessError):
    tracked = set()

n_scanned, n_hits = 0, 0
for p in walk_files():
    if not p.lower().endswith(TEXT_EXT) and os.path.basename(p) not in ("LICENSE", ".gitignore"):
        continue
    if os.path.abspath(p) == os.path.abspath(__file__):
        continue          # 本檔內含的是「比對用的樣式」，不是路徑
    try:
        with open(p, encoding="utf-8") as fh:
            txt = fh.read()
    except (OSError, UnicodeDecodeError):
        continue
    n_scanned += 1
    for pat in ABS_PATH_PATTERNS:
        for m in pat.finditer(txt):
            n_hits += 1
            line = txt[:m.start()].count("\n") + 1
            mark = "已入庫" if rel(p) in tracked else "未入庫"
            fail("%s L%d 含本機絕對路徑「%s」（%s）——clone 的人跑不動，也外洩使用者名稱"
                 % (rel(p), line, m.group(0), mark))
print("    掃了 %d 個文字檔，命中 %d 處" % (n_scanned, n_hits))


# ==========================================================================
# 9. 打包覆蓋率（提醒，不計入不同步）
# ==========================================================================

print("■ 檢查 9：git 追蹤範圍（打包清單來源）")

shippable = []
for p in walk_files():
    r_ = rel(p)
    if r_.endswith((".pyc", ".zip")) or "/__pycache__/" in r_:
        continue
    shippable.append(r_)
untracked = sorted(set(shippable) - tracked)
print("    git ls-files %d 個｜工作目錄可打包 %d 個" % (len(tracked), len(shippable)))
if untracked:
    notes.append(
        "有 %d 個檔案還沒 commit，scripts/package_skill.py 走的是 git ls-files，"
        "現在打包會少掉它們（先 `git add -A && git commit`）：%s%s"
        % (len(untracked), "、".join(untracked[:6]), "…" if len(untracked) > 6 else "")
    )


# ==========================================================================
# 結果
# ==========================================================================

print("\n" + "=" * 72)
if notes:
    print("提醒（不計入不同步）：")
    for n in notes:
        print("  · %s" % n)
    print("")
if issues:
    print("發現 %d 項文件與程式不同步：" % len(issues))
    for i in issues:
        print("  - %s" % i)
    print("\n文件說得出口的東西，倉庫裡就要有。修好再送出。")
    sys.exit(1)
print("文件與程式一致。")
print("（本檔只比對「說了什麼」與「有什麼」，不保證文件說得對——那要人讀。）")
sys.exit(0)
