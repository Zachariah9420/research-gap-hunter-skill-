# 研究缺口報告：稀疏自編碼器抽取的特徵在微調後的穩定性

**模式**：完整獵捕
**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）
**貢獻判準**：方法新穎
**中文索引**：不適用（題目非在地界定，使用者不在華語學術體系）
**降級聲明**：無
**候選結算**：生成 7 ＝ 存活 2 ＋ 待確認 2 ＋ 已淘汰 3

> 本檔是 evals 用的**手寫**合成樣本，與 good_report.md 沒有衍生關係，也不由
> make_fixtures.py 生成。它存在的理由有兩個：
> （1）釘住表頭〈中文索引〉的**第三個**合法值「不適用（題目非在地界定，使用者不在
> 華語學術體系）」——這個題目既非在地界定、使用者也不在華語學術體系，兩個例外都不
> 成立，所以不該掛「未檢索」那句覆蓋率警語；
> （2）提供一份與 good_report.md 主題、形狀都不同的第二份綠樣本，避免所有樣本共用
> 同一個基底時，查核器只被證明「認得那一份報告」。
>
> 文中所有文獻皆為虛構（Author S、Author T……），識別碼使用 Crossref 測試前綴
> 10.5555，不對應任何真實出版品。

## 一、領域共識與未被質疑的預設

- 主流立場：稀疏自編碼器抽出的特徵被當成模型內部的穩定實體，可以跨檢查點沿用（代表文獻：Author S et al. (2024)〈Sparse features as stable model internals〉，DOI:10.5555/synthetic-0101）
- 主流立場：特徵品質以人工標註的可解釋性分數衡量，標註流程本身不被檢驗（代表文獻：Author T (2025)〈Rating interpretability of learned features〉，DOI:10.5555/synthetic-0102）
- 預設 A1：〈特徵的身分可以用字典向量的餘弦相似度跨檢查點對應〉｜標題層掃描 22 篇（檢索詞 `sparse autoencoder feature identity checkpoint`，limit 22）｜摘要層精讀 7 篇（pick 索引 0,1,3,5,8,10,13），其中 5 篇沿用此預設｜推翻性檢索 `feature matching instability across training checkpoints` 回傳 11 篇，讀後 3 篇確實檢驗過此預設｜樣本來源：2021–2026，Semantic Scholar ＋ Crossref
- 預設 A2：〈可解釋性標註的評分者間信度足夠高，不必另行報告〉｜標題層掃描 18 篇（檢索詞 `interpretability annotation rater agreement feature`，limit 18）｜摘要層精讀 6 篇（pick 索引 0,2,4,7,9,11），其中 4 篇沿用此預設｜推翻性檢索 `inter-rater reliability interpretability ratings` 回傳 9 篇，讀後 2 篇確實檢驗過此預設｜樣本來源：2021–2026，Semantic Scholar
- 預設 A3：〈微調只會加上新特徵，不會拆散既有特徵〉〔印象，未驗證〕——摘要層精讀只有 2 篇（M′ < 3），不得作為 G3 輸入

## 二、存活候選（生成 7 個 → 存活 2 個）

### 候選 1（C01）：以餘弦相似度對應的特徵身分，在微調後會系統性高估穩定性

- **缺口類型**：G3 預設反轉（反轉 A1）
- **新穎性判定**：ADJACENT
- **搜尋證據**：查詢 1 `sparse autoencoder feature stability fine-tuning`（回傳 13 筆）；查詢 2 `feature identity matching cosine similarity drift`（回傳 8 筆）；查詢 3 `dictionary learning representation drift after adaptation`（回傳 6 筆）
- **最接近的既有研究**：Author U et al. (2025)〈Measuring dictionary drift across training runs〉，DOI:10.5555/synthetic-0103。差異維度是處理與比較基準：該研究比較的是**不同隨機種子的獨立訓練**，本候選比較的是**同一個基礎模型微調前後**。為什麼這個差異有理由造成不同結果：獨立訓練之間沒有共同起點，餘弦對應本來就只能算弱基準；微調前後共用起點，對應看起來會非常好，因此高估的方向與幅度都可能相反，這是可被否證的預測。
- **已排隊檢查**：該文 limitations 只提到字典尺寸的影響，未點名微調情境；`snowball --direction citations DOI:10.5555/synthetic-0103` 於 2026-08-10 執行，回傳 17 筆，其中未見以微調前後為對照者。
- **可行性**：需要同一基礎模型的微調前後檢查點與一份標註集，使用者已有兩組檢查點；訓練字典的算力約三天。
- **指導教授適配**：請向老師確認，是否接受「對應方法本身的效度」作為主要貢獻，而不是提出新的字典學習方法。
- **最可能失敗的原因**：若兩個檢查點的差異太小，高估幅度會落在雜訊裡而測不出來；社會性風險是口委可能認為這是評測細節而非研究問題。

### 候選 2（C02）：把特徵穩定性的量測從字典空間改到下游行為空間

- **缺口類型**：G1 負空間
- **新穎性判定**：OPEN
- **搜尋證據**：查詢 1 `behavioural equivalence of sparse features`（回傳 2 筆，皆不相關）；查詢 2 `feature stability downstream intervention effect`（回傳 3 筆，皆為特徵編輯而非穩定性）；查詢 3（換詞重搜，術語校正後）`causal intervention consistency learned features`（回傳 2 筆，仍不相關）
- **最接近的既有研究**：三輪查詢（含一次術語校正）都沒有回傳可以當成最近鄰的文獻；最接近的只有可解釋性評測的上位概念綜述，量測對象與方法都不同，不足以當最近鄰。這是「這次搜尋沒有回傳」，不是關於文獻總體的結論。
- **已排隊檢查**：不適用（無最近鄰）
- **可行性**：需要一組可重複的干預實驗腳本，使用者要自己寫，估三週；資料端沒有額外門檻。
- **最可能失敗的原因**：行為空間的量測雜訊可能大到蓋掉字典空間的差異；社會性風險是完全空白的檢索結果往往意味著這個問題被領域認為不重要，這一點要先跟老師確認。
- **指導教授適配**：請確認老師是否認為「換一個量測空間」在本領域算得上方法貢獻。

## 三、待確認（證據不足，尚未定案）

| 候選 | 暫定狀態 | 還缺哪一項證據 | 補齊的具體動作 |
|---|---|---|---|
| C03 微調後新增特徵的比例可預測任務遷移幅度 | DONE? | 標題高度相似的 Author V et al. (2025) 只讀到標題，摘要未取得，處理與結果變項兩項對不齊 | 跑 `pick` 取該篇摘要，比對母體／處理／結果變項／研究設計四項，齊了改判 DONE，不齊回到存活 |
| C04 借用「基因表現漂移」框架描述特徵漂移 | 待驗證 | G2 三段式的第 3 項沒過：說不出基因表現裡的「表現量」對應到特徵空間的哪一個可量測的量，也說不出這個對應要怎麼被否證 | 讀 DOI:10.5555/synthetic-0108 的方法段，逐字抄出它的表現量定義，寫成一句可測量的對應式；寫不出來就結案為不適用 |

## 四、已淘汰

| 候選 | 判定 | 淘汰原因 | 關鍵文獻 | 識別碼 | 發表型態 | 撤稿檢查 |
|---|---|---|---|---|---|---|
| C05 用線性探針比較微調前後的特徵可分性 | DONE | 摘要逐字引句：「We probe the same base model before and after fine-tuning and report that linear separability of sparse features changes by less than two points on all six tasks.」母體、處理、結果變項、研究設計四項全中。 | Author W et al. (2025) | DOI:10.5555/synthetic-0104 | 期刊 | 已查，Crossref 無記錄 |
| C06 以字典大小為調節變項檢驗特徵穩定性 | CROWDED | 三篇分別涵蓋本候選的三個子問題：字典尺寸與重建誤差（Author X）、尺寸與特徵數的關係（Author Y）、尺寸對跨檢查點對應的影響（Author Z）；逐一比對後沒有剩餘的未涵蓋子問題，故非 ADJACENT。 | Author X et al. (2023)；Author Y et al. (2024)；Author Z et al. (2025) | DOI:10.5555/synthetic-0105；DOI:10.5555/synthetic-0106；DOI:10.5555/synthetic-0107 | 期刊、會議、會議 | 已查，Crossref 無記錄 |
| C07 用自動化說明生成取代人工可解釋性標註 | DONE | 摘要逐字引句：「An automated explainer reproduces human interpretability ratings with a rank correlation of 0.81 across twelve thousand features.」母體與結果變項與本候選相同，研究設計同為與人工標註的相關性驗證。 | Author AA et al. (2024) | DOI:10.5555/synthetic-0109 | 會議 | 已查，Crossref 無記錄 |

## 五、下一步

- 本週先讀 Author U et al. (2025) 的方法段，確認它的對應演算法能不能直接搬到微調前後的設定。
- 候選 2 先寫一份最小的干預腳本跑通一個特徵，再決定要不要投入三週。
- C03 最便宜：一次 `pick` 就能決定它是 DONE 還是回到存活，先做它。
- C04 的框架移植要嘛寫得出可測量的對應式，要嘛就結案，不要讓它一直掛著。
- 固定動作：把存活候選拿給指導教授，直接問——哪一個你願意帶？

## 六、檢索紀錄（不得省略）

本次檢索後端：lit_api.py

| # | 階段／候選 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | 第1步-共識 | `sparse autoencoder feature identity checkpoint` | 22 | Sparse features as stable model internals；Checkpoint-to-checkpoint feature matching；Dictionary learning for transformer activations |
| 2 | 第1步-共識 | `interpretability annotation rater agreement feature` | 18 | Rating interpretability of learned features；Annotation protocols for feature explanation；Human evaluation of sparse dictionaries |
| 3 | 第1步-推翻A1 | `feature matching instability across training checkpoints` | 11 | Instability of learned dictionaries；When do features persist；Matching criteria and their failure modes |
| 4 | 第1步-推翻A2 | `inter-rater reliability interpretability ratings` | 9 | Agreement among interpretability annotators；Reliability of explanation ratings；Calibrating human raters for features |
| 5 | C01 | `sparse autoencoder feature stability fine-tuning` | 13 | Measuring dictionary drift across training runs；Feature persistence under adaptation；Fine-tuning and representation change |
| 6 | C01 | `feature identity matching cosine similarity drift` | 8 | Cosine matching for dictionary elements；Drift metrics for learned features；Identity criteria in sparse coding |
| 7 | C01 | `dictionary learning representation drift after adaptation` | 6 | Representation drift in adapted models；Adaptation effects on sparse codes；Post-hoc dictionary alignment |
| 8 | C02 | `behavioural equivalence of sparse features` | 2 | Behavioural probing of language models；Equivalence classes in model behaviour |
| 9 | C02 | `feature stability downstream intervention effect` | 3 | Feature editing for behaviour control；Intervention strength and side effects；Steering vectors in practice |
| 10 | C02 | `causal intervention consistency learned features` | 2 | Causal probing of learned representations；Consistency of activation patching |
| 11 | C03 | `new feature proportion transfer performance fine-tuning` | 7 | Newly emerged features after adaptation；Feature counts and transfer；Task similarity and dictionary overlap |
| 12 | C04 | `gene expression drift framework transfer representation` | 5 | Expression drift in developmental biology；Framework transfer across scientific domains；Quantifying drift with reference distributions |
| 13 | C05 | `linear probe separability before after fine-tuning` | 9 | Probing sparse features before and after fine-tuning；Linear probes for dictionary elements；Separability metrics for representations |
| 14 | C06 | `dictionary size moderator feature stability` | 12 | Dictionary size and reconstruction error；How many features does a model have；Size effects on cross-checkpoint matching |
| 15 | C07 | `automated explanation replace human interpretability rating` | 10 | Automated explainers for sparse features；Scaling interpretability annotation；Rank agreement between machine and human raters |

## 七、可查證清單（複製給 lit-review）

```
retract: 10.5555/synthetic-0101 10.5555/synthetic-0102 10.5555/synthetic-0103 10.5555/synthetic-0104 10.5555/synthetic-0105 10.5555/synthetic-0106 10.5555/synthetic-0107 10.5555/synthetic-0108 10.5555/synthetic-0109
check:   （本報告全部引用文獻）
```

```json rgh-block
{
"schema": "rgh-block/1",
"settlement": {"generated": 7, "survived": 2, "pending": 2, "killed": 3},
"assumptions": [
{"id": "A1", "status": "framed", "anchor": "特徵的身分可以用字典向量的餘弦相似度跨檢查點對應", "frame": {"N": 22, "query": "sparse autoencoder feature identity checkpoint", "limit": 22, "Mp": 7, "pick": [0,1,3,5,8,10,13], "M": 5, "refute_query": "feature matching instability across training checkpoints", "Kp": 11, "K": 3, "sample": "2021–2026，Semantic Scholar ＋ Crossref"}},
{"id": "A2", "status": "framed", "anchor": "可解釋性標註的評分者間信度足夠高，不必另行報告", "frame": {"N": 18, "query": "interpretability annotation rater agreement feature", "limit": 18, "Mp": 6, "pick": [0,2,4,7,9,11], "M": 4, "refute_query": "inter-rater reliability interpretability ratings", "Kp": 9, "K": 2, "sample": "2021–2026，Semantic Scholar"}},
{"id": "A3", "status": "impression", "anchor": "微調只會加上新特徵，不會拆散既有特徵", "frame": null}
]
}
```
