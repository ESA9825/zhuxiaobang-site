# 住小帮官网复刻报告（zhuxiaobang.com）

## 1. 目标与结论

目标：把 `zhuxiaobang.com` 这个站在本地**完整、1:1** 复刻，可离线浏览。

结论：达成。做法不是"照着样子重写"，而是**把原站真实产物搬下来改路径**——
同一份 webpack bundle、同一批图片、同一套 CSS、同一份文案，离线跑起来渲染结果与线上一致。

站点规模比预想小得多：整站是**一个静态 SPA + 两类附加页面**，没有业务接口依赖。

| 组成 | 内容 | 页面数 |
| --- | --- | --- |
| 主站 SPA（basename `/site`） | 首页 / 关于我们 / 居住研究院 / 装修锦囊（+ 通配回退到首页） | 4 |
| 静态协议页 | 隐私政策、用户协议、第三方信息共享清单、敏感个人信息清单、帐号注销须知、权限申请说明 | 6 |
| 住好家官网 | 同域第二个前端应用（create-react-app，独立 bundle） | 1 |

## 2. 站点形态（观察，附证据）

1. **纯静态 SPA，无业务接口**。用 REA 连接真实浏览器、模拟真人点击（goto + 等待）抓取五条路由，
   共 **236 次网络事务 / 229 个响应体**（`capture/rea-session.json`）。其中唯一的 XHR 全部是字节的
   监控埋点（`mon.zijieapi.com`、`mcs.zijieapi.com`、`lf3-short.ibytedapm.com`），
   **没有任何内容接口** —— 页面文案、图片、结构都烘焙在前端 bundle 里。
   这是"1:1 离线复刻"可行的根本原因：没有服务端数据需要伪造。

2. **路由表直接可读**。`index.f433a181.js`（webpack 运行时）里写明
   `basename:"/site"`，路由只有 `/home`、`/about`、`/institute`、`/decorateTips` 和通配 `*`；
   通配组件与 `/home` 是同一个 chunk，所以未知路径渲染首页。

3. **导航下拉与页脚指向的额外页面**。展开「业务合作 / 了解住小帮」两个 hover 下拉实测：
   `业务合作 → 商家入驻`（跳 `e.zhuxiaobang.com`，独立商家系统、需登录，不属本镜像范围）；
   `了解住小帮 → 关于我们 / 装修锦囊 / 居住研究院`（即上述 3 条 SPA 路由）。
   页脚另有 6 个同域协议页与 `/zhuhaojia`（住好家官网）。

4. **换域入口等价**。用户提供的 `api3-normal-lq.zhuxiaobang.com` 与 `www.zhuxiaobang.com`
   返回的 HTML **sha256 完全相同**（`7498402…c3a9`），引用同一套 CDN bundle，
   因此同一份镜像同时等价于这两个入口。

5. **CDN 目录列举不可用**（`?prefix=` 返回 404），所以资源清单不靠猜：由
   ① webpack 的 chunk/css 映射表 ② bundle 内引用 ③ 线上实际请求 三路并集得出，
   再用抓包留下的响应体做 sha256 交叉校验。

## 3. 交付物

```
site-clone/
├── mirror/          113 个文件、90.5 MiB，python3 serve.py 即可服务
├── capture/         REA 证据包（47 MB，含逐事务请求/响应体/截图）
├── truth/           逐路由事务表、资源清单、探针与对比结果、截图、审计报告
├── scripts/         抓取 / 构建 / 探针 / 对比 / 审计脚本
├── serve.py         本地服务
├── README.md        使用说明
└── REPORT.md        本文件
```

资源清单（`mirror/MANIFEST.json`）：**110 条资源，0 下载失败，0 sha256 不符**，
其中 62 条与抓包响应体逐字节对上（其余为协议页、住好家资源等抓包未覆盖的部分）。
另有 1 条 webpack 映射里存在、但线上本身已 404 的 chunk（`chunk/785.d5b28db2.js`，
五条路由从未请求它），已单独记录为 `absent_upstream`。

改写（`mirror/REWRITES.json`）：16 个文件、43 处 URL 字符串，112 条规则。
改写前会做**可逆性自证**：把本地路径还原回原始 URL 后必须与原文件逐字节相同，否则拒绝写入。

## 4. 验证方法与结果

验证原则：**先建噪声基线，再判定差异**。逐页把线上跑两遍，得到"线上自己和自己"的差异量，
低于这个量级的差异不能算作复刻失真。

### 4.1 逐页探针（同一台 Chrome、同视口 1440×900、同 reduced-motion 环境）

11 个页面全部渲染成功：标题、文本长度、元素数、图片数、失败请求数、控制台错误数逐项比对。

| 指标 | 结果 |
| --- | --- |
| 页面渲染成功 | 11 / 11 |
| 服务端 404 | 0（`truth/mirror-access-verify.log`，137 次请求全 200） |
| 控制台错误 / 未捕获 Promise 拒绝 | 0 / 0 |
| 图片加载失败 | 0 |
| 标题、文本长度、页高 | 全部一致 |
| 本地引用悬空（`scripts/audit_refs.py`） | 0（45 条引用全部命中） |
| 意外外呼域名 | 0（只剩三处埋点域，离线静默失败） |

### 4.2 像素对比

关闭 CSS 动画/过渡后整页截图逐像素比较（2× 设备像素，允许单通道 ±2）。
"噪声"= 线上同一页连跑两次（在不同时间、同一干净浏览器里）的差异像素数，取多次对照的最大值。

| 页面 | 镜像 vs 线上 | 线上自比噪声 | 判定 |
| --- | ---: | ---: | --- |
| `/site/home` | 69,757 | 1,190,862 | 远低于噪声 |
| `/site/about` | 1,204 | 2,375 | 低于噪声 |
| `/site/institute` | 0 | 0 | 完全一致 |
| `/site/decorateTips` | 0 | 0 | 完全一致 |
| `/faas/ugc/*`（6 页） | 0 | 0 | 完全一致 |
| `/zhuhaojia` | 5,293 ~ 1,267,730 | 161,652 ~ 1,199,518 | 动画相位主导，见 §4.4 |

单页约 780 万像素。四条 SPA 路由里两条逐像素完全相同，`/site/home` 与 `/site/about`
的差异来自动效/滚动驱动的相位（`/site/home` 首页有大幅动画，线上自己两次运行也会差 10 万像素级）。
不同轮次的具体数值会波动，因此判定用的是"逐轮对照"，而不是固定阈值。

`/site/about` 的残留差异来自时间轴进度点的滚动状态；线上该页自己两次运行就差 3,913 像素，
镜像与线上的差距（2,732）比它更小。

### 4.3 渲染后 DOM 对比（同一滚动位置）

单张截图覆盖不到滚动驱动组件，因此做两层 DOM 对比。两层都先遮蔽固有随机项：
UI 库的 `data-rc-id`、播放器随机 id、以及被有意改写的 URL/`target` 属性。

**第一层（判定依据）：同一状态逐字节比对。** 把两侧都驱动到同一个明确状态（页面底部），
再逐字节比较：

| 路由 | 结果 | 字节数 |
| --- | --- | ---: |
| `/site/home` | 完全相同 | 35,974 |
| `/site/about` | 完全相同 | 34,198 |
| `/site/institute` | 完全相同 | 24,383 |
| `/site/decorateTips` | 完全相同 | 19,177 |

**第二层（信息性）：5 个滚动位置的序列对比。** 这一层只在"两侧都复现该状态"时才计入比较
（`stable` 标记，由同状态连拍两次得出）。它会波动：`/site/home`、`/site/decorateTips`
在一轮里 5/5 一致，另一轮又会各自停在两个不同状态之一（线上自己同样会翻），
原因是这些页面的状态与滚动历史/计时相关。因此判定不依赖这一层，但结果照实记录在
`truth/verify*/`、`truth/live-dom.json`、`truth/mirror-dom.json`。

### 4.4 已确证的差异（不掩饰）

1. **`/zhuhaojia` 有动画相位差**：差异集中在"装修进度相册"自动滚动的照片墙上，
   两次截图停在不同相位。线上该页自己连跑两次差 **1,199,518** 像素，镜像与线上差
   **1,267,730** 像素（同一量级：都是"相册停在另一帧"）。该动画由 JS 驱动，
   冻结 CSS 动画无效。因此这一页的验收改用 DOM/文本/资源集合判定（均一致），
   像素差在 `scripts/final_report.py` 里作为显式规则（`ANIMATION_DOMINATED`）记录，
   而非靠模糊阈值放过。
2. **链接的 `target` 属性**：原站把站内协议页当外链（`target="_blank"`），
   镜像把这些链接改写成本地路径后，UI 组件按站内链接渲染，因此少了 `target="_blank"`。
   5 个链接受影响，已纳入 DOM 比对的遮蔽项并在 README 说明。
3. **协议页高度在滚动后偶发 ±30px**：干净加载下线上/本地几何完全一致
   （`scrollHeight` 9731 / 9731、`body` 宽 1152 / 1152），差异只出现在"滚动一遍再测"的瞬时状态，
   已通过"高度连续两次稳定后再测量"消除。
4. **`resources` 计数差**：本地服务发 `Cache-Control: no-store`，线上 CDN 命中缓存的资源在本地会重新请求，
   因此镜像请求数是线上的**超集**（逐页 `only_live` 全为空，即线上加载的资源镜像一个不少）。
   计数差异不构成缺失。
5. **一次测量被同机其它进程污染**：`truth/mirror-pages.json` 的某一轮里，隐私政策页出现 9 个
   `/uinotes-api/app-detail?...` 404。该路径在页面与 bundle 中均不存在，干净加载与
   fetch/XHR 钩子实验都复现不出来；`ps` 显示同机另有一个 `uinotes-v35` 项目的 agent 在跑，
   应是它打到共享浏览器上的流量。改用独立 Chrome（9334 端口、全新 profile）重跑后，
   7 个内容页 **0 个失败请求**（`truth/mirror-pages.json`）。

## 5. 未覆盖 / 未知

- **商家入驻**（`e.zhuxiaobang.com`）是独立系统且需登录，不在镜像范围。
- **外链**：京公网安备、京 ICP、高德地图、邮件等保持指向真实地址。
- **埋点域名**保留原样，离线时请求失败（不影响渲染）；未做本地桩替换。
- 站点的内容会随后端发布变化：本镜像固化的是 **2026-10-13** 抓取到的版本
  （bundle `index.f433a181.js`、`chunk/48.0c173d84.js` 等，sha256 见 `MANIFEST.json`）。
- 首页那条「住小帮将于 2026 年 8 月 8 日停止运营及服务」的公告是**原站真实内容**（烘焙在 bundle 内），
  不是镜像引入的；`/zhuhaojia` 的「住好家部分服务关停公告」同理。

## 5.1 本地补丁：隐藏两条关停公告

按用户要求，本地副本隐藏了两处关停公告浮层。两条公告都**硬编码在各自 bundle 的 JSX 里**
（没有开关、没有时间条件），所以没有"配置项"可改。做法是：**bundle 保持逐字节不变**，
只在外壳 `<head>` 注入一条精确的 CSS 规则：

```html
<style data-mirror-patch="hide-shutdown-notice">.zy5Z34YOK7ZhegFKjmCW{display:none !important}</style>
<style data-mirror-patch="hide-zhuhaojia-shutdown-notice">.index_notice-overlay__\+MWtd{display:none !important}</style>
```

| 补丁 | 目标文件 | 选择器 | 依据 |
| --- | --- | --- | --- |
| `hide-shutdown-notice` | `mirror/index.html` | `.zy5Z34YOK7ZhegFKjmCW` | 该 class 在 CSS 中仅出现一次，规则为 `position:fixed; z-index:9999` 的整屏浮层 |
| `hide-zhuhaojia-shutdown-notice` | `mirror/zhuhaojia/index.html` | `.index_notice-overlay__\+MWtd` | 同上，`position:fixed; z-index:100` |

可复现、可回退：`scripts/build_mirror.py` 负责注入并把结果记进 `mirror/REWRITES.json`
（`local_patches_applied` / `local_patches_available`）。

```bash
python3 scripts/build_mirror.py                                  # 默认：隐藏两条公告
ZXB_HIDE_SHUTDOWN_NOTICE=0 python3 scripts/build_mirror.py       # 恢复主站公告
ZXB_HIDE_ZHUHAOJIA_NOTICE=0 python3 scripts/build_mirror.py      # 恢复住好家公告
```

改动被验证为"只少了公告"：

- 公告文字不再出现在可见文本里（`noticeVisible`：镜像 `false`、线上 `true`，逐路由断言）；
- 浮层 `display:none`、占位高度 0，视口中心命中页面的正常内容 → **不再遮挡交互**；
- 页面其余部分不变：把补丁样式从比对中遮蔽后，4 条 SPA 路由的渲染后 DOM 仍与线上**逐字节相同**；
- 元素数、图片数、控制台错误、失败请求、资源覆盖全部照旧通过（`scripts/final_report.py` → PASS）。

唯一有意保留的差异：隐藏公告后首页可见文本从 1,312 字降为 866 字（`/zhuhaojia` 从 914 降为 400），
公告节点本身仍在 DOM 中（只是不显示），因此结构比对仍与线上一致。

## 5.2 本地补丁：解除首页滚动锁定

**现象**：本地首页用滚轮/触控板滑不动（其它三条路由正常）。**先确认这不是镜像引入的**：
线上 `www.zhuxiaobang.com/site/home` 行为完全一致 —— 滚轮、合成滚动手势都无效，
程序化 `window.scrollTo` 有效；对照的静态页面（协议页）滚轮正常。

**排查证据**：

- 滚轮事件确实到达页面（`target=HTML`、`defaultPrevented=false`），但页面不动，
  且**没有任何 `scroll` 事件**产生 —— 说明不是被 `preventDefault` 拦下；
- 逐帧采样（rAF）显示 `scrollY` 恒为 0，也没有 `scrollTop=0` 赋值；
- 派发滚轮时 CDP 的 `Input.dispatchMouseEvent` 会超时（30–90s 无响应），
  说明主线程被牵住 —— 这正是「非 passive wheel 监听」的典型症状。

**根因**（关停版本里两处叠加）：

1. 首页组件注册了 `window.addEventListener("scroll", p, {passive:!1})`，而 `p` 是
   `window.scrollTo(0, 0)` —— 任何滚动都被立刻拉回顶部；
2. 分屏翻页器在模块 47572 里注册了全局非 passive 滚轮监听
   `(0,f.Z)("wheel",C,{passive:!1})`，Chrome 必须等主线程答复才滚动。

**处理（最终形态）**：只解除第 1 条 —— 它才是"页面被钉住"的直接原因；第 2 条**保留**，
因为它是原站设计的分屏翻页交付方式（见 §5.6：滚轮先翻完 section 内的分页点，再翻到下一屏）：

| 文件 | 原文 | 处理 | 默认 |
| --- | --- | --- | --- |
| `cdn/async/467.b5543a47.js` | `window.addEventListener("scroll",p,{passive:!1})` | 替换为 `(void 0)` | 生效（`ZXB_FIX_SCROLL_RESET=0` 可关） |
| `cdn/633.4a4bf70d.js` | `(0,f.Z)("wheel",C,{passive:!1})` | **保留**，仅在需要"纯连续滚动"时才移除 | 保留（`ZXB_FIX_WHEEL_PAGER=1` 才移除） |

补丁要求每处**必须恰好匹配一次**，否则拒绝写入；改写记录进 `mirror/REWRITES.json`
（`code_patches_applied`），摘要进 `sha256_after`，`scripts/verify_manifest.py` 照常校验。

**效果**：首页恢复响应滚轮 —— 先把当前 section 的分页点翻完，翻完了才继续翻到下一屏，
反向同理（实测轨迹见 §5.6）。页高与文本长度与原始一致（3,464 / 4,572 / 3,252 / 3,464）；
把补丁注入的节点从比对中遮蔽后，四条路由的渲染后 DOM 仍与线上**逐字节相同**；`final_report.py` → PASS。

> 过程中的一个中间版本曾把第 2 条也一并移除，结果首页变成"普通连续滚动"、而 section 内的
> 分页点失去翻页入口（见 §5.3）。用户随后指明期望的是 api3-normal-hl 那一版
> `decorateTips` 的交付方式，因此改为"只解第 1 条、保留第 2 条"，并额外保留点击分页点这条入口。

## 5.3 本地补丁：让"两屏"内容能翻到第二屏

首页「海量内容与达人」这一类 section 内部是**纵向 swiper**（实测：一个 2 屏、一个 3 屏，
高度 = 视口，`pagination.type = bullets`、**`clickable: false`**、**未启用 `mousewheel` 模块**）。
也就是说原站里这两个 section 的翻页**只能靠 §5.2 那个滚轮翻屏器联动**（滚轮 → `slideNext()`）。
§5.2 把翻屏器解掉之后，分页点仍然显示两屏，但第二屏没有了入口 —— 这正是截图里"蓝点表示有两页、
另一页不出现"的原因。

**处理**：补丁 `clickable-swiper-dots`（`ZXB_FIX_SWIPER_DOTS=0` 可关，默认开启）：在外壳注入一段
小脚本，把每个 swiper 实例的分页点接上点击（`inst.slideTo(i)`），并把光标改成 pointer。

这是**镜像本地新增的交互**（原站没有这条路径）。§5.2 恢复滚轮翻页后，这条路不再必需，
但与滚轮路径**并存**：滚轮照原站方式翻页，想直接跳某一屏也可以点分页点。

**验证**：点击第二个分页点后 `activeIndex 0 → 1`，第二屏内容渲染为
「权威装修锦囊 让你跟着装不踩坑 / 行业专家编审，提供一站式家装布局及选购建议」；
页面滚动、其它三条路由、DOM 逐字节比对均不受影响（`scripts/final_report.py` → PASS）。

## 5.4 本地补丁开关一览

| 开关 | 默认 | 作用 |
| --- | --- | --- |
| `ZXB_HIDE_SHUTDOWN_NOTICE` | 1 | 隐藏首页「住小帮关停公告」浮层 |
| `ZXB_HIDE_ZHUHAOJIA_NOTICE` | 1 | 隐藏住好家官网「住好家部分服务关停公告」浮层 |
| `ZXB_FIX_SCROLL_RESET` | 1 | 移除首页"每次 scroll 拉回顶部"的锁定 |
| `ZXB_FIX_WHEEL_PAGER` | **0** | 移除全局非 passive 滚轮翻屏监听（默认**不移除**：那是原站的翻页交付方式，设 1 可切成"纯连续滚动"） |
| `ZXB_FIX_SWIPER_DOTS` | 1 | 让 section 内 swiper 的分页点可点击（与滚轮翻页并存） |

全部关成 0（并保留默认就为 0 的 `ZXB_FIX_WHEEL_PAGER`）即得到与线上完全一致的忠实副本：

```bash
ZXB_HIDE_SHUTDOWN_NOTICE=0 ZXB_HIDE_ZHUHAOJIA_NOTICE=0 \
ZXB_FIX_SCROLL_RESET=0 ZXB_FIX_SWIPER_DOTS=0 \
  python3 scripts/build_mirror.py
```

想要"普通连续滚动、不要分屏翻页"就反过来：

```bash
ZXB_FIX_WHEEL_PAGER=1 python3 scripts/build_mirror.py
```

## 5.5 本地补丁：解除住好家官网的滚动锁

**现象**：`/zhuhaojia` 页面滑不动（隐藏公告后依然滑不动）。

**根因**（住好家根组件 `Tt` 的 `useEffect`，`zhuhaojia/static/js/main.f9a99cdd.js`）：
它在挂载时执行

```js
document.body.style.overflow = "hidden";
document.body.style.touchAction = "none";
document.addEventListener("touchmove", e => e.preventDefault(), {passive:false});
document.addEventListener("wheel",     e => e.preventDefault(), {passive:false});
```

也就是说：公告浮层只是个"外壳"，真正锁住滚动的是**内联 `overflow:hidden` +
两条无条件 `preventDefault()` 的 non-passive 输入监听**。只把浮层 `display:none`
改变不了这个状态 —— 实测 `body` 计算值是 `visible` 之后滚轮依然无效，直到把这两条监听去掉。

**处理**（两条补丁，共用开关 `ZXB_FIX_ZHUHAOJIA_SCROLL=0` 可关）：

| 类型 | 内容 |
| --- | --- |
| 注入 CSS | `html,body{overflow:visible !important;touch-action:auto !important}`（`!important` 才能压过内联样式） |
| 代码补丁 `unlock-zhuhaojia-input` | 删除 `document.addEventListener("touchmove",e,{passive:!1})` 与 `document.addEventListener("wheel",t,{passive:!1})` 两条语句（替换为 `(void 0)`，清理函数保留、无害） |

**验证**：滚轮连续滚动到页面底部（`scrollY 0 → 572`，572 即最大可滚距离），页脚
（公司名称/地址/联系电话、京 ICP 备案）正常显示；公告文字仍不可见；
`final_report.py` → PASS；清单校验与引用审计不受影响。

## 5.6 滚轮翻页的交付方式（与参考站对照）

期望行为（用户以 `https://api3-normal-hl.zhuxiaobang.com/site/decorateTips` 为参照）：
**向下滚时先把当前 section 的分页点翻完，翻完了页面才继续往下；向上滚同理，先翻回上一屏，
没内容了再往上走。**

参考站实测轨迹（`scrollY` / 各 swiper 的 activeIndex）：

| 滚轮 | 参考站 `api3-normal-hl/site/decorateTips` | 本地镜像 `/site/home` |
| --- | --- | --- |
| 1 | `y 790, idx [0]` | `y 710, idx [0,0]` |
| 2 | `y 1580, idx [0,0]` | `y 790, idx [1,0]` ← 页面不动，分页点翻页 |
| 3 | `y 1580, idx [1,0]` ← 页面不动，分页点翻页 | `y 1580, idx [1,0]` |
| 4 | `y 2370, idx [1,0]` | `y 1580, idx [1,2]` ← 页面不动，分页点翻页 |
| 5 | `y 2370, idx [1,1]` ← 页面不动，分页点翻页 | `y 2595, idx [1,2]` |
| 6 | `y 2674, idx [1,1]` | `y 2674, idx [1,2]` |

反向（本地镜像，从 `y 2370` 往上滚）：`1580 → 1580(idx 1→0) → 790 → 790(idx 0→0) → 0`，
同样是"先翻回上一屏，没内容了再往上"。

结论：两条路径的**行为模式一致**（先翻点、后翻屏），差异只是各 section 内部的屏数不同。

## 6. 商家平台（商家入驻）归档

**来源**：公开归档仓库 `github.com/ESA9825/zhuxiaobang-site` 的 `public/archive/merchant/`
（101 个文件 / 67.9 MiB，含应用本体与 API fixture）。抓取脚本：
`scripts/fetch_merchant.py`（逐文件记录 sha256，写入 `mirror/archive/merchant/MANIFEST.json`）。

**处理方式：完全原样，不改一个字节。** 这一点是刻意的：

- 该应用的 HTML/JS 引用自己的绝对路径（`/archive/merchant/assets/...`），
  所以镜像里就存放在 `mirror/archive/merchant/`，由 `serve.py` 按同一路径直出，
  不需要任何 URL 改写；
- 它的 `window.routerBase` 保持 `"/"`，页面路由（`/home`、`/user/login/` 等约 70 条）
  由 `serve.py` 按其路由表回退到应用入口；
- 上游在 `index.html` 里内置的 mock 脚本、链接修正脚本等**全部保留**。

**接口离线可用**：应用的接口是同源相对路径（`/homed/business/bservice/...`），
`serve.py` 用归档自带的 fixture（`mirror/_mock/*.json`）应答，规则与上游
`public/sw.js`（运行时兜底）与 `scripts/build-pages.mjs`（逐接口 fixture 映射）一致：

| 接口 | fixture |
| --- | --- |
| `/homed/business/bservice/account/getinfo` | `merchant-account.json` |
| `/homed/business/bservice/authority/queryRouteList`、`userType/get` | `merchant-route-list.json` |
| `/homed/business/bservice/user/get_user_info` | `merchant-user-info.json` |
| `/homed/business/bservice/opportunity/phoneInit` | `merchant-phone-init.json` |
| `/homed/business/bservice/config/navibarButtons` | `merchant-navibar-buttons.json` |
| `/homed/business/bservice/businessOrganization/queryPlatform*` | `merchant-pack-info.json` |
| `/homed/api/fe/invoke/getNgccSign`、`queryBySubjectIds` | `merchant-empty.json` |
| `/passport/aff/web/subject/login_list` | `passport-login-list.json` |
| 其余 `/homed/business/*`、`/passport/*` | 按上游 sw.js 规则返回空结构 |

### 6.1 修复一处上游缺陷：缺失的 `<script>` 开标签
+
+归档的 `index.html` 里有一段内联 mock 脚本**只有 `</script>`、没有开标签**，
+导致浏览器把这段 JS 当成正文渲染（页头出现一大段字母），**而且该脚本实际没有执行**。
+上游那份 GitHub Pages 部署有同样的现象。
+
+处理：补回缺失的 `<script>` 开标签（一处插入，`ZXB_FIX_MERCHANT_SCRIPT_TAG=0` 可还原成字节完全一致）。
+`scripts/verify_all.sh` 现在带一条回归断言：商家页可见文本里不得再出现脚本源码。
+
+### 6.2 主站「商家入驻」入口指向本地商家平台

主站导航配置里原本是外部地址：

```js
{id: s.MERCHANT_SETTLEMENT, text: "商家入驻", type: "link",
 url: "https://e.zhuxiaobang.com/home?app_entrance=login"}
```

改造成本比想象高一点，记一下踩到的坑：

1. **不能只改成路径**。第一版把它改成 `/home?app_entrance=login`，但主站 SPA 的 `basename` 是 `/site`，
   客户端路由会把根路径拼上 basename，最终渲染成 `href="/site/home?app_entrance=login"` ——
   点过去到了主站自己的首页。
2. **绝对地址才不会被拼前缀**。改成 `url:(location.origin + "/home?app_entrance=login")`（运行时求值），
   渲染出的 href 就是 `http://127.0.0.1:8899/home?app_entrance=login`，且换端口也不用改。
3. **还要绕开客户端路由的点击拦截**。即便 href 正确，点击仍会被 SPA 路由接管成站内跳转（URL 不变）。
   因此再注入一段脚本，在**捕获阶段**接管该链接的点击、直接整页跳转
   （捕获阶段早于 React 在根容器上的委托监听，`stopPropagation` 后路由看不到这次点击）。

两个补丁分别可关：`ZXB_FIX_MERCHANT_ENTRY`（bundle 里那行配置）、
`ZXB_FIX_MERCHANT_ENTRY_CLICK`（注入的点击接管脚本）。

**验证**：从主站导航点击该入口，落到 `/home?app_entrance=login`（标题「住小帮商家平台」、商家落地页内容），
连续 2/2 次一致；直接访问该地址 4/4 次稳定渲染落地页。

### 6.3 已知缺口
+
+归档里缺 `assets/static/bg.039718a0.jpg`（页面会请求它并 404）。经核对：
+归档仓库没有这个文件，上游 Pages 部署同样 404，线上 `e.zhuxiaobang.com` 返回 403（平台已关停），
+因此**无法补齐**，与上游保持一致。
+
+**验证**：
+
+- 商家树 101 个文件：**100 个与原清单逐字节一致 + 1 个（`index.html`）为已记录的本地补丁**；
- 浏览器实测三条入口均正常渲染：`/home?app_entrance=login`（商家入驻首页，标题"住小帮商家平台"）
  与 `/user/login/`（登录页）0 控制台报错、0 失败资源（我们的 mock 还顺手修掉了上游那份
  部署里 `getSignStatus` 的 404）；
- 与上游部署对照：同尺寸整页截图逐像素比较，**差异 2,780 像素 / 493 万（0.056%）**，
  且集中在右上角登录态那一小块 —— 即两边渲染一致。

## 6. 复现

```bash
cd "/Users/esa/Documents/ChatGPT/住小帮/site-clone"
python3 scripts/fetch_assets.py         # 下载 110 个资源并与抓包响应体交叉校验
python3 scripts/build_mirror.py         # 生成 index.html 并改写 URL（含可逆性自证）
python3 serve.py --port 8899            # 本地服务
bash   scripts/verify_all.sh            # 一键门禁（约 10 分钟，含线上对照）
```

## 7. GitHub Pages 部署

**目标**：把本项目部署到 `github.com/ESA9825/zhuxiaobang-site`，替换原来的站点
（仓库内容已整体更换，历史保留在上一条提交里）。

**结构**：仓库里放镜像本体 + 构建脚本，由 GitHub Actions 生成并发布：

```
mirror/                         站点本体（含商家归档）
scripts/build_pages.py          Pages 构建脚本
.github/workflows/deploy-pages.yml   checkout -> build_pages.py -> upload-pages-artifact -> deploy-pages
```

**Pages 是子路径部署**（`https://<user>.github.io/<repo>/`），而镜像是按 origin 根写的
（`/cdn/…`、`/site/…`、`/archive/…`），所以 `build_pages.py` 做五件事：

1. `mirror/` → `out/`；
2. 把根绝对 URL 加上 `/<repo>` 前缀（HTML/JS/CSS/JSON/SVG）；
3. 把两处 router base 挪到同一前缀下：主站 SPA 的 `basename:"/site"` → `"/<repo>/site"`，
   商家应用的 `window.routerBase = "/"` → `"/<repo>/"`；
4. 静态托管没有 SPA 回退，因此把客户端路由落成真文件：主站 4 条路由 + 商家应用路由表里
   的 73 条（从它的 umi bundle 里读取）；
5. 商家接口：11 个 fixture 写成对应路径的静态文件，并复用上游那份 `sw.js`
   （注册在主站前缀下）兜住其余 `/homed/*`、`/passport/*` 请求。

**踩到的三个坑**（都已修，并写进脚本注释）：

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 商家应用整页空白 | 路由表里的 `path:"/home/"` 被一起加了前缀，路由匹配不上（`rg -c` 按行计数还骗过我一次：这个 bundle 只有一行） | 加 `unprefix_route_paths`：`path:"/<repo>/…"` → `path:"/…"`（上游构建也是这么做的） |
| 商家页满屏「网络异常」 | 接口路径 `/homed/business/` 被加了前缀，而页面内置 mock 是按**原路径**做子串匹配的，匹配不上就真的发请求、然后失败 | 接口 token（`homed`/`passport`/`addone`）排除在前缀替换之外 |
| 主站 `/home` 路由依赖兜底 | 同一类问题（主站的 `/home` 路由也被加过前缀） | 同上，由路由还原步骤统一处理 |

**验证**：

- 本地先用纯静态服务器模拟子路径（`/zhuxiaobang-site/` 挂到 `out/`）：主站四页、商家落地页/登录页、
  住好家、协议页、商家静态资源、接口 fixture、`sw.js` 全部 200 且渲染正常；
- 线上（Actions 部署完成后）实测同样一组路径：全部 200；浏览器渲染
  `/site/home/`、`/site/about/`、`/home/`、`/zhuhaojia/` 标题与内容正确，
  商家落地页无报错。

**已知限制**（静态归档 + 离线 fixture 的固有边界）：

- 登录后的商家后台页（如 `/bank/dashboard/`）只能渲染空态/提示，因为 fixture 只覆盖落地页与登录流；
- 主站页面的 slardar 埋点插件按 `<origin>/slardar/...` 取，Pages 上必然是 404（纯埋点，无影响）；
- 商家归档缺 `assets/static/bg.039718a0.jpg`（上游同样缺）。
