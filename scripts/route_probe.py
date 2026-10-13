"""Probe every route through browser-harness and dump comparable measurements.

Piped into `browser-harness`. Runs the same measurements against the live site
and the local mirror so the two can be diffed:

  ZXB_ORIGIN=https://www.zhuxiaobang.com ZXB_OUT=truth/live-probe.json
  ZXB_ORIGIN=http://127.0.0.1:8899       ZXB_OUT=truth/mirror-probe.json

Per route: document title, text, element/image counts, broken images, resource
count, any resource with status >= 400, and a full-page screenshot.
"""

import base64
import json
import os
import time

origin = os.environ["ZXB_ORIGIN"]
out = os.environ["ZXB_OUT"]
routes = os.environ.get("ZXB_ROUTES", "/site/home,/site/about,/site/institute,/site/decorateTips").split(",")
shot_dir = os.environ.get("ZXB_SHOTS", os.path.join(os.path.dirname(out), "shots", "origin"))
width = int(os.environ.get("ZXB_W", "1440"))
height = int(os.environ.get("ZXB_H", "900"))

os.makedirs(shot_dir, exist_ok=True)

HOOK = """
window.__probe = {errors: [], rejects: []};
window.addEventListener('error', function (e) {
  window.__probe.errors.push(String((e && (e.message || e.type)) || 'error'));
}, true);
window.addEventListener('unhandledrejection', function (e) {
  window.__probe.rejects.push(String((e && e.reason && (e.reason.message || e.reason)) || 'rejection'));
});
// Freeze CSS animation/transition so an animation phase cannot be mistaken for
// a fidelity difference. Applied identically to the live site and the mirror.
(function () {
  function inject() {
    if (!document.head) { return setTimeout(inject, 5); }
    var s = document.createElement('style');
    s.setAttribute('data-probe-freeze', '1');
    s.textContent = '*,*::before,*::after{animation:none !important;transition:none !important}';
    document.head.appendChild(s);
  }
  inject();
})();
"""

MEASURE = r"""
(function () {
  var imgs = Array.prototype.slice.call(document.images);
  var broken = imgs.filter(function (i) { return i.currentSrc && i.complete && i.naturalWidth === 0; });
  var external = Array.prototype.slice.call(document.querySelectorAll('[src],[href]'))
    .map(function (n) { return n.getAttribute('src') || n.getAttribute('href') || ''; })
    .filter(function (u) { return /^(https?:)?\/\//.test(u); });
  var res = performance.getEntriesByType('resource');
  return JSON.stringify({
    title: document.title,
    url: location.href,
    textLen: (document.body.innerText || '').length,
    textHead: (document.body.innerText || '').slice(0, 400),
    // the mirror injects its own <style>/<script data-mirror-patch> nodes; they are a
    // local addition, not part of the site, so they are not counted
    elements: document.getElementsByTagName('*').length -
              document.querySelectorAll('style[data-mirror-patch],script[data-mirror-patch]').length,
    images: imgs.length,
    brokenImages: broken.map(function (i) { return i.currentSrc || i.src; }),
    externalRefs: external,
    resources: res.length,
    resourcePaths: res.map(function (r) { var u = new URL(r.name); return u.host + u.pathname; }),
    failed: res.filter(function (r) { return r.responseStatus >= 400; })
              .map(function (r) { return r.responseStatus + ' ' + r.name; }),
    consoleErrors: (window.__probe && window.__probe.errors) || [],
    rejects: (window.__probe && window.__probe.rejects) || [],
    scrollHeight: document.documentElement.scrollHeight,
    noticeVisible: (document.body.innerText || '').indexOf('\u5173\u505c\u516c\u544a') >= 0
  });
})()
"""


def slug(path):
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in path.strip("/").replace("/", "_")) or "root"


cdp("Page.enable")
cdp("Runtime.enable")
cdp("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
# animations are the one thing screenshots cannot compare deterministically
cdp("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
cdp("Page.addScriptToEvaluateOnNewDocument", source=HOOK)


def evalval(expr, retries=3):
    """Runtime.evaluate with an explicit budget; heavy pages must not abort a run."""
    last = None
    for _ in range(retries):
        try:
            r = cdp("Runtime.evaluate", _response_timeout=30, expression=expr, returnByValue=True)
            return (r.get("result") or {}).get("value")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.0)
    print("  eval failed:", expr[:60], last)
    return None


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
    for i in range(8):
        evalval("window.scrollTo(0, %d)" % int(total * (i + 1) / 8))
        time.sleep(0.8)
    evalval("window.scrollTo(0, 0)")
    evalval("window.dispatchEvent(new Event('scroll'))")
    # let scroll-driven state and any late reflow settle: the measured height
    # must be a stable value, not whatever the last frame happened to be
    time.sleep(2.0)
    height = -1
    stable = 0
    for _ in range(12):
        current = evalval("document.documentElement.scrollHeight") or 0
        stable = stable + 1 if current == height else 0
        height = current
        if stable >= 2:
            break
        time.sleep(1.0)

    data = json.loads(evalval(MEASURE))
    shot = os.path.join(shot_dir, slug(route) + ".png")
    scale_used = None
    # very tall pages exceed the compositor texture limit at 2x, so fall back to
    # a halved scale; the same rule runs on both origins, keeping it comparable
    for scale in (1, 0.5):
        try:
            cap = cdp(
                "Page.captureScreenshot",
                _response_timeout=60,
                format="png",
                captureBeyondViewport=True,
                clip={
                    "x": 0,
                    "y": 0,
                    "width": width,
                    "height": min(data["scrollHeight"], 20000),
                    "scale": scale,
                },
            )
            with open(shot, "wb") as fh:
                fh.write(base64.b64decode(cap["data"]))
            scale_used = scale
            break
        except Exception as exc:  # noqa: BLE001
            if scale == 0.5:
                print("screenshot failed", route, exc)
                shot = None
    data["shotScale"] = scale_used
    data["screenshot"] = shot
    results[route] = data
    print(
        "PROBE %-22s title=%s text=%d imgs=%d broken=%d failed=%d errs=%d h=%d"
        % (
            route,
            (data["title"] or "")[:24],
            data["textLen"],
            data["images"],
            len(data["brokenImages"]),
            len(data["failed"]),
            len(data["consoleErrors"]),
            data["scrollHeight"],
        )
    )

with open(out, "w", encoding="utf-8") as fh:
    json.dump({"origin": origin, "viewport": {"width": width, "height": height}, "routes": results}, fh, ensure_ascii=False, indent=1)
print("WROTE", out)
