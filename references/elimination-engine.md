# 淘汰引擎：呼叫 lit-review 的 lit_api.py

第 3 步開跑前讀這一份。`lit_api.py` 是**純標準函式庫腳本**，即使 lit-review skill 沒有被載入也能跑——本技能呼叫的是**腳本**，不是 skill。

## 一、找到 lit_api.py（可攜偵測，結果寫進報告表頭）

按順序探測四個位置，**不要寫死任何一台機器的路徑**：（1）環境變數 `LIT_API_PATH`；（2）使用者家目錄的 skills 目錄；（3）同層或上層的姊妹 repo `lit-review-skill/scripts/lit_api.py`；（4）上層的 `lit-review/scripts/lit_api.py`。四個都沒中，**就問使用者一句**：「你的 lit-review 放在哪裡？（我要的是 `scripts/lit_api.py` 的路徑）」；使用者說沒裝就直接走〈四、降級階梯〉的階 2。

**PowerShell（Windows）**

```powershell
$py = @('python','py','python3') | Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
$LIT = @(
  $env:LIT_API_PATH,
  (Join-Path $env:USERPROFILE '.claude\skills\lit-review\scripts\lit_api.py'),
  '.\lit-review-skill\scripts\lit_api.py',
  '..\lit-review-skill\scripts\lit_api.py',
  '..\lit-review\scripts\lit_api.py'
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if ($LIT -and $py) { & $py "$LIT" --help *> $null; $LIT_OK = ($LASTEXITCODE -eq 0) } else { $LIT_OK = $false }
"lit_api available: $LIT_OK  ($LIT)"
```

**bash（macOS / Linux）**

```bash
PY=$(command -v python3 || command -v python)
LIT=""
for p in "$LIT_API_PATH" "$HOME/.claude/skills/lit-review/scripts/lit_api.py" \
         "./lit-review-skill/scripts/lit_api.py" "../lit-review-skill/scripts/lit_api.py" \
         "../lit-review/scripts/lit_api.py"; do
  [ -n "$p" ] && [ -f "$p" ] && LIT="$p" && break
done
if [ -n "$LIT" ] && [ -n "$PY" ] && "$PY" "$LIT" --help >/dev/null 2>&1; then
  echo "lit_api available: true  ($LIT)"
else
  echo "lit_api available: false"
fi
```

`--help` 不連網、成本為零；exit 0 代表可用，unknown subcommand 會回 2。Windows 上直譯器名稱不一定是 `python`（可能只有 `py`），macOS／Linux 上通常是 `python3`——上面兩段都先解析直譯器再用，不要假設 `python` 一定在 PATH。

**永遠不要自動安裝、下載、clone 或複製 lit-review。偵測是唯讀的。** 也不要把階 2 的判定用階 0 的措辭寫出來——「已查核」這三個字只屬於階 0。

## 二、漏斗契約（順序是契約的一部分，由便宜到貴）

```
每個候選：       search ×2 → brief → pick 2–5 篇 → 下判定
判 DONE/CROWDED：verify（殺手來自 lit_api 以外時必跑）→ retract → versions（只有預印本時）
存活時：         snowball --direction citations 跑最近鄰（見 SKILL.md 的滾雪球規則）
整輪結束：       自行組檔 → export-xml（殺手文獻＋淘汰理由 → EndNote，見本檔〈六、交棒到 EndNote〉）
```

**不要直接讀 `search` 的原始 JSON——那會毀掉漏斗。** 只讀 `brief` 的行，再 `pick` 你要的索引。這條也決定了第 1 步預設清單裡 N 與 M′ 的分工：`brief` 的行數是 N（標題層），`pick` 出來讀過摘要的才是 M′，兩個數字不可互相頂替。

```powershell
python "$LIT" search "<候選主張，領域術語，英文>" --limit 12 > "gap_C01_q1.json"
python "$LIT" search "<最近鄰查詢>" --limit 12 > "gap_C01_q2.json"
python "$LIT" brief "gap_C01_q1.json"
python "$LIT" pick "gap_C01_q1.json" 0 3 5 > "gap_C01_picked.json"
python "$LIT" verify --title "Exact title as cited" --authors "Chen, L.; Wang, H." --year 2023
python "$LIT" verify-batch "gap_kill_claims.json" --workers 4
python "$LIT" retract 10.1145/3411764.3445374 10.1016/j.ijhcs.2022.102876
python "$LIT" versions "ARXIV:2301.12345"
python "$LIT" snowball "DOI:10.1145/3411764.3445374" --direction citations --limit 20 > "gap_C01_cit.json"
python "$LIT" snowball "DOI:10.1145/3411764.3445374" --direction references --limit 20 > "gap_C01_ref.json"
python "$LIT" fulltext 10.1016/j.ijhcs.2022.102876
python "$LIT" export-xml "gap_killers.json" > "gap_killers.xml"
```

bash 下同樣的指令，只要把 `python` 換成偵測到的 `$PY`、路徑引號照留即可。

## 三、各指令的判讀與坑

- **`search`**：回傳的 `total` 只是寬鬆關鍵字計數，**不能當 CROWDED 的證據**；只有實際 `pick` 出來讀過的文獻才算數。S2 回 429 時會退回 OpenAlex，那個分支**沒有 `total` 欄位**，不要寫依賴它的邏輯。**`total` 與 `results` 是兩個不同的母體**：`total` 是整個索引對這組關鍵字的寬鬆計數，`results` 是相關性排序後真的回給你的那一頁（長度 ≤ `--limit`，可能更短）。**在頁面裡數出來的任何比例（年份、有無 DOI、期刊分布）都只描述那一頁，不描述 `total`**——兩者之間沒有子集關係，任何把它們用「其中」串起來的句子都是假的。`search` **有** `--year`（如 `--year 2025-`），它會讓 `total` 變成年份過濾後的總數，那才是與未過濾 `total` 同母體、可以相減的數字；代價是同一組查詢詞要多跑一次檢索，**landscape 的〈狀態〉句型不需要它**（見 SKILL.md〈證據標準〉），真的跑了就在〈檢索紀錄〉另起一列、查詢詞照抄並註明 `--year`。
- **`brief`**：一行一筆，**只有標題／年份／被引數／venue／DOI，沒有摘要**。行尾旗標 `A`＝有摘要可讀、`P`＝有 OA PDF、`!`＝品質紅旗。任何「摘要層」的判斷都不能建立在 brief 行上。
- **`pick`**：讀 brief 選中那幾筆的完整資料（含摘要）。DONE 的逐字引句、G4 的效果量、第 1 步的 M，全部只能來自這裡。
- **`verify`**：回 `not_found` → **這個淘汰無效**，候選回到存活或待確認，報告寫「宣稱的既有研究查無，判定撤回」；回 `partial_failure` 是上游故障、不是「不存在」，重試即可；出現 `single_source_degraded` 要在報告寫明該判定只靠單一索引。中文標題會回 `unsupported_title` 並以 exit 1 結束——**那是「換索引」的信號，不是「查無」**。
- **`retract`**：回 🚨 → 淘汰無效；回 ❓ 查詢失敗**不等於乾淨**，報告寫「未查」。`coverage_caveat` 在**每一筆乾淨記錄**上都會出現（與年份無關，不要拿它當年份判斷的依據）；**殺手文獻的年份要從 `search`／`verify` 的書目取，`retract` 的回傳沒有年份欄**。
- **`versions`**：找不到 `published_version` 的預印本只能支持 CROWDED，**不能支持 DONE**（改標〔已有人在做（預印本）〕進第三節）；找得到就改對那個正式版 DOI 重跑 `retract`。
- **`snowball`**：**不要用 `--direction both`**——`brief`／`pick` 只會讀到第一個命中的鍵，另一個方向會無聲消失。兩個方向分兩個檔。
- **`fulltext`（G5 必經）**：它回的是**位置不是內文**——`oa_locations`（OA 連結）或 `how_to_get`（機構取得途徑），不繞過付費牆。**拿到 OA 連結後還要真的去讀**：用 WebFetch／PDF 讀取工具／EndNote 的 `read_pdf_section`，讀「方法—測量」段落，把題項文字或量表名稱**逐字引出來**。讀不到就標〔待全文查證〕移進第三節，不要用印象補。
- **`.env`**：`lit_api.py` 讀 `<cwd>/.env` 然後 `~/.env`，**不讀 skill 資料夾自己的 `.env`**。沒有 `S2_API_KEY` 時 `search` 會自動退回 OpenAlex，但 `verify` 不會，只會降級成單源並說明；`fulltext` 的 Unpaywall 查詢需要 `CROSSREF_MAILTO`，沒設就只剩 S2／OpenAlex 的 OA 欄位。

## 四、降級階梯（報告表頭必須寫實際落在哪一階）

| 階 | 條件 | hunt 缺口獵捕的〈文獻工具〉必寫 | landscape 領域地形的〈文獻工具〉必寫 |
|---|---|---|---|
| 0 | lit_api 可用 | `lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）` | `lit-review lit_api.py（本模式僅用 search／brief／pick，未執行機器查核）` |
| 1 | 檔案在但 python 壞了 | `僅程序沿用 lit-review，未執行機器查核；存在性與撤稿未經驗證` | `僅程序沿用 lit-review，未執行機器查核；本模式無 brief／pick，筆數來自實際使用的檢索工具` |
| 2 | 沒有 lit-review，但有其他檢索工具 | `<實際用的工具名>；未做撤稿查核，存在性僅單源` | `<實際用的工具名>；本模式無 brief／pick，錨定文獻可能無識別碼` |
| 3 | 完全沒有檢索能力 | `本次無法執行淘汰步驟` | `本次無檢索能力，家族與錨定文獻均無工具回傳可依據` |

**這張表是〈文獻工具〉那一行的唯一出處**，兩個模式共用同一組階與同一組條件，但**各讀自己那一欄**：報告表頭逐字照抄本次落到的那一階、本模式那一格，不要另外造句（以前 SKILL.md 的樣板裡另有一份四行版本，兩份對不上——同一個 Consensus MCP 在那邊算階 1、在這裡算階 2，於是〈覆蓋率警告〉該不該掛就出現兩個答案。現在只留這一份）。階 2 那一格的 `<實際用的工具名>` 是唯一要自己填的位置，填真的用過的那個工具名。

**為什麼要分兩欄。** 以前只有一欄，而那一欄的階 0 寫的是「存在性、撤稿、滾雪球均已機器查核」——那三件事是淘汰配備，landscape 在定義上不跑（SKILL.md〈證據標準〉的〈不跑〉那一條）。同一個字串在 hunt 是實話、在 landscape 是假話，而規格又要求逐字照抄，於是每一份地形報告的表頭都在宣告三件它被禁止做的檢查，只能靠內文另寫一段去追認。**規格不該要求任何一個模式寫下自己知道是假的東西**：兩欄之後，兩邊都逐字照抄、兩邊都是實話，也不必再補救。

**跨欄照抄是一筆違規**（地形報告寫 hunt 欄的字串、缺口報告寫 landscape 欄的字串都算）：報告型別由第一行的判別字串決定，〈文獻工具〉的合法值就只有那一欄的四個字串。這也是這張表要維持階與階之間**看得出差別**的理由——階 0 那一格點名 `lit_api.py`、寫「僅用 search／brief／pick」，階 1／2 寫「無 brief／pick」，階 2 還要填工具名：一份階 2 的報告拿不出階 0 那一格的形狀，**階 2 就讀不成階 0**。

landscape 的階數影響只有三件事：階 2／3 的錨定文獻可能拿不到識別碼（照寫、標〔無識別碼〕）；沒有 `brief`／`pick` 時〈狀態〉的檢索句型改寫成實際用的工具回傳了幾筆（句型見 SKILL.md〈證據標準〉，兩段子句的角色不變，只是第一段多半變成「未回傳總數」）；階 3 沒有任何工具回傳可依據，〈狀態〉一律〔涵蓋不足〕、錨定文獻寫不出來——**這一階不得用印象補齊家族清單與文獻**，那正是〈不捏造引用〉那一條。landscape **不需要**〈覆蓋率警告〉那一行——那句話講的是「存活清單偏長不是新穎性證據」，而 landscape 沒有存活清單。

**階 2／3 的淘汰標準**（沒有這一條，淘汰在這兩階等於做不到）：一筆**暫定淘汰**必須同時具備 (a) 逐字抄回的標題與作者年份、(b) 摘要或摘要片段的**逐字引句**、(c) 至少一個可點的 URL。**三項齊備只讓它成為「暫定淘汰」，不讓它成為 DONE。** 決定它落在哪一節的是識別碼：

- **有識別碼**（DOI／arXiv ID／S2 corpus ID 至少一個）→ 可判 DONE，寫進**四、已淘汰**，並一律加註〔單源、未經識別碼查核〕（意思是識別碼沒有經 `verify`／`retract` 機器查核過，不是沒有識別碼）。
- **沒有識別碼**（`web_search` 只給得出可點 URL）→ **一律〔DONE?〕寫進三、待確認，永遠不進四、已淘汰**。〈還缺哪一項證據〉寫「殺手文獻只有 URL、沒有識別碼」，〈補齊的具體動作〉寫「補查該篇 DOI／arXiv ID，或改用查得到識別碼的來源重搜」。
- **(a)(b)(c) 任一項不齊** → 一樣是〔DONE?〕進三、待確認。

**可點的 URL 不能取代識別碼**，這條在任何一階都成立，與 SKILL.md〈誠實紀律〉「無識別碼文獻不得單獨支撐 DONE」是同一條規則的兩種說法，格式查核器的 ID-01 也是照這條寫的。CROWDED 同理：三篇都要滿足 (a)(c)，而且第四節那一列的〈識別碼〉欄要填得出來；填不出來就整列退回三、待確認（暫定狀態〔DONE?〕），不得列入已淘汰。

這條的代價要講清楚：階 2／3 只有 `web_search` 時，會有一批候選卡在〔DONE?〕而不是被乾淨地淘汰，**存活與待確認的清單因此偏長——那是工具限制的徵狀，不是新穎性的證據**，正是〈覆蓋率警告〉那一行要說的事。這比反過來好：假的 DONE 沒有人會再去翻。

**階 2／3 只跑得動四個生成器，不是六個**——這件事要在報告的〈降級聲明〉寫出來，不要靜默略過。沒有 `brief`／`pick` 就沒有標題層／摘要層的分工，量化預設的取樣框（N／M′／M／K′／K）在定義上組不出來，所以**第一節的每一條預設一律標〔印象，未驗證〕**（對應 SKILL.md〈rgh-block〉區塊裡的 `"status": "impression"` 與 `"frame": null`——這一階不存在合法的 `framed`，硬填 `frame` 就是把組不出來的數字編出來）；而印象級預設不得長出候選，於是 **G3 一律寫「不適用（無摘要層抽樣工具）」**。**G5** 走的是 `lit_api.py fulltext` 拿全文位置，這一階也沒有：**若能自行找到 OA PDF（`web_search` 撞到、或期刊頁面直接掛 PDF）並真的讀到「方法—測量」段落，G5 仍可照常進行**；找不到就寫「不適用（無全文取得途徑）」，**不得用摘要或印象補**。可以照跑的是 G1、G2、G4、G6。硬湊 `pick` 索引來讓 G3 看起來成立，是這一階最容易犯、也最難被抓到的假造。

階 2 還要注意：撤稿檢查**沒有便宜的替代品，不要假裝做過**，報告寫「撤稿檢查：未執行」，並請使用者自行到 Retraction Watch 查；滾雪球退回 Google Scholar 的 Cited by，標「非 API，覆蓋不完整」；品質紅旗不可用時，**不要憑記憶自創期刊品質判斷**。

**階 2／3 一定要在表頭加〈覆蓋率警告〉那一行**（逐字：本次未使用可機器查核的檢索後端，存活清單偏長是預期結果，不構成新穎性證據。）。這一階存活清單長是工具限制的徵狀，不是新穎性的證據，使用者必須在讀第二節之前就知道。階 3 另外把「本次未執行任何檢索，以下僅為候選生成，不含新穎性驗證」寫在表頭最後一行，全部候選進第三節、狀態一律〔未驗證〕。

## 五、中文索引

符合 SKILL.md〈工具準備〉兩個例外之一時，**任何 OPEN 或 ADJACENT 判定之前必須另跑一輪中文檢索**：臺灣博碩士論文加值系統（NDLTD）、華藝線上圖書館（Airiti）、TCI。工具端用 `web_search` 搭 `site:ndltd.ncl.edu.tw`、`site:airitilibrary.com`，或直接用中文正規術語——**台灣與中國大陸術語不同，兩套都要試**。

中文文獻**不得**用英譯標題丟進英文資料庫硬查，那會製造錯誤配對；`lit_api.py verify` 對中文標題會回 `unsupported_title` 並以 exit 1 結束，看到這個回應是「切換索引」的信號，不是「查無」。中文檢索列進第六節時，〈查詢詞〉欄照抄中文查詢字串，並在該列註明索引名。

環境無法檢索這些庫時，**必須在報告明寫**（不得省略、不得假裝已查）：「中文文獻未檢索，本報告的新穎性判定覆蓋率有限，請自行至 NDLTD／Airiti 補查後才下結論。」

**兩個例外都不符合的題目**（既非在地界定，使用者也不在華語學術體系）：表頭〈中文索引〉逐字寫「不適用（題目非在地界定，使用者不在華語學術體系）」，**不寫「未檢索」、也不掛上面那句覆蓋率警語**。這個值只有在兩個例外都不成立時才合法；只要沾到任何一個例外（題目牽涉台灣／華語圈／特定機構、產業或法規，或使用者的論文要交給華語學術體系審查），就只能在「已檢索 <索引名>」與「未檢索（附覆蓋率警語）」之間選。理由是那句警語要留給真的有覆蓋率風險的報告——每一份都掛，等於每一份都沒掛。

## 六、交棒到 EndNote（`export-xml` 的組檔步驟）

**本技能沒有任何一步會自動產生 `gap_killers.json`**——`pick` 的輸出預設走 stdout，`search` 存的是各候選各自的檔。要匯進 EndNote 得先自己組：

1. 把每個殺手文獻的 `pick` 輸出（`> gap_C01_picked.json`）合併成**一個 JSON 陣列**，存成 `gap_killers.json`。
2. **逐筆補上 `research_notes` 欄**，寫入：判定（DONE／CROWDED）、淘汰理由、對應的候選編號（C01…）。`export-xml` 只會把已存在的 `research_notes` 帶進 Research Notes 欄；**沒有這一欄，匯出的就只是一份普通書目**，三個月後你會看不出某個方向為什麼被砍掉。
3. 再跑 `python "$LIT" export-xml "gap_killers.json" > "gap_killers.xml"`，匯入 EndNote。

其餘交棒（`map`／`matrix`／`gap`／`check`）見 SKILL.md〈交棒回 lit-review〉。第 3 步的淘汰不呼叫 `gap`，交棒階段才呼叫。
