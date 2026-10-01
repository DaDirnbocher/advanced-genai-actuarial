"""Case Study 5 report app: the LLM steps. GPT-6 Luna drafts E.1 and E.2 with the prior years' texts as examples;
code checks the draft (the drafting gate) and fills in every number; a second, independent call checks the stated
causes against the driver bullets. No Streamlit here.

Each call is one structured-output request on the plain OpenAI Responses API, with store=False, reasoning effort
"none" and temperature 0, as in the Case Study 5 notebook. Recorded runs for the sample workbooks are kept in
recordings.json, so that the app shows a draft without a key or without internet.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import random
import re
import time
from pathlib import Path
from typing import Any

import report_core as rc

MODEL = "gpt-6-luna"
EFFORT = "none"            # GPT-6 accepts a temperature only at reasoning effort "none"
TEMPERATURE = 0
# USD per million tokens, standard processing, as in the Case Study 5 notebook (OpenAI pricing page, 22 September
# 2026): input, cached input, input written to the cache, output.
PRICES = (0.10, 0.01, 0.125, 0.50)
MAX_OUTPUT_TOKENS = 6000
RECORDINGS_PATH = Path(__file__).resolve().parent / "recordings.json"

# ---------------------------------------------------------------------------
# The drafting prompt
# ---------------------------------------------------------------------------

SLOT_BRIEF = {
    "e1_policy": "Art. 297(1)(a): objectives, policies and processes for managing own funds, the time horizon used for "
                 "business planning, and any material change over the reporting period.",
    "e1_structure": "Art. 297(1)(b): structure, amount and quality of own funds by tier at the end of the reporting "
                    "period and of the previous one, with the significant changes in each tier and their reasons; "
                    "Art. 297(1)(g): ancillary own funds (say so if there are none). Code inserts Table E.1 after "
                    "this slot.",
    "e1_eligibility": "Art. 297(1)(c) and (d): eligible own funds to cover the SCR and the MCR, and how the tier "
                      "limits apply; Art. 297(1)(h): items deducted from own funds and restrictions on their "
                      "availability (say so if there are none).",
    "e1_reconciliation": "Art. 297(1)(e): the differences between equity in the financial statements and the excess "
                         "of assets over liabilities, with their amounts.",
    "e2_amounts": "Art. 297(2)(a) and (b): the SCR and the MCR at the end of the reporting period and of the previous "
                  "one, and the coverage ratios; code inserts Table E.2 (SCR by risk module) after this slot.",
    "e2_methods": "Art. 297(2)(c), (d), (f) and (g): standard formula or internal model, simplified calculations, "
                  "undertaking-specific parameters, capital add-on and the inputs used to calculate the MCR.",
    "e2_changes": "Art. 297(2)(h): material changes to the SCR and the MCR over the reporting period, by risk module, "
                  "and their reasons.",
}

DRAFT_PROMPT = """You draft sections E.1 (Own funds) and E.2 (Solvency Capital Requirement and Minimum Capital
Requirement) of the Solvency and Financial Condition Report (SFCR) of the insurer described below, for the
reporting year, for market professionals and the supervisor. You write only the seven text slots listed in the
user message. Code inserts Table E.1 (own funds by tier, available and eligible) after the slot e1_structure and
Table E.2 (SCR by risk module, MCR and coverage ratios) after the slot e2_amounts; you may refer to both tables.

Rules (code checks each one; a draft that breaks one comes back to you once):
1. NUMBERS. Every number, percentage, year and date is a placeholder {{ID}} copied exactly from the facts
   catalogue of the reporting year. Code replaces it by the value WITH its unit: {{scr_cur}} becomes
   "EUR 373.1 million", {{cov_scr_cur}} becomes "220%", {{cov_scr_change_pp}} becomes "16 percentage points",
   {{date_cur}} becomes "31 December 2026". So never type a digit, and never write a unit ("EUR", "%", "per cent",
   "million", "percentage points") next to a placeholder. Only "Tier 1", "Tier 2", "Tier 3", "Table E.1" and
   "Table E.2" may contain digits. Do not use number words ("two", "doubled", "a third") for figures either.
2. CHANGES. A change placeholder (IDs ending in _change_pct, _change_eur or _change_pp) gives only the size of the
   change. The direction you write must match the direction in the catalogue. For a ratio, use the _change_pp
   placeholder, never a per cent change.
3. PERIODS. Tie every figure to its year-end or year in the same sentence, e.g. "at {{date_cur}}" or
   "({{year_prev}}: {{scr_prev}})".
4. CAUSES. State a cause only where a driver bullet of the reporting year supports it, and never carry a cause over
   from an earlier year. Where a bullet says that the reasons are not known or not yet analysed, say exactly that.
   Something that happens after the reporting year-end (a plan, a cover that starts later) did not change any
   figure of the reporting year. In bullet_decisions, account for every bullet of the reporting year: the slot that
   uses it, or "not used" and why. In causal_claims, list every sentence that states a cause (because, due to,
   driven by, as a result of, reflecting, owing to, ...), copied exactly, with the bullet it rests on.
5. CONSISTENCY. {consistency_rule}
6. WORDING. {wording_rule}
7. LENGTH. About 450 to 700 words across the seven slots, in short paragraphs; separate paragraphs within a slot by a
   blank line. No headings, no bullet lists, no tables in the slots.

Return JSON with the seven slots, bullet_decisions and causal_claims. If you receive feedback on a draft, return the
complete corrected JSON."""

CONSISTENCY_WITH_EXAMPLES = (
    "The texts this insurer published for earlier years follow in the user message as examples, with their figures "
    "as placeholders (in an example, _cur means that example's year and _prev the year before). Keep their "
    "structure, their terminology and their sentence patterns wherever this year's facts allow, so that this year's "
    "text reads like the earlier ones. But update every movement and every cause to the reporting year: an example "
    "shows how the insurer writes, not what happened this year.")
CONSISTENCY_WITHOUT_EXAMPLES = (
    "There are no earlier texts to follow. Write in a neutral, factual style for market professionals.")
WORDING_RULES_ON = (
    "HOUSE RULES. Describe the movement of each figure with exactly the house phrase that the catalogue gives for its "
    "change (for example 'decreased slightly'), and use the house terms. Never use a term that the terminology "
    "list says to avoid.")
WORDING_RULES_OFF = "Choose the words for movements and the terms yourself."

TEXT_FACT_KEYS = ["company_name", "legal_form", "lines_of_business", "home_member_state", "capital_policy",
                  "planning_horizon", "tier1_items", "tier2_items", "tier3_items", "ancillary_own_funds",
                  "deductions_restrictions", "calculation", "simplifications", "undertaking_specific_parameters",
                  "capital_add_on", "mcr_inputs"]


def instructions(n_examples: int, house_rules: bool) -> str:
    return DRAFT_PROMPT.replace("{consistency_rule}", CONSISTENCY_WITH_EXAMPLES if n_examples else
                                CONSISTENCY_WITHOUT_EXAMPLES).replace(
        "{wording_rule}", WORDING_RULES_ON if house_rules else WORDING_RULES_OFF)


def catalogue(facts: dict[str, rc.Fact], house_rules: bool) -> str:
    lines = []
    for f in facts.values():
        meaning = f.label
        if f.kind == "level":
            meaning += " at the end of " + ("the reporting year" if f.period == "cur" else "the previous year")
        elif f.kind.startswith("change"):
            meaning = f"change of the {f.label} from the previous year (size only)"
        extra = f" | direction: {f.direction}" if f.direction else ""
        if house_rules and f.phrase:
            extra += f" | house phrase: {f.phrase}"
        lines.append(f"{{{{{f.id}}}}} = {f.display} | {meaning}{extra}")
    return "\n".join(lines)


def movement_summary(company: rc.Company, year: int) -> str:
    facts = rc.facts_for(company, year)
    rows = []
    for mid, f in rc.movements(facts).items():
        if mid in ("of_total", "bscr") or not rc.METRIC[mid].movement:
            continue
        rows.append(f"- {rc.METRIC[mid].label}: {f.direction} {f.display}")
    return "\n".join(rows)


def example_block(company: rc.Company, year: int) -> str:
    facts = rc.facts_for(company, year)
    parts = [f"=== Example: {year} ===", "Movements of the year:", movement_summary(company, year),
             "Driver bullets of the year:"]
    parts += [f"[{b['id']}] {b['topic']}: {b['text']}" for b in company.bullets.get(year, [])]
    parts.append("Published text, figures as placeholders:")
    for slot, text in company.slots(year).items():
        template, _ = rc.templatize(text, facts)
        parts.append(f"{slot}: {template}")
    return "\n".join(parts)


def user_message(company: rc.Company, year: int, n_examples: int, house_rules: bool) -> str:
    facts = rc.facts_for(company, year)
    text_facts = {k: company.text.get(k, "") for k in TEXT_FACT_KEYS if company.text.get(k)}
    out = ["INSURER (text facts)", json.dumps(text_facts, indent=1, ensure_ascii=False), ""]
    history = [y for y in sorted(company.history_years, reverse=True) if y < year][:n_examples]
    if history:
        out.append("EXAMPLES: TEXTS PUBLISHED FOR EARLIER YEARS (most recent first)")
        out += [example_block(company, y) for y in history]
        out.append("")
    out += [f"REPORTING YEAR {year}: SLOTS TO WRITE"]
    out += [f"- {k}: {v}" for k, v in SLOT_BRIEF.items()]
    out += ["", f"FACTS CATALOGUE {year} (placeholder = rendered value | meaning | direction"
                + (" | house phrase)" if house_rules else ")"), catalogue(facts, house_rules), ""]
    if house_rules and company.terminology:
        out.append("TERMINOLOGY (house term: terms to avoid)")
        out += [f"- {t['preferred']}: avoid {', '.join(t['avoid'])}" for t in company.terminology]
        out.append("")
    out.append(f"DRIVER BULLETS {year}")
    out += [f"[{b['id']}] {b['topic']}: {b['text']}" for b in company.bullets.get(year, [])]
    return "\n".join(out)


def draft_schema(company: rc.Company, year: int) -> dict:
    ids = [b["id"] for b in company.bullets.get(year, [])]
    slots = {s: {"type": "string"} for s in rc.SLOT_IDS}
    decision = _obj({"bullet_id": {"type": "string", "enum": ids},
                     "used_in": {"type": "string", "enum": rc.SLOT_IDS + ["not used"]},
                     "note": {"type": "string"}})
    claim = _obj({"sentence": {"type": "string"}, "bullet_id": {"type": "string", "enum": ids + ["none"]}})
    schema = _obj({**slots, "bullet_decisions": {"type": "array", "items": decision},
                   "causal_claims": {"type": "array", "items": claim}})
    return {"name": "sfcr_e1_e2_draft", "strict": True, "schema": schema}


def _obj(props: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "properties": props, "required": list(props)}


# ---------------------------------------------------------------------------
# The drafting gate (code)
# ---------------------------------------------------------------------------

UNIT_NEAR = re.compile(r"\{\{[^{}]+\}\}\s*(?:%|per ?cent|percentage points?|million|bn|EUR|euros?)\b|"
                       r"(?:EUR|€)\s*\{\{", re.IGNORECASE)
ALLOWED_DIGITS = re.compile(r"\b(?:Tier\s?[123]|Table\s?E\.[12]|E\.[1-6])\b")
NUMBER_WORDS = re.compile(r"\b(?:twice|doubled|halved|tripled|a third|a quarter|one-third|one-quarter)\b",
                          re.IGNORECASE)


def gate(company: rc.Company, year: int, draft: dict, house_rules: bool) -> dict:
    """What code checks before it accepts a draft: placeholders, typed digits, units, directions, the house rules
    (if switched on), the bullet decisions and the causal claims. Errors go back to the model once."""
    facts = rc.facts_for(company, year)
    errors, warnings = [], []
    for slot in rc.SLOT_IDS:
        text = draft.get(slot, "") or ""
        if len(text.split()) < 8:
            errors.append(f"slot {slot} is empty or shorter than 8 words")
        for pid in sorted(set(rc.PLACEHOLDER.findall(text))):
            if pid not in facts:
                near = difflib.get_close_matches(pid, list(facts), n=2)
                errors.append(f"{slot}: unknown placeholder {{{{{pid}}}}}"
                              + (f"; did you mean {', '.join('{{' + n + '}}' for n in near)}?" if near else ""))
        rest = ALLOWED_DIGITS.sub(" ", rc.PLACEHOLDER.sub(" ", text))
        for sentence in rc.split_sentences(rest):
            digits = re.findall(r"\S*\d\S*", sentence)
            if digits:
                errors.append(f"{slot}: digit(s) {digits} outside a placeholder in {sentence[:140]!r}; "
                              "use a placeholder or rephrase")
        for m in UNIT_NEAR.finditer(text):
            errors.append(f"{slot}: unit next to a placeholder in {text[max(0, m.start() - 30):m.end() + 10]!r}; "
                          "code renders the unit, remove it")
        for m in NUMBER_WORDS.finditer(text):
            warnings.append(f"{slot}: number word {m.group(0)!r}")
    rendered = {s: rc.render(draft.get(s, "") or "", facts) for s in rc.SLOT_IDS}
    for f in rc.run_checks(company, year, rendered):
        if f.check in ("T-DIR", "R-PP", "N-DATE") and f.severity == "error":
            errors.append(f"{f.slot}: {f.message} - in {f.quote[:140]!r}")
        elif f.check in ("T-HOUSE", "G-TERM") and house_rules:
            errors.append(f"{f.slot}: {f.message} - in {f.quote[:140]!r}")
    ids = [b["id"] for b in company.bullets.get(year, [])]
    decided = {d.get("bullet_id") for d in draft.get("bullet_decisions", [])}
    for bid in ids:
        if bid not in decided:
            errors.append(f"bullet_decisions: no decision for bullet {bid}")
    alltext = _norm(" ".join(draft.get(s, "") or "" for s in rc.SLOT_IDS))
    for c in draft.get("causal_claims", []):
        if _norm(c.get("sentence", "")) not in alltext:
            errors.append(f"causal_claims: sentence not found verbatim in the slots: {c.get('sentence', '')[:120]!r}")
    return {"passed": not errors, "errors": errors, "warnings": warnings,
            "placeholders": sum(len(rc.PLACEHOLDER.findall(draft.get(s, "") or "")) for s in rc.SLOT_IDS)}


def _norm(text: str) -> str:
    return " ".join(text.replace("“", '"').replace("”", '"').replace("’", "'").split()).lower()


# ---------------------------------------------------------------------------
# One structured call
# ---------------------------------------------------------------------------

def cost_usd(usage: dict) -> float:
    p_in, p_cached, p_write, p_out = PRICES
    ordinary = usage["input_tokens"] - usage["cached_tokens"] - usage["cache_write_tokens"]
    return (ordinary * p_in + usage["cached_tokens"] * p_cached + usage["cache_write_tokens"] * p_write
            + usage["output_tokens"] * p_out) / 1e6


def _usage(response) -> dict:
    u = response.usage
    details = getattr(u, "input_tokens_details", None)
    cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
    write = getattr(details, "cache_write_tokens", None) if details else None
    if write is None and details is not None:
        write = (getattr(details, "model_extra", None) or {}).get("cache_write_tokens", 0)
    return {"input_tokens": u.input_tokens, "cached_tokens": cached, "cache_write_tokens": write or 0,
            "output_tokens": u.output_tokens}


def worst_case_usd(instructions_text: str, user_text: str, max_output_tokens: int = MAX_OUTPUT_TOKENS) -> float:
    """An upper estimate of a call's cost before it is sent: about 3 characters per input token, and the most output
    the call may return."""
    est_in = (len(instructions_text) + len(user_text)) // 3 + 200
    return (est_in * PRICES[0] + max_output_tokens * PRICES[3]) / 1e6


def call(client, instructions_text: str, items: list[dict], schema: dict,
         max_output_tokens: int = MAX_OUTPUT_TOKENS) -> dict:
    """One structured call with up to four retries on rate limits and passing network trouble. Never raises."""
    import openai
    retryable = (openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError, openai.InternalServerError)
    kwargs = dict(model=MODEL, instructions=instructions_text, input=items, store=False,
                  max_output_tokens=max_output_tokens, text={"format": {"type": "json_schema", **schema}},
                  reasoning={"effort": EFFORT}, temperature=TEMPERATURE)
    t0 = time.time()
    for attempt in range(1, 6):
        try:
            response = client.responses.create(**kwargs)
            break
        except retryable as exc:
            if "insufficient_quota" in str(exc):
                return {"status": "no_credit", "error": "no credit left on this key", "seconds": time.time() - t0}
            if attempt == 5:
                return {"status": "api_error", "error": short_error(exc), "seconds": time.time() - t0}
            time.sleep(2 ** attempt + random.uniform(0, 1))
        except Exception as exc:  # a refused request: a bad parameter, a model the key cannot use, a wrong key
            return {"status": "api_error", "error": short_error(exc), "seconds": time.time() - t0}
    usage = _usage(response)
    out = {"status": "ok", "error": None, "seconds": round(time.time() - t0, 2), "usage": usage,
           "usd": round(cost_usd(usage), 6), "model": getattr(response, "model", MODEL),
           "output_text": response.output_text}
    if response.status == "incomplete":
        out.update(status="api_error", error=f"incomplete response: {response.incomplete_details}")
        return out
    try:
        out["parsed"] = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError) as exc:
        out.update(status="api_error", error=f"output is not valid JSON: {exc}")
    return out


def short_error(exc: Exception) -> str:
    """One line describing a failed call. It never repeats a key, not even a masked one."""
    text = re.sub(r"sk-[A-Za-z0-9_\-*]{4,}", "sk-***", " ".join(str(exc).split()))
    return f"{type(exc).__name__}: {text[:160]}"


def fingerprint(*parts: Any) -> str:
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# The draft: one call, the gate, at most one revision
# ---------------------------------------------------------------------------

def run_draft(client, company: rc.Company, year: int, n_examples: int, house_rules: bool,
              max_revisions: int = 1) -> dict:
    instr = instructions(n_examples, house_rules)
    user = user_message(company, year, n_examples, house_rules)
    schema = draft_schema(company, year)
    items: list[dict] = [{"role": "user", "content": [{"type": "input_text", "text": user}]}]
    attempts, draft = [], None
    for attempt in range(max_revisions + 1):
        res = call(client, instr, items, schema)
        rec = {"attempt": attempt + 1, "status": res["status"], "error": res.get("error"),
               "usage": res.get("usage"), "usd": res.get("usd", 0.0), "seconds": res.get("seconds", 0.0)}
        if res["status"] != "ok":
            attempts.append(rec)
            break
        draft = res["parsed"]
        for s in rc.SLOT_IDS:  # registry IDs have no spaces; code removes whitespace inside {{ }}
            draft[s] = re.sub(r"\{\{([^{}]*)\}\}", lambda m: "{{" + re.sub(r"\s+", "", m.group(1)) + "}}",
                              draft.get(s, "") or "")
        rec["draft"] = draft
        rec["gate"] = gate(company, year, draft, house_rules)
        attempts.append(rec)
        if rec["gate"]["passed"] or attempt == max_revisions:
            break
        feedback = "Feedback on your draft; return the complete corrected JSON:\n- " + "\n- ".join(rec["gate"]["errors"])
        items += [{"role": "assistant", "content": [{"type": "output_text", "text": res["output_text"]}]},
                  {"role": "user", "content": [{"type": "input_text", "text": feedback}]}]
    final = attempts[-1]
    return {"status": final["status"], "error": final.get("error"), "attempts": attempts,
            "passed": bool(final.get("gate", {}).get("passed")), "draft": draft,
            "usd": round(sum(a.get("usd") or 0.0 for a in attempts), 6),
            "seconds": round(sum(a.get("seconds") or 0.0 for a in attempts), 2),
            "input_tokens": sum((a.get("usage") or {}).get("input_tokens", 0) for a in attempts),
            "output_tokens": sum((a.get("usage") or {}).get("output_tokens", 0) for a in attempts),
            "n_examples": n_examples, "house_rules": house_rules, "model": MODEL, "effort": EFFORT,
            "temperature": TEMPERATURE, "prompt_fingerprint": fingerprint(MODEL, instr, schema)}


# ---------------------------------------------------------------------------
# The independent check of causes (LLM judge; code grounds every quote)
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """You check the causal statements in a draft of SFCR sections E.1 and E.2 against the driver bullets
of the reporting year, written by the insurer's finance and risk teams. The bullets are the only evidence. For each
numbered sentence decide:
- supported: a bullet of the reporting year gives the same cause for the same effect; paraphrase is fine.
- unsupported: the sentence gives a cause that no bullet of the reporting year gives, contradicts a bullet, carries
  a cause over from an earlier year, stretches a bullet to other figures, or presents as known a reason that a bullet
  says is not known.
- no_cause: the sentence states no cause.
sentence_quote: at least five consecutive words copied exactly from the sentence, the words that state the cause.
For supported, bullet_id and bullet_quote (at least five consecutive words copied exactly from that bullet);
otherwise bullet_id "none" and bullet_quote "". reason: one short sentence.
Return exactly one verdict for each numbered sentence, in the order given, with n = its number, and nothing else."""


def causal_sentences(slots: dict[str, str]) -> list[tuple[str, str]]:
    """(slot, sentence) for every sentence that code finds a causal phrase in."""
    out = []
    for slot, text in slots.items():
        for s in rc.split_sentences(text):
            if rc.CAUSAL.search(s):
                out.append((slot, s))
    return out


def judge_schema(company: rc.Company, year: int) -> dict:
    ids = [b["id"] for b in company.bullets.get(year, [])]
    item = _obj({"n": {"type": "integer"}, "verdict": {"type": "string", "enum": ["supported", "unsupported",
                                                                                   "no_cause"]},
                 "sentence_quote": {"type": "string"}, "bullet_id": {"type": "string", "enum": ids + ["none"]},
                 "bullet_quote": {"type": "string"}, "reason": {"type": "string"}})
    return {"name": "cause_check", "strict": True, "schema": _obj({"verdicts": {"type": "array", "items": item}})}


def run_judge(client, company: rc.Company, year: int, slots: dict[str, str]) -> dict:
    sentences = causal_sentences(slots)
    if not sentences:
        return {"status": "ok", "verdicts": [], "usd": 0.0, "seconds": 0.0, "note": "no causal sentence found"}
    bullets = "\n".join(f"[{b['id']}] {b['topic']}: {b['text']}" for b in company.bullets.get(year, []))
    numbered = "\n".join(f"{i}. {s}" for i, (_, s) in enumerate(sentences, start=1))
    user = f"DRIVER BULLETS {year}\n{bullets}\n\nSENTENCES\n{numbered}"
    res = call(client, JUDGE_PROMPT, [{"role": "user", "content": [{"type": "input_text", "text": user}]}],
               judge_schema(company, year), max_output_tokens=2000)
    out = {"status": res["status"], "error": res.get("error"), "usd": res.get("usd", 0.0),
           "seconds": res.get("seconds", 0.0), "usage": res.get("usage"), "model": MODEL,
           "prompt_fingerprint": fingerprint(MODEL, JUDGE_PROMPT, judge_schema(company, year))}
    if res["status"] != "ok":
        return out
    bullet_text = {b["id"]: b["text"] for b in company.bullets.get(year, [])}
    verdicts = []
    for v in res["parsed"].get("verdicts", []):
        n = v.get("n", 0)
        if not 1 <= n <= len(sentences):
            continue
        slot, sentence = sentences[n - 1]
        grounded = _norm(v.get("sentence_quote", "")) in _norm(sentence) and len(v.get("sentence_quote", "").split()) >= 3
        if v.get("verdict") == "supported":
            grounded = grounded and _norm(v.get("bullet_quote", "")) in _norm(bullet_text.get(v.get("bullet_id"), ""))
        verdicts.append({**v, "slot": slot, "sentence": sentence, "grounded": grounded})
    out["verdicts"] = verdicts
    return out


def judge_findings(judge: dict) -> list[rc.Finding]:
    """The judge's verdicts as findings: an unsupported cause is a warning; a verdict whose quotes code cannot find
    in the text or the bullet is reported as not verifiable."""
    out = []
    for v in judge.get("verdicts", []):
        if not v.get("grounded"):
            out.append(rc.Finding("L-CAUSE", "warning", v["slot"], v["sentence"],
                                  "the LLM check's quote is not in the text or the bullet: verdict not verifiable"))
        elif v["verdict"] == "unsupported":
            out.append(rc.Finding("L-CAUSE", "warning", v["slot"], v["sentence"],
                                  f"unsupported cause (LLM check): {v.get('reason', '')}"))
    return out


# ---------------------------------------------------------------------------
# Recordings
# ---------------------------------------------------------------------------

def draft_key(company_id: str, year: int, n_examples: int, house_rules: bool) -> str:
    return f"{company_id}|{year}|examples={n_examples}|house_rules={'on' if house_rules else 'off'}"


def judge_key(company_id: str, year: int, method: str, slots: dict[str, str]) -> str:
    return f"{company_id}|{year}|{method}|{fingerprint(slots)[:16]}"


def load_recordings(path: Path = RECORDINGS_PATH) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"meta": {}, "drafts": {}, "judge": {}}
