# Evals

Six scripts live here: the report checker (`format_check.py`), two test suites over it (`self_test.py`, `mutation_test.py`), the fixture generator those suites depend on (`make_fixtures.py`), the docs-versus-repo scanner (`doc_scan.py`) and the package scanner (`zip_check.py`). No network, no API keys, seconds to run.
Run both suites **and `doc_scan.py`** before shipping any change to `format_check.py`, to the output-format block in `SKILL.md`, or to either README — the suites catch a broken checker, `doc_scan.py` catches a README that still describes the previous one.

```bash
python evals/self_test.py                            # every fixture must land on its expected check id
python evals/mutation_test.py                        # proves each rule is what catches its fixture
python evals/mutation_test.py -v                     # also lists which rule backstops which
python evals/make_fixtures.py                        # regenerate the derived fixtures from good_report.md
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

`format_check.py` catches: a `DONE` with no paper named, a survivor whose search-evidence field says 「同上」, a header claiming three survivors when two are present, an assumption presented as quantified without the sample frame behind it, a candidate that was generated and then silently vanished, the sentence 「沒有人做過」.

It does **not** catch, and cannot: whether the named paper exists, whether its abstract really says what the report quotes, whether the paper was retracted, whether any query was ever actually run, whether `N`/`M′`/`M`/`K′`/`K` are the real numbers or plausible-looking inventions. A report can be entirely fabricated and pass every check in this directory with a green tick. Existence, retraction and bibliographic correctness are lit-review's job — `verify`, `retract`, `check` — and section 七 of the report format exists precisely so the user can paste the DOI list straight into them.

**Form is checkable, truth is not. Do not let a green run be read as a verified report.**

### Parts of SKILL.md that are deliberately *not* mechanised

Stated here so nobody mistakes the checker's silence for approval:

- the 覆蓋率警告 header line required at tiers 2/3, and the tier strings themselves — the checker only verifies that 文獻工具 is declared and is not a placeholder, not that the wording matches the tier actually used;
- 偵察模式's invariants (1 candidate, 2 searches, only 〔DONE?〕/〔待再查〕) — a recon-mode report is checked as an ordinary report;
- the 第1步-共識 / 第1步-推翻A\<k\> rows in section 六 — `TRACE-01` covers candidates, not the step-1 searches behind section 一;
- whether the `pick` indices listed in an assumption actually number M′, whether a CROWDED's three papers really map to three distinct sub-questions, whether a DONE's four-way match holds;
- everything in sections 五 and 七.

## format_check.py

The checks below are the parts of `SKILL.md` that survive being reduced to a mechanical rule. Each one exists because a plausible-looking report can satisfy the format while quietly skipping the work.

| id | Check | Why |
|---|---|---|
| `STRUCT-01` | 〈存活候選〉〈待確認〉〈已淘汰〉〈檢索紀錄〉 sections all present | A report missing 檢索紀錄 has no audit trail; one missing 待確認 has nowhere to put an undecided candidate, so it drops it |
| `STRUCT-02` | Header declares 文獻工具 tier | Tier 2 wording must never be read as tier 0 |
| `COUNT-01` | Declared survivor count == number of `### 候選 N` blocks | The cheapest way to look thorough is to claim candidates that were never written |
| `COUNT-02` | Generated count ≥ survivor count | Arithmetic sanity |
| `RECON-01` | 候選結算 reconciles: 生成 N ＝ 存活 M ＋ 待確認 P ＋ 已淘汰 Q, each count matches the section it names, and every `C<nn>` appears in exactly one of 二/三/四 | Silent disappearance is the failure mode the 待確認 section was added to prevent; without an arithmetic interlock the section just moves the hiding place |
| `VERDICT-01` | Each section's verdict/state value is in that section's vocabulary (二: ADJACENT/OPEN/INCREMENTAL, 三: the pending states, 四: DONE/CROWDED only) | Invented verdicts smuggle in unstated criteria; a pending state in the kill table is an elimination that was never earned |
| `VERDICT-02` | Survivors are only ADJACENT / OPEN / INCREMENTAL | A DONE in the survivor list is a contradiction |
| `ASSUM-01` | A quantified assumption carries the whole sample frame — 標題層掃描 N／檢索詞／limit／摘要層精讀 M′／pick 索引／其中 M 篇沿用／推翻性檢索／回傳 K′／讀後 K／樣本來源 — with M ≤ M′, K ≤ K′, M′ ≥ 3; anything less must be written 〔印象，未驗證〕 | The assumption list is the most hallucinable artifact in the skill: it is written before any candidate exists and everything downstream inherits it. A bare 「檢視 20 篇」 cannot be audited; the split frame can |
| `ASSUM-02` | A G3 candidate names the assumption it inverts, and that assumption is not 〔印象，未驗證〕 | G3 turns an assumption into a research topic. If the assumption was an impression, the whole candidate is an impression wearing evidence |
| `EVID-01` | Every survivor has a search-evidence field | — |
| `EVID-02` | That field is not empty or a placeholder (`同上`, `略`, `TBD`, `…`) | — |
| `EVID-03` | That field contains at least one concrete query string | Queries must be copy-pasteable so the user can re-run them |
| `NEIGH-01` | 最接近的既有研究 present; if it names a paper it carries an identifier | Without a DOI the user cannot check the claim |
| `KILL-01` | Every eliminated row names key literature | 每一個淘汰都必須指名殺死它的那篇文獻。There is no exemption any more: a row that cannot name literature is not an elimination, it belongs in 待確認 |
| `KILL-02` | `CROWDED` names ≥3 papers | `CROWDED` is otherwise the cheapest verdict in the skill and becomes an escape hatch |
| `KILL-03` | `DONE` carries a verbatim quoted sentence in its reason | A false DONE deletes a viable topic silently and permanently |
| `ID-01` | Named key literature carries a DOI / arXiv id / S2 corpus id | Makes the `retract` and `verify` handoff mechanically possible |
| `TRACE-01` | Every candidate in 二/三/四 has a row in 〈檢索紀錄〉 — **except** a 三 row whose state is 〔未驗證〕, or 〔UNSEARCHABLE〕 blocked on terminology | The one guard against a report produced with zero searches — and a kill with no logged search is worse than a survivor with none. The exemption exists because those rows are in 待確認 *precisely because nobody searched them*: demanding a log row from them would make the honest report non-conformant and the cheapest way to go green would be to invent a search that never ran. See `SKILL.md`〈互鎖的例外〉 |
| `TRACE-02` | 〈檢索紀錄〉 query cells are concrete, not placeholders | Same reason |
| `LANG-01` | No assertive non-existence wording anywhere | 「我沒搜到」 is a result; 「不存在」 is a claim |
| `TIER-01` | If the header declares no search was run, no verdict and no elimination may appear | — |

**The parser is deliberately tolerant.** `SKILL.md` is prose and its wording will drift. Labels are matched through an alias table (`搜尋證據` / `檢索證據` / `證據`; `最接近的既有研究` / `最近鄰文獻`), table columns are matched by keyword rather than position, both half- and full-width colons are accepted, `→` / `->` / `至` all parse in the count line, `＝`/`=` and `＋`/`+` both parse in the settlement line, and the `（C03）` id in a candidate heading may be omitted (older reports still parse, they just fail `RECON-01`).

`LANG-01` carries a suppression guard: a line containing `≠`, `不代表`, `不得寫`, `並非`, `錯誤示範` and similar is read as *discussing* the forbidden phrase rather than asserting it, so a report may quote the rule it is obeying. The guard is deliberately narrow — see 〈Narrative documents〉 below for why quoting alone is not enough to earn an exemption.

Every finding prints its check id, line number, message and the offending line, and `--json` emits the same fields plus the parse summary (`candidate_sections`, `pending_rows`, `kill_rows`, `trace_rows`, `settlement`, `assumptions`, `report_blocks`) so a wrapper can tell "clean" from "parsed nothing". Line numbers are always ≥ 1: a whole-file defect anchors at line 1 rather than line 0, because a consumer cannot jump to line 0.

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

`self_test.py` treats the example accordingly: if `examples/worked_example.md` carries the marker, it **must** pass the checker or the suite fails; if it does not, the suite prints a warning saying the file is unchecked and moves on. It never pretends the file was verified. The example currently carries the marker and passes, so that assertion is live — a future edit to the walkthrough's embedded report will turn `self_test.py` red.

## fixtures/

Three baselines are hand-written:

- `good_report.md` — a full, realistic, fully compliant zh-TW report in the seven-section format: three survivors, three pending rows, six eliminated rows, twenty-two search-log rows, two quantified assumptions and one impression-level one.
- `good_nosearch_report.md` — the tier-3 degraded report (see below), written straight from `SKILL.md`'s rules for that mode.
- `chinese_index_na.md` — a second full report on an unrelated topic, written to pin the third 〈中文索引〉 header value 「不適用（題目非在地界定，使用者不在華語學術體系）」. It is hand-written rather than generated so that the value is exercised by a report that genuinely has no locally-bounded candidate, instead of by an edit to one that does.

**Everything else is generated by `make_fixtures.py` from `good_report.md`**, one substantive edit each, so "only one dimension is broken" holds by construction rather than by eyesight. The generator refuses to run if the text it is told to replace does not occur exactly once, and `self_test.py` re-runs it in `--check` mode and fails if any fixture on disk has drifted from the generator — a hand-edited fixture would eventually break a second dimension and nobody would notice.

| Fixture | Broken dimension | Expected |
|---|---|---|
| `good_report.md` | — | exit 0, no findings |
| `good_nosearch_report.md` | — (the degraded mode: no search tool was available) | exit 0, no findings |
| `bracketed_verdict_ok.md` | — (bracketed state 〔待驗證〕 followed by a note) | exit 0, no findings |
| `narrative_wrapper.md` | — (report block inside a teaching document) | exit 0, no findings |
| `unsearched_pending.md` | — (a partially-searched run: a candidate honestly parked in 待確認 as 〔未驗證〕 is exempt from the search-log interlock) | exit 0, no findings |
| `chinese_index_na.md` | — (hand-written second baseline; 〈中文索引〉 = 不適用) | exit 0, no findings |
| `missing_trace_section.md` | 〈六、檢索紀錄〉 retitled, so there is no audit trail | exit 1, `STRUCT-01` |
| `no_tool_tier.md` | 〈文獻工具〉 header declaration is a placeholder | exit 1, `STRUCT-02` |
| `count_mismatch.md` | Section 二 heading says 存活 4 個, three candidate blocks exist | exit 1, `COUNT-01` |
| `count_inverted.md` | Section 二 heading says 生成 2 個 → 存活 3 個 | exit 1, `COUNT-02` |
| `recon_mismatch.md` | 候選結算 claims 待確認 4, section 三 has 3 rows | exit 1, `RECON-01` |
| `bad_verdict.md` | Verdict `NOVEL`, outside the vocabulary | exit 1, `VERDICT-01` |
| `done_in_survivors.md` | A `DONE` verdict sits in the survivor list | exit 1, `VERDICT-02` |
| `assumption_no_frame.md` | 預設 A2 lost its 摘要層精讀／pick／沿用 segment | exit 1, `ASSUM-01` |
| `impression_as_g3.md` | 預設 A1 is 〔印象，未驗證〕 but candidate 1 still inverts it | exit 1, `ASSUM-02` |
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

### The degraded mode must also be green

`SKILL.md` specifies a *second* compliant output: when no search backend is available at all, the report declares 「本次未執行任何檢索…」, emits **zero** `### 候選` blocks, puts every candidate in 待確認 with the state 〔未驗證〕, and fills in no verdict anywhere. An earlier version of this checker made that mode unsatisfiable — omitting the verdict raised `VERDICT-01`, writing 未驗證 raised `VERDICT-02`, and writing `OPEN` raised `TIER-01`, with `EVID-03` and `TRACE-01` firing on top regardless. A checker that cannot be satisfied by its own specification trains the model to ignore it, which is worse than having no checker.

So `format_check.py` recognises the degraded mode and suspends the checks that presuppose a search actually happened (`EVID-03`, `TRACE-01`, the missing-field arms of `VERDICT-01` and `NEIGH-01`, and `VERDICT-02`). `TIER-01` stays armed and now covers the kill table as well — a report that admits it ran no search but eliminates six candidates anyway is exactly the dishonesty this mode invites, and `no_search_with_verdicts.md` guards it.

**Every bibliographic reference in the fixtures is synthetic.** Authors are `Author A` … `Author AA` (`good_report.md` and everything derived from it use `A`–`R`; `chinese_index_na.md` has its own `S`–`AA` namespace so the two baselines never collide); identifiers use the Crossref test prefix `10.5555`. One place falls outside that scheme: the NDLTD／Airiti row in `good_report.md`'s search log (and in every fixture derived from it) lists three invented zh-TW thesis titles with no `Author X` label and no system number, so neither tell applies to them — what covers them is the per-file banner at the top of the fixture, which says every reference in the file is fictional. Nothing in `fixtures/` corresponds to a real publication, and nothing in it should ever be cited.

### Choosing the fixture topic

The base corpus is about urban park green space and residents' physical activity. Three properties make it work as a test asset: the field has enough real international literature that a `CROWDED` or `DONE` verdict reads as plausible rather than invented; it has an obvious locally-bounded variant (shade in Taiwanese neighbourhood parks) that genuinely could only be settled in NDLTD / Airiti, so the Chinese-index path is exercised by a candidate that really needs it instead of by a decoration; and it is far enough from measurement-heavy CS that the assumption lines about exposure metrics and self-report validity are the field's own arguments, not borrowed ones.

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
5. written-down counts (checks, fixtures, mutants, generators, template sections) match the derived ones, in both `N checks` and `N 條規則` shapes;
6. the verdict vocabulary in `SKILL.md` matches the one `format_check.py` accepts;
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

`self_test.py` asserts the *set* of check ids, not merely that the run went red. If a single broken dimension starts raising two ids, that is a defect in the checks — overlapping rules make the output undiagnosable — and it must be fixed in `format_check.py`, not absorbed into the expectations. The self-test also asserts that the human-readable mode agrees with `--json` on the exit code, that every finding has a valid line number, that each generated fixture differs from `good_report.md` by no more than two lines, and that the fixtures on disk are byte-identical to what the generator produces.

`self_test.py` also asserts **coverage**: every id in `CHECK_DESCRIPTIONS` must own a fixture. A check with no fixture is not a tested check — it is only a check that `good_report.md` happens not to trip — and the suite fails rather than letting that pass silently. `mutation_test.py` asserts the mirror image: every declared id must own a mutant.

## mutation_test.py — proving the rule is what caught it

A green self-test proves a bad fixture goes red. It does not prove *which rule* turned it red. A fixture can trip three rules at once while the rule you believe is guarding it never executes; the suite still passes, and the coverage table lies.

So `mutation_test.py` weakens each rule's **condition** — not its `self.add` line — in a throwaway copy of `format_check.py` under `tempfile.mkdtemp()`, and re-runs that rule's fixture:

- the target id disappears → that rule is what caught it (**PASS**)
- the target id survives → something else was catching it and the rule is unproven (**FAIL**)

Mutating the condition rather than the reporting line is the whole point: deleting a `self.add` obviously removes its finding and proves nothing. Every mutant is also run against `good_report.md`, because a weakening that turns a compliant report red has damaged a different rule. The real `format_check.py` is opened read-only throughout.

Where a rule has several arms that all fire on one fixture, the mutation targets the rule's **guard** instead of a single arm — `ASSUM-01`'s mutant treats every assumption as impression-level, `TIER-01`'s mutant disarms the whole degraded-mode branch, `RECON-01`'s mutant back-fills the settlement numbers from the actual row counts. That is still a condition, and it still proves the rule is load-bearing.

Rules backstopped by another are reported rather than hidden: `-v` prints which id took over after the target was weakened. Defence in depth is fine. Not knowing which layer fires first is not.

## Adding a check

1. Add the rule to `CHECK_DESCRIPTIONS` with a prefixed id, then implement it in the matching `check_*` method.
2. Add a fixture spec to `FIXTURES_SPEC` in `make_fixtures.py` breaking that one dimension only, and run the generator.
3. Add the row to `EXPECTED` in `self_test.py`.
4. Add the row to `MUTATIONS` in `mutation_test.py`, weakening the new rule's **condition**.
5. Run `python evals/self_test.py` then `python evals/mutation_test.py`. The new fixture must raise exactly its own id, every existing fixture must be unchanged (an old fixture gaining a second id means the new check overlaps an old one), and the new mutant must turn its fixture green.

If the new rule can fire on the degraded no-search report, gate it on `self.rep.no_search_declared` — see the degraded-mode note above.

## Not covered here

No network, so nothing about search quality, coverage, or literature truth is tested — see the block at the top. There is also no test of the skill's *judgment*: whether the six generators produced good candidates, whether an elimination was correct, whether a survivor is genuinely novel. Those are not mechanically checkable and this directory does not pretend otherwise. The honest limitations section of the README says the same thing in the user's language.
