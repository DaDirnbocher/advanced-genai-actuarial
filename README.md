# Advanced Applications of Generative AI in Actuarial Science

Companion material for **EAA Seminar E0572**, held on **1–2 October 2026 in Vilnius, Lithuania**,
taught by **Dr Simon Hatzesberger**: eight Jupyter notebooks that you can read on this page and run
in your web browser, plus the article's original migration notebook as a first example for Case Study 4,
and the slides as a PDF.

**New here?** Do the short laptop check below before you travel. Everything else on this page can
wait until the seminar.

---

## Before the seminar: check your laptop

**What you need**

- a laptop with an up-to-date web browser (Chrome, Edge, Firefox or Safari), and its charger;
- a **Google account**, because the notebooks run in Google Colab; a free private account is fine;
- nothing else. You do not install anything, you do not need a GitHub account, and you do not need
  an API key: a shared key for the exercises is handed out in the room. No programming experience is
  assumed.

**The check** — please do it on the laptop you will bring.

1. Click this button. It opens the first notebook, `00_getting_started`, in Google Colab:

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/00_getting_started/00_getting_started.ipynb)

2. If Colab asks you to sign in, sign in with your Google account.
3. In Colab's menu bar, choose **Runtime → Run all**. Colab warns that the notebook was not authored
   by Google; click **Run anyway**. The notebook comes from this page; running it installs nothing and
   sends nothing to a language model.
4. Wait until every code cell shows its result, then scroll down to section 9, **Check your setup**.
   Its last line should read:

   ```
   Verdict: your setup is ready for the seminar - nothing to do.
   ```

That is all. On the way down, section 6 prints `[ATTENTION] No secret named OPENAI_API_KEY is
visible to this notebook.` That is expected: you add the seminar key in the room. If you have time,
read the notebook itself; it explains notebooks, Colab and API keys from the beginning.

**If something does not work**

- **Your company laptop blocks Colab or the Google sign-in.** Many company laptops do. Try your
  private Google account in the browser; if Colab still does not open, bring a private laptop.
- **Colab says it is not available for your account.** Company Google accounts can have Colab
  switched off by their administrator. Sign in with a private Google account instead.
- **Anything else**, including a line in section 9 that ends in `[ATTENTION]`: note what you see and
  bring it to the start of day 1, and we will sort it out.

---

## New to GitHub?

This page is a **GitHub repository**: a public folder of files. For the seminar you only need to
know five things.

- **No account is needed.** You can read, run and download everything without signing in to
  GitHub. You never need to *fork*, *clone* or *star* anything.
- **Reading a notebook.** Click a notebook's name in the table below. GitHub shows it with the
  outputs saved from our own runs: text, tables, charts and model answers. Large notebooks
  sometimes show an error on GitHub instead; open those in Colab, where the saved outputs appear as
  well.
- **Running a notebook.** Click its **Open in Colab** button. Colab fetches its own copy of the
  notebook, so nothing you change there affects this page. Your changes are not kept either, unless
  you choose **File → Save a copy in Drive** in Colab.
- **Downloading everything.** Only needed if you want to run the notebooks on your own computer
  instead of in Colab: the green **Code** button at the top of this page, then **Download ZIP**.
- **The folders.** Each notebook sits in its own folder under `notebooks/`, some with a `data/`
  folder of small files that the notebook reads by itself. You never need to open these by hand.

**Words you will meet**

| Word | What it means |
|---|---|
| Notebook | A document that mixes text, code and the results of that code; the file name ends in `.ipynb`. |
| Cell | One block of a notebook, either text or code. A code cell runs when you press **Shift+Enter**. |
| Google Colab | Google's free service that runs notebooks in your browser, on Google's computers. |
| Runtime | The temporary computer Colab lends you. After a while without activity it is reset; then run the notebook again from the top with **Runtime → Run all**. |
| API key | A password that lets code call a language model and bills the calls to the key's owner. Keep it private. |
| Repository | A folder of files and its history, here hosted on GitHub. |

---

## Notebooks

Each notebook belongs to one session of the seminar. **Read** opens it on GitHub, the button opens it
in Colab to run.

| Read | Run | Covers |
|---|---|---|
| [`00_getting_started`](notebooks/00_getting_started/00_getting_started.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/00_getting_started/00_getting_started.ipynb) | What a notebook is, running cells, Google Colab, and setting up your API key |
| [`01_llm_basics`](notebooks/01_llm_basics/01_llm_basics.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/01_llm_basics/01_llm_basics.ipynb) | Your first API call and the parameters you control, how a model picks its next token (greedy decoding, temperature and top-p on GPT-2 small), tokens and cost, prompt engineering, and the limitations of LLMs |
| [`02_llm_techniques`](notebooks/02_llm_techniques/02_llm_techniques.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/02_llm_techniques/02_llm_techniques.ipynb) | Structured outputs in three stages on ten synthetic motor insurance contracts (RISCBAC), with dates, booleans, an enum, optional fields, an ordered cover level and nested objects, checked by code; function calling that queries an SQLite database of mortality tables through two read-only tools; a real LoRA fine-tuning run; a signpost to retrieval-augmented generation; and when to reach for which technique |
| [`03_cs1_claims_text_features`](notebooks/03_cs1_claims_text_features/03_cs1_claims_text_features.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/03_cs1_claims_text_features/03_cs1_claims_text_features.ipynb) | Case Study 1: extracting body part, cause and number of body parts from one-line claim descriptions with structured outputs, a short introduction to machine learning with train/test split and error measures, and what the three fields add to a claim-cost model, plus exercises on designing your own feature and on cross-validation |
| [`04_cs2_rag_market_comparison`](notebooks/04_cs2_rag_market_comparison/04_cs2_rag_market_comparison.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/04_cs2_rag_market_comparison/04_cs2_rag_market_comparison.ipynb) | Case Study 2: retrieval-augmented generation over three insurers' annual reports: chunking, retrieval, structured outputs, exact-match scoring and a small model benchmark, plus an extra exercise on embeddings as pricing features |
| [`05_cs3_vehicle_damage_vision`](notebooks/05_cs3_vehicle_damage_vision/05_cs3_vehicle_damage_vision.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/05_cs3_vehicle_damage_vision/05_cs3_vehicle_damage_vision.ipynb) | Case Study 3: classifying vehicle damage from photos: a fine-tuned GPT-4o against zero-shot models, evaluation with intervals and a near-copy check, location and context, and a fraud-awareness exercise with a generated fake |
| [`06_cs4_multi_agent_code_migration`](notebooks/06_cs4_multi_agent_code_migration/06_cs4_multi_agent_code_migration.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/06_cs4_multi_agent_code_migration/06_cs4_multi_agent_code_migration.ipynb) | Case Study 4: five LLM agents migrate the article's R reserving scripts (chain ladder, GLM with bootstrap) to Python in a LangGraph graph: fenced tools, a test suite that runs the translation on a hidden second triangle, capped retries, the article's results next to what re-running them taught, a leak experiment, and a second example of agentic data analysis on freMTPL2 in which code checks every number; exercises on prompt injection, a VBA migration and a human approval node |
| [`06 … first_example`](notebooks/06_cs4_multi_agent_code_migration/first_example/R_to_Python_Migration.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/06_cs4_multi_agent_code_migration/first_example/R_to_Python_Migration.ipynb) | Case Study 4, first example: the article's original notebook. Five agents in a fixed LangGraph graph migrate a chain-ladder script (and a GLM with bootstrap) from R to Python, checked by a test suite written in advance; runs without a key on recorded runs |
| [`07_cs5_report_qa`](notebooks/07_cs5_report_qa/07_cs5_report_qa.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/07_cs5_report_qa/07_cs5_report_qa.ipynb) | Case Study 5: drafting the new SFCR policyholder part (Solvency II review) for a fictitious insurer, with code inserting every number and the prescribed text, then checking it: deterministic checks first, LLM checks that stay warnings unless code confirms them, planted and hold-out errors against a clean control, a judge measured on its own labelled test set, a Lithuanian machine translation with its checks, and a human sign-off; exercises on planting errors, writing a check and tuning the judge |

The notebooks ship **with their outputs saved**, so you can read what the models answered without
running anything. Re-running a cell replaces its output with a fresh answer.

### Apps

[`apps/cs2_market_comparison`](apps/cs2_market_comparison/) runs the Case Study 2 pipeline as a
step-by-step Streamlit app for the live demonstration. You do not need it to follow the seminar. Its
README explains the setup; it needs the same single OpenAI key as the notebooks.

[`apps/cs5_report_generation`](apps/cs5_report_generation/) drafts the SFCR sections E.1 (own funds) and
E.2 (SCR and MCR) for three fictitious insurers from Excel workbooks, in two ways — last year's text with
the figures updated, and a language model with the prior years' texts as examples — and puts both drafts
through the same checks. Its sample workbooks can be downloaded, edited and uploaded again, and it runs
without a key on recorded model runs. Its README explains the setup.

---

## Slides

[`slides/E0572_slides.pdf`](slides/E0572_slides.pdf) holds the slides of the seminar as presented on
1–2 October 2026: 126 slides, in the order of the two days. Each Live Demonstration slide carries a QR
code that opens the matching notebook in Colab. On slide 18 the model providers are named rather than
shown with their logos.

---

## About the seminar

Two days on applying Generative AI to real actuarial work — not chatbot demonstrations, but the
techniques that put a Large Language Model inside a process you can audit: structured outputs,
function calling, fine-tuning and retrieval-augmented generation, applied to five case studies.
Case Studies 1 to 3 and Part A of Case Study 4 follow a published article; Part B of Case Study 4
and Case Study 5 were written for this seminar.

The seminar's aims are to:

1. **Understand capabilities and limitations** — where Large Language Models add value, how they
   fail, and which risks matter in insurance.
2. **Choose the right approach** — when Generative AI fits, and when statistics, Machine Learning or
   conventional programming fit better.
3. **Build practical workflows** — combine models with documents, tools and agents.
4. **Evaluate results and retain control** — check output quality, trace results to sources, and
   build reproducibility and human review into every workflow.

---

## The two days

| Thursday, 1 October 2026 | |
|---|---|
| 09:00–09:15 | Introduction & Welcome |
| 09:15–11:00 | Foundations of Generative AI in Actuarial Practice |
| 11:15–12:45 | **Case Study 1** — Improving claim cost prediction with LLM-extracted features from unstructured data |
| 13:45–15:15 | **Case Study 2** — Market comparison using retrieval-augmented generation |
| 15:30–17:00 | **Case Study 3** — Image-based vehicle damage classification and localisation |

| Friday, 2 October 2026 | |
|---|---|
| 09:00–10:45 | **Case Study 4** — Multi-agent systems for actuarial code and data |
| 11:00–12:30 | **Case Study 5** — Report generation and quality assurance with Generative AI |
| 13:30–15:00 | Outlook and discussion: further applications, challenges and future developments |

---

## Running the notebooks

### In Google Colab — recommended, nothing to install

Click the **Open in Colab** button of a notebook, in the table above or at the top of the notebook
itself. Everything runs in your browser on one fixed Python setup, identical for everyone in the
room. There is nothing to install and nothing to configure.

### Locally — optional, for readers who already use Python

```bash
git clone https://github.com/simonhatzesberger/advanced-genai-actuarial.git
cd advanced-genai-actuarial
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

Without Git, download the ZIP instead (green **Code** button → **Download ZIP**), unpack it, and
open a terminal in the unpacked folder `advanced-genai-actuarial-main`; then start from the third
line.

Python 3.12 or 3.13. One `requirements.txt` covers all the notebooks. It includes `torch`,
`transformers`, `peft`, `datasets` and `accelerate` for the two sections that run a small open model
on the machine itself: GPT-2 small in `01_llm_basics` (about 551 MB, almost all of it model weights,
downloaded on first use) and a LoRA fine-tuning run in `02_llm_techniques` (about 1 GB). On Linux,
pip installs the CUDA build of `torch` by default, a larger download; the CPU build, installed as
described on <https://pytorch.org/get-started/locally/>, is enough here. **Do not** run the install
command inside Colab — Colab already ships most of the scientific stack, and each notebook's setup
cell installs only what is missing there.

Small files a notebook needs — a 3,000-claim sample, recorded model answers, the case-study bundles —
are committed in a `data/` folder next to it, and its `README.md` gives each file's source.
Files a notebook downloads or builds on its first run — annual reports, claim photos, the freMTPL2
portfolio, embedding caches — land in a `_local/` folder next to it. That folder is git-ignored: those
files are fetched from where they are published and are not redistributed here. The saved outputs
quote from them where a lesson needs it: `04_cs2_rag_market_comparison` prints the report passages it
retrieved, and `05_cs3_vehicle_damage_vision` shows twelve of the claim photos as thumbnails of at most
256 pixels. The weights of the two small open models in `01_llm_basics` and `02_llm_techniques` go to
the Hugging Face cache of the machine that runs the notebook.

---

## Your API key

**You can read every notebook without a key.** They are committed with their outputs saved, so the
answers the models gave are there on the page. Nothing is needed to follow along.

**To call a model yourself, you need a key.** In the room you receive a shared seminar key; it is
temporary, spend-capped and revoked when the seminar ends. The notebooks look for it under the name
`OPENAI_API_KEY`, first in **Colab Secrets**, then in an environment variable. `00_getting_started`,
section 6, walks through Colab Secrets step by step. On your own machine, set the variable in the
terminal, then start `jupyter lab` from the same window:

- macOS and Linux: `export OPENAI_API_KEY="your-key-here"`
- Windows PowerShell: `$env:OPENAI_API_KEY = "your-key-here"`

The variable lasts as long as that terminal. The notebooks do not read a `.env` file; the Case Study 2
app has a key lookup of its own, described in its README.

<details>
<summary>Seminar code (for use in the room)</summary>

```text
Hl3Z1R18m0Lu-BZaH8rDYB_JvyUtL7zA1y4ApGLD58F6SbuDbdByZwAseX8CSRD_mbyYxD7ItNT3BlbkFJc1xb-QYN0MuttRGqJ1XPesFYLmaWwaqeqaDfInsYWhZc1ODyT2r_SfWLqVQI6iA46rM_
```

In the room you are told what to put in front of these lines and which 6 characters to add at the end.
</details>

**What a run costs.** `00_getting_started`, `01_llm_basics` and `02_llm_techniques` call a deliberately
cheap model: the one call in `00_getting_started` stays off until you switch it on, `01_llm_basics`
costs well under a cent, and the 19 requests of `02_llm_techniques` cost USD 0.0116 in its saved run.
Without a key, `02_llm_techniques` replays the replies of that run from `data/`. Each case study states
at the top what running it costs. At list prices, the saved runs cost USD 0.031 (Case Study 1),
USD 0.54 (Case Study 2, about USD 0.65 on a first run), USD 0.13 (Case Study 3), USD 0.0998 (Case
Study 4) and USD 0.0094 (Case Study 5). Work too slow or too expensive to repeat in the room was
recorded once: Case Studies 1, 3, 4 and 5 read it from `data/` and repeat it only if you switch it on.

Three rules for the seminar key, and for any key of your own:

- **Keep it private.** Colab Secrets or an environment variable — never in a notebook cell, a
  screenshot or a commit.
- **Keep usage small.** Seminar examples only, no bulk jobs.
- **Send no real data.** No company, client or personal data goes to a model during this seminar.

---

## Repository structure

```
advanced-genai-actuarial/
│
├── README.md                              ← you are here
├── requirements.txt                       ← one package list for the notebooks
├── LICENSE                                ← MIT, for the code
├── LICENSE-CONTENT.md                     ← CC BY 4.0, for the prose and figures
├── .gitignore
│
├── notebooks/
│   ├── 00_getting_started/
│   │   └── 00_getting_started.ipynb
│   ├── 01_llm_basics/
│   │   └── 01_llm_basics.ipynb
│   ├── 02_llm_techniques/
│   │   ├── 02_llm_techniques.ipynb
│   │   └── data/                          ← synthetic contracts, a mortality-table database, recorded replies
│   ├── 03_cs1_claims_text_features/
│   │   ├── 03_cs1_claims_text_features.ipynb
│   │   └── data/                          ← 3,000 claims and the recorded extractions
│   ├── 04_cs2_rag_market_comparison/
│   │   └── 04_cs2_rag_market_comparison.ipynb
│   ├── 05_cs3_vehicle_damage_vision/
│   │   ├── 05_cs3_vehicle_damage_vision.ipynb
│   │   └── data/                          ← recorded predictions and the near-copy screen
│   ├── 06_cs4_multi_agent_code_migration/
│   │   ├── 06_cs4_multi_agent_code_migration.ipynb
│   │   ├── first_example/                 ← the article's original notebook, with its R scripts, tests and recorded runs
│   │   └── data/                          ← case-study bundle and recorded runs
│   └── 07_cs5_report_qa/
│       ├── 07_cs5_report_qa.ipynb
│       └── data/                          ← case-study bundle and recorded runs
│
├── slides/
│   └── E0572_slides.pdf                   ← the slides as presented, 1–2 October 2026
│
└── apps/
    ├── cs2_market_comparison/             ← the Case Study 2 pipeline as a Streamlit app
    └── cs5_report_generation/             ← Case Study 5: drafting and checking SFCR E.1 and E.2, with sample workbooks
```

Each notebook folder holds one Jupyter notebook, saved with its outputs. Where a notebook reads small
committed files, they sit in a `data/` folder next to it, with a `README.md` giving their sources.

---

## The article behind the case studies

Case Studies 1 to 4 are built on:

> Hatzesberger S, Nonneman I (2026) Advanced applications of generative AI in actuarial science:
> case studies beyond ChatGPT. *European Actuarial Journal* 16(2):481–523.
> <https://doi.org/10.1007/s13385-026-00464-9>

Part B of Case Study 4, a data analysis on freMTPL2, is not from the article. Neither is Case Study 5,
which takes up a proposal in Sect. 7.2 of the article; both were written for this seminar.

The article's own code is published separately at
<https://github.com/IAA-AITF/Actuarial-AI-Case-Studies>. This repository is the seminar's teaching
version of that material: reworked for a two-day classroom, re-recorded against current models, and
extended with exercises.

---

## Licences

| What | Licence |
|---|---|
| Code | MIT — see [LICENSE](LICENSE) |
| Prose, notebook markdown, figures | CC BY 4.0 — see [LICENSE-CONTENT.md](LICENSE-CONTENT.md) |
| Slides | CC BY 4.0 for the author's own text and figures — see [LICENSE-CONTENT.md](LICENSE-CONTENT.md) |

Neither licence covers EAA branding, material adapted from the article above, third-party datasets,
the third-party material the slides quote, or the installed dependencies.
[LICENSE-CONTENT.md](LICENSE-CONTENT.md) sets out each exception, and each notebook's `data/README.md`
gives the source of the files in its folder.

---

## Contact

Questions about the material: **Dr Simon Hatzesberger** — <https://github.com/simonhatzesberger>

Questions about the seminar itself, registration or logistics: the
[European Actuarial Academy](https://actuarial-academy.com/).
