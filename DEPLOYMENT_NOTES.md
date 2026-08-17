# Zhuxiaobang Pixel Archive

## Status

- Source reference: `https://www.zhuxiaobang.com/`
- Project: `/Users/esa/dev/zhuxiaobang-clone`
- Local URL: `http://127.0.0.1:3002/`
- Aliyun URL: `http://zhuxiaobang.mofun.vip/zhuxiaobang-clone/index.html`
- Node: `v24.14.1`
- Build: `npm run typecheck`, `npm run lint`, `npm run build` all passed.
- Service: `launchctl` label `local.zhuxiaobang-clone`

## Start

```sh
launchctl bootout gui/$(id -u)/local.zhuxiaobang-clone 2>/dev/null || true
launchctl bootstrap gui/$(id -u) /Users/esa/Library/LaunchAgents/local.zhuxiaobang-clone.plist
```

## Stop

```sh
launchctl bootout gui/$(id -u)/local.zhuxiaobang-clone
```

## Primary URLs

- `/` redirects to the archived original homepage.
- `/site/home` redirects to the archived original homepage.
- `/site/about` redirects to the archived original about page.
- `/site/decorateTips` redirects to the archived original decorate-tips page.
- `/site/institute` redirects to the archived original institute page.
- `/merchant` redirects to the archived original merchant entry app at `/home?app_entrance=login`.
- `/zhuhaojia` redirects to the archived original zhuhaojia page.
- `/faas/ugc/private_protocal_text.html` redirects to the archived privacy policy.
- `/faas/ugc/user_protocal.html` redirects to the archived user agreement.
- `/archive` lists the offline archive pages.
- `/archive/<page>/index.html` serves the original rendered DOM, CSS, JS, and downloaded assets directly.
- The shutdown notice block is hidden on the main SPA archive pages via a small CSS override.
- All archived HTML pages have an explicit `<!doctype html>`.
- The main SPA pages disable the original full-page scroll lock so the homepage can scroll normally with the wheel.

## Notes

- Aliyun OSS default domains force-download HTML. The public clone is served through the custom domain `zhuxiaobang.mofun.vip`, which is bound to the `mofun-vip` OSS bucket.
- The live entry redirects to `/zhuxiaobang-clone/archive/home/index.html`; the merchant entry is at `http://zhuxiaobang.mofun.vip/zhuxiaobang-clone/merchant/index.html`.
- This project now serves the archived original pages at the primary local URLs.
- The earlier non-branded reference routes remain in `src/app` for development history but are no longer the primary landing experience.
- `public/archive/` contains the local archive of the original rendered DOM, CSS, JS, and downloaded images.
- Dynamic app pages, real search, user accounts, merchant backend, and live services are out of scope.
- The archive should be kept offline and should not be deployed publicly.
