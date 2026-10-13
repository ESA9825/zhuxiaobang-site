"""Compare the SPA's DOM at identical scroll offsets on both origins.

Piped into `browser-harness`. Scroll-driven widgets (progress timelines, lazy
sections) are not comparable by a single screenshot, so this walks a fixed set
of offsets and hashes the rendered DOM at each one. Equal hashes at equal
offsets mean the same markup, in the same state.

  ZXB_ORIGIN=https://www.zhuxiaobang.com ZXB_OUT=truth/live-dom.json
"""

import hashlib
import json
import os
import re
import time

origin = os.environ["ZXB_ORIGIN"]
out = os.environ["ZXB_OUT"]
routes = os.environ.get("ZXB_ROUTES", "/site/home,/site/about,/site/institute,/site/decorateTips").split(",")
offsets = [float(x) for x in os.environ.get("ZXB_OFFSETS", "0,0.25,0.5,0.75,1.0").split(",")]

# The mirror is a local rewrite of the original URLs, and URLs appear inside DOM
# attributes. Mapping the local paths back to the original URLs before hashing
# turns "did the rewrite change the markup" into a real comparison.
LOCAL_TO_ORIGINAL = {}
norm_path = os.environ.get("ZXB_NORM_MAP", "")
if norm_path and os.path.exists(norm_path):
    rules = json.load(open(norm_path, encoding="utf-8"))["rules"]
    for original_key, local_value in rules.items():
        LOCAL_TO_ORIGINAL[local_value] = "//" + original_key


def normalize(html):
    for local in sorted(LOCAL_TO_ORIGINAL, key=len, reverse=True):
        if local in html:
            html = html.replace(local, LOCAL_TO_ORIGINAL[local])
    return html


# Two things legitimately differ between two loads of the same page: the UI
# library's random `data-rc-id` values, and URL-valued attributes (which this
# mirror rewrites on purpose). Masking them leaves structure, text and styling,
# which is what equivalence should be judged on.
MASKERS = (
    (re.compile(r'data-rc-id="[^"]*"'), 'data-rc-id="X"'),
    (re.compile(r'\b(href|src|srcset|poster|data-src|content)="[^"]*"'), r'\1="U"'),
    # the UI library only adds target="_blank" to URLs it considers external,
    # so rewriting content links to local paths drops it; see VERIFY.md
    (re.compile(r'\s*\btarget="[^"]*"'), ''),
    (re.compile(r'id="video_[A-Za-z0-9]*"'), 'id="video_X"'),
    # local mirror patch (injected CSS), not part of the original site
    (re.compile(r'<style data-mirror-patch="[^"]*">[^<]*</style>'), ''),
    (re.compile(r'<script data-mirror-patch="[^"]*">.*?</script>', re.S), ''),
)


def mask(html):
    for pattern, repl in MASKERS:
        html = pattern.sub(repl, html)
    return html

cdp("Page.enable")
cdp("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)
cdp("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])


def evalval(expr, retries=3):
    """Runtime.evaluate with an explicit budget; a busy renderer must not abort."""
    last = None
    for _ in range(retries):
        try:
            r = cdp("Runtime.evaluate", _response_timeout=30, expression=expr, returnByValue=True, awaitPromise=True)
            return (r.get("result") or {}).get("value")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.0)
    print("  eval failed:", expr[:60], last)
    return None


def snapshot():
    html = mask(normalize(evalval("document.body.innerHTML") or ""))
    return {
        "hash": hashlib.sha256(html.encode("utf-8")).hexdigest()[:32],
        "bytes": len(html),
        "nodes": evalval("document.getElementsByTagName('*').length"),
        "text": evalval("document.body.innerText") or "",
    }


results = {}
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
    total = evalval("document.documentElement.scrollHeight") or 0

    states = []
    for frac in offsets:
        y = int(max(0, total - 900) * frac)
        evalval("window.scrollTo(0, %d)" % y)
        evalval("window.dispatchEvent(new Event('scroll'))")
        time.sleep(2.0)
        snap = snapshot()
        # a state only counts if the page reproduces it: media players and other
        # async widgets keep mutating for a while after the scroll
        time.sleep(1.5)
        again = snapshot()
        snap["stable"] = snap["hash"] == again["hash"]
        snap["offset"] = frac
        snap["scrollY"] = evalval("window.scrollY")
        snap["textHash"] = hashlib.sha256(snap.pop("text").encode("utf-8")).hexdigest()[:32]
        states.append(snap)
    results[route] = states
    print("SCROLL %-22s %s" % (route, " ".join(s["hash"][:8] for s in states)))

with open(out, "w", encoding="utf-8") as fh:
    json.dump({"origin": origin, "routes": results}, fh, ensure_ascii=False, indent=1)
print("WROTE", out)
