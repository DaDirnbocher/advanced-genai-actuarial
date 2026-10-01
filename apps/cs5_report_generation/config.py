"""Case Study 5 report app: paths, the sample workbooks, captions and the seminar look."""

from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = APP_DIR / "samples"

SAMPLES = {
    "brisendale": {
        "file": "brisendale_mutual.xlsx",
        "label": "Brisendale Mutual — non-life mutual (Ireland); the insurer of the Case Study 5 notebook",
        "story": "Motor and home insurance. In 2026 a new motor quota share cuts the insurance risk it keeps, and the "
                 "SCR coverage ratio rises from 204% to 220%.",
    },
    "tallowmere": {
        "file": "tallowmere_life.xlsx",
        "label": "Tallowmere Life — life insurer (Austria)",
        "story": "Guaranteed and unit-linked life business. Falling interest rates in 2026 reduce own funds and raise "
                 "market risk: the ratio falls from 188% to 166%.",
    },
    "quillbrook": {
        "file": "quillbrook_insurance.xlsx",
        "label": "Quillbrook Insurance — composite insurer (Lithuania)",
        "story": "Life, health and non-life business. The tier limits cap its eligible own funds, a hailstorm hits "
                 "2026, and the ratio falls from 139% to 133%, below its risk appetite of 140%.",
    },
}
UPLOAD = "upload"
SESSION_CAP_USD = 0.50

CAPTIONS = {
    0: "Each fictitious insurer comes as one Excel workbook: figures for 2021 to 2026, the driver bullets of the "
       "finance and risk teams, the E.1 and E.2 texts published for 2022 to 2025, the house phrases and the "
       "terminology. Download a workbook, change it in Excel, and upload it again.",
    1: "Code derives every total, the own funds eligible under the tier limits of Art. 82 of Delegated Regulation "
       "(EU) 2015/35 and every ratio from the inputs of the workbook; nothing derived is typed. These are the figures "
       "that every method below must report correctly.",
    2: "How the insurer wrote E.1 and E.2 in earlier years. Each year the finance and risk teams explain the "
       "movements in bullets, and the actuary turns figures and bullets into the same kind of text: the boilerplate "
       "stays, the movements and their causes change. This archive is the house style a new text should follow, "
       "for a person and for a model.",
    3: "Two ways to draft the reporting year. The old way copies last year's text and updates the figures. The new "
       "way gives a language model the figures as placeholders, this year's bullets and 0 to 4 prior years as "
       "examples; code checks the draft and fills in every number.",
    4: "Every draft goes through the same checks. Code checks figures, years, dates, movement words, house phrases, "
       "terminology, the elements of Art. 297 and whether each cause can be traced to a bullet of the year. An "
       "optional LLM check judges the causes, and code grounds every quote it gives. What no check can verify is "
       "listed, not skipped.",
    5: "The draft is a proposal. A person reviews every finding, edits the text, runs the checks again and signs "
       "off; the export holds the text, the two tables, the remaining findings and the sign-off.",
}

# ---------------------------------------------------------------------------
# Colours — seminar palette (as in the Case Study 2 app)
# ---------------------------------------------------------------------------

COLOR_CYAN = "#009CDB"
COLOR_NAVY = "#0F2B72"
COLOR_CYAN_LIGHT = "#E6F5FB"
COLOR_BORDER = "#D5DEEA"

CSS = f"""
html, body, [class*="css"] {{ font-size: 15px; }}
.stApp {{ background-color: #FFFFFF; color: {COLOR_NAVY}; }}
.stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp h6, .stApp .stMarkdown {{ color: {COLOR_NAVY}; }}

.stButton > button, .stDownloadButton > button, .stApp input[type="text"], .stApp input[type="password"],
.stApp textarea, .stApp div[data-baseweb="input"], .stApp div[data-baseweb="textarea"],
.stApp div[data-baseweb="select"] > div, .demo-card-header, .text-box, .prompt-section-bar, .prompt-section-body,
[class*="st-key-card_step_"] div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stCodeBlock"] pre,
details[data-testid="stExpander"], details[data-testid="stExpander"] summary, div[data-testid="stAlertContainer"],
.notice-box {{ border-radius: 0 !important; }}

#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ display: none !important; }}
[data-testid="stAppDeployButton"], .stAppDeployButton {{ display: none !important; }}
section[data-testid="stSidebar"] {{ display: none !important; }}
div[data-testid="collapsedControl"] {{ display: none !important; }}
.stApp [data-testid="stAppViewBlockContainer"], .stApp [data-testid="stMainBlockContainer"] {{
    padding-top: 1.4rem !important; }}

.stApp input[type="text"], .stApp input[type="password"], .stApp textarea,
.stApp div[data-baseweb="input"] input, .stApp div[data-baseweb="textarea"] textarea,
.stApp div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; color: {COLOR_NAVY} !important; border: 1px solid {COLOR_BORDER} !important; }}
.stApp div[data-testid="stFileUploader"] section {{ background-color: #FFFFFF !important;
    border: 1px dashed #8FA3C4 !important; }}

.stApp .stButton > button, .stApp .stButton > button *, .stApp .stDownloadButton > button,
.stApp .stDownloadButton > button * {{ color: #FFFFFF !important; }}
.stApp .stButton > button, .stApp .stDownloadButton > button {{ background-color: {COLOR_CYAN} !important;
    border: 0 !important; font-weight: 600 !important; padding: 8px 18px !important; }}
.stApp .stButton > button:hover, .stApp .stDownloadButton > button:hover {{ background-color: {COLOR_NAVY} !important; }}
.stApp .stButton > button:disabled, .stApp .stButton > button:disabled * {{ background-color: #D0D6E0 !important;
    color: #6B7890 !important; }}

input[type="radio"], input[type="checkbox"] {{ accent-color: {COLOR_CYAN} !important; }}
label[data-baseweb="radio"]:has(input:checked) > div:first-child {{ background-color: {COLOR_CYAN} !important;
    border-color: {COLOR_CYAN} !important; }}
label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {{ background-color: #FFFFFF !important; }}
div[role="radiogroup"] > label {{ margin-bottom: 4px; }}
div[data-baseweb="slider"] [role="slider"] {{ background-color: {COLOR_CYAN} !important;
    border-color: {COLOR_CYAN} !important; }}

.stApp .app-header-banner {{ background: {COLOR_NAVY}; border-bottom: 4px solid {COLOR_CYAN}; padding: 18px 24px;
    margin-bottom: 22px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }}
.stApp .app-header-banner, .stApp .app-header-banner * {{ color: #FFFFFF !important; }}
.stApp .app-header-banner .header-title {{ font-size: 1.35rem; font-weight: 700; line-height: 1.3; }}
.stApp .app-header-banner .header-subtitle {{ font-size: 0.95rem; opacity: 0.85; margin-top: 3px; line-height: 1.4; }}
.stApp .app-header-banner .restart-btn {{ background: transparent; border: 1px solid rgba(255, 255, 255, 0.55);
    padding: 8px 18px; font-weight: 600; font-size: 0.95rem; text-decoration: none !important; white-space: nowrap; }}
.stApp .app-header-banner .restart-btn:hover {{ background: rgba(255, 255, 255, 0.10); }}

.demo-card-header {{ background: {COLOR_NAVY}; border-left: 6px solid {COLOR_CYAN}; padding: 10px 18px;
    font-weight: 600; font-size: 1.05rem; margin-bottom: -1px; }}
.demo-card-header, .demo-card-header * {{ color: #FFFFFF !important; }}
.stApp [class*="st-key-card_step_"] [data-testid="stVerticalBlockBorderWrapper"],
.stApp [class*="st-key-card_step_"] [data-testid="stVerticalBlockBorderWrapper"] > div,
.stApp [class*="st-key-card_step_"] [data-testid="stVerticalBlock"] {{ border-radius: 0 !important; }}
.stApp [class*="st-key-card_step_"] [data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {COLOR_BORDER} !important; background-color: #FFFFFF; }}
[class*="st-key-card_step_"] {{ margin-bottom: 26px; }}

.field-label {{ font-weight: 700; font-size: 1rem; margin-top: 12px; margin-bottom: 4px; }}
.field-label.first-label {{ margin-top: 0; }}
.edu-caption {{ color: #45557A !important; font-style: italic; font-size: 0.93rem; margin: 0 0 16px 0;
    line-height: 1.45; }}

.stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p {{ color: {COLOR_CYAN} !important; font-weight: 700; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {COLOR_CYAN} !important; }}

.notice-box {{ display: flex; align-items: flex-start; gap: 12px; padding: 12px 16px; margin: 12px 0;
    line-height: 1.5; border: 1px solid transparent; font-size: 0.95rem; }}
.notice-box .notice-icon {{ flex: 0 0 auto; font-weight: 700; font-size: 1.05rem; line-height: 1.4; }}
.notice-box .notice-text {{ flex: 1 1 auto; }}
.notice-box.notice-success {{ background: #E6F5FB; border-color: #9ED6EE; }}
.notice-box.notice-success .notice-icon {{ color: {COLOR_CYAN} !important; }}
.notice-box.notice-info {{ background: #F3F6FA; border-color: {COLOR_BORDER}; }}
.notice-box.notice-warning {{ background: #FFF6DD; border-color: #F0CB6A; }}
.notice-box.notice-warning .notice-icon {{ color: #A86400 !important; }}
.notice-box.notice-error {{ background: #FBEAEA; border-color: #EFB0AC; }}
.notice-box.notice-error .notice-icon {{ color: #B3261E !important; }}

div[data-testid="stCodeBlock"] pre {{ background-color: #F5F8FC !important; border: 1px solid #E3E9F2 !important; }}
details[data-testid="stExpander"] summary {{ background-color: #F5F8FC !important; }}

/* ---------- Texts with highlighted figures ---------- */
.text-box {{ background: #FFFFFF; border: 1px solid #E3E9F2; padding: 12px 16px; line-height: 1.6;
    font-size: 0.95rem; margin-bottom: 10px; }}
.slot-title {{ font-weight: 700; font-size: 0.86rem; letter-spacing: 0.3px; text-transform: uppercase;
    color: #45557A !important; margin: 14px 0 4px 0; }}
.slot-title .art {{ font-weight: 400; text-transform: none; letter-spacing: 0; }}
.fig-link {{ background: {COLOR_CYAN_LIGHT}; border-bottom: 2px solid {COLOR_CYAN}; padding: 0 2px; }}
.fig-changed {{ background: #FFF1C9; border-bottom: 2px solid #E0A100; padding: 0 2px; }}
.fig-placeholder {{ font-family: ui-monospace, Consolas, monospace; font-size: 0.82rem; background: #EEF2F7;
    padding: 0 3px; }}
.flagged {{ background: #FBEAEA; border-bottom: 2px solid #B3261E; }}
.bullet-tag {{ display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 0 6px; margin: 0 4px 0 0;
    background: {COLOR_NAVY}; vertical-align: 1px; }}
.bullet-tag, .bullet-tag * {{ color: #FFFFFF !important; }}
.bullet-row {{ margin: 0 0 8px 0; line-height: 1.5; font-size: 0.93rem; }}
.legend {{ font-size: 0.85rem; color: #45557A !important; margin: 4px 0 10px 0; }}
.sev {{ display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 1px 7px; text-transform: uppercase; }}
.sev-error {{ background: #B3261E; }}
.sev-warning {{ background: #A86400; }}
.sev-info {{ background: #6B7890; }}
.sev, .sev * {{ color: #FFFFFF !important; }}
.metric-big {{ font-size: 1.6rem; font-weight: 700; line-height: 1.2; }}
.metric-label {{ font-size: 0.85rem; color: #45557A !important; }}
.prompt-section-bar {{ background: {COLOR_NAVY}; padding: 5px 12px; font-weight: 600; font-size: 0.82rem;
    letter-spacing: 0.6px; }}
.prompt-section-bar, .prompt-section-bar * {{ color: #FFFFFF !important; }}
.prompt-section-body {{ background: #FFFFFF; padding: 12px 14px; margin: 0 0 16px 0;
    font-family: ui-monospace, Consolas, monospace; font-size: 0.8rem; line-height: 1.5; max-height: 360px;
    overflow-y: auto; white-space: pre-wrap; border: 1px solid #E3E9F2; border-top: none; }}
"""
