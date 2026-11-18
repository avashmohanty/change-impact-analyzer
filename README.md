# Change Impact Analyzer

Read a free-text change request, identify which catalogued systems it modifies, compute the **downstream blast radius** from a dependency graph, and rate risk, with the LLM doing only the language-understanding step.

## Problem
Change advisory reviews depend on the author listing what a change touches. Authors under-report: a credential rotation "for everything that talks to payments" doesn't name Payments or the Customer DB, and the reviewer has to know the architecture by heart to catch it. Failures show up as incidents caused by systems nobody knew were downstream. Asking a chatbot "what could this break?" produces fluent, unverifiable guesses.

## Approach
1. **LLM extracts facts only:** which catalogued systems the change modifies (exact names from a closed list, each with a verbatim evidence phrase), whether a concrete rollback plan is stated, whether testing was actually done.
2. **Grounding:** a component is accepted only if its name is in the catalog and its evidence phrase appears in the request. Invented systems and invented quotes are rejected.
3. **Deterministic logic computes the rest:** transitive downstream dependents from the catalog graph, and a risk level from criticality, blast radius, and missing controls. Anything that must be auditable lives in plain code, not in the model.
4. **Safe failure:** if no system is identified, the result is `Needs review`, never `Low`.
5. **Eval harness** with a keyword/alias baseline as the control.

## Run it
```bash
python data/build_data.py
python test_pipeline.py                 # offline tests: graph, risk rules, grounding
python eval.py --mode baseline          # measured here
export ANTHROPIC_API_KEY=...            # optional: set ANTHROPIC_MODEL
python eval.py --mode llm               # fill in the table below
python analyze.py --mode llm --cr CR-16 # write output/sample_report.md
```
Standard library only.

## Measured result
Dataset: 12-system synthetic catalog, 17 hand-written change requests (20 gold system references, 4 of them indirect).

| Metric | Alias + keyword baseline (**measured**) | LLM (`--mode llm`) |
|---|---|---|
| Component precision / recall | 1.00 / 0.80 | _run it_ |
| Recall on explicitly named systems | 16 of 16 | _run it_ |
| Recall on indirectly referenced systems | **0 of 4** | _run it_ |
| End-to-end risk level accuracy | 14 of 17 (82%) | _run it_ |
| High-risk changes missed silently | 0 (3 flagged for review) | _run it_ |

**What the baseline tells you:** string matching handles every system a change names directly, and fails on 100% of indirect references ("the thing that sends receipts", "end-of-day processing window", "everything that talks to payments"). The worst miss is a credential rotation across Payments and the Customer DB, which touches the highest-blast-radius system in the catalog. The `Needs review` rule is what stops that from being rated Low. This is the gap an LLM should close, and the harness measures whether it does.

**The LLM column is empty on purpose.** I had no API key when building this. The LLM path is covered by offline tests with a faked model (including rejection of an invented system and an invented quote) but not by a live run.

## Limitations
- 17 hand-written, single-author-labelled requests against an invented catalog. This is a method demonstration, not a benchmark.
- The baseline's rollback and test keyword flags score 17 of 17 because I wrote them looking at this same data. They would not on real change records.
- The risk rules (criticality, blast-radius thresholds, one-level escalation for missing controls) are an illustrative policy. Replace them with your CAB's actual matrix.
- Quality is capped by the catalog. A stale or incomplete dependency map gives confident but wrong blast radii.
- Change records contain system and client details. Check your AI policy and redact before sending real text to an external model.

Created by Avash Mohanty, 2026
