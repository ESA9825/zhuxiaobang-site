#!/usr/bin/env python3
"""Build the GitHub Pages deployment from the mirror.

GitHub Pages serves a project site under /<repo>/, while the mirror is written
for the root of an origin (absolute URLs like /cdn/..., /site/..., /archive/...).
This script turns the mirror into a self-contained static tree:

  1. copy mirror/ -> out/
  2. prefix every root-absolute URL with /<repo> (HTML/JS/CSS/JSON/SVG)
  3. move router bases under the same prefix (the SPA basename and the merchant
     app's window.routerBase), which the mirror keeps root-relative locally
  4. materialise client-side routes as real files, because a static host has no
     SPA fallback (the main site's four routes, the merchant app's ~70 routes)
  5. write the merchant API fixtures to the paths the app requests, and install
     the upstream service worker as a catch-all for the remaining endpoints

Usage: python3 scripts/build_pages.py [--base /zhuxiaobang-site] [--out out]
"""

import argparse
import json
import os
import re
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE_DIR, "mirror")
TEXT_EXT = (".html", ".js", ".css", ".json", ".svg", ".txt", ".xml")

# Root tokens that mark a page/asset URL as absolute in this mirror. API paths
# (homed, passport, addone) are deliberately absent: they are data endpoints, the
# merchant page's own mock shims match them by substring, and the service worker
# answers them by path - prefixing them breaks both.
ROOT_TOKENS = (
    "cdn|vendor|archive|site|zhuhaojia|faas|home|user|account|activity|"
    "assets-management|bank|business-operation|commodity|dashboard|imchat|"
    "info-admin|marketing-promotion|member|nopower|order|product|team|"
    "redirectToHome|redirectToHttp|mock"
)

# main-site SPA routes (basename /site) plus the shell for "/"
SPA_ROUTES = ("", "site", "site/home", "site/about", "site/institute", "site/decorateTips")

# merchant fixtures, same table the upstream archive publishes
MOCK_FIXTURES = {
    "homed/business/bservice/account/getinfo": "merchant-account.json",
    "homed/business/bservice/authority/queryRouteList": "merchant-route-list.json",
    "homed/business/bservice/userType/get": "merchant-route-list.json",
    "homed/business/bservice/user/get_user_info": "merchant-user-info.json",
    "homed/business/bservice/opportunity/phoneInit": "merchant-phone-init.json",
    "homed/business/bservice/config/navibarButtons": "merchant-navibar-buttons.json",
    "homed/business/bservice/businessOrganization/queryPlatformPackInfo": "merchant-pack-info.json",
    "homed/business/bservice/businessOrganization/queryPlatformAllInfo": "merchant-pack-info.json",
    "homed/business/bservice/businessOrganization/queryBySubjectIds": "merchant-empty.json",
    "homed/api/fe/invoke/getNgccSign": "merchant-empty.json",
    "passport/aff/web/subject/login_list": "passport-login-list.json",
}


def prefix_urls(out_dir, base):
    """Make root-absolute URLs absolute under the Pages base path."""
    tokens = tuple(t for t in ROOT_TOKENS.split("|") if t)
    pattern = re.compile(r'(["\'(])(/[A-Za-z][A-Za-z0-9_./-]*)')
    entity = re.compile(r'(&quot;|&#39;)(/[A-Za-z][A-Za-z0-9_./-]*)')

    def bump(match):
        quote, path = match.group(1), match.group(2)
        seg = path[1:].split("/", 1)[0]
        if seg in tokens and not path.startswith(base + "/"):
            return quote + base + path
        return match.group(0)

    changed = 0
    for dirpath, _, files in os.walk(out_dir):
        for name in files:
            if not name.endswith(TEXT_EXT):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8", errors="surrogateescape") as fh:
                original = fh.read()
            text = pattern.sub(bump, original)
            text = entity.sub(bump, text)
            if text != original:
                with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
                    fh.write(text)
                changed += 1
    return changed


def unprefix_route_paths(out_dir, base):
    """Route tables must stay root-relative; only the router base carries the prefix.

    The upstream archive's own build does the same (path:"/<base>/ -> path:"/).
    """
    variants = [('path:"%s/' % base, 'path:"/'), ("path:'%s/" % base, "path:'/"),
                ('redirect:"%s/' % base, 'redirect:"/'), ("redirect:'%s/" % base, "redirect:'/"),
                ('"path":"%s/' % base, '"path":"/'), ('"redirect":"%s/' % base, '"redirect":"/')]
    files = 0
    hits = 0
    for dirpath, _, names in os.walk(out_dir):
        for name in names:
            if not name.endswith(".js"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8", errors="surrogateescape") as fh:
                text = fh.read()
            n = sum(text.count(old) for old, _ in variants)
            if not n:
                continue
            for old, new in variants:
                text = text.replace(old, new)
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
                fh.write(text)
            files += 1
            hits += n
    return files, hits


def rewrite_file(path, replacements):
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        text = fh.read()
    for old, new in replacements:
        text = text.replace(old, new)
    with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write(text)


def copy_shell(out_dir, base, router_base=None, register_sw=False):
    """Write index.html copies for client-side routes."""
    main_shell = os.path.join(out_dir, "index.html")
    merchant_shell = os.path.join(out_dir, "archive", "merchant", "index.html")
    written = 0

    if os.path.isfile(merchant_shell) and register_sw:
        text = open(merchant_shell, encoding="utf-8", errors="surrogateescape").read()
        registration = (
            '<script>if("serviceWorker" in navigator){'
            'navigator.serviceWorker.register("%s/sw.js",{scope:"%s/"});}</script>' % (router_base.rstrip("/"), router_base.rstrip("/"))
        )
        if "serviceWorker.register" not in text:
            text = text.replace("</body>", registration + "</body>", 1)
        with open(merchant_shell, "w", encoding="utf-8", errors="surrogateescape") as fh:
            fh.write(text)

    for route in SPA_ROUTES:
        target_dir = os.path.join(out_dir, route) if route else out_dir
        target = os.path.join(target_dir, "index.html") if route else main_shell
        if route and not os.path.isfile(target):
            os.makedirs(target_dir, exist_ok=True)
            shutil.copyfile(main_shell, target)
            written += 1

    # merchant routes (its router base is the Pages base path)
    routes = merchant_routes(out_dir)
    base_slug = base.strip("/")
    for route in routes:
        rel = route.strip("/")
        # the route table is read after prefixing, so strip the base again
        if rel == base_slug:
            continue
        if rel.startswith(base_slug + "/"):
            rel = rel[len(base_slug) + 1:]
        if not rel:
            continue
        target_dir = os.path.join(out_dir, rel)
        target = os.path.join(target_dir, "index.html")
        if not os.path.isfile(target):
            os.makedirs(target_dir, exist_ok=True)
            shutil.copyfile(merchant_shell, target)
            written += 1
    return written, len(routes)


def merchant_routes(out_dir):
    """Read the merchant app's route table out of its umi bundle."""
    assets = os.path.join(out_dir, "archive", "merchant", "assets")
    if not os.path.isdir(assets):
        return []
    for name in sorted(os.listdir(assets)):
        if name.startswith("umi") and name.endswith(".js"):
            text = open(os.path.join(assets, name), encoding="utf-8", errors="replace").read()
            found = set(re.findall(r'path:"(/[A-Za-z0-9_/:.-]*)"', text))
            return sorted(p for p in found if not p.startswith("/opt/"))
    return []


def write_mocks(out_dir, mirror_dir):
    """Static fixtures at the paths the merchant app requests."""
    written = 0
    mock_src = os.path.join(mirror_dir, "_mock")
    for route, fixture in MOCK_FIXTURES.items():
        src = os.path.join(mock_src, fixture)
        if not os.path.isfile(src):
            continue
        dest = os.path.join(out_dir, route, "index.html")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)
        written += 1
    sw = os.path.join(mock_src, "sw.js")
    if os.path.isfile(sw):
        shutil.copyfile(sw, os.path.join(out_dir, "sw.js"))
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("ZXB_PAGES_BASE", "/zhuxiaobang-site"))
    ap.add_argument("--out", default=os.path.join(BASE_DIR, "out"))
    args = ap.parse_args()
    base = "/" + args.base.strip("/")
    out_dir = os.path.abspath(args.out)

    if not os.path.isdir(MIRROR):
        print("mirror not found: %s" % MIRROR)
        return 1
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(MIRROR, out_dir, symlinks=False)

    # drop the mirror's own bookkeeping so the published tree stays clean
    for name in ("MANIFEST.json", "REWRITES.json"):
        path = os.path.join(out_dir, name)
        if os.path.isfile(path):
            os.remove(path)
    merchant_manifest = os.path.join(out_dir, "archive", "merchant", "MANIFEST.json")
    if os.path.isfile(merchant_manifest):
        os.remove(merchant_manifest)

    rewritten = prefix_urls(out_dir, base)
    route_files, route_hits = unprefix_route_paths(out_dir, base)

    # router bases move under the Pages prefix
    for dirpath, _, files in os.walk(os.path.join(out_dir, "cdn")):
        for name in files:
            if name.endswith(".js"):
                path = os.path.join(dirpath, name)
                rewrite_file(path, [('basename:"/site"', 'basename:"%s/site"' % base)])
    rewrite_file(
        os.path.join(out_dir, "archive", "merchant", "index.html"),
        [('window.routerBase = "/"', 'window.routerBase = "%s/"' % base)],
    )

    shell_count, route_count = copy_shell(out_dir, base, router_base=base, register_sw=True)
    mocks = write_mocks(out_dir, MIRROR)
    open(os.path.join(out_dir, ".nojekyll"), "w").close()

    total = sum(len(files) for _, _, files in os.walk(out_dir))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out_dir) for f in fs)
    print("built %s" % out_dir)
    print("   base path      : %s/" % base)
    print("   files prefixed : %d" % rewritten)
    print("   routes restored: %d in %d files" % (route_hits, route_files))
    print("   shell copies   : %d (of %d merchant routes)" % (shell_count, route_count))
    print("   api fixtures   : %d + sw.js" % mocks)
    print("   total          : %d files / %.1f MiB" % (total, size / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
