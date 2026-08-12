# 短範例：一份領域地形報告（室內定位）

> # ⚠️ 本檔所有文獻、識別碼與命中筆數都是編造的
>
> 這份檔案裡的**每一筆文獻、作者、年份、DOI、命中筆數、年份分布，全部是為了示範而編造
> 的**，不是真實文獻，也不是任何一次真實檢索的結果。辨識方式只有兩條，**兩條合起來沒有
> 任何漏網之魚**：
>
> 1. **每一個標題都加了 `[示例]` 前綴**，一個不漏——中文標題也一樣。本檔不存在「只寫
>    作者與年份、沒有標題」的引用寫法，所以不需要第三種標記來補洞。
> 2. **每一個識別碼都是 `10.0000/EX-L.nn`**，用的是未註冊的 Crossref 前綴 `10.0000/`，
>    永遠解析不出東西；`EX-L` 這個中綴是本檔專用（`examples/worked_example.md` 用的是
>    `EX.`，兩份不會混淆）。
>
> 兩個看起來像例外、但都被第 1 條蓋住的地方，先講清楚，免得被當成漏網：
>
> - **F4 的第三筆錨定文獻**刻意標成〔無識別碼〕，用來示範階 2 檢索拿不到 DOI 時該怎麼
>   寫。它沒有識別碼，但它有 `[示例]` 前綴。
> - **第五節〈前三筆標題〉那一欄按規格就是不帶識別碼的**（它抄的是工具回傳的標題本
>   身），整欄每一個標題也都有 `[示例]` 前綴。
>
> 除此之外，本檔沒有任何一筆引用逃出上面的規則；**看到逃出去的，那是本檔的 bug，請開
> issue，不要當成真文獻。**
>
> **不要引用本檔的任何一筆文獻，不要拿去餵給 `retract` 或 `check`。**

主題刻意挑一個平凡的工程題目（建築物室內定位），跟本 skill 作者自己的研究領域無關，
免得範例被當成現成答案抄走。**這裡示範的是報告的形狀與誠實標準**：一個家族該被寫成
什麼樣子、什麼時候該直接標〔涵蓋不足〕收手、以及最後那張牆表怎麼從前面的預設長出來。

**這份檔案的報告本體用 `format-check: report-start` 與 `format-check: report-end` 兩行
HTML 註解圍起來**，跟 [`worked_example.md`](worked_example.md) 同一個做法：圍欄之外的
教學文字不受查核，圍欄之內一條都不放寬。`python evals/format_check.py
examples/landscape_example.md` 今天跑出來是 exit 0。

**本檔的〈狀態〉欄用的是兩段子句的句型**（前段是索引自報的寬鬆總數、或逐字寫「未回傳
總數（原因）」，後段是這一輪真的讀到的那一頁與頁內的年份計數），中間**沒有**「其中」
——那兩個數字不是同一個母體。表頭〈文獻工具〉抄的是降級階梯表 **landscape 那一欄**，
不是 hunt 那一欄。舊版的本檔兩處都不是這樣寫的，改動的來由見 `README.md`〈Where these
three rules came from〉。

**還要知道地形這一套規則刻意很薄**：`evals/format_check.py` 對地形報告只有五條自己的
規則（表頭宣告、不得出現判定詞彙、成本必填、狀態合法且掛檢索證據、牆表與預設雙向對
帳），外加跨模式共用的幾條。**它驗的是「有沒有照格式騙人」，不驗這些家族切得對不對、
那些代價是不是真的。** 那一層只有人讀得出來。

**報告型別看第一行**：`# 領域地形報告：` 是這一種，`# 研究缺口報告：` 是
`worked_example.md` 那一種；查核器認不出第一行時，退而看表頭〈模式〉。

---

<!-- format-check: report-start -->
# 領域地形報告：建築物室內定位

**模式**：領域地形（盤點做法，不淘汰、不判新穎性）
**文獻工具**：google-scholar MCP；本模式無 brief／pick，錨定文獻可能無識別碼
**檢索語言**：英文
**這份報告不做什麼**：不淘汰任何做法、不判斷新穎性、不宣稱任何做法沒有人做過。要新穎性判定請跑缺口獵捕。
**家族結算**：盤點 5 個家族，其中〔涵蓋不足〕1 個、〔判不出〕0 個
**檢索量**：實際跑了 9 次檢索

## 一、一眼表

| 家族 | 一句話 | 買到什麼 | 付出什麼 | 狀態 | 錨定文獻數 |
|---|---|---|---|---|---|
| F1 Wi-Fi 指紋比對 | 先量測整棟樓的訊號地圖再比對 | 不必加裝硬體 | 每次改裝潢就要重測 | 飽和 | 4 |
| F2 藍牙信標 | 佈信標、用訊號強度推距離 | 佈建便宜、耗電低 | 訊號強度與距離關係很不穩 | 活躍 | 4 |
| F3 慣性航位推算 | 用手機的加速度與陀螺儀累積位移 | 完全不依賴外部訊號 | 誤差隨時間累積、必須被校正 | 活躍 | 3 |
| F4 UWB 飛行時間測距 | 量測無線脈衝的來回時間 | 公分級精度 | 需要專用硬體、成本高 | 新興 | 3 |
| F5 視覺定位 | 用相機畫面比對場景地圖 | 精度高、可同時建圖 | 耗電與算力最重 | 〔涵蓋不足〕 | 2 |

## 二、各家族

### F1 Wi-Fi 指紋比對

- **一句話**：事先在建築物內密集量測各點的無線電訊號特徵，之後把即時量測值拿去比對這張地圖。
- **買到什麼**：完全利用既有的無線網路設備，不必為了定位再加裝任何硬體。
- **付出什麼**：那張地圖是勞力密集的一次性資產，環境一改（隔間、家具、人流）就開始失準，重測成本落在營運方。
- **錨定文獻**：`[示例] Fingerprint-based indoor localization: a decade in review`，Halloran & Xu (2019)，DOI:10.0000/EX-L.01；`[示例] Radio map ageing and its effect on positioning error`，Bergqvist (2021)，DOI:10.0000/EX-L.02；`[示例] Crowdsourced radio map maintenance in shopping malls`，Nakagawa et al. (2022)，DOI:10.0000/EX-L.03；`[示例] Device heterogeneity in RSSI fingerprinting`，Duarte & Kim (2020)，DOI:10.0000/EX-L.04
- **狀態**：飽和｜`wifi fingerprinting indoor positioning` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 40 筆，其中 2021 之後 6 筆
- **結構上做不到**：它的輸出是「與地圖上哪一點最像」的相似度排序，本身不含任何運動模型，所以單靠它得不到方向與速度；要拿到那些，得再疊一個濾波器或另一個家族。
- **默默預設**：F1-a〈量測完成之後，環境的無線電特性在使用期間維持穩定〉；F1-b〈不同型號的裝置量到的訊號強度可以互相比較〉
- **進入成本**：一支手機加一套開源比對程式就能起步；真正的成本是量測——一層樓的密集採點大約 1 人×1 週，而且要重複付。

### F2 藍牙信標

- **一句話**：在空間裡佈設低功耗藍牙信標，用接收到的訊號強度推估與各信標的距離再解位置。
- **買到什麼**：信標單價低、電池可撐數年，佈建與汰換都便宜，是目前最容易讓業主點頭的一種。
- **付出什麼**：訊號強度換距離這件事本身不穩，人體遮蔽與多路徑會讓同一個位置量到差很多的值，精度通常停在數公尺。
- **錨定文獻**：`[示例] BLE beacon positioning in retail environments`，Ferreira (2020)，DOI:10.0000/EX-L.11；`[示例] Path-loss model mismatch in crowded indoor spaces`，Osei & Lindholm (2021)，DOI:10.0000/EX-L.12；`[示例] Beacon density versus accuracy: an empirical trade-off`，Ruiz (2022)，DOI:10.0000/EX-L.13；`[示例] Battery-life planning for large beacon deployments`，Tanaka & Brody (2023)，DOI:10.0000/EX-L.14
- **狀態**：活躍｜`bluetooth low energy beacon indoor positioning` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 36 筆，其中 2021 之後 19 筆
- **結構上做不到**：它量的是訊號強度這個純量，不含角度資訊，所以單一信標無法給出方位；要解出位置至少要三個信標同時可見。
- **默默預設**：F2-a〈訊號強度與距離之間存在可用的單調關係〉；F2-b〈空間的擁有者願意讓你事先佈建並長期維護硬體〉
- **進入成本**：數十顆信標（數百美元）加一次現場佈設；沒有場地的擁有權或使用許可，這個家族對你等於不存在。

### F3 慣性航位推算

- **一句話**：用裝置自身的加速度計與陀螺儀累積位移，從一個已知起點推算現在在哪裡。
- **買到什麼**：完全不依賴任何外部訊號或基礎設施，走進電梯、地下室、訊號死角都照樣有輸出。
- **付出什麼**：誤差隨時間單調累積，數分鐘就會飄到不能用，所以它幾乎不能單獨使用，一定要被別的家族週期性拉回來。
- **錨定文獻**：`[示例] Pedestrian dead reckoning with smartphone IMUs: error growth characteristics`，Aaltonen (2018)，DOI:10.0000/EX-L.21；`[示例] Step-length estimation across gait types`，Moreau & Ishikawa (2021)，DOI:10.0000/EX-L.22；`[示例] Drift correction by opportunistic anchors`，Petrov (2023)，DOI:10.0000/EX-L.23
- **狀態**：活躍｜`pedestrian dead reckoning smartphone indoor` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 28 筆，其中 2021 之後 15 筆
- **結構上做不到**：它算的是位移增量，沒有任何絕對參考，所以它無法自己決定起點，也無法在飄掉之後自己發現飄掉了。
- **默默預設**：F3-a〈起始位置是已知的，而且路徑是連續的、不會被瞬間搬移〉；F3-b〈被定位的是一個以人類步態行走的人，步伐可被模型化〉
- **進入成本**：只要一支手機，是五個家族裡最低的；但要做到堪用，得補一套校正機制，那部分的難度不低。

### F4 UWB 飛行時間測距

- **一句話**：用超寬頻脈衝量測訊號來回的飛行時間，直接換算距離。
- **買到什麼**：公分級精度，是五個家族裡唯一能穩定做到這個量級的。
- **付出什麼**：需要專用的錨點與標籤硬體，單點成本比藍牙高一個量級；而且精度依賴視線路徑，被牆或人擋住就退化。
- **錨定文獻**：`[示例] UWB ranging accuracy under non-line-of-sight conditions`，Vasquez & Aho (2021)，DOI:10.0000/EX-L.31；`[示例] Deployment cost of UWB anchor networks in warehouses`，Lindgren (2022)，DOI:10.0000/EX-L.32；`[示例] Consumer UWB chipsets and the near-term device base`（2023）〔無識別碼〕
- **狀態**：新興｜`ultra-wideband indoor positioning accuracy` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 22 筆，其中 2021 之後 17 筆
- **結構上做不到**：它量的是兩點之間的距離，不含語意，所以它不知道自己在哪一個房間、也不知道那條路徑有沒有穿牆——房間層級的判斷要另外接一張平面圖。
- **默默預設**：F4-a〈空間的擁有者願意讓你事先佈建並長期維護硬體〉；F4-b〈量測的兩點之間存在直達的視線路徑〉
- **進入成本**：一組開發套件（數百至上千美元）＋一次現場錨點佈設；比藍牙貴，門檻主要在硬體不在演算法。

### F5 視覺定位

- **一句話**：用相機拍到的畫面去比對事先建好的場景地圖，解出相機的位置與姿態。
- **買到什麼**：精度高，而且同一套流程可以順便把地圖建出來。
- **付出什麼**：耗電與算力是五個家族裡最重的；還沒查到它在連續使用情境下的續航數字。
- **錨定文獻**：`[示例] Visual relocalization in large indoor scenes`，Sørensen (2020)，DOI:10.0000/EX-L.41；`[示例] Texture-poor environments and visual SLAM failure modes`，Iqbal & Renard (2022)，DOI:10.0000/EX-L.42
- **狀態**：〔涵蓋不足〕
- **結構上做不到**：它的輸入是影像，所以在無紋理的白牆走廊或全黑環境下，它得不到可比對的特徵——這是輸入本身的性質，不是演算法還沒做好。
- **默默預設**：F5-a〈場景具備足夠且穩定的視覺紋理，而且外觀不會大幅改變〉；F5-b〈裝置有持續的供電與算力可以長時間跑〉
- **進入成本**：一支中高階手機加一套開源視覺定位框架；真正的門檻是事先建圖，以及維持地圖與現場一致。

> 〔涵蓋不足〕的處理示範：F5 只湊到 2 篇錨定文獻，未達 3 篇的下限。依規則**標了就走**
> ——不追、不補搜、不把它升級成一個小調查。它的〈狀態〉欄不掛檢索句型，而**〔涵蓋不足〕
> 是唯一免掛的值**：其餘五個（飽和／活躍／新興／衰退／〔判不出〕）都要掛，因為它們都是
> 拿數字撐起來的判斷，而〔涵蓋不足〕宣告的正是「沒有數字可掛」。它的預設照樣寫，因為
> 〈默默預設〉講的是這個做法本身的性質，跟這一輪查了幾篇無關。
>
> 本檔沒有任何一個家族標〔判不出〕，這是對的：那個值要三項同時成立，而這裡第二、三項
> 都不成立。F4 的 17／22 是本檔近年占比最高的一族，仍然不到八成；就算到了，第三項也擋
> 著——**多數家族並不是這樣**（F1 只有 6／40）。一個成熟領域裡某一族特別熱，那是真的
> 熱，不是儀器分不出來。〔判不出〕要的是整份報告每一族都貼著上限的那種情形。

## 三、實際上怎麼疊

實務上幾乎沒有人單用一個家族。三種常見組合：

- **F3 ＋ F1**：慣性推算負責高頻連續軌跡，Wi-Fi 指紋每隔數十秒把累積漂移拉回來。成本落在
  營運方——要有人維護那張無線電地圖，而維護的理由是為了 F1，享受到的卻是整套系統。
- **F3 ＋ F2**：同樣的分工，把校正來源換成信標。校正頻率變高、單次校正精度變差，硬體成本
  從「重測人力」轉成「佈建與換電池」，也就是從營運成本轉成資本支出。
- **F4 單獨用於局部、其餘區域交給 F2**：成本敏感的做法——只在真的需要公分級的作業區佈
  UWB，其餘走藍牙。代價是兩套座標系要對齊，而對齊誤差通常沒有被寫進系統規格裡。

## 四、能量在哪裡

- `ultra-wideband indoor positioning accuracy` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 22 筆，其中 2021 之後 17 筆——近年占比是五個家族裡最高的。
- `wifi fingerprinting indoor positioning` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 40 筆，其中 2021 之後 6 筆——讀到的那一頁最長，近年占比最低。本輪沒有拿到任何索引總數，所以**不能**說它「總量最大」——那句話講的是母體，而本檔手上只有那一頁。
- `pedestrian dead reckoning smartphone indoor` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 28 筆，其中 2021 之後 15 筆。
- `bluetooth low energy beacon indoor positioning` 在 google-scholar MCP 未回傳總數（工具不報索引計數）；本次實際讀取回傳的前 36 筆，其中 2021 之後 19 筆。

〔印象，未驗證〕近三年的標題裡「融合」「多來源」出現得比單一家族的名字更頻繁，看起來
研究重心正在從「哪一種最準」移到「怎麼把幾種接起來」。本輪沒有為這個觀察跑檢索，所以
它不是檢索結果，另起一行寫在這裡。

## 五、檢索紀錄

| # | 家族 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | （盤家族） | `indoor positioning survey` | 無總數（工具不報索引計數）／讀 24 | `[示例] A survey of indoor localization techniques` / `[示例] Indoor localization for mobile devices: a survey of sensing modalities` / `[示例] Benchmarking indoor positioning: lessons from five competitions` |
| 2 | （盤家族） | `indoor positioning review` | 無總數（工具不報索引計數）／讀 31 | `[示例] Indoor positioning technologies: a structured review` / `[示例] A critical review of infrastructure requirements in indoor localization` / `[示例] Hybrid indoor positioning: a review of fusion architectures` |
| 3 | （盤家族） | `indoor positioning taxonomy` | 無總數（工具不報索引計數）／讀 18 | `[示例] Indoor positioning systems: a taxonomy of sensing modalities` / `[示例] Classifying indoor localization by infrastructure dependence` / `[示例] Toward a shared vocabulary for indoor positioning` |
| 4 | F1 | `wifi fingerprinting indoor positioning` | 無總數（工具不報索引計數）／讀 40 | `[示例] Fingerprint-based indoor localization: a decade in review` / `[示例] Radio map ageing and its effect on positioning error` / `[示例] Device heterogeneity in RSSI fingerprinting` |
| 5 | F2 | `bluetooth low energy beacon indoor positioning` | 無總數（工具不報索引計數）／讀 36 | `[示例] BLE beacon positioning in retail environments` / `[示例] Path-loss model mismatch in crowded indoor spaces` / `[示例] Beacon density versus accuracy: an empirical trade-off` |
| 6 | F3 | `pedestrian dead reckoning smartphone indoor` | 無總數（工具不報索引計數）／讀 28 | `[示例] Pedestrian dead reckoning with smartphone IMUs: error growth characteristics` / `[示例] Step-length estimation across gait types` / `[示例] Drift correction by opportunistic anchors` |
| 7 | F4 | `ultra-wideband indoor positioning accuracy` | 無總數（工具不報索引計數）／讀 22 | `[示例] UWB ranging accuracy under non-line-of-sight conditions` / `[示例] Deployment cost of UWB anchor networks in warehouses` / `[示例] Consumer UWB chipsets and the near-term device base` |
| 8 | F5 | `visual indoor localization relocalization` | 無總數（工具不報索引計數）／讀 9 | `[示例] Visual relocalization in large indoor scenes` / `[示例] Texture-poor environments and visual SLAM failure modes` |
| 9 | （第六節 W3） | `infrastructure-free indoor positioning` | 無總數（工具不報索引計數）／讀 11 | `[示例] Infrastructure-free indoor positioning using ambient magnetic fields` / `[示例] Opportunistic signals of convenience for localization` / `[示例] Zero-deployment positioning: a position paper` |

## 六、這個領域的牆（默默預設總表）

| 牆 | 這條預設 | 來源預設 | 家族數 | 性質 | 拆的可能性 |
|---|---|---|---|---|---|
| W1 | 環境在部署完成之後是靜態的：訊號地圖、視覺外觀、視線路徑都不會被人與貨物持續改變 | F1-a、F4-b、F5-a | 3 | 歷史偶然 | 拿掉之後，「一次性建圖」就不再是有效的產品形態，系統要改成持續自我更新；不方便的是營運方，因為維護成本會從一次性變成經常性，而現行的採購合約幾乎都不是這樣寫的 |
| W2 | 被定位的是一個攜帶標準智慧型手機、以人類步態移動的人 | F1-b、F3-b、F5-b | 3 | 歷史偶然 | 拿掉之後，堆高機、推車、輪椅、機器人都算數，而它們的運動模型與供電條件跟人完全不同；現行做法多半在步態假設上做過調校，換載體要重調 |
| W3 | 定位仰賴事先佈建、而且有人長期維護的基礎設施 | F2-b、F4-a | 2 | 已經有人在拆 | `[示例] Infrastructure-free indoor positioning using ambient magnetic fields`，Delacroix & Ohta (2022)，DOI:10.0000/EX-L.51 直接以「不佈建任何硬體」為前提；`[示例] Opportunistic signals of convenience for localization`，Weir (2023)，DOI:10.0000/EX-L.52 走的是利用既有訊號的路線 |
| W4 | 位置估計是連續的，而且起點是已知的 | F3-a | 1 | 真的必要 | 拿不掉：航位推算在定義上算的就是位移增量，沒有起點就沒有可累加的基準，這不是實作選擇而是方法的形式 |
| W5 | 訊號強度與距離之間存在可用的單調關係 | F2-a | 1 | 真的必要 | 拿不掉：這個家族用來解距離的就是這個關係本身，關係不成立時剩下的不是精度變差，而是根本沒有可解的量 |
<!-- format-check: report-end -->

---

## 這份範例在示範什麼

| 位置 | 對應的規則 | 沒有這條規則會發生什麼 |
|---|---|---|
| 每個家族都有〈付出什麼〉 | 成本必填，查不到寫「還沒查到」不留白 | 只寫買到什麼的家族看起來免費，讀者會以為它是明顯的最佳解——而真的沒有代價的做法早就把別人清光了 |
| F5 標〔涵蓋不足〕就收手 | 錨定不足 3 篇就標記，不追、不補搜 | 為了把表格填滿而編第三筆錨定文獻，這是這個模式最可能的造假點 |
| 〈狀態〉掛的是**兩段子句**的檢索句型 | 前段是索引自報的寬鬆總數（本檔沒有，所以逐字寫「未回傳總數」），後段是這次真的讀到的那一頁與頁內的年份計數；兩段之間沒有「其中」 | 兩個數字被一個「其中」串成一個母體，報告等於印了一句它自己知道是假的話——舊句型就是這樣，而寫報告的人只好在旁邊再補一句去拆穿它 |
| 第四節那句「不能說它總量最大」 | 頁內數字只描述那一頁，不描述索引 | 40 筆被讀成「這個領域有 40 篇」，而它其實只是本輪讀到的一頁 |
| 表頭〈文獻工具〉抄的是階梯表 landscape 那一欄 | 兩個模式共用同一組階與條件，各讀自己那一欄；跨欄照抄是違規 | 抄到 hunt 那一欄，地形報告的表頭就宣告了它被禁止執行的撤稿、存在性與滾雪球查核 |
| 沒有任何一族標〔判不出〕 | 那個值要三項同時成立，其中一項是「這份報告多數家族都是這樣」 | 一個成熟領域裡最熱的那一族被誤標成〔判不出〕，而它其實是真的熱——那一格會從資訊變成聳肩 |
| 第四節最後那句〔印象，未驗證〕 | 寫不成檢索句型的觀察要另起一行標記 | 印象混進檢索結果裡，整節的可信度一起被拉低 |
| 〈結構上做不到〉寫方法的性質 | 寫「它的輸出不含方向」，不寫「沒有人用它做過方向估計」 | 一個沒有搜過的不存在斷言混進報告，而這正是本 skill 唯一絕不放寬的兩條之一 |
| 第六節每個編號都對得回第二節 | 牆只能從已寫下的預設長出來 | 憑空想出來的牆混進總表，而它看起來最像洞見、也最沒有來源 |
| 第五節前三列是家族推導檢索 | `survey`／`review`／`taxonomy` 各一輪，家族抄回顧文獻已做好的分類 | 家族清單沒有來源，等於憑印象列——那是這個模式最容易編造的一環 |
| 表頭沒有〈覆蓋率警告〉 | 那一行講的是存活清單，地形報告沒有存活清單 | 每份報告都掛同一句警語，等於每份都沒掛 |

### 〈檢索量〉那個數字是怎麼來的（本檔刻意把偏離寫出來）

表頭的〈檢索量〉沒有東西可以對帳，所以這裡把它拆開，順便把本檔**沒有**照字面跑滿的那一段講清楚。

本檔的 9 次拆成三段：**3 次家族推導**（`survey`／`review`／`taxonomy` 各一輪，就是 `SKILL.md`
〈怎麼盤出家族清單〉要求的那三輪）＋ **5 次家族查詢**（一個家族一次，用來撐起〈狀態〉那一欄的
檢索句型）＋ **1 次牆的查詢**（W3 判成〔已經有人在拆〕，而那個值必須指名是誰在拆，指不出來就
不合法，所以它自己要一次檢索）。

**偏離的地方**：`SKILL.md` 的〈兩種模式〉表寫的是「每個家族 2–3 次檢索」，照字面五個家族就是
10–15 次，加上推導那三輪是 13–18 次。本檔一個家族只跑一次，總數少於那個字面預算。理由寫在這裡
而不是靜靜地少跑：這五個家族的名稱在領域裡都是固定術語，第一次查詢就回得出可用的錨定文獻與
〈狀態〉句型，沒有換詞重搜的需要——那個 2–3 次的預算是留給**第一次回傳太少、或術語根本不確定**
的家族的，不是每個家族都要花掉的定額。F5 就是被那第一次查詢擋下來的例子：第 8 列查了，讀到 9 筆，
仍然湊不到 3 篇錨定文獻，於是照規則標〔涵蓋不足〕收手——**而不是**再跑兩次去把它補滿。

反過來的那一半同樣重要：一個家族一次都沒查就寫得出〈狀態〉，那是印象不是檢索，這個模式沒有那種
豁免。所以本檔的每一個家族在第五節都有自己的一列。

**要往下走的話**：這五道牆可以直接餵給缺口獵捕的第 1 步。承接進來的預設寫成
`預設 A1〔承接自地形 W1，支撐家族 F1、F4、F5〕：〈一句話〉`，效力等同〔印象，未驗證〕
——可以用來決定往哪裡挖，**不能直接當 G3 預設反轉的輸入**，也不必在缺口報告第六節附上
檢索紀錄（它不是那一輪搜出來的）。真的要反轉其中一條，就只對那一條補跑取樣框，補完標籤
改成〔承接自地形 W1，已補取樣框〕、後面接五個數字——**標籤保留、不要改寫成〔印象，未驗證〕**，
兩者效力相同但來源不同。規則見 `SKILL.md`〈第 1 步〉。
