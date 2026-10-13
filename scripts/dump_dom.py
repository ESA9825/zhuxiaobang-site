"""Dump the rendered DOM of one route for a textual comparison.

Piped into `browser-harness`:
  ZXB_ORIGIN=https://www.zhuxiaobang.com ZXB_DOM_OUT=/tmp/live-dom.html
  ZXB_NORM_MAP=mirror/REWRITES.json   (mirror only; restores original URLs)
"""

import json
import os
import re
import time

origin = os.environ["ZXB_ORIGIN"]
route = os.environ.get("ZXB_ROUTE", "/site/home")
dest = os.environ["ZXB_DOM_OUT"]

LOCAL_TO_ORIGINAL = {}
norm_path = os.environ.get("ZXB_NORM_MAP", "")
if norm_path and os.path.exists(norm_path):
    rules = json.load(open(norm_path, encoding="utf-8"))["rules"]
    for original_key, local_value in rules.items():
        LOCAL_TO_ORIGINAL[local_value] = "//" + original_key


def evalval(expr, retries=3):
    for _ in range(retries):
        try:
            r = cdp("Runtime.evaluate", _response_timeout=30, expression=expr, returnByValue=True)
            return (r.get("result") or {}).get("value")
        except Exception:  # noqa: BLE001
            time.sleep(1.0)
    return None


cdp("Page.enable")
cdp("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)
cdp("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
cdp("Page.addScriptToEvaluateOnNewDocument", source="""
(function () {
  function inject() {
    if (!document.head) { return setTimeout(inject, 5); }
    var s = document.createElement('style');
    s.textContent = '*,*::before,*::after{animation:none !important;transition:none !important}';
    document.head.appendChild(s);
  }
  inject();
})();
""")

new_tab(origin + route)
wait_for_load()
wait_for_network_idle(timeout=25)

scroll_frac = float(os.environ.get("ZXB_SCROLL", "0"))
if scroll_frac:
    total = evalval("document.documentElement.scrollHeight") or 0
    evalval("window.scrollTo(0, %d)" % int(max(0, total - 900) * scroll_frac))
    evalval("window.dispatchEvent(new Event('scroll'))")
time.sleep(2.5)

html = evalval("document.body.innerHTML") or ""
for local in sorted(LOCAL_TO_ORIGINAL, key=len, reverse=True):
    html = html.replace(local, LOCAL_TO_ORIGINAL[local])
for pattern, repl in (
    (re.compile(r'data-rc-id="[^"]*"'), 'data-rc-id="X"'),
    (re.compile(r'\b(href|src|srcset|poster|data-src|content)="[^"]*"'), r'\1="U"'),
    (re.compile(r'\s*\btarget="[^"]*"'), ''),
    (re.compile(r'id="video_[A-Za-z0-9]*"'), 'id="video_X"'),
    # local mirror patch (injected CSS), not part of the original site
    (re.compile(r'<style data-mirror-patch="[^"]*">[^<]*</style>'), ''),
    (re.compile(r'<script data-mirror-patch="[^"]*">.*?</script>', re.S), ''),
):
    html = pattern.sub(repl, html)
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(html)
print("WROTE", dest, len(html), "bytes")
