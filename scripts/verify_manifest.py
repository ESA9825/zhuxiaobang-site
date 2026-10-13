#!/usr/bin/env python3
"""Check every mirrored file against its recorded sha256.

Two trees are covered:

  * the main site, where two digests are legitimate - the bytes as downloaded
    (mirror/MANIFEST.json) and the bytes after the URL rewrite
    (mirror/REWRITES.json) for the files that rewrite touched;
  * the merchant app, which is stored verbatim, so every file must match
    mirror/archive/merchant/MANIFEST.json exactly.

Anything matching neither is corrupted or undocumented. Run this after unpacking
an archive to prove the copy is intact.
"""

import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE, "mirror")


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verify_site():
    manifest = json.load(open(os.path.join(MIRROR, "MANIFEST.json"), encoding="utf-8"))
    rewrites = json.load(open(os.path.join(MIRROR, "REWRITES.json"), encoding="utf-8"))
    after = {f["file"]: f.get("sha256_after") for f in rewrites["files_rewritten"]}

    ok = rewritten = 0
    problems = []
    for asset in manifest["assets"]:
        path = os.path.join(MIRROR, asset["path"])
        if not os.path.isfile(path):
            problems.append("missing: %s" % asset["path"])
            continue
        actual = digest(path)
        if actual == asset["sha256"]:
            ok += 1
        elif after.get(asset["path"]) == actual:
            rewritten += 1
        else:
            problems.append(
                "digest mismatch: %s (manifest %s, rewrites %s, actual %s)"
                % (asset["path"], asset["sha256"][:12], (after.get(asset["path"]) or "-")[:12], actual[:12])
            )

    for name, expected in after.items():
        if any(a["path"] == name for a in manifest["assets"]):
            continue
        path = os.path.join(MIRROR, name)
        if not os.path.isfile(path):
            problems.append("missing rewritten file: %s" % name)
        elif digest(path) != expected:
            problems.append("digest mismatch: %s (rewrites %s)" % (name, (expected or "-")[:12]))
        else:
            rewritten += 1

    entries = len(manifest["assets"]) + len(after)
    summary = "main site: %d as-downloaded, %d as-rewritten (%d entries)" % (ok, rewritten, entries)
    return summary, problems


def verify_verbatim(subdir, patched=None):
    """A tree copied as-is: every file must match its manifest digest.

    `patched` maps mirror-relative paths to the digest recorded after a
    documented local patch (REWRITES.json), which is acceptable too.
    """
    patched = patched or {}
    root = os.path.join(MIRROR, subdir)
    manifest_path = os.path.join(root, "MANIFEST.json")
    if not os.path.isfile(manifest_path):
        return "", []
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    ok = patched_ok = 0
    problems = []
    for entry in manifest["files"]:
        # paths are recorded relative to the mirror root
        rel = entry["path"]
        if rel.startswith(subdir + "/"):
            rel = rel[len(subdir) + 1:]
            path = os.path.join(root, rel)
        else:
            path = os.path.join(MIRROR, rel)
        if not os.path.isfile(path):
            problems.append("[%s] missing: %s" % (subdir, entry["path"]))
            continue
        actual = digest(path)
        if actual == entry["sha256"]:
            ok += 1
        elif patched.get(entry["path"]) == actual:
            patched_ok += 1
        else:
            problems.append("[%s] digest mismatch: %s" % (subdir, entry["path"]))
    summary = "%s: %d verbatim + %d documented local patch (%d files total)" % (
        subdir, ok, patched_ok, len(manifest["files"]))
    return summary, problems


def main():
    summaries = []
    problems = []
    rewrites = json.load(open(os.path.join(MIRROR, "REWRITES.json"), encoding="utf-8"))
    patched = {f["file"]: f.get("sha256_after") for f in rewrites["files_rewritten"]}
    for verifier in (verify_site, lambda: verify_verbatim("archive/merchant", patched)):
        summary, found = verifier()
        if summary:
            summaries.append(summary)
        problems.extend(found)

    print("manifest check")
    for line in summaries:
        print("   %s" % line)
    print("   problems: %d" % len(problems))
    for p in problems[:20]:
        print("      %s" % p)
    print("verdict: %s" % ("PASS" if not problems else "FAIL"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
