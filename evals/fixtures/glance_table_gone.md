# 領域地形報告：都市綠地暴露量測

**模式**：領域地形（盤點做法，不淘汰、不判新穎性）
**文獻工具**：lit-review lit_api.py（存在性、撤稿、滾雪球均已機器查核）
**檢索語言**：英文
**這份報告不做什麼**：不淘汰任何做法、不判斷新穎性、不宣稱任何做法沒有人做過。要新穎性判定請跑缺口獵捕。
**家族結算**：盤點 7 個家族，其中〔涵蓋不足〕1 個
**檢索量**：實際跑了 10 次檢索

> 本檔是 evals 用的合成樣本。文中所有文獻皆為虛構（Author BA、Author BB……），
> 識別碼使用 Crossref 測試前綴 10.5555，不對應任何真實出版品。
> 相對於 good_landscape.md，本檔刻意壞掉一處：〈一、一眼表〉的表整張不見了，標題還在。這是「從渲染畫面把表複製回來」的樣子——每一列連同表頭都沒有直線 `|`，於是沒有任何形狀認得出這裡曾經有一張表，而 check_status／check_cost 是逐列跑的，沒有列就沒有對象。整張表沒寫也走同一筆。這是節名唯一被允許的用法：它只能**多**出一筆 finding，不能決定要不要解析。

## 一、一眼表

## 二、各家族

### F1 遙測綠覆指數

- **一句話**：用衛星或航照影像計算植被指數，再對每個居住地址取周邊緩衝區的平均值。
- **買到什麼**：一次計算就覆蓋整座城市，任何地址都給得出數字，跨城市與跨年度可以直接比。
- **付出什麼**：從空中量到的綠包含私人庭院、行道樹冠與封閉校園，居民走不進去的綠也被算進暴露量；影像時點與雲遮也會讓同一地址的數值在不同月份差很多。
- **錨定文獻**：Author BA et al. (2019)〈Satellite-derived vegetation indices as exposure metrics in health research〉，DOI:10.5555/synthetic-2001；Author BB (2021)〈A review of greenness exposure assessment methods〉，arXiv:2405.00021；Author BC et al. (2022)〈Buffer size sensitivity in residential greenness studies〉，DOI:10.5555/synthetic-2003；Author BD et al. (2023)〈Seasonal variation in vegetation index exposure estimates〉，DOI:10.5555/synthetic-2004
- **狀態**：飽和｜`satellite vegetation index greenness exposure` 在 Semantic Scholar 回傳 318 筆，其中 2023 之後 41 筆
- **結構上做不到**：它的輸出是每個像元的反射率換算值，本身不帶「這塊綠地能不能進去」這個屬性；要區分可及與不可及，得再疊一層權屬或出入口圖資。
- **默默預設**：F1-a〈從空中看得到的綠，就是地面上的人接觸得到的綠〉；F1-b〈影像取得的那個時點，可以代表更長一段期間的綠量〉
- **進入成本**：公開影像與一套地理資訊軟體即可，前置知識是投影與緩衝區運算；一個人約一至二週可以跑出全市結果。

### F2 圖資緩衝區與設施清冊

- **一句話**：用政府公園圖資與路網，算出每個地址在多少距離內有多少公園。
- **買到什麼**：單位與政策文件一致（公頃、人均綠地、步行五分鐘），結果直接接得上都市計畫的討論。
- **付出什麼**：圖資更新落後現地，關閉整修中的公園仍留在清冊裡；多邊形只說有沒有，不說走不走得進去、開不開放。
- **錨定文獻**：Author BE et al. (2018)〈Accessibility measures of urban parks: a comparison〉，DOI:10.5555/synthetic-2005；Author BF (2020)〈Network distance versus Euclidean buffers in park accessibility〉，DOI:10.5555/synthetic-2006；Author BG et al. (2022)〈Administrative park inventories and their update lag〉，DOI:10.5555/synthetic-2007；Author BH et al. (2024)〈Service area analysis for neighbourhood open space〉，DOI:10.5555/synthetic-2008
- **狀態**：飽和｜`park accessibility buffer network analysis` 在 Semantic Scholar 回傳 264 筆，其中 2023 之後 29 筆
- **結構上做不到**：它算的是圖資上的幾何關係，本身不含任何使用行為；要講使用，得再接一種量到人的資料。
- **默默預設**：F2-a〈圖資上標記為公園的多邊形，實際上都進得去、用得到〉
- **進入成本**：公開圖資與地理資訊軟體，前置知識是路網分析；一個人約一週。

### F3 街景影像評分

- **一句話**：抓取街景影像，由評分者或影像模型評出街道層級的綠意與品質分數。
- **買到什麼**：拿到人眼高度看得到的綠，和遙測給的俯視綠量是兩件事；空間解析度細到單一路段。
- **付出什麼**：影像涵蓋只到車輛開得到的街道，巷弄與公園內部拍不到；評分判準在不同城市之間搬動時要重新校準，人工評分的成本隨路段數線性上升。
- **錨定文獻**：Author BI et al. (2020)〈Street view imagery for eye-level greenness assessment〉，DOI:10.5555/synthetic-2009；Author BJ et al. (2021)〈Human versus automated scoring of streetscape quality〉，DOI:10.5555/synthetic-2010；Author BK (2022)〈Coverage bias in street view based environmental audits〉，DOI:10.5555/synthetic-2011；Author BL et al. (2023)〈Transferability of streetscape scoring models across cities〉，DOI:10.5555/synthetic-2012；Author BM et al. (2024)〈Eye-level and overhead greenness give different exposure estimates〉，DOI:10.5555/synthetic-2013
- **狀態**：活躍｜`street view imagery eye-level greenness` 在 Semantic Scholar 回傳 187 筆，其中 2023 之後 96 筆
- **結構上做不到**：它的輸入是拍攝當下的一張影像，本身不帶時間軸；要講季節或日夜差異，得另外收不同時點的影像。
- **默默預設**：F3-a〈街道視角拍到的畫面，等同使用者在該處的視覺經驗〉；F3-b〈評分判準對不同年齡與不同行動能力的使用者一致〉
- **進入成本**：影像取用授權與一台可跑影像模型的機器，前置知識是影像處理與抽樣設計；一個人約三至四週。

### F4 使用者自陳問卷

- **一句話**：直接問居民到訪頻率、停留時間與對周邊綠意的感受。
- **買到什麼**：拿得到動機、偏好與感受，這些在任何客觀量測裡都不存在對應欄位；成本低、可與健康量表放在同一份問卷。
- **付出什麼**：回憶偏誤與社會期許讓次數被高估，「上個月去了幾次」對多數受訪者是重建而不是回憶；重複施測的疲勞讓長期追蹤難做。
- **錨定文獻**：Author BN et al. (2017)〈Self-reported park visitation: validity against objective measures〉，DOI:10.5555/synthetic-2014；Author BO (2019)〈Recall bias in leisure activity questionnaires〉，DOI:10.5555/synthetic-2015；Author BP et al. (2021)〈Perceived versus measured neighbourhood greenness〉，DOI:10.5555/synthetic-2016；Author BQ et al. (2023)〈Questionnaire design effects on reported outdoor time〉，DOI:10.5555/synthetic-2017
- **狀態**：飽和｜`self-reported park visitation questionnaire validity` 在 Semantic Scholar 回傳 221 筆，其中 2023 之後 24 筆
- **結構上做不到**：它的輸出是受訪者對自己行為的陳述，本身不帶外部校準；要講量測誤差的大小，得同時收一種不倚賴陳述的資料。
- **默默預設**：F4-a〈受訪者說得出自己上個月去了幾次〉
- **進入成本**：問卷設計、抽樣與研究倫理審查，前置知識是量表與抽樣；一個人約四至六週含審查等待。

### F5 行動裝置定位軌跡

- **一句話**：用手機或穿戴裝置的定位軌跡，切出落在綠地多邊形內的停留片段。
- **買到什麼**：個人層次、有時間戳的實際停留，可以同時回答去了哪裡、待多久、什麼時段。
- **付出什麼**：願意交出定位資料的人本身就是特定族群，樣本自選；都市峽谷的定位誤差可達數十公尺，公園邊界附近的判定不穩；資料授權與隱私審查的行政成本高於方法本身。
- **錨定文獻**：Author BR et al. (2020)〈GPS-based measurement of green space exposure〉，DOI:10.5555/synthetic-2018；Author BS et al. (2022)〈Positional error in urban canyons and activity space delineation〉，DOI:10.5555/synthetic-2019；Author BT (2023)〈Participation bias in location-sharing studies〉，DOI:10.5555/synthetic-2020；Author BU et al. (2024)〈Dwell-time segmentation for park visit detection〉，DOI:10.5555/synthetic-2021
- **狀態**：活躍｜`gps trajectory green space exposure dwell time` 在 Semantic Scholar 回傳 143 筆，其中 2023 之後 71 筆
- **結構上做不到**：它記錄的是裝置的位置，本身不帶持有者在該位置做了什麼；要講活動內容或強度，得再接加速規或自陳。
- **默默預設**：F5-a〈帶著裝置的移動軌跡，等於這個人的活動〉；F5-b〈願意交出定位資料的人，和不願意的人在暴露量上沒有系統差異〉
- **進入成本**：資料授權、研究倫理審查與一套軌跡處理流程，前置知識是時空資料處理；一個人約六至八週，行政等待占一半。

### F6 定點人流計數

- **一句話**：在公園出入口或步道設紅外線或影像計數器，逐時記錄通過人次。
- **買到什麼**：連續、不倚賴受訪者記憶的使用量，可以看出時段分布與改造前後的變化。
- **付出什麼**：只數得到人次、數不出是誰，無法連到個人特徵或健康結果；設備需要供電與維護，遮蔽與並排通過會低估。
- **錨定文獻**：Author BV et al. (2021)〈Automated pedestrian counters in park evaluation〉，DOI:10.5555/synthetic-2022；Author BW et al. (2023)〈Undercounting in infrared trail counters〉，DOI:10.5555/synthetic-2023；Author BX et al. (2024)〈Continuous footfall data for park renovation assessment〉，DOI:10.5555/synthetic-2024
- **狀態**：新興｜`pedestrian counter park footfall continuous` 在 Semantic Scholar 回傳 38 筆，其中 2023 之後 27 筆
- **結構上做不到**：它的輸出是通過事件的計數，本身不帶身分，同一個人來回會被記兩次；要講人數或個人劑量，得另外做一次校正調查。
- **默默預設**：F6-a〈通過出入口的人次，可以代表這段期間的使用強度〉
- **進入成本**：設備採購與場地許可，前置知識是時間序列處理；一個人約二至三週，場地許可是主要瓶頸。

### F7 現地稽核量表

- **一句話**：由訓練過的稽核員到現場，用結構化量表逐項評設施、維護與活動支持度。
- **買到什麼**：拿到只有到現場才看得到的細節：鋪面狀況、遮蔭、座椅、照明、維護程度。
- **付出什麼**：還沒查到
- **錨定文獻**：Author BY et al. (2016)〈Direct observation instruments for park environments〉，DOI:10.5555/synthetic-2025；Author BZ (2018)〈Inter-rater reliability of environmental audit tools〉，DOI:10.5555/synthetic-2026
- **狀態**：〔涵蓋不足〕
- **結構上做不到**：它的輸出是稽核當下的現地狀態，本身不帶使用者在場的資訊；要講誰在用，得另外收行為觀察。
- **默默預設**：F7-a〈訓練過的稽核員在不同場域給出的分數可以互相比較〉
- **進入成本**：稽核員訓練與現地行程安排，前置知識是量表操作與信度檢定；兩人約三週可完成一個行政區。

## 三、實際上怎麼疊

實務上很少單用一個家族。三種常見的疊法：

1. **F1 ＋ F2**：先用遙測算出全市的綠量，再用圖資把「進得去的綠」切出來。前者給覆蓋、後者給可及性，成本仍然接近零，代價是兩層都不知道誰真的去了。這是政策報告最常見的組合。
2. **F5 ＋ F4**：用軌跡量到訪、用問卷補動機與感受。軌跡負責「去了沒」，問卷負責「為什麼去」，兩邊的樣本必須是同一批人，成本落在資料授權與倫理審查，通常比方法本身貴。
3. **F6 ＋ F7**：計數器給連續的使用量、現地稽核給環境條件，兩者在同一個公園對接，適合改造前後的評估。成本落在設備維護與稽核員行程，而且兩種資料的時間解析度差很多，對接時要先講清楚要比較的是哪一段期間。

## 四、能量在哪裡

- `street view imagery eye-level greenness` 在 Semantic Scholar 回傳 187 筆，其中 2023 之後 96 筆——超過一半集中在近三年。
- `gps trajectory green space exposure dwell time` 在 Semantic Scholar 回傳 143 筆，其中 2023 之後 71 筆。
- `pedestrian counter park footfall continuous` 在 Semantic Scholar 回傳 38 筆，其中 2023 之後 27 筆；總量小，但近三年占比是本次盤點裡最高的。
- `satellite vegetation index greenness exposure` 在 Semantic Scholar 回傳 318 筆，其中 2023 之後 41 筆；總量最大，近三年占比最低，回顧文獻多半把它當成基準線而不是研究對象。
- 〔印象，未驗證〕三種較新的家族（F3、F5、F6）都在往「量到個人實際在場」這個方向走，而較舊的兩種（F1、F2）量的是地點的屬性。這一句是讀完摘要之後的印象，本次沒有為它跑過對應的檢索。

## 五、檢索紀錄

| # | 家族 | 查詢詞（逐字） | 回傳筆數 | 前三筆標題（逐字，來自工具回傳） |
|---|---|---|---|---|
| 1 | （家族清單） | `green space exposure assessment review` | 46 | A review of greenness exposure assessment methods / Measuring exposure to urban nature: a methodological review / Green space and health: exposure metrics revisited |
| 2 | （家族清單） | `green space exposure measurement survey` | 31 | Surveying measurement approaches for urban green exposure / From satellites to surveys: a methodological survey / Exposure science for urban nature |
| 3 | （家族清單） | `green space exposure taxonomy` | 12 | A taxonomy of green space exposure metrics / Classifying environmental exposure measures / Toward a shared vocabulary for greenness exposure |
| 4 | F1 | `satellite vegetation index greenness exposure` | 318 | Satellite-derived vegetation indices as exposure metrics in health research / Buffer size sensitivity in residential greenness studies / Seasonal variation in vegetation index exposure estimates |
| 5 | F2 | `park accessibility buffer network analysis` | 264 | Accessibility measures of urban parks: a comparison / Network distance versus Euclidean buffers in park accessibility / Service area analysis for neighbourhood open space |
| 6 | F3 | `street view imagery eye-level greenness` | 187 | Street view imagery for eye-level greenness assessment / Human versus automated scoring of streetscape quality / Eye-level and overhead greenness give different exposure estimates |
| 7 | F4 | `self-reported park visitation questionnaire validity` | 221 | Self-reported park visitation: validity against objective measures / Recall bias in leisure activity questionnaires / Questionnaire design effects on reported outdoor time |
| 8 | F5 | `gps trajectory green space exposure dwell time` | 143 | GPS-based measurement of green space exposure / Dwell-time segmentation for park visit detection / Positional error in urban canyons and activity space delineation |
| 9 | F6 | `pedestrian counter park footfall continuous` | 38 | Automated pedestrian counters in park evaluation / Continuous footfall data for park renovation assessment / Undercounting in infrared trail counters |
| 10 | W2 | `measurement invariance environmental exposure subgroup` | 57 | Differential misclassification of greenness exposure across age groups / Measurement invariance in environmental audit instruments / Subgroup differences in exposure measurement error |

## 六、這個領域的牆（默默預設總表）

| 牆 | 這條預設 | 來源預設 | 家族數 | 性質 | 拆的可能性 |
|---|---|---|---|---|---|
| W1 | 暴露可以用一個「人不在場也量得到」的空間代理量代替 | F1-a、F2-a、F3-a | 3 | 歷史偶然 | 拆掉之後，暴露必須量到人真的在場，成本從一次全市計算變成逐人收資料；不方便的是政策端，因為代理量正是它可以對全市發布的那個數字 |
| W2 | 量測工具對所有族群一視同仁，不需要先檢驗差異 | F3-b、F5-b、F7-a | 3 | 已經有人在拆 | Author BF et al. (2024)〈Differential misclassification of greenness exposure across age groups〉，DOI:10.5555/synthetic-2027 |
| W3 | 量測到的那個時點或那一段，可以代表更長的期間 | F1-b、F6-a | 2 | 真的必要 | 這兩個家族的資料本身就是離散取樣，取消取樣點等於取消這個家族；能改的是取樣密度與如何標示不確定性，不是這條預設本身 |
| W4 | 個人層次的暴露，可以由這個人自己的紀錄或回憶還原 | F4-a、F5-a | 2 | 歷史偶然 | 拆掉之後要改用不倚賴當事人的來源（定點計數、現地觀察），代價是失去個人層次的連結；不方便的是需要把暴露接到個人健康結果的研究 |
