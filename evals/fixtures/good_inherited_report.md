# 研究缺口報告：都市綠地暴露量測與居民身體活動

**模式**：完整獵捕
**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）
**貢獻判準**：方法新穎
**中文索引**：不適用（題目非在地界定，使用者不在華語學術體系）
**地形來源**：landscape_都市綠地暴露量測_20260801.md（承接 W1、W3 共 2 條）
**降級聲明**：無
**候選結算**：生成 5 ＝ 存活 2 ＋ 待確認 1 ＋ 已淘汰 2

> 本檔是 evals 用的合成樣本。文中所有文獻皆為虛構（Author CA、Author CB……），
> 識別碼使用 Crossref 測試前綴 10.5555，不對應任何真實出版品。

## 一、領域共識與未被質疑的預設

- 主流立場：綠地暴露的計算範圍幾乎都綁在住家地址上，活動範圍被當成可以由住家位置近似的東西（代表文獻：Author CA et al. (2022)〈Home-based buffers as the default exposure unit〉，DOI:10.5555/synthetic-3001）
- 預設 A1：〈居民的綠地暴露可以用住家所在行政區的平均值近似〉｜標題層掃描 21 篇（檢索詞 `neighbourhood unit green space exposure adults`，limit 21）｜摘要層精讀 7 篇（pick 索引 0,2,4,6,9,12,15），其中 6 篇沿用此預設｜推翻性檢索 `activity space versus residential neighbourhood exposure` 回傳 10 篇，讀後 4 篇確實檢驗過此預設｜樣本來源：2019–2025，Semantic Scholar ＋ Crossref
- 預設 A2〔承接自地形 W1，支撐家族 F1、F2、F3〕：〈暴露可以用一個「人不在場也量得到」的空間代理量代替〉——未補取樣框，效力同〔印象，未驗證〕，不得作為 G3 輸入
- 預設 A3〔承接自地形 W3，已補取樣框〕：〈量測到的那個時點或那一段，可以代表更長的期間〉｜標題層掃描 18 篇（檢索詞 `greenness exposure temporal stability`，limit 18）｜摘要層精讀 6 篇（pick 索引 0,1,3,5,8,11），其中 5 篇沿用此預設｜推翻性檢索 `seasonal variation greenness exposure misclassification` 回傳 11 篇，讀後 4 篇確實檢驗過此預設｜樣本來源：2018–2025，Semantic Scholar

## 二、存活候選（生成 5 個 → 存活 2 個）

### 候選 1（C01）：以個人日常活動空間取代住家行政區作為綠地暴露的計算範圍，重估暴露與身體活動的關聯

- **缺口類型**：G3 預設反轉（反轉 A1）
- **新穎性判定**：ADJACENT
- **搜尋證據**：查詢 1 `activity space green space exposure physical activity`（回傳 11 筆）；查詢 2 `individual mobility derived exposure neighbourhood effect`（回傳 8 筆）
- **最接近的既有研究**：Author CB et al. (2023)〈Activity-space exposure and adult walking behaviour〉，DOI:10.5555/synthetic-3002。差異維度是分析單位：該研究以行政區平均值為暴露量並在討論中承認它抹掉了通勤沿線的綠地，本候選改以個人一週的活動軌跡切出暴露範圍；通勤路線上的綠地若佔了實際暴露的一大半，兩種算法會給出方向一致但強度差距明顯的估計，這是可被否證的預測。
- **已排隊檢查**：該文 limitations 寫「暴露單元的選擇仍待檢驗」，未點名以活動空間重算；snowball citations 於 2026-08-10 執行，11 篇引用文獻的標題與摘要中未見以個人活動軌跡界定暴露範圍者。
- **可行性**：需要一週以上的個人移動軌跡與活動量，使用者手上有一批既有的穿戴裝置資料；暴露範圍的定義要與資料保管單位確認一次，估兩週。
- **指導教授適配**：請向老師確認，是否接受「暴露單元的選擇」本身作為主要貢獻。
- **最可能失敗的原因**：軌跡資料的取樣間隔若過疏，切出來的活動空間會退化成住家周邊，兩種算法的差異被自己的資料抹掉；社會性風險是口委可能認為換一個暴露單元只是操作化細節。

### 候選 2（C02）：以連續一年的逐月綠地暴露序列取代單一時點量測，檢驗暴露錯分是否隨季節改變

- **缺口類型**：G3 預設反轉（反轉 A3）
- **新穎性判定**：OPEN
- **搜尋證據**：查詢 1 `monthly greenness exposure time series misclassification`（回傳 4 筆）；查詢 2 `seasonal greenness and physical activity association stability`（回傳 6 筆）；查詢 3（換詞重搜）`repeated measures vegetation index exposure assessment`（回傳 3 筆）
- **最接近的既有研究**：Author CC et al. (2021)〈Single-date vegetation indices in exposure assessment〉，DOI:10.5555/synthetic-3003。差異維度是時間尺度：該研究以單一夏季影像代表全年暴露，本候選以逐月序列重算；落葉期與生長期的綠覆差距若大於族群間的差距，單一時點的排序本身就會換位，有理由讓關聯強度隨取樣月份改變。
- **已排隊檢查**：該文 future work 提到「宜檢驗影像日期的敏感性」但未指定做法；snowball citations 於 2026-08-10 執行，7 篇引用文獻中未見以逐月序列重算暴露者。
- **可行性**：影像來源為公開資料，成本低；需要一次批次處理的運算時間，使用者已有可用的工作站。
- **指導教授適配**：請確認老師是否認為時間尺度的敏感性分析足以撐起一篇論文，而不是只當成附錄。
- **最可能失敗的原因**：逐月序列之間高度相關，重算後排序幾乎不動，結論退化成「本來就沒差」；社會性風險是這個結果不利於發表。

## 三、待確認（證據不足，尚未定案）

| 候選 | 暫定狀態 | 還缺哪一項證據 | 補齊的具體動作 |
|---|---|---|---|
| C03 以通勤路線沿線的綠地暴露預測通勤者的身體活動量 | DONE? | 標題高度相似的 Author CD et al. (2024) 只讀到標題，摘要未取得，母體與研究設計兩項對不齊 | 跑 `pick` 取該篇摘要，比對母體／處理／結果變項／研究設計四項，齊了改判 DONE，不齊回到存活 |

## 四、已淘汰

| 候選 | 判定 | 淘汰原因 | 關鍵文獻 | 識別碼 | 發表型態 | 撤稿檢查 |
|---|---|---|---|---|---|---|
| C04 以住家周邊綠覆率預測成人每週中高強度身體活動時間 | DONE | 摘要逐字引句：「Using a 500-metre residential buffer, we find that each 10 percent increase in green cover is associated with 6.1 additional minutes of weekly moderate-to-vigorous physical activity among 4,100 urban adults.」母體、自變項、結果變項、研究設計四項全中。 | Author CE et al. (2023) | DOI:10.5555/synthetic-3004 | 期刊 | 已查，Crossref 無記錄 |
| C05 比較不同緩衝區半徑對綠地暴露估計值的影響 | CROWDED | 三篇分別涵蓋本候選的三個子問題：半徑選擇的敏感性（Author CF）、半徑與健康結果的耦合（Author CG）、跨城市的半徑可移植性（Author CH）；逐一比對後沒有剩餘的未涵蓋子問題，故非 ADJACENT。 | Author CF et al. (2021)；Author CG et al. (2022)；Author CH et al. (2024) | DOI:10.5555/synthetic-3005；DOI:10.5555/synthetic-3006；DOI:10.5555/synthetic-3007 | 期刊、期刊、會議 | 已查，Crossref 無記錄 |

## 五、下一步

- 本週先讀 Author CB et al. (2023) 的全文方法段，確認它的行政區暴露量能不能直接換成活動空間。
- 向資料保管單位確認軌跡資料的二次利用範圍，這一項決定候選 1 能不能留。
- 逐月影像的批次處理先跑一個行政區試算，確認候選 2 的訊號量級。
- C03 只差一次 `pick`，先做它。
- 固定動作：把存活候選拿給指導教授，直接問——哪一個你願意帶？

## 六、檢索紀錄（不得省略）

本次檢索後端：lit_api.py

| # | 階段／候選 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | 第1步-共識 | `neighbourhood unit green space exposure adults` | 21 | Home-based buffers as the default exposure unit；Administrative units in exposure assessment；Neighbourhood definitions and health associations |
| 2 | 第1步-推翻A1 | `activity space versus residential neighbourhood exposure` | 10 | Activity-space exposure and adult walking behaviour；Beyond the residential neighbourhood；Mobility-based exposure measures |
| 3 | 第1步-共識（補框 A3） | `greenness exposure temporal stability` | 18 | Temporal stability of vegetation indices；Single-date vegetation indices in exposure assessment；Repeat imagery in environmental epidemiology |
| 4 | 第1步-推翻A3 | `seasonal variation greenness exposure misclassification` | 11 | Seasonal misclassification of greenness exposure；Leaf-off imagery and exposure ranking；Month of acquisition and effect estimates |
| 5 | C01 | `activity space green space exposure physical activity` | 11 | Activity-space exposure and adult walking behaviour；Green space along commuting routes；Mobility-weighted greenness measures |
| 6 | C01 | `individual mobility derived exposure neighbourhood effect` | 8 | Mobility-derived exposure and the neighbourhood effect；GPS-based exposure windows；Individual trajectories in environmental health |
| 7 | C02 | `monthly greenness exposure time series misclassification` | 4 | Monthly composites for exposure assessment；Time-series greenness and misclassification；Image date sensitivity in exposure studies |
| 8 | C02 | `seasonal greenness and physical activity association stability` | 6 | Season and the greenness-activity association；Stability of environmental effect estimates；Warm-season bias in exposure studies |
| 9 | C02 | `repeated measures vegetation index exposure assessment` | 3 | Repeated-measures vegetation indices；Longitudinal exposure assessment with satellite data；Averaging windows in greenness exposure |
| 10 | C03 | `commuting route green exposure physical activity` | 9 | Green exposure along commuting routes；Route-based environmental exposure；Commute greenness and active travel |
| 11 | C04 | `residential green cover moderate-to-vigorous physical activity` | 12 | Residential green cover and weekly activity minutes；Buffer-based green cover and adult activity；Green cover gradients and activity |
| 12 | C05 | `buffer radius sensitivity green space exposure` | 14 | Buffer radius choices in greenness research；Radius sensitivity and health associations；Transferability of buffer definitions |

## 七、可查證清單（複製給 lit-review）

```
retract: 10.5555/synthetic-3001 10.5555/synthetic-3002 10.5555/synthetic-3003 10.5555/synthetic-3004 10.5555/synthetic-3005 10.5555/synthetic-3006 10.5555/synthetic-3007
check:   （本報告全部引用文獻）
```

```json rgh-block
{
"schema": "rgh-block/1",
"settlement": {"generated": 5, "survived": 2, "pending": 1, "killed": 2},
"assumptions": [
{"id": "A1", "status": "framed", "anchor": "居民的綠地暴露可以用住家所在行政區的平均值近似", "frame": {"N": 21, "query": "neighbourhood unit green space exposure adults", "limit": 21, "Mp": 7, "pick": [0,2,4,6,9,12,15], "M": 6, "refute_query": "activity space versus residential neighbourhood exposure", "Kp": 10, "K": 4, "sample": "2019–2025，Semantic Scholar ＋ Crossref"}},
{"id": "A2", "status": "inherited", "anchor": "暴露可以用一個「人不在場也量得到」的空間代理量代替", "frame": null, "wall": "W1", "families": ["F1","F2","F3"]},
{"id": "A3", "status": "inherited_framed", "anchor": "量測到的那個時點或那一段，可以代表更長的期間", "frame": {"N": 18, "query": "greenness exposure temporal stability", "limit": 18, "Mp": 6, "pick": [0,1,3,5,8,11], "M": 5, "refute_query": "seasonal variation greenness exposure misclassification", "Kp": 11, "K": 4, "sample": "2018–2025，Semantic Scholar"}, "wall": "W3"}
]
}
```
