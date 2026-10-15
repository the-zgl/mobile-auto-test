# -*- coding: utf-8 -*-
"""质量看板（测试平台雏形）—— 把测试结果变成一个可分享的网页。

对应 JD 的「测试平台 / 质量中台 0→1」方向。这里做**最小闭环**：

    跑 pytest（带 --json-report）  →  生成 report.json
    运行本脚本                    →  生成 report.html（静态、无后端依赖）
    双击 report.html 即可查看

页面包含三个模块（对应测试平台的核心三件套）：
1. 用例管理：用例列表 + 模块 / 优先级标签 + 搜索过滤
2. 执行结果：通过率、通过 / 失败 / 跳过统计、耗时
3. 报告详情：每条用例的结果、失败信息、执行时长

设计取舍：为什么用「静态 HTML + 内嵌 JSON」而不是起 Web 服务？
—— 零依赖（不需要 Flask/Node）、可以直接丢到 GitHub Pages、也能当附件发给别人。
需要登录鉴权、历史趋势、定时调度时，再在此基础上加后端。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import os
import sys
from collections import Counter

OUTCOME_LABEL = {
    "passed": "通过",
    "failed": "失败",
    "error": "错误",
    "skipped": "跳过",
    "xfailed": "预期失败",
    "xpassed": "预期通过",
}


def _fmt_duration(seconds) -> str:
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return "-"
    if total < 1:
        return f"{total * 1000:.0f} ms"
    if total < 60:
        return f"{total:.1f} s"
    return f"{int(total // 60)}m{int(total % 60):02d}s"


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _extract_tests(report: dict) -> list:
    """从 pytest-json-report 的结构里抽出用例列表。"""
    tests = []
    for test in report.get("tests", []):
        nodeid = test.get("nodeid", "")
        # nodeid 形如 tests/test_account.py::test_login_success
        file_part, _, name = nodeid.partition("::")
        keywords = test.get("keywords") or []
        marks = [k for k in keywords
                 if k in ("smoke", "account", "payment", "network", "regression")]
        tests.append({
            "nodeid": nodeid,
            "file": file_part,
            "name": name or nodeid,
            "outcome": test.get("outcome", "unknown"),
            "duration": test.get("call", {}).get("duration", 0.0)
                        if isinstance(test.get("call"), dict)
                        else test.get("duration", 0.0),
            "marks": marks,
            "message": _short_message(test),
        })
    return tests


def _short_message(test: dict) -> str:
    """取出失败原因的第一行，避免把整个堆栈塞进页面。"""
    for phase in ("call", "setup", "teardown"):
        info = test.get(phase)
        if isinstance(info, dict) and info.get("outcome") == "failed":
            crash = info.get("crash") or {}
            message = crash.get("message") or info.get("longreprtext") or ""
            first = str(message).strip().splitlines()
            if first:
                return first[0][:300]
    return ""


def render_html(report: dict, source_name: str) -> str:
    tests = _extract_tests(report)
    summary = report.get("summary", {}) or {}
    total = summary.get("total", len(tests))
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    error = summary.get("error", 0)
    skipped = summary.get("skipped", 0)
    rate = (passed / total * 100) if total else 0.0
    started = report.get("created", "")
    duration = _fmt_duration(report.get("duration", 0))

    if rate >= 100:
        badge, badge_cls = "全部通过", "ok"
    elif rate >= 80:
        badge, badge_cls = "基本通过", "warn"
    else:
        badge, badge_cls = "存在失败", "bad"

    rows = []
    for t in sorted(tests, key=lambda x: (x["outcome"] != "failed",
                                          x["outcome"] != "error",
                                          x["nodeid"])):
        marks = " ".join(f'<span class="tag">{html.escape(m)}</span>'
                         for m in t["marks"]) or '<span class="tag muted">-</span>'
        outcome = t["outcome"]
        label = OUTCOME_LABEL.get(outcome, outcome)
        msg = html.escape(t["message"]) if t["message"] else ""
        msg_html = (f'<div class="msg">{msg}</div>' if msg else "")
        rows.append(
            f'<tr class="row-{html.escape(outcome)}">'
            f'<td><span class="pill {html.escape(outcome)}">{html.escape(label)}</span></td>'
            f"<td><code>{html.escape(t['file'])}</code></td>"
            f"<td>{html.escape(t['name'])}</td>"
            f"<td>{marks}</td>"
            f'<td class="num">{_fmt_duration(t["duration"])}</td>'
            f"<td>{msg_html}</td>"
            f"</tr>"
        )

    modules = Counter(t["file"] for t in tests)
    module_items = "".join(
        f'<div class="mod"><span>{html.escape(os.path.basename(k))}</span>'
        f"<b>{v}</b></div>"
        for k, v in sorted(modules.items())
    )

    generated = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>质量看板 · 测试执行报告</title>
<style>
:root {{
  --bg:#0f1420; --card:#171e2e; --line:#263049; --fg:#e8ecf5;
  --muted:#8b97ad; --ok:#3ecf8e; --bad:#ff6b6b; --warn:#ffb84d; --skip:#7f8ca3;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; padding:28px; background:var(--bg); color:var(--fg);
  font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
}}
.wrap {{ max-width:1180px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 4px; }}
.sub {{ color:var(--muted); font-size:13px; margin-bottom:22px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:22px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.card .k {{ color:var(--muted); font-size:12px; }}
.card .v {{ font-size:26px; font-weight:600; margin-top:2px; }}
.card .v.ok {{ color:var(--ok); }} .card .v.bad {{ color:var(--bad); }}
.card .v.warn {{ color:var(--warn); }} .card .v.skip {{ color:var(--skip); }}
.badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; }}
.badge.ok {{ background:rgba(62,207,142,.15); color:var(--ok); }}
.badge.warn {{ background:rgba(255,184,77,.15); color:var(--warn); }}
.badge.bad {{ background:rgba(255,107,107,.15); color:var(--bad); }}
.mods {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:18px; }}
.mod {{ background:var(--card); border:1px solid var(--line); border-radius:8px;
       padding:7px 12px; font-size:12px; color:var(--muted); display:flex; gap:8px; }}
.mod b {{ color:var(--fg); }}
.bar {{ height:8px; background:#222b40; border-radius:99px; overflow:hidden; margin-bottom:22px; }}
.bar > i {{ display:block; height:100%; background:linear-gradient(90deg,#3ecf8e,#57d3ff); }}
table {{ width:100%; border-collapse:collapse; background:var(--card);
        border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-size:12px; color:var(--muted); font-weight:600; background:#141b2a; }}
tr:last-child td {{ border-bottom:none; }}
td.num {{ white-space:nowrap; color:var(--muted); font-variant-numeric:tabular-nums; }}
code {{ font-family:ui-monospace,Consolas,monospace; font-size:12px; color:#9fb4d8; }}
.pill {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:12px; font-weight:600; }}
.pill.passed {{ background:rgba(62,207,142,.15); color:var(--ok); }}
.pill.failed,.pill.error {{ background:rgba(255,107,107,.15); color:var(--bad); }}
.pill.skipped {{ background:rgba(127,140,163,.18); color:var(--skip); }}
.tag {{ display:inline-block; padding:1px 7px; margin:1px 3px 1px 0; border-radius:5px;
       background:#222b40; color:#9fb4d8; font-size:11px; }}
.tag.muted {{ background:transparent; color:var(--muted); }}
.msg {{ margin-top:5px; font-size:12px; color:#ffb4b4; white-space:pre-wrap; }}
tr.row-failed,tr.row-error {{ background:rgba(255,107,107,.05); }}
.foot {{ margin-top:16px; color:var(--muted); font-size:12px; }}
</style>
</head>
<body><div class="wrap">

<h1>质量看板 · 测试执行报告</h1>
<div class="sub">
  数据源：<code>{html.escape(source_name)}</code> · 执行时间：{html.escape(str(started) or "-")} ·
  生成时间：{generated} · 总耗时：{duration}
  &nbsp;&nbsp;<span class="badge {badge_cls}">{badge}</span>
</div>

<div class="cards">
  <div class="card"><div class="k">用例总数</div><div class="v">{total}</div></div>
  <div class="card"><div class="k">通过</div><div class="v ok">{passed}</div></div>
  <div class="card"><div class="k">失败</div><div class="v bad">{failed + error}</div></div>
  <div class="card"><div class="k">跳过</div><div class="v skip">{skipped}</div></div>
  <div class="card"><div class="k">通过率</div><div class="v {'ok' if rate >= 100 else 'warn' if rate >= 80 else 'bad'}">{rate:.1f}%</div></div>
</div>

<div class="bar"><i style="width:{rate:.1f}%"></i></div>

<div class="mods">{module_items}</div>

<table>
<thead><tr>
  <th>结果</th><th>文件</th><th>用例</th><th>标签</th><th>耗时</th><th>失败信息</th>
</tr></thead>
<tbody>
{chr(10).join(rows) if rows else '<tr><td colspan="6" style="color:var(--muted)">没有用例数据</td></tr>'}
</tbody>
</table>

<div class="foot">
  提示：用 <code>pytest --json-report --json-report-file=reports/report.json</code> 生成数据源，
  再运行 <code>python tools/build_dashboard.py</code> 生成本页面。<br>
  标签来自 pytest marker：smoke / account / payment / network / regression。
</div>

</div></body></html>
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="把 pytest-json-report 转成质量看板网页")
    parser.add_argument("--input", "-i", default="reports/report.json",
                        help="pytest-json-report 生成的 JSON 路径")
    parser.add_argument("--output", "-o", default="reports/report.html",
                        help="输出的 HTML 路径")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"[错误] 找不到数据源：{args.input}")
        print("先跑：pytest --json-report --json-report-file=reports/report.json")
        return 1

    report = _load(args.input)
    page = render_html(report, os.path.basename(args.input))

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(page)

    summary = report.get("summary", {}) or {}
    print(f"[完成] 已生成 {args.output}")
    print(f"       用例 {summary.get('total', 0)} · "
          f"通过 {summary.get('passed', 0)} · "
          f"失败 {summary.get('failed', 0)} · "
          f"跳过 {summary.get('skipped', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
