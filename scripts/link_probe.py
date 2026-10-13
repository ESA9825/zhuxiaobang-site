"""Enumerate every page the site links to, from the rendered DOM.

Piped into `browser-harness`. Visits each SPA route, walks the whole page, and
collects every anchor (href, text) plus every resource URL the page loaded, so
the page inventory is derived from what the site actually offers rather than
from a guessed list.

  ZXB_ORIGIN=https://api3-normal-lq.zhuxiaobang.com ZXB_OUT=truth/links.json
"""

import json
import os
import time

origin = os.environ["ZXB_ORIGIN"]
out = os.environ["ZXB_OUT"]
routes = os.environ.get("ZXB_ROUTES", "/site/home,/site/about,/site/institute,/site/decorateTips").split(",")

COLLECT = r"""
(function () {
  var anchors = Array.prototype.slice.call(document.querySelectorAll('a[href]')).map(function (a) {
    return {href: a.href, text: (a.innerText || '').trim().slice(0, 60)};
  });
  return JSON.stringify({
    title: document.title,
    anchors: anchors,
    resources: performance.getEntriesByType('resource').map(function (r) { return r.name; })
  });
})()
"""

cdp("Page.enable")
cdp("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)

results = {}
seen = set()
first = True
for route in routes:
    url = origin + route
    if first:
        new_tab(url)
        first = False
    else:
        goto_url(url)
    wait_for_load()
    wait_for_network_idle(timeout=25)
    total = js("document.documentElement.scrollHeight") or 0
    for i in range(6):
        try:
            js("window.scrollTo(0, %d)" % int(total * (i + 1) / 6))
        except Exception as exc:  # noqa: BLE001 - a busy renderer must not kill the crawl
            print("scroll %d on %s failed: %s" % (i, route, exc))
        time.sleep(0.7)
    js("window.scrollTo(0, 0)")
    time.sleep(1.0)

    data = json.loads(js(COLLECT))
    results[route] = data
    for a in data["anchors"]:
        seen.add((a["href"], a["text"]))
    print("LINKS %-22s anchors=%d resources=%d" % (route, len(data["anchors"]), len(data["resources"])))

with open(out, "w", encoding="utf-8") as fh:
    json.dump({"origin": origin, "routes": results, "unique_anchors": sorted(seen)}, fh, ensure_ascii=False, indent=1)
print("WROTE", out, "unique anchors:", len(seen))
