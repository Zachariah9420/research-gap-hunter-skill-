# 領域地形報告：低軌衛星直連手機的地面干擾管理

**模式**：領域地形（盤點做法，不淘汰、不判新穎性）
**文獻工具**：lit-review lit_api.py（本模式僅用 search／brief／pick，未執行機器查核）
**檢索語言**：英文
**這份報告不做什麼**：不淘汰任何做法、不判斷新穎性、不宣稱任何做法沒有人做過。要新穎性判定請跑缺口獵捕。
**家族結算**：盤點 6 個家族，其中〔涵蓋不足〕0 個、〔判不出〕5 個
**檢索量**：實際跑了 10 次檢索

> 本檔是 evals 用的合成樣本。文中所有文獻皆為虛構（Author CA、Author CB……），
> 識別碼使用 Crossref 測試前綴 10.5555，不對應任何真實出版品。
>
> 這一份釘的是〔判不出〕**成立**的那一側：一個比年份視窗還年輕的領域，六個家族有五個
> 讀到的那一頁幾乎全部落在切分年之後。三項條件同時成立（證據不少、方向朝後、多數家族
> 都是這樣），所以那五族標〔判不出〕是這個模式的正確答案，而不是一種閃避。F4 的
> 13／20 不到八成，仍然是〔活躍〕——那一族在這個年輕領域裡反而是分得出來的。

## 一、一眼表

| 家族 | 一句話 | 買到什麼 | 付出什麼 | 狀態 | 錨定文獻數 |
|---|---|---|---|---|---|
| F1 動態頻譜協調 | 用地理圍籬排程哪一段頻率何時可用 | 沿用既有的頻率管理制度 | 排程表要跟著衛星軌跡重算 | 〔判不出〕 | 4 |
| F2 衛星端波束整形 | 在衛星端把訊號能量從敏感區壓下來 | 不必動到地面任何設備 | 壓下來的同時也壓掉服務覆蓋 | 〔判不出〕 | 4 |
| F3 眾包式地面量測 | 用一般手機大量回報收到的訊號 | 拿得到真實地面的分布 | 回報者的裝置與位置都不受控 | 〔判不出〕 | 3 |
| F4 監理條件設計 | 把干擾上限寫進服務授權條件 | 責任歸屬事前就講清楚 | 條件寫死之後跟不上技術變動 | 活躍 | 4 |
| F5 終端側緩解 | 手機端自己回退功率或改排程 | 不需要跨營運商協調 | 要改動終端，普及速度最慢 | 〔判不出〕 | 3 |
| F6 通道模型與模擬 | 用模型推估地面各點會收到多少能量 | 佈署之前就估得出風險 | 模型參數本身缺乏實測校準 | 〔判不出〕 | 4 |

## 二、各家族

### F1 動態頻譜協調

- **一句話**：依衛星軌跡與地面接收站位置，動態排定哪一段頻率在哪一段時間可以被使用。
- **買到什麼**：整套做法接得上既有的頻率指配制度，主管機關與營運商用同一組名詞討論，不必為它另立一套治理架構。
- **付出什麼**：排程表要隨軌跡週期重算，任何一顆衛星的軌道調整都會讓整張表過期；跨營運商共用同一段頻率時，協調的行政成本高於運算本身。
- **錨定文獻**：Author CA et al. (2023)〈Dynamic spectrum coordination for direct-to-device satellite links〉，DOI:10.5555/synthetic-3001；Author CB (2024)〈Geofenced frequency scheduling under orbital motion〉，DOI:10.5555/synthetic-3002；Author CC et al. (2024)〈Coordination overhead in shared spectrum satellite access〉，DOI:10.5555/synthetic-3003；Author CD et al. (2025)〈Recomputing exclusion zones as constellations evolve〉，DOI:10.5555/synthetic-3004
- **狀態**：〔判不出〕｜`dynamic spectrum coordination satellite direct to device` 在 Semantic Scholar 的寬鬆關鍵字總數 96 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 18 筆
- **結構上做不到**：它排的是「誰在什麼時候可以發射」，本身不含任何一次實際的接收量測；要知道排程有沒有奏效，得再接一種量到地面的資料。
- **默默預設**：F1-a〈會受影響的地面接收站，位置與規格事前就登記得出來〉；F1-b〈一次量測或一次推估的結果，可以代表接下來一整段排程期間〉
- **進入成本**：一份公開的軌道根數與一套排程求解器，前置知識是頻率管理法規與軌道力學；一個人約三至四週。

### F2 衛星端波束整形

- **一句話**：在衛星端調整天線的波束形狀與功率分布，讓落在敏感區域的能量降下來。
- **買到什麼**：緩解完全發生在天上，地面的接收站、手機與基地台都不必改任何東西。
- **付出什麼**：壓低敏感區能量的同時也壓掉了那一帶的服務覆蓋，兩者是同一個旋鈕；波束整形的自由度受限於天線硬體，發射之後改不了。
- **錨定文獻**：Author CE et al. (2023)〈Beam shaping for terrestrial interference mitigation from low-earth orbit〉，DOI:10.5555/synthetic-3005；Author CF (2024)〈Coverage cost of null steering in satellite direct-to-device systems〉，DOI:10.5555/synthetic-3006；Author CG et al. (2024)〈Antenna aperture limits on beam agility〉，DOI:10.5555/synthetic-3007；Author CH et al. (2025)〈Power flux density shaping over dense urban areas〉，DOI:10.5555/synthetic-3008
- **狀態**：〔判不出〕｜`satellite beam shaping terrestrial interference mitigation` 在 Semantic Scholar 的寬鬆關鍵字總數 74 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 19 筆
- **結構上做不到**：它調整的是發射端的能量分布，本身不帶接收端的環境資訊，所以它算不出地形遮蔽與建物反射之後真正落在某一點的值；那要另外一種模型或量測。
- **默默預設**：F2-a〈緩解的責任落在網路側，終端只要照著既有規格運作就好〉
- **進入成本**：天線模型與鏈路預算工具，前置知識是天線理論與鏈路設計；一個人約四至六週，實際驗證需要衛星營運方的配合。

### F3 眾包式地面量測

- **一句話**：讓一般使用者的手機在背景回報收到的訊號強度與位置，聚合成地面的實際分布圖。
- **買到什麼**：拿得到真實地面、真實裝置、真實時段的分布，涵蓋範圍隨使用者人數自然擴張，成本遠低於專業量測車。
- **付出什麼**：回報者的裝置型號、天線特性與擺放姿勢都不受控，同一點的讀值離散度大；回報密度與人口密度綁在一起，人少的地方正好是量不到的地方。
- **錨定文獻**：Author CI et al. (2024)〈Crowdsourced measurement of satellite direct-to-device downlink levels〉，DOI:10.5555/synthetic-3009；Author CJ (2024)〈Device heterogeneity in crowdsourced radio measurements〉，DOI:10.5555/synthetic-3010；Author CK et al. (2025)〈Spatial sampling bias in participatory spectrum monitoring〉，DOI:10.5555/synthetic-3011
- **狀態**：〔判不出〕｜`crowdsourced spectrum measurement direct to device downlink` 在 Semantic Scholar 未回傳總數（S2 連續 429，本輪退回 OpenAlex 分支，該分支沒有總數欄位）；本次實際讀取回傳的前 20 筆，其中 2023 之後 17 筆
- **結構上做不到**：它收到的是裝置自報的接收指標，本身不帶校準基準，所以它量得出相對高低、量不出絕對的功率通量密度；要接上法規門檻，得另外用受控儀器校準一次。
- **默默預設**：F3-a〈一次量測或一次推估的結果，可以代表接下來一整段排程期間〉；F3-b〈受到影響的一方回報得出自己被影響了〉
- **進入成本**：一支可以背景取樣的應用程式與一套聚合流程，前置知識是行動量測與隱私設計；兩人約六至八週，資料授權與倫理審查占一半。

### F4 監理條件設計

- **一句話**：把干擾上限、量測方法與違規處置寫進服務授權的條件裡，讓責任在開台之前就分配好。
- **買到什麼**：責任歸屬事前講清楚，爭議發生時有一份雙方都簽過的判準可以援引，不必臨時談判。
- **付出什麼**：條件一旦寫死就跟不上技術變動，星系規模與波束能力每年都在改；過嚴會擋掉服務，過鬆則要等到爭議發生才發現。
- **錨定文獻**：Author CL et al. (2022)〈Licensing conditions for satellite direct-to-device services〉，DOI:10.5555/synthetic-3012；Author CM (2023)〈Interference limits as regulatory instruments〉，DOI:10.5555/synthetic-3013；Author CN et al. (2024)〈Enforcement design for cross-border spectrum disputes〉，DOI:10.5555/synthetic-3014；Author CO et al. (2025)〈Regulatory lag and constellation growth〉，DOI:10.5555/synthetic-3015
- **狀態**：活躍｜`licensing conditions satellite direct to device interference limit` 在 Semantic Scholar 的寬鬆關鍵字總數 131 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 13 筆
- **結構上做不到**：它處理的是條文與程序，本身不產生任何量測值；要判定某一次爭議事實上有沒有超標，得由前面幾個家族之一提供數字。
- **默默預設**：F4-a〈會受影響的地面接收站，位置與規格事前就登記得出來〉
- **進入成本**：法規文本與公開徵詢紀錄，前置知識是電信法制與國際協調程序；一個人約四週。

### F5 終端側緩解

- **一句話**：由手機自己在偵測到共存風險時回退發射功率或改變傳輸排程。
- **買到什麼**：緩解發生在單一裝置內，不需要跨營運商或跨國協調，決策延遲最短。
- **付出什麼**：要改動終端的韌體或協定堆疊，換機週期決定普及速度，是所有家族裡最慢的一種；回退也直接犧牲該裝置自己的傳輸品質。
- **錨定文獻**：Author CP et al. (2024)〈Terminal-side power back-off for satellite-terrestrial coexistence〉，DOI:10.5555/synthetic-3016；Author CQ (2024)〈Scheduling adaptation in user equipment under external interference〉，DOI:10.5555/synthetic-3017；Author CR et al. (2025)〈Firmware update cadence and the pace of terminal-side mitigation〉，DOI:10.5555/synthetic-3018
- **狀態**：〔判不出〕｜`terminal side mitigation satellite terrestrial coexistence` 在 Semantic Scholar 的寬鬆關鍵字總數 58 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 20 筆
- **結構上做不到**：它看得到的只有這一台裝置收到的訊號，本身不帶鄰近裝置的狀態，所以它判斷不出整區的共存情形；要做到那一層，得把回報聚合起來，那是另一個家族。
- **默默預設**：F5-a〈緩解的責任落在網路側，終端只要照著既有規格運作就好〉
- **進入成本**：一套可改的終端軟體堆疊與一個實驗場域，前置知識是無線協定實作；兩人約八週以上，取得可改的終端是主要瓶頸。

### F6 通道模型與模擬

- **一句話**：用傳播模型與地形資料，推估地面各點在特定軌道配置下會收到多少能量。
- **買到什麼**：在任何硬體佈署之前就估得出風險分布，可以拿來比較不同軌道與波束設計的取捨，成本只有算力。
- **付出什麼**：模型參數多半沿用地面行動通訊的經驗值，還沒查到針對這種入射角的系統性實測校準；輸出的精度因此無法自證，只能與別的模型互比。
- **錨定文獻**：Author CS et al. (2023)〈Propagation modelling for low-earth-orbit direct-to-device links〉，DOI:10.5555/synthetic-3019；Author CT (2024)〈Elevation-angle dependence in urban clutter loss〉，DOI:10.5555/synthetic-3020；Author CU et al. (2024)〈Simulation platforms for satellite-terrestrial coexistence studies〉，DOI:10.5555/synthetic-3021；Author CV et al. (2025)〈Parameter uncertainty in coexistence simulations〉，DOI:10.5555/synthetic-3022
- **狀態**：〔判不出〕｜`propagation model low earth orbit direct to device coexistence` 在 Semantic Scholar 的寬鬆關鍵字總數 45 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 16 筆
- **結構上做不到**：它的輸出是模型在給定參數下的推估值，本身不含任何一次現地觀測，所以它說不出自己偏離現實多少；那要一次獨立的實測比對。
- **默默預設**：F6-a〈會受影響的地面接收站，位置與規格事前就登記得出來〉；F6-b〈一次量測或一次推估的結果，可以代表接下來一整段排程期間〉
- **進入成本**：地形與建物圖資、一套傳播模擬工具，前置知識是無線傳播與地理資訊處理；一個人約三至五週。

## 三、實際上怎麼疊

實務上很少單用一個家族。三種常見的疊法：

1. **F6 ＋ F1**：先用模擬估出風險分布，再據以排定頻率與時段。模擬負責「哪裡可能出事」、排程負責「那就別在那時候發」，成本落在模型參數的可信度上——排程的品質不會比它上游的模型更好。
2. **F3 ＋ F6**：用眾包量測回頭校準模型參數，兩者互為對方的弱點補償。代價是量測的空間分布不均，校準品質在人少的地方最差，而那些地方往往正是需要估準的地方。
3. **F4 ＋ F2**：把干擾上限寫進授權條件，由衛星端的波束整形去滿足它。條文給出可執行的門檻、波束整形給出達成手段，成本落在營運商——覆蓋損失是被監理條件買單的那一項。

## 四、能量在哪裡

- `terminal side mitigation satellite terrestrial coexistence` 在 Semantic Scholar 的寬鬆關鍵字總數 58 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 20 筆——讀到的那一頁整頁都落在切分年之後。
- `satellite beam shaping terrestrial interference mitigation` 在 Semantic Scholar 的寬鬆關鍵字總數 74 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 19 筆。
- `licensing conditions satellite direct to device interference limit` 在 Semantic Scholar 的寬鬆關鍵字總數 131 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 13 筆——本次盤點裡唯一一族的近年占比不到八成，也是唯一一族的年份切分還分得出東西。
- `propagation model low earth orbit direct to device coexistence` 在 Semantic Scholar 的寬鬆關鍵字總數 45 筆（工具自報，未加年份條件）；本次實際讀取回傳的前 20 筆，其中 2023 之後 16 筆。
- 〔印象，未驗證〕六個家族有五個讀到的那一頁幾乎整頁都落在 2023 之後，這與商用直連手機服務在 2023 前後才開始出現是一致的。年份切分在這樣的領域裡分不出飽和與活躍，所以那五族的〈狀態〉是〔判不出〕；本次沒有為這個解釋跑過對應的檢索。

## 五、檢索紀錄

| # | 家族 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | （家族清單） | `satellite direct to device survey` | 總數 41／讀 20 | A survey of satellite direct-to-device connectivity / Direct-to-device from low earth orbit: a survey of link architectures / Coexistence challenges in satellite direct-to-device services |
| 2 | （家族清單） | `satellite terrestrial coexistence review` | 總數 63／讀 20 | A review of satellite-terrestrial spectrum coexistence / Interference management for shared spectrum: a review / Regulatory and technical reviews of coexistence practice |
| 3 | （家族清單） | `direct to device interference taxonomy` | 總數 17／讀 17 | A taxonomy of interference mitigation for direct-to-device links / Classifying coexistence mechanisms by locus of control / Toward a shared vocabulary for satellite-terrestrial coexistence |
| 4 | F1 | `dynamic spectrum coordination satellite direct to device` | 總數 96／讀 20 | Dynamic spectrum coordination for direct-to-device satellite links / Geofenced frequency scheduling under orbital motion / Recomputing exclusion zones as constellations evolve |
| 5 | F2 | `satellite beam shaping terrestrial interference mitigation` | 總數 74／讀 20 | Beam shaping for terrestrial interference mitigation from low-earth orbit / Coverage cost of null steering in satellite direct-to-device systems / Power flux density shaping over dense urban areas |
| 6 | F3 | `crowdsourced spectrum measurement direct to device downlink` | 無總數（S2 連續 429，退回 OpenAlex 分支）／讀 20 | Crowdsourced measurement of satellite direct-to-device downlink levels / Device heterogeneity in crowdsourced radio measurements / Spatial sampling bias in participatory spectrum monitoring |
| 7 | F4 | `licensing conditions satellite direct to device interference limit` | 總數 131／讀 20 | Licensing conditions for satellite direct-to-device services / Interference limits as regulatory instruments / Regulatory lag and constellation growth |
| 8 | F5 | `terminal side mitigation satellite terrestrial coexistence` | 總數 58／讀 20 | Terminal-side power back-off for satellite-terrestrial coexistence / Scheduling adaptation in user equipment under external interference / Firmware update cadence and the pace of terminal-side mitigation |
| 9 | F6 | `propagation model low earth orbit direct to device coexistence` | 總數 45／讀 20 | Propagation modelling for low-earth-orbit direct-to-device links / Elevation-angle dependence in urban clutter loss / Parameter uncertainty in coexistence simulations |
| 10 | W3 | `shifting mitigation responsibility to user equipment` | 總數 22／讀 20 | Who mitigates? Responsibility allocation in spectrum coexistence / Terminal-centric coexistence architectures / Rebalancing network and terminal duties in shared spectrum |

## 六、這個領域的牆（默默預設總表）

| 牆 | 這條預設 | 來源預設 | 家族數 | 性質 | 拆的可能性 |
|---|---|---|---|---|---|
| W1 | 會受影響的地面接收站，位置與規格事前登記得出來 | F1-a、F4-a、F6-a | 3 | 歷史偶然 | 拆掉之後，保護對象必須改由觀測反推而不是由名冊查出，成本從一次查表變成持續監測；不方便的是主管機關，因為現行的指配與爭議處理程序都建立在那份名冊上 |
| W2 | 一次量測或一次推估的結果，可以代表接下來一整段期間 | F1-b、F3-a、F6-b | 3 | 真的必要 | 這三個家族的輸入本身就是離散取樣或單次推估，取消取樣點等於取消這個家族；能改的是取樣密度與如何標示不確定性，不是這條預設本身 |
| W3 | 緩解的責任落在網路側，終端只要照著既有規格運作 | F2-a、F5-a | 2 | 已經有人在拆 | Author CW et al. (2025)〈Who mitigates? Responsibility allocation in spectrum coexistence〉，DOI:10.5555/synthetic-3031 |
| W4 | 受到影響的一方回報得出自己被影響了 | F3-b | 1 | 歷史偶然 | 拆掉之後要改用不倚賴當事人回報的來源（受控監測站、營運商側的統計），代價是失去使用者端的涵蓋廣度；不方便的是需要大範圍分布資料的研究 |
