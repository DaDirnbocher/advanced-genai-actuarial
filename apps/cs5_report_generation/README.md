# Case Study 5 — live demo: report generation for SFCR sections E.1 and E.2

A step-by-step Streamlit app for the room. It drafts the capital-management sections of a Solvency and Financial
Condition Report (SFCR) — **E.1 Own funds** and **E.2 Solvency Capital Requirement and Minimum Capital
Requirement** (Annex XX and Art. 297 of Delegated Regulation (EU) 2015/35) — from figures in Excel and the driver
bullets of the finance and risk teams. It does so twice:

- **the old way**: last year's published text, with every figure updated by code;
- **the new way**: a language model (GPT-6 Luna) with 0 to 4 prior years' texts as examples, while code owns every
  number,

and then puts both drafts through the same checks. It is the companion to the notebook
[`notebooks/07_cs5_report_qa`](../../notebooks/07_cs5_report_qa/07_cs5_report_qa.ipynb), which drafts and checks the
new policyholder part of the SFCR. The app takes the part for market professionals and the year-to-year routine of
writing it.

**Why E.1 and E.2.** Every Solvency II insurer writes these sections every year, and the year-to-year work is always
the same: the boilerplate stays, the figures change, and the movements and their causes have to be described anew.
The new SFCR format (Delegated Regulation (EU) 2026/269) applies from 30 January 2027. EIOPA's stated view — not a
provision — is that the SFCR for financial year 2027 is the first in the new format, so a year-end 2026 report still
follows this structure.

---

## What the app shows, step by step

| Step | What happens on screen |
|---|---|
| **0 — Company** | Pick one of three fictitious insurers, or upload a workbook of your own. Each sample can be downloaded, changed in Excel and uploaded again. |
| **1 — Figures** | Figures for 2021 to 2026. Code derives every total, the own funds eligible under the tier limits (Art. 82) and every ratio; nothing derived is typed. The movements of 2026, with the house phrase for each, and the facts catalogue: every figure as a `{{placeholder}}`. |
| **2 — Earlier years** | The E.1 and E.2 texts published for 2022 to 2025, next to the bullets they draw on, with every figure highlighted. A table shows which blocks stay word for word the same each year (boilerplate) and which are rewritten. |
| **3 — Drafting 2026** | **A**: the 2025 text with the 2026 figures. **B**: GPT-6 Luna with 0 to 4 prior years as examples and a switch for the house rules (movement phrases and terminology from the workbook). Code checks the draft — placeholders, typed digits, directions, dates and, if switched on, the house rules — and returns it once with feedback before it fills in the numbers. |
| **4 — Checks** | The same checks on both drafts: figures, years, dates, movement words, house phrases, ratios in percentage points, terminology, the elements of Art. 297, whether each cause can be traced to a bullet of the year, and whether each bullet is reflected. Optionally an independent LLM check judges the causes; code looks up every quote it gives. |
| **5 — Review** | Edit the text, watch the checks run again, sign off, and download the result as Word (.docx) or Markdown, with both tables, the remaining findings and the sign-off. |

**What to look for.** The old way gets every figure right and still produces errors: "The SCR increased slightly"
for an SCR that fell, causes carried over from last year, and dates shifted by the find-and-replace ("notes issued in
March 2025" for notes issued in March 2024). The model with no example writes a correct but foreign text (about 900
words; wording similarity to last year about 0.3–0.4); with one to four prior years it writes in the insurer's own words
(similarity about 0.8–0.9). The house-rules switch decides who chooses the movement words: with the rules on, every
recorded draft follows the house phrases; with them off, the checks report 1 to 15 deviations per draft.

---

## The three sample workbooks

All three insurers are fictitious and all figures are synthetic. `samples/` holds one workbook each:

| Workbook | Insurer | Story |
|---|---|---|
| `brisendale_mutual.xlsx` | Brisendale Mutual, non-life mutual (Ireland) | The insurer of the notebook; its 2025 and 2026 figures and its 2026 bullets DR1–DR6 are the notebook's. A motor quota share cuts insurance risk; the SCR coverage ratio rises from 204% to 220%. |
| `tallowmere_life.xlsx` | Tallowmere Life, life insurer (Austria) | Interest rates drive own funds; subordinated notes issued in 2024. Falling rates in 2026 take the ratio from 188% to 166%. |
| `quillbrook_insurance.xlsx` | Quillbrook Insurance, composite (Lithuania) | The tier limits cap eligible own funds; a hailstorm hits 2026 and the ratio falls from 139% to 133%, below the risk appetite of 140%. |

Each workbook has six sheets: **Company** (text facts and the risk appetite), **Figures** (EUR million, 2021–2026;
yellow cells are inputs, grey cells are formulas that the app ignores and recomputes), **Bullets** (the driver
bullets, 2022–2026), **Narratives** (the E.1 and E.2 texts published for 2022–2025, one row per text block, with the
bullets each block draws on), **House phrases** and **Terminology**. The year to draft is the last year with figures
and bullets but no text. A workbook of your own needs the same sheets and column names; the easiest start is a sample.

`tools/make_samples.py` builds the three workbooks. It writes every published text as a template with placeholders,
renders it, and asserts that the app reads back exactly the intended placeholder for every figure; the published
texts of 2022 to 2025 pass every check of the app.

---

## Setup

From this folder:

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` holds only what this app needs; its pins match the repository's root `requirements.txt` and the
Case Study 2 app, plus `openpyxl` (reading the workbooks) and `python-docx` (the Word export).

### One key: `OPENAI_API_KEY`

Only the LLM steps need a key; everything else runs without one. The app looks for the key in the environment
variable `OPENAI_API_KEY`, then in a `.env` file in this folder (copy `.env.example`), then in a password field in
Step 0. The key is never shown, logged or written to disk.

**Without a key or without internet** the app shows recorded runs for the three sample workbooks: one GPT-6 Luna
draft for every setting (0 to 4 prior years, house rules on and off) and the LLM check of the causes for each draft
and for the old-way text. They were recorded on 1 October 2026 with `tools/record_runs.py` and are kept in
`recordings.json`; together they cost USD 0.063. A recording is used only for an unchanged sample workbook.

### Cost

GPT-6 Luna, reasoning effort `none`, temperature 0, `store=False`, at USD 0.10 per million input tokens and USD 0.50
per million output tokens (list prices of 22 September 2026, as in the notebook). A draft with four prior years costs
about USD 0.002 (about 10,000 input and 1,600 output tokens; a revision round doubles it); a check of the causes about
USD 0.0002. The session is capped at USD 0.50, checked before every call.

---

## Starting it in the room

```bash
cd apps/cs5_report_generation
streamlit run app.py
```

The app opens at <http://localhost:8502> (the Case Study 2 app uses 8501, so both can run side by side).
`python app.py` works too. Start it **from this folder**: Streamlit reads the seminar theme and the port from
`.streamlit/config.toml` in the folder it is started from. **Restart** in the header resets the demo.

---

## The checks

| Check | What it checks |
|---|---|
| `N-LINK` | every number belongs to a figure of the reporting year or to its driver bullets; a figure of an earlier year is named |
| `N-YEAR` | every year is the reporting year or the previous one, or a dated event the workbook confirms |
| `N-DATE` | every month and year ("March 2024") matches the Company sheet or a driver bullet |
| `T-DIR` | every movement word matches the direction of the change |
| `T-HOUSE` | every quantified movement uses the house phrase for its size |
| `R-PP` | a change of a ratio is given in percentage points, not per cent |
| `C-CAUSE` | every stated cause can be traced to a bullet of the year, and not only to a bullet of an earlier year |
| `B-COVER` | every bullet of the year is reflected in the text, or left out on purpose |
| `G-TERM` | the house terms are used, and none of the terms to avoid |
| `E-ELEM` | the elements of Art. 297(1) and (2) are there |
| `L-CAUSE` | optional LLM check: every cause is supported by a bullet of the year; code grounds the quotes |

The checks are heuristics written for these texts. They find what the room should discuss; they do not replace the
review, and Step 5 makes that explicit.

---

## Files

```
app.py               Streamlit interface (Steps 0-5)
report_core.py       figures, workbook reader, placeholders, the old method, the checks; no Streamlit, no model
drafting.py          the drafting prompt, the drafting gate, the LLM check of causes, recordings
export.py            Word and Markdown export
config.py            sample workbooks, captions, the seminar look
samples/             the three workbooks
recordings.json      recorded LLM runs for the samples
tools/               make_samples.py (builds the workbooks), record_runs.py (records the LLM runs)
.streamlit/          theme and port
.env.example         template for the local key file
```

Brisendale Mutual, Tallowmere Life and Quillbrook Insurance are fictitious insurers created for teaching; all figures
are synthetic, and every supervisory authority is a placeholder.
