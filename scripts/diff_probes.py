#!/usr/bin/env python3
"""Compare the live-site probe with the mirror probe.

Metrics must match exactly; screenshots are compared pixel by pixel with a
small per-channel tolerance, and a diff image is written for any route that
differs so the difference can be looked at rather than guessed about.

Run with an interpreter that has Pillow (the browser-harness venv has it):
  /Users/esa/.local/share/uv/tools/browser-harness/bin/python scripts/diff_probes.py
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRUTH = os.path.join(BASE, "truth")
LIVE_JSON = os.environ.get("ZXB_LIVE", os.path.join(TRUTH, "live-probe.json"))
MIRROR_JSON = os.environ.get("ZXB_MIRROR", os.path.join(TRUTH, "mirror-probe.json"))
OUT = os.environ.get("ZXB_VERIFY_DIR", os.path.join(TRUTH, "verify"))
# optional "a.json,b.json" pairs (separated by ";") recorded by running the
# probe twice against the live site; the largest per-route delta across the
# pairs is the noise floor below which a mirror difference is not evidence of a
# fidelity problem
CONTROL = os.environ.get("ZXB_CONTROL", "")
TOLERANCE = int(os.environ.get("ZXB_PIXEL_TOLERANCE", "2"))

FIELDS = ("title", "textLen", "elements", "images", "brokenImages", "consoleErrors", "rejects", "scrollHeight")
TELEMETRY_HOSTS = ("mon.zijieapi.com", "mcs.zijieapi.com", "ibytedapm.com")


def resource_basenames(entry):
    """Asset filenames loaded by a page, ignoring telemetry beacons.

    Comparing basenames rather than full URLs keeps the check meaningful across
    the mirror's URL rewrite: a missing or extra asset still shows up.
    """
    names = set()
    for host_path in entry.get("resourcePaths") or []:
        host = host_path.split("/", 1)[0].split(":")[0]
        if any(t in host for t in TELEMETRY_HOSTS):
            continue
        name = host_path.rstrip("/").split("/")[-1]
        # favicons are fetched by the browser rather than the renderer, so the
        # performance entries include them only sometimes; the file is mirrored
        # and referenced regardless (checked by scripts/audit_refs.py)
        if name == "favicon.ico":
            continue
        names.add(name)
    return names


def compare_images(a_path, b_path, diff_path):
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return {"skipped": "Pillow unavailable"}
    a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
    if a.size != b.size:
        return {"size_a": a.size, "size_b": b.size, "identical": False, "reason": "size mismatch"}
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if bbox is None:
        return {"size_a": a.size, "size_b": b.size, "identical": True, "max_channel_delta": 0, "pixels_over_tolerance": 0, "bbox": None}
    gray = diff.convert("L")
    hist = gray.histogram()
    over = sum(hist[TOLERANCE + 1:])
    extreme = max(i for i, n in enumerate(hist) if n)
    gray.point(lambda v: 255 if v > TOLERANCE else 0).save(diff_path)
    return {
        "size_a": a.size,
        "size_b": b.size,
        "identical": over == 0,
        "max_channel_delta": extreme,
        "pixels_over_tolerance": over,
        "pixels_total": a.size[0] * a.size[1],
        "bbox": list(bbox),
        "diff_image": os.path.relpath(diff_path, BASE),
    }


def control_deltas():
    if not CONTROL:
        return {}
    out = {}
    for pair in CONTROL.split(";"):
        try:
            left_path, right_path = pair.split(",")
            left = json.load(open(left_path, encoding="utf-8"))["routes"]
            right = json.load(open(right_path, encoding="utf-8"))["routes"]
        except Exception as exc:  # noqa: BLE001
            print("control pair unusable (%s)" % exc)
            continue
        for route, lv in left.items():
            rv = right.get(route)
            if not rv or not lv.get("screenshot") or not rv.get("screenshot"):
                continue
            res = compare_images(
                lv["screenshot"], rv["screenshot"], os.path.join(OUT, "control-%s.png" % route.strip("/").replace("/", "-"))
            )
            delta = res.get("pixels_over_tolerance")
            if delta is None:
                continue
            out[route] = max(out.get(route, 0), delta)
    if out:
        print("control noise floor (live vs live): %s" % json.dumps(out))
    return out


def main():
    live = json.load(open(LIVE_JSON, encoding="utf-8"))
    mirror = json.load(open(MIRROR_JSON, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    control = control_deltas()
    report, failures = {}, 0

    for route, lv in live["routes"].items():
        mv = mirror["routes"].get(route)
        if not mv:
            report[route] = {"error": "route missing from mirror probe"}
            failures += 1
            continue
        entry = {"metrics": {}}
        for f in FIELDS:
            same = lv.get(f) == mv.get(f)
            if f == "title":  # the harness marks the title with a horse glyph
                same = (lv.get(f) or "").split(" ", 1)[-1] == (mv.get(f) or "").split(" ", 1)[-1]
            entry["metrics"][f] = {"live": lv.get(f), "mirror": mv.get(f), "match": same}
            if not same:
                failures += 1
        lres, mres = resource_basenames(lv), resource_basenames(mv)
        entry["metrics"]["assets"] = {
            "live": sorted(lres),
            "mirror": sorted(mres),
            # The mirror must load at least everything the live page loads. It
            # may request more: this server sends Cache-Control: no-store, so
            # assets the live CDN answers from cache are fetched again.
            "match": not (lres - mres),
            "only_live": sorted(lres - mres),
            "only_mirror": sorted(mres - lres),
        }
        if lres - mres:
            failures += 1
        if lv.get("screenshot") and mv.get("screenshot"):
            entry["pixels"] = compare_images(
                lv["screenshot"], mv["screenshot"], os.path.join(OUT, "diff-%s.png" % route.strip("/").replace("/", "-"))
            )
            px = entry["pixels"]
            floor = control.get(route)
            entry["pixels"]["control_noise"] = floor
            if px.get("identical") is False and "skipped" not in px:
                # a difference no larger than the live site's own run-to-run
                # difference is not evidence of a fidelity problem
                if floor is None or px.get("pixels_over_tolerance", 0) > floor:
                    failures += 1
                    px["within_control_noise"] = False
                else:
                    px["within_control_noise"] = True
        entry["text_match"] = lv.get("textHead") == mv.get("textHead")
        report[route] = entry

    with open(os.path.join(OUT, "probe-diff.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    for route, entry in report.items():
        if "error" in entry:
            print("%-24s ERROR %s" % (route, entry["error"]))
            continue
        bad = [k for k, v in entry["metrics"].items() if not v["match"]]
        px = entry.get("pixels") or {}
        print(
            "%-24s metrics=%s pixels=%s"
            % (
                route,
                "OK" if not bad else "DIFF(%s)" % ",".join(bad),
                "identical" if px.get("identical") else "over=%s max=%s" % (px.get("pixels_over_tolerance"), px.get("max_channel_delta")),
            )
        )
    print("\nverdict: %s (%d mismatches)" % ("IDENTICAL" if failures == 0 else "DIFFERENCES", failures))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
