#!/bin/bash
# Byte-level DOM comparison per route, at a matched, settled state.
#
# The scroll-offset probe compares a *sequence* of states and is therefore
# sensitive to timers; this check drives both origins to the same explicit
# state (top or bottom of the page) and requires the masked, URL-normalised DOM
# to be byte-identical. Results go to truth/dom-settled.json.
#
#   bash scripts/settled_dom_check.sh [scroll_fraction]
set -uo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"

PORT="${ZXB_PORT:-8899}"
CDP="${BU_CDP_URL:-http://127.0.0.1:9333}"
SCROLL="${1:-1.0}"
ROUTES=${ZXB_ROUTES:-"/site/home,/site/about,/site/institute,/site/decorateTips"}
TMP="${TMPDIR:-/tmp}/zxb-settled"
mkdir -p "$TMP"

{
  printf '{"scroll": %s, "routes": {' "$SCROLL"
  first=1
  IFS=',' read -r -a list <<< "$ROUTES"
  for route in "${list[@]}"; do
    slug="$(echo "$route" | tr -c 'A-Za-z0-9' '-')"
    ZXB_ROUTE="$route" ZXB_SCROLL="$SCROLL" ZXB_ORIGIN="https://www.zhuxiaobang.com" \
      ZXB_DOM_OUT="$TMP/live$slug.html" BU_CDP_URL="$CDP" \
      browser-harness < scripts/dump_dom.py > /dev/null 2>&1
    ZXB_ROUTE="$route" ZXB_SCROLL="$SCROLL" ZXB_ORIGIN="http://127.0.0.1:${PORT}" \
      ZXB_NORM_MAP="$here/mirror/REWRITES.json" ZXB_DOM_OUT="$TMP/mirror$slug.html" BU_CDP_URL="$CDP" \
      browser-harness < scripts/dump_dom.py > /dev/null 2>&1
    if cmp -s "$TMP/live$slug.html" "$TMP/mirror$slug.html"; then
      status=identical
    else
      status=differs
    fi
    bytes=$(wc -c < "$TMP/live$slug.html" | tr -d ' ')
    [ "$first" -eq 0 ] && printf ','
    first=0
    printf '"%s": {"bytes": %s, "status": "%s"}' "$route" "$bytes" "$status"
    printf '  %-24s %s (%s bytes)\n' "$route" "$status" "$bytes" >&2
  done
  printf '}}\n'
} > truth/dom-settled.json

echo "wrote truth/dom-settled.json"
