#!/usr/bin/env python3
"""Serve the offline mirror of zhuxiaobang.com.

  python3 serve.py [--port 8899] [--root mirror] [--log mirror-access.log]

Behaviour:
  * every path under /site and / is answered with mirror/index.html, which is
    what the real site does too (the shell is delivered for every route and the
    client router picks the page);
  * mirrored cdn/vendor files are served byte-for-byte with correct MIME types;
  * collection-style media URLs (trailing slash) resolve to video.mp4;
  * anything else is a real 404, so a missing asset can never hide behind the
    SPA fallback; every request is logged for audit.
"""

import argparse
import json
import os
import posixpath
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

MIME = {
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".mp4": "video/mp4",
    ".pdf": "application/pdf",
    ".txt": "text/plain; charset=utf-8",
}

# --- merchant app (mirror/archive/merchant, copied verbatim) ---------------
#
# The merchant app is served unchanged: its HTML and JS reference their own
# absolute paths (/archive/merchant/assets/...), so it lives under exactly that
# path in the mirror. Its router base is "/", i.e. its pages are root-relative
# routes; they are listed here from the app's own router table (assets/umi.*.js)
# so the server can fall back to its index.html without swallowing 404s.
MERCHANT_ENTRY = "archive/merchant/index.html"
MERCHANT_ROUTE_PREFIXES = (
    "/home",
    "/user",
    "/account",
    "/activity",
    "/assets-management",
    "/bank",
    "/business-operation",
    "/commodity",
    "/dashboard",
    "/imchat",
    "/info-admin",
    "/marketing-promotion",
    "/member",
    "/nopower",
    "/order",
    "/product",
    "/redirectToHome",
    "/redirectToHttp",
    "/team",
)

# API fixtures: the same table the upstream archive publishes as static files
# (scripts/build-pages.mjs), so the app boots without its backend.
MOCK_FIXTURES = {
    "/homed/business/bservice/account/getinfo": "merchant-account.json",
    "/homed/business/bservice/authority/queryRouteList": "merchant-route-list.json",
    "/homed/business/bservice/userType/get": "merchant-route-list.json",
    "/homed/business/bservice/user/get_user_info": "merchant-user-info.json",
    "/homed/business/bservice/opportunity/phoneInit": "merchant-phone-init.json",
    "/homed/business/bservice/config/navibarButtons": "merchant-navibar-buttons.json",
    "/homed/business/bservice/businessOrganization/queryPlatformPackInfo": "merchant-pack-info.json",
    "/homed/business/bservice/businessOrganization/queryPlatformAllInfo": "merchant-pack-info.json",
    "/homed/business/bservice/businessOrganization/queryBySubjectIds": "merchant-empty.json",
    "/homed/api/fe/invoke/getNgccSign": "merchant-empty.json",
    "/passport/aff/web/subject/login_list": "passport-login-list.json",
}

# fallbacks for endpoints the fixture table does not name, ported from the
# upstream archive's sw.js so behaviour matches that deployment
MOCK_EMPTY_LIST = (
    "navibarButtons",
    "queryRouteList",
    "newFunctionsGuide",
    "enumlist",
    "message/recent",
    "queryBySubjectIds",
)

class MirrorHandler(SimpleHTTPRequestHandler):
    server_version = "zxb-mirror/1.0"

    def log_message(self, fmt, *args):
        line = "%s %s" % (self.address_string(), fmt % args)
        with open(self.server.log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def translate_path(self, path):
        return super().translate_path(unquote(urlparse(path).path))

    def do_GET(self):
        self.respond()

    def do_HEAD(self):
        self.respond(body=False)

    def do_POST(self):
        self.respond(body=True)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def mock_api(self, raw):
        """Answer the merchant app's API calls with the archived fixtures."""
        path = raw.rstrip("/") or raw
        fixture = MOCK_FIXTURES.get(path)
        if fixture is None:
            for routed, name in MOCK_FIXTURES.items():
                if path == routed.rstrip("/"):
                    fixture = name
                    break
        if fixture is None and path.startswith("/homed/business/"):
            for token in MOCK_EMPTY_LIST:
                if token in path:
                    return json.dumps({"code": 0, "data": []})
            if "phoneInit" in path or "mobileinfo/get" in path:
                return json.dumps({"code": 0, "data": {"employee_id": "1"}})
            if "getSignStatus" in path:
                return json.dumps({"code": 0, "data": {"signed": True}})
            if "has_im" in path:
                return json.dumps({"code": 0, "data": False})
            return json.dumps({"code": 0, "data": {}})
        if fixture is None and path.startswith(("/homed/api/", "/addone/", "/passport/")):
            return json.dumps({"code": 0, "data": [] if path.startswith("/passport/") else {}})
        if fixture is None:
            return None
        full = os.path.join(self.server.root, "_mock", fixture)
        if not os.path.isfile(full):
            return json.dumps({"code": 0, "data": {}})
        with open(full, encoding="utf-8") as fh:
            return fh.read()

    def send_json(self, payload, body=True):
        data = payload.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(data)

    def respond(self, body=True):
        raw = unquote(urlparse(self.path).path)
        rel = posixpath.normpath(raw).lstrip("/")
        if rel in (".", ""):
            rel = ""
        target = os.path.join(self.server.root, rel)

        if raw.endswith("/") and rel and os.path.isdir(target):
            candidate = os.path.join(target, "video.mp4")
            if os.path.isfile(candidate):
                target = candidate

        if os.path.isfile(target):
            return self.send_file(target, body)

        payload = self.mock_api(raw)
        if payload is not None:
            return self.send_json(payload, body)

        # content links inside the SPA are rewritten to root paths, and the
        # client router prefixes its basename, so /site/faas/... must resolve too
        if raw.startswith("/site/") and rel.startswith("site/"):
            alt = os.path.join(self.server.root, rel[len("site/"):])
            if os.path.isfile(alt):
                return self.send_file(alt, body)

        # the client router owns /site/* (the real site returns the shell for
        # every route); 住好家官网 is a second client-routed app under /zhuhaojia
        if raw in ("/", "/site", "/site/") or raw.startswith("/site/"):
            return self.send_file(os.path.join(self.server.root, "index.html"), body)
        if raw in ("/zhuhaojia", "/zhuhaojia/") or raw.startswith("/zhuhaojia/"):
            return self.send_file(os.path.join(self.server.root, "zhuhaojia", "index.html"), body)

        # merchant app routes (root-relative because its router base is "/")
        if raw.rstrip("/") in ("", "/home") or any(
            raw == p or raw.startswith(p + "/") for p in MERCHANT_ROUTE_PREFIXES
        ):
            return self.send_file(os.path.join(self.server.root, MERCHANT_ENTRY), body)

        self.send_error(404, "Not found: %s" % raw)

    def send_file(self, path, body=True):
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            return self.send_error(404, str(exc))
        ctype = MIME.get(os.path.splitext(path)[1].lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror"))
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    log_path = args.log or os.path.join(os.path.dirname(root), "mirror-access.log")
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), MirrorHandler)
    httpd.root = root
    httpd.log_path = log_path
    print("serving %s at http://127.0.0.1:%d/ (log: %s)" % (root, args.port, log_path))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
