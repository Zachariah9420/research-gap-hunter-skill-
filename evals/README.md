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
| `STRUCT-01` | hunt | 〈存活候選〉〈待確認〉〈已淘汰〉〈檢索紀錄〉 sections all present | A report missing 檢索紀錄 has no audit trail; one missing 待確認 has nowhere to put an undecided candidate, so it drops it |
| `STRUCT-02` | both | Header declares 文獻工具 tier | Tier 2 wording must never be read as tier 0 |
| `COUNT-01` | hunt | Declared survivor count == number of `### 候選 N` blocks | The cheapest way to look thorough is to claim candidates that were never written |
| `COUNT-02` | hunt | Generated count ≥ survivor count | Arithmetic sanity |
| `RECON-01` | hunt | 候選結算 reconciles: 生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q, each count matches the section it names, and every `C<nn>` appears in exactly one of 二/三/四 | Silent disappearance is the failure mode the 待確認 section was added to prevent; without an arithmetic interlock the section just moves the hiding place |
| `VERDICT-01` | hunt | Each section's verdict/state value is in that section's vocabulary (二: ADJACENT/OPEN/INCREMENTAL, 三: the pending states, 四: DONE/CROWDED only) | Invented verdicts smuggle in unstated criteria; a pending state in the kill table is an elimination that was never earned |
| `VERDICT-02` | hunt | Survivors are only ADJACENT / OPEN / INCREMENTAL | A DONE in the survivor list is a contradiction |
| `ASSUM-01` | hunt | A quantified assumption carries the whole sample frame — 標題層掃描 N／檢索詞／limit／摘要層精讀 M′／pick 索引／其中 M 篇沿用／推翻性檢索／回傳 K′／讀後 K／樣本來源 — with M ≤ M′, K ≤ K′, M′ ≥ 3; anything less must be written 〔印象，未驗證〕. **Exempt: an assumption labelled 〔承接自地形 W\<k\>〕 without 已補取樣框** — a landscape report by definition never ran N／M′／M／K′／K, so demanding a frame from it demands a set of numbers nobody produced. Add 已補取樣框 to the label and it is held to the full frame like any other | The assumption list is the most hallucinable artifact in the skill: it is written before any candidate exists and everything downstream inherits it. A bare 「檢視 20 篇」 cannot be audited; the split frame can. The inherited exemption is the same principle pointed the other way — a checker that demands evidence of work that was never supposed to happen this round teaches the model to invent it |
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
| `LSTAT-01` | landscape | 〈狀態〉 is one of 飽和／活躍／新興／衰退／〔涵蓋不足〕, and anything but 〔涵蓋不足〕 carries the search clause (`回傳 X 筆` plus a verbatim query) in the same field | 「哪些飽和、哪些還在動」 is the question this mode exists to answer, so it is also the sentence most worth faking. Requiring the search inline makes 〔涵蓋不足〕 the cheap answer and 飽和 the paid one — the gradient has to point that way or the mode fills up with confident adjectives |
| `LWALL-01` | landscape | §六 and §二 reconcile both ways: every `F<n>-<字母>` in §二 lands in exactly one wall, every id in 〈來源預設〉 exists in §二, and 〈家族數〉 equals the deduplicated family count | This section is the deliverable — it is what 第 1 步 of the hunt inherits. An assumption written in §二 and missing from §六 is dropped in transit; a wall citing ids that do not exist was imagined rather than pooled. Same defect class as `RECON-01`, same reason for an arithmetic interlock |

**The parser is deliberately tolerant.** `SKILL.md` is prose and its wording will drift. Labels are matched through an alias table (`搜尋證據` / `檢索證據` / `證據`; `最接近的既有研究` / `最近鄰文獻`), table columns are matched by keyword rather than position, both half- and full-width colons are accepted, `→` / `->` / `至` all parse in the count line, `＝`/`=` and `＋`/`+` both parse in the settlement line, and the `（C03）` id in a candidate heading may be omitted (older reports still parse, they just fail `RECON-01`).

**The assumption line carries an optional bracketed provenance label between its id and its colon** — `預設 A1〔承接自地形 W3，支撐家族 F1、F4〕：…` — because that is the only form `SKILL.md` 第 1 步（甲） gives for a wall inherited from a landscape report, and inheritance is the single interface between the two modes. The label decides which rule set the line falls under: 承接自地形 without 已補取樣框 is exempt from `ASSUM-01` and barred from G3 by `ASSUM-02`; 承接自地形…已補取樣框 is treated exactly like a locally quantified assumption on both counts. The label is classified off the **label**, never off the body: `SKILL.md`'s own template ends such a line with 「效力同〔印象，未驗證〕」, and reading that as the line's provenance would collapse an inherited wall into an ordinary impression and lose the fact that another report produced it. Nothing rewrites the label, and no message ever tells a report to replace it with 〔印象，未驗證〕 — same force, different provenance, and the reader has to be able to see which.

`LANG-01` carries a suppression guard: a line containing `≠`, `不代表`, `不得寫`, `並非`, `錯誤示範` and similar is read as *discussing* the forbidden phrase rather than asserting it, so a report may quote the rule it is obeying. The guard is deliberately narrow — see 〈Narrative documents〉 below for why quoting alone is not enough to earn an exemption.

Every finding prints its check id, line number, message and the offending line, and `--json` emits the same fields plus the parse summary (`mode`, `candidate_sections`, `pending_rows`, `kill_rows`, `trace_rows`, `settlement`, `assumptions`, `families`, `glance_rows`, `wall_rows`, `report_blocks`) so a wrapper can tell "clean" from "parsed nothing". Line numbers are always ≥ 1: a whole-file defect anchors at line 1 rather than line 0, because a consumer cannot jump to line 0.

### Why the landscape rule set is thin

Five rules, plus the two that are genuinely mode-independent. That is not an unfinished rule set; it is the point of the mode.

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
| `missing_trace_section.md` | 〈六、檢索紀錄〉 retitled, so there is no audit trail | exit 1, `STRUCT-01` |
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

**The four bridge fixtures exist because nothing covered the bridge.** `SKILL.md` makes the landscape report's wall table the input to the hunt's 第 1 步, and that hand-off is the whole justification for having two modes — yet the checker's assumption-line pattern required the colon to follow the id directly, so every form the spec prescribes failed to parse. The consequences were both silent: an inherited assumption was invisible to the parser, therefore neither counted nor checked; and walking the full permitted path — pay the frame on one wall, relabel it 已補取樣框, invert it with a G3 candidate — made the checker reject a conformant report with 「G3 候選指到第一節沒有的預設 A3」, a message that sends the reader looking for a line that is in fact right there. Every suite was green throughout, which is the point: no fixture had ever put a 〔承接自地形 …〕 label in front of the checker. The four now cover the two-by-two — unframed/framed × feeding G3 or not — so neither semantics can regress without a red run, and the two red ones pin the *messages* as well as the ids.

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

`ASSUM-01` and `ASSUM-02` each own **two** mutants, one per arm, because the inherited semantics are a genuinely separate branch rather than another way of reaching the same code: `ASSUM-01`'s second mutant makes every inherited assumption count as unframed (so a claimed 已補取樣框 stops being held to the frame) and `ASSUM-02`'s second treats an unframed inherited wall as a legal G3 input. Both are conditions, both are unique in the source, and each is paired with the fixture that trips only its own arm. A check id may appear more than once in `MUTATIONS`; the coverage assertion deduplicates.

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
