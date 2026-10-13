#!/usr/bin/env python3
"""Download every asset the site needs, and cross-check it against the capture.

Source of truth for the URL set:
  1. the webpack runtime chunk/css maps in index.f433a181.js
  2. asset paths referenced by the captured JS/CSS bodies (truth/bodies/...)

Every HTTP response is written under mirror/ mirroring its original URL path and
recorded in mirror/MANIFEST.json with its sha256. When the same URL was also
retained as a capture body, the two digests must agree; disagreements are
reported, never silently accepted.
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE, "mirror")
BODIES = os.path.join(BASE, "truth", "bodies")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
)

SITE_HOST = "lf-homed-fe.zhuxiaobang.com"
SITE_PREFIX = "/obj/homed-fe-src/cgfe/homed_site/"
SCM_PREFIX = "/obj/homed-fe-src/scm/homed_fe_new_pc/"
SITE = "https://" + SITE_HOST + SITE_PREFIX
WWW_HOST = "www.zhuxiaobang.com"
H5_PREFIX = "/faas/ugc/"

# extra URLs that are not discoverable by scanning the site bundle
EXTRA = [
    "https://lf3-static.bytednsdoc.com/obj/eden-cn/jpahaz_lm_kltvo/ljhwZthlaukjlkulzlp/lib/react.production.17.0.2.min.js",
    "https://lf3-static.bytednsdoc.com/obj/eden-cn/jpahaz_lm_kltvo/ljhwZthlaukjlkulzlp/lib/react-dom.17.0.2.production.min.js",
    "https://lf3-static.bytednsdoc.com/obj/eden-cn/jpahaz_lm_kltvo/ljhwZthlaukjlkulzlp/images/loading.png",
    "https://lf3-static.bytednsdoc.com/obj/eden-cn/fapybjlz_lm_zlp/ljhwZthlaukjlkulzlp/security/secsdk.umd.js",
    "https://lf3-short.ibytedapm.com/slardar/fe/sdk-web/browser.cn.js",
    "https://lf3-short.ibytedapm.com/slardar/fe/sdk-web/plugins/common-monitors.1.16.9.js",
    "https://lf3-short.ibytedapm.com/slardar/fe/sdk-web/plugins/blank-screen.1.16.9.js",
    # signed agreement PDFs linked from page content; mirroring them keeps the
    # documents reachable after the signatures expire
    "https://lf26-addone-sign.bytetos.com/tos-cn-v-736065/fbb3831fae9e43228a82b08a5381622d.pdf"
    "?x-expires=1992342633&x-signature=7NdXBa229e%2BMFaJRHpHfYSgXuLI%3D",
    "https://lf26-addone-sign.bytetos.com/tos-cn-v-736065/o8esxKxFegHI8YZFueff5AwVBIjCgM8AAAnBAe.pdf"
    "?x-expires=2041399531&x-signature=5d23o9J5CGV06U0fo9mwLsSjYEA%3D",
    "https://lf3-addone-sign.bytetos.com/tos-cn-v-736065/57043c21d2b54655b0a419177bb915ed.pdf"
    "?x-expires=1987570572&x-signature=ezjRvkpsZFG4jf8jQbbnWu63JyU%3D",
    # the agreement pages linked from the footer, plus their shared helper
    "https://www.zhuxiaobang.com/faas/ugc/private_protocal_text.html",
    "https://www.zhuxiaobang.com/faas/ugc/user_protocal.html",
    "https://www.zhuxiaobang.com/faas/ugc/third_party_sdk.html",
    "https://www.zhuxiaobang.com/faas/ugc/sensitive_personal_message.html",
    "https://www.zhuxiaobang.com/faas/ugc/account_logout.html",
    "https://www.zhuxiaobang.com/faas/ugc/apply_and_use.html",
    "https://www.zhuxiaobang.com/faas/ugc/config.js",
    # agreement pages linked from the merchant app
    "https://www.zhuxiaobang.com/faas/ugc/merchant_service_protocol.html",
    "https://www.zhuxiaobang.com/faas/ugc/merchant_privacy_protocol.html",
    "https://www.zhuxiaobang.com/faas/ugc/merchant_commitment_letter.html",
    "https://www.zhuxiaobang.com/faas/ugc/ehome_message_protect.html",
    "http://lf3-static.bytednsdoc.com/obj/eden-cn/jpahaz_lm_kltvo/ljhwZthlaukjlkulzlp/images/favicon.ico",
    # 住好家官网: a second, self-contained CRA app served under /zhuhaojia
    "https://www.zhuxiaobang.com/zhuhaojia",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "manifest.json",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "favicon.ico",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/css/main.9eb295c4.css",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/js/main.f9a99cdd.js",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/phone1.8d70e8dc33aa1fabd1c6.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/phone2.6c29131f3f9b7e2e9130.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/phone3.44f396e298030a8d3a7e.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/phone4.ef123a36a892a2c70fe8.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/realTimeDuration.8ab23228537d3d9ac0b4.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/title.6f820101685aa874e515.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/banner1.9e5294396ec08d09a336.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/banner2.7f5b59a34e95364355d5.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/banner3.cf129455918b81499f56.png",
    "https://lf-homed-fe.zhuxiaobang.com" + SCM_PREFIX + "static/media/logoFooter.f9b9750ad9cb267e54c4.png",
]


def local_path(url):
    """Local path for one original URL.

    Site CDN assets keep their tree under cdn/ (main site) or zhuhaojia/
    (住好家官网); content pages on the site's own domain keep the site's URL
    path; everything else lands under vendor/<host>/<path>.
    """
    pr = urlparse(url)
    if pr.netloc == SITE_HOST:
        if pr.path.startswith(SITE_PREFIX):
            return os.path.join("cdn", pr.path[len(SITE_PREFIX):])
        if pr.path.startswith(SCM_PREFIX):
            return os.path.join("zhuhaojia", pr.path[len(SCM_PREFIX):])
    if pr.netloc == WWW_HOST:
        if pr.path == "/zhuhaojia" or pr.path.startswith("/zhuhaojia/"):
            return os.path.join("zhuhaojia", "index.html")
        if pr.path.startswith(H5_PREFIX):
            return pr.path.lstrip("/")
    rel = os.path.join("vendor", pr.netloc, pr.path.lstrip("/"))
    if rel.endswith(os.sep):  # media URLs address a collection, not a file
        rel = rel + "video.mp4"
    return rel


def discover_urls():
    """Union of chunk/css maps and every asset path referenced in the bundle."""
    urls = set(EXTRA)
    site = SITE
    runtime = os.path.join(BODIES, SITE_HOST, SITE_PREFIX.strip("/"), "index.f433a181.js")
    with open(runtime, encoding="utf-8") as fh:
        src = fh.read()

    # literal filenames plus names rebuilt from the webpack maps, which are
    # emitted as "chunk/"+e+"."+{70:"ca6329e4",...}[e]+".js"
    for name in re.findall(r'"([A-Za-z0-9_./-]+\.(?:js|css))"', src):
        urls.add(site + name)
    for marker, tmpl in (('"chunk/"+e+"."', "chunk/%d.%s.js"), ('"async/"+e+"."', "async/%d.%s.css")):
        at = src.find(marker)
        if at < 0:
            continue
        block = re.search(r"\{(\d+:\"[0-9a-f]{8}\"(?:,\d+:\"[0-9a-f]{8}\")*)\}", src[at:at + 800])
        for cid, h in re.findall(r"(\d+):\"([0-9a-f]{8})\"", block.group(1)) if block else []:
            urls.add(site + tmpl % (int(cid), h))

    # anything the live site actually requested is required by definition
    live = os.path.join(BASE, "truth", "live-urls.txt")
    if os.path.exists(live):
        for line in open(live, encoding="utf-8"):
            u = line.strip()
            if u.startswith(site):
                urls.add(u)

    # the delivered shell references assets the JS/CSS never mention (favicon)
    shell = os.path.join(BODIES, "www.zhuxiaobang.com", "site", "home")
    if os.path.exists(shell):
        text = open(shell, encoding="utf-8", errors="replace").read()
        for m in re.findall(r"(?:https?:)?//" + re.escape(SITE_HOST) + re.escape(SITE_PREFIX) + r"([A-Za-z0-9_./@-]+)", text):
            urls.add(site + m.lstrip("/"))
    # named entry chunks referenced literally in the shell
    for name in ("chunk/48.0c173d84.js", "index.f433a181.js", "48.4d555b07.css", "index.b12a9bb2.css"):
        urls.add(site + name)

    for dirpath, _, files in os.walk(BODIES):
        for f in files:
            if not f.endswith((".js", ".css")):
                continue
            s = open(os.path.join(dirpath, f), encoding="utf-8", errors="replace").read()
            for m in re.findall(r"//lf-homed-fe\.zhuxiaobang\.com" + re.escape(SITE_PREFIX) + r"([A-Za-z0-9_./@-]+)", s):
                urls.add(site + m.lstrip("/"))
            for m in re.findall(
                r"[\"'(]((?:image|font|media|public)/[A-Za-z0-9_.@-]+\.(?:png|jpe?g|gif|svg|webp|woff2?|ttf|otf|mp4|json|ico))",
                s,
            ):
                urls.add(site + m)
            for m in re.findall(r"//(v9-default\.365yg\.com/[A-Za-z0-9_./-]+)", s):
                urls.add("https://" + m)
    return sorted(urls)


def digest(b):
    return hashlib.sha256(b).hexdigest()


def captured_digests():
    """sha256 for URLs we already hold as capture bodies, keyed by <host>/<path>."""
    out = {}
    for dirpath, _, files in os.walk(BODIES):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, BODIES).replace(os.sep, "/")
            if "__" in rel:  # query-bearing capture path, no matching download URL
                continue
            with open(full, "rb") as fh:
                out[rel] = digest(fh.read())
    return out


def main():
    urls = discover_urls()
    wire = set()
    live = os.path.join(BASE, "truth", "live-urls.txt")
    if os.path.exists(live):
        wire = {u.strip() for u in open(live, encoding="utf-8") if u.strip()}
    known = captured_digests()
    manifest = []
    mismatch, failed, absent = [], [], []
    print("downloading %d assets" % len(urls))

    for i, url in enumerate(urls, 1):
        rel = local_path(url)
        dest = os.path.join(MIRROR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        data = status = None
        try:
            for attempt in range(3):  # transient DNS/CDN hiccups are not results
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        data = resp.read()
                        status = resp.status
                    break
                except urllib.error.HTTPError:
                    raise
                except Exception as transient:  # noqa: BLE001
                    if attempt == 2:
                        raise
                    print("  retry %s (%s)" % (url, transient))
                    time.sleep(1.5)
            if data is None:
                raise RuntimeError("no response")
        except urllib.error.HTTPError as exc:
            # a map entry the live site never requested may simply no longer be
            # published upstream; that is an observation, not a mirror defect
            if exc.code == 404 and url not in wire:
                absent.append({"url": url, "error": "HTTP 404", "note": "not requested by the live site"})
                print("  absent-upstream %s" % url)
                continue
            failed.append({"url": url, "error": "HTTP %s" % exc.code})
            print("  FAIL %s %s" % (exc.code, url))
            continue
        except Exception as exc:  # noqa: BLE001
            failed.append({"url": url, "error": str(exc)})
            print("  FAIL %s (%s)" % (url, exc))
            continue

        with open(dest, "wb") as fh:
            fh.write(data)
        d = digest(data)

        pr = urlparse(url)
        capture_rel = (pr.netloc + "/" + pr.path.lstrip("/")) if pr.netloc != SITE_HOST else (
            SITE_HOST + SITE_PREFIX + rel[len("cdn/"):].replace(os.sep, "/")
        )
        note = None
        if capture_rel in known:
            if known[capture_rel] != d:
                mismatch.append({"url": url, "downloaded": d, "captured": known[capture_rel]})
                note = "MISMATCH"
            else:
                note = "verified"
                known.pop(capture_rel)

        manifest.append(
            {"url": url, "path": rel.replace(os.sep, "/"), "bytes": len(data), "sha256": d, "status": status, "cross_check": note}
        )
        print("  [%2d/%2d] %7d B %s %s" % (i, len(urls), len(data), note or "-", rel))
        time.sleep(0.05)

    with open(os.path.join(MIRROR, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "generated_from": "scripts/fetch_assets.py",
                "assets": manifest,
                "failures": failed,
                "absent_upstream": absent,
                "digest_mismatches": mismatch,
                "captured_bodies_not_downloaded": sorted(known.keys()),
            },
            fh,
            ensure_ascii=False,
            indent=1,
        )
    print(
        "\nfiles=%d failures=%d absent-upstream=%d mismatches=%d capture-only=%d"
        % (len(manifest), len(failed), len(absent), len(mismatch), len(known))
    )

    # coverage gate: every site URL seen on the wire must exist in the mirror
    live = os.path.join(BASE, "truth", "live-urls.txt")
    if os.path.exists(live):
        missing = [
            u.strip()
            for u in open(live, encoding="utf-8")
            if u.strip().startswith(SITE) and not os.path.exists(os.path.join(MIRROR, local_path(u.strip())))
        ]
        if missing:
            print("MISSING from mirror: %d" % len(missing))
            for u in missing:
                print("  ", u)
            return 1
        print("coverage ok: every wire URL under %s%s is present locally" % (SITE_HOST, SITE_PREFIX))
    return 0 if not failed and not mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
