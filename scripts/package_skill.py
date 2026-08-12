#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把這個 repo 打包成可上傳的 skill ZIP（ChatGPT Skills、或分享給別人）。

    python scripts/package_skill.py                # 產生 research-gap-hunter.zip
    python scripts/package_skill.py -o /tmp/x.zip  # 指定輸出位置

⚠️ 打包前先 commit。
    檔案清單來自 `git ls-files`，**還沒 commit 的檔案不在裡面，也就不會被打包**。
    這是刻意的（未入庫的東西不該分享出去），但代價是：在一個只 commit 了 SKILL.md
    的工作目錄裡打包，會產出一個沒有 README、沒有 evals、沒有 references 的
    單檔 ZIP，而且看起來一切正常。所以請先 `git add -A && git commit`。
    本腳本會在打包後把「工作目錄有、但沒入庫」的檔案數印出來提醒你。

為什麼不能直接壓縮 clone 下來的資料夾：
  1. `.git` 會被一起包進去（無用歷史，且掃描器可能因此標記）
  2. 資料夾名稱會是 repo 名 `research-gap-hunter-skill`，但 skill 的識別名是
     `research-gap-hunter`（SKILL.md frontmatter 的 name）——本腳本會把頂層改成
     `research-gap-hunter`

打包後會跑兩道閘，任何一道沒過都會**刪掉 ZIP 並以非零離開碼結束**：

  1. 完整性：從 ZIP 裡的 SKILL.md 出發，追它（以及 references/ 那些檔）寫出來的
     相對連結。SKILL.md 現在把「開跑前先讀 references/…」寫成硬性步驟，載入 skill
     的模型會照做；連結指到的檔案要是不在包裡，對方拿到的是一個一開跑就撞牆的
     skill——而且外觀完全正常。**只有 SKILL.md 的單檔包永遠不是有效的包。**
  2. 安全：evals/zip_check.py，確認沒有把金鑰、個人 email、或本機絕對路徑包進去。

寧可不給檔案，也不要給一個殘缺或外洩的檔案。
"""
import argparse
import os
import posixpath
import re
import subprocess
import sys
import zipfile

# 與 evals/doc_scan.py〈檢查 3〉同一條樣式：markdown 行內連結
LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EXTERNAL_LINK_PREFIXES = ("http", "mailto:", "~", "$", "<", "#")


def broken_internal_links(zip_path):
    """ZIP 裡的 SKILL.md 叫人去讀、包裡卻沒有的檔案。

    從 SKILL.md 出發做廣度優先：SKILL.md 連到的 .md 也要再追下去，因為
    references/ 那兩份自己也互相連、也連回 SKILL.md。回傳 (來源檔, 找不到的目標)
    的清單；SKILL.md 本身不在包裡是最嚴重的一種，用 (None, "SKILL.md") 表示。
    """
    prefix = SKILL_NAME + "/"
    with zipfile.ZipFile(zip_path) as z:
        inside = set(n[len(prefix):] for n in z.namelist() if n.startswith(prefix))
        if "SKILL.md" not in inside:
            return [(None, "SKILL.md")]
        broken, seen, queue = [], set(), ["SKILL.md"]
        while queue:
            cur = queue.pop(0)
            if cur in seen:
                continue
            seen.add(cur)
            try:
                text = z.read(prefix + cur).decode("utf-8", "replace")
            except KeyError:
                continue
            base = posixpath.dirname(cur)
            for raw in LINK_RE.findall(text):
                link = raw.split("#")[0].strip()
                if not link or link.startswith(EXTERNAL_LINK_PREFIXES):
                    continue
                target = posixpath.normpath(posixpath.join(base, link))
                if target.startswith(".."):
                    # 指到包外面的東西：對方 clone 或解壓之後一樣讀不到
                    broken.append((cur, link))
                elif target not in inside:
                    broken.append((cur, target))
                elif target.endswith(".md"):
                    queue.append(target)
    # 去重但保留順序，讓訊息穩定可比對
    out, taken = [], set()
    for item in broken:
        if item not in taken:
            taken.add(item)
            out.append(item)
    return out

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = "research-gap-hunter"  # 與 SKILL.md frontmatter 的 name 一致
SKIP_DIRS = {".git", "__pycache__", ".venv", ".pytest_cache", ".idea", ".vscode"}
SKIP_FILES = {".env", ".DS_Store", "Thumbs.db"}
SKIP_EXT = (".pyc", ".pyo", ".zip")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=os.path.join(os.getcwd(), f"{SKILL_NAME}.zip"))
    args = ap.parse_args()

    out = os.path.abspath(args.output)

    # 優先用 git 追蹤清單：打包內容就等於「使用者 clone 會拿到什麼」，
    # 也自動排除 .gitignore 的東西（本機的預覽圖、快取、.env）。
    # 注意：還沒 commit 的新檔案不在 git ls-files 裡，也就不會被打包——
    # 這是刻意的（未入庫的東西不該分享出去），但打包前記得先 commit。
    files_list, source = [], "git ls-files"
    try:
        r = subprocess.run(["git", "-C", REPO, "ls-files"], capture_output=True,
                           text=True, encoding="utf-8", timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            files_list = [os.path.join(REPO, p) for p in r.stdout.splitlines() if p.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    if not files_list:                      # 不是 git repo（例如已解壓的 ZIP）就走檔案掃描
        source = "檔案掃描"
        for root, dirs, fs in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            files_list += [os.path.join(root, f) for f in fs]

    # 工作目錄裡「本來該被打包、卻沒入庫」的檔案。少一個 README 不會讓任何檢查變紅，
    # 但拿到包的人第一眼就會發現——所以寧可在這裡吵一句。
    tracked = set(os.path.abspath(p) for p in files_list)
    missing = []
    if source == "git ls-files":
        for root, dirs, fs in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in fs:
                p = os.path.join(root, f)
                if f in SKIP_FILES or f.endswith(SKIP_EXT) or f.startswith(".env"):
                    continue
                if os.path.abspath(p) not in tracked:
                    missing.append(os.path.relpath(p, REPO).replace("\\", "/"))

    n, raw = 0, 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files_list:
            f = os.path.basename(p)
            if f in SKIP_FILES or f.endswith(SKIP_EXT) or f.startswith(".env"):
                continue
            if not os.path.isfile(p) or os.path.abspath(p) == out:
                continue
            arc = os.path.join(SKILL_NAME, os.path.relpath(p, REPO)).replace("\\", "/")
            z.write(p, arc)
            n += 1
            raw += os.path.getsize(p)

    size = os.path.getsize(out)
    print(f"打包完成：{out}")
    print(f"  {n} 個檔案（清單來源：{source}）｜原始 {raw / 1024:.0f} KB → 壓縮 {size / 1024:.0f} KB")
    print(f"  頂層資料夾：{SKILL_NAME}/（SKILL.md 位於 {SKILL_NAME}/SKILL.md）\n")

    if missing:
        print(f"⚠️ 有 {len(missing)} 個檔案在工作目錄裡但沒入庫，因此**不在這個 ZIP 裡**：")
        for p in missing[:12]:
            print(f"     {p}")
        if len(missing) > 12:
            print(f"     …另外 {len(missing) - 12} 個")
        print("   先 `git add -A && git commit` 再打包，否則對方拿到的是殘缺的 skill。\n")

    # 閘 1：完整性。SKILL.md 叫人去讀的檔案要是不在包裡，這個 skill 一開跑就撞牆，
    # 而且外觀完全正常——那比沒有包更糟，所以跟外洩一樣的處理方式：刪檔、非零離開。
    broken = broken_internal_links(out)
    if broken:
        os.remove(out)
        print("\n❌ 完整性檢查未通過，已刪除 ZIP。")
        if broken == [(None, "SKILL.md")]:
            print(f"   ZIP 裡沒有 {SKILL_NAME}/SKILL.md——這根本不是一個 skill 包。")
        else:
            print(f"   SKILL.md 把「先讀 references/…」寫成硬性步驟，但包裡少了它叫人讀的檔案：")
            for src, tgt in broken[:12]:
                print(f"     {src} → {tgt}（不在 ZIP 裡）")
            if len(broken) > 12:
                print(f"     …另外 {len(broken) - 12} 筆")
            print(f"   只有 SKILL.md 的單檔包永遠不是有效的包：載入這個 skill 的模型會照著")
            print(f"   SKILL.md 去讀 references/，讀不到就只能自己編——那正是本 skill 要防的事。")
        if missing:
            print(f"\n   最可能的原因：有 {len(missing)} 個檔案還沒入庫（打包清單來自 git ls-files）。")
            print("   先 `git add -A && git commit`，再重新打包。")
        sys.exit(1)

    sys.stdout.flush()   # 讓子行程的輸出接在上面，而不是被緩衝到最後才吐出來
    check = os.path.join(REPO, "evals", "zip_check.py")
    if not os.path.isfile(check):
        os.remove(out)
        print(f"\n❌ 找不到 {check}，無法做安全檢查，已刪除 ZIP。")
        print("   沒檢查過的包不能出門——這比沒有包更糟。")
        sys.exit(1)
    r = subprocess.run([sys.executable, check, out], text=True, encoding="utf-8")
    if r.returncode != 0:
        os.remove(out)
        print("\n❌ 安全檢查未通過，已刪除 ZIP。修正後重新打包。")
        sys.exit(1)

    if missing:
        # 兩道閘都過了，但工作目錄裡還有東西沒入庫。這不是致命錯誤（SKILL.md 沒有
        # 連到它們），卻仍然是「對方拿到的東西比你以為的少」，所以在最後一行再講一次，
        # 不讓它被前面的輸出捲走。
        print(f"\n⚠️ 可以上傳，但這個 ZIP 少了 {len(missing)} 個未入庫的檔案（清單見上）。")
        print("   SKILL.md 沒有連到它們，所以完整性檢查放行；但如果那些檔案本來就該一起分享")
        print("   （README、evals、LICENSE…），先 `git add -A && git commit` 再打包一次。")
        sys.exit(0)
    print("\n可以上傳了。")


if __name__ == "__main__":
    main()
