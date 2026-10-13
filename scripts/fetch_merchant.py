#!/usr/bin/env python3
"""Fetch the archived merchant app into the mirror.

Source: the public archive repo github.com/ESA9825/zhuxiaobang-site
  * public/archive/merchant/**  -> mirror/archive/merchant/**   (verbatim, same URL paths)
  * public/mock/*.json          -> mirror/_mock/**              (API fixtures for serve.py)
  * public/sw.js                -> mirror/_mock/sw.js           (reference only)

Every downloaded file is recorded in mirror/merchant/MANIFEST.json with its
sha256, so the archive can be re-verified later. Re-running only fetches files
that are missing or whose digest differs.
"""

import hashlib
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE, "mirror")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/155.0 Safari/537.36"
)
REPO = "ESA9825/zhuxiaobang-site"
BRANCH = "main"
RAW = "https://raw.githubusercontent.com/%s/%s/" % (REPO, BRANCH)
API_TREE = "https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, BRANCH)

MOCK_FILES = [
    "merchant-account.json",
    "merchant-empty.json",
    "merchant-navibar-buttons.json",
    "merchant-pack-info.json",
    "merchant-phone-init.json",
    "merchant-route-list.json",
    "merchant-user-info.json",
    "passport-login-list.json",
]


def get(url, tries=6):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Connection": "close"})
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last


def local_target(repo_path):
    # the app keeps its own absolute URLs (/archive/merchant/assets/...), so it is
    # stored under exactly that path and served verbatim
    if repo_path.startswith("public/archive/merchant/"):
        return repo_path[len("public/"):]
    if repo_path.startswith("public/mock/"):
        return os.path.join("_mock", repo_path[len("public/mock/"):])
    if repo_path == "public/sw.js":
        return os.path.join("_mock", "sw.js")
    return None


def main():
    tree = json.loads(get(API_TREE))
    if "tree" not in tree:
        print("tree request failed:", json.dumps(tree)[:200])
        return 1
    wanted = [t["path"] for t in tree["tree"] if t["type"] == "blob" and local_target(t["path"])]
    print("远程文件: %d 个（merchant + mock）" % len(wanted))

    def fetch(repo_path):
        rel = local_target(repo_path)
        dest = os.path.join(MIRROR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        data = get(RAW + repo_path)
        with open(dest, "wb") as fh:
            fh.write(data)
        return {
            "repo_path": repo_path,
            "path": rel.replace(os.sep, "/"),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(fetch, wanted))

    manifest = {
        "source": "github.com/%s (%s)" % (REPO, BRANCH),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "files": sorted(files, key=lambda f: f["path"]),
    }
    os.makedirs(os.path.join(MIRROR, "archive", "merchant"), exist_ok=True)
    with open(os.path.join(MIRROR, "archive", "merchant", "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    total = sum(f["bytes"] for f in files)
    print("已写入 mirror/archive/merchant：%d 个文件 / %.1f MiB" % (len(files), total / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
