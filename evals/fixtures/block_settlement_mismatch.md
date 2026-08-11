# 研究缺口報告：都市公園綠地與居民身體活動

**模式**：完整獵捕
**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）
**貢獻判準**：方法新穎 ＋ 在地驗證（複選）
**中文索引**：已檢索 NDLTD 臺灣博碩士論文加值系統、Airiti 華藝線上圖書館
**降級聲明**：無
**候選結算**：生成 12 ＝ 存活 3 ＋ 待確認 3 ＋ 已淘汰 6

> 本檔是 evals 用的合成樣本。文中所有文獻皆為虛構（Author A、Author B……），
> 識別碼使用 Crossref 測試前綴 10.5555，不對應任何真實出版品。
> 相對於 good_report.md，本檔刻意壞掉一處：區塊結算的〈已淘汰〉寫 5，生成 12 ≠ 存活 3 ＋ 待確認 3 ＋ 已淘汰 5。算術在區塊裡就對不起來，所以查核器不再拿這四個數字去跟散文的列數比對——一個缺陷不該變成三句話，其中兩句還會把作者送去改沒有壞的東西（第四節那六列是對的）。

## 一、領域共識與未被質疑的預設

- 主流立場：都市綠地與居民身體活動的關聯，主要以住家周邊緩衝區內的綠覆率或綠地面積比例衡量（代表文獻：Author A et al. (2021)〈Residential green space exposure and adult physical activity〉，DOI:10.5555/synthetic-0001）
- 主流立場：綠地不足被當成土地使用的供給問題，而不是誰真的走得到、走得進去的問題（代表文獻：Author B (2023)〈A survey of green space exposure metrics〉，arXiv:2401.00001）
- 預設 A1：〈住家周邊的綠地面積可以代表居民實際獲得的綠地暴露〉｜標題層掃描 24 篇（檢索詞 `urban green space physical activity`，limit 24）｜摘要層精讀 8 篇（pick 索引 0,2,3,5,7,9,11,14），其中 6 篇沿用此預設｜推翻性檢索 `park use versus residential greenness exposure` 回傳 9 篇，讀後 3 篇確實檢驗過此預設｜樣本來源：2019–2025，Semantic Scholar ＋ Crossref
- 預設 A2：〈自陳問卷測得的身體活動量足以取代加速規的客觀量測〉｜標題層掃描 31 篇（檢索詞 `self-report accelerometer physical activity agreement`，limit 31）｜摘要層精讀 5 篇（pick 索引 1,4,6,8,12），其中 4 篇沿用此預設｜推翻性檢索 `measurement error self-reported physical activity` 回傳 12 篇，讀後 2 篇確實檢驗過此預設｜樣本來源：2019–2025，Semantic Scholar
- 預設 A3：〈居民願意步行前往公園的距離上限大約是 500 公尺〉〔印象，未驗證〕——摘要層精讀只有 2 篇（M′ < 3），不得作為 G3 輸入

## 二、存活候選（生成 12 個 → 存活 3 個）

### 候選 1（C01）：以實際到訪公園的頻率取代住家周邊綠地面積作為暴露變項，重估綠地與身體活動的關聯

- **缺口類型**：G3 預設反轉（反轉 A1）
- **新穎性判定**：ADJACENT
- **搜尋證據**：查詢 1 `green space exposure measurement physical activity`（回傳 12 筆）；查詢 2 `park visitation frequency accelerometer physical activity`（回傳 9 筆）；查詢 3 `residential greenness buffer versus park use exposure`（回傳 7 筆）
- **最接近的既有研究**：Author C et al. (2023)〈Residential greenness and moderate-to-vigorous physical activity in adults〉，DOI:10.5555/synthetic-0002。差異維度是暴露變項的操作化：該研究以住家 500 公尺緩衝區的綠覆率當暴露量，本候選以居民實際到訪公園的頻率與停留時間當暴露量；住得近不等於走得進去，若兩種暴露量測給出的關聯強度差距明顯，就代表既有估計量到的是可及性而不是使用，這是可被否證的預測。
- **已排隊檢查**：該文 limitations 只寫「未區分綠地的可及性與實際使用」，未點名以到訪頻率重做暴露量測；snowball citations 於 2026-08-10 執行，14 篇引用文獻的標題與摘要中未見以到訪頻率為暴露變項者。
- **可行性**：需要同時具備到訪紀錄與活動量的資料，使用者手上有兩個行政區的公園使用日誌；暴露變項的定義需與公園管理單位對齊一次，估兩週。
- **指導教授適配**：請向老師確認，是否接受「暴露量測方式本身的效度」作為主要貢獻，而不是提出新的綠地指標。
- **最可能失敗的原因**：到訪紀錄若倚賴受訪者回憶，量測誤差可能大到蓋掉兩種暴露的差異；社會性風險是口委可能認為換一種暴露量測只是操作化細節，不是研究問題。

### 候選 2（C02）：以公園步道人流計數器的逐時資料，量測公園改造前後居民使用量的實際變化

- **缺口類型**：G6 未被訓練過的資料
- **新穎性判定**：OPEN
- **搜尋證據**：查詢 1 `park renovation footfall counter continuous measurement`（回傳 3 筆）；查詢 2 `natural experiment park improvement physical activity`（回傳 5 筆）；查詢 3（換詞重搜）`pedestrian counter data urban park usage`（回傳 2 筆）
- **最接近的既有研究**：Author K et al. (2022)〈Natural experiment on park renovation and self-reported activity〉，DOI:10.5555/synthetic-0007。差異維度是資料來源：該研究以改造前後兩次問卷的自陳使用量為結果變項，沒有連續量測這一端；自陳會受回憶偏誤與社會期許影響，改造後「感覺變好」容易被記成「去得更多」，有理由讓效果量的分布不同。
- **已排隊檢查**：該文 future work 提到「宜以客觀量測驗證」但未指定量測方式；snowball citations 於 2026-08-10 執行，9 篇引用文獻中未見以連續人流計數為結果變項者。
- **可行性**：需要公園管理單位的計數器原始資料授權，使用者尚未取得；方法端只需中斷時間序列分析，成本低。
- **指導教授適配**：請確認老師是否有管道取得計數器資料，以及公園管理單位是否同意這批資料寫進論文。
- **最可能失敗的原因**：計數器只數人次、數不出活動強度，對不上身體活動的結果變項；社會性風險是管理單位不願被量出改造成效不如預期。

### 候選 3（C03）：台灣都市鄰里公園的遮蔭配置與高齡居民步行活動量的關聯

- **缺口類型**：G1 負空間
- **新穎性判定**：INCREMENTAL
- **搜尋證據**：查詢 1 `park shade older adults walking hot climate`（回傳 14 筆）；查詢 2 `neighbourhood park use older adults subtropical`（回傳 11 筆）；查詢 3（中文索引）「鄰里公園 高齡 步行 遮蔭」於 NDLTD 與 Airiti（合計回傳 6 筆）
- **最接近的既有研究**：Author L et al. (2021)〈Shade provision and older adults' park-based walking〉，DOI:10.5555/synthetic-0008。差異維度是氣候情境：該研究的樣本是溫帶城市的高齡使用者，遮蔭在當地不是限制活動時段的主要因素；台灣夏季的高溫與日照時數讓遮蔭成為能不能出門的門檻，有理由讓遮蔭與步行量的關聯強度與時段分布都不同。
- **已排隊檢查**：該文 limitations 點名「樣本限於溫帶氣候城市」，正好指向本候選；因此本候選定位為在地驗證而非新穎主張；snowball citations 於 2026-08-10 執行，12 篇引用文獻中未見亞熱帶城市情境者。
- **可行性**：需要現場觀察與受訪同意與 IRB；使用者已聯繫兩個行政區的里辦公室，期限內可行。
- **指導教授適配**：請確認老師是否接受「在地驗證」作為主要貢獻，以及系所是否認可此類貢獻定位。
- **最可能失敗的原因**：可招募的高齡受訪人數過少導致統計檢定力不足；社會性風險是夏季現場觀察的時段限制讓資料收集期被壓縮。

## 三、待確認（證據不足，尚未定案）

| 候選 | 暫定狀態 | 還缺哪一項證據 | 補齊的具體動作 |
|---|---|---|---|
| C04 以街景影像自動評分公園步道品質並預測使用量 | DONE? | 標題高度相似的 Author M et al. (2024) 只讀到標題，摘要未取得，母體與結果變項兩項對不齊 | 跑 `pick` 取該篇摘要，比對母體／處理／結果變項／研究設計四項，齊了改判 DONE，不齊回到存活 |
| C05 以穿戴裝置的 GPS 軌跡切出居民在公園內的活動片段 | UNSEARCHABLE | 領域正規術語未定：`park based physical activity GPS` 與 `greenspace exposure trajectory segmentation` 回到兩個不相通的社群 | 先讀兩個社群各一篇綜述確定術語，再用該術語重跑兩輪檢索，才回來判定 |
| C06 現行公園品質評估量表其實測到的是景觀美感而非活動支持度 | 待全文查證 | 量表題項只存在於全文，DOI:10.5555/synthetic-0012 無 OA 版本，尚未讀到方法—測量段落 | 走館際合作取得全文，讀方法段並逐字引出題項文字，才可以下構念質疑 |

## 四、已淘汰

| 候選 | 判定 | 淘汰原因 | 關鍵文獻 | 識別碼 | 發表型態 | 撤稿檢查 |
|---|---|---|---|---|---|---|
| C07 以住家到最近公園的距離預測居民身體活動量 | DONE | 摘要逐字引句：「Using distance from home to the nearest public park, we find that each additional 100 metres is associated with 3.4 fewer minutes of weekly moderate-to-vigorous physical activity among 5,200 urban adults.」母體、自變項、結果變項、研究設計四項全中。 | Author D et al. (2024) | DOI:10.5555/synthetic-0003 | 期刊 | 已查，Crossref 無記錄 |
| C08 以公園設施稽核評分預測公園使用人次 | DONE | 摘要逐字引句：「A facility audit score explains 46 percent of the variance in observed visitor counts across 168 neighbourhood parks.」母體與結果變項與本候選相同，研究設計同為橫斷面稽核。 | Author N et al. (2023) | DOI:10.5555/synthetic-0013 | 會議 | 已查，Crossref 無記錄 |
| C09 比較自陳與加速規測得的公園內身體活動量 | DONE | 摘要逐字引句：「We compare self-reported and accelerometer-measured park-based activity in the same participants and find no agreement beyond chance for sessions shorter than ten minutes.」四項對齊，含同樣的比較設計。 | Author O et al. (2024) | DOI:10.5555/synthetic-0014 | 期刊 | 已查，Crossref 無記錄 |
| C10 建立綠地暴露與身體活動的劑量—反應曲線 | CROWDED | 三篇分別涵蓋本候選的三個子問題：暴露的量化方式（Author E）、劑量—反應函數的形狀（Author F）、跨城市泛化（Author G）；逐一比對後沒有剩餘的未涵蓋子問題，故非 ADJACENT。 | Author E et al. (2022)；Author F et al. (2023)；Author G et al. (2024) | DOI:10.5555/synthetic-0004；DOI:10.5555/synthetic-0005；DOI:10.5555/synthetic-0006 | 期刊、會議、期刊 | 已查，Crossref 無記錄 |
| C11 以社經地位分層檢驗公園可及性的不平等 | CROWDED | 三篇分別涵蓋本候選的三個子問題：可及性指標的建構（Author H）、社經梯度是否存在（Author I）、與健康結果的耦合（Author J）；剩餘子問題為零。 | Author H (2021)；Author I (2022)；Author J (2023) | DOI:10.5555/synthetic-0009；DOI:10.5555/synthetic-0010；DOI:10.5555/synthetic-0011 | 期刊、期刊、會議 | 已查，Crossref 無記錄 |
| C12 以系統性觀察法量測公園分區的活動強度 | CROWDED | 三篇分別涵蓋本候選的三個子問題：觀察工具的信效度（Author P）、分區與活動強度的對應（Author Q）、觀察與穿戴裝置的一致性（Author R）；剩餘子問題為零，且三篇都已在都市公園場域驗證過。 | Author P et al. (2022)；Author Q et al. (2023)；Author R et al. (2024) | DOI:10.5555/synthetic-0015；DOI:10.5555/synthetic-0016；DOI:10.5555/synthetic-0017 | 期刊、會議、會議 | 已查，Crossref 無記錄 |

## 五、下一步

- 本週先讀 Author C et al. (2023) 的全文方法段，確認它的緩衝區暴露量能不能直接換成到訪頻率。
- 向公園管理單位口頭詢問計數器原始資料的取得可能，這一項決定候選 2 能不能留。
- 候選 3 的 IRB 申請書先寫草稿，這條路徑的時間成本最大。
- 待確認的三個候選各有一個明確動作（見第三節），其中 C04 最便宜，先做它。
- 固定動作：把存活候選拿給指導教授，直接問——哪一個你願意帶？

## 六、檢索紀錄（不得省略）

本次檢索後端：lit_api.py

| # | 階段／候選 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | 第1步-共識 | `urban green space physical activity` | 24 | Residential green space exposure and adult physical activity；Greenness metrics and moderate-to-vigorous activity；A survey of green space exposure metrics |
| 2 | 第1步-共識 | `self-report accelerometer physical activity agreement` | 31 | Self-report and device-based measures of activity；Validity of physical activity questionnaires；Agreement between accelerometer and recall |
| 3 | 第1步-推翻A1 | `park use versus residential greenness exposure` | 9 | Does proximity imply use；Access, use and the exposure gap；What greenness buffers actually capture |
| 4 | 第1步-推翻A2 | `measurement error self-reported physical activity` | 12 | Measurement error in activity recall；Social desirability in health surveys；Correcting bias in self-reported activity |
| 5 | C01 | `green space exposure measurement physical activity` | 12 | Residential greenness and moderate-to-vigorous physical activity in adults；Exposure definitions in green space research；Comparing greenness and use-based exposure |
| 6 | C01 | `park visitation frequency accelerometer physical activity` | 9 | Park visits and device-measured activity；Visit frequency as an exposure variable；Time spent in parks and activity minutes |
| 7 | C01 | `residential greenness buffer versus park use exposure` | 7 | Buffer size choices in greenness studies；Use-weighted exposure metrics；Proximity, use and the attenuation problem |
| 8 | C02 | `park renovation footfall counter continuous measurement` | 3 | Footfall sensors in public space；Counting park visitors automatically；Continuous monitoring of open space use |
| 9 | C02 | `natural experiment park improvement physical activity` | 5 | Natural experiment on park renovation and self-reported activity；Park improvements and neighbourhood activity；Evaluating open space investment |
| 10 | C02 | `pedestrian counter data urban park usage` | 2 | Pedestrian counters for urban analytics；Sensor-based estimates of park usage |
| 11 | C03 | `park shade older adults walking hot climate` | 14 | Shade provision and older adults' park-based walking；Thermal comfort and outdoor activity；Heat exposure and walking in older populations |
| 12 | C03 | `neighbourhood park use older adults subtropical` | 11 | Neighbourhood parks and ageing residents；Older adults' outdoor activity in warm cities；Park design for an ageing population |
| 13 | C03 | 「鄰里公園 高齡 步行 遮蔭」（NDLTD＋Airiti） | 6 | 都市鄰里公園遮蔭設施對高齡者步行行為之影響；社區公園使用行為與高齡者身體活動關聯之研究；亞熱帶都市公園夏季使用時段之調查 |
| 14 | C04 | `street view imagery park path quality visitation` | 8 | Street view imagery for streetscape audits；Automated path quality scoring；Image-based prediction of park visits |
| 15 | C05 | `park based physical activity GPS segmentation` | 4 | Segmenting GPS traces by land use；Trajectory analysis for activity episodes；Linking GPS and accelerometer data |
| 16 | C06 | `park quality audit scale aesthetics activity support` | 6 | Audit tools for park quality；Aesthetics and perceived safety in parks；What park quality scales measure |
| 17 | C07 | `distance to nearest park physical activity adults` | 11 | Distance to parks and adult physical activity；Access metrics in built environment research；Proximity effects on walking |
| 18 | C08 | `park facility audit score visitor counts` | 9 | Facility audits and observed park use；Amenities and visitor numbers；Predicting park attendance from design |
| 19 | C09 | `self-report versus accelerometer park based activity` | 7 | Comparing recall and device measures in parks；Session length and recall accuracy；Device-based validation of park activity |
| 20 | C10 | `green space dose response physical activity` | 15 | Dose-response between greenness and activity；Threshold effects in green space exposure；Generalising dose-response across cities |
| 21 | C11 | `park accessibility socioeconomic inequality` | 13 | Measuring park accessibility；Socioeconomic gradients in park access；Access inequality and health outcomes |
| 22 | C12 | `systematic observation park zones activity intensity` | 10 | Systematic observation of park zones；Zone-level activity intensity；Agreement between observation and wearables |

## 七、可查證清單（複製給 lit-review）

```
retract: 10.5555/synthetic-0002 10.5555/synthetic-0003 10.5555/synthetic-0004 10.5555/synthetic-0005 10.5555/synthetic-0006 10.5555/synthetic-0007 10.5555/synthetic-0008 10.5555/synthetic-0009 10.5555/synthetic-0010 10.5555/synthetic-0011 10.5555/synthetic-0013 10.5555/synthetic-0014 10.5555/synthetic-0015 10.5555/synthetic-0016 10.5555/synthetic-0017
check:   （本報告全部引用文獻）
```

```json rgh-block
{
"schema": "rgh-block/1",
"settlement": {"generated": 12, "survived": 3, "pending": 3, "killed": 5},
"assumptions": [
{"id": "A1", "status": "framed", "anchor": "住家周邊的綠地面積可以代表居民實際獲得的綠地暴露", "frame": {"N": 24, "query": "urban green space physical activity", "limit": 24, "Mp": 8, "pick": [0,2,3,5,7,9,11,14], "M": 6, "refute_query": "park use versus residential greenness exposure", "Kp": 9, "K": 3, "sample": "2019–2025，Semantic Scholar ＋ Crossref"}},
{"id": "A2", "status": "framed", "anchor": "自陳問卷測得的身體活動量足以取代加速規的客觀量測", "frame": {"N": 31, "query": "self-report accelerometer physical activity agreement", "limit": 31, "Mp": 5, "pick": [1,4,6,8,12], "M": 4, "refute_query": "measurement error self-reported physical activity", "Kp": 12, "K": 2, "sample": "2019–2025，Semantic Scholar"}},
{"id": "A3", "status": "impression", "anchor": "居民願意步行前往公園的距離上限大約是 500 公尺", "frame": null}
]
}
```
