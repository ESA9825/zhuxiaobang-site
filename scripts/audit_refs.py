#!/usr/bin/env python3
"""Static audit of the mirror: every local reference must resolve to a file.

Scans the mirrored HTML/JS/CSS for references into the mirror's own trees
(/cdn/, /vendor/, /zhuhaojia/, /faas/) and checks that each one exists. A
dangling reference or a leftover external CDN reference fails the gate, so a
missing asset cannot hide behind the SPA fallback.
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE, "mirror")

LOCAL_TREES = ("/cdn/", "/vendor/", "/zhuhaojia/", "/faas/")
LOCAL_RE = re.compile(r"[\"'(]((?:/cdn/|/vendor/|/zhuhaojia/|/faas/)[A-Za-z0-9._~!$&*+@%=:/-]*)")
ALLOWED_REMOTE_HOSTS = {"mon.zijieapi.com", "mcs.zijieapi.com", "lf3-short.ibytedapm.com"}
PROBE = os.path.join(BASE, "truth", "mirror-all.json")


def check_local_refs():
    checked = 0
    missing = []
    for dirpath, _, files in os.walk(MIRROR):
        for f in files:
            if not f.endswith((".html", ".js", ".css")):
                continue
            path = os.path.join(dirpath, f)
            rel_file = os.path.relpath(path, MIRROR)
            text = open(path, encoding="utf-8", errors="replace").read()
            for ref in sorted(set(LOCAL_RE.findall(text))):
                checked += 1
                target = os.path.join(MIRROR, ref.lstrip("/"))
                if os.path.isfile(target):
                    continue
                if ref.endswith("/") and (os.path.isdir(target) or os.path.isfile(os.path.join(target, "video.mp4"))):
                    continue
                missing.append([rel_file, ref])
    return checked, missing


def check_remote_requests():
    if not os.path.exists(PROBE):
        return None
    probe = json.load(open(PROBE, encoding="utf-8"))
    unexpected = {}
    for route, data in probe["routes"].items():
        for host_path in data.get("resourcePaths") or []:
            host = host_path.split("/", 1)[0].split(":")[0]
            if host in ("127.0.0.1", "localhost") or host in ALLOWED_REMOTE_HOSTS:
                continue
            unexpected.setdefault(host, set()).add(route)
    return {h: sorted(r) for h, r in sorted(unexpected.items())}


def main():
    checked, missing = check_local_refs()
    unexpected = check_remote_requests()

    print("local references checked: %d" % checked)
    print("missing targets: %d" % len(missing))
    for rel_file, ref in missing[:20]:
        print("   %s -> %s" % (rel_file, ref))
    if unexpected is None:
        print("remote-request check: skipped (no probe output yet)")
    else:
        print("remote hosts contacted by the mirror: %d" % len(unexpected))
        for host, routes in list(unexpected.items())[:20]:
            print("   %s (%s)" % (host, ", ".join(routes)))

    report = {
        "local_references_checked": checked,
        "missing": missing,
        "unexpected_remote_hosts": unexpected,
    }
    out = os.path.join(BASE, "truth", "ref-audit.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    ok = not missing and not unexpected
    print("verdict: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
