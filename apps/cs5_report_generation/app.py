"""Case Study 5 live demo — report generation: SFCR sections E.1 (own funds) and E.2 (SCR and MCR) from figures
and driver bullets, the old way and with a language model, and the checks that every draft goes through.

Start with `streamlit run app.py` from this folder (or `python app.py`, which does the same).
The logic lives in report_core.py (figures, old method, checks), drafting.py (the LLM steps) and export.py.
"""

from __future__ import annotations


# --- `python app.py` launcher shim ---------------------------------------------------------
def _is_running_under_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False
    return get_script_run_ctx(suppress_warning=True) is not None


if __name__ == "__main__" and not _is_running_under_streamlit():
    import os
    import sys
    from pathlib import Path

    from streamlit.web import cli as stcli

    os.chdir(Path(__file__).resolve().parent)  # so .streamlit/config.toml (the theme) is found
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    sys.exit(stcli.main())
# --- end shim ------------------------------------------------------------------------------

import hashlib
import html
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

_APP_DIR = str(Path(__file__).resolve().parent)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import drafting as dr  # noqa: E402
import export as ex  # noqa: E402
import report_core as rc  # noqa: E402
from config import CAPTIONS, CSS, SAMPLES, SAMPLES_DIR, SESSION_CAP_USD, UPLOAD  # noqa: E402

st.set_page_config(
    page_title="Case Study 5 — Report generation",
    page_icon=":material/description:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

METHOD_A = "A · last year's text, figures updated"
METHOD_B = "B · language model with prior years as examples"
DEPENDENT_KEYS = ["draft_b", "judge", "review_method", "signoff_reviewer", "signoff_decision", "signoff_notes",
                  "_recheck"]


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _reset_dependent() -> None:
    for key in list(st.session_state):
        if key in DEPENDENT_KEYS or key.startswith("edit_"):
            st.session_state.pop(key, None)
    st.session_state["judge"] = {}


def _reset_demo() -> None:
    _reset_dependent()
    for key in ("company_choice", "uploaded_xlsx", "manual_key", "use_other_key", "n_examples", "house_rules",
                "_company_sig"):
        st.session_state.pop(key, None)


st.session_state.setdefault("company_choice", "brisendale")
st.session_state.setdefault("ledger", [])
st.session_state.setdefault("judge", {})

if st.query_params.get("restart") == "1":
    _reset_demo()
    try:
        del st.query_params["restart"]
    except KeyError:
        pass
    st.rerun()


# ---------------------------------------------------------------------------
# API key — environment, then .env in this folder, then the password field. Never shown.
# ---------------------------------------------------------------------------

def _stored_key() -> tuple[str | None, str | None]:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"].strip(), "environment variable"
    env_file = Path(_APP_DIR) / ".env"
    if env_file.is_file():
        try:
            from dotenv import dotenv_values

            value = dotenv_values(env_file).get("OPENAI_API_KEY")
        except Exception:
            value = None
        if value:
            return value.strip(), ".env file in the app folder"
    return None, None


def _api_key() -> str | None:
    manual = (st.session_state.get("manual_key") or "").strip()
    stored, _ = _stored_key()
    if manual and (st.session_state.get("use_other_key") or not stored):
        return manual
    return stored


def _client():
    from openai import OpenAI
    return OpenAI(api_key=_api_key(), max_retries=0, timeout=180)


def _spent() -> float:
    return sum(st.session_state.get("ledger", []))


def _can_spend(worst: float) -> bool:
    return _spent() + worst <= SESSION_CAP_USD


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

_NOTICE_ICONS = {"success": "✓", "info": "i", "warning": "!", "error": "✕"}


def _notice(kind: str, body_html: str) -> None:
    st.markdown(f'<div class="notice-box notice-{kind}"><span class="notice-icon">{_NOTICE_ICONS.get(kind, "i")}'
                f'</span><span class="notice-text">{body_html}</span></div>', unsafe_allow_html=True)


def _field_label(text: str, *, first: bool = False) -> None:
    cls = "field-label first-label" if first else "field-label"
    st.markdown(f'<div class="{cls}">{html.escape(text)}</div>', unsafe_allow_html=True)


@contextmanager
def step_card(step_number: int, title: str):
    with st.container(key=f"card_step_{step_number}"):
        st.markdown(f'<div class="demo-card-header">Step {step_number} — {html.escape(title)}</div>',
                    unsafe_allow_html=True)
        with st.container(border=True):
            caption = CAPTIONS.get(step_number)
            if caption:
                st.markdown(f'<div class="edu-caption">{html.escape(caption)}</div>', unsafe_allow_html=True)
            yield


def render_header() -> None:
    st.html(
        '<div class="app-header-banner"><div>'
        '<div class="header-title">Advanced Applications of Generative AI in Actuarial Science — Case Study 5</div>'
        '<div class="header-subtitle">Report generation: SFCR sections E.1 (own funds) and E.2 (SCR and MCR) from '
        "figures and driver bullets · fictitious insurers, synthetic figures</div></div>"
        '<a class="restart-btn" href="?restart=1" target="_self">↻ Restart</a></div>'
    )


def _sev(severity: str) -> str:
    return f'<span class="sev sev-{severity}">{severity}</span>'


def _fmt_value(mid: str, value: float) -> str:
    if mid in rc.RATIOS:
        return f"{value:,.0f}%"
    return f"{value:,.1f}"


def _text_html(template: str, facts: dict[str, rc.Fact], changed: set[str] | None = None) -> str:
    """A template rendered for reading: every figure highlighted, with its placeholder as tooltip."""
    out, pos = [], 0
    for m in rc.PLACEHOLDER.finditer(template):
        out.append(html.escape(template[pos:m.start()]))
        pid = m.group(1)
        f = facts.get(pid)
        shown = f.display if f else f"[unknown {pid}]"
        cls = "fig-changed" if changed and pid in changed else "fig-link"
        out.append(f'<span class="{cls}" title="{{{{{html.escape(pid)}}}}}">{html.escape(shown)}</span>')
        pos = m.end()
    out.append(html.escape(template[pos:]))
    return "".join(out).replace("\n\n", "<br/><br/>").replace("\n", "<br/>")


def _slot_heading(slot: str, extra_html: str = "") -> None:
    art = {"e1_policy": "297(1)(a)", "e1_structure": "297(1)(b), (g)", "e1_eligibility": "297(1)(c), (d), (h)",
           "e1_reconciliation": "297(1)(e)", "e2_amounts": "297(2)(a), (b)", "e2_methods": "297(2)(c), (d), (f), (g)",
           "e2_changes": "297(2)(h)"}[slot]
    st.markdown(f'<div class="slot-title">{rc.SLOT_SECTION[slot]} · {html.escape(rc.SLOT_TITLE[slot])} '
                f'<span class="art">(Art. {art})</span> {extra_html}</div>', unsafe_allow_html=True)


def _show_document(slot_htmls: dict[str, str], company: rc.Company, year: int, tags: dict[str, str] | None = None,
                   tables: bool = True) -> None:
    for slot in rc.SLOT_IDS:
        tag_html = ""
        if tags and tags.get(slot):
            tag_html = " ".join(f'<span class="bullet-tag">{html.escape(t.strip())}</span>'
                                for t in tags[slot].split(";") if t.strip())
        _slot_heading(slot, tag_html)
        st.markdown(f'<div class="text-box">{slot_htmls.get(slot, "")}</div>', unsafe_allow_html=True)
        if tables and slot == "e1_structure":
            st.caption("Table E.1 (inserted by code): own funds by tier, EUR million")
            st.dataframe(pd.DataFrame(rc.table_e1(company, year)).set_index(""), use_container_width=True)
        if tables and slot == "e2_amounts":
            st.caption("Table E.2 (inserted by code): SCR by risk module, MCR and coverage ratios, EUR million")
            st.dataframe(pd.DataFrame(rc.table_e2(company, year)).set_index(""), use_container_width=True)


# ---------------------------------------------------------------------------
# The workbook
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, max_entries=16)
def _load_company(data: bytes, name: str) -> rc.Company:
    return rc.load_workbook(data, source_name=name)


def _workbook_bytes() -> tuple[bytes | None, str, str | None]:
    """(bytes, file name, sample key or None) of the chosen workbook."""
    choice = st.session_state.get("company_choice")
    if choice == UPLOAD:
        f = st.session_state.get("uploaded_xlsx")
        return (f.getvalue(), f.name, None) if f is not None else (None, "", None)
    path = SAMPLES_DIR / SAMPLES[choice]["file"]
    return path.read_bytes(), path.name, choice


@st.cache_data(show_spinner=False)
def _recordings() -> dict:
    return dr.load_recordings()


def _recordings_valid(stem: str | None, data: bytes) -> bool:
    if stem is None:
        return False
    meta = _recordings().get("meta", {})
    expected = meta.get("workbooks_sha256", {}).get(SAMPLES[stem]["file"].removesuffix(".xlsx"))
    return expected == hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Step 0 — Company and key
# ---------------------------------------------------------------------------

def render_step0() -> tuple[rc.Company | None, bytes | None, str | None]:
    company = None
    with step_card(0, "Company and workbook"):
        col_wb, col_key = st.columns([0.68, 0.32], gap="large")
        with col_wb:
            _field_label("Fictitious insurer", first=True)
            options = list(SAMPLES) + [UPLOAD]
            st.radio("Fictitious insurer", options, key="company_choice", label_visibility="collapsed",
                     format_func=lambda k: SAMPLES[k]["label"] if k in SAMPLES else "Upload your own workbook (.xlsx)")
            choice = st.session_state.company_choice
            if choice in SAMPLES:
                st.caption(SAMPLES[choice]["story"])
            else:
                st.file_uploader("A workbook in the layout of the samples", type=["xlsx"], key="uploaded_xlsx")
            data, name, stem = _workbook_bytes()
            sig = hashlib.sha256(data).hexdigest() if data else ""
            if st.session_state.get("_company_sig") != sig:
                _reset_dependent()
                st.session_state["_company_sig"] = sig
            if data:
                st.download_button("Download this workbook (.xlsx)", data, file_name=name or "workbook.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl_workbook")
        with col_key:
            _field_label("OpenAI API key", first=True)
            stored, origin = _stored_key()
            if stored:
                _notice("success", f"Found in the {html.escape(origin)}. The value is never shown.")
                st.checkbox("Use a different key for this session", key="use_other_key")
            if not stored or st.session_state.get("use_other_key"):
                st.text_input("OpenAI API key", type="password", key="manual_key", placeholder="sk-...",
                              label_visibility="collapsed",
                              help="Kept only in this browser session; never written to disk or shown.")
            if not _api_key():
                st.caption("Without a key the app shows recorded runs of the language model for the three sample "
                           "workbooks. Everything else runs without a key.")
            st.caption(f"Model: {dr.MODEL} (reasoning effort {dr.EFFORT}, temperature {dr.TEMPERATURE}). "
                       f"This session: USD {_spent():.4f} of a cap of USD {SESSION_CAP_USD:.2f}.")
        if not data:
            st.caption("Upload a workbook to continue.")
            return None, None, None
        try:
            company = _load_company(data, name)
        except rc.WorkbookError as exc:
            _notice("error", f"The workbook cannot be read: {html.escape(str(exc))}")
            return None, None, None
        except Exception as exc:  # a file that is not a workbook at all
            _notice("error", f"The file cannot be read as a workbook ({html.escape(type(exc).__name__)}).")
            return None, None, None
        y = company.current_year
        hist = company.history_years
        if y - 1 not in company.figures:
            _notice("error", f"The workbook needs figures for {y - 1} to compare {y} with.")
            return None, None, None
        _notice("success",
                f"<strong>{html.escape(company.name)}</strong>: figures {company.years[0]}–{company.years[-1]}, "
                f"driver bullets for {', '.join(str(k) for k in sorted(company.bullets))}, published E.1/E.2 texts for "
                f"{', '.join(str(k) for k in hist) or 'no year'}. "
                f"<strong>The year to draft is {y}.</strong>")
    return company, data, stem


# ---------------------------------------------------------------------------
# Step 1 — Figures
# ---------------------------------------------------------------------------

FIGURE_ROWS = ["scr", "mcr", "eof_scr", "cov_scr", "eof_mcr", "cov_mcr", "of_t1", "of_t2", "of_t3", "of_total",
               "of_inelig_scr", "scr_market", "scr_default", "scr_life", "scr_health", "scr_nonlife", "div_benefit",
               "bscr", "scr_operational", "lac_tp", "lac_dt", "foreseeable_div", "equity_fs", "eaol"]


def render_step1(company: rc.Company) -> None:
    y = company.current_year
    with step_card(1, f"The figures, {company.years[0]} to {company.years[-1]}"):
        rows = []
        for mid in FIGURE_ROWS:
            values = [company.figures[yr][mid] for yr in company.years]
            if all(abs(v) < 1e-9 for v in values):
                continue
            m = rc.METRIC[mid]
            rows.append({"item": m.label, "section": m.section, **{str(yr): _fmt_value(mid, v)
                                                                  for yr, v in zip(company.years, values)}})
        col_t, col_c = st.columns([0.66, 0.34], gap="large")
        with col_t:
            _field_label("Key figures (EUR million; ratios in per cent)", first=True)
            st.dataframe(pd.DataFrame(rows).set_index("item"), use_container_width=True, height=420)
        with col_c:
            _field_label("SCR coverage ratio", first=True)
            st.line_chart(pd.DataFrame({"SCR coverage ratio (%)": [company.figures[yr]["cov_scr"]
                                                                   for yr in company.years]},
                                       index=[str(yr) for yr in company.years]), height=210)
            appetite = company.text.get("appetite_low")
            if appetite:
                st.caption(f"Risk appetite in the Company sheet: at least {appetite}%"
                           + (f", up to {company.text['appetite_high']}%" if company.text.get("appetite_high") else ""))
            problems = rc.consistency_findings(company.figures)
            cached = rc.cached_differences(company)
            if not [p for p in problems if p["severity"] != "info"] and not cached:
                _notice("success", "Every year passes the figure checks: tier limits, the MCR corridor and "
                                   "basic own funds = excess of assets over liabilities − foreseeable dividends + "
                                   "subordinated liabilities.")
            for p in problems:
                _notice({"error": "error", "warning": "warning"}.get(p["severity"], "info"),
                        f"{p['year']}: {html.escape(p['message'])}")
            if cached:
                _notice("warning", f"{len(cached)} value(s) that Excel computed differ from the values code derives; "
                                   "the app uses its own.")

        _field_label(f"The movements of {y}: what every draft must describe")
        facts = rc.facts_for(company, y)
        mv_rows = []
        for mid, f in rc.movements(facts).items():
            if not rc.METRIC[mid].movement or mid in ("bscr", "of_total"):
                continue
            mv_rows.append({"item": rc.METRIC[mid].label, str(y - 1): _fmt_value(mid, company.figures[y - 1][mid]),
                            str(y): _fmt_value(mid, company.figures[y][mid]),
                            "change": f.display, "direction": f.direction, "house phrase": f.phrase or "-"})
        st.dataframe(pd.DataFrame(mv_rows).set_index("item"), use_container_width=True)
        with st.expander(f"The facts catalogue of {y}: every figure as a placeholder ({len(facts)} entries)"):
            st.dataframe(pd.DataFrame([{"placeholder": "{{" + f.id + "}}", "renders as": f.display,
                                        "meaning": f.label, "direction": f.direction or "",
                                        "house phrase": f.phrase or ""} for f in facts.values()]),
                         use_container_width=True, hide_index=True, height=360)


# ---------------------------------------------------------------------------
# Step 2 — Prior years
# ---------------------------------------------------------------------------

def render_step2(company: rc.Company) -> None:
    hist = sorted(company.history_years, reverse=True)
    with step_card(2, f"How E.1 and E.2 were written in earlier years ({', '.join(str(h) for h in sorted(hist))})"):
        if not hist:
            _notice("info", "The workbook holds no published text for an earlier year.")
            return
        example = rc.facts_for(company, hist[0])["eof_scr_cur"].display
        st.markdown(f'<div class="legend"><span class="fig-link">{html.escape(example)}</span> a figure that code '
                    'links to the figures of its year (hover for the placeholder) · <span class="bullet-tag">B1</span> '
                    'the bullets a block draws on</div>', unsafe_allow_html=True)
        tabs = st.tabs([str(h) for h in hist])
        for tab, yr in zip(tabs, hist):
            with tab:
                facts = rc.facts_for(company, yr)
                col_b, col_t = st.columns([0.32, 0.68], gap="large")
                with col_b:
                    _field_label(f"Driver bullets {yr}", first=True)
                    for b in company.bullets.get(yr, []):
                        st.markdown(f'<div class="bullet-row"><span class="bullet-tag">{html.escape(b["id"])}</span>'
                                    f'<strong>{html.escape(b["topic"])}</strong> — {html.escape(b["text"])}</div>',
                                    unsafe_allow_html=True)
                with col_t:
                    _field_label(f"Published E.1 and E.2, {yr}", first=True)
                    htmls, tags = {}, {}
                    for row in company.narratives[yr]:
                        template, _ = rc.templatize(row["text"], facts)
                        htmls[row["slot"]] = _text_html(template, facts)
                        tags[row["slot"]] = row.get("based_on", "")
                    _show_document(htmls, company, yr, tags, tables=False)

        _field_label("What changes from one year to the next")
        sims = []
        for slot in rc.SLOT_IDS:
            row = {"text block": f"{rc.SLOT_SECTION[slot]} · {rc.SLOT_TITLE[slot]}"}
            for a, b in zip(sorted(hist)[:-1], sorted(hist)[1:]):
                ta, _ = rc.templatize(company.slots(a).get(slot, ""), rc.facts_for(company, a))
                tb, _ = rc.templatize(company.slots(b).get(slot, ""), rc.facts_for(company, b))
                row[f"{a} → {b}"] = f"{100 * rc.similarity(ta, tb):.0f}%"
            sims.append(row)
        st.dataframe(pd.DataFrame(sims).set_index("text block"), use_container_width=True)
        st.caption("Word-level similarity of consecutive years after every figure is replaced by its placeholder. "
                   "100% means the same words with new figures (boilerplate); lower values mean that the block was "
                   "rewritten for the year's movements and bullets. A new text should keep the first and rewrite the "
                   "second: the old way below keeps both.")


# ---------------------------------------------------------------------------
# Step 3 — Drafting
# ---------------------------------------------------------------------------

def render_step3(company: rc.Company, data: bytes, stem: str | None) -> dict[str, dict[str, str]]:
    y = company.current_year
    facts = rc.facts_for(company, y)
    drafts: dict[str, dict[str, str]] = {}
    with step_card(3, f"Drafting E.1 and E.2 for {y}: the old way and the new way"):
        tab_a, tab_b = st.tabs([METHOD_A, METHOD_B])
        with tab_a:
            if y - 1 not in company.narratives:
                _notice("info", f"There is no published text for {y - 1} to copy.")
            else:
                cu = rc.copy_and_update(company, y)
                drafts[METHOD_A] = cu["slots"]
                changed = {c["placeholder"] for c in cu["changes"] if c["placeholder"]}
                n_changed = len({(c["slot"], c["placeholder"]) for c in cu["changes"] if c["placeholder"]})
                st.markdown(f'<div class="legend">The {y - 1} text with every figure that code can link to the '
                            f'{y - 1} figures replaced by the same item for {y}: <span class="fig-changed">'
                            f'updated figure</span> · <span class="fig-link">figure unchanged</span>. '
                            f'{n_changed} figures were updated; every word is from {y - 1}.</div>',
                            unsafe_allow_html=True)
                _show_document({s: _text_html(t, facts, changed) for s, t in cu["templates"].items()}, company, y)
                _notice("info", "Read it as a reviewer: the figures are this year's, but are the movement words, the "
                                "causes and the dates? Step 4 checks.")
        with tab_b:
            drafts_b = _render_llm_tab(company, data, stem, facts)
            if drafts_b:
                drafts[METHOD_B] = drafts_b
    return drafts


def _render_llm_tab(company: rc.Company, data: bytes, stem: str | None, facts: dict) -> dict[str, str] | None:
    y = company.current_year
    max_k = len([h for h in company.history_years if h < y])
    col_s, col_r = st.columns([0.5, 0.5], gap="large")
    with col_s:
        _field_label("Prior years given to the model as examples", first=True)
        st.slider("Prior years as examples", 0, max_k, value=min(4, max_k), key="n_examples",
                  label_visibility="collapsed")
        st.caption("0 = no example: the model only knows the rules. 4 = the texts of the last four years: the model "
                   "sees how this insurer writes.")
    with col_r:
        _field_label("House rules", first=True)
        st.toggle("Apply the house rules (movement phrases and terminology from the workbook)", value=True,
                  key="house_rules")
        st.caption("On: code computes each movement phrase from the size of the change ('decreased slightly') and "
                   "the gate enforces it and the house terms. Off: the model decides the words itself.")
    k, rules = st.session_state.n_examples, st.session_state.house_rules
    rec_key = dr.draft_key(company.company_id, y, k, rules)
    recorded = _recordings().get("drafts", {}).get(rec_key) if _recordings_valid(stem, data) else None
    worst = dr.worst_case_usd(dr.instructions(k, rules), dr.user_message(company, y, k, rules)) * 2

    b1, b2, _ = st.columns([0.34, 0.30, 0.36])
    with b1:
        live = st.button(f"Draft live with {dr.MODEL} (about USD 0.002)", key="btn_draft_live",
                         disabled=not _api_key() or not _can_spend(worst))
    with b2:
        show_rec = st.button("Show the recorded draft", key="btn_draft_rec", disabled=recorded is None)
    if not _api_key() and recorded is None:
        st.caption("No key and no recording for this workbook and these settings: add a key in Step 0 to draft.")
    if live:
        with st.spinner(f"{dr.MODEL} drafts E.1 and E.2; code checks the draft (one revision round if needed) ..."):
            res = dr.run_draft(_client(), company, y, k, rules)
        st.session_state.ledger.append(res.get("usd", 0.0))
        st.session_state["draft_b"] = {**res, "source": "live", "settings": (k, rules)}
        st.session_state["judge"].pop(METHOD_B, None)
        _clear_edits(METHOD_B)
        st.rerun()  # so that the cost in Step 0 and the checks below include the new draft
    elif show_rec and recorded:
        st.session_state["draft_b"] = {**recorded, "source": "recorded", "settings": (k, rules)}
        st.session_state["judge"].pop(METHOD_B, None)
        _clear_edits(METHOD_B)
        st.rerun()

    res = st.session_state.get("draft_b")
    if not res:
        with st.expander("What the model receives with these settings"):
            _show_prompt(company, y, k, rules)
        return None
    rk, rr = res.get("settings", (k, rules))
    if (rk, rr) != (k, rules):
        _notice("info", f"The draft below was made with {rk} prior year(s) and house rules "
                        f"{'on' if rr else 'off'}; draft again to apply the settings above.")
    if res.get("status") != "ok" or not res.get("draft"):
        _notice("error", f"The call did not return a draft: {html.escape(str(res.get('error')))}")
        return None
    src = ("recorded on " + res.get("recorded_utc", "")[:10]) if res.get("source") == "recorded" else "live"
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-big">{"passed" if res.get("passed") else "not passed"}</div>'
                f'<div class="metric-label">drafting gate ({len(res.get("attempts", []))} call(s))</div>',
                unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-big">USD {res.get("usd", 0):.4f}</div><div class="metric-label">cost ({src})'
                f'</div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-big">{res.get("input_tokens", 0):,} / {res.get("output_tokens", 0):,}</div>'
                f'<div class="metric-label">input / output tokens</div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-big">{res.get("seconds", 0):.0f} s</div><div class="metric-label">'
                f'{res.get("model", dr.MODEL)}</div>', unsafe_allow_html=True)
    for a in res.get("attempts", []):
        errs = (a.get("gate") or {}).get("errors", [])
        if errs and a is not res["attempts"][-1]:
            with st.expander(f"Attempt {a['attempt']}: the gate returned {len(errs)} error(s) to the model"):
                for e in errs:
                    st.markdown(f"- {html.escape(e)}")
    final_gate = (res["attempts"][-1].get("gate") or {}) if res.get("attempts") else {}
    if final_gate.get("errors"):
        _notice("warning", "The final draft still breaks rule(s) of the gate: "
                + "; ".join(html.escape(e) for e in final_gate["errors"][:4]))
    draft = res["draft"]
    st.markdown(f'<div class="legend"><span class="fig-link">{html.escape(facts["scr_cur"].display)}</span> a figure '
                'that code filled in from a placeholder (hover to see it)</div>', unsafe_allow_html=True)
    _show_document({s: _text_html(draft.get(s, ""), facts) for s in rc.SLOT_IDS}, company, y)
    col_d, col_c = st.columns(2, gap="large")
    with col_d:
        _field_label("The model's decision on each bullet")
        bullets = {b["id"]: b["topic"] for b in company.bullets.get(y, [])}
        st.dataframe(pd.DataFrame([{"bullet": f"{d['bullet_id']} {bullets.get(d['bullet_id'], '')}",
                                    "used in": d["used_in"], "note": d["note"]}
                                   for d in draft.get("bullet_decisions", [])]),
                     use_container_width=True, hide_index=True)
    with col_c:
        _field_label("Sentences the model says state a cause")
        st.dataframe(pd.DataFrame([{"bullet": c["bullet_id"], "sentence": rc.render(c["sentence"], facts)}
                                   for c in draft.get("causal_claims", [])]),
                     use_container_width=True, hide_index=True)
    with st.expander("The draft as the model wrote it: placeholders instead of figures"):
        for s in rc.SLOT_IDS:
            st.markdown(f"**{s}**")
            st.code(draft.get(s, ""), language="text", wrap_lines=True)
    with st.expander("What the model receives with these settings"):
        _show_prompt(company, y, rk, rr)
    return {s: rc.render(draft.get(s, ""), facts) for s in rc.SLOT_IDS}


def _show_prompt(company: rc.Company, y: int, k: int, rules: bool) -> None:
    instr, user = dr.instructions(k, rules), dr.user_message(company, y, k, rules)
    st.html(f'<div class="prompt-section-bar">INSTRUCTIONS ({len(instr):,} characters)</div>'
            f'<pre class="prompt-section-body">{html.escape(instr)}</pre>'
            f'<div class="prompt-section-bar">USER MESSAGE ({len(user):,} characters)</div>'
            f'<pre class="prompt-section-body">{html.escape(user)}</pre>')


def _clear_edits(method: str) -> None:
    tag = "A" if method == METHOD_A else "B"
    for key in list(st.session_state):
        if key.startswith(f"edit_{tag}_"):
            st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Step 4 — Checks
# ---------------------------------------------------------------------------

def render_step4(company: rc.Company, data: bytes, stem: str | None,
                 drafts: dict[str, dict[str, str]]) -> dict[str, list[rc.Finding]]:
    y = company.current_year
    results: dict[str, list[rc.Finding]] = {}
    with step_card(4, "The checks"):
        for method, slots in drafts.items():
            findings = rc.run_checks(company, y, slots)
            judge = st.session_state["judge"].get(method)
            if judge:
                findings += dr.judge_findings(judge)
            results[method] = findings
        checks = dict(rc.CHECKS)
        checks["L-CAUSE"] = "an LLM check: every cause is supported by a bullet of the year (optional, below)"
        summary = []
        for cid, what in checks.items():
            row = {"check": cid, "what it checks": what}
            for method, findings in results.items():
                errs = sum(1 for f in findings if f.check == cid and f.severity == "error")
                warns = sum(1 for f in findings if f.check == cid and f.severity == "warning")
                infos = sum(1 for f in findings if f.check == cid and f.severity == "info")
                row[method.split(" · ")[0]] = " · ".join(x for x in (f"{errs} error" + ("s" if errs != 1 else "") if errs else "",
                                                                       f"{warns} warning" + ("s" if warns != 1 else "") if warns else "",
                                                                       f"{infos} note" + ("s" if infos != 1 else "") if infos else "")
                                                         if x) or "-"
            summary.append(row)
        if METHOD_B not in drafts:
            st.caption("Method B appears here once a draft exists in Step 3.")
        st.dataframe(pd.DataFrame(summary).set_index("check"), use_container_width=True)

        tabs = st.tabs(list(results))
        for tab, method in zip(tabs, results):
            with tab:
                findings = results[method]
                order = {"error": 0, "warning": 1, "info": 2}
                rows = [{"severity": f.severity, "check": f.check, "where": f.slot or "(document)",
                         "finding": f.message, "sentence": f.quote}
                        for f in sorted(findings, key=lambda f: (order.get(f.severity, 3), f.check))]
                n_err = sum(1 for f in findings if f.severity == "error")
                n_warn = sum(1 for f in findings if f.severity == "warning")
                _notice("error" if n_err else "warning" if n_warn else "success",
                        f"{n_err} error(s), {n_warn} warning(s) and {len(findings) - n_err - n_warn} note(s).")
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                                 column_config={"sentence": st.column_config.TextColumn(width="large"),
                                                "finding": st.column_config.TextColumn(width="large")})
                with st.expander("The elements of Art. 297 in this draft"):
                    st.dataframe(pd.DataFrame(rc.element_status(company, y, drafts[method])),
                                 use_container_width=True, hide_index=True)
                _render_judge(company, data, stem, method, drafts[method])
    return results


def _render_judge(company: rc.Company, data: bytes, stem: str | None, method: str, slots: dict[str, str]) -> None:
    y = company.current_year
    _field_label("LLM check of the stated causes")
    st.caption("A second, independent call reads every sentence that code finds a causal phrase in and judges it "
               "against this year's bullets. Code then looks up every quote the judge gives; a verdict whose quote "
               "is not in the text or the bullet counts as not verifiable.")
    key_method = "copy_and_update" if method == METHOD_A else None
    if method == METHOD_B:
        res = st.session_state.get("draft_b") or {}
        k, rules = res.get("settings", (0, True))
        key_method = f"llm_examples={k}_rules={'on' if rules else 'off'}"
    rec_key = dr.judge_key(company.company_id, y, key_method, slots)
    recorded = _recordings().get("judge", {}).get(rec_key) if _recordings_valid(stem, data) else None
    tag = "A" if method == METHOD_A else "B"
    c1, c2, _ = st.columns([0.34, 0.30, 0.36])
    with c1:
        live = st.button("Check the causes live (about USD 0.0005)", key=f"btn_judge_live_{tag}",
                         disabled=not _api_key() or not _can_spend(0.004))
    with c2:
        show = st.button("Show the recorded check", key=f"btn_judge_rec_{tag}", disabled=recorded is None)
    if live:
        with st.spinner("The LLM check reads the causal sentences ..."):
            judge = dr.run_judge(_client(), company, y, slots)
        st.session_state.ledger.append(judge.get("usd", 0.0))
        st.session_state["judge"][method] = {**judge, "source": "live"}
        st.rerun()
    if show and recorded:
        st.session_state["judge"][method] = {**recorded, "source": "recorded"}
        st.rerun()
    judge = st.session_state["judge"].get(method)
    if judge:
        if judge.get("status") != "ok":
            _notice("error", f"The check did not return: {html.escape(str(judge.get('error')))}")
            return
        rows = [{"verdict": v["verdict"], "bullet": v.get("bullet_id", ""), "quotes found": "yes" if v["grounded"] else "no",
                 "sentence": v["sentence"], "reason": v.get("reason", "")} for v in judge.get("verdicts", [])]
        src = "recorded" if judge.get("source") == "recorded" else "live"
        st.caption(f"{len(rows)} causal sentence(s), USD {judge.get('usd', 0):.4f} ({src}).")
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                         column_config={"sentence": st.column_config.TextColumn(width="large")})


# ---------------------------------------------------------------------------
# Step 5 — Review and export
# ---------------------------------------------------------------------------

def render_step5(company: rc.Company, drafts: dict[str, dict[str, str]],
                 results: dict[str, list[rc.Finding]]) -> None:
    y = company.current_year
    with step_card(5, "Review, sign-off and export"):
        method = st.radio("Draft to review", list(drafts), key="review_method", horizontal=True)
        tag = "A" if method == METHOD_A else "B"
        _notice("info", "Edit the text where a finding asks for it, then run the checks again. Figures you type "
                        "yourself are checked like any other.")
        edited = {}
        for slot in rc.SLOT_IDS:
            key = f"edit_{tag}_{slot}"
            st.session_state.setdefault(key, drafts[method].get(slot, ""))
            edited[slot] = st.text_area(f"{rc.SLOT_SECTION[slot]} · {rc.SLOT_TITLE[slot]}", key=key, height=140)
        findings = rc.run_checks(company, y, edited)
        judge = st.session_state["judge"].get(method)
        if judge and all(edited[s] == drafts[method].get(s, "") for s in rc.SLOT_IDS):
            findings += dr.judge_findings(judge)
        n_err = sum(1 for f in findings if f.severity == "error")
        n_warn = sum(1 for f in findings if f.severity == "warning")
        _notice("error" if n_err else "warning" if n_warn else "success",
                f"The edited text: {n_err} error(s), {n_warn} warning(s), "
                f"{len(findings) - n_err - n_warn} note(s). The checks run again on every edit.")
        with st.expander("Findings of the edited text"):
            if findings:
                st.dataframe(pd.DataFrame([{"severity": f.severity, "check": f.check, "where": f.slot or "(document)",
                                            "finding": f.message} for f in findings]),
                             use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns([0.3, 0.3, 0.4], gap="large")
        with c1:
            st.text_input("Reviewer", key="signoff_reviewer", placeholder="name of the reviewing actuary")
        with c2:
            st.selectbox("Decision", ["approved", "approved with changes", "returned for rework"],
                         key="signoff_decision", index=None, placeholder="choose")
        with c3:
            st.text_input("Notes", key="signoff_notes", placeholder="e.g. how the remaining warnings were assessed")
        signoff = {"reviewer": st.session_state.get("signoff_reviewer"),
                   "decision": st.session_state.get("signoff_decision"),
                   "notes": st.session_state.get("signoff_notes")}
        if n_err and signoff["decision"] in ("approved", "approved with changes"):
            _notice("warning", "The text still has errors: an approval should say in the notes why each one is "
                               "acceptable.")
        stamp = datetime.now().strftime("%Y%m%d")
        base = f"{company.company_id}_sfcr_E1_E2_{y}_{tag}_{stamp}"
        d1, d2, _ = st.columns([0.3, 0.3, 0.4])
        with d1:
            st.download_button("Download Word (.docx)", ex.to_docx(company, y, edited, method, findings, signoff),
                               file_name=base + ".docx", key="dl_docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with d2:
            st.download_button("Download Markdown (.md)", ex.to_markdown(company, y, edited, method, findings,
                                                                        signoff).encode("utf-8"),
                               file_name=base + ".md", mime="text/markdown", key="dl_md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

render_header()
company, data, stem = render_step0()
if company is not None:
    render_step1(company)
    render_step2(company)
    drafts = render_step3(company, data, stem)
    if drafts:
        results = render_step4(company, data, stem, drafts)
        render_step5(company, drafts, results)
