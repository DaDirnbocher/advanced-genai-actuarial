"""Author's tool: records the LLM runs that the app shows when no key is visible.

    python tools/record_runs.py            # needs OPENAI_API_KEY; stops before USD 0.12 in total

For each sample workbook it records one draft per setting (0 to 4 prior years as examples, house rules on and off)
and the independent check of causes on every recorded draft and on the copy-and-update text. Not needed to run the app.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import drafting as dr  # noqa: E402
import report_core as rc  # noqa: E402

CAP_USD = 0.12
SAMPLES = ["brisendale_mutual", "tallowmere_life", "quillbrook_insurance"]
_lock = threading.Lock()
spent = {"usd": 0.0}


def key_from_env() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, "OPENAI_API_KEY")[0]
    except Exception:
        return None


def book(usd: float) -> None:
    with _lock:
        spent["usd"] += usd


def main() -> None:
    from openai import OpenAI
    key = key_from_env()
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=key, max_retries=0, timeout=180)
    rec = dr.load_recordings()
    rec.setdefault("drafts", {})
    rec.setdefault("judge", {})
    companies = {s: rc.load_workbook(APP_DIR / "samples" / f"{s}.xlsx") for s in SAMPLES}
    sha = {s: hashlib.sha256((APP_DIR / "samples" / f"{s}.xlsx").read_bytes()).hexdigest() for s in SAMPLES}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    jobs = [(s, k, rules) for s in SAMPLES for k in range(0, 5) for rules in (True, False)]

    def draft_job(job):
        s, k, rules = job
        c = companies[s]
        key_ = dr.draft_key(c.company_id, c.current_year, k, rules)
        old = rec["drafts"].get(key_)
        fp = dr.fingerprint(dr.MODEL, dr.instructions(k, rules), dr.draft_schema(c, c.current_year))
        if old and old.get("prompt_fingerprint") == fp and old.get("workbook_sha256") == sha[s] and old.get("draft"):
            return key_, old, False
        if spent["usd"] + 2 * dr.worst_case_usd(dr.instructions(k, rules), dr.user_message(c, c.current_year, k, rules)) > CAP_USD:
            return key_, None, False
        res = dr.run_draft(client, c, c.current_year, k, rules)
        book(res["usd"])
        res.update(recorded_utc=now, workbook_sha256=sha[s], company=c.name)
        return key_, res, True

    with ThreadPoolExecutor(max_workers=4) as pool:
        for key_, res, fresh in pool.map(draft_job, jobs):
            if res is None:
                print(f"[skipped] {key_}: the cap of USD {CAP_USD} would be exceeded")
                continue
            rec["drafts"][key_] = res
            if fresh:
                print(f"[draft] {key_}: {res['status']}, gate {'passed' if res['passed'] else 'NOT passed'}, "
                      f"{len(res['attempts'])} call(s), USD {res['usd']:.4f}; total USD {spent['usd']:.4f}")

    judge_jobs = []
    for s in SAMPLES:
        c = companies[s]
        y = c.current_year
        F = rc.facts_for(c, y)
        cu = rc.copy_and_update(c, y)
        judge_jobs.append((s, "copy_and_update", cu["slots"]))
        for k in range(0, 5):
            for rules in (True, False):
                d = rec["drafts"].get(dr.draft_key(c.company_id, y, k, rules))
                if d and d.get("draft"):
                    slots = {slot: rc.render(d["draft"][slot], F) for slot in rc.SLOT_IDS}
                    judge_jobs.append((s, f"llm_examples={k}_rules={'on' if rules else 'off'}", slots))

    def judge_job(job):
        s, method, slots = job
        c = companies[s]
        key_ = dr.judge_key(c.company_id, c.current_year, method, slots)
        if key_ in rec["judge"] and rec["judge"][key_].get("status") == "ok":
            return key_, rec["judge"][key_], False
        if spent["usd"] + 0.003 > CAP_USD:
            return key_, None, False
        res = dr.run_judge(client, c, c.current_year, slots)
        book(res.get("usd", 0.0))
        res.update(recorded_utc=now, method=method, company=c.name)
        return key_, res, True

    with ThreadPoolExecutor(max_workers=4) as pool:
        for key_, res, fresh in pool.map(judge_job, judge_jobs):
            if res is None:
                print(f"[skipped] judge {key_}: the cap would be exceeded")
                continue
            rec["judge"][key_] = res
            if fresh:
                n_un = sum(1 for v in res.get("verdicts", []) if v["verdict"] == "unsupported")
                print(f"[judge] {key_}: {res['status']}, {len(res.get('verdicts', []))} sentence(s), {n_un} unsupported, "
                      f"USD {res.get('usd', 0):.4f}; total USD {spent['usd']:.4f}")

    rec["meta"] = {"model": dr.MODEL, "effort": dr.EFFORT, "temperature": dr.TEMPERATURE,
                   "prices_usd_per_mtok": dr.PRICES, "recorded_utc": now, "workbooks_sha256": sha,
                   "note": "Recorded with tools/record_runs.py; the app shows these runs when no key is visible."}
    total = sum(d.get("usd", 0) for d in rec["drafts"].values()) + sum(j.get("usd", 0) for j in rec["judge"].values())
    rec["meta"]["total_usd_all_recordings"] = round(total, 6)
    dr.RECORDINGS_PATH.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Spent in this run: USD {spent['usd']:.4f}; all recordings together: USD {total:.4f}")


if __name__ == "__main__":
    main()
