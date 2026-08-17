#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy the zhuxiaobang static archive under a namespaced Aliyun OSS prefix."""

import base64
import hashlib
import hmac
import mimetypes
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "public" / "archive"
BUCKET_NAME = "mofun-vip"
REGION = "oss-cn-chengdu"
PREFIX = "zhuxiaobang-clone"
ENDPOINT = f"https://{BUCKET_NAME}.{REGION}.aliyuncs.com"

MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".xml": "text/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".json": "application/json",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".eot": "application/vnd.ms-fontobject",
    ".otf": "font/otf",
    ".mp4": "video/mp4",
}


def sign(verb, headers, path, access_key_id, access_key_secret):
    md5 = headers.get("Content-MD5", "")
    content_type = headers.get("Content-Type", "")
    date = headers.get("Date", "")
    canonical_oss_headers = ""
    for key in sorted(headers):
        if key.lower().startswith("x-oss-"):
            canonical_oss_headers += key.lower() + ":" + headers[key].strip() + "\n"
    resource = "/" + BUCKET_NAME + path
    string_to_sign = (
        verb
        + "\n"
        + md5
        + "\n"
        + content_type
        + "\n"
        + date
        + "\n"
        + canonical_oss_headers
        + resource
    )
    signature = base64.b64encode(
        hmac.new(
            access_key_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha1,
        ).digest()
    ).decode()
    return "OSS " + access_key_id + ":" + signature


def content_type_for(name):
    guessed, _ = mimetypes.guess_type(name)
    if guessed:
        return guessed
    return MIME_MAP.get(Path(name).suffix.lower(), "application/octet-stream")


def upload_file(object_key, data, content_type, access_key_id, access_key_secret):
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    md5 = base64.b64encode(hashlib.md5(data).digest()).decode()
    headers = {
        "Date": date,
        "Content-MD5": md5,
        "Content-Type": content_type,
        "Content-Disposition": "inline",
        "x-oss-acl": "public-read",
    }
    headers["Authorization"] = sign(
        "PUT", headers, "/" + object_key, access_key_id, access_key_secret
    )
    url = ENDPOINT + "/" + object_key
    request = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def patch_archive_links(text):
    replacements = {
        '<base href="/archive/merchant/">': f'<base href="/{PREFIX}/archive/merchant/">',
        'href="/"': f'href="/{PREFIX}/"',
        'href="/site/home"': f'href="/{PREFIX}/site/home"',
        'href="/site/about"': f'href="/{PREFIX}/site/about"',
        'href="/site/decorateTips"': f'href="/{PREFIX}/site/decorateTips"',
        'href="/site/institute"': f'href="/{PREFIX}/site/institute"',
        'href="/merchant"': f'href="/{PREFIX}/merchant/index.html"',
        'href="/faas/ugc/private_protocal_text.html"': (
            f'href="/{PREFIX}/faas/ugc/private_protocal_text.html"'
        ),
        'href="/faas/ugc/user_protocal.html"': (
            f'href="/{PREFIX}/faas/ugc/user_protocal.html"'
        ),
        'href="/zhuhaojia"': f'href="/{PREFIX}/zhuhaojia"',
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def redirect_html(target):
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN"><head><meta charset="utf-8">\n'
        f'<meta http-equiv="refresh" content="0;url=/{PREFIX}{target}">\n'
        f"<title>Redirecting</title></head><body></body></html>\n"
    ).encode("utf-8")


def build_deploy_tree(destination: Path):
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    archive_dest = destination / "archive"
    shutil.copytree(SOURCE_DIR, archive_dest)

    for html_path in archive_dest.rglob("index.html"):
        text = html_path.read_text(encoding="utf-8")
        html_path.write_text(patch_archive_links(text), encoding="utf-8")

    redirects = {
        "index.html": "/archive/home/index.html",
        "site/home/index.html": "/archive/home/index.html",
        "site/about/index.html": "/archive/about/index.html",
        "site/decorateTips/index.html": "/archive/decorate-tips/index.html",
        "site/institute/index.html": "/archive/institute/index.html",
        "merchant/index.html": "/archive/merchant/index.html",
        "faas/ugc/private_protocal_text.html": "/archive/privacy/index.html",
        "faas/ugc/user_protocal.html": "/archive/terms/index.html",
        "zhuhaojia/index.html": "/archive/zhuhaojia/index.html",
    }
    for relative, target in redirects.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(redirect_html(target))

    return destination


def collect_files(root: Path):
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        files.append((path, relative))
    return sorted(files, key=lambda item: item[1])


def main():
    dry_run = "--dry-run" in sys.argv
    access_key_id = os.environ.get("ALIYUN_ACCESS_KEY_ID")
    access_key_secret = os.environ.get("ALIYUN_ACCESS_KEY_SECRET")
    if not dry_run and (not access_key_id or not access_key_secret):
        print("Missing ALIYUN_ACCESS_KEY_ID or ALIYUN_ACCESS_KEY_SECRET")
        return 2

    with tempfile.TemporaryDirectory(prefix="zhuxiaobang-oss-") as tmp:
        deploy_root = Path(tmp)
        build_deploy_tree(deploy_root)
        files = collect_files(deploy_root)
        print(f"Prepared {len(files)} files for OSS prefix /{PREFIX}/")
        if dry_run:
            for _, relative in files:
                print("  ", relative)
            return 0

        ok = 0
        failed = 0
        for path, relative in files:
            data = path.read_bytes()
            object_key = f"{PREFIX}/{relative}"
            status = upload_file(
                object_key,
                data,
                content_type_for(relative),
                access_key_id,
                access_key_secret,
            )
            if status in (200, 201, 204):
                ok += 1
                print(f"  OK {object_key} ({len(data)} bytes)")
            else:
                failed += 1
                print(f"  FAIL {object_key} HTTP {status}")

        print(f"\nDone: {ok} uploaded, {failed} failed")
        print(
            f"Site URL: http://{BUCKET_NAME}.{REGION}.aliyuncs.com/{PREFIX}/"
        )
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
