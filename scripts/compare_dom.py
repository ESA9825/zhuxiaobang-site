#!/usr/bin/env python3
"""Compare two scroll_probe outputs (route -> scroll offset -> DOM hash).

  python3 scripts/compare_dom.py truth/live-dom.json truth/mirror-dom.json

Prints one line per route with a match/mismatch per scroll offset, so a
scroll-driven widget cannot make a whole page look different. Run it with two
live captures as a control: what the site fails to reproduce against itself is
the noise floor for any mirror comparison.
"""

import json
import sys


def load(path):
    data = json.load(open(path, encoding="utf-8"))
    return data.get("origin", "?"), data["routes"]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    left_origin, left = load(sys.argv[1])
    right_origin, right = load(sys.argv[2])

    total = matched = 0
    print("left : %s" % left_origin)
    print("right: %s" % right_origin)
    for route in left:
        lstates = left[route]
        rstates = right.get(route)
        if not rstates:
            print("%-24s missing on the right" % route)
            continue
        marks = []
        for l, r in zip(lstates, rstates):
            # only states both captures reproduced are comparable
            if not (l.get("stable", True) and r.get("stable", True)):
                marks.append("%s%s" % ("~", l["offset"]))
                continue
            same = l["hash"] == r["hash"]
            total += 1
            matched += 1 if same else 0
            marks.append("%s%s" % ("=" if same else "!", l["offset"]))
        print("%-24s %s" % (route, " ".join(marks)))

    print("\nscroll states identical: %d/%d" % (matched, total))
    return 0 if matched == total else 1


if __name__ == "__main__":
    sys.exit(main())
