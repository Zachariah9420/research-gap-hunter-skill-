# 完整走一遍：一個教育領域的研究缺口獵捕

> # ⚠️ 本檔所有文獻都是假的
>
> 這份檔案裡的**每一筆文獻、作者、年份、DOI、系統編號、摘要引句、命中筆數，全部是為了
> 示範而編造的**，不是真實文獻，也不是任何一次真實檢索的結果。辨識方式有三個，**每一筆
> 都至少中一個，沒有例外**：
>
> 1. **所有標題都加了 `[示例]` 前綴**（中文標題也一樣）。
> 2. **所有 DOI 都用 `10.0000/EX.xx` 這個未註冊的 Crossref 前綴**，永遠解析不出東西。
> 3. **DOI 以外的識別碼也一律帶 `EX.` 這個示例編號**——本檔唯一的非 DOI 識別碼是那個
>    NDLTD 系統編號，寫成 `ncl.edu.tw/EX.90`，不是真實的學年度＋校院所代碼格式，
>    貼進 NDLTD 查不到任何東西。
>
> 只用作者姓氏與年份提到的文獻（沒有標題可掛 `[示例]` 的那種），一律在同一句裡註明
> 「示例作者」。**不要引用本檔的任何一筆文獻，不要拿去餵給 `retract` 或 `check`。**
>
> 真實跑出來的報告不會有 `[示例]` 前綴，不會有 `10.0000/` 的 DOI，也不會有 `EX.` 開頭的
> 系統編號——看到這幾個東西就代表你在看這份教學檔，不是在看結果。
>
> 這裡示範的是**流程與判定的形狀**：什麼證據可以殺死一個候選、什麼證據不行、
> 以及一個判定在什麼情況下應該被自己推翻。

**這一份走的是模式二（缺口獵捕）**——貴的那一種：先回答四個問題，再跑數十次檢索，
每個候選都要被主動殺一次。模式一（領域地形）的短範例是
[`landscape_example.md`](landscape_example.md)，那一份不淘汰、不判新穎性，
兩份是不同的產物，不要互相對照格式。

主題刻意挑一個平凡的教育題目（國中校園手機禁令），跟本 skill 作者自己的研究領域無關，
免得範例被當成現成答案抄走。

**這份檔案怎麼讀**：中間那一段被 `format-check: report-start` 與 `format-check: report-end`
兩行 HTML 註解標記包起來的，是**報告本體**，它逐字遵守 `SKILL.md` 第 5 步的輸出格式；
`python evals/format_check.py examples/worked_example.md` 只會查這一段，回傳 0。
標記之外的都是教學說明（第 0 步的問答、後面三個附錄），不是報告內容，所以不受查核——
這也是為什麼附錄的教學文字可以引用那些報告裡不准寫的措辭。

---

## 第 0 步：盤點條件（使用者的實際回答）

| # | 問題 | 使用者回答 |
|---|---|---|
| 1 | 領域 | 教育心理／中等教育政策 |
| 2 | 直覺 | 「我們學校禁手機兩年，成績沒什麼變，但學生看起來焦慮反而更高」 |
| 3 | 獨有資料 | 任教學校三學年的段考成績、出缺勤、輔導室個案紀錄（去識別化後可用，校方已口頭同意） |
| 4 | 硬性限制 | 距離口試 5 個月；資料已收集完畢；指導教授專長是課程與教學，不熟計量 |

**降級聲明**：無（四項都答了）。

## 第 0.5 步：貢獻判準

使用者所在系所（教育研究所碩士班）接受的判準是**情境移轉**與**在地驗證**，不是理論新穎。
→ 這一點直接改變後面的淘汰門檻：**文獻密集（CROWDED）不自動構成淘汰理由**，
要問的是「台灣國中的情境差異有沒有理由讓結果不同」。

## 〈時程停損〉的結論先講（因為它改變了整份報告的目的）

（這條規則以前是獨立的「第 3.5 步」，現在住在**第 4 步〈時程停損〉**裡面，內容沒變，
只是不再是一個獨立步驟。本檔以下一律用名字稱呼它，不用編號。）

第 0 步第 4 項：**5 個月、資料已收完、已進入寫作階段**。
→ 依停損閘，預設建議是**維持題目、重寫貢獻定位**，六個生成器只用來磨利框架。
→ 所以下面的候選不是「換題目的選項」，是「同一批資料可以誠實宣稱什麼」的選項。
**這件事在報告開頭就要講清楚，不能等到最後才講。**

---

<!-- format-check: report-start -->
# 研究缺口報告：國中校園智慧型手機禁令與學習成效

**模式**：完整獵捕
**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）
**貢獻判準**：情境移轉＋在地驗證（非理論新穎）
**中文索引**：已檢索 NDLTD 臺灣博碩士論文加值系統、Airiti 華藝線上圖書館
**降級聲明**：無
**候選結算**：生成 12 ＝ 存活 2 ＋ 待確認 4 ＋ 已淘汰 6

> 本段是示範用的合成報告：所有文獻、DOI、命中筆數皆為虛構，識別碼一律使用未註冊的
> `10.0000/` 前綴，不對應任何真實出版品。
>
> **時程判定（第 4 步〈時程停損〉）**：使用者距離口試 5 個月且資料已收完，本報告**不建議換題目**。
> 以下候選是用來決定「這批資料該被寫成哪一個宣稱」，不是用來另起爐灶。

## 一、領域共識與未被質疑的預設

- 主流立場：校園手機禁令能小幅提升學業表現，效果集中在原本成績較低的學生（代表文獻：`[示例] Banning smartphones in secondary schools: attainment effects across four districts`，Aldridge & Norreys (2018)，DOI:10.0000/EX.01）
- 主流立場：禁令的效果被當成注意力問題處理，而不是校園作息與同儕互動的制度問題（代表文獻：`[示例] Attention, distraction and the case for phone-free classrooms`，Варга & Lindqvist (2020)，DOI:10.0000/EX.03）
- 預設 A1：〈禁令的效果來自「減少課堂分心」這個中介機制〉｜標題層掃描 24 篇（檢索詞 `smartphone ban school achievement`，limit 24）｜摘要層精讀 8 篇（pick 索引 0,1,3,5,7,9,12,15），其中 6 篇沿用此預設｜推翻性檢索 `phone ban achievement alternative mechanism sleep peer` 回傳 9 篇，讀後 2 篇確實檢驗過此預設｜樣本來源：2015–2025，Semantic Scholar ＋ Crossref
- 預設 A2：〈結果變項應該是標準化測驗分數〉｜標題層掃描 24 篇（檢索詞 `mobile phone policy secondary school outcome`，limit 24）｜摘要層精讀 7 篇（pick 索引 0,2,4,6,8,11,13），其中 6 篇沿用此預設｜推翻性檢索 `phone restriction wellbeing outcome measurement` 回傳 11 篇，讀後 3 篇確實檢驗過此預設｜樣本來源：2015–2025，Semantic Scholar
- 預設 A3：〈禁令是一個二元且單向的處理：實施之後不會被撤除〉｜標題層掃描 19 篇（檢索詞 `phone policy implementation fidelity school`，limit 19）｜摘要層精讀 5 篇（pick 索引 1,2,4,7,9），其中 4 篇沿用此預設｜推翻性檢索 `school technology policy reversal discontinuation` 回傳 8 篇，讀後 3 篇確實檢驗過此預設｜樣本來源：2015–2025，Semantic Scholar ＋ Crossref
- 預設 A4：〈禁令研究幾乎都在西方國家做〉〔印象，未驗證〕——摘要層精讀只有 2 篇（M′ < 3），不得作為 G3 輸入

## 二、存活候選（生成 12 個 → 存活 2 個）

### 候選 1（C01）：在禁令實施期間，手機依賴程度高的學生，其焦慮指標的學期內變化軌跡與低依賴組不同

- **缺口類型**：G6 未被訓練過的資料（使用者任教學校三學年的輔導室紀錄）
- **新穎性判定**：ADJACENT
- **搜尋證據**：查詢 1 `smartphone ban adolescent anxiety longitudinal`（回傳 12 筆）；查詢 2 `mobile phone dependence school policy wellbeing`（回傳 12 筆）；查詢 3 `phone restriction anxiety trajectory within-person`（回傳 4 筆）
- **最接近的既有研究**：`[示例] School phone restrictions and adolescent wellbeing: a cross-sectional survey of 3,100 students`，Okonkwo et al. (2022)，DOI:10.0000/EX.05。差異維度是分析單位與時間尺度：該研究是單一時點的橫斷面校際比較（學校為分析單位），本候選是同一批學生跨三學期的組內變化（個人×學期）。為什麼這個差異有理由造成不同結果：橫斷面比較會被「哪一種學校會採用禁令」的選擇效應污染，組內設計把學校層級的固定差異吃掉；若焦慮上升是禁令造成的而非學校本身特性造成的，兩種設計會給出方向相反的估計——這是可被否證的預測，不是換一個標籤。
- **已排隊檢查**：讀了 EX.05 的 limitations 與 future work，只提到樣本地區侷限，未點名縱貫或組內設計；`snowball --direction citations DOI:10.0000/EX.05` 於 2026-08-10 執行，回傳 20 筆，其中未見以組內軌跡為設計者。→ 不是已排隊。
- **可行性**：需要學生層級的重複測量。使用者手上有三學年輔導室紀錄，但焦慮指標不是標準量表，是輔導教師的文字紀錄——這是最大的風險，見下。
- **指導教授適配**：要交還使用者確認——指導教授專長是課程與教學、不熟計量，組內固定效果模型他可能帶不動，也可能在口試時無法替你接話。問他：這個做法你願意帶嗎？需不需要找計量方向的委員？
- **最可能失敗的原因**：輔導室的文字紀錄無法轉成可信的焦慮量尺，整個縱貫比較會塌掉；並列的社會性風險是指導教授不熟這個方法。

### 候選 2（C02）：台灣國中「集中保管」與「自主保管」兩種手機管理制度的成效比較

- **缺口類型**：G1 負空間（制度變體從未被分開比較）
- **新穎性判定**：INCREMENTAL（不是 OPEN，理由見中文索引那一列的搜尋證據）
- **搜尋證據**：查詢 1 `phone storage policy secondary school collection versus self-custody`（回傳 2 筆，皆不相關）；查詢 2 `mobile phone confiscation policy student outcomes`（回傳 12 筆，皆為英美全面禁令）；查詢 3（中文索引）NDLTD「國中 手機 管理 成效」（回傳 2 筆）與 Airiti「校園手機 集中保管」（回傳 1 筆）
- **最接近的既有研究**：`[示例] 國中校園手機集中保管制度對學生學習投入之影響`，林 (2021，示例作者)，NDLTD 系統編號 `ncl.edu.tw/EX.90`（示例編號，非真實系統編號）。差異維度是研究設計與選擇效應：該論文比較的是不同縣市的兩群學校，未處理「哪一種學校會採用集中保管」的採用選擇；本候選用的是同一所學校在制度變更前後的縱貫紀錄。為什麼這個差異有理由造成不同結果：跨校比較把制度效果與校風混在一起，校內前後設計把校風固定住，兩者若給出不同方向，就說明既有估計主要來自選擇而非制度。
- **已排隊檢查**：該論文的建議事項提到「宜擴及不同管理型態之比較」，等於已點名這個方向，但未指定設計；這一筆是 NDLTD 學位論文，沒有可用的被引查詢 API（`lit_api.py` 對中文標題會回 `unsupported_title`），所以滾雪球這一步改成人工——2026-08-10 在華藝的「引用本文」頁逐筆掃過 6 筆，其中未見校內前後設計者。**這一格寫「人工檢索」不是偷懶，是誠實：中文索引沒有 API，寫成 `snowball` 執行過才是造假。**→ 屬於已被點名但尚未被做，因此本候選定位為在地驗證而非新穎主張。
- **可行性**：資料已在手上，5 個月做得完。
- **指導教授適配**：符合他的專長（制度與課程實施），風險低；仍要確認系所是否認可「在地驗證」作為主要貢獻。
- **最可能失敗的原因**：制度變更的時間點若與其他校務變動重疊，前後比較無法歸因。

## 三、待確認（證據不足，尚未定案）

| 候選 | 暫定狀態 | 還缺哪一項證據 | 補齊的具體動作 |
|---|---|---|---|
| C03 借用「公共場所禁菸令外溢效應」框架分析手機禁令 | 〔待驗證〕 | G2 三段式的第 3 項沒過：說不出禁菸研究的「二手暴露量」對應到手機情境的哪一個可測量的量，也說不出這個對應要怎麼被否證 | 讀 EX.71 的方法段，逐字抄出它的暴露量定義，寫成一句可測量的對應式；寫不出來就結案為不適用，不進存活 |
| C06 兩份 meta-analysis 對禁令效果量結論相反 | 〔矛盾已觀察，機制未知〕 | 兩個效果量都逐字抄自摘要（`d = 0.17, 95% CI [0.08, 0.26]` 對 `d = -0.02, 95% CI [-0.11, 0.07]`），信賴區間確實不重疊；但不一致的原因只能從全文的 method 段判斷，本次未取得全文 | 對 EX.31／EX.32 跑 `fulltext`，比對兩篇的納入條件與效果量換算方式，找出機制才算研究問題 |
| C08 現行「課堂分心」量表其實測到的是自陳的注意力自我評價 | 〔待全文查證〕 | 量表題項只存在於全文，EX.81 無 OA 版本，尚未讀到方法—測量段落 | 走館際合作或 `fulltext` 取得全文，讀方法段並逐字引出題項文字，才可以下構念質疑 |
| C10 禁令對「上課時間以外」的手機使用是否產生替代效果 | DONE? | 標題高度相似的 `[示例] Displacement effects of school device restrictions`（Fenwick et al., 2023，示例作者）只讀到標題，摘要未取得；母體與結果變項兩項對不齊 | 跑 `pick` 取該篇摘要，比對母體／處理／結果變項／研究設計四項，四項齊了改判 DONE，不齊就回到存活候選重跑一輪 |

## 四、已淘汰

| 候選 | 判定 | 淘汰原因 | 關鍵文獻 | 識別碼 | 發表型態 | 撤稿檢查 |
|---|---|---|---|---|---|---|
| C04 禁令解除後的學習表現反彈 | CROWDED（由 OPEN 改判） | 第一輪用日常用語查詞造成假的 OPEN，換成領域正規術語後命中三篇，分別涵蓋本候選的三個子問題：反彈是否發生（EX.21）、反彈幅度是否超過基線（EX.22）、哪些學生反彈最大（EX.23）；逐一比對後沒有剩下的子問題。完整經過見附錄一 | `[示例] De-implementation of school technology policies: what happens after reversal` (2021)；`[示例] Policy discontinuation effects on adolescent screen behaviour` (2022)；`[示例] Rebound effects following removal of classroom device restrictions` (2023) | DOI:10.0000/EX.21；DOI:10.0000/EX.22；DOI:10.0000/EX.23 | 期刊、期刊、會議 | 已查，Crossref 無記錄（2026-08-10） |
| C05 禁令對低社經背景學生的差別效果 | CROWDED | 三篇分別涵蓋本候選的三個子問題：是否隨家戶所得而異（EX.11）、是否隨基線成績而異（EX.12）、是否由家庭數位近用差異驅動（EX.13）；剩餘子問題為零，故非 ADJACENT。拆解表見附錄二 | `[示例] Heterogeneous effects of school phone bans by family income` (2020)；`[示例] Who benefits from phone restrictions? A quantile analysis` (2022)；`[示例] Digital access inequality and classroom phone policy` (2023) | DOI:10.0000/EX.11；DOI:10.0000/EX.12；DOI:10.0000/EX.13 | 期刊×3 | 已查，Crossref 無記錄（2026-08-10） |
| C07 「禁令有效是因為減少課堂分心」這個中介機制從未被直接檢驗 | DONE | 摘要逐字引句：「We test whether the achievement gain from the ban is mediated by observed off-task behaviour, and find the mediation path accounts for 61% of the total effect.」母體、處理、結果變項、研究設計四項全中，對照表見附錄二 | `[示例] Does attention mediate the effect of phone bans? A classroom observation study`，Prieto et al. (2021) | DOI:10.0000/EX.02 | 期刊 | 已查，Crossref 無記錄（2026-08-10） |
| C09 借用「道路限速政策順從度」框架分析師生對禁令的順從 | DONE | 摘要逐字引句：「We adapt the speed-limit compliance framework to school phone bans and show that perceived enforcement certainty predicts compliance more strongly than perceived harm.」四項對齊，含同樣的框架移植與順從度結果變項 | `[示例] Compliance frameworks transferred from traffic policy to school device rules`，Halvorsen (2022) | DOI:10.0000/EX.41 | 期刊 | 已查，Crossref 無記錄（2026-08-10） |
| C11 現行禁令研究使用的「學業投入」量表其實測到的是課堂服從 | DONE | 摘要逐字引句：「A confirmatory factor analysis shows the engagement scale used in phone-ban studies loads primarily on classroom compliance rather than cognitive engagement.」母體與量表皆與本候選相同，研究設計同為因素效度檢驗 | `[示例] What do engagement scales measure in device-policy research?`，Ceballos & Wu (2023) | DOI:10.0000/EX.51 | 期刊 | 已查，Crossref 無記錄（2026-08-10） |
| C12 以校內出缺勤紀錄取代自陳量表衡量禁令的行為效果 | CROWDED | 三篇分別涵蓋本候選的三個子問題：行政紀錄作為結果變項的效度（EX.61）、出缺勤對政策變動的敏感度（EX.62）、與自陳量表的收斂效度（EX.63）；剩餘子問題為零 | `[示例] Administrative records as outcome measures in school policy evaluation` (2019)；`[示例] Attendance sensitivity to school rule changes` (2021)；`[示例] Convergent validity of self-report and administrative behaviour measures` (2022) | DOI:10.0000/EX.61；DOI:10.0000/EX.62；DOI:10.0000/EX.63 | 期刊×2、會議×1 | 已查，Crossref 無記錄（2026-08-10） |

## 五、下一步

- 本週先翻三份輔導室紀錄，判斷文字紀錄能不能轉成可信的焦慮量尺。這一題決定候選 1 活不活。
- 去 NDLTD 把那兩篇碩士論文的全文抓下來讀方法章，確認它們處理到什麼程度——候選 2 的貢獻宣稱要怎麼寫，取決於這件事。
- 對 EX.31／EX.32 兩份 meta-analysis 跑 `fulltext`，拿得到全文，C06 就有機會從〔矛盾已觀察，機制未知〕變成一個真的研究問題；拿不到就在報告寫明沒拿到。
- C10 最便宜：一次 `pick` 就能決定它是 DONE 還是回到存活，先做它。
- 固定動作：把存活候選拿給指導教授，直接問——哪一個你願意帶？

## 六、檢索紀錄（不得省略）

本次檢索後端：lit_api.py（另含 NDLTD／Airiti 人工檢索，非 API）

| # | 階段／候選 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | 第1步-共識 | `smartphone ban school achievement` | 24 | `[示例] Banning smartphones in secondary schools: attainment effects across four districts` / `[示例] Phone-free schools and test scores` / `[示例] Mobile device rules and learning outcomes` |
| 2 | 第1步-共識 | `mobile phone policy secondary school outcome` | 24 | `[示例] Attention, distraction and the case for phone-free classrooms` / `[示例] Outcome measures in device-policy research` / `[示例] School rules and adolescent behaviour` |
| 3 | 第1步-推翻A1 | `phone ban achievement alternative mechanism sleep peer` | 9 | `[示例] Sleep as a pathway from phone use to attainment` / `[示例] Peer interaction changes after device restriction` / `[示例] Competing mechanisms in school technology policy` |
| 4 | 第1步-推翻A2 | `phone restriction wellbeing outcome measurement` | 11 | `[示例] Beyond test scores: wellbeing outcomes of device rules` / `[示例] Measuring adolescent wellbeing in policy evaluation` / `[示例] Outcome selection bias in education policy studies` |
| 5 | 第1步-推翻A3 | `school technology policy reversal discontinuation` | 8 | `[示例] De-implementation of school technology policies: what happens after reversal` / `[示例] When schools reverse device bans` / `[示例] Policy churn in secondary education` |
| 6 | C01 | `smartphone ban adolescent anxiety longitudinal` | 12 | `[示例] School phone restrictions and adolescent wellbeing: a cross-sectional survey of 3,100 students` / `[示例] Anxiety and device restriction in schools` / `[示例] Wellbeing outcomes of classroom phone policies` |
| 7 | C01 | `mobile phone dependence school policy wellbeing` | 12 | `[示例] Phone dependence and school adjustment` / `[示例] Problematic use and classroom rules` / `[示例] Dependence profiles among secondary students` |
| 8 | C01 | `phone restriction anxiety trajectory within-person` | 4 | `[示例] Within-person variation in adolescent affect` / `[示例] Daily diary study of phone use` / `[示例] Trajectories of school-related anxiety` |
| 9 | C02 | `phone storage policy secondary school collection versus self-custody` | 2 | `[示例] Locker policies in US high schools` / `[示例] Device management in one-to-one programmes` |
| 10 | C02 | `mobile phone confiscation policy student outcomes` | 12 | `[示例] Confiscation practices and student compliance` / `[示例] Enforcement intensity in device policy` / `[示例] Banning smartphones in secondary schools: attainment effects across four districts` |
| 11 | C02 | NDLTD「國中 手機 管理 成效」（人工檢索，非 API） | 2 | `[示例] 國中校園手機集中保管制度對學生學習投入之影響` / `[示例] 手機使用規範與國中生自我調節學習之關係` |
| 12 | C02 | Airiti「校園手機 集中保管」（人工檢索，非 API） | 1 | `[示例] 中等學校行動載具管理策略之個案研究` |
| 13 | C03 | `secondhand smoke spillover framework behavioural policy transfer` | 7 | `[示例] Spillover effects of public smoking bans on household behaviour` / `[示例] Exposure metrics in behavioural policy` / `[示例] Transferring exposure models across domains` |
| 14 | C04 | `phone ban lifted rebound student performance` | 3 | `[示例] Smartphone addiction treatment outcomes` / `[示例] Digital detox interventions in young adults` / `[示例] Problematic phone use and relapse` |
| 15 | C04 | `smartphone ban removal academic outcomes` | 1 | `[示例] Screen time and sleep in adolescents` |
| 16 | C04（術語校正後） | `de-implementation school technology policy student outcomes` | 12 | `[示例] De-implementation of school technology policies: what happens after reversal` / `[示例] Policy discontinuation effects on adolescent screen behaviour` / `[示例] Rebound effects following removal of classroom device restrictions` |
| 17 | C05 | `heterogeneous effects school phone ban socioeconomic` | 12 | `[示例] Heterogeneous effects of school phone bans by family income` / `[示例] Who benefits from phone restrictions? A quantile analysis` / `[示例] Digital access inequality and classroom phone policy` |
| 18 | C06 | `meta-analysis school phone ban achievement effect size` | 9 | `[示例] Meta-analysis of school phone bans on achievement` / `[示例] Do phone bans work? An updated meta-analysis` / `[示例] Systematic review of classroom device policies` |
| 19 | C07 | `phone ban achievement mediation attention classroom` | 12 | `[示例] Does attention mediate the effect of phone bans? A classroom observation study` / `[示例] Off-task behaviour and mobile device policy` / `[示例] Mediation analysis in education policy` |
| 20 | C08 | `classroom distraction scale construct validity self-report` | 6 | `[示例] What do distraction scales measure?` / `[示例] Self-report attention measures in classrooms` / `[示例] Construct validity in education measurement` |
| 21 | C09 | `speed limit compliance framework school rules transfer` | 5 | `[示例] Compliance frameworks transferred from traffic policy to school device rules` / `[示例] Enforcement certainty and rule following` / `[示例] Deterrence models in school settings` |
| 22 | C10 | `phone ban displacement out-of-school use substitution` | 8 | `[示例] Displacement effects of school device restrictions` / `[示例] After-school screen use following classroom bans` / `[示例] Substitution in adolescent media use` |
| 23 | C11 | `student engagement scale factor structure device policy` | 7 | `[示例] What do engagement scales measure in device-policy research?` / `[示例] Factor structure of classroom engagement measures` / `[示例] Compliance versus engagement in secondary classrooms` |
| 24 | C12 | `administrative attendance records outcome measure school policy` | 10 | `[示例] Administrative records as outcome measures in school policy evaluation` / `[示例] Attendance sensitivity to school rule changes` / `[示例] Convergent validity of self-report and administrative behaviour measures` |

## 七、可查證清單（複製給 lit-review）

```
retract: 10.0000/EX.01 10.0000/EX.02 10.0000/EX.03 10.0000/EX.05 10.0000/EX.11 10.0000/EX.12 10.0000/EX.13 10.0000/EX.21 10.0000/EX.22 10.0000/EX.23 10.0000/EX.31 10.0000/EX.32 10.0000/EX.41 10.0000/EX.51 10.0000/EX.61 10.0000/EX.62 10.0000/EX.63 10.0000/EX.71 10.0000/EX.81
check:   （本報告全部引用文獻）
```
<!-- format-check: report-end -->

> 再說一次：上面那串 DOI 是**假的**，貼進 `retract` 只會全部回 `❓ 查詢失敗`。
> 真實報告的第七節可以直接複製執行，這一份不行。

---

## 附錄一：C04 從 OPEN 被推翻成 CROWDED 的完整經過

這是整個技能唯一真正保護使用者的機制，所以完整記下來。

**第一輪。** 候選 C04 的陳述是「禁令解除後，學生的學習表現會反彈到禁令前的水準，甚至更差」。
用直覺的詞去搜：

```
python "$LIT" search "phone ban lifted rebound student performance" --limit 12
→ total 3，brief 三行全部是手機成癮治療的文章，沒有一行帶 A 旗標
python "$LIT" search "smartphone ban removal academic outcomes" --limit 12
→ total 1，不相關
```

兩種查詢都幾乎沒有相關文獻 → 依判定表這是 **OPEN**。
到這裡為止，一份不夠謹慎的報告就會寫「這個方向沒人做過」——那正是**不得寫**的措辭，
然後使用者高高興興地帶著它去口試。

**警覺點。** OPEN 的規則要求先問一句：**是真的沒有文獻，還是我不會講這個領域的話？**
「lifted」「rebound」是日常用語，不是政策研究的正規術語。所以不下判定，先去把術語撈回來：

```
python "$LIT" snowball "DOI:10.0000/EX.01" --direction references --limit 20 > gap_C04_ref.json
python "$LIT" brief "gap_C04_ref.json"
```

參考文獻清單裡反覆出現三個詞：**de-implementation**、**policy discontinuation**、**reversal effects**。
這三個詞沒有一個是第一輪會想到的。

**第二輪。** 換成正規術語再搜：

```
python "$LIT" search "de-implementation school technology policy student outcomes" --limit 12
→ total 12，其中 7 行帶 A 旗標
python "$LIT" search "policy discontinuation adolescent screen behaviour" --limit 12
→ total 9
python "$LIT" pick "gap_C04_q3.json" 0 2 6
→ 三篇摘要都直接處理「政策撤除後的反彈」
```

三篇分別涵蓋了 C04 的三個子問題（反彈是否發生／反彈幅度是否超過基線／哪些學生反彈最大），
沒有剩下的子問題 → **CROWDED**，淘汰。

**這一段的教訓，一句話**：`total = 3` 不代表「沒人做過」，它代表「我用錯詞了」。
零命中最常見的原因不是缺口，是術語不對。**所有 OPEN 判定都必須先跑過一輪術語校正才算數。**

（反過來也要誠實：術語校正跑完之後如果**仍然**是零命中，那才是有意義的 OPEN。
本次沒有任何一個候選走到那一步。）

## 附錄二：淘汰的舉證長什麼樣

**C05 的 CROWDED 拆解**（CROWDED 必須做到這件事，否則它就只是一句「這領域文獻很多」）：

| 原候選的子問題 | 哪一篇蓋掉它 | 怎麼蓋掉的 |
|---|---|---|
| 效果是否隨家戶所得而異 | EX.11 | 依所得五分位分組估計，低分位效果最大 |
| 是否隨基線成績而異（不只所得） | EX.12 | 分量迴歸，低分量學生獲益最多 |
| 是否由家庭數位近用差異驅動 | EX.13 | 以家中裝置數為調節變項直接檢驗 |

三個子問題全部有人蓋到，沒有剩下的，所以判 CROWDED。
如果第三個子問題無人碰過，依規則就必須**改判 ADJACENT**，不能用 CROWDED 淘汰。

**C07 的 DONE 四項對照**（DONE 必須做到這件事，「標題看起來很像」不算）：

| 對照項 | 本候選 | EX.02 | 對上了嗎 |
|---|---|---|---|
| 母體 | 中學生 | 中學生（11–15 歲） | ✅ |
| 處理／自變項 | 全面手機禁令 | 全面手機禁令 | ✅ |
| 結果變項 | 學業表現，中介為分心 | 學業表現，中介為離題行為觀察 | ✅ |
| 研究設計 | 中介分析 | 中介分析（課堂觀察） | ✅ |

四項全中 → DONE。只要有一項對不齊（例如它的中介變項是自陳分心而非觀察），
判定就要退成 **DONE?**，**不淘汰**，改寫進第三節並寫明缺哪一項——C10 就是這樣處理的。

## 附錄三：這個範例在示範什麼（給讀 skill 的人）

| 段落 | 對應的規則 | 沒有這條規則會發生什麼 |
|---|---|---|
| 第一節的 A4〔印象，未驗證〕 | 量化預設必須帶完整取樣框，印象級不得進 G3 | 一個沒查證的前提會長出候選，後面所有搜尋證據都在替它背書 |
| 第一節 A1–A3 的五段式取樣框 | N 是標題層、M′ 是摘要層、K 來自另一次推翻性檢索 | 用「檢視 24 篇其中 19 篇沿用」這種寫法時，那 24 篇的摘要其實一篇都沒讀 |
| 表頭的〈候選結算〉 | 生成 12 ＝ 存活 2 ＋ 待確認 4 ＋ 已淘汰 6 | 判不出來的候選被靜默丟掉，報告看起來乾淨，其實少了四個 |
| 第三節整張表 | 每個暫定狀態都要寫「還缺哪一項證據」與「補齊的動作」 | 〔待驗證〕變成一個沒有出口的垃圾桶 |
| C07 的四項對照表 | DONE 必須讀過摘要＋逐字引句＋四項全中 | 標題像就殺掉，一個唯一開著的題目被永久刪除，而且沒有人會再回頭看 |
| C05 的子問題拆解 | CROWDED 必須列 ≥3 篇並逐篇對應子問題 | CROWDED 變成不用附文獻的萬用理由，淘汰表越長越假 |
| **C04 從 OPEN 被推翻** | OPEN 判定前必須先做術語校正 | 錯誤示範：把「沒人做過」當結論，其實只是不會講這個領域的話，使用者帶著假的新穎性進口試 |
| C02 的中文索引 | 在地界定題目必須另跑 NDLTD／Airiti／TCI | 英文索引的沉默被當成證據，製造出最難發現的一種假 OPEN |
| C02 判 INCREMENTAL＋〈時程停損〉 | 時程緊時預設是保留題目、重寫貢獻 | 剩 5 個月的學生被勸去換題，論文毀掉 |
| C03 標〔待驗證〕 | G2 三段式驗證缺一不可 | 最聰明、最無法查證的跨域移植會系統性地占滿存活名單 |
| C06 標〔矛盾已觀察，機制未知〕 | G4 沒有機制就只是觀察 | 一個沒有研究問題的觀察被包裝成缺口 |
| 第六節整張表 | 二／三／四節的每個候選都要有對應列 | 整份報告可以零次搜尋憑空編出來，而且外觀跟真跑過的一模一樣 |
| 全篇的識別碼欄 | 每筆文獻都要帶 DOI／arXiv ID／系統編號 | 撤稿檢查跑不起來，使用者也無從驗證，只能相信 |

最後一件事：這份報告的存活數是 **2**，不是因為 2 是目標，是因為證據就長這樣。
如果證據支持 8 個存活，就寫 8 個，並如實加一句「存活數偏高，可能反映檢索覆蓋不足」——
**不得為了把數字壓到好看而把候選改判成 CROWDED。**
