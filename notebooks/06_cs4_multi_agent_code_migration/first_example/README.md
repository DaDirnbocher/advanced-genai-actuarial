# Case Study 4, first example: the article's original migration notebook

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/simonhatzesberger/advanced-genai-actuarial/blob/main/notebooks/06_cs4_multi_agent_code_migration/first_example/R_to_Python_Migration.ipynb)

The simplest way into Case Study 4. Five agents — **R Analysis**, **Translation**, **Compilation**,
**Test Runner** and **Report** — migrate an actuarial R script to Python. A **LangGraph** graph with fixed
edges decides the order and sends compilation or test failures back to the Translation Agent. A test
suite written and verified in advance judges the result; its expected values stay outside the
Translation Agent's context.

| Section | What happens |
|---|---|
| 3 | the tools, the five agents and the graph |
| 4 | **chain-ladder reserving** (198 lines of R) migrated to Python and checked by 14 tests (6 on the data, 8 on the numbers) |
| 5 | GLM-based reserving with bootstrap (265 lines of R, 15 tests) |
| 6 | a benchmark: each example migrated ten times |

The main notebook of the case study,
[`06_cs4_multi_agent_code_migration`](../06_cs4_multi_agent_code_migration.ipynb), builds on this one:
fenced tools, a hidden second triangle, GPT-6 models, a leak experiment and a second example on agentic
data analysis.

## Source and changes

This is the notebook published with the article

> Hatzesberger S, Nonneman I (2026) Advanced applications of generative AI in actuarial science: case
> studies beyond ChatGPT. *European Actuarial Journal* 16(2):481–523.
> <https://doi.org/10.1007/s13385-026-00464-9>

at [IAA-AITF/Actuarial-AI-Case-Studies](https://github.com/IAA-AITF/Actuarial-AI-Case-Studies)
(`case-studies/2026/actuarial_legacy_code_migration_multi-agent_system`, version 1.0 of 15 April 2026),
with its example scripts, data and tests. Three changes were made for the seminar, and nothing else:

1. The API key comes from Colab Secrets or the environment variable `OPENAI_API_KEY`; the `getpass`
   prompt is gone, so **Run all** never waits for input.
2. A cell that calls the models runs live only if a key is visible and its switch in section 2 is on
   (`RUN_SIMPLE_LIVE` on, `RUN_DIFFICULT_LIVE` and `RUN_BENCHMARK` off). Otherwise it loads the recorded
   run from `recorded/`, so the notebook runs from top to bottom without a key.
3. In Colab, the example, test and recorded files are fetched from this repository, and the packages are
   pinned as in the repository's `requirements.txt` (`langchain==1.4.3`, `langchain-openai==1.6.2`,
   `langgraph==1.2.11`).

The models are the article's: GPT-5.4 (`gpt-5.4-2026-03-05`) for the R Analysis and Translation Agents,
GPT-5.4 mini (`gpt-5.4-mini-2026-03-17`) for the other three.

**Saved outputs.** Sections 1 to 4 were run on 2 October 2026 with the seminar's environment: the
chain-ladder migration passed 14 of 14 tests at the first attempt, without a retry. Sections 5 and 6 keep
the outputs of the article's run of 15 April 2026 (the benchmark: 10 of 10 runs passed for each example).
Absolute local paths in the saved outputs were shortened to paths relative to this folder.

## Files

```
R_to_Python_Migration.ipynb   the notebook
examples/simple/              chain_ladder.R and triangle.csv
examples/difficult/           reserving_glm.R, claims_triangle.csv and policies.db (SQLite)
tests/                        the prespecified test suites, their expected values and conftest.py
recorded/                     the recorded runs: chain_ladder/ (2 October 2026), reserving_glm/ and
                              benchmark/ (15 April 2026)
```

Running the notebook writes `output/` (and, with the benchmark switched on, `benchmark_runs/`); both
are git-ignored. For the cells that compare R's output with Python's, an R installation with `Rscript`
is needed; without it, those cells say so and show the Python side only.

## Licence

The notebook, its code and its example and test files come from the article's repository, where code
and notebooks are licensed under the MIT licence (see [LICENSE](LICENSE), Copyright (c) 2025
International Actuarial Association) and textual material under CC BY 4.0. They keep those terms here.
