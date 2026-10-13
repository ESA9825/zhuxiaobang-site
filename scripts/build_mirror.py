#!/usr/bin/env python3
"""Rewrite the mirrored bundle so it runs offline from a local HTTP server.

Reads mirror/MANIFEST.json (original URL -> local file) and the captured page
shell, then rewrites every reference to a mirrored URL into its local path:

  //lf-homed-fe.zhuxiaobang.com/obj/.../homed_site/<x>  ->  /cdn/<x>
  //<vendor-host>/<path>                                ->  /vendor/<host>/<path>

Only URL text changes. Each rewritten file is verified by substituting the local
paths back and requiring a byte-identical match with the original, so an
accidental edit cannot hide in the diff.

An optional local patch (ZXB_HIDE_SHUTDOWN_NOTICE=1, the default) hides the
"住小帮关停公告" overlay by appending one CSS rule to the shell. The bundle itself
stays byte-identical; set the variable to 0 for a fully faithful copy. Every
patch applied is recorded in mirror/REWRITES.json.
"""

import hashlib
import json
import os
import re
import sys
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE, "mirror")
SHELL = os.path.join(BASE, "truth", "bodies", "www.zhuxiaobang.com", "site", "home")

URL_RE = re.compile(r"(?:https?:)?//[A-Za-z0-9._-]+(?:/[A-Za-z0-9._~!$&'()*+,;=:@%/\-]*)?")
# only web assets are rewritten; JSON manifests keep their original URLs so the
# audit trail and the rewrite rules stay reproducible
EXT = (".js", ".css", ".html", ".svg")


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rules_from_manifest():
    man = json.load(open(os.path.join(MIRROR, "MANIFEST.json"), encoding="utf-8"))
    rules = {}
    for a in man["assets"]:
        if not a["url"].startswith(("http://", "https://")):
            raise SystemExit(
                "MANIFEST.json no longer holds original URLs (%r); re-run scripts/fetch_assets.py" % a["url"]
            )
        pr = urlparse(a["url"])
        key = pr.netloc + pr.path
        rel = a["path"]
        if rel.endswith("/video.mp4"):  # collection-style media URL
            value = "/" + rel[: -len("video.mp4")]
        elif rel.endswith("index.html"):  # directory-style entry point
            value = "/" + rel[: -len("index.html")].rstrip("/")
        else:
            value = "/" + rel
        if value in rules.values() and rules.get(key) != value:
            raise SystemExit("rewrite collision: %s and another rule share target %s" % (key, value))
        rules[key] = value
    # the CDN root itself is the webpack public path
    rules["lf-homed-fe.zhuxiaobang.com/obj/homed-fe-src/cgfe/homed_site/"] = "/cdn/"
    rules["lf-homed-fe.zhuxiaobang.com/obj/homed-fe-src/scm/homed_fe_new_pc/"] = "/zhuhaojia/"
    return rules


def rewrite(text, rules, keys):
    counts = {}

    def repl(m):
        raw = m.group(0)
        core = raw[raw.index("//") + 2:]
        for key in keys:
            if core.startswith(key):
                counts[key] = counts.get(key, 0) + 1
                return rules[key] + core[len(key):]
        return raw

    return URL_RE.sub(repl, text), counts


def main():
    rules = rules_from_manifest()
    keys = sorted(rules, key=len, reverse=True)
    changed, total = [], 0

    targets = []
    for sub in ("cdn", "vendor", "zhuhaojia", "faas"):
        for dirpath, _, files in os.walk(os.path.join(MIRROR, sub)):
            for f in files:
                if f.endswith(EXT):
                    targets.append(os.path.join(dirpath, f))

    for path in targets:
        with open(path, encoding="utf-8", errors="surrogateescape") as fh:
            original = fh.read()
        rewritten, counts = rewrite(original, rules, keys)
        if rewritten == original:
            continue
        # prove the rewrite is reversible: no other byte may differ
        restored, _ = rewrite_restore(rewritten, rules)
        if normalize_scheme(restored) != normalize_scheme(original):
            print("REFUSING %s: rewrite is not reversible" % os.path.relpath(path, MIRROR))
            return 1
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
            fh.write(rewritten)
        n = sum(counts.values())
        total += n
        changed.append(
            {
                "file": os.path.relpath(path, MIRROR),
                "rewrites": n,
                # the manifest records the digest of the bytes as downloaded;
                # this is the digest after the URL rewrite
                "sha256_after": digest(path),
            }
        )

    # the SPA shell: one file serves every route
    with open(SHELL, encoding="utf-8", errors="surrogateescape") as fh:
        shell = fh.read()
    shell_out, shell_counts = rewrite(shell, rules, keys)
    restored, _ = rewrite_restore(shell_out, rules)
    if normalize_scheme(restored) != normalize_scheme(shell):
        print("REFUSING shell: rewrite is not reversible")
        return 1
    with open(os.path.join(MIRROR, "index.html"), "w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write(shell_out)
    total += sum(shell_counts.values())
    changed.append(
        {
            "file": "index.html",
            "rewrites": sum(shell_counts.values()),
            "sha256_after": digest(os.path.join(MIRROR, "index.html")),
        }
    )

    patches = apply_patches(changed)
    code_patches = apply_code_patches(changed)

    # guard: running build_mirror twice without re-fetching narrows the record,
    # because already-rewritten files no longer contain the original URLs
    previous = 0
    if os.path.isfile(os.path.join(MIRROR, "REWRITES.json")):
        try:
            previous = len(json.load(open(os.path.join(MIRROR, "REWRITES.json"), encoding="utf-8"))["files_rewritten"])
        except Exception:  # noqa: BLE001
            previous = 0
    if previous and len(changed) < previous:
        print(
            "WARNING: this run rewrote %d files but the previous record had %d; "
            "run scripts/fetch_assets.py first so the mirror matches its manifest"
            % (len(changed), previous)
        )

    with open(os.path.join(MIRROR, "REWRITES.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "files_rewritten": changed,
                "total_rewrites": total,
                "rules": rules,
                "local_patches_applied": [
                    {"id": p["id"], "description": p["description"], "targets": p["targets"],
                     "kind": "script" if p.get("script") else "style",
                     "selectors": p.get("selectors"), "css": p.get("css")} for p in patches
                ],
                "code_patches_applied": [
                    {"id": p["id"], "description": p["description"], "edits": p["edits"]} for p in code_patches
                ],
                "code_patches_available": [
                    {"id": p["id"], "env": p["env"], "description": p["description"], "edits": p["edits"]}
                    for p in CODE_PATCHES
                ],
                "local_patches_available": [
                    {"id": p["id"], "env": p["env"], "description": p["description"], "targets": p["targets"],
                     "kind": "script" if p.get("script") else "style",
                     "selectors": p.get("selectors"), "css": p.get("css")} for p in LOCAL_PATCHES
                ],
            },
            fh,
            ensure_ascii=False,
            indent=1,
        )
    print("rewrote %d references across %d files" % (total, len(changed)))
    print("local patches applied: %s" % (", ".join(p["id"] for p in patches) or "none"))
    print("code patches applied: %s" % (", ".join(p["id"] for p in code_patches) or "none"))
    for c in sorted(changed, key=lambda c: -c["rewrites"])[:12]:
        print("  %5d  %s" % (c["rewrites"], c["file"]))
    return 0


def rewrite_restore(text, rules):
    """Undo a rewrite (local path -> original URL) to verify reversibility."""
    reverse = {v: "//" + k for k, v in rules.items()}
    counts = {}
    keys = sorted(reverse, key=len, reverse=True)
    for key in keys:
        if key in text:
            counts[key] = text.count(key)
            text = text.replace(key, reverse[key])
    return text, counts


# Both shutdown notices are hardcoded in their bundles (no config flag, no date
# condition). Their CSS-module classes appear exactly once each, and the elements
# are position:fixed full-screen overlays, so a one-rule hide is precise and
# leaves the bundles byte-identical. Each patch has its own switch; set the
# variable to 0 to build a faithful copy.
LOCAL_PATCHES = (
    {
        "id": "hide-shutdown-notice",
        "env": "ZXB_HIDE_SHUTDOWN_NOTICE",
        "targets": ["index.html"],
        "selectors": [".zy5Z34YOK7ZhegFKjmCW"],
        "description": "隐藏首页「住小帮关停公告」整屏浮层（主站 bundle 硬编码）",
    },
    {
        "id": "hide-zhuhaojia-shutdown-notice",
        "env": "ZXB_HIDE_ZHUHAOJIA_NOTICE",
        "targets": ["zhuhaojia/index.html"],
        "selectors": [r".index_notice-overlay__\+MWtd"],
        "description": "隐藏住好家官网「住好家部分服务关停公告」整屏浮层",
    },
    {
        "id": "unlock-zhuhaojia-scroll",
        "env": "ZXB_FIX_ZHUHAOJIA_SCROLL",
        "targets": ["zhuhaojia/index.html"],
        "css": "html,body{overflow:visible !important;touch-action:auto !important}",
        "description": "住好家公告组件挂载时把 body 设成 overflow:hidden；隐藏浮层不会解除滚动锁，这里用 !important 覆盖它",
    },
    {
        "id": "clickable-swiper-dots",
        "env": "ZXB_FIX_SWIPER_DOTS",  # 默认开启：滚轮翻页与点击分页两条路并存
        "targets": ["index.html"],
        "css": ".swiper-pagination-bullet{cursor:pointer}",
        "description": "让分屏 swiper 的分页点可点击（与滚轮翻页并存；只挂点击事件，不改动 DOM 结构）",
        "script": """
(function () {
  var wired = typeof WeakSet === 'function' ? new WeakSet() : null;
  function seen(el) { return wired ? wired.has(el) : el.__mirrorDots; }
  function mark(el) { if (wired) { wired.add(el); } else { el.__mirrorDots = true; } }
  function wire() {
    var list = document.querySelectorAll('.swiper');
    for (var k = 0; k < list.length; k++) {
      var el = list[k], inst = el.swiper;
      if (!inst || !inst.pagination || !inst.pagination.bullets) continue;
      if (seen(el)) continue;
      mark(el);
      var bullets = inst.pagination.bullets;
      for (var i = 0; i < bullets.length; i++) {
        (function (bullet, index) {
          // 不改 DOM：光标由注入的 CSS 控制，这里只挂点击
          bullet.addEventListener('click', function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            inst.slideTo(index);
          }, false);
        })(bullets[i], i);
      }
    }
  }
  var timer = null;
  function schedule() { if (timer) clearTimeout(timer); timer = setTimeout(wire, 200); }
  schedule();
  setTimeout(schedule, 1500);
  setTimeout(schedule, 4000);
  try {
    new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  } catch (err) { /* 老浏览器忽略 */ }
})();
""",
    },
    {
        "id": "merchant-entry-click",
        "env": "ZXB_FIX_MERCHANT_ENTRY_CLICK",
        "targets": ["index.html"],
        "description": "「商家入驻」链接交给 SPA 路由会被当成本站路由（/home 被拼成 /site/home）；"
        "这段在捕获阶段接管点击，直接整页跳转到本地商家平台",
        "script": """
(function () {
  var TARGET = '/home?app_entrance=login';
  document.addEventListener('click', function (ev) {
    var el = ev.target;
    var a = el && el.closest ? el.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('/home?app_entrance=login') === -1) return;
    // capture phase runs before React's delegated handlers, so the SPA router
    // never sees this click
    ev.preventDefault();
    ev.stopPropagation();
    window.location.assign(TARGET);
  }, true);
})();
""",
    },
)


def inject_patch(html, patch):
    """Insert the patch's tag(s); a patch may bring CSS, a script, or both."""
    style_css = patch.get("css") or (
        ",".join(patch["selectors"]) + "{display:none !important}" if patch.get("selectors") else None
    )
    inserted = []

    def already(marker):
        return marker in html

    if style_css:
        marker = '<style data-mirror-patch="%s">' % patch["id"]
        if not already(marker):
            tag = marker + style_css + "</style>"
            if "</head>" not in html:
                print("WARNING: no </head>, cannot inject %s" % patch["id"])
                return html, False
            html = html.replace("</head>", tag + "</head>", 1)
        inserted.append(True)

    if patch.get("script"):
        marker = '<script data-mirror-patch="%s">' % patch["id"]
        if not already(marker):
            tag = marker + patch["script"] + "</script>"
            if "</body>" not in html:
                print("WARNING: no </body>, cannot inject %s" % patch["id"])
                return html, False
            html = html.replace("</body>", tag + "</body>", 1)
        inserted.append(True)

    return html, bool(inserted)


def apply_patches(changed):
    """Inject local patches into their target files and refresh their digests."""
    applied = []
    by_file = {c["file"]: c for c in changed}
    for patch in LOCAL_PATCHES:
        if os.environ.get(patch["env"], patch.get("default", "1")) == "0":
            continue
        for target in patch["targets"]:
            path = os.path.join(MIRROR, target)
            if not os.path.isfile(path):
                print("WARNING: patch target missing: %s" % target)
                continue
            with open(path, encoding="utf-8", errors="surrogateescape") as fh:
                html = fh.read()
            html, ok = inject_patch(html, patch)
            if not ok:
                continue
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
                fh.write(html)
            entry = by_file.get(target) or {"file": target, "rewrites": 0}
            entry.setdefault("local_patches", [])
            if patch["id"] not in entry["local_patches"]:
                entry["local_patches"].append(patch["id"])
            entry["sha256_after"] = digest(path)
            if target not in by_file:
                changed.append(entry)
                by_file[target] = entry
            applied.append(patch)
    return applied


# The shutdown build pins the home page: one listener forces the window back to
# the top on every scroll event, and the section pager registers a *non-passive*
# wheel listener, so Chrome must ask the main thread before scrolling and the
# wheel/gesture never moves the page (verified: same behaviour on the live site,
# while the other three routes scroll normally). Releasing both makes the home
# page scroll like an ordinary page. Each edit must match exactly once.
CODE_PATCHES = (
    {
        "id": "unpin-home-scroll",
        "env": "ZXB_FIX_SCROLL_RESET",
        "description": "解除首页「每次 scroll 都拉回顶部」的锁定",
        "edits": [
            {
                "file": "cdn/async/467.b5543a47.js",
                "find": 'window.addEventListener("scroll",p,{passive:!1})',
                "replace": "(void 0)",  # keep the statement valid: "(()=>{(void 0)})"
                "note": "首页组件每次 scroll 都把窗口拉回顶部",
            },
        ],
    },
    {
        "id": "disable-home-wheel-pager",
        "env": "ZXB_FIX_WHEEL_PAGER",
        "default": "0",  # 默认保留原站行为：滚轮先翻完 section 内的分页点，再翻页
        "description": "移除全局非 passive 滚轮翻屏监听（它会牵住主线程，导致滚轮/手势都不生效）",
        "edits": [
            {
                "file": "cdn/633.4a4bf70d.js",
                "find": '(0,f.Z)("wheel",C,{passive:!1})',
                "replace": "(void 0)",  # keep the statement valid: "return(void 0),{...}"
                "note": "分屏翻页器的全局 non-passive wheel 监听",
            },
        ],
    },
    {
        "id": "unlock-zhuhaojia-input",
        "env": "ZXB_FIX_ZHUHAOJIA_SCROLL",
        "description": "住好家根组件用 non-passive wheel/touchmove 监听无条件 preventDefault，彻底锁死滚动；去掉这两条",
        "edits": [
            {
                "file": "zhuhaojia/static/js/main.f9a99cdd.js",
                "find": 'document.addEventListener("touchmove",e,{passive:!1})',
                "replace": "(void 0)",
                "note": "touchmove 阻止默认，等于锁死触摸滚动",
            },
            {
                "file": "zhuhaojia/static/js/main.f9a99cdd.js",
                "find": 'document.addEventListener("wheel",t,{passive:!1})',
                "replace": "(void 0)",
                "note": "wheel 阻止默认，等于锁死滚轮滚动",
            },
        ],
    },
    {
        "id": "merchant-missing-script-tag",
        "env": "ZXB_FIX_MERCHANT_SCRIPT_TAG",
        "description": (
            "归档的商家应用 index.html 少了一个 <script> 开标签（只有 </script>），"
            "导致那段 mock 脚本被当成正文文字显示、而且没有执行；补回开标签"
        ),
        "edits": [
            {
                "file": "archive/merchant/index.html",
                "find": "</script>\n\n(function () {\n  var originalFetch = window.fetch;",
                "replace": "</script>\n\n<script>\n(function () {\n  var originalFetch = window.fetch;",
                "note": "补回缺失的 <script> 开标签（上游归档缺陷，其线上部署同样显示这段文字）",
            },
        ],
    },
    {
        "id": "local-merchant-entry",
        "env": "ZXB_FIX_MERCHANT_ENTRY",
        "description": (
            "主站「业务合作 → 商家入驻」原本指向线上 e.zhuxiaobang.com，"
            "改为指向本地已归档的商家平台（/home?app_entrance=login）"
        ),
        "edits": [
            {
                "file": "cdn/async/635.2d3b16c7.js",
                "find": 'url:"https://e.zhuxiaobang.com/home?app_entrance=login"',
                # absolute so the client router does not prefix its basename
                # (/home would render as /site/home)
                "replace": 'url:(location.origin+"/home?app_entrance=login")',
                "note": "导航配置里的商家入驻入口：指向本地商家平台",
            },
        ],
    },
)


def apply_code_patches(changed):
    applied = []
    by_file = {c["file"]: c for c in changed}
    for patch in CODE_PATCHES:
        if os.environ.get(patch["env"], patch.get("default", "1")) == "0":
            continue
        done = True
        for edit in patch["edits"]:
            path = os.path.join(MIRROR, edit["file"])
            if not os.path.isfile(path):
                print("WARNING: code patch target missing: %s" % edit["file"])
                done = False
                continue
            with open(path, encoding="utf-8", errors="surrogateescape") as fh:
                src = fh.read()
            count = src.count(edit["find"])
            entry = by_file.get(edit["file"]) or {"file": edit["file"], "rewrites": 0}
            if count == 0 and src.count(edit["replace"]) > 0:
                # already patched: keep the record and its digest complete
                entry.setdefault("code_patches", [])
                if patch["id"] not in entry["code_patches"]:
                    entry["code_patches"].append(patch["id"])
                entry["sha256_after"] = digest(path)
                if edit["file"] not in by_file:
                    changed.append(entry)
                    by_file[edit["file"]] = entry
                continue
            if count != 1:
                print(
                    "REFUSING %s: pattern found %d times in %s (expected exactly 1)"
                    % (patch["id"], count, edit["file"])
                )
                done = False
                continue
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
                fh.write(src.replace(edit["find"], edit["replace"], 1))
            entry = by_file.get(edit["file"]) or {"file": edit["file"], "rewrites": 0}
            entry.setdefault("code_patches", [])
            if patch["id"] not in entry["code_patches"]:
                entry["code_patches"].append(patch["id"])
            entry["sha256_after"] = digest(path)
            if edit["file"] not in by_file:
                changed.append(entry)
                by_file[edit["file"]] = entry
        if done:
            applied.append(patch)
    return applied


def normalize_scheme(text):
    """Scheme is not part of the local rewrite, so compare it away."""
    return text.replace("https://", "//").replace("http://", "//")




if __name__ == "__main__":
    sys.exit(main())
