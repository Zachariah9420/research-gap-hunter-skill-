# Evals

Six scripts live here: the report checker (`format_check.py`), two test suites over it (`self_test.py`, `mutation_test.py`), the fixture generator those suites depend on (`make_fixtures.py`), the docs-versus-repo scanner (`doc_scan.py`) and the package scanner (`zip_check.py`). No network, no API keys, seconds to run.
Run both suites **and `doc_scan.py`** before shipping any change to `format_check.py`, to the output-format block in `SKILL.md`, or to either README — the suites catch a broken checker, `doc_scan.py` catches a README that still describes the previous one.

```bash
python evals/self_test.py                            # every fixture must land on its expected check id
python evals/mutation_test.py                        # proves each rule is what catches its fixture
python evals/mutation_test.py -v                     # also lists which rule backstops which
python evals/make_fixtures.py                        # regenerate the derived fixtures from their baselines
python evals/make_fixtures.py --check                # verify the fixtures on disk match the generator
python evals/doc_scan.py                             # docs vs repo: counts, paths, commands, links
python evals/format_check.py <report.md>             # check a real report
python evals/format_check.py <report.md> --json      # machine-readable findings
python evals/zip_check.py research-gap-hunter.zip    # before sharing a package
```

Exit codes: `0` clean, `1` violations found, `2` usage or read error. `2` is deliberately distinct from `1` — a missing file is not a clean report.

**Every count in this directory is derived, never written down.** `self_test.py` prints `check 覆蓋率：N / M` from `len(CHECK_DESCRIPTIONS)` against the ids its fixtures pin; `mutation_test.py` prints the same denominator and fails if any declared check has no mutant. An earlier version of this file carried a hand-counted number in prose and it was wrong — in the direction that flattered the repo. Read the numbers off a run, not off this page. The top-level READMEs *do* have to write some counts down, since they are read by people who will never run anything; `doc_scan.py` is what keeps those honest.

## What this can and cannot do

This skill has no runtime engine. It is prose that instructs a model, and the model's output is the product. So the only thing that can be automated here is **whether the report obeys its own format** — never whether the report is true.

`format_check.py` catches: a `DONE` with no paper named, a survivor whose search-evidence field says 「同上」, a header claiming three survivors when two are present, an assumption presented as quantified without the sample frame behind it, a candidate that was generated and then silently vanished, the sentence 「沒有人做過」 — and, in a landscape report, a technique family described with no cost, a family called 飽和 with no search behind the word, a wall whose contributing assumptions do not exist, and the word `CROWDED` appearing in a document that never paid for a verdict.

It also catches **the lines it cannot read**: a table row that never made it into the table, a row whose column count does not match its header, a candidate or family heading it does not recognise, an assumption line in a shape the pattern rejects. That is a separate promise from the ones above and the one this directory took longest to make good on — see 〈The parser is tolerant about form and never silent〉.

It does **not** catch, and cannot: whether the named paper exists, whether its abstract really says what the report quotes, whether the paper was retracted, whether any query was ever actually run, whether `N`/`M′`/`M`/`K′`/`K` are the real numbers or plausible-looking inventions. A report can be entirely fabricated and pass every check in this directory with a green tick. Existence, retraction and bibliographic correctness are lit-review's job — `verify`, `retract`, `check` — and section 七 of the report format exists precisely so the user can paste the DOI list straight into them.

**Form is checkable, truth is not. Do not let a green run be read as a verified report.**

### Parts of SKILL.md that are deliberately *not* mechanised

Stated here so nobody mistakes the checker's silence for approval:

- the 覆蓋率警告 header line required at tiers 2/3, and the tier strings themselves — the checker only verifies that 文獻工具 is declared and is not a placeholder, not that the wording matches the tier actually used;
- 偵察模式's invariants (1 candidate, 2 searches, only 〔DONE?〕/〔待再查〕) — a recon-mode report is checked as an ordinary report;
- the 第1步-共識 / 第1步-推翻A\<k\> rows in section 六 — `TRACE-01` covers candidates, not the step-1 searches behind section 一. This is also *how* `SKILL.md`'s exemption for an inherited-unframed assumption holds: it is never in the interlock's target list to begin with, so nothing ever asks a report to log a search it did not run. `self_test.py` pins that rather than asserting it in prose — see 〈fixtures/〉 below;
- the 〈地形來源〉 header line a report must add when it inherits, and the `W<k>` id inside a 〔承接自地形 …〕 label — the checker reads the label to classify the line, not to verify that the wall it names exists in some other file it cannot see;
- whether the `pick` indices listed in an assumption actually number M′, whether a CROWDED's three papers really map to three distinct sub-questions, whether a DONE's four-way match holds;
- everything in sections 五 and 七.

And in a landscape report, everything in 〈三、實際上怎麼疊〉 and 〈四、能量在哪裡〉; whether a family really has 3–6 anchors or whether those anchors carry identifiers; whether 〈性質〉 is one of its three allowed values and whether 已經有人在拆 names the work; whether the wall table is ordered by 家族數 descending; whether a 〔涵蓋不足〕 was an honest retreat or a family nobody bothered to search. See 〈Why the landscape rule set is thin〉 below for why that list is long on purpose.

## format_check.py

The checks below are the parts of `SKILL.md` that survive being reduced to a mechanical rule. Each one exists because a plausible-looking report can satisfy the format while quietly skipping the work.

**Two report types, two rule sets.** `SKILL.md` now specifies two outputs: the gap report (`# 研究缺口報告：…`) and the landscape report (`# 領域地形報告：…`). They are different documents, not variants — the landscape report has no candidates, no verdicts and no eliminations, so nineteen of the rules below have nothing to attach to in it, and applying them anyway would produce a page of category errors. `format_check.py` reads the type off the first `# ` heading, falling back to the header 〈模式〉 line, and dispatches to the matching rule set (`Checker` or `LandscapeChecker`). Neither is ever judged by the other's rules. Anything it cannot identify is treated as a gap report, because that was the only type this checker had before landscape existed and a new mode must not silently un-check the old one. The `--json` output names the type in `mode`, so a wrapper never has to guess.

The **mode** column says which rule set a check belongs to: `hunt`, `landscape`, or `both`.

| id | mode | Check | Why |
|---|---|---|---|
| `PARSE-01` | both | Anything that looks like part of the report's structure but cannot be read is reported: a table row that never entered the table (blockquoted, full-width `｜`, **missing its leading `\|`**, or stranded after a non-table line broke the run), a row whose cell count differs from its header, a candidate heading or a landscape family heading the pattern does not recognise, and **a whole table that cannot be found where one belongs** | Every other rule in this table judges what the report *says*. This one reports what the checker **could not read**, and it exists because the alternative is worse than a miss: an unread row is checked by nothing, and the counting rules then render it as arithmetic — `RECON-01` says 「結算寫已淘汰 6，第四節實際有 5 列」 when the 6 is correct and a row's *shape* is what broke. That message sends the author to change the right number. A separate id is how the author gets sent to the line instead |
| `SECT-01` | both | A `## ` section whose contents identify it (its table header, the blocks under it, or the assumption lines in it) but whose **heading text does not** — `SKILL.md`〈輸出格式〉 line 70: 「區段標題與欄位標籤不得改寫」 | This is the rule that had to exist before any of the location fixes were safe to make. A rewritten heading is a form violation in its own right, and until this round it was instead a **silencer**: `## 一、一眼表` → `## 一、總覽表` deleted every glance row, and `LSTAT-01`/`LCOST-01` went dark for every one of them with no finding at all. The finding now lands on the one line that is wrong, and everything underneath is still checked — the heading never decides whether something gets parsed |
| `STRUCT-01` | hunt | 〈存活候選〉〈待確認〉〈已淘汰〉〈檢索紀錄〉 sections all present | A report missing 檢索紀錄 has no audit trail; one missing 待確認 has nowhere to put an undecided candidate, so it drops it |
| `STRUCT-02` | both | Header declares 文獻工具 tier | Tier 2 wording must never be read as tier 0 |
| `COUNT-01` | hunt | Declared survivor count == number of `### 候選 N` blocks | The cheapest way to look thorough is to claim candidates that were never written |
| `COUNT-02` | hunt | Generated count ≥ survivor count | Arithmetic sanity |
| `RECON-01` | hunt | 候選結算 reconciles: 生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q, each count matches the section it names, and every `C<nn>` appears in exactly one of 二/三/四 | Silent disappearance is the failure mode the 待確認 section was added to prevent; without an arithmetic interlock the section just moves the hiding place |
| `VERDICT-01` | hunt | Each section's verdict/state value is in that section's vocabulary (二: ADJACENT/OPEN/INCREMENTAL, 三: the pending states, 四: DONE/CROWDED only), **and is not blank** | Invented verdicts smuggle in unstated criteria; a pending state in the kill table is an elimination that was never earned. Blank counts as outside the vocabulary because of what blank used to buy: `check_kills` skips a row with no verdict, so `KILL-01`/`KILL-02`/`KILL-03`/`ID-01` all lost their subject and an elimination with an empty 判定 cell passed unread |
| `VERDICT-02` | hunt | Survivors are only ADJACENT / OPEN / INCREMENTAL | A DONE in the survivor list is a contradiction |
| `ASSUM-01` | hunt | An assumption line is written in a shape the parser can read, **and** a quantified one carries the whole sample frame — 標題層掃描 N／檢索詞／limit／摘要層精讀 M′／pick 索引／其中 M 篇沿用／推翻性檢索／回傳 K′／讀後 K／樣本來源 — with M ≤ M′, K ≤ K′, M′ ≥ 3; anything less must be written 〔印象，未驗證〕. **Exempt: an assumption labelled 〔承接自地形 W\<k\>〕 without 已補取樣框** — a landscape report by definition never ran N／M′／M／K′／K, so demanding a frame from it demands a set of numbers nobody produced. Add 已補取樣框 to the label and it is held to the full frame like any other | The assumption list is the most hallucinable artifact in the skill: it is written before any candidate exists and everything downstream inherits it. A bare 「檢視 20 篇」 cannot be audited; the split frame can. The inherited exemption is the same principle pointed the other way — a checker that demands evidence of work that was never supposed to happen this round teaches the model to invent it |
| `ASSUM-02` | hunt | A G3 candidate names the assumption it inverts, and that assumption is neither 〔印象，未驗證〕 **nor an inherited wall whose sampling frame has not been paid** | G3 turns an assumption into a research topic. If the assumption was an impression, the whole candidate is an impression wearing evidence — and an unframed inherited wall carries exactly the same force, since landscape's evidence bar is deliberately one notch lower. The two are reported separately on purpose: an inherited assumption *is* in section 一, so telling its author it does not exist sends them looking for a missing line instead of paying for the one frame that would make the candidate legal |
| `EVID-01` | hunt | Every survivor has a search-evidence field | — |
| `EVID-02` | hunt | That field is not empty or a placeholder (`同上`, `略`, `TBD`, `…`) | — |
| `EVID-03` | hunt | That field contains at least one concrete query string | Queries must be copy-pasteable so the user can re-run them |
| `NEIGH-01` | hunt | 最接近的既有研究 present; if it names a paper it carries an identifier | Without a DOI the user cannot check the claim |
| `KILL-01` | hunt | Every eliminated row names key literature | 每一個淘汰都必須指名殺死它的那篇文獻。There is no exemption any more: a row that cannot name literature is not an elimination, it belongs in 待確認 |
| `KILL-02` | hunt | `CROWDED` names ≥3 papers | `CROWDED` is otherwise the cheapest verdict in the skill and becomes an escape hatch |
| `KILL-03` | hunt | `DONE` carries a verbatim quoted sentence in its reason | A false DONE deletes a viable topic silently and permanently |
| `ID-01` | hunt | Named key literature carries a DOI / arXiv id / S2 corpus id | Makes the `retract` and `verify` handoff mechanically possible |
| `TRACE-01` | hunt | Every candidate in 二/三/四 has a row in 〈檢索紀錄〉 — **except** a 三 row whose state is 〔未驗證〕, or 〔UNSEARCHABLE〕 blocked on terminology | The one guard against a report produced with zero searches — and a kill with no logged search is worse than a survivor with none. The exemption exists because those rows are in 待確認 *precisely because nobody searched them*: demanding a log row from them would make the honest report non-conformant and the cheapest way to go green would be to invent a search that never ran. See `SKILL.md`〈互鎖的例外〉 |
| `TRACE-02` | hunt | 〈檢索紀錄〉 query cells are concrete, not placeholders | Same reason |
| `LANG-01` | both | No assertive non-existence wording anywhere | 「我沒搜到」 is a result; 「不存在」 is a claim |
| `TIER-01` | hunt | If the header declares no search was run, no verdict and no elimination may appear | — |
| `LHEAD-01` | landscape | Header declares 〈模式〉 as 領域地形 **and** carries 〈這份報告不做什麼〉 verbatim | A tidy landscape map reads like a novelty conclusion. The disclaimer is the one line that stops that reading, and it is a fixed string precisely so it cannot be softened into 「本報告主要著重於…」 |
| `LVOCAB-01` | landscape | No novelty-verdict token (`ADJACENT`／`OPEN`／`INCREMENTAL`／`DONE`／`CROWDED`) anywhere in the document | **The mode-confusion guard, and the most important of the five.** The failure this mode invites is drifting into verdicts it never paid for: the hunt makes you name a paper and quote its abstract before you may write `DONE`, and a landscape report that writes it has skipped all of that while inheriting the word's authority |
| `LCOST-01` | landscape | Every family carries both 〈買到什麼〉 and 〈付出什麼〉, neither empty nor a placeholder | A family with no stated cost has been described dishonestly — if a method really had no cost it would have cleared the field years ago. One-sided description is the most likely way this mode misleads, and 「還沒查到」 is an accepted value, so the honest answer is always available |
| `LSTAT-01` | landscape | 〈狀態〉 is one of 飽和／活躍／新興／衰退／〔涵蓋不足〕 and is not blank, and anything but 〔涵蓋不足〕 carries the search clause (`回傳 X 筆` plus a verbatim query) in the same field | 「哪些飽和、哪些還在動」 is the question this mode exists to answer, so it is also the sentence most worth faking. Requiring the search inline makes 〔涵蓋不足〕 the cheap answer and 飽和 the paid one — the gradient has to point that way or the mode fills up with confident adjectives |
| `LWALL-01` | landscape | §六 and §二 reconcile both ways: every `F<n>-<字母>` in §二 lands in exactly one wall, every id in 〈來源預設〉 exists in §二, and 〈家族數〉 equals the deduplicated family count | This section is the deliverable — it is what 第 1 步 of the hunt inherits. An assumption written in §二 and missing from §六 is dropped in transit; a wall citing ids that do not exist was imagined rather than pooled. Same defect class as `RECON-01`, same reason for an arithmetic interlock |

`LANG-01` carries a suppression guard: a line containing `≠`, `不代表`, `不得寫`, `並非`, `錯誤示範` and similar is read as *discussing* the forbidden phrase rather than asserting it, so a report may quote the rule it is obeying. The guard is deliberately narrow — see 〈Narrative documents〉 below for why quoting alone is not enough to earn an exemption.

Every finding prints its check id, line number, message and the offending line, and `--json` emits the same fields plus the parse summary (`mode`, `candidate_sections`, `pending_rows`, `kill_rows`, `trace_rows`, `settlement`, `assumptions`, `unreadable`, `renamed_sections`, `families`, `glance_rows`, `wall_rows`, `report_blocks`) so a wrapper can tell "clean" from "parsed nothing". `unreadable` is the count behind `PARSE-01` plus the unreadable assumption lines: a wrapper that wants one number for "did this file actually get read" reads that one. `renamed_sections` is a different thing and is deliberately not folded into it — those lines *were* read, the heading naming them is what is wrong. Line numbers are always ≥ 1: a whole-file defect anchors at line 1 rather than line 0, because a consumer cannot jump to line 0.

### Nothing that carries checks is located by the text of a section heading

This is the load-bearing sentence of the parser, and it is stated first because the previous round wrote it down — inside `parse_landscape`'s docstring, 「家族靠 `### F<n>` 認，不靠它落在哪一節——節名一旦被改寫，整份報告就會變成『沒有家族因此沒有違規』，那是最壞的一種綠燈」 — and then applied it to two parsers out of six. The glance table and the assumption lines were still found by their `## ` heading, and an adversary got a clean exit 0 out of a broken report by renaming one heading. Writing a principle in a docstring and applying it to the instance in front of you is how a repo ships a false green twice.

So, uniformly: **a table is identified by its header columns, a candidate or family block by the field lines it owns, an assumption line by its own line shape.** Section headings name sections; they never gate parsing. Concretely:

| Structure | Located by | Not by |
|---|---|---|
| landscape glance table | a header carrying 〈家族〉 **and** 〈狀態〉 **and** 買到/付出 | the word 一眼 in the `## ` heading |
| landscape wall table | a header carrying 〈牆〉 and 〈來源預設〉 (checked first — 〈家族數〉 contains 家族) | the word 牆 in the heading |
| kill / pending / trace tables | 〈判定〉+〈關鍵文獻〉 / 〈暫定狀態〉+〈還缺〉 / 〈查詢詞〉+〈回傳筆數〉 | the words 淘汰 / 待確認 / 檢索紀錄 |
| family block | ≥2 of 〈默默預設〉〈狀態〉〈買到什麼〉〈付出什麼〉 in the lines it owns | `### F<n>` alone, or sitting inside a 家族 section |
| candidate block | ≥2 of 〈缺口類型〉〈新穎性判定〉〈搜尋證據〉〈最接近的既有研究〉 | the word 候選 in the heading |
| assumption line | `ASSUM_LINE_RE` matching the line, scanned across **the whole document** | being inside a 共識 section — there is no section gate left at all |

The heading pattern itself is `HEADISH_RE`, which matches `###F1 …` with no space after the hashes. CommonMark does not call that a heading and neither did `HEAD_RE`, which meant the family under it was not merely unparsed but **invisible**: no block, and no line saying a block could not be read. It is now scanned, registered from its contents, and reported.

Three consequences fall out, and all three are the point:

- **A renamed heading produces `SECT-01` and nothing else changes.** Every rule underneath still runs against the same rows. The finding names the line that is actually wrong.
- **Which keyword `classify_section` looks for is now cosmetic.** It supplies a fallback name for a section whose shape says nothing (〈五、下一步〉, 〈七、可查證清單〉) and the "what it would have been called" half of the `SECT-01` message. It cannot make a row disappear.
- **The one remaining use of a heading is additive only.** If a section is *named* as a table section and contains no table header at all, that is `PARSE-01` — the shape-based path cannot see a table that was pasted back from a rendered view, because such a paste has no `|` anywhere, not even in the header. A heading may add a finding; it may never subtract one. For the landscape glance table — the only structure in either report type that nothing else counts — there is a second, shape-only arm: if **no** section anywhere in the document yields a glance table, that is reported regardless of what any heading says. That arm is what covers a heading rename and a de-piped table happening together.

#### What is still located by a string, and why that is correct

Three places name something by its text rather than finding it by shape. Each is listed with the reason, so the next sweep does not have to rediscover the argument — and so that a reason going stale is visible rather than assumed.

- **The report type** (`# 領域地形報告：` / `# 研究缺口報告：`, with the header 〈模式〉 line as a fallback). `SKILL.md` designates the first line as the type discriminator, so this is the spec, not a shortcut. More importantly it **cannot fail silently in either direction**: a landscape report read as a gap report collects `STRUCT-01` four times plus `COUNT-01` and `RECON-01`; a gap report read as a landscape one collects `LHEAD-01` twice. Both are a page of category errors, which is loud and obviously wrong — the opposite of the failure mode this section exists to prevent. A shape-based type detector would be strictly more code for a case that already screams.
- **Header field labels** — 文獻工具, 候選結算, 這份報告不做什麼, 降級聲明. These are located by their own text, document-wide, not by which section they sit in, and each *is* the subject of the rule that reads it (`STRUCT-02`, `RECON-01`, `LHEAD-01`, `TIER-01`). A missing or renamed label is exactly what those rules report. There is no rule underneath them to switch off.
- **A section named as a table section that contains no table.** Additive only, as above: it can produce a finding, never suppress one.

And one place a heading rename genuinely goes unreported: **a section that carries no checks** — 〈三、實際上怎麼疊〉, 〈四、能量在哪裡〉, 〈五、下一步〉, 〈七、可查證清單〉, and the landscape 〈五、檢索紀錄〉 whose table this file does not parse at all. `SKILL.md` forbids renaming those too, but the checker cannot tell a renamed section from an extra one when nothing in it identifies it, and guessing would mean flagging any section it does not recognise. The rule it holds instead is narrower and true: **if the checker can tell what a section is, its heading has to say so.**

### The parser is tolerant about form and never silent

Two halves, and the second is the one that took three rounds of bugs to learn.

**Tolerant about form.** `SKILL.md` is prose and its wording will drift. Labels are matched through an alias table (`搜尋證據` / `檢索證據` / `證據`; `最接近的既有研究` / `最近鄰文獻`), table columns are matched by keyword rather than position, both half- and full-width colons are accepted, `→` / `->` / `至` all parse in the count line, `＝`/`=` and `＋`/`+` both parse in the settlement line, and the `（C03）` id in a candidate heading may be omitted (older reports still parse, they just fail `RECON-01`). Line-level structure accepts a leading `> ` (blockquote), an ordered-list marker as well as `-`/`*`/`+`, bold anywhere the emphasis would naturally fall, and — for candidate and family headings — `###` or `####`, matched after `strip_md`, so `### **候選 1（C01）**：…` reads. Three of those prefixes exist for one reason: **`SKILL.md` displays its own formats inside blockquotes** (第 1 步 shows the assumption line as `> 預設 A1…`, twice), and a reader copies the shape they can see. A checker that rejects the shape its own specification renders is not strict, it is wrong.

**Never silent.** Tolerance has an end, and what happens at the end is the whole question. Until this round, everything past the end of the pattern was *dropped*: the line vanished, the counts moved underneath the rules that depend on them, and the run went green. That is the worst behaviour available to a checker. A false red costs somebody five minutes; a false green reports success on a report it did not read, and it teaches the author that a green run means something. So the line now held is: any line that **looks like** part of the structure and does not parse produces a finding naming the canonical form — `ASSUM-01` for an assumption line, `PARSE-01` for a row or a structural heading. Where a drop is still tolerated, it is listed in 〈What a malformed line does〉 below with the reason, not left for the next person to rediscover.

**And when the two halves trade off, the false red wins.** That sentence is here because the principle was applied backwards once and it cost a round: round 3 narrowed the look-alike detector so ordinary prose would stop being flagged, and the same narrowing made an em-dash-separated assumption line invisible to *both* patterns. One false red removed, one false green restored. The direction is not symmetric and should not be traded as if it were — a false red costs a reader five minutes of confusion; a false green is the checker saying "pass" about a document it did not read. So the look-alike pattern now carries no lookahead at all, [`assumption_prose_mention.md`](fixtures/assumption_prose_mention.md) is a fixture that must come back **red**, and the comment above `ASSUM_LOOKALIKE_RE` says why, so that the next person to notice the false red does not quietly fix it. Where this is *still* traded the wrong way and knowingly, the cases are enumerated in 〈Known reachable false greens〉 below.

**The assumption line carries optional bracketed provenance labels between its id and its delimiter** — `預設 A1〔承接自地形 W3，支撐家族 F1、F4〕：…` — because that is the form `SKILL.md` 第 1 步（甲） gives for a wall inherited from a landscape report, and inheritance is the single interface between the two modes. There may be **more than one** bracket (`〔承接自地形 W2〕〔已補取樣框〕：…` is the natural way to write a frame that was paid later), the brackets may be 〔〕/【】/［］/（）, and the delimiter may be `：`, `:` or `｜` — the last because 第 1 步 spells the paid-frame rewrite as `預設 A1〔承接自地形 W3，已補取樣框〕｜標題層掃描 …`, with no colon at all. The label decides which rule set the line falls under: 承接自地形 without 已補取樣框 is exempt from `ASSUM-01` and barred from G3 by `ASSUM-02`; 承接自地形…已補取樣框 is treated exactly like a locally quantified assumption on both counts. Reading only the first bracket is not a smaller version of the same bug, it is a different one: it silently downgrades a framed inheritance to an unframed one and tells the author to pay a cost they already paid. The label is classified off the **label**, never off the body: `SKILL.md`'s own template ends such a line with 「效力同〔印象，未驗證〕」, and reading that as the line's provenance would collapse an inherited wall into an ordinary impression and lose the fact that another report produced it. Nothing rewrites the label, and no message ever tells a report to replace it with 〔印象，未驗證〕 — same force, different provenance, and the reader has to be able to see which.

When an assumption line cannot be read, `ASSUM-02` stays quiet about any G3 candidate pointing at it. `ASSUM-01` has already said 「這一行看起來是一條預設，卻不是讀得出來的形式」 at that line; adding 「G3 候選指到第一節沒有的預設 A2」 on top would be the same misleading sentence this round exists to delete — the line *is* in section 一, and the checker knows it is, because that is what it just reported.

### What a malformed line does — the sweep

`ASSUM_LINE_RE` was never special. It was the one somebody happened to test, and it failed twice in the same way, so every other parser was put through the same question: *if this line or row is malformed — wrong bullet, blockquoted, extra brackets, full-width punctuation, bold in an unexpected place, a table row with the wrong column count — does it produce a finding, or does it vanish?* The table is the answer, kept here so the next person does not redo it.

**Two rows of it were wrong when they were written, and an adversary proved it with one-character edits.** They are marked ✗→✓ below. The 「closed」 claim for glance rows and for pending/kill/trace rows covered exactly the three deformations somebody had thought of — blockquote, full-width bar, stranded after a break — and missed the cheapest one of all: **delete the leading `|`**. `parse_table` only consumes lines that `startswith("|")`, and `ROWISH_RE`, the detector that was supposed to catch what `parse_table` refused, is anchored at the start of the line too. So the row was neither consumed nor reported, and if it was the *first* data row the table did not even break, so nothing downstream registered a count change. That is the shape of every false green in this file: the detector and the parser share an assumption, so the detector cannot see what the parser drops.

The lesson recorded, since a table of closed cases is exactly the artifact that invites the next false green: **a row of this table is a claim about a parser, and it is worth what the fixture behind it is worth.** Every ✓ below is now pinned by a fixture, and each fixture is a single-character or single-line edit to a baseline, because that is the size of edit that produced all three of this round's false greens.

| Parser | Malformed how | Before | Now |
|---|---|---|---|
| assumption line | blockquoted `> 預設 A1…`; two adjacent brackets; no bullet; ordered-list marker; `｜` instead of `：`; 【】/（） brackets | dropped, silent (or `ASSUM-02`「指到第一節沒有的預設」, pointing at a line that is there) | all parse |
| assumption line ✗→✓ | full-width ［］ brackets, which `evals/README.md` promised and `ASSUM_LINE_RE` did not contain (it had half-width `\[`, U+005B, not ［, U+FF3B) | **false red** on a form this page guarantees; `doc_scan.py` cannot see it, because it never compares a doc claim against the contents of a character class | parses; the four pairs live in one `BRA_OPEN`/`BRA_CLOSE` constant used by both patterns, so they cannot drift apart again |
| assumption line | **anything else** that starts with 預設 + an id, whatever follows it, including a table row `\| 預設 A1 \| …` | dropped, silent | `ASSUM-01`, naming the canonical form |
| assumption line ✗→✓→✗ | a separator outside the accepted class: `- 預設 A2——〈…〉` | round 3 added a lookahead requiring a structural character (`：` `:` `｜` `\|` `〈` or a label bracket) after the id, so that prose would stop being flagged. That lookahead made this line invisible to **both** patterns: assumptions 3→2, `unreadable` 0, exit 0, zero findings — the exact false green the look-alike rule exists to close, bought back by a fix aimed at a false red | the lookahead is gone. `ASSUM-01`, pinned by `assumption_em_dash_separator.md` and by a mutant that restores the lookahead verbatim |
| assumption line ✗→✓→✗ | prose that merely begins with 預設 + an id: `- 預設 A1 與 A2 都與量測方式有關` | round 2: **false red**. Round 3: green, via the lookahead in the row above | **false red again, on purpose.** The two directions trade off through the same lookahead, and when they trade off the false red is the one to take: it costs a reader five minutes, a false green is the checker saying "pass" about a document it did not read. Pinned by `assumption_prose_mention.md`, which is a *red* fixture with a parse read-back. To avoid it, do not open a sentence with 預設 + an id |
| assumption line | its section heading renamed, or deleted outright | dropped, silent: assumptions 2→0, `unreadable` 0, exit 0 — and a G3 candidate then drew 「G3 候選 C01 的輸入 A1 不在第一節」, the exact misleading sentence the previous round existed to delete | assumption lines are scanned across the whole document; the heading is not a gate. The rename itself is `SECT-01` |
| candidate block | bold heading; `####`; blockquoted heading | dropped → `COUNT-01`「宣告存活 3 個，實際只有 2 個」, whose cheapest fix deletes the candidate from the count | all parse |
| candidate block | heading unrecognisable otherwise (`候選三`, a renamed keyword) | as above | `PARSE-01`; the block is still registered from any `C<nn>` in the heading, so the counts stay honest and its fields are still checked |
| candidate block ✗→✓ | `### C01：<題目>`; `### C01 題目：…`; `###候選 1（C01）：…` (the last invisible to `HEAD_RE` entirely — no space after the hashes) | dropped → pure `COUNT-01`/`RECON-01` arithmetic, whose cheapest green fix deletes a real candidate from the settlement | `PARSE-01`; the block is registered from the field lines it owns (〈缺口類型〉〈新穎性判定〉〈搜尋證據〉), so the arithmetic never moves |
| candidate fields (verdict, evidence, nearest study, gap type) | blockquoted; label carrying a parenthetical or stray `*` | dropped → `EVID-01`/`NEIGH-01`/`VERDICT-01`「缺少…欄」 on a field that is present | all parse; those three messages now also name the required shape |
| pending / kill / trace rows | blockquoted row; full-width `｜`; a row stranded after a non-table line broke the run (this one drops **every following row**) | dropped → `RECON-01`/`TRACE-01` rendered it as a count mismatch | `PARSE-01` per row, plus the count finding, which the `PARSE-01` message explains |
| pending / kill / trace rows ✗→✓ | **leading `\|` deleted** — one character | not closed, and this row used to say it was. Neither consumed (`parse_table` wants `startswith("\|")`) nor reported (`ROWISH_RE` is anchored at the line start too). A trace row with a placeholder query lost `TRACE-02` outright; kill/pending rows surfaced only as `RECON-01` arithmetic, whose cheapest green fix decrements the settlement and deletes a real row from the reconciliation | `PARSE-01`, naming the missing leading bar: once the header is known, any unconsumed non-blank line in the section carrying ≥ `max(2, columns−1)` unescaped half-width `\|` is a stray. Half-width only — full-width `｜` is legal content in an assumption line and in a landscape 〈狀態〉 cell |
| pending / kill / trace rows | cell count ≠ header count | silent; values shift a column, and a shift that lands empty in a checked cell disables that check | `PARSE-01` |
| kill row / pending row | 判定 or 暫定狀態 cell blank (or the column missing from the header) | silent — and `check_kills` skipped the row, so `KILL-01`/`02`/`03`/`ID-01` had no subject | `VERDICT-01`, whose message names both causes |
| kill table | header row missing, so the first data row becomes the header | `RECON-01` count off by one | `VERDICT-01` per row (no 判定 column) + `RECON-01`; between them the header is where the author looks |
| landscape family block | `家族 F1：…` prefix; `####`; bold | dropped → `LWALL-01`「指到第二節沒有的預設」 pointing at §六 when §二's heading broke, and that family's cost and status went unchecked | all parse |
| landscape family block ✗→✓ | heading unrecognisable otherwise: `### 遙測綠覆指數` (no id), `### 一、遙測綠覆指數`, `###F1 …` (no space — invisible to `HEAD_RE`) | dropped → `LWALL-01` orphan messages pointing at §六 when §二's heading is what broke, and that family's cost and status went unchecked. The old salvage path existed but was gated on the block being *inside a 家族 section* — and that section is itself identified by its family blocks, so the gate was circular | `PARSE-01`; the family is registered from the field lines it owns, and its `F<n>` comes from the `F<n>-<字母>` ids in its 默默預設 field — which is where `LWALL-01` reads them anyway, so §六 stays correct |
| landscape glance / wall rows ✗→✓ | blockquoted, full-width, stranded, wrong cell count — **and the leading `\|` deleted**, which this row used to claim was closed and was not | silent for the glance table (nothing else counts those rows, so a first-row deletion did not even break the table); `LWALL-01` orphan messages for the wall table | `PARSE-01` for all of them |
| landscape glance row | 狀態 cell blank | silent, while a blank 買到/付出 in the same table raised `LCOST-01` | `LSTAT-01` |
| any section ✗→✓ | its `## ` heading rewritten (`一、一眼表` → `總覽表` / `家族一覽` / `快速對照` / `概覽`; `一、領域共識與未被質疑的預設` → `一、這個領域大家都同意什麼`) | **the worst case in this table**: everything under it stopped being parsed and nothing said so. Glance rows vanished and `LSTAT-01` + `LCOST-01` went dark for every row; assumptions went 2→0 and took `ASSUM-01`/`ASSUM-02` with them. `SKILL.md` line 70 forbids rewriting these headings, so the rename was itself an uncaught form violation | `SECT-01` on the heading; contents located by shape and checked exactly as before |
| a table section | pasted back from a rendered view — **no `\|` anywhere**, header included | silent: with no header there is no column count, so the missing-leading-bar detector has nothing to compare against, and no shape identifies the section | `PARSE-01`, from the section heading (the one additive use of a heading in the file), plus a document-level arm for the glance table specifically — see the four deliberate drops below |
| report type (`# 研究缺口報告` / `# 領域地形報告`) | H1 blockquoted | H1 missed; saved only by the 〈模式〉 line, and with both mangled a landscape report would be judged by hunt rules — a page of category errors | blockquote stripped before matching |

Four drops are deliberate and stay:

- **A row that was never written.** A family missing from the one-glance table, a candidate with no row anywhere: nothing was malformed, so there is nothing for a parse rule to report. Cross-checking the glance table against the family blocks would be a *content* rule in the shape of `LWALL-01`, and the landscape rule set is thin on purpose (below). The hunt side already has this interlock where it matters — `RECON-01` and `TRACE-01`. **A whole missing table is a different case and is reported**: the glance table is the only structure in either report type that nothing else counts, so a document with no glance table anywhere raises `PARSE-01` — that is existence, not reconciliation, and it costs no content rule.
- **Only the first table in a section is read.** A second table under the same `## ` heading is not a form `SKILL.md` offers, and its rows now surface as `PARSE-01` strays rather than disappearing, which is the honest outcome for a shape the spec does not define.
- **Prose inside a section.** A sentence that is not a field, a row or a heading is not reported. The parser cannot distinguish commentary from a mangled field without guessing, and a checker that flags every sentence trains people to ignore it.
- **A field line with no list marker at all** (`新穎性判定：ADJACENT` with nothing in front) is still read as a missing field rather than an unreadable one. It is reported — `VERDICT-01`/`EVID-01`/`NEIGH-01` fire, anchored on the right candidate block, and those messages now state the required shape. Making bare `X：Y` lines fields would turn every colon in a candidate block into a field-parsing gamble, and the finding is already in the right place.

The line to hold, in one sentence: **tolerant about form, never silent about something it could not read.**

#### What a false green would still take

The previous two rounds both ended believing they were done, so this list is part of the deliverable rather than an appendix. Each item is something a sweep actually found, or a boundary the design accepts on purpose.

The mechanical evidence behind the list: every line of all five hand-written baselines was deformed one at a time in eight ways — leading bar deleted, bar made full-width, line blockquoted, heading renamed, hashes de-spaced, heading bolded, list marker removed — and every result was checked for *counts dropping while the exit code stayed 0*. Zero combinations. That is a real sweep and it is also exactly the shape of sweep whose previous edition missed the one-character case, so read it as "the deformations we thought of", not as coverage.

- **Two independent breakages at once.** A de-piped table (no `|` anywhere, header included) under a heading that was *also* renamed defeats both location paths. For the glance table the document-level arm still catches it; for kill / pending / trace, `STRUCT-01` and `RECON-01` still fire, so it is loud — but their messages point at a missing section and at arithmetic, not at the table, which is the misleading-message failure this round set out to reduce rather than a false green. Nobody has produced a case where two simultaneous breakages are *silent*, and one was searched for.
- **Full-width `｜` used as a row separator with the leading bar also missing.** The stray detector counts half-width `|` only, deliberately: full-width `｜` is legal content inside an assumption line and inside a landscape 〈狀態〉 cell, so counting it would put false reds on correctly written lines. A row using full-width bars *with* a leading one is caught by `ROWISH_RE`; a row with neither is not.
- **Field labels.** `SKILL.md` line 70 forbids rewriting 欄位標籤 as well as section headings, and only the second half of that sentence now has a rule. A renamed *field* label is usually loud in a useful way — `EVID-01`/`VERDICT-01`/`LCOST-01` report the field as absent — but a renamed *column* label in a table is not: the column simply stops mapping, and whether that surfaces depends on which rule reads it. `SECT-01` has no column-label sibling. This is the most likely place the next false green lives.
- **The landscape 〈五、檢索紀錄〉 table is not parsed at all.** No `LTRACE` rule exists, so nothing in it can be malformed in a way this file would notice — including its rows losing their leading bars. That is a gap in the rule set, not in the parser, and it is downstream of the deliberate thinness argument above.
- **Everything content-level, unchanged.** A report can be internally consistent, perfectly shaped, fully parsed, and entirely fabricated. Nothing here touches that, and no amount of location work will.

### Why the landscape rule set is thin

Five rules, plus the four that are genuinely mode-independent — `LANG-01`, `STRUCT-02`, `PARSE-01` and `SECT-01`, each pinned in this mode by a fixture of its own, because "this rule also applies to landscape" is worth nothing as a sentence. That is not an unfinished rule set; it is the point of the mode.

Note what the four cross-mode rules are *about*: none of them judges the content of a landscape report. They say the checker could read it, and that it is shaped the way the spec says. Adding readability guarantees costs the mode nothing — a model cannot make a report cheaper to write by leaving a table unparseable — which is why the thinness argument below never applies to them.

The landscape mode exists because the hunt's evidence bars — a verbatim abstract quote and a four-way match for a `DONE`, three papers mapped to three sub-questions for a `CROWDED` — are too heavy for someone who only wants to know where he is. In a measured four-run trial, more than half of all candidates ended in 「待確認」: a defensible verdict, a useless orientation. **Putting a thick rule set on the cheap mode reproduces exactly that outcome**, because a checker is a cost, and the model pays it by leaving fields empty or hedged. So the rules here were chosen against one question — *what does a landscape report look like when it is following the format and already misleading you?* — and there are only a few answers:

1. it quietly starts issuing verdicts (`LVOCAB-01`);
2. it lists what each family buys and stays silent on what it costs (`LCOST-01`);
3. it calls a family 飽和 or 新興 as if that were a fact about the field rather than a count returned by a search (`LSTAT-01`);
4. its final table of walls does not correspond to the assumptions it actually wrote down (`LWALL-01`);
5. it never says out loud that it is not a novelty judgement, and gets read as one (`LHEAD-01`).

Everything else is left alone on purpose. Anchor counts, identifiers on anchors, the 〈性質〉 vocabulary, the ordering of the wall table, whether 〔涵蓋不足〕 was honest — all of them are real rules in `SKILL.md`, and none of them is the difference between a useful map and a misleading one. Checking them would buy accuracy on details while raising the price of the whole mode.

Two consequences worth stating plainly:

- **`LVOCAB-01` has no quotation guard**, unlike `LANG-01`. A landscape report has no reason to write `DONE` even to discuss it, and a mention/use exemption on the single most important check here would be the hole that swallows it. If a future landscape document genuinely needs to quote the vocabulary, it should use the `report-start`/`report-end` fence and keep the quoting prose outside.
- **`LANG-01` grants exactly one exemption in this mode**: the 〈這份報告不做什麼〉 header line, which is required to contain 「不宣稱任何做法沒有人做過」 and would otherwise be flagged on every conformant report. The exemption matches the whole field value against the fixed string, so appending anything to that line puts it straight back under the rule. A checker that cannot be satisfied by its own specification trains the model to ignore it — the same reasoning as the degraded no-search mode below.

**Arms, and what the mutants prove.** Several of these rules have multiple arms: `LSTAT-01` checks vocabulary, the search clause and the verbatim query; `LWALL-01` checks unknown ids, duplicate ids, the family count and orphaned assumptions; `LCOST-01` checks the family blocks and the one-glance table. `mutation_test.py` weakens the arm its fixture actually trips, exactly as `ASSUM-01` does — so a green mutation run proves each *rule* is load-bearing, not that every arm of it is. Do not read it as more than that.

That caveat is not decoration. **Every false green this repo has shipped was an unpinned arm of a rule whose mutant was green.** `PARSE-01` was proved by a wrong-cell-count fixture while the missing-leading-bar arm did not exist; `LSTAT-01` was proved by a family-block fixture while nothing established that its glance-table arm could still find the glance table. `PARSE-01` and `SECT-01` now carry one mutant per arm — read the count off a `mutation_test.py` run, not off this page — and that is the standard a *location* rule has to meet, because an arm of a location rule failing does not weaken one check, it switches off every check downstream of it.

## Known reachable false greens — the acceptance test for the restructure

**Read this section first if you are about to change the parser.** Everything below is a defect that reproduces against the working tree *today*, was deliberately left unfixed, and is written down so that it can be re-run rather than re-discovered. Each entry gives the exact edit and the observed output, because a list of vulnerabilities without repro steps decays into folklore within one round.

Why they are not fixed. The diagnosis this round arrived at is that parsing a prose report with regexes, under a requirement to be simultaneously **tolerant** (`SKILL.md` is prose, a model's wording drifts, and a checker that red-flags every variation gets ignored) and **never silent** (a dropped line is a false green, which is worse than a miss), is a contradiction: every patch *moves* the boundary between the two rather than removing it. The em-dash regression is the proof — round 3's lookahead, added to stop a false red, bought back exactly the false green the rule existed to close. Five more patches on this parser would buy five more boundary moves. The parser is being restructured instead, and each item below is meant to be re-run as an acceptance test afterwards: **if the restructure is real, every one of these becomes unreachable as a class, not fixed one at a time.**

None of them is exotic. Every one is a single inserted or edited line, and four of the five are reachable by honest mistake — a heading typed to break up a long table, an author's own comment, an IME emitting full-width punctuation, a number written in Chinese.

| # | The false green | The edit that produces it | Observed |
|---|---|---|---|
| FG-1 | **Split-table tail swallowed by an inserted heading.** Nothing counts the rows of the landscape one-glance table (stated as a deliberate drop above), so rows that fall out of it are unread and unreported | In `good_landscape.md`, insert one line — `## 一之二、（續）` — immediately before the `\| F5 …` row of the glance table | exit 0, zero findings. `F5`–`F7` are gone: they sit in a section with no table header, so no parser claims them and no stray detector sees them. It stays exit 0 when a swallowed row also carries a blank 〈付出什麼〉 and an asserted 〈狀態〉 — `LCOST-01` and `LSTAT-01` go from two red findings to silence |
| FG-2 | **Settlement / count decoy takes the first match, including inside an HTML comment.** `parse_report` scans for the first line matching 〈候選結算〉 or 〈生成 N → 存活 M〉 and breaks. Nothing requires that line to be in the header, or to be visible when the markdown is rendered | Prepend one line to a fixture that is currently red for exactly this arithmetic. To [`recon_mismatch.md`](fixtures/recon_mismatch.md): `<!-- **候選結算**：生成 12 ＝ 存活 3 ＋ 待確認 3 ＋ 已淘汰 6 -->`. To [`count_mismatch.md`](fixtures/count_mismatch.md): `<!-- 生成 12 個 → 存活 3 個 -->` | exit 0, zero findings, in both cases. The reconciliation the checker performed was against a number the reader cannot see — an HTML comment renders as nothing |
| FG-3 | **The report-block markers excise content and raise nothing.** `apply_report_blocks` blanks everything outside `report-start`/`report-end`. It was built for teaching documents; nothing distinguishes that use from carving a hole in a report | In [`assumption_no_frame.md`](fixtures/assumption_no_frame.md), bracket the broken `預設 A2` line: `report-end` on the line before it, `report-start` on the line after, with a `report-start` at the top. **Two markers, not one** — the single-marker variants are loud (`ASSUM-01` survives, or `STRUCT-01`/`COUNT-01` fire) | exit 0, zero findings, assumptions 3→2. The only trace is `report_blocks: 2` in the output — a number, not a finding. Nothing says a line was excluded from checking |
| FG-4 | **The lost-leading-pipe threshold counts half-width `\|` only.** Deliberate (full-width `｜` is legal content in an assumption line and in a 〈狀態〉 cell), and listed above as an accepted boundary. It is repeated here because it is reachable by IME drift, not only by an adversary | In [`glance_row_lost_pipe.md`](fixtures/glance_row_lost_pipe.md) — already missing its leading bar — replace the remaining `\|` on that one row with full-width `｜` | exit 0, zero findings. `parse_table` will not take the row (no leading bar), `ROWISH_RE` will not take it (anchored at the start), and the stray threshold counts no half-width bars. Neither consumed nor reported |
| FG-5 | **The 家族數 reconciliation skips silently when the cell holds no ASCII digit.** `LWALL-01` does `re.search(r"\d+", …)` on the cell and returns without a finding if there is no match | In `good_landscape.md`, rewrite `W3`'s 家族數 from `2` to `三` while leaving 〈來源預設〉 at two families — a genuinely wrong count, written in a Chinese numeral | exit 0, zero findings. The control — the same wrong count written as ASCII `3` — raises `LWALL-01`. The check is one CJK numeral away from silence. (`\d` *does* match full-width `２`, so only non-decimal numerals reach this) |

How to use this list after the restructure: reproduce all five, and require that each one either raises a finding or is impossible to express. An item that still produces exit 0 with zero findings means the restructure moved the boundary again rather than removing it — which is the outcome this section exists to make visible.

Two things this list is not. It is not exhaustive: it is what one adversarial pass found, and the previous three rounds each ended believing their list was complete. And it is not the whole ceiling — 〈What a false green would still take〉 above holds the boundaries the design accepts on purpose, and the wording-drift class sits outside both lists because it is a vocabulary problem rather than a parsing one — both patterns key on the literal word 「預設」, so rewriting the assumption lines of [`good_nosearch_report.md`](fixtures/good_nosearch_report.md) as 「前提 A1：…」 or 「假設 A1：…」 gives assumptions **2→0**, `unreadable` **0**, exit **0**, zero findings. Worth re-running alongside the five, for the same reason.

## Narrative documents — the report block

`examples/worked_example.md` is not a report. It is a teaching walkthrough that *contains* report fragments, and its prose quotes 「沒人做過」 in order to warn against writing it. Running the checker over it as if it were a report produces category errors: `STRUCT-02` fires because the header sits below a `## 第 0 步` heading, `COUNT-01` compares a narrative sentence against zero candidate blocks, and `LANG-01` fires three times on the very sentences that teach the rule.

Two fixes were available and one of them is wrong:

- **Rejected: exempt quoted text from `LANG-01`.** It would make the example green at the cost of the check. A report could then write 「我們可以確定地說：「這個題目沒有人做過」」 and pass. The mention/use distinction is not recoverable from punctuation, and `LANG-01` guards the single most consequential sentence type in the whole output.
- **Adopted: check only a delimited report block.** A document may mark where its report actually starts and ends:

```markdown
<!-- format-check: report-start -->
# 研究缺口報告：…
…
<!-- format-check: report-end -->
```

When at least one such block exists, `format_check.py` checks **only** the lines inside the blocks, and nothing else in the file — teaching prose, error demonstrations, before/after comparisons are all invisible to it. Lines outside are blanked rather than removed, so **reported line numbers still refer to the original file**. A `report-start` with no matching `report-end` runs to end of file. Multiple blocks in one document are all checked.

Note what this does *not* do: it does not weaken a single check. Inside the block every rule applies at full strength, including `LANG-01`. The example gets no leniency about its own report — it gets a boundary around the part that claims to be one. `narrative_wrapper.md` is the fixture: `good_report.md` wrapped in a document whose surrounding prose contains 「沒人做過」, expected to be clean.

`self_test.py` treats the examples accordingly: it walks `examples/` off disk rather than from a hard-coded filename, and for every `.md` there, if the file carries the marker it **must** pass the checker or the suite fails; if it does not, the suite prints a warning saying that file is unchecked and moves on. It never pretends a file was verified. Every example currently carries the marker and passes, so those assertions are live — a future edit to an embedded report will turn `self_test.py` red. Reading the directory instead of naming a file is the fix for the obvious next failure: a new walkthrough gets added, nobody remembers this list, and it goes unchecked while the suite stays green.

## fixtures/

The baselines are hand-written:

- `good_report.md` — a full, realistic, fully compliant zh-TW report in the seven-section format: three survivors, three pending rows, six eliminated rows, twenty-two search-log rows, two quantified assumptions and one impression-level one.
- `good_nosearch_report.md` — the tier-3 degraded report (see below), written straight from `SKILL.md`'s rules for that mode.
- `chinese_index_na.md` — a second full report on an unrelated topic, written to pin the third 〈中文索引〉 header value 「不適用（題目非在地界定，使用者不在華語學術體系）」. It is hand-written rather than generated so that the value is exercised by a report that genuinely has no locally-bounded candidate, instead of by an edit to one that does.
- `good_landscape.md` — the landscape baseline: seven technique families for measuring urban green-space exposure, one of them deliberately marked 〔涵蓋不足〕 with 「還沒查到」 for its cost, and a four-row wall table into which every one of the ten `F<n>-<字母>` assumptions lands exactly once. It is a **base**, not a variant of the first: the landscape fixtures are derived from it, not from `good_report.md`.
- `good_inherited_report.md` — **the bridge**: a hunt report whose header carries 〈地形來源〉 and whose section 一 holds all three kinds of assumption at once — one quantified this round (`A1`), one inherited from wall W1 and left unframed (`A2`), and one inherited from W3 whose sampling frame was then paid (`A3`, labelled 〔承接自地形 W3，已補取樣框〕). `A3` is inverted by a G3 candidate, which is the full path `SKILL.md` permits and the one the checker used to reject. It is a base rather than a derivation because the three kinds have to coexist in one file for a one-line edit to isolate any of them.

**Everything else is generated by `make_fixtures.py` from one of the three bases**, one substantive edit each, so "only one dimension is broken" holds by construction rather than by eyesight. The generator refuses to run if the text it is told to replace does not occur exactly once, and `self_test.py` re-runs it in `--check` mode and fails if any fixture on disk has drifted from the generator — a hand-edited fixture would eventually break a second dimension and nobody would notice. Which base each derived fixture came from is declared once, in `make_fixtures.derived_bases()`, and `self_test.py` imports it rather than keeping a second copy — two hand-maintained mappings drift, and the day they drift nobody notices.

| Fixture | Broken dimension | Expected |
|---|---|---|
| `good_report.md` | — | exit 0, no findings |
| `good_nosearch_report.md` | — (the degraded mode: no search tool was available) | exit 0, no findings |
| `bracketed_verdict_ok.md` | — (bracketed state 〔待驗證〕 followed by a note) | exit 0, no findings |
| `narrative_wrapper.md` | — (report block inside a teaching document) | exit 0, no findings |
| `unsearched_pending.md` | — (a partially-searched run: a candidate honestly parked in 待確認 as 〔未驗證〕 is exempt from the search-log interlock) | exit 0, no findings |
| `chinese_index_na.md` | — (hand-written second baseline; 〈中文索引〉 = 不適用) | exit 0, no findings |
| `good_inherited_report.md` | — (the bridge baseline: an inherited-**framed** wall legally inverted by a G3 candidate) | exit 0, no findings |
| `inherited_unframed_ok.md` | — (the inherited-**unframed** wall sits in section 一 feeding no G3: no sample frame demanded, no search-log row demanded) | exit 0, no findings |
| `assumption_blockquote_ok.md` | — (`A3` written the way `SKILL.md` 第 1 步 displays it, `> ` and all) | exit 0, no findings |
| `assumption_two_brackets_ok.md` | — (`A3`'s provenance and paid-frame labels as two adjacent brackets) | exit 0, no findings |
| `assumption_fullwidth_bracket_ok.md` | — (`A3`'s label in full-width ［］, one of the four pairs this page promises) | exit 0, no findings |
| `missing_trace_section.md` | 〈六、檢索紀錄〉 deleted outright, so there is no audit trail (it used to be *retitled*, which is now `SECT-01` — the table is found by its header either way) | exit 1, `STRUCT-01` |
| `trace_section_renamed.md` | 〈六、檢索紀錄〉 retitled 〈六、附錄：查詢筆記〉; the 22 log rows still parse | exit 1, `SECT-01` |
| `consensus_section_renamed.md` | 〈一、領域共識與未被質疑的預設〉 retitled; the three assumptions still parse and no G3 candidate is told its input is missing | exit 1, `SECT-01` |
| `no_tool_tier.md` | 〈文獻工具〉 header declaration is a placeholder | exit 1, `STRUCT-02` |
| `count_mismatch.md` | Section 二 heading says 存活 4 個, three candidate blocks exist | exit 1, `COUNT-01` |
| `count_inverted.md` | Section 二 heading says 生成 2 個 → 存活 3 個 | exit 1, `COUNT-02` |
| `recon_mismatch.md` | 候選結算 claims 待確認 4, section 三 has 3 rows | exit 1, `RECON-01` |
| `bad_verdict.md` | Verdict `NOVEL`, outside the vocabulary | exit 1, `VERDICT-01` |
| `done_in_survivors.md` | A `DONE` verdict sits in the survivor list | exit 1, `VERDICT-02` |
| `assumption_no_frame.md` | 預設 A2 lost its 摘要層精讀／pick／沿用 segment | exit 1, `ASSUM-01` |
| `inherited_framed_partial.md` | 預設 A3 claims 〔已補取樣框〕 but the frame lost its 摘要層精讀／pick／沿用 segment | exit 1, `ASSUM-01` |
| `impression_as_g3.md` | 預設 A1 is 〔印象，未驗證〕 but candidate 1 still inverts it | exit 1, `ASSUM-02` |
| `inherited_unframed_as_g3.md` | C02 inverts `A2`, a wall inherited from the landscape report whose frame was never paid | exit 1, `ASSUM-02` |
| `missing_evidence_field.md` | Survivor has no search-evidence field at all | exit 1, `EVID-01` |
| `no_evidence.md` | Survivor's search-evidence field is the placeholder 「同上」 | exit 1, `EVID-02` |
| `vague_evidence.md` | Search evidence is prose with no verbatim query | exit 1, `EVID-03` |
| `neighbour_no_id.md` | Nearest study is named but carries no identifier | exit 1, `NEIGH-01` |
| `unnamed_kill.md` | The `DONE` row names no literature | exit 1, `KILL-01` |
| `crowded_two_papers.md` | `CROWDED` names only two papers | exit 1, `KILL-02` |
| `done_no_quote.md` | `DONE` reason carries no verbatim abstract quote | exit 1, `KILL-03` |
| `kill_no_identifier.md` | Key literature named, identifier cell blank | exit 1, `ID-01` |
| `untraced_candidate.md` | C03 has no row in 〈檢索紀錄〉 | exit 1, `TRACE-01` |
| `trace_placeholder_query.md` | A 〈檢索紀錄〉 query cell is 「（略）」 | exit 1, `TRACE-02` |
| `assertive_language.md` | 「沒有人做過…目前不存在相關研究…可以確定是新的」 | exit 1, `LANG-01` ×4 (one clause matches two patterns) |
| `no_search_with_verdicts.md` | Header declares no search ran, verdicts and kills filled anyway | exit 1, `TIER-01` |
| `good_landscape.md` | — (the landscape baseline; second hand-written base) | exit 0, no findings |
| `landscape_no_disclaimer.md` | The 〈這份報告不做什麼〉 header line is deleted | exit 1, `LHEAD-01` |
| `landscape_verdict_word.md` | §三 concludes that a combination is `CROWDED` | exit 1, `LVOCAB-01` |
| `landscape_no_cost.md` | F5 states what it buys; its 〈付出什麼〉 is 「—」 | exit 1, `LCOST-01` |
| `landscape_status_asserted.md` | F5 is 活躍 「近三年明顯在加速」 with no search clause in the field | exit 1, `LSTAT-01` |
| `landscape_orphan_assumption.md` | W3 drops F6-a (and its 家族數 with it), so that assumption reaches no wall | exit 1, `LWALL-01` |
| `landscape_assertive.md` | A landscape report writes 「這種疊法沒有人做過」 | exit 1, `LANG-01` |
| `landscape_no_tier.md` | A landscape report's 〈文獻工具〉 declaration is a placeholder | exit 1, `STRUCT-02` |
| `assumption_unreadable_line.md` | 預設 A3's bracket label runs straight into the body with no delimiter, so the line does not parse | exit 1, `ASSUM-01` |
| `assumption_em_dash_separator.md` | 預設 A2's separator is an em dash (`- 預設 A2——〈…〉`), outside the class `ASSUM_LINE_RE` accepts. `A2` is inverted by no candidate, so with round 3's lookahead in place this file was **silent**: assumptions 3→2, `unreadable` 0, exit 0, zero findings | exit 1, `ASSUM-01` |
| `assumption_prose_mention.md` | — (a sentence *about* two assumptions, `- 預設 A1 與 A2 都與量測方式有關`). **A deliberate false red**: it was a green fixture until the lookahead that kept it green was found to be what silenced the row above. Kept red on purpose; if it ever goes green again, the lookahead is back | exit 1, `ASSUM-01` |
| `candidate_head_unreadable.md` | 候選 3's heading numbers itself 「候選三」, so the heading does not parse (the `C03` id still does) | exit 1, `PARSE-01` |
| `kill_row_short.md` | C08's eliminated row is one cell short of its header | exit 1, `PARSE-01` |
| `landscape_wall_row_short.md` | W3's wall row is one cell short of its header, so 〈家族數〉 reads 〈性質〉 and the arithmetic is skipped | exit 1, `PARSE-01` |
| `kill_row_no_verdict.md` | C07's eliminated row has an empty 判定 cell | exit 1, `VERDICT-01` |
| `candidate_head_no_keyword.md` | 候選 1's heading is `### C01：<題目>` — no 候選 keyword, so neither the heading pattern nor the look-alike sees it | exit 1, `PARSE-01` |
| `family_head_no_id.md` | F1's family heading loses its `F1`; the family is rebuilt from its 默默預設 ids | exit 1, `PARSE-01` |
| `glance_row_lost_pipe.md` | the glance table's F1 row loses its leading `\|` — one character, and it used to be silent | exit 1, `PARSE-01` |
| `glance_table_gone.md` | 〈一、一眼表〉 keeps its heading, the table under it is gone (what a paste from a rendered view looks like) | exit 1, `PARSE-01` |
| `landscape_no_glance.md` | 〈一、一眼表〉 removed entirely — the document-level arm, which is what survives a rename and a de-piped table at once | exit 1, `PARSE-01` |
| `landscape_section_renamed.md` | 〈一、一眼表〉 retitled 〈一、總覽表〉; all seven glance rows still parse | exit 1, `SECT-01` |

**The two green assumption-shape fixtures are green on purpose, and their green carries information.** A green run is exactly what a silently dropped line produces, so a fixture that merely passes proves nothing about whether the line was read. Both of these rewrite `A3` — the assumption a G3 candidate inverts — so a drop turns the run red with 「G3 候選指到第一節沒有的預設 A3」 and a half-read label turns it red with the unframed message. On top of that, `self_test.py` reads both files back through the parser and asserts that `A3` is present, classified 承接 **and** 已補框, and actually named by a G3 candidate. Without that read-back the pair would degrade into two more files that happen to pass.

**The five unreadable-input fixtures pin the other half of the promise.** Two of them (`kill_row_short.md`, `landscape_wall_row_short.md`) are the same defect in the two modes, which is what makes `PARSE-01`'s `both` an assertion rather than a claim — the same job the last two rows of this table do for `LANG-01` and `STRUCT-02`. `candidate_head_unreadable.md` is the one worth reading twice: before the fix it raised `COUNT-01` and `RECON-01` saying 「宣告存活 3 個，實際只有 2 個」, and the cheapest way to make that green is to change the 3 to a 2 — which deletes a candidate that was written, from the one interlock that exists to stop candidates disappearing. It now raises `PARSE-01` alone, because the block is registered from the `C03` in its heading and the counts stay right.

**The four bridge fixtures exist because nothing covered the bridge.** `SKILL.md` makes the landscape report's wall table the input to the hunt's 第 1 步, and that hand-off is the whole justification for having two modes — yet the checker's assumption-line pattern required the colon to follow the id directly, so every form the spec prescribes failed to parse. (That pattern then failed a second time, in the same mechanism, on the blockquoted and two-bracket forms — which is why the sweep above exists and why the rule is now stated as a property of every parser rather than a fix to one of them.) The consequences were both silent: an inherited assumption was invisible to the parser, therefore neither counted nor checked; and walking the full permitted path — pay the frame on one wall, relabel it 已補取樣框, invert it with a G3 candidate — made the checker reject a conformant report with 「G3 候選指到第一節沒有的預設 A3」, a message that sends the reader looking for a line that is in fact right there. Every suite was green throughout, which is the point: no fixture had ever put a 〔承接自地形 …〕 label in front of the checker. The four now cover the two-by-two — unframed/framed × feeding G3 or not — so neither semantics can regress without a red run, and the two red ones pin the *messages* as well as the ids.

**The interlock exemption is asserted, not narrated.** `SKILL.md`〈互鎖的例外〉 exempts an inherited-unframed assumption from needing a row in section 六. In `format_check.py` that holds because section 一's assumptions were never in `check_trace`'s target list at all — a green run on `inherited_unframed_ok.md` therefore proves it only as long as the fixture really withholds the row. So `self_test.py` reads both bridge fixtures back through the parser, requires that each still contains an inherited-unframed assumption, and fails if any search-log row names it. Without that, someone adding a tidy 第1步-A2 row later would leave the suite green and the exemption untested.

The last two rows of the table are not new rules. They are what makes `both` in the mode column an assertion rather than a claim: without them, "`LANG-01` and `STRUCT-02` also apply to landscape reports" would be a sentence in this file that no fixture had ever tested, and a dispatch bug that skipped them entirely would leave every suite green.

### The degraded mode must also be green

`SKILL.md` specifies a *second* compliant output: when no search backend is available at all, the report declares 「本次未執行任何檢索…」, emits **zero** `### 候選` blocks, puts every candidate in 待確認 with the state 〔未驗證〕, and fills in no verdict anywhere. An earlier version of this checker made that mode unsatisfiable — omitting the verdict raised `VERDICT-01`, writing 未驗證 raised `VERDICT-02`, and writing `OPEN` raised `TIER-01`, with `EVID-03` and `TRACE-01` firing on top regardless. A checker that cannot be satisfied by its own specification trains the model to ignore it, which is worse than having no checker.

So `format_check.py` recognises the degraded mode and suspends the checks that presuppose a search actually happened (`EVID-03`, `TRACE-01`, the missing-field arms of `VERDICT-01` and `NEIGH-01`, and `VERDICT-02`). `TIER-01` stays armed and now covers the kill table as well — a report that admits it ran no search but eliminates six candidates anyway is exactly the dishonesty this mode invites, and `no_search_with_verdicts.md` guards it.

**Every bibliographic reference in the fixtures is synthetic.** Authors are `Author A` … `Author CH` (`good_report.md` and everything derived from it use `A`–`R`; `chinese_index_na.md` has its own `S`–`AA` namespace, `good_landscape.md` a third one, `BA`–`BZ`, and `good_inherited_report.md` a fourth, `CA`–`CH`, so no two baselines ever collide); identifiers use the Crossref test prefix `10.5555`. One place falls outside that scheme: the NDLTD／Airiti row in `good_report.md`'s search log (and in every fixture derived from it) lists three invented zh-TW thesis titles with no `Author X` label and no system number, so neither tell applies to them — what covers them is the per-file banner at the top of the fixture, which says every reference in the file is fictional. Nothing in `fixtures/` corresponds to a real publication, and nothing in it should ever be cited.

### Choosing the fixture topic

The base corpus is about urban park green space and residents' physical activity. Three properties make it work as a test asset: the field has enough real international literature that a `CROWDED` or `DONE` verdict reads as plausible rather than invented; it has an obvious locally-bounded variant (shade in Taiwanese neighbourhood parks) that genuinely could only be settled in NDLTD / Airiti, so the Chinese-index path is exercised by a candidate that really needs it instead of by a decoration; and it is far enough from measurement-heavy CS that the assumption lines about exposure metrics and self-report validity are the field's own arguments, not borrowed ones.

`good_landscape.md` stays inside that same corpus deliberately: it maps the *measurement* families for green-space exposure (satellite indices, GIS buffers, street-view scoring, questionnaires, GPS traces, footfall counters, on-site audits). Two things fall out of that choice. The families are genuinely distinguished by their trade-offs rather than their names, which is the property `SKILL.md` asks for and the hardest one to fake in a fixture; and its wall W1 is the same proposition as `good_report.md`'s 預設 A1, so the pair also demonstrates the bridge the two modes are supposed to form — without either file claiming to be the other's output. What it deliberately is **not** is the domain of the live trial (image recognition), for the reason immediately below.

**The rule this encodes: a test corpus must not carry anyone's unpublished research direction.** Fixtures are the part of a repo people read most carefully, because they are the part that shows what the tool considers a good report — so a fixture built on a topic someone on the project is actively researching publishes that work by the back door. It also makes the corpus worse as a test: a topic the author knows intimately gets written with private context a reader cannot check, and plausibility to the author stops being evidence of plausibility to anyone else. Pick a topic with a real public literature that nobody on the project is working on.

## doc_scan.py — the docs must describe this repo, not the previous one

```bash
python evals/doc_scan.py
```

Everything else in this directory checks a *report*. This one checks the *documentation*, and it is the reason a stale README is a failing gate rather than a footnote. It derives the numbers first — check count from `CHECK_DESCRIPTIONS`, fixture count from `fixtures/` and `self_test.EXPECTED`, mutant count from `MUTATIONS` — and then reads `SKILL.md`, both top-level READMEs, this file, `references/` and `examples/` looking for claims that no longer match:

1. every `` `path.md` `` / `` `path.py` `` mentioned in prose actually exists;
2. every `python evals/…` / `python scripts/…` command tells the reader to run a file that is there;
3. every relative markdown link resolves;
4. the two READMEs still have the same number of `##` sections — the mirror is a promise, and a section that exists in one language only is a promise made to half the readers;
5. written-down counts (checks, fixtures, mutants, generators, template sections) match the derived ones, in both `N checks` and `N 條規則` shapes, and **both** output templates in `SKILL.md` — the gap report's and the landscape report's — still have the same `## ` section names as their baseline fixtures;
6. the verdict vocabulary in `SKILL.md` matches the one `format_check.py` accepts, the five 〈狀態〉 values likewise, and the 〈這份報告不做什麼〉 fixed sentence is byte-identical in both places — a one-character drift there would make every conformant landscape report fail `LHEAD-01`, with the report right and the checker wrong;
7. the two suites' coverage assertions still hold;
8. no local absolute path (`C:\Users\<name>\…`, `/home/<name>/…`) has leaked into any text file — the same class `zip_check.py` catches in the package, caught earlier;
9. how much of the working tree `git ls-files` actually covers, since `scripts/package_skill.py` packages from that list and silently ships whatever is committed.

Exit `1` on any mismatch, item 8 included — a leaked path fails the run here exactly as it does in the package. Item 9 is the exception: it prints as an advisory, because uncommitted files are a packaging hazard rather than a documentation defect. Read the whole output, not only the exit code.

What it is for: the counts in the top-level READMEs went stale by three and four while every suite in this directory stayed green, because until this script existed nothing in the repo read the prose. Eight occurrences — four claims, mirrored in both languages — and a reader had no way to know.

## zip_check.py

Before sharing a packaged skill (uploading to ChatGPT, sending it to someone):

```bash
python evals/zip_check.py research-gap-hunter.zip
```

Scans the archive for API keys, personal email addresses, machine-specific absolute paths, and stray `.env` / `.git` / `__pycache__` entries, and exits non-zero on a hit so `scripts/package_skill.py` deletes the archive instead of handing it over. Manual review misses these; a regex does not. This one matters more here than it looks: gap-hunter's docs quote clone paths, so the `C:\Users\…` pattern is the one most likely to fire.

## Each bad fixture must raise exactly one check

`self_test.py` asserts the *set* of check ids, not merely that the run went red. If a single broken dimension starts raising two ids, that is a defect in the checks — overlapping rules make the output undiagnosable — and it must be fixed in `format_check.py`, not absorbed into the expectations. The self-test also asserts that the human-readable mode agrees with `--json` on the exit code, that every finding has a valid line number, that each generated fixture differs from **its own** baseline by no more than two lines (the mapping comes from `make_fixtures.derived_bases()`, not a second copy kept here), and that the fixtures on disk are byte-identical to what the generator produces. It additionally asserts the inherited-unframed search-log exemption directly against the fixtures, as described under 〈fixtures/〉.

`self_test.py` also asserts **coverage**: every id in `CHECK_DESCRIPTIONS` must own a fixture. A check with no fixture is not a tested check — it is only a check that `good_report.md` happens not to trip — and the suite fails rather than letting that pass silently. `mutation_test.py` asserts the mirror image: every declared id must own a mutant.

## mutation_test.py — proving the rule is what caught it

A green self-test proves a bad fixture goes red. It does not prove *which rule* turned it red. A fixture can trip three rules at once while the rule you believe is guarding it never executes; the suite still passes, and the coverage table lies.

So `mutation_test.py` weakens each rule's **condition** — not its `self.add` line — in a throwaway copy of `format_check.py` under `tempfile.mkdtemp()`, and re-runs that rule's fixture:

- the target id disappears → that rule is what caught it (**PASS**)
- the target id survives → something else was catching it and the rule is unproven (**FAIL**)

Mutating the condition rather than the reporting line is the whole point: deleting a `self.add` obviously removes its finding and proves nothing. Every mutant is also run against **all three** clean baselines — `good_report.md`, `good_landscape.md` and `good_inherited_report.md` — because a weakening that turns a compliant report red has damaged a different rule, and with three document shapes a mutation can now damage the shape it was not aimed at. The real `format_check.py` is opened read-only throughout.

Where a rule has several arms that all fire on one fixture, the mutation targets the rule's **guard** instead of a single arm — `ASSUM-01`'s mutant treats every assumption as impression-level, `TIER-01`'s mutant disarms the whole degraded-mode branch, `RECON-01`'s mutant back-fills the settlement numbers from the actual row counts. That is still a condition, and it still proves the rule is load-bearing.

Four mutants weaken the *parser's* self-awareness rather than a report rule: the column-count comparison, the candidate-heading fallback, the assumption-line look-alike, and the blank-verdict arm. Each returns the checker to the behaviour it had before this round, which is the useful thing to see in a mutation run — `PARSE-01`'s heading mutant makes `candidate_head_unreadable.md` red under `COUNT-01`/`RECON-01` instead, printed as a backstop under `-v`, and that backstop is precisely the misleading pair the fix removed. The blank-verdict mutant restores the old `continue`, because merely disabling the report there would let the vocabulary arm catch the same row and prove nothing.

`ASSUM-01`, `ASSUM-02` and `PARSE-01` each own more than one mutant, one per arm, because the branches are genuinely separate rather than another way of reaching the same code: `ASSUM-01`'s second mutant makes every inherited assumption count as unframed (so a claimed 已補取樣框 stops being held to the frame) and `ASSUM-02`'s second treats an unframed inherited wall as a legal G3 input. Both are conditions, both are unique in the source, and each is paired with the fixture that trips only its own arm. A check id may appear more than once in `MUTATIONS`; the coverage assertion deduplicates.

Rules backstopped by another are reported rather than hidden: `-v` prints which id took over after the target was weakened. Defence in depth is fine. Not knowing which layer fires first is not.

## Adding a check

1. Add the rule to `CHECK_DESCRIPTIONS` with a prefixed id, then implement it in the matching `check_*` method — on `Checker` for a gap rule, on `LandscapeChecker` for a landscape one, on `BaseChecker` only if it genuinely applies to both.
2. Add a fixture spec to `FIXTURES_SPEC` (gap), `LAND_FIXTURES_SPEC` (landscape) or `INHERIT_FIXTURES_SPEC` (a hunt report that inherited walls) in `make_fixtures.py` breaking that one dimension only, and run the generator. Break exactly the arm you intend to mutate: a fixture that trips two arms of the same rule needs a mutation that disarms both, and the honest way to get one is usually a narrower fixture rather than a wider mutation.
3. Add the row to `EXPECTED` in `self_test.py`.
4. Add the row to `MUTATIONS` in `mutation_test.py`, weakening the new rule's **condition**.
5. Run `python evals/self_test.py` then `python evals/mutation_test.py`. The new fixture must raise exactly its own id, every existing fixture must be unchanged (an old fixture gaining a second id means the new check overlaps an old one), and the new mutant must turn its fixture green.

If the new rule can fire on the degraded no-search report, gate it on `self.rep.no_search_declared` — see the degraded-mode note above.

## Not covered here

No network, so nothing about search quality, coverage, or literature truth is tested — see the block at the top. There is also no test of the skill's *judgment*: whether the six generators produced good candidates, whether an elimination was correct, whether a survivor is genuinely novel. Those are not mechanically checkable and this directory does not pretend otherwise. The honest limitations section of the README says the same thing in the user's language.
