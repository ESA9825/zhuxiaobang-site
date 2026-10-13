#!/bin/bash
# One-command verification gate for the zhuxiaobang.com mirror.
#
#   bash scripts/verify_all.sh
#
# Steps: static reference audit, live-vs-mirror pixel/metric comparison per
# route, DOM comparison at several scroll offsets, live-vs-live control runs
# that establish how much of any difference is the site's own noise, and one
# aggregated verdict (scripts/final_report.py).
#
# Requires: the browser-harness daemon (BU_CDP_URL / browser-harness-chrome) and
# network access for the live side. Takes roughly 20 minutes.
set -uo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"

PORT="${ZXB_PORT:-8899}"
CDP="${BU_CDP_URL:-http://127.0.0.1:9333}"
LIVE="https://www.zhuxiaobang.com"
MIRROR="http://127.0.0.1:${PORT}"
SPA="/site/home,/site/about,/site/institute,/site/decorateTips"
PAGES="/zhuhaojia,/faas/ugc/private_protocal_text.html,/faas/ugc/user_protocal.html,/faas/ugc/third_party_sdk.html,/faas/ugc/sensitive_personal_message.html,/faas/ugc/account_logout.html,/faas/ugc/apply_and_use.html"
PY_IMG="/Users/esa/.local/share/uv/tools/browser-harness/bin/python"
[ -x "$PY_IMG" ] || PY_IMG=python3

fail=0
step() { printf '\n=== %s\n' "$1"; }

step "1/6 static reference audit"
python3 scripts/audit_refs.py || fail=1

step "2/6 starting the mirror on port ${PORT}"
python3 serve.py --port "$PORT" --log truth/mirror-access-verify.log &
server_pid=$!
trap 'kill $server_pid 2>/dev/null' EXIT
for _ in $(seq 1 20); do
  curl -sf -o /dev/null "$MIRROR/" && break
  sleep 0.5
done
curl -sf -o /dev/null "$MIRROR/" || { echo "mirror did not start"; exit 1; }

probe() { # origin, routes, out, shots
  ZXB_ORIGIN="$1" ZXB_ROUTES="$2" ZXB_OUT="$3" ZXB_SHOTS="$4" \
    BU_CDP_URL="$CDP" browser-harness < scripts/route_probe.py
}

step "3/6 probing the SPA routes on both origins"
probe "$LIVE"   "$SPA"   truth/live-probe.json   truth/shots/live
probe "$MIRROR" "$SPA"   truth/mirror-probe.json truth/shots/mirror
probe "$LIVE"   "$SPA"   truth/live-spa2.json    truth/shots/live-spa2
probe "$LIVE"   "$SPA"   truth/live-spa3.json    truth/shots/live-spa3

step "4/6 probing the content pages on both origins"
probe "$LIVE"   "$PAGES" truth/live-pages.json   truth/shots/live-pages
probe "$MIRROR" "$PAGES" truth/mirror-pages.json truth/shots/mirror-pages
probe "$LIVE"   "$PAGES" truth/live-pages2.json  truth/shots/live-pages2

step "5/6 pixel and metric comparison"
ZXB_LIVE=truth/live-probe.json ZXB_MIRROR=truth/mirror-probe.json \
  ZXB_CONTROL="truth/live-probe.json,truth/live-spa2.json;truth/live-spa2.json,truth/live-spa3.json" \
  ZXB_VERIFY_DIR=truth/verify "$PY_IMG" scripts/diff_probes.py || fail=1
ZXB_LIVE=truth/live-pages.json ZXB_MIRROR=truth/mirror-pages.json \
  ZXB_CONTROL="truth/live-pages.json,truth/live-pages2.json" \
  ZXB_VERIFY_DIR=truth/verify-pages "$PY_IMG" scripts/diff_probes.py || fail=1
echo "-- control: the live site against itself (explains the remaining deltas)"
ZXB_LIVE=truth/live-probe.json ZXB_MIRROR=truth/live-spa2.json \
  ZXB_VERIFY_DIR=truth/verify-control-spa "$PY_IMG" scripts/diff_probes.py || true

echo "-- extra controls for the two routes that animate continuously"
probe "$LIVE" "/site/about" truth/about-live-1.json truth/shots/about-live-1
probe "$LIVE" "/site/about" truth/about-live-2.json truth/shots/about-live-2
probe "$LIVE" "/zhuhaojia" truth/zhj-live-1.json truth/shots/zhj-live-1
probe "$LIVE" "/zhuhaojia" truth/zhj-live-2.json truth/shots/zhj-live-2

step "6/6 DOM comparison at several scroll offsets"
ZXB_ORIGIN="$LIVE" ZXB_OUT=truth/live-dom.json BU_CDP_URL="$CDP" \
  browser-harness < scripts/scroll_probe.py
ZXB_ORIGIN="$MIRROR" ZXB_NORM_MAP=mirror/REWRITES.json ZXB_OUT=truth/mirror-dom.json \
  BU_CDP_URL="$CDP" browser-harness < scripts/scroll_probe.py
python3 scripts/compare_dom.py truth/live-dom.json truth/mirror-dom.json || true
echo "-- control: the live site against itself"
ZXB_ORIGIN="$LIVE" ZXB_OUT=truth/live-dom2.json ZXB_ROUTES="$SPA" BU_CDP_URL="$CDP" \
  browser-harness < scripts/scroll_probe.py
python3 scripts/compare_dom.py truth/live-dom.json truth/live-dom2.json || true

step "6b/6 settled DOM byte comparison (the decisive DOM check)"
ZXB_PORT="$PORT" BU_CDP_URL="$CDP" bash scripts/settled_dom_check.sh 1.0 || fail=1

step "6c/6 merchant app (verbatim archive) and its offline API fixtures"
python3 - <<PY || fail=1
import sys, urllib.request
base = "http://127.0.0.1:${PORT}"
checks = [
    ("/home?app_entrance=login", "text/html"),
    ("/user/login/", "text/html"),
    ("/archive/merchant/assets/umi.36248b50.js", "javascript"),
    ("/homed/business/bservice/account/getinfo", "application/json"),
    ("/homed/business/bservice/config/navibarButtons", "application/json"),
    ("/passport/aff/web/subject/login_list", "application/json"),
]
bad = []
for path, want in checks:
    try:
        with urllib.request.urlopen(base + path, timeout=15) as r:
            ctype = r.headers.get("Content-Type", "")
            body = r.read(2048)
            if r.status != 200 or want not in ctype or not body:
                bad.append("%s -> %s %s" % (path, r.status, ctype))
    except Exception as exc:
        bad.append("%s -> %s" % (path, exc))
print("   merchant endpoints checked: %d, problems: %d" % (len(checks), len(bad)))
for b in bad:
    print("      %s" % b)
sys.exit(1 if bad else 0)
PY
probe "$MIRROR" "/home?app_entrance=login,/user/login/" truth/merchant-local.json truth/shots/merchant-local
python3 - <<PY || fail=1
import json, sys
d = json.load(open("truth/merchant-local.json"))["routes"]
bad = [r for r, v in d.items() if v["consoleErrors"] or v["failed"] or v["brokenImages"] or v["textLen"] < 300]
# regression guard: the archive's index.html was missing a <script> open tag, which
# printed its source as page text; it must not come back
for r, v in d.items():
    if "originalFetch" in (v.get("textHead") or ""):
        bad.append(r + " (script source visible as text)")
for r, v in d.items():
    print("   %-28s text=%s imgs=%s errors=%s failed=%s" % (r, v["textLen"], v["images"], len(v["consoleErrors"]), len(v["failed"])))
sys.exit(1 if bad else 0)
PY

step "verdict"
echo "404s served during the run: $(grep -c ' 404 ' truth/mirror-access-verify.log 2>/dev/null || echo 0)"
"$PY_IMG" scripts/final_report.py || fail=1
exit "$fail"
