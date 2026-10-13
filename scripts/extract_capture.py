#!/usr/bin/env python3
"""Turn the exported REA evidence bundle into a flat, auditable ground truth.

Reads $ZXB_CAPTURE (default site-clone/capture/rea-session.json) and writes into
site-clone/truth/:

  routes.json           per route: steps, transactions (status, type, url, body state)
  transactions.tsv      one row per transaction across every captured route
  live-urls.txt         unique URLs seen on the wire
  bodies/<host>/<path>  response bodies exactly as the browser received them
  screenshots/end.png   final viewport screenshot of the scenario
  SUMMARY.md            counts, failures, and origin breakdown
"""

import base64
import json
import os
import re
from collections import Counter, defaultdict
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURE = os.environ.get("ZXB_CAPTURE", os.path.join(BASE, "capture", "rea-session.json"))
OUT = os.environ.get("ZXB_TRUTH", os.path.join(BASE, "truth"))
os.makedirs(OUT, exist_ok=True)


def safe_path(host, path, query):
    p = path.lstrip("/") or "index"
    if query:
        p += "__" + re.sub(r"[^A-Za-z0-9=_.&-]", "_", query)[:120]
    return os.path.join(host, p)


def main():
    bundle = json.load(open(CAPTURE, encoding="utf-8"))
    records = [r for r in bundle["records"] if r["operation"] == "capture_browser_scenario"]
    if not records:
        raise SystemExit("no capture_browser_scenario record in %s" % CAPTURE)

    routes_out = {}
    rows = []
    all_urls = set()
    body_count = 0
    body_bytes = 0
    failures = []

    for rec in records:
        nr = rec["normalized_result"]
        scenario = json.dumps(rec.get("parameters", {}).get("actions"), ensure_ascii=False)
        items = nr["events"]["items"]

        reqs, resps, contents = {}, {}, defaultdict(dict)
        for it in items:
            kind = it.get("kind")
            tid = it.get("transaction_id")
            if kind == "request":
                reqs[tid] = it
            elif kind == "response":
                resps[tid] = it
            elif kind == "network-content":
                contents[tid][it.get("phase")] = it
            elif kind in ("request-failed", "request-unfinished"):
                failures.append(
                    {
                        "kind": kind,
                        "step_index": it.get("step_index"),
                        "transaction_id": tid,
                        "url": (it.get("url") or {}).get("url"),
                        "failure": it.get("failure"),
                    }
                )

        # step_index -> route url, from the ordered steps the scenario recorded
        step_urls = {}
        for si, step in enumerate(nr.get("steps") or []):
            u = ((step.get("after_url") or {}).get("url")) or ""
            if u:
                step_urls[si] = u

        per_step = defaultdict(lambda: {"route": None, "transactions": []})
        for tid, req in reqs.items():
            si = req.get("step_index")
            url = (req.get("url") or {}).get("url") or ""
            resp = resps.get(tid) or {}
            content = (contents.get(tid) or {}).get("response") or {}
            state = (content.get("body") or {}).get("state")
            blob = (content.get("body") or {}).get("content")
            dest = None
            if state == "captured" and blob:
                pr = urlparse(url)
                dest = safe_path(pr.netloc, pr.path, pr.query)
                full = os.path.join(OUT, "bodies", dest)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                data = base64.b64decode(blob)
                with open(full, "wb") as fh:
                    fh.write(data)
                body_count += 1
                body_bytes += len(data)

            entry = {
                "transaction_id": tid,
                "method": req.get("method"),
                "resource_type": req.get("resource_type"),
                "status": resp.get("status"),
                "url": url,
                "body_state": state,
                "body_path": dest,
                "body_bytes": len(blob) if blob else 0,
                "failure": req.get("failure"),
            }
            per_step[si]["route"] = step_urls.get(si)
            per_step[si]["transactions"].append(entry)
            all_urls.add(url)
            rows.append(
                (
                    step_urls.get(si, "?"),
                    si if si is not None else -1,
                    req.get("method"),
                    entry["resource_type"],
                    resp.get("status"),
                    state,
                    url,
                )
            )

        for si, data in sorted(per_step.items(), key=lambda kv: (kv[0] is None, kv[0])):
            route = data["route"] or "unknown"
            routes_out.setdefault(route, {"steps": [], "transactions": []})
            routes_out[route]["steps"].append(si)
            routes_out[route]["transactions"].extend(data["transactions"])

        # final screenshot artifact, if the scenario captured one
        for step in reversed(nr.get("steps") or []):
            shot = ((step.get("artifacts") or {}).get("screenshot") or {})
            if shot.get("state") == "captured":
                data = (shot.get("value") or {}).get("data_base64")
                if data:
                    os.makedirs(os.path.join(OUT, "screenshots"), exist_ok=True)
                    path = os.path.join(OUT, "screenshots", "live-end.png")
                    with open(path, "wb") as fh:
                        fh.write(base64.b64decode(data))
                break

    for route, data in routes_out.items():
        data["transaction_count"] = len(data["transactions"])
        data["status_counts"] = dict(Counter(t["status"] for t in data["transactions"]))

    with open(os.path.join(OUT, "routes.json"), "w", encoding="utf-8") as fh:
        json.dump(routes_out, fh, ensure_ascii=False, indent=1)

    with open(os.path.join(OUT, "transactions.tsv"), "w", encoding="utf-8") as fh:
        fh.write("route\tstep\tmethod\tresource_type\tstatus\tbody_state\turl\n")
        for r in sorted(rows, key=lambda r: (r[1], r[6])):
            fh.write("\t".join(str(x) for x in r) + "\n")

    with open(os.path.join(OUT, "live-urls.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(all_urls)) + "\n")

    origins = Counter(urlparse(u).netloc for u in all_urls)
    lines = [
        "# 线上抓取真值（REA capture_browser_scenario）",
        "",
        "- 输入证据包：`%s`" % os.path.relpath(CAPTURE, BASE),
        "- 记录数：%d 个 scenario" % len(records),
        "- 唯一 URL：%d 条" % len(all_urls),
        "- 已落盘响应体：%d 个 / %.1f MiB" % (body_count, body_bytes / 1048576),
        "- 抓取失败事务：%d" % len(failures),
        "",
        "## 逐域统计",
        "",
    ]
    for host, n in origins.most_common():
        lines.append("- `%s` — %d 条 URL" % (host, n))
    lines += ["", "## 逐路由事务数", ""]
    for route, data in routes_out.items():
        lines.append(
            "- `%s` — %d 条事务 %s"
            % (route, data["transaction_count"], json.dumps(data["status_counts"]))
        )
    if failures:
        lines += ["", "## 失败/未完成事务", ""]
        for f in failures:
            lines.append("- step %s %s `%s` — %s" % (f["step_index"], f["kind"], f["url"], f["failure"]))
    lines += ["", "## 复现", "", "```bash", "python3 scripts/extract_capture.py", "```", ""]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(json.dumps(
        {
            "routes": len(routes_out),
            "unique_urls": len(all_urls),
            "bodies": body_count,
            "body_mib": round(body_bytes / 1048576, 1),
            "failures": len(failures),
            "origins": dict(origins),
        },
        ensure_ascii=False,
        indent=1,
    ))


if __name__ == "__main__":
    main()
