"""Capture every route of zhuxiaobang.com through the browser-harness CDP session.

Piped into `browser-harness`, so the helpers (cdp, js, new_tab, goto_url,
wait_for_load, wait_for_network_idle, drain_events) are pre-imported globals.

Outputs, per route, into $ZXB_OUTDIR:
  <slug>.json  network transactions (url/method/status/headers/body) + rendered DOM
  <slug>.png   viewport screenshot after the route settles

Env:
  ZXB_OUTDIR   output directory (required)
  ZXB_ROUTES   comma separated paths, default the five known routes
  ZXB_SCROLLS  scroll steps used to trigger lazy loading, default 10
"""

import base64
import json
import os
import time

outdir = os.environ["ZXB_OUTDIR"]
routes = os.environ.get(
    "ZXB_ROUTES",
    "/site/home,/site/about,/site/institute,/site/decorateTips,/site/notfound-probe",
).split(",")
scrolls = int(os.environ.get("ZXB_SCROLLS", "10"))
origin = os.environ.get("ZXB_ORIGIN", "https://www.zhuxiaobang.com")

os.makedirs(outdir, exist_ok=True)


def slug(path):
    s = path.strip("/").replace("/", "_") or "root"
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in s)


def collect_events():
    """Fold buffered CDP network events into ordered transactions with bodies."""
    try:
        events = drain_events() or []
    except Exception as exc:  # noqa: BLE001 - report, keep capturing
        print("drain_events failed:", exc)
        return []

    order, reqs, resps, failed = [], {}, {}, {}
    for ev in events:
        method = ev.get("method")
        p = ev.get("params") or {}
        rid = p.get("requestId")
        if method == "Network.requestWillBeSent":
            if rid not in reqs:
                order.append(rid)
            reqs[rid] = {
                "url": p.get("request", {}).get("url"),
                "method": p.get("request", {}).get("method"),
                "requestHeaders": p.get("request", {}).get("headers"),
                "postData": p.get("request", {}).get("postData"),
                "resourceType": p.get("type"),
                "initiator": (p.get("initiator") or {}).get("type"),
            }
        elif method == "Network.responseReceived":
            r = p.get("response") or {}
            resps[rid] = {
                "status": r.get("status"),
                "statusText": r.get("statusText"),
                "mimeType": r.get("mimeType"),
                "responseHeaders": r.get("headers"),
                "fromDiskCache": r.get("fromDiskCache"),
                "fromServiceWorker": r.get("fromServiceWorker"),
                "protocol": r.get("protocol"),
                "remoteIPAddress": r.get("remoteIPAddress"),
                "encodedDataLength": r.get("encodedDataLength"),
            }
        elif method == "Network.loadingFailed":
            failed[rid] = {"errorText": p.get("errorText"), "blockedReason": p.get("blockedReason")}

    out = []
    for rid in order:
        txn = dict(reqs.get(rid) or {})
        txn.update(resps.get(rid) or {})
        if rid in failed:
            txn["failed"] = failed[rid]
        body = None
        if rid in resps:
            for attempt in range(3):
                try:
                    body = cdp("Network.getResponseBody", requestId=rid)
                    break
                except Exception:  # noqa: BLE001 - body may be evicted or streaming
                    time.sleep(0.3)
        if body:
            txn["bodyBase64Encoded"] = body.get("base64Encoded")
            txn["body"] = body.get("body")
        out.append(txn)
    return out


cdp("Page.enable")
cdp(
    "Network.enable",
    maxTotalBufferSize=500 * 1024 * 1024,
    maxResourceBufferSize=200 * 1024 * 1024,
)

first = True
summary = []
for route in routes:
    url = origin + route
    try:
        drain_events()
    except Exception:  # noqa: BLE001
        pass

    if first:
        new_tab(url)
        first = False
    else:
        goto_url(url)
    wait_for_load()
    wait_for_network_idle(timeout=25)

    height = js("document.body.scrollHeight") or 0
    for i in range(scrolls):
        js("window.scrollTo(0, %d)" % int(height * (i + 1) / scrolls))
        time.sleep(1.0)
    js("window.scrollTo(0, 0)")
    time.sleep(1.5)
    try:
        wait_for_network_idle(timeout=15)
    except Exception:  # noqa: BLE001
        pass

    title = js("document.title")
    final_url = js("location.href")
    dom = js("document.documentElement.outerHTML")
    html = js("document.body.innerHTML")
    txns = collect_events()

    name = slug(route)
    shot = os.path.join(outdir, name + ".png")
    try:
        data = cdp("Page.captureScreenshot", format="png", captureBeyondViewport=False)
        with open(shot, "wb") as fh:
            fh.write(base64.b64decode(data["data"]))
    except Exception as exc:  # noqa: BLE001
        print("screenshot failed for", route, exc)
        shot = None

    payload = {
        "route": route,
        "finalUrl": final_url,
        "title": title,
        "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "viewport": js("JSON.stringify({w:innerWidth,h:innerHeight,dpr:devicePixelRatio,scrollHeight:document.body.scrollHeight})"),
        "screenshot": shot,
        "dom": dom,
        "bodyHtml": html,
        "transactions": txns,
    }
    with open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    kinds = {}
    for t in txns:
        kinds[t.get("resourceType")] = kinds.get(t.get("resourceType"), 0) + 1
    summary.append((route, final_url, len(txns), kinds, len(html or "")))
    print("CAPTURED", route, "->", final_url, "txns", len(txns), kinds)

print("SUMMARY", json.dumps(summary, ensure_ascii=False))
