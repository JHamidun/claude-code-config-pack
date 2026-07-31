#!/usr/bin/env python3
"""session-mentor · render_report.py
Merge stats.json (from collect.py) + analysis.json (from the agent) into a single
self-contained, theme-aware HTML report. No external assets, opens in any browser.

Usage:
  python render_report.py stats.json analysis.json --out report.html
  python render_report.py stats.json --out report.html   # stats-only (no analysis yet)
"""
import argparse, json, html, os, sys

CSS = """
:root{--bg:#fbfbfd;--card:#fff;--ink:#0d1117;--mut:#57606a;--line:#e6e8eb;--accent:#4f46e5;--accent2:#06b6d4;--good:#16a34a;--warn:#d97706;--bar:#c7d2fe}
@media(prefers-color-scheme:dark){:root{--bg:#0b0d10;--card:#14171c;--ink:#e6edf3;--mut:#9198a1;--line:#232830;--accent:#818cf8;--accent2:#22d3ee;--good:#4ade80;--warn:#fbbf24;--bar:#312e81}}
:root[data-theme=light]{--bg:#fbfbfd;--card:#fff;--ink:#0d1117;--mut:#57606a;--line:#e6e8eb;--accent:#4f46e5;--good:#16a34a;--warn:#d97706;--bar:#c7d2fe}
:root[data-theme=dark]{--bg:#0b0d10;--card:#14171c;--ink:#e6edf3;--mut:#9198a1;--line:#232830;--accent:#818cf8;--good:#4ade80;--warn:#fbbf24;--bar:#312e81}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:26px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 28px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:28px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.tile .n{font-size:26px;font-weight:700;letter-spacing:-.02em}.tile .l{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin-bottom:16px}
.card h2{font-size:17px;margin:0 0 14px;display:flex;align-items:center;gap:8px}
.bar-row{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}
.bar-row .k{width:150px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-row .t{flex:1;background:var(--bar);height:10px;border-radius:6px;overflow:hidden}
.bar-row .t i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px}
.bar-row .v{width:60px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink)}
.spark{display:flex;align-items:flex-end;gap:3px;height:64px}
.spark i{flex:1;background:linear-gradient(180deg,var(--accent),var(--accent2));border-radius:3px 3px 0 0;min-height:2px}
.sec p{margin:0 0 10px}.sec ul{margin:0 0 6px;padding-left:20px}.sec li{margin:3px 0}
.pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:20px;background:var(--bar);color:var(--ink);margin:2px 4px 2px 0}
code{background:var(--line);padding:1px 5px;border-radius:5px;font-size:.9em}
.foot{color:var(--mut);font-size:12px;text-align:center;margin-top:30px}
.toggle{position:fixed;top:14px;right:14px;background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:20px;padding:6px 12px;cursor:pointer;font-size:12px}
"""

JS = """
const r=document.documentElement;
document.querySelector('.toggle').onclick=()=>{const d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');r.setAttribute('data-theme',d==='dark'?'light':'dark')};
document.querySelectorAll('[data-count]').forEach(el=>{const to=+el.dataset.count;let s=0,st=performance.now();const dur=900;function f(t){const p=Math.min(1,(t-st)/dur);el.textContent=Math.round(to*(1-Math.pow(1-p,3))).toLocaleString('ru');if(p<1)requestAnimationFrame(f)}requestAnimationFrame(f)});
"""


def esc(s):
    return html.escape(str(s))


def fmt(n):
    return f"{n:,}".replace(",", " ")


def tile(n, label):
    return f'<div class="tile"><div class="n" data-count="{int(n)}">0</div><div class="l">{esc(label)}</div></div>'


def bars(d, top=10):
    items = list(d.items())[:top]
    mx = max((v for _, v in items), default=1) or 1
    rows = ""
    for k, v in items:
        w = int(100 * v / mx)
        rows += (f'<div class="bar-row"><span class="k">{esc(k)}</span>'
                 f'<span class="t"><i style="width:{w}%"></i></span>'
                 f'<span class="v">{fmt(v)}</span></div>')
    return rows


def sparkline(day_map):
    vals = list(day_map.values())
    if not vals:
        return ""
    mx = max(vals) or 1
    bars_ = "".join(f'<i style="height:{int(100*v/mx)}%" title="{esc(k)}: {v}"></i>'
                    for k, v in day_map.items())
    return f'<div class="spark">{bars_}</div>'


def render_section(sec):
    body = ""
    if sec.get("body"):
        for para in str(sec["body"]).split("\n\n"):
            body += f"<p>{esc(para)}</p>"
    if sec.get("items"):
        body += "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in sec["items"]) + "</ul>"
    if sec.get("snippets"):
        for sn in sec["snippets"]:
            body += f"<p><code>{esc(sn)}</code></p>"
    return f'<div class="card sec"><h2>{esc(sec.get("title",""))}</h2>{body}</div>'


def build(stats, analysis):
    t = stats["totals"]
    tiles = "".join([
        tile(t["sessions"], "сессий"),
        tile(t["messages"], "сообщений"),
        tile(t["tool_calls"], "вызовов инструментов"),
        tile(t["edits"], "правок"),
        tile(t["files_touched"], "файлов"),
        tile(round(t["out_tokens"] / 1000), "K токенов"),
    ])
    period = (analysis or {}).get("period") or f'последние {stats.get("generated_window_days","?")} дней'
    sections_html = "".join(render_section(s) for s in (analysis or {}).get("sections", []))
    proj = "".join(f'<span class="pill">{esc(k)} · {fmt(v)}</span>'
                   for k, v in list(stats.get("per_project", {}).items())[:12])

    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Session Mentor · {esc(period)}</title>
<style>{CSS}</style></head><body>
<button class="toggle">◐ тема</button>
<div class="wrap">
  <h1>Как ты работаешь с Claude Code</h1>
  <p class="sub">Отчёт Session Mentor · {esc(period)} · данные не покидали машину</p>
  <div class="tiles">{tiles}</div>
  <div class="card"><h2>⚙️ Инструменты (tool mix)</h2>{bars(stats.get("tool_mix",{}))}</div>
  <div class="card"><h2>📈 Активность по дням</h2>{sparkline(stats.get("activity_by_day",{}))}</div>
  <div class="card"><h2>📁 Проекты</h2>{proj or '<p class="sub">—</p>'}</div>
  {sections_html or '<div class="card sec"><h2>Анализ</h2><p class="sub">analysis.json не передан — показаны только метрики. Запусти анализ-шаг из SKILL.md.</p></div>'}
  <div class="foot">session-mentor · сгенерировано локально</div>
</div>
<script>{JS}</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stats")
    ap.add_argument("analysis", nargs="?", default=None)
    ap.add_argument("--out", default="mentor-report.html")
    a = ap.parse_args()
    stats = json.load(open(a.stats, encoding="utf-8"))
    analysis = json.load(open(a.analysis, encoding="utf-8")) if a.analysis and os.path.exists(a.analysis) else None
    out = build(stats, analysis)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(out)
    sys.stderr.write(f"wrote {a.out} ({len(out)//1024} KB)\n")


if __name__ == "__main__":
    main()
