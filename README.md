# 住小帮官网（zhuxiaobang.com）离线 1:1 镜像

对 `zhuxiaobang.com` 前端产物的完整离线复刻：**原站真实 bundle + 真实资源 + 真实文案**，
不做重写、不做近似。本地起一个静态服务即可浏览，断网可用。

## 快速开始

```bash
cd "/Users/esa/Documents/ChatGPT/住小帮/site-clone"
python3 serve.py --port 8899
# 浏览器打开 http://127.0.0.1:8899/site/institute
```

入口：

| 路径 | 内容 |
| --- | --- |
| `/site/home` | 首页（含原站真实的「关停公告」弹窗） |
| `/site/about` | 了解住小帮 |
| `/site/institute` | 居住研究院 |
| `/site/decorateTips` | 装修锦囊 |
| `/zhuhaojia` | 住好家官网（同域第二个前端应用） |
| `/faas/ugc/*.html` | 隐私政策 / 用户协议 / 第三方信息共享清单 / 敏感个人信息清单 / 帐号注销须知 / 权限申请说明 |
| `/home?app_entrance=login` | **商家入驻 / 商家平台**（完整归档，见下节）——主站导航「业务合作 → 商家入驻」已指向这里 |

## 商家平台（`/archive/merchant`，原样归档）

商家应用取自公开归档仓库 `github.com/ESA9825/zhuxiaobang-site` 的
`public/archive/merchant/`，**102 个文件按原样存放、一个字节都没改**：它的
HTML/JS 引用自己的绝对路径（`/archive/merchant/assets/...`），所以镜像里就放在
`mirror/archive/merchant/`，由本地服务按同样的路径直出。

入口：

| 路径 | 内容 |
| --- | --- |
| `/home?app_entrance=login` | 商家入驻首页（应用自身的首页路由） |
| `/user/login/` | 商家登录页 |
| `/archive/merchant/index.html` | 应用入口文件 |

归档的 `index.html` 少了一个 `<script>` 开标签（导致那段 mock 脚本被当文字显示且不执行），
本地补回该标签（`ZXB_FIX_MERCHANT_SCRIPT_TAG=0` 可还原字节一致）；另有 1 个背景图
`assets/static/bg.039718a0.jpg` 上游归档与线上都已缺失，无法补齐。

它的接口调用（`/homed/business/*`、`/homed/api/*`、`/passport/*`、`/addone/*`）由
`serve.py` 用归档提供的同一套 fixture 返回（`mirror/_mock/*.json`），规则与上游
`public/sw.js` + `scripts/build-pages.mjs` 一致，因此**离线可用**、不需要后端。

导航里的「业务合作 → 商家入驻」指向 `e.zhuxiaobang.com`（独立商家系统，需登录），不属本镜像范围。

## 目录

```
mirror/                直接可服务的站点（83+ 个文件，58 MB）
  index.html           SPA 外壳，每个 /site/* 路由都返回它（与原站一致）
  cdn/                 原 //lf-homed-fe.zhuxiaobang.com/obj/homed-fe-src/cgfe/homed_site/
  vendor/              第三方库与跨域资源（React 17、secsdk、slardar、许可证 PDF、视频等）
  zhuhaojia/           住好家官网（原 scm/homed_fe_new_pc/）与 /zhuhaojia 入口
  faas/ugc/            6 个静态协议页
  MANIFEST.json        每个资源的原始 URL、本地路径、字节数、sha256
  REWRITES.json        本次改写的全部 URL 规则与逐文件改写次数
scripts/               抓取、构建、校验脚本（见下）
truth/                 线上抓包真值、探针输出、截图、对比结果
capture/               REA 证据包（原始抓包）
```

## 镜像做了什么改写

只有 URL 字符串被改写，页面结构、样式、文案、资源字节全部保持原样：

1. `//lf-homed-fe.zhuxiaobang.com/obj/homed-fe-src/cgfe/homed_site/` → `/cdn/`
2. `//lf-homed-fe.zhuxiaobang.com/obj/homed-fe-src/scm/homed_fe_new_pc/` → `/zhuhaojia/`
3. 第三方库（React、secsdk、slardar、视频、许可证 PDF）→ `/vendor/<原域名>/<原路径>`
4. 站内内容页链接（`/faas/ugc/*.html`、`/zhuhaojia`）→ 本地路径

改写是可逆的：`scripts/build_mirror.py` 在写入前会把本地路径还原回原始 URL 并与原文件逐字节比对，
不一致就拒绝写入。未改写的第三方埋点域名（`mon.zijieapi.com`、`mcs.zijieapi.com`、
`lf3-short.ibytedapm.com`）保留原样，离线时请求静默失败，不影响渲染。

## 本地补丁：已隐藏两条关停公告

原站首页有一层「住小帮关停公告」整屏浮层（会把首页盖住），住好家官网有自己的
「住好家部分服务关停公告」。两者都是硬编码在 bundle 里的，本镜像按需隐藏：
**bundle 一字未改**，只在外壳 `<head>` 注入一条精确的 CSS 规则（`display:none`）。

另外两处本地修补（原站关停版本自带的毛病）：

1. **首页滚动被锁死**：组件每次 scroll 都把窗口拉回顶部 —— 线上首页同样滑不动。
   只解除这一条；分屏翻页器（滚轮先翻完 section 内的分页点、翻完再翻屏）**按原站保留**。
2. **分页点额外支持点击**：原站只能靠滚轮联动翻页，本地副本额外把分页点接成可点击，
   与滚轮翻页并存（`ZXB_FIX_SWIPER_DOTS=0` 可关）。

3. **住好家官网滚动被锁**：它的根组件挂载时给 `body` 设了 `overflow:hidden`，
   还加了两条无条件 `preventDefault()` 的 non-passive `wheel`/`touchmove` 监听。
   一并解除后该页可正常滚动到底。

想拿回"完全忠实"的版本：

```bash
ZXB_HIDE_SHUTDOWN_NOTICE=0 ZXB_HIDE_ZHUHAOJIA_NOTICE=0 \
ZXB_FIX_SCROLL_RESET=0 ZXB_FIX_SWIPER_DOTS=0 ZXB_FIX_ZHUHAOJIA_SCROLL=0 \
  python3 scripts/build_mirror.py
```

（`ZXB_FIX_WHEEL_PAGER` 默认就是 0 = 保留原站翻页方式；设成 1 可切成"纯连续滚动"。）

六个开关详见 [REPORT.md](REPORT.md) §5.1–§5.6。

## 校验

```bash
bash scripts/verify_all.sh          # 一键门禁：静态引用 + 线上/本地逐页对比 + DOM 对比 + 对照组
python3 scripts/audit_refs.py       # 本地引用是否全部存在、有没有意外外呼
```

当前结果见 [REPORT.md](REPORT.md)：11 个页面全部渲染成功、0 个 404、0 个控制台报错、
0 个失败资源；像素对比中 7/11 页与线上逐像素完全相同，其余 4 页的差异
**不超过线上自身连跑两次的差异**（动效/滚动相位）；把两侧驱动到同一状态后，
4 条 SPA 路由的渲染后 DOM **逐字节相同**。

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/fetch_assets.py` | 按 webpack 映射表 + bundle 引用 + 线上实际请求下载全部资源，与抓包响应体做 sha256 交叉校验 |
| `scripts/build_mirror.py` | 生成 `mirror/index.html` 并改写 URL（可逆性自证） |
| `scripts/route_probe.py` | 浏览器探针：逐页测量标题/文本/元素/图片/失败请求/控制台错误 + 整页截图 |
| `scripts/diff_probes.py` | 线上 vs 本地：指标比对 + 像素比对（支持噪声基线） |
| `scripts/scroll_probe.py` | 在多个滚动位置对渲染后 DOM 取哈希（遮蔽随机 id 与 URL 属性） |
| `scripts/compare_dom.py` | 比对两份 DOM 探针结果 |
| `scripts/audit_refs.py` | 静态引用审计 |
| `scripts/extract_capture.py` | 从 REA 证据包还原逐路由事务与响应体 |
| `serve.py` | 本地服务（SPA 回退、正确的 MIME、目录式媒体 URL、逐请求日志） |
