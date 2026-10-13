# 存档说明与还原步骤

本目录是 `zhuxiaobang.com` 官网的离线 1:1 镜像及其全部证据，可整体打包归档。
解包后按下面两步即可运行与复核。

## 1. 跑起来

```bash
cd site-clone
python3 serve.py --port 8899
# 浏览器打开 http://127.0.0.1:8899/site/institute
```

0 个第三方依赖，只用 Python 3 标准库。镜像本身是纯静态文件，
`mirror/` 目录也可以直接丢给任意静态服务器（需要 SPA 回退：`/site/*` 一律返回 `mirror/index.html`）。

## 2. 复核（离线可做的部分）

```bash
python3 scripts/verify_manifest.py   # 逐文件 sha256 核对（原始字节 / 改写后字节）
python3 scripts/audit_refs.py        # 引用完整性 + 意外外呼检查
```

两者都应以 `verdict: PASS` 结束。`verify_manifest.py` 是解包后判断"这份存档有没有损坏"的依据：
清单里每个文件要么与"下载时的原始字节"摘要一致，要么与"URL 改写后"的摘要一致。

需要浏览器的完整复核（会访问线上站点做对比）：

```bash
bash scripts/verify_all.sh        # 约 20 分钟
```

前置条件：本机 Chrome 已开远程调试并有 `browser-harness` 可用；
`Pillow` 用于图像比对（`/Users/esa/.local/share/uv/tools/browser-harness/bin/python` 自带）。

## 3. 目录内容

| 路径 | 内容 |
| --- | --- |
| `mirror/` | 可直接服务的站点本体（含 `MANIFEST.json`：原始 URL、本地路径、sha256） |
| `mirror/archive/merchant/` | 商家入驻/商家平台应用（**原样归档**，含自己的 `MANIFEST.json`） |
| `mirror/_mock/` | 商家平台接口 fixture（`serve.py` 用来离线应答 `/homed/*`、`/passport/*`） |
| `mirror/REWRITES.json` | 全部 URL 改写规则与逐文件改写次数 |
| `capture/` | REA 抓包证据包（原始事务、响应体、截图） |
| `truth/` | 逐路由事务表、资源清单、探针输出、逐页截图、对比与审计结果 |
| `truth/bodies/` | 抓包时浏览器实际收到的响应体（与 `mirror/` 做交叉校验用） |
| `truth/shots/` | 各轮探针的整页截图（线上 / 本地 / 对照组） |
| `truth/verify*/` | 像素差异图、并排对照图、逐项判定结果 |
| `scripts/` | 抓取、构建、探针、比对、审计脚本 |
| `serve.py` | 本地服务 |
| `README.md` / `REPORT.md` | 使用说明 / 复刻报告（含验证方法与已知差异） |

## 4. 版本信息

- 固化时间：**2026-10-13**
- 主 bundle：`index.f433a181.js`（`cdn/`）、`chunk/48.0c173d84.js`
- 资源数：110（`mirror/MANIFEST.json` 可核对每一项 sha256）
- 覆盖页面：4 条 SPA 路由 + 10 个协议页 + 住好家官网 `/zhuhaojia` + 商家平台 `/home?app_entrance=login`
- 商家平台来源：`github.com/ESA9825/zhuxiaobang-site` → `public/archive/merchant/`（抓取脚本 `scripts/fetch_merchant.py`）

## 5. 本地补丁（与线上有意的差异）

本副本隐藏了两处关停公告浮层（主站首页「住小帮关停公告」、住好家官网「住好家部分服务关停公告」）。
bundle 字节未改，只在外壳 `<head>` 注入 `display:none` 的 CSS 规则，
记录见 `mirror/REWRITES.json` 的 `local_patches_applied`。

```bash
# 恢复全部本地补丁（= 与线上完全一致的忠实副本）
ZXB_HIDE_SHUTDOWN_NOTICE=0 ZXB_HIDE_ZHUHAOJIA_NOTICE=0 \
ZXB_FIX_SCROLL_RESET=0 ZXB_FIX_SWIPER_DOTS=0 ZXB_FIX_ZHUHAOJIA_SCROLL=0 \
  python3 scripts/build_mirror.py
```

五个开关（默认全开）：

| 开关 | 作用 |
| --- | --- |
| `ZXB_HIDE_SHUTDOWN_NOTICE` | 隐藏首页「住小帮关停公告」浮层 |
| `ZXB_HIDE_ZHUHAOJIA_NOTICE` | 隐藏住好家官网关停公告浮层 |
| `ZXB_FIX_SCROLL_RESET` | 移除首页"每次 scroll 拉回顶部"的锁定 |
| `ZXB_FIX_WHEEL_PAGER` | 默认 0（**不移除**）：那是原站的翻页交付方式"滚轮先翻完分页点再翻屏"；设 1 可切成纯连续滚动 |
| `ZXB_FIX_SWIPER_DOTS` | 让 section 内 swiper 分页点可点击（能翻到第二屏） |
| `ZXB_FIX_ZHUHAOJIA_SCROLL` | 解除住好家官网的滚动锁（内联 overflow:hidden + 两条 preventDefault 监听） |
